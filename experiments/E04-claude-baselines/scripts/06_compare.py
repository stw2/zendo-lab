"""Paired verified comparisons against every E3 arm on the shared dev manifest."""
import argparse
from pathlib import Path
import subprocess
import sys

from claude_backend import ARMS

BASELINES = ("gpt-6-luna-codex-high", "gpt-6-sol-codex-high", "gpt-6.1-sol-codex-high",
             "gpt-5.6-terra-codex-high", "gpt-6-astra-codex-high")


def parts(root, arm):
    files = [*root.glob(arm + ".jsonl"), *root.glob(arm + ".part*.jsonl")]
    if not files:
        raise SystemExit(f"Private baseline/run files unavailable for {arm}; no comparison invented.")
    return sorted(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args()
    experiment = Path(__file__).resolve().parents[1]
    old = experiment.parent / "E03-codex-frontier/results/runs"
    new = experiment / "results/runs"
    out = experiment / "results/comparisons"
    out.mkdir(parents=True, exist_ok=True)
    for arm in ([args.arm] if args.arm else ARMS):
        for baseline in BASELINES:
            name = arm + "__vs__" + baseline
            subprocess.run([sys.executable, "-m", "zendo_bench", "compare", "--manifest", "dev", "--verify",
                            "--a", *map(str, parts(new, arm)), "--b", *map(str, parts(old, baseline)),
                            "--json", str(out / (name + ".json")),
                            "--markdown", str(out / (name + ".md"))], check=True)


if __name__ == "__main__":
    main()
