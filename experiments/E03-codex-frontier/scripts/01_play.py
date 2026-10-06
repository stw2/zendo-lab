"""E03: one arm's dev games through Codex (codex_backend.py), with ZendoBench 1.0.0's own runner.

`python 01_play.py ARM OUT [--exclude EARLIER.jsonl ...] [--first N] [--batch K]` plays the dev manifest's 460
games (or the first N of each tier, a smoke run) into the new run file OUT, less the games finished in the
EARLIER files, K calls at once. The player is `model`: each decision is one stateless call that answers from its
prompt alone, so a game left without an outcome is played again by a later run (`--exclude`). Every try's trace
(Codex's events and the server's messages) goes to traces/OUT-STEM.traces.jsonl beside OUT (git-ignored with it).

Exit codes: 0 every chosen game finished; 3 the ChatGPT usage limit stopped the run (resume later); 4 the breaker
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
from codex_backend import STATE, CodexBackend  # noqa: E402

# Run in this order, one at a time (owner, 2026-10-06): each arm finishes before the next starts.
ARMS = {"gpt-6-luna-codex-high": "gpt-6-luna",
        "gpt-6-sol-codex-high": "gpt-6-sol",
        "gpt-6.1-sol-codex-high": "gpt-6.1-sol",
        "gpt-5.6-terra-codex-high": "gpt-5.6-terra",
        "gpt-6-astra-codex-high": "gpt-6-astra"}


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
    if flags():
        print(f"{len(flags())} isolation flag(s) in the state folder's flags/: look at them first.", file=sys.stderr)
        return 5
    out = Path(args.out)
    backend = CodexBackend(ARMS[args.arm], trace=out.parent / "traces" / f"{out.stem}.traces.jsonl")
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
    print(json.dumps({"end": end, "minutes": round((time.time() - began) / 60, 1)}))
    if flags():
        return 5
    return {"complete": 0, "usage_limit": 3, "stopped": 4}.get(end.get("status"), 1)


if __name__ == "__main__":
    sys.exit(main())
