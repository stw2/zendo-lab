"""Offline preflight: real CLI and sandbox, mock API only; no model measurements."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import claude_backend as cb

from claude_backend import ClaudeBackend, CLI_SHA256, CLI_VERSION, MODELS, SDK_IDENTITY, THINKING, STATE, digest, profile


def main():
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trace = root / "results/runs/preflight" / f"offline-{stamp}.jsonl"
    sandbox, _ = profile()
    # Native OAuth refresh locks the dedicated config directory via this sibling.
    # This exact runtime path is writable; repository access remains denied below.
    config_lock = STATE / "config.lock"
    if config_lock.exists():
        raise RuntimeError("Dedicated config lock already exists; do not disturb a live login")
    lock = subprocess.run(["/usr/bin/sandbox-exec", "-f", str(sandbox), "/bin/mkdir", str(config_lock)],
                          capture_output=True)
    if lock.returncode:
        raise RuntimeError("Sandbox denied isolated authentication lock creation")
    unlock = subprocess.run(["/usr/bin/sandbox-exec", "-f", str(sandbox), "/bin/rmdir", str(config_lock)],
                            capture_output=True)
    if unlock.returncode:
        raise RuntimeError("Sandbox denied isolated authentication lock removal")
    # Known harmless files outside the runtime: only their denied exit status is read.
    read = subprocess.run(["/usr/bin/sandbox-exec", "-f", str(sandbox), "/bin/cat", str(root / "DESIGN.md")],
                          capture_output=True)
    if read.returncode == 0:
        raise RuntimeError("Sandbox allowed repository data access")
    with tempfile.TemporaryDirectory(prefix="e04-sandbox-") as folder:
        target = Path(folder) / "denied"
        write = subprocess.run(["/usr/bin/sandbox-exec", "-f", str(sandbox), "/usr/bin/touch", str(target)],
                               capture_output=True)
        if write.returncode == 0 or target.exists():
            raise RuntimeError("Sandbox allowed unrelated temporary-file write")
    rows = []
    for model in MODELS:
        backend = ClaudeBackend(model, trace=trace, offline=True, timeout=60, backoff=[])
        reply = backend._try("E4 system probe. Answer with OK.", "E4 user probe.",
                             {"attempt": 0, "episode": "offline", "decision": 0})
        assert reply.text == "OK" and reply.record["reasoning"] == "Offline fixture."
        assert reply.record["requests"] == 1 and reply.record["stop_reason"] == "end_turn"
        backend.close()
        rows.append({"model": model, "benchmark_messages_unchanged": True, "sdk_identity": SDK_IDENTITY,
                     "other_prompt_additions": False, "tools": [], "effort": "high",
                     "thinking": THINKING, "max_tokens": 128000, "stream_reconstruction": True})
    # Exercise the native CLI's attempted continuation, not just a parser fixture.
    original = cb.mock_response
    def tool_stop_fixture(model):
        return [chunk.replace(b'"stop_reason": "end_turn"', b'"stop_reason": "tool_use"')
                for chunk in original(model)]
    cb.mock_response = tool_stop_fixture
    try:
        backend = ClaudeBackend(MODELS[0], trace=trace, offline=True, timeout=60, backoff=[])
        reply = backend._try("E4 system probe. Answer with OK.", "E4 user probe.",
                             {"attempt": 0, "episode": "offline-continuation", "decision": 0})
        assert reply.text == "OK" and reply.record["requests"] == 1
        assert reply.record["stop_reason"] == "tool_use"
        assert reply.record["continuations_blocked"] >= 1
        backend.close()
    finally:
        cb.mock_response = original
    # A real CLI stream-recovery request must stop at the guard and become a
    # wrapper-retryable infrastructure failure, never another provider request.
    def stream_error_fixture(model):
        error = {"type": "error", "error": {"type": "api_error", "message": "Internal server error"}}
        return [*original(model)[:-2], ("event: error\ndata: " + json.dumps(error) + "\n\n").encode()]
    cb.mock_response = stream_error_fixture
    try:
        backend = ClaudeBackend(MODELS[0], trace=trace, offline=True, timeout=60, backoff=[])
        try:
            backend._try("E4 system probe. Answer with OK.", "E4 user probe.",
                         {"attempt": 0, "episode": "offline-stream-error", "decision": 0})
        except cb.BackendFailure as failure:
            assert failure.record["requests"] == 1
            assert failure.record["recoveries_blocked"] >= 1
        else:
            raise RuntimeError("Incomplete provider response was treated as an answer")
        finally:
            backend.close()
    finally:
        cb.mock_response = original
    report = {"utc": stamp, "offline_only": True, "claude_cli": CLI_VERSION,
              "claude_binary_sha256": CLI_SHA256, "repository_read_denied": True,
              "unrelated_write_denied": True, "models": rows,
              "cli_continuation_blocked_without_resampling": True,
              "provider_stream_recovery_blocked_and_retryable": True,
              "isolated_auth_lock_create_remove_allowed": True,
              "private_trace_sha256": digest(trace.read_bytes())}
    (root / "results/isolation-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
