#!/usr/bin/env bash
# 01_run.sh ARM   one arm's dev games (DESIGN.md) into results/runs/ARM.jsonl, from any folder of the repository.
# Arms run one at a time, in DESIGN.md's order. A stopped run resumes into ARM.partN.jsonl with --exclude over
# the earlier files, as the same attempt. When the Claude subscription usage limit stops a part (exit 3), the script waits
# WAIT seconds (default 1800) and resumes, up to ROUNDS parts (default 40). Any other stop ends it: 4 the
# breaker, 5 an isolation flag (look before anything else; 04_denials.py checks the sandbox's log after each
# part), 1 anything else. SMOKE=1 plays the first game of
# each tier into results/runs/smoke/ instead: a connection check, not a measurement (DESIGN.md).
set -euo pipefail
arm=${1:?usage: 01_run.sh ARM}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E04-claude-baselines
R="$E/results/runs"; extra=()
if [ "${SMOKE:-0}" = 1 ]; then R="$R/smoke"; extra=(--first 1); fi
mkdir -p "$R"
for round in $(seq 1 "${ROUNDS:-40}"); do
  shopt -s nullglob
  earlier=("$R/$arm.jsonl" "$R/$arm".part*.jsonl)
  shopt -u nullglob
  existing=(); for f in "${earlier[@]}"; do [ -e "$f" ] && existing+=("$f"); done
  if [ ${#existing[@]} -eq 0 ]; then out="$R/$arm.jsonl"; resume=()
  else out="$R/$arm.part$(( ${#existing[@]} + 1 )).jsonl"; resume=(--exclude "${existing[@]}"); fi
  name="$(basename "$out" .jsonl)"
  { echo "arm $arm"; echo "out $out"; echo "zendo-lab $(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
    echo "started $(date -u +%FT%TZ)"; } > "$R/$name.cmd"
  since="$(date '+%Y-%m-%d %H:%M:%S')"
  set +e
  uv run python "$E/scripts/01_play.py" "$arm" "$out" ${resume[@]+"${resume[@]}"} ${extra[@]+"${extra[@]}"} > "$R/$name.log" 2>&1
  code=$?
  sleep 5  # the kernel's sandbox reports reach the log shortly after
  uv run python "$E/scripts/04_denials.py" "$since" > "$R/$name.denials.json" 2>&1
  denials=$?
  set -e
  [ "$denials" = 0 ] || code=5
  [ -s "$R/traces/$name.traces.jsonl" ] && gzip -9f "$R/traces/$name.traces.jsonl"  # the part's call traces
  echo "$code" > "$R/$name.exit"
  echo "ended $(date -u +%FT%TZ) exit $code (denials check $denials)" >> "$R/$name.cmd"
  [ "$code" = 3 ] || exit "$code"
  echo "$(date -u +%FT%TZ) usage limit; waiting ${WAIT:-1800} s before part $(( ${#existing[@]} + 2 ))" >> "$R/$arm.waits"
  sleep "${WAIT:-1800}"
done
exit 3
