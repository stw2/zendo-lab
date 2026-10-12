#!/usr/bin/env bash
# 02_score.sh ARM   score --verify and diagnose an arm's run files (qwen3.5-4b-mlx-ARM.jsonl and any .partN.jsonl).
# 02_score.sh pairs compare --verify force16-show with force16 and with show (one player, so compare pairs them).
# Pooled summaries and the run files' sha256 go to results/scores/ (committed); the per-game diagnose report
# stays in results/runs/ (git-ignored) with the run files.
set -euo pipefail
arg=${1:?usage: 02_score.sh ARM|pairs}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E02-small-model-interventions; R=$E/results/runs; S=$E/results/scores
mkdir -p "$S"
shopt -s nullglob
arm_files() { local f=("$R/qwen3.5-4b-mlx-$1.jsonl" "$R/qwen3.5-4b-mlx-$1".part*.jsonl); echo "${f[@]}"; }
if [ "$arg" = pairs ]; then
  for b in force16 show; do
    uv run python -m zendo_bench compare --manifest dev --verify --json "$S/force16-show__$b.compare.json" \
      --markdown "$S/force16-show__$b.compare.md" --a $(arm_files force16-show) --b $(arm_files "$b")
  done
  exit 0
fi
arm=qwen3.5-4b-mlx-$arg
files=($(arm_files "$arg"))
uv run python -m zendo_bench score --manifest dev --verify --json "$S/$arm.score.json" --markdown "$S/$arm.score.md" "${files[@]}"
uv run python -m zendo_bench diagnose --manifest dev --json "$R/$arm.diagnose.json" --markdown "$S/$arm.diagnose.md" "${files[@]}"
python3 - "$S/$arm.files.json" "${files[@]}" <<'PY'
import hashlib, json, os, sys
out, files = sys.argv[1], sys.argv[2:]
rows = [dict(file=os.path.basename(f), sha256=hashlib.sha256(open(f, "rb").read()).hexdigest(), bytes=os.path.getsize(f))
        for f in files]
open(out, "w").write(json.dumps(rows, indent=1) + "\n")
print(json.dumps(rows, indent=1))
PY
