"""Installation probes remain denied, while unexpected E4 accesses still flag."""
import gzip
import importlib.util
import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "experiments/E04-claude-baselines/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("e04_denials", SCRIPTS / "04_denials.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_installation_exception_is_exact_and_read_only():
    for relative in (".cache/claude/staging", ".local/share/claude/versions", ".local/state/claude/locks"):
        path = audit.USER_DIR / relative
        assert audit.benign("file-read-data", str(path))
        assert not audit.benign("file-read-data", str(path / "private-file"))
        assert not audit.benign("file-write-data", str(path))


def test_unexpected_e4_read_flags_but_other_process_is_not_attributed():
    lines = [f"Sandbox: claude({pid}) deny(1) file-read-data /private/example" for pid in (101, 202)]
    report = audit.classify(lines, {101})
    assert report["flagged"] == [["claude", "file-read-data", "/private/example", 1]]
    assert report["unrelated_denials"] == 1


def test_pid_scope_comes_from_plain_or_compressed_trace(tmp_path):
    text = "\n".join(json.dumps(row) for row in (
        {"kind": "start", "value": {"pid": 999}},
        {"kind": "spawned", "value": {"pid": 101}},
        {"kind": "spawned", "value": {"pid": 202}},
    )) + "\n"
    plain = tmp_path / "trace.jsonl"
    plain.write_text(text)
    zipped = tmp_path / "trace.jsonl.gz"
    with gzip.open(zipped, "wt") as stream:
        stream.write(text)
    assert audit.trace_pids(plain) == audit.trace_pids(zipped) == {101, 202}
