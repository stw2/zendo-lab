"""E03's backend: a model behind the Codex CLI (`codex exec`), with every tool off, as one ZendoBench 1.0.0 backend.

ZendoBench stays unpatched: `CodexBackend` is a `zendo_bench.backends.base.Backend`, and ZendoBench's own
runner plays, records and scores the games (`01_play.py`). Each decision is one stateless call: ZendoBench's
system prompt becomes Codex's instructions (`model_instructions_file`), its user message the prompt, and the
last agent message of the turn the reply, read under ZendoBench's ungrammared policy as an HTTP reply is.

Isolation (DESIGN.md):
- No tools in the request: every Codex feature on by default is disabled (the list is frozen at setup,
  `features.json`), web search off, no MCP servers, plugins, skills, hooks or AGENTS.md (`--ignore-user-config`,
  `--ignore-rules`, `project_doc_max_bytes=0`), the plan and user-input tools off, and Codex's own context
  messages off (permissions, apps, collaboration modes, environment context, skills). The model catalog is the
  server's, frozen at setup, with CATALOG_EDIT applied to each model (`catalog.json`): without it Codex still
  offers code mode's exec and wait, apply_patch and experimental tools, and adds a sub-agent role message.
  `codex debug prompt-input` shows the model the user message alone, and the server's echo of a request shows
  no tools (`00_check.py --call`).
- Its own Codex home, logged in on its own (not the owner's ~/.codex), sessions ephemeral (none kept).
- Each call runs in a new empty folder, Codex's sandbox read-only; the folder must still be empty after.
- The whole `codex` process runs under macOS's sandbox (`sandbox.sb`): every user folder (the
  repositories, run files, ~/.codex, ZendoBench's sealed salt), temporary folder and volume is closed
  to it, but its own state.
- Flags: a completed or started item other than the agent message, reasoning or a Codex notice (a command,
  a file read or change, a tool, MCP or web call), or a file left in the call's folder, raises
  `IsolationFlag`: the call's events go to a flag file and the run stops (`01_play.py`). After each run part,
  04_denials.py flags any sandbox denial for the codex process beyond its own startup.

Traces, for analysis after the run: each try of each call adds one line to the run part's trace file (01_play.py
puts it in traces/ beside the run file; both stay out of git). The line holds the try's metadata and outcome,
Codex's whole event stream, its own stderr lines, and the server's messages from Codex's websocket trace: the
response objects (each echoes the request's tools and settings, and the output), rate-limit and timing messages,
with the streamed deltas counted, not kept. `trace_id` joins it to the call record in the run file. A line in
which any string value of Codex's login file appears is withheld.

Failures, as ZendoBench's HTTP adapter treats them: a failed call (a failed turn, an error event, a non-zero
exit, a timeout, no answer and no output) is retried with backoff; when the retries are spent, the game is
stopped unfinished (`GameStopped`) and a later run plays it again. The ChatGPT usage limit stops the run
cleanly (`UsageLimitReached`); the games in flight are unfinished and replayed on resume.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

from zendo_bench.backends.base import (FINISH_ACTION, FINISH_EOS_IN_THOUGHT, Backend, BackendFailure, GameStopped,
                                       Reply, UsageLimitReached)

HERE = Path(__file__).resolve().parent
SOURCE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()  # as loaded: one value for the whole run
STATE = Path(os.environ.get("E03_STATE", Path.home() / ".cache" / "zendo-lab" / "e03-codex"))
CODEX_VERSION = "0.160.0"
EFFORT = "high"
SUMMARY = "detailed"  # reasoning summaries kept in the call record, as E1 kept reasoning (--keep-reasoning)
TIMEOUT = 3600  # seconds a call may take (ZendoBench's unstreamed HTTP default)
BACKOFF = [30, 60, 120, 300, 900]  # seconds before each retry of a failed call
FIELD_CHARS = 500

# Codex's own context, off; the plan and user-input tools, web search and AGENTS.md off
CONFIG = ["include_permissions_instructions=false", "include_apps_instructions=false",
          "include_collaboration_mode_instructions=false", "include_environment_context=false",
          "skills.include_instructions=false", "tools.update_plan.enabled=false",
          "tools.experimental_request_user_input.enabled=false", 'web_search="disabled"',
          "project_doc_max_bytes=0", 'sandbox_mode="read-only"']
# Each model's catalog entry, edited at setup: no sub-agent role message, no code-mode tools (exec, wait), no
# experimental tools and no apply_patch tool
CATALOG_EDIT = {"multi_agent_version": None, "tool_mode": "direct_only", "experimental_supported_tools": [],
                "apply_patch_tool_type": None}
ANSWER, THOUGHT, NOTICE = "agent_message", "reasoning", "error"
USAGE_LIMIT = ("usage limit", "usage_limit", "hit your usage")
# Codex's trace of its websocket: the server's messages to Codex, kept in the call traces (the requests it sends
# are logged only as masked frames). No login token is in it (checked before each write, `login_secrets`).
TRACE_TARGET = "tungstenite::protocol=trace"
FRAME_DUMP = ("<FRAME>", "final: ", "reserved: ", "opcode: ", "length: ", "payload length: ", "payload: ")


def split(stderr):
    """Codex's own stderr lines; the server's messages from the trace, with their streamed deltas counted, not kept."""
    plain, server, deltas = [], [], 0
    for line in stderr.splitlines():
        if " tungstenite::" in line:
            if "Received message " in line:
                try:
                    message = json.loads(line.split("Received message ", 1)[1])
                except ValueError:
                    continue
                if str(message.get("type", "")).endswith(".delta"):
                    deltas += 1
                else:
                    server.append(message)
        elif line.strip() and not line.lstrip().startswith(FRAME_DUMP):
            plain.append(line)
    return "\n".join(plain), server, deltas


def parsed(line):
    """A line of Codex's event stream as JSON, or as the text it is."""
    try:
        return json.loads(line)
    except ValueError:
        return line


def login_secrets():
    """The string values of Codex's own login file (tokens, ids), read when called: none may enter a trace."""
    found = []

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, str) and len(value) >= 16:
            found.append(value)

    try:
        walk(json.loads((STATE / "codex-home" / "auth.json").read_text()))
    except (OSError, ValueError):
        pass
    return found


class IsolationFlag(RuntimeError):
    """The model did something other than answer (a tool, command, file or web item), or left a file in the
    call's folder. Not a ZendoBench failure: its evidence goes to a flag file in the state folder's `flags/`
    and the run stops (01_play.py)."""

    def __init__(self, message, evidence):
        super().__init__(message)
        flags = STATE / "flags"
        flags.mkdir(parents=True, exist_ok=True)
        path = flags / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}.json"
        path.write_text(json.dumps({"flag": message, **evidence}, indent=1))


def file_sha256(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def text_sha256(text):
    return sha256(text.encode("utf-8")).hexdigest()


def binary():
    """The pinned CLI's native binary, installed by 00_setup.sh into the state folder."""
    found = sorted((STATE / "codex-cli" / "node_modules").glob("@openai/codex-*/vendor/*/bin/codex"))
    if len(found) != 1:
        raise SystemExit(f"Expected one pinned Codex binary under the state folder, found {len(found)}: run 00_setup.py.")
    return found[0]


def environment():
    """The only variables the codex process gets: no API keys, the owner's HOME or TMPDIR."""
    return {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(STATE / "home"), "TMPDIR": str(STATE / "tmp") + "/",
            "CODEX_HOME": str(STATE / "codex-home"), "LANG": "en_US.UTF-8", "NO_COLOR": "1"}


def profile():
    """The sandbox profile with the state folder filled in, written to the state folder; its path and sha256."""
    parents = "\n  ".join(f'(literal "{p}")' for p in [STATE, *STATE.parents] if p != Path("/"))
    text = (HERE / "sandbox.sb").read_text().replace("@PARENTS@", parents).replace("@STATE@", str(STATE))
    path = STATE / "sandbox.sb"
    path.write_text(text)
    return path, text_sha256((HERE / "sandbox.sb").read_text())


def frozen(name):
    """A file 00_setup.sh froze in the state folder, checked against the sha256 it recorded."""
    setup = json.loads((STATE / "setup.json").read_text())
    path = STATE / name
    if file_sha256(path) != setup[name]:
        raise SystemExit(f"{name} in the state folder changed since 00_setup.sh froze it.")
    return path, setup[name]


class CodexBackend(Backend):
    """One model through `codex exec`, tools off (module docstring). Safe to call from many threads."""

    def __init__(self, model, *, effort=EFFORT, summary=SUMMARY, timeout=TIMEOUT, backoff=BACKOFF, trace=None):
        self.model, self.effort, self.summary, self.timeout, self.backoff = model, effort, summary, timeout, backoff
        self.trace_path = None if trace is None else Path(trace)
        self.binary = binary()
        version = subprocess.run([str(self.binary), "--version"], capture_output=True, text=True,
                                 env=environment()).stdout.split()
        if not version or version[-1] != CODEX_VERSION:
            raise SystemExit(f"The pinned Codex is {CODEX_VERSION}; found {' '.join(version)}.")
        self.binary_sha256 = file_sha256(self.binary)
        self.catalog, self.catalog_sha256 = frozen("catalog.json")
        features, self.features_sha256 = frozen("features.json")
        self.disabled = json.loads(features.read_text())
        self.profile, self.profile_sha256 = profile()
        for folder in ("calls", "tmp", "home", "instructions"):
            (STATE / folder).mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.random = random.Random()

    # ------------------------------------------------------------------ the call

    def instructions(self, system):
        """ZendoBench's system prompt (one per tier) as a file Codex reads; its path and sha256."""
        digest = text_sha256(system)
        path = STATE / "instructions" / f"{digest}.txt"
        with self.lock:
            if not path.exists():
                path.write_text(system)
        return path, digest

    def command(self, instructions, folder):
        flags = [x for name in self.disabled for x in ("--disable", name)]
        settings = [*CONFIG, f'model="{self.model}"', f'model_reasoning_effort="{self.effort}"',
                    f'model_reasoning_summary="{self.summary}"', f'model_instructions_file="{instructions}"',
                    f'model_catalog_json="{self.catalog}"']
        return ["/usr/bin/sandbox-exec", "-f", str(self.profile), str(self.binary), "exec", "--ignore-user-config",
                "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "-C", str(folder), "--sandbox", "read-only",
                "--json", *flags, *[x for s in settings for x in ("-c", s)], "-"]

    def call(self, request):
        messages = request.messages
        if [m["role"] for m in messages] != ["system", "user"]:
            raise RuntimeError(f"Expected a system and a user message, got {[m['role'] for m in messages]}.")
        rendered = json.dumps([[m["role"], m["content"]] for m in messages], separators=(",", ":"))
        about = {"decision": request.decision, "episode": request.episode_id, "messages_sha256": text_sha256(rendered)}
        tries = []
        for attempt in range(len(self.backoff) + 1):
            try:
                reply = self._try(messages[0]["content"], messages[1]["content"], dict(about, attempt=attempt))
            except BackendFailure as failure:
                tries.append({"error": str(failure)[:FIELD_CHARS], **failure.record})
                if attempt == len(self.backoff):
                    break
                wait = self.backoff[attempt] * (0.75 + 0.5 * self.random.random())
                tries[-1]["waited"] = round(wait, 1)
                time.sleep(wait)
                continue
            except (GameStopped, UsageLimitReached) as stop:
                if tries:
                    stop.record["retries"] = tries
                raise
            if tries:
                reply.record["retries"] = tries
            return reply
        raise GameStopped(f"Codex retry budget exhausted; the game is unfinished. {tries[-1]['error']}",
                          {"retries": tries, "retry_budget_exhausted": True})

    def _try(self, system, user, about):
        instructions, instructions_sha256 = self.instructions(system)
        folder = Path(tempfile.mkdtemp(prefix="call-", dir=STATE / "calls"))
        trace = {"trace_id": uuid.uuid4().hex, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "model": self.model, "effort": self.effort, **about, "instructions_sha256": instructions_sha256,
                 "prompt_sha256": text_sha256(user)}
        record = {"model": self.model, "effort": self.effort, "instructions_sha256": instructions_sha256,
                  "prompt_sha256": trace["prompt_sha256"], "trace_id": trace["trace_id"]}
        began, done, plain, outcome = time.monotonic(), None, "", "error"
        try:
            try:
                done = subprocess.run(self.command(instructions, folder), input=user, capture_output=True, text=True,
                                      cwd=folder, env=dict(environment(), RUST_LOG=TRACE_TARGET), timeout=self.timeout)
            except subprocess.TimeoutExpired:
                raise BackendFailure(f"Timeout after {self.timeout} s.", dict(record, seconds=self.timeout))
            record["seconds"] = round(time.monotonic() - began, 3)
            plain, trace["server"], trace["server_deltas"] = split(done.stderr)
            left = sorted(p.name for p in folder.iterdir())
            if left:
                raise IsolationFlag(f"The call left {len(left)} file(s) in its folder.",
                                    dict(record, left=left, stdout=done.stdout, stderr=plain[-4000:]))
            reply = self._read(done.stdout, plain, done.returncode, record)
            outcome = "answer" if reply.text is not None else "no answer"
            return reply
        except IsolationFlag:
            outcome = "isolation flag"
            raise
        except UsageLimitReached:
            outcome = "usage limit"
            raise
        except BackendFailure as failure:
            outcome = f"failure: {str(failure)[:FIELD_CHARS]}"
            raise
        finally:
            shutil.rmtree(folder, ignore_errors=True)
            self._trace(dict(trace, outcome=outcome, seconds=round(time.monotonic() - began, 3),
                             exit_code=None if done is None else done.returncode,
                             events=[] if done is None else [parsed(x) for x in done.stdout.splitlines() if x.strip()],
                             stderr=plain.splitlines()))

    def _trace(self, trace):
        """One line of the run part's trace file (module docstring). Never written if a login token is in it."""
        if self.trace_path is None:
            return
        try:
            text = json.dumps(trace, separators=(",", ":"), ensure_ascii=False)
        except (TypeError, ValueError):
            text = json.dumps({k: trace.get(k) for k in ("trace_id", "utc", "outcome")} | {"trace_withheld": "unserialisable"})
        if any(secret in text for secret in login_secrets()):
            text = json.dumps({k: trace.get(k) for k in ("trace_id", "utc", "outcome")} | {"trace_withheld": "credential"})
        with self.lock:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)
            with self.trace_path.open("a") as stream:
                stream.write(text + "\n")

    def _read(self, stdout, stderr, exit_code, record):
        events, unreadable = [], 0
        for line in stdout.splitlines():
            if line.strip():
                try:
                    events.append(json.loads(line))
                except ValueError:
                    unreadable += 1
        kinds = Counter()
        answers, thoughts, notices, other, failed, usage, thread = [], [], [], [], [], None, None
        for event in events:
            kind = event.get("type")
            item = event.get("item") or {}
            kinds[kind if not item else f"{kind}:{item.get('type')}"] += 1
            if kind == "thread.started":
                thread = event.get("thread_id")
            elif kind in ("item.started", "item.updated", "item.completed"):
                if item.get("type") not in (ANSWER, THOUGHT, NOTICE):
                    other.append(event)
                elif kind == "item.completed" and item.get("type") == ANSWER:
                    answers.append(item.get("text") or "")
                elif kind == "item.completed" and item.get("type") == THOUGHT:
                    thoughts.append(item.get("text") or "")
                elif kind == "item.completed" and item.get("type") == NOTICE:
                    notices.append(str(item.get("message") or item.get("text") or "")[:FIELD_CHARS])
            elif kind == "turn.completed":
                usage = event.get("usage")
            elif kind == "turn.failed" or (kind == "error" and not str(event.get("message", "")).startswith("Reconnecting")):
                failed.append(json.dumps(event)[:FIELD_CHARS])
            elif kind == "error":
                notices.append(str(event.get("message"))[:FIELD_CHARS])
        record.update(events=dict(kinds), notices=notices, unreadable_lines=unreadable, thread_id=thread,
                      exit_code=exit_code)
        if other:
            raise IsolationFlag(f"{len(other)} item(s) other than an answer or reasoning: "
                                f"{sorted({(e.get('item') or {}).get('type') for e in other})}.",
                                dict(record, items=other, stderr=stderr[-4000:]))
        problem = " ".join(failed) + " " + stderr[-2000:]
        if any(phrase in problem.lower() for phrase in USAGE_LIMIT):
            raise UsageLimitReached(f"Codex usage limit: {problem.strip()[:300]}", dict(record, failed=failed))
        if failed or exit_code:
            raise BackendFailure(f"Codex call failed (exit {exit_code}): {problem.strip()[:300]}",
                                 dict(record, failed=failed, stderr=stderr[-FIELD_CHARS:]))
        if usage is None:
            raise BackendFailure("Codex turn ended without a usage report.", dict(record, stderr=stderr[-FIELD_CHARS:]))
        if thoughts:
            reasoning = "\n\n".join(thoughts)
            record.update(reasoning=reasoning, reasoning_chars=len(reasoning), reasoning_sha256=text_sha256(reasoning))
        record["agent_messages"] = len(answers)
        text = answers[-1] if answers else None  # the last agent message of the turn is the answer
        text = text or None  # an empty final message is none
        if text is None and not usage.get("output_tokens"):
            raise BackendFailure("Codex turn ended with no answer and no output.", record)
        return Reply(text, FINISH_ACTION if text is not None else FINISH_EOS_IN_THOUGHT, usage, record)

    # ------------------------------------------------------------------ the record

    def describe(self):
        """The settings the run header keeps (no paths, no credentials), in the shape of ZendoBench's Python-backend
        record (`backends.function.FunctionBackend.describe`): `score --verify` and `sft-export` know a run's
        backend by this name (`records.GRAMMARED`), and "function" reads every reply ungrammared, as this
        backend's replies are; the Codex settings are the agent's configuration."""
        return {"backend": "function", "agent": f"{__name__}:{type(self).__qualname__} (codex exec)",
                "agent_source_sha256": SOURCE_SHA256, "per_episode": False,
                "agent_config": self.settings()}

    def settings(self):
        return {"harness": "codex-exec", "codex_cli": CODEX_VERSION, "codex_binary_sha256": self.binary_sha256,
                "model": self.model, "reasoning_effort": self.effort, "reasoning_summary": self.summary,
                "service_tier": "default", "auth": "ChatGPT sign-in, a Codex home of its own",
                "catalog_sha256": self.catalog_sha256, "catalog_edit": CATALOG_EDIT,
                "features_disabled": self.disabled, "features_sha256": self.features_sha256, "config": CONFIG,
                "flags": ["--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
                          "--sandbox read-only", "--json"],
                "sandbox_profile_sha256": self.profile_sha256, "call_folder": "new and empty per call",
                "output_cap": "none settable in Codex (the provider's default)",
                "traces": "every try: Codex's events and the server's messages (deltas counted), beside the run file",
                "timeout": self.timeout, "retries": {"backoff_seconds": self.backoff, "jitter": "x0.75-1.25"}}
