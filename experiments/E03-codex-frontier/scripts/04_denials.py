"""E03: the sandbox's denials for codex processes since a time, from the system log. A denial other than
Codex's own startup (below) raises an isolation flag (a flag file in the state folder's flags/, exit 5).

`python 04_denials.py "YYYY-MM-DD HH:MM:SS"` (local time; 01_run.sh passes each part's start).

Benign, seen when the pinned CLI starts under the sandbox with no model call (00_check.py):
- CoreFoundation reading ~/.CFUserTextEncoding (it reads the account's home, not $HOME);
- metadata reads of the state folder's parent folders (/Users, the home folder, ~/.cache, ~/.cache/zendo-lab),
  as a path to the state folder is resolved.
"""

from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codex_backend import STATE  # noqa: E402

HOME = Path.home()
LINE = re.compile(r"Sandbox: (codex[\w.-]*)\((\d+)\) deny\(\d+\) ([\w-]+) (.+)$")
PARENTS = {str(p) for p in STATE.parents}


def benign(operation, path):
    if operation == "file-read-data" and path == str(HOME / ".CFUserTextEncoding"):
        return True
    return operation == "file-read-metadata" and path in PARENTS


def shown(path):
    return path.replace(str(HOME), "~")


def main():
    since = sys.argv[1]
    done = subprocess.run(["/usr/bin/log", "show", "--start", since, "--style", "compact", "--predicate",
                           'sender == "Sandbox" AND eventMessage CONTAINS "codex"'],
                          capture_output=True, text=True, check=True)
    seen, flagged = Counter(), Counter()
    for line in done.stdout.splitlines():
        match = LINE.search(line)
        if not match:
            continue
        process, _, operation, path = match.groups()
        key = (process, operation, shown(path.strip()))
        (seen if benign(operation, path.strip()) else flagged)[key] += 1
    print(json.dumps({"since": since, "benign": [[*k, n] for k, n in sorted(seen.items())],
                      "flagged": [[*k, n] for k, n in sorted(flagged.items())]}, indent=1))
    if flagged:
        flags = STATE / "flags"
        flags.mkdir(parents=True, exist_ok=True)
        path = flags / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-denials-{uuid.uuid4().hex[:8]}.json"
        path.write_text(json.dumps({"flag": "sandbox denials", "since": since,
                                    "denials": [[*k, n] for k, n in sorted(flagged.items())]}, indent=1))
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
