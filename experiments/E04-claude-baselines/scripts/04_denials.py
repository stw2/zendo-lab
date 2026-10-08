"""Audit Claude sandbox denials since a run part began; unknown denials stop E4.

The allowlist contains reviewed, denied CLI startup/installation probes.
These accesses remain denied; the list grants no filesystem access. No unrelated
experiment is modified by this audit. Reports stay in private results/runs/.
"""
from collections import Counter
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys

from claude_backend import IsolationFlag, STATE

USER_DIR = Path.home()
LINE = re.compile(r"Sandbox: (claude[\w.-]*)\((\d+)\) deny\(\d+\) ([\w-]+)(?: (.*))?$")


def benign(operation, path):
    data = {USER_DIR / ".CFUserTextEncoding", USER_DIR, USER_DIR / ".gitconfig", STATE,
            USER_DIR / ".cache/claude/staging", USER_DIR / ".local/share/claude/versions",
            USER_DIR / ".local/state/claude/locks"}
    metadata = {*STATE.parents, USER_DIR / "Library", USER_DIR / "Library/Keychains/login.keychain-db",
                USER_DIR / ".config/git/ignore"}
    return ((operation == "file-read-data" and Path(path) in data)
            or (operation == "file-read-metadata" and Path(path) in metadata)
            or (operation == "forbidden-exec-sugid" and not path))


def trace_pids(path):
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as stream:
        return {row["value"]["pid"] for line in stream
                if (row := json.loads(line))["kind"] == "spawned"}


def classify(lines, pids):
    seen, flagged = Counter(), Counter()
    unrelated = 0
    for line in lines:
        match = LINE.search(line)
        if match:
            process, pid, operation, path = match.groups()
            if int(pid) not in pids:
                unrelated += 1
                continue
            path = path or ""
            key = (process, operation, path.replace(str(USER_DIR), "~"))
            (seen if benign(operation, path) else flagged)[key] += 1
    return {"process_scope": "recorded E4 CLI PIDs", "process_count": len(pids),
            "unrelated_denials": unrelated, "benign": [[*k, n] for k, n in sorted(seen.items())],
              "flagged": [[*k, n] for k, n in sorted(flagged.items())]}


def main():
    since, trace = sys.argv[1:]
    pids = trace_pids(trace)
    done = subprocess.run(["/usr/bin/log", "show", "--start", since, "--style", "compact", "--predicate",
                           'sender == "Sandbox" AND eventMessage CONTAINS "claude"'],
                          capture_output=True, text=True, check=True)
    report = {"since": since, **classify(done.stdout.splitlines(), pids)}
    print(json.dumps(report, indent=2))
    if report["flagged"]:
        raise IsolationFlag("Unexpected sandbox denial; inspect private audit", report)


if __name__ == "__main__":
    main()
