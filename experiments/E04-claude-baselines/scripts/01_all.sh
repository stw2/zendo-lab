#!/usr/bin/env bash
# 01_all.sh   every arm in DESIGN.md's order, one at a time, from any folder of the repository; an arm already
# complete (its last part exited 0) is skipped. It first waits until no 01_run.sh of this experiment runs, so it
# can be started while an arm is running. Per arm: SMOKE=1 01_run.sh ARM (the connection check; skipped if the
# arm's smoke run already exited 0), then 01_run.sh ARM, which resumes by itself after the usage limit. A part
# the breaker stopped (exit 4: games in a row without an outcome) is resumed after WAIT seconds, up to 3 times.
# Any other stop ends the chain: 5 an isolation flag, 1 anything else. Its log: results/runs/01_all.log.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E04-claude-baselines
R="$E/results/runs"
ARMS="claude-haiku-5-5-claude-high-v2 claude-sonnet-5-5-claude-high-v2 claude-opus-5-5-claude-high-v2 claude-fable-5-1-claude-high-v2"
log() { echo "$(date -u +%FT%TZ) $*" >> "$R/01_all.log"; }

last_exit() {  # last_exit DIR ARM: the exit code of the arm's last part in DIR, or "none"
  local dir=$1 arm=$2 n last=none
  [ -e "$dir/$arm.exit" ] && last=$(cat "$dir/$arm.exit")
  for n in $(seq 2 60); do
    [ -e "$dir/$arm.part$n.exit" ] && last=$(cat "$dir/$arm.part$n.exit")
  done
  echo "$last"
}

mkdir -p "$R"
log "chain started at $(git rev-parse --short HEAD)"
while pgrep -f "$E/scripts/01_run.sh" > /dev/null; do sleep 60; done
for arm in $ARMS; do
  if [ "$(last_exit "$R" "$arm")" = 0 ]; then
    bash "$E/scripts/02_score.sh" "$arm"
    log "$arm complete and verified; skipped"; continue
  fi
  if [ "$(last_exit "$R/smoke" "$arm")" != 0 ]; then
    log "$arm smoke started"
    set +e
    SMOKE=1 bash "$E/scripts/01_run.sh" "$arm"; code=$?
    set -e
    log "$arm smoke exit $code"
    [ "$code" = 0 ] || { log "chain stopped: $arm's connection check failed"; exit "$code"; }
  fi
  shopt -s nullglob
  smoke=("$R/smoke/$arm.jsonl" "$R/smoke/$arm".part*.jsonl)
  uv run python -m zendo_bench score --manifest dev --verify "${smoke[@]}" > "$R/smoke/$arm.verify.log"
  uv run python "$E/scripts/05_audit.py" "${smoke[@]}" > "$R/smoke/$arm.audit.json"
  for try in 1 2 3 4; do
    log "$arm run started (try $try)"
    set +e
    bash "$E/scripts/01_run.sh" "$arm"; code=$?
    set -e
    log "$arm run exit $code"
    [ "$code" = 4 ] && [ "$try" -lt 4 ] && { sleep "${WAIT:-1800}"; continue; }
    break
  done
  [ "$code" = 0 ] || { log "chain stopped: $arm exit $code"; exit "$code"; }
  bash "$E/scripts/02_score.sh" "$arm"
done
uv run python "$E/scripts/03_table.py"
log "chain done"
