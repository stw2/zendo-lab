#!/usr/bin/env bash
# 05_compare_a2.sh [E01_RUNS]   the harness check (DESIGN.md): `zendo_bench compare --verify` of GPT-6 Luna through
# Codex (gpt-6-luna-codex-high, E3) with GPT-6 Luna through OpenRouter (gpt-6-luna-openrouter-high, E1's A2) on
# the same 460 dev games, paired. E01_RUNS: the folder holding A2's run files (default: E01's results/runs/ in this
# checkout); each file's sha256 must match E01's committed results/scores/gpt-6-luna-openrouter-high.files.json.
# Writes results/scores/luna-codex-vs-a2.compare.json and .md.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E03-codex-frontier; R=$E/results/runs; S=$E/results/scores
A2=${1:-experiments/E01-dev-baseline/results/runs}
python3 - "$A2" experiments/E01-dev-baseline/results/scores/gpt-6-luna-openrouter-high.files.json <<'EOF'
import hashlib, json, os, sys
folder, listed = sys.argv[1], json.load(open(sys.argv[2]))
for row in listed:
    path = os.path.join(folder, row["file"])
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert digest == row["sha256"], f"{row['file']}: sha256 {digest} is not E01's {row['sha256']}"
print(f"A2's {len(listed)} run files match E01's sha256")
EOF
shopt -s nullglob
# A2's files by repository-relative links in results/runs/e01-a2/ (git-ignored), so no local path enters the outputs
L=$R/e01-a2; mkdir -p "$L"
for f in "$A2/gpt-6-luna-openrouter-high.jsonl" "$A2/gpt-6-luna-openrouter-high".part*.jsonl; do
  ln -sf "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" "$L/$(basename "$f")"
done
a2=("$L/gpt-6-luna-openrouter-high.jsonl" "$L/gpt-6-luna-openrouter-high".part*.jsonl)
codex=("$R/gpt-6-luna-codex-high.jsonl" "$R/gpt-6-luna-codex-high".part*.jsonl)
uv run python -m zendo_bench compare --manifest dev --verify --a "${a2[@]}" --b "${codex[@]}" \
  --json "$S/luna-codex-vs-a2.compare.json" --markdown "$S/luna-codex-vs-a2.compare.md"
