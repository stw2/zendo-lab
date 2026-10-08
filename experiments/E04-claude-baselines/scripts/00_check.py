"""Offline preflight: real CLI and sandbox, mock API only; no model measurements."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile

from claude_backend import ClaudeBackend, CLI_SHA256, CLI_VERSION, MODELS, SDK_IDENTITY, STATE, digest, profile


def main():
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trace = root / "results/runs/preflight" / f"offline-{stamp}.jsonl"
    sandbox, _ = profile()
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
                     "thinking": "adaptive", "max_tokens": 128000, "stream_reconstruction": True})
    report = {"utc": stamp, "offline_only": True, "claude_cli": CLI_VERSION,
              "claude_binary_sha256": CLI_SHA256, "repository_read_denied": True,
              "unrelated_write_denied": True, "models": rows,
              "private_trace_sha256": digest(trace.read_bytes())}
    (root / "results/isolation-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
