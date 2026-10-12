#!/usr/bin/env bash
# 01_run.sh ARM   one arm's dev run (DESIGN.md) into results/runs/qwen3.5-4b-mlx-ARM.jsonl, from the repository
# root. ARM is force16, show or force16-show (scripts/intervene.py). A second call resumes the run:
# it writes .partN.jsonl with --exclude-finished over the earlier files. SMOKE=1 plays the first T1 game into
# results/runs/smoke/ instead: a check of the MLX path, not a measurement (DESIGN.md). The body is one block,
# so bash reads all of it before the run starts and an edit to this file cannot reach a running call.
{
set -euo pipefail
arm=${1:?usage: 01_run.sh ARM}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E02-small-model-interventions

R="$E/results/runs"; extra=()
if [ "${SMOKE:-0}" = 1 ]; then R="$R/smoke"; extra=(--first 1 --tiers T1); fi
mkdir -p "$R"
out="$R/qwen3.5-4b-mlx-$arm.jsonl"
if [ "${SMOKE:-0}" = 1 ]; then rm -f "$out"
elif [ -e "$out" ]; then
  shopt -s nullglob
  earlier=("$out" "${out%.jsonl}".part*.jsonl); n=$(( ${#earlier[@]} + 1 ))
  out="${out%.jsonl}.part$n.jsonl"; extra=(--exclude-finished "${earlier[@]}")
fi
name="$(basename "$out" .jsonl)"
{ echo "arm $arm"; echo "out $out"; echo "zendo-lab $(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  echo "started $(date -u +%FT%TZ)"; } > "$R/$name.cmd"
set +e
uv run python "$E/scripts/intervene.py" "$arm" "$out" ${extra[@]+"${extra[@]}"} > "$R/$name.log" 2>&1
code=$?
set -e
echo "$code" > "$R/$name.exit"
echo "ended $(date -u +%FT%TZ) exit $code" >> "$R/$name.cmd"
exit $code
}
