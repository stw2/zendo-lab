"""E04: one arm's dev games through Claude (claude_backend.py), with ZendoBench 1.0.0's own runner.

`python 01_play.py ARM OUT [--exclude EARLIER.jsonl ...] [--first N] [--batch K]` plays the dev manifest's 460
games (or the first N of each tier, a smoke run) into the new run file OUT, less the games finished in the
EARLIER files, K calls at once. The player is `model`: each decision is one stateless call that answers from its
prompt alone, so a game left without an outcome is played again by a later run (`--exclude`). Every try's trace
(Claude's events and the server's messages) goes to traces/OUT-STEM.traces.jsonl beside OUT (git-ignored with it).

Exit codes: 0 every chosen game finished; 3 the Claude subscription usage limit stopped the run (resume later); 4 the breaker
stopped it (games in a row without an outcome); 5 an isolation flag stopped it (look before anything else);
1 anything else.
"""

import argparse
import json
from pathlib import Path
import sys
import time

from zendo_bench.backends.threaded_batch import ThreadedBatch
from zendo_bench.bench import runner
from zendo_bench.bench.cli import load_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_backend import STATE, ClaudeBackend  # noqa: E402

from claude_backend import ARMS


def flags():
    return sorted((STATE / "flags").glob("*.json")) if (STATE / "flags").exists() else []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arm", choices=ARMS)
    parser.add_argument("out")
    parser.add_argument("--exclude", nargs="*", default=[])
    parser.add_argument("--first", type=int)
    parser.add_argument("--batch", type=int, default=12)
    args = parser.parse_args()
    registrations = Path(__file__).resolve().parents[1] / "results/attempts.json"
    registered = json.loads(registrations.read_text()) if registrations.exists() else {}
    if not (registered.get(args.arm) or {}).get("attemptId"):
        raise SystemExit("Register this arm in E4 and record its attemptId before live inference.")
    if flags():
        print(f"{len(flags())} isolation flag(s) in the state folder's flags/: look at them first.", file=sys.stderr)
        return 5
    out = Path(args.out)
    if out.exists():
        raise SystemExit("Run files are immutable: select a fresh part filename.")
    backend = ClaudeBackend(ARMS[args.arm], trace=out.parent / "traces" / f"{out.stem}.traces.jsonl")
    engine = ThreadedBatch(backend, batch=args.batch) if args.batch > 1 else backend
    began = time.time()
    try:
        end = runner.run(load_manifest("dev"), lambda tier: engine, arm=args.arm, out=args.out, exclude=args.exclude,
                         first=args.first, batched=args.batch > 1, player="model")
    except BaseException as error:
        if flags():
            print(f"Isolation flag: {flags()[-1].name}", file=sys.stderr)
            return 5
        print(f"Stopped: {type(error).__name__}: {str(error)[:500]}", file=sys.stderr)
        return 1
    finally:
        backend.close()
    print(json.dumps({"end": end, "minutes": round((time.time() - began) / 60, 1)}))
    if flags():
        return 5
    return {"complete": 0, "usage_limit": 3, "stopped": 4}.get(end.get("status"), 1)


if __name__ == "__main__":
    sys.exit(main())
