"""Audit Claude sandbox denials since a run part began; unknown denials stop E4.

The allowlist contains denied startup probes observed with only the offline fixture.
These accesses remain denied; the list grants no filesystem access. No unrelated
experiment is modified by this audit. Reports stay in private results/runs/.
"""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

from claude_backend import IsolationFlag, STATE

USER_DIR = Path.home()
LINE = re.compile(r"Sandbox: (claude[\w.-]*)\((\d+)\) deny\(\d+\) ([\w-]+)(?: (.*))?$")


def benign(operation, path):
    data = {USER_DIR / ".CFUserTextEncoding", USER_DIR, USER_DIR / ".gitconfig", STATE}
    metadata = {*STATE.parents, USER_DIR / "Library", USER_DIR / "Library/Keychains/login.keychain-db",
                USER_DIR / ".config/git/ignore"}
    return ((operation == "file-read-data" and Path(path) in data)
            or (operation == "file-read-metadata" and Path(path) in metadata)
            or (operation == "forbidden-exec-sugid" and not path))


def main():
    since = sys.argv[1]
    done = subprocess.run(["/usr/bin/log", "show", "--start", since, "--style", "compact", "--predicate",
                           'sender == "Sandbox" AND eventMessage CONTAINS "claude"'],
                          capture_output=True, text=True, check=True)
    seen, flagged = Counter(), Counter()
    for line in done.stdout.splitlines():
        match = LINE.search(line)
        if match:
            process, pid, operation, path = match.groups()
            path = path or ""
            key = (process, operation, path.replace(str(USER_DIR), "~"))
            (seen if benign(operation, path) else flagged)[key] += 1
    report = {"since": since, "benign": [[*k, n] for k, n in sorted(seen.items())],
              "flagged": [[*k, n] for k, n in sorted(flagged.items())]}
    print(json.dumps(report, indent=2))
    if flagged:
        raise IsolationFlag("Unexpected sandbox denial; inspect private audit", report)


if __name__ == "__main__":
    main()
