"""Stateless, tool-free Claude CLI calls for the unmodified ZendoBench runner.

The CLI's documented EXTRA_BODY setting substitutes unchanged benchmark messages
plus the fixed SDK identity sentence documented in DESIGN.md's amendments.
A local forwarding guard checks every inference request BEFORE sending its unchanged
bytes to Anthropic. Authentication headers are forwarded only to api.anthropic.com
and never recorded. Every request, response stream, CLI event and stderr line is
written incrementally to a private trace, including failed and interrupted tries.
"""
from __future__ import annotations

from hashlib import sha256
import http.client
import http.server
import json
import os
from pathlib import Path
import random
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit
import uuid

from zendo_bench.backends.base import (
    Backend, BackendFailure, FINISH_ACTION, FINISH_EOS_IN_THOUGHT,
    FINISH_CUT_IN_ACTION, FINISH_CUT_IN_THOUGHT,
    GameStopped, Reply, UsageLimitReached,
)

HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get("E04_STATE", Path.home() / ".cache/zendo-lab/e04-claude"))
CLI_VERSION = "2.1.293"
CLI_SHA256 = "4e21122a227857da1178aca3299700c1fd7f2b77c93f12e73c2c76db796a105e"
SOURCE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1")
ARMS = {f"{model}-claude-high": model for model in MODELS}
TIMEOUT = 3600
BACKOFF = [30, 60, 120, 300, 900]
MAX_OUTPUT = 128000
SDK_IDENTITY = "You are a Claude agent, built on Anthropic's Claude Agent SDK."
THINKING = {"type": "adaptive", "display": "summarized"}
SETTINGS = {"disableAllHooks": True, "showThinkingSummaries": True, "ultracode": False,
            "autoMemoryEnabled": False, "fastMode": False}
FLAGS = ["--safe-mode", "--restricted", "--setting-sources", "",
         "--settings", json.dumps(SETTINGS, separators=(",", ":")),
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
         "--tools", "", "--disallowedTools", "*", "--disable-slash-commands",
         "--no-chrome", "--no-session-persistence", "--permission-prompts", "none",
         "--effort", "high", "--output-format", "stream-json", "--verbose",
         "--include-partial-messages", "--max-turns", "1"]


def digest(value):
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def environment():
    # An allowlist: no inherited keys, proxy settings, model overrides, or customizations.
    return {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8", "NO_COLOR": "1",
            "CLAUDE_CONFIG_DIR": str(STATE / "config"), "TMPDIR": str(STATE / "tmp") + "/",
            "CLAUDE_CODE_TMPDIR": str(STATE / "tmp"), "DISABLE_AUTOUPDATER": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL": "1",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
            "CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS": "1", "CLAUDE_CODE_DISABLE_CRON": "1",
            "CLAUDE_CODE_AUTO_CONNECT_IDE": "false", "ENABLE_CLAUDEAI_MCP_SERVERS": "false",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1", "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
            "CLAUDE_CODE_MAX_RETRIES": "0", "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(MAX_OUTPUT),
            "CLAUDE_CODE_EFFORT_LEVEL": "high", "API_TIMEOUT_MS": str(TIMEOUT * 1000)}


def profile():
    template = (HERE / "sandbox.sb").read_text()
    parents = "\n  ".join(f'(literal "{p}")' for p in [STATE, *STATE.parents] if p != Path("/"))
    path = STATE / "sandbox.sb"
    path.write_text(template.replace("@PARENTS@", parents).replace("@STATE@", str(STATE)))
    return path, digest(template)


class IsolationFlag(RuntimeError):
    def __init__(self, message, record=None):
        path = STATE / "flags" / f"{uuid.uuid4().hex}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"flag": message, "record": record or {}}, indent=2) + "\n")
        super().__init__(message)


def validate_request(body, model, system, user):
    """A discrepancy stops inference; no silent fallback, prompt addition or tool."""
    expected = {"model": model, "system": [{"type": "text", "text": SDK_IDENTITY},
                                          {"type": "text", "text": system}],
                "messages": [{"role": "user", "content": user}], "tools": [],
                "max_tokens": MAX_OUTPUT, "thinking": THINKING,
                "output_config": {"effort": "high"}, "stream": True}
    differences = [key for key, value in expected.items() if body.get(key) != value]
    # Unexpected sampling/grammar settings change the experiment. Provider defaults apply.
    differences += [key for key in ("temperature", "top_p", "top_k", "tool_choice", "stop_sequences")
                    if key in body]
    allowed = set(expected) | {"metadata", "context_management", "safeguards"}
    differences += sorted(set(body) - allowed - set(differences))
    if differences:
        raise ValueError("Request differs from protocol: " + ", ".join(differences))


class Trace:
    """Append-only, flushed records. A trace write failure aborts the call."""
    locks = {}
    locks_lock = threading.Lock()

    def __init__(self, path, trace_id):
        self.path, self.trace_id = Path(path), trace_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.locks_lock:
            self.lock = self.locks.setdefault(str(self.path.resolve()), threading.Lock())
        self.secrets = set()
        self.error = None

    def write(self, kind, value):
        with self.lock:
            text = json.dumps({"trace_id": self.trace_id, "kind": kind, "time": time.time(),
                               "value": value}, ensure_ascii=False, separators=(",", ":"))
            for secret in self.secrets:
                if secret:
                    text = text.replace(secret, "[credential redacted]")
            text = re.sub(r"(?i)Bearer [A-Za-z0-9_.~-]+", "Bearer [redacted]", text)
            try:
                with self.path.open("a") as stream:
                    stream.write(text + "\n")
                    stream.flush()
            except BaseException as error:
                self.error = error
                raise


class Guard:
    """One call, one loopback endpoint, fixed upstream. No credentials are logged."""
    def __init__(self, model, system, user, trace, *, offline=False):
        self.model, self.system, self.user, self.trace = model, system, user, trace
        self.offline = offline
        self.failure = None
        self.requests = 0
        self.responses = []
        self.events = []
        self.response_complete = threading.Event()
        self.continuations_blocked = 0
        self.recoveries_blocked = 0
        self.transport_failed = False
        self.condition = threading.Condition()
        self.connections = set()
        self.active_handlers = 0
        self.prefix = "/" + uuid.uuid4().hex
        guard = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_error(403, "E4 permits only its single inference request")

            def do_POST(self):
                connection = None
                with guard.condition:
                    guard.active_handlers += 1
                try:
                    path = urlsplit(self.path)
                    if path.path != guard.prefix + "/v1/messages":
                        raise ValueError("Unexpected API path")
                    raw = self.rfile.read(int(self.headers["Content-Length"]))
                    body = json.loads(raw)
                    with guard.trace.lock:
                        for name in ("authorization", "x-api-key"):
                            if self.headers.get(name):
                                guard.trace.secrets.add(self.headers[name])
                                guard.trace.secrets.add(self.headers[name].removeprefix("Bearer "))
                    if guard.requests:
                        if guard.response_complete.is_set():
                            guard.continuations_blocked += 1
                            guard.trace.write("continuation_blocked", {"body": body,
                                               "reason": "first API response already complete; no repair/resampling"})
                            self.send_error(409, "E4 returns only the first model response")
                            return
                        reason = guard.recovery_reason()
                        if reason:
                            guard.recoveries_blocked += 1
                            guard.trace.write("recovery_blocked", {"body": body, "reason": reason})
                            self.send_error(409, "E4 retries provider failures in a fresh call; no CLI recovery")
                            return
                        raise ValueError("CLI attempted a second inference request in one decision")
                    validate_request(body, guard.model, guard.system, guard.user)
                    guard.requests += 1
                    guard.trace.write("request", {"body": body, "body_sha256": digest(raw),
                                                  "path": "/v1/messages", "sequence": guard.requests,
                                                  "anthropic_beta": self.headers.get("anthropic-beta")})
                    if guard.offline:
                        chunks = mock_response(guard.model)
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Content-Length", str(sum(map(len, chunks))))
                        self.end_headers()
                        for chunk in chunks:
                            guard.trace.write("provider_stream", chunk.decode())
                            guard.observe(chunk.decode())
                            self.wfile.write(chunk)
                        return
                    # Do not allow CLI redirects, arbitrary upstreams or auth headers in traces.
                    connection = http.client.HTTPSConnection("api.anthropic.com", timeout=TIMEOUT)
                    with guard.condition:
                        guard.connections.add(connection)
                    headers = {k: v for k, v in self.headers.items()
                               if k.lower() not in ("host", "connection", "transfer-encoding", "accept-encoding")}
                    headers["Accept-Encoding"] = "identity"
                    connection.request("POST", "/v1/messages" + ("?" + path.query if path.query else ""),
                                       body=raw, headers=headers)
                    response = connection.getresponse()
                    guard.responses.append(response.status)
                    guard.trace.write("provider_status", {"status": response.status,
                                      "request_id": response.getheader("request-id"),
                                      "content_type": response.getheader("content-type"),
                                      "retry_after": response.getheader("retry-after"),
                                      "rate_limit_headers": {k: v for k, v in response.getheaders()
                                                             if "ratelimit" in k.lower()}})
                    self.send_response(response.status)
                    for k, v in response.getheaders():
                        if k.lower() in ("content-type", "content-length", "retry-after", "request-id"):
                            self.send_header(k, v)
                    self.send_header("Connection", "close")
                    self.end_headers()
                    # readline preserves all SSE bytes, including partial events on EOF.
                    while chunk := response.readline():
                        guard.trace.write("provider_stream", chunk.decode("utf-8", errors="replace"))
                        guard.observe(chunk.decode("utf-8", errors="replace"))
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    self.close_connection = True
                except (ValueError, KeyError) as error:
                    guard.failure = str(error)
                    guard.trace.write("guard_rejected", {"error": str(error)})
                    self.send_error(403, "E4 request rejected by protocol guard")
                except BaseException as error:
                    # Transport failure is retryable; a failed trace write is not.
                    if isinstance(error, (OSError, http.client.HTTPException)):
                        guard.transport_failed = True
                    guard.trace.write("proxy_error", {"type": type(error).__name__, "error": str(error)})
                    self.close_connection = True
                finally:
                    if connection is not None:
                        connection.close()
                    with guard.condition:
                        guard.connections.discard(connection)
                        guard.active_handlers -= 1
                        guard.condition.notify_all()

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def recovery_reason(self):
        """Only observed infrastructure failures qualify; no request is forwarded."""
        if self.response_complete.is_set():
            return None
        if self.responses and (self.responses[-1] in (401, 429) or self.responses[-1] >= 500):
            return f"provider HTTP {self.responses[-1]} before a complete response"
        if any(event.get("type") == "error" for event in self.events):
            return "provider emitted a streaming error before a complete response"
        if self.transport_failed:
            return "provider transport failed before a complete response"
        return None

    def observe(self, text):
        for line in text.splitlines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                self.events.append(event)
                if event.get("type") == "message_stop":
                    self.response_complete.set()

    def __enter__(self):
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_port}{self.prefix}"

    def __exit__(self, *args):
        self.server.shutdown()
        # A killed CLI does not necessarily wake a proxy thread blocked on the
        # provider's next SSE event. Close that socket and join the handlers
        # before the trace's final end row or compression can happen.
        with self.condition:
            connections = list(self.connections)
        for connection in connections:
            if connection.sock is not None:
                try:
                    connection.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            connection.close()
        with self.condition:
            if not self.condition.wait_for(lambda: self.active_handlers == 0, timeout=10):
                raise IsolationFlag("Proxy stream failed to finalize before trace close")
        self.server.server_close()
        self.thread.join()


def mock_response(model):
    """Protocol fixture, never a model result; used only by offline preflight."""
    events = [
        {"type": "message_start", "message": {"id": "msg_e04_offline", "type": "message",
         "role": "assistant", "model": model, "content": [], "stop_reason": None,
         "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 0}}},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "Offline fixture."}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "signature_delta", "signature": "fixture"}},
        {"type": "content_block_stop", "index": 0},
        {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "OK"}},
        {"type": "content_block_stop", "index": 1},
        {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
         "usage": {"output_tokens": 2}},
        {"type": "message_stop"},
    ]
    return [("event: " + event["type"] + "\ndata: " + json.dumps(event) + "\n\n").encode() for event in events]


def read_reply(events, stderr, exit_code, record, model, *, provider_events=None):
    init = [e for e in events if e.get("type") == "system" and e.get("subtype") == "init"]
    results = [e for e in events if e.get("type") == "result"]
    messages = [e["message"] for e in events if e.get("type") == "assistant" and "message" in e]
    for event in init:
        if event.get("tools") or event.get("mcp_servers") or event.get("skills") or event.get("slash_commands"):
            raise IsolationFlag("CLI initialized tools or customizations", record)
        if event.get("model") != model or event.get("claude_code_version") != CLI_VERSION:
            raise IsolationFlag("CLI model or version changed", record)
    for message in messages:
        if message.get("model") == "<synthetic>":
            continue
        if message.get("model") != model:
            raise IsolationFlag("Response model differs from requested model", record)
        if any(c.get("type") not in ("text", "thinking", "redacted_thinking") for c in message.get("content", [])):
            raise IsolationFlag("Assistant emitted a non-text/thinking block", record)
    for event in events:
        if event.get("type") == "stream_event":
            block = event.get("event", {}).get("content_block", {})
            if block and block.get("type") not in ("text", "thinking", "redacted_thinking"):
                raise IsolationFlag("Assistant streamed a tool or other unexpected block", record)
    result = results[-1] if results else {}
    if result.get("permission_denials") or result.get("subagent_stats", {}).get("spawned", 0):
        raise IsolationFlag("CLI attempted a tool or delegated", record)
    problem = " ".join(str(e.get("result", "")) for e in results) + " " + stderr[-2000:]
    complete_provider = provider_events is not None and any(e.get("type") == "message_stop" for e in provider_events)
    lowered = problem.lower()
    quota = any(term in lowered for term in ("usage limit", "usage_limit", "hit your limit", "weekly limit"))
    if not complete_provider and quota and "not your usage limit" not in lowered:
        raise UsageLimitReached("Claude subscription limit", record)
    if not complete_provider and (exit_code or not result or result.get("is_error") or result.get("terminal_reason") == "api_error"):
        raise BackendFailure(f"Claude call failed (exit {exit_code}): {problem[:500]}", record)
    if len(init) != 1 or (not complete_provider and len(results) != 1):
        raise BackendFailure("Missing or duplicate CLI init/result", record)
    # The pinned CLI emits one assistant event per completed content block, not
    # one per API message. Reconstruct the canonical message from raw API events.
    stream = provider_events if provider_events is not None else [e["event"] for e in events if e.get("type") == "stream_event"]
    if any(e.get("type") == "error" for e in stream):
        raise BackendFailure("Provider emitted a streaming error", record)
    starts = [e["message"] for e in stream if e.get("type") == "message_start"]
    if len(starts) != 1 or sum(e.get("type") == "message_stop" for e in stream) != 1:
        raise BackendFailure("Expected one complete streamed API message", record)
    message = dict(starts[0])
    if message.get("model") != model:
        raise IsolationFlag("Streamed response model differs from requested model", record)
    blocks = {}
    for event in stream:
        kind = event.get("type")
        if kind == "content_block_start":
            if event["content_block"].get("type") not in ("text", "thinking", "redacted_thinking"):
                raise IsolationFlag("Provider emitted an actual tool or other unexpected block", record)
            blocks[event["index"]] = dict(event["content_block"])
        elif kind == "content_block_delta":
            delta = event["delta"]
            field = {"text_delta": "text", "thinking_delta": "thinking", "signature_delta": "signature"}.get(delta["type"])
            if field is None or event["index"] not in blocks:
                raise IsolationFlag("Unexpected streamed content delta", record)
            block = blocks[event["index"]]
            block[field] = block.get(field, "") + delta.get(field, "")
        elif kind == "message_delta":
            message.update(event.get("delta", {}))
            message["usage"] = {**message.get("usage", {}), **event.get("usage", {})}
    contents = [blocks[i] for i in sorted(blocks)]
    answer = "".join(c.get("text", "") for c in contents if c.get("type") == "text") or None
    thoughts = "\n\n".join(c.get("thinking", "") for c in contents if c.get("type") == "thinking")
    record.update(stop_reason=message.get("stop_reason"), terminal_reason=result.get("terminal_reason"),
                  reasoning=thoughts, reasoning_sha256=digest(thoughts),
                  redacted_thinking_blocks=sum(c.get("type") == "redacted_thinking" for c in contents),
                  response_model=message.get("model"), exit_code=exit_code)
    if not answer and not thoughts and not message.get("usage", {}).get("output_tokens"):
        raise BackendFailure("Claude returned no answer and no output", record)
    if message.get("stop_reason") == "max_tokens":
        finish = FINISH_CUT_IN_ACTION if answer else FINISH_CUT_IN_THOUGHT
    else:
        finish = FINISH_ACTION if answer else FINISH_EOS_IN_THOUGHT
    return Reply(answer, finish, message.get("usage", {}), record)


class ClaudeBackend(Backend):
    def __init__(self, model, *, trace, timeout=TIMEOUT, backoff=BACKOFF, offline=False):
        if model not in MODELS:
            raise ValueError("Use an explicit E4 model ID")
        self.model, self.trace_path = model, Path(trace)
        self.timeout, self.backoff, self.offline = timeout, backoff, offline
        self.binary = STATE / "bin/claude"
        if digest(self.binary.read_bytes()) != CLI_SHA256:
            raise RuntimeError("Pinned Claude binary differs: run 00_setup.py")
        self.profile, self.profile_sha256 = profile()
        self.lock = threading.Lock()
        self.condition = threading.Condition()
        self.running = 0
        self.processes = set()
        self.closing = threading.Event()

    def call(self, request):
        with self.condition:
            if self.closing.is_set():
                raise GameStopped("Run is stopping")
            self.running += 1
        try:
            return self._call(request)
        finally:
            with self.condition:
                self.running -= 1
                self.condition.notify_all()

    def _call(self, request):
        messages = request.messages
        if [m["role"] for m in messages] != ["system", "user"]:
            raise ValueError("Expected benchmark system and user messages")
        about = {"decision": request.decision, "episode": request.episode_id,
                 "messages_sha256": digest(json.dumps([[m["role"], m["content"]] for m in messages],
                                                       separators=(",", ":")))}
        tries = []
        for attempt in range(len(self.backoff) + 1):
            try:
                reply = self._try(messages[0]["content"], messages[1]["content"], dict(about, attempt=attempt))
            except BackendFailure as error:
                tries.append({"error": str(error)[:500], **error.record})
                if attempt < len(self.backoff):
                    delay = self.backoff[attempt] * random.uniform(.75, 1.25)
                    tries[-1]["waited"] = round(delay, 1)
                    if self.closing.wait(delay):
                        raise GameStopped("Run stopped during retry wait", {"retries": tries})
                    continue
                raise GameStopped("Claude retry budget exhausted; game unfinished", {"retries": tries}) from error
            except (GameStopped, UsageLimitReached) as stop:
                stop.record["retries"] = tries
                raise
            reply.record["retries"] = tries
            return reply

    def _try(self, system, user, about):
        trace_id = uuid.uuid4().hex
        trace = Trace(self.trace_path, trace_id)
        record = {"trace_id": trace_id, "model": self.model, "effort": "high",
                  "instructions_sha256": digest(system), "prompt_sha256": digest(user)}
        trace.write("start", {**record, **about, "system": system, "user": user,
                              "offline_fixture": self.offline})
        folder = Path(tempfile.mkdtemp(prefix="call-", dir=STATE / "calls"))
        instructions = STATE / "instructions" / (digest(system) + ".txt")
        with self.lock:
            if not instructions.exists():
                instructions.write_text(system)
        guard = Guard(self.model, system, user, trace, offline=self.offline)
        events, stderr, errors = [], [], []
        process = None
        outcome = "interrupted"
        began = time.monotonic()

        def drain(pipe, kind):
            try:
                for line in pipe:
                    if kind == "stdout":
                        try:
                            event = json.loads(line)
                            if not isinstance(event, dict):
                                raise ValueError("non-object event")
                            events.append(event)
                        except ValueError:
                            errors.append("unparseable stdout")
                    else:
                        stderr.append(line)
                    trace.write(kind, line)
            except BaseException as error:
                errors.append(str(error))
                if process is not None:
                    process.kill()

        try:
            with guard as endpoint:
                env = environment()
                env["ANTHROPIC_BASE_URL"] = endpoint
                env["CLAUDE_CODE_EXTRA_BODY"] = json.dumps({
                    "system": [{"type": "text", "text": SDK_IDENTITY}, {"type": "text", "text": system}],
                    "messages": [{"role": "user", "content": user}], "thinking": THINKING}, separators=(",", ":"))
                if self.offline:
                    env["ANTHROPIC_API_KEY"] = "offline-placeholder"
                command = ["/usr/bin/sandbox-exec", "-f", str(self.profile), str(self.binary), *FLAGS,
                           "--model", self.model, "--system-prompt-file", str(instructions), "-p"]
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, cwd=folder, env=env,
                                           start_new_session=True)
                with self.condition:
                    self.processes.add(process)
                    if self.closing.is_set():
                        os.killpg(process.pid, signal.SIGKILL)
                trace.write("spawned", {"pid": process.pid})
                threads = [threading.Thread(target=drain, args=(pipe, kind), daemon=True)
                           for pipe, kind in ((process.stdout, "stdout"), (process.stderr, "stderr"))]
                for thread in threads:
                    thread.start()
                process.stdin.write(user)
                process.stdin.close()
                try:
                    process.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise BackendFailure("Claude call timed out", record)
                finally:
                    for thread in threads:
                        thread.join(timeout=10)
                    if any(thread.is_alive() for thread in threads):
                        errors.append("stream reader did not finish")
                record.update(seconds=round(time.monotonic() - began, 3), requests=guard.requests,
                              response_statuses=guard.responses, continuations_blocked=guard.continuations_blocked,
                              recoveries_blocked=guard.recoveries_blocked)
                if trace.error or errors:
                    raise IsolationFlag("Incomplete transcript: " + "; ".join(errors), record)
                if guard.failure:
                    raise IsolationFlag(guard.failure, record)
                if list(folder.iterdir()):
                    raise IsolationFlag("Claude wrote into the empty call directory", record)
                reply = read_reply(events, "".join(stderr), process.returncode, record, self.model,
                                   provider_events=guard.events)
                if guard.requests != 1:
                    raise IsolationFlag("Expected one guarded request per decision", record)
                outcome = "answer" if reply.text else "no_answer"
                return reply
        except BaseException as error:
            outcome = type(error).__name__ + ": " + str(error)[:500]
            raise
        finally:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            with self.condition:
                self.processes.discard(process)
            trace.write("end", {"outcome": outcome, "seconds": round(time.monotonic() - began, 3),
                                "exit_code": None if process is None else process.returncode})
            shutil.rmtree(folder, ignore_errors=True)

    def close(self):
        # ZendoBench's threaded driver abandons in-flight threads on a stop. Stop
        # our CLI processes and wait for their trace finalizers before it exits.
        self.closing.set()
        with self.condition:
            for process in self.processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
            if not self.condition.wait_for(lambda: self.running == 0, timeout=30):
                raise IsolationFlag("In-flight trace finalization did not finish")
        return {"active_calls": 0, "traces_finalized": True}

    def describe(self):
        return {"backend": "function", "agent": f"{__name__}:{type(self).__qualname__} (claude -p)",
                "agent_source_sha256": SOURCE_SHA256, "per_episode": False, "agent_config": self.settings()}

    def settings(self):
        return {"harness": "claude-print", "claude_cli": CLI_VERSION, "claude_binary_sha256": CLI_SHA256,
                "model": self.model, "reasoning_effort": "high", "thinking": THINKING,
                "show_thinking_summaries": True, "max_tokens": MAX_OUTPUT,
                "sampling": "provider defaults; temperature, top_p, top_k omitted",
                "auth": "Claude subscription; dedicated configuration and login",
                "flags": FLAGS, "sandbox_profile_sha256": self.profile_sha256,
                "prompt_substitution": "CLAUDE_CODE_EXTRA_BODY; unchanged benchmark messages plus fixed SDK identity",
                "sdk_identity": SDK_IDENTITY,
                "request_guard": "loopback capture; validate before forwarding unchanged bytes to Anthropic",
                "response_policy": "first complete API response, unchanged; block all CLI continuations/repairs",
                "traces": "incremental requests, full provider and CLI streams, stderr, every try",
                "timeout": self.timeout, "retries": {"backoff_seconds": self.backoff, "jitter": "x0.75-1.25"}}
