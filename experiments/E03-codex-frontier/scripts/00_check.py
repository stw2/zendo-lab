"""E03 isolation checks, before any game and with no model call. `python 00_check.py` prints each check and exits
non-zero if one fails. Not a measurement; the output goes to results/isolation-check.txt (committed).

1. What the model is shown: `codex debug prompt-input` with the runs' settings lists the user message alone
   (no developer message, environment context, skills or sub-agent role). ZendoBench's system prompt is
   Codex's instructions, which the listing does not show.
2. The sandbox: under sandbox.sb, a process cannot list or read the repositories, run files, the owner's
   ~/.codex, ZendoBench's sealed salt or the temporary folders, and can use the state folder's own parts.
3. The pinned CLI starts under the sandbox.
4. With `--call` (one trivial model call, not a game): the request the server received, from its echo in
   Codex's trace, read in memory and never written (the trace holds the login's tokens): no tools, the arm's
   effort and summary, and the settings Codex sends (verbosity, temperature, top-p, tier, output cap).
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codex_backend import CATALOG_EDIT, CONFIG, STATE, CodexBackend, environment  # noqa: E402

PROBE = "E03 isolation check: the only user message."
HOME = Path.home()
REPO = Path(__file__).resolve().parents[3]


def shown(text):
    """No local paths in the committed output: the repository and its parent by name, the home folder as ~."""
    return (text.replace(str(REPO), "<repository>").replace(str(REPO.parent), "<repository's parent>")
            .replace(str(HOME), "~"))


def sandboxed(profile, *argv):
    return subprocess.run(["/usr/bin/sandbox-exec", "-f", str(profile), *argv], capture_output=True, text=True,
                          cwd=STATE / "calls", env=environment())


def main():
    failures = 0

    def check(name, ok, detail=""):
        nonlocal failures
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {shown(name)}{'  ' + shown(detail) if detail else ''}")

    backend = CodexBackend("gpt-6-luna")
    instructions, _ = backend.instructions("E03 isolation check: the system prompt.")
    exec_argv = backend.command(instructions, STATE / "calls")
    settings = exec_argv[exec_argv.index("--json") + 1:-1]  # the --disable and -c pairs of a run's call
    listing = subprocess.run([str(backend.binary), "debug", "prompt-input", *settings, PROBE], capture_output=True,
                             text=True, cwd=STATE / "calls", env=environment())
    items = json.loads(listing.stdout) if listing.returncode == 0 else []
    texts = [(i.get("role"), [c.get("text") for c in i.get("content", [])]) for i in items]
    check("the model is shown the user message alone", texts == [("user", [PROBE])], json.dumps(texts)[:300])

    profile = backend.profile
    closed = [REPO / "README.md", REPO / "experiments", REPO.parent, HOME / ".codex", HOME / ".zendo-bench-v1.0.0",
              HOME / ".ssh", Path("/private/tmp"), Path("/private/var/folders"), Path("/Users/Shared")]
    for path in closed:
        target = path.parent if not path.exists() else path
        argv = ["/bin/ls", str(target)] if target.is_dir() else ["/bin/cat", str(target)]
        done = sandboxed(profile, *argv)
        check(f"closed: {argv[0].split('/')[-1]} {target}",
              done.returncode != 0 and "Operation not permitted" in done.stderr, done.stderr.strip()[:120])
    for part in ("codex-home", "calls", "tmp", "home"):
        done = sandboxed(profile, "/bin/ls", str(STATE / part))
        check(f"open: the state folder's {part}/", done.returncode == 0, done.stderr.strip()[:120])
    done = sandboxed(profile, str(backend.binary), "--version")
    check("the pinned Codex starts under the sandbox", done.returncode == 0, done.stdout.strip())
    print(f"settings: {len(backend.disabled)} features disabled; config {CONFIG}; catalog edit {CATALOG_EDIT}")
    if "--call" in sys.argv:
        failures += request_check(backend)
    return 1 if failures else 0


def request_check(backend):
    """One trivial call with Codex's trace on; the server's echo of the request (response.completed)."""
    instructions, _ = backend.instructions("E03 request check: answer with one word.")
    folder = Path(tempfile.mkdtemp(prefix="call-", dir=STATE / "calls"))
    done = subprocess.run(backend.command(instructions, folder), input="Say OK.", capture_output=True, text=True,
                          cwd=folder, env=dict(environment(), RUST_LOG="tungstenite::protocol=trace"), timeout=600)
    folder.rmdir()
    echoes = []
    for line in done.stderr.splitlines():
        if "Received message " in line:
            try:
                message = json.loads(line.split("Received message ", 1)[1])
            except ValueError:
                continue
            if message.get("type") == "response.completed" and message["response"].get("generate") is not False:
                echoes.append(message["response"])
    del done  # the trace holds the login's tokens: nothing of it is kept
    if len(echoes) != 1:
        print(f"FAIL  the request check found {len(echoes)} completed responses")
        return 1
    echo = echoes[0]
    fields = {"model": echo.get("model"), "tools": echo.get("tools"), "reasoning": echo.get("reasoning"),
              "text": echo.get("text"), "temperature": echo.get("temperature"), "top_p": echo.get("top_p"),
              "service_tier": echo.get("service_tier"), "max_output_tokens": echo.get("max_output_tokens"),
              "truncation": echo.get("truncation"), "input_tokens": (echo.get("usage") or {}).get("input_tokens")}
    ok = (echo.get("tools") == [] and (echo.get("reasoning") or {}).get("effort") == backend.effort
          and (echo.get("reasoning") or {}).get("summary") == backend.summary)
    print(f"{'PASS' if ok else 'FAIL'}  the server received no tools, effort {backend.effort}, summary "
          f"{backend.summary}  {json.dumps(fields)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
