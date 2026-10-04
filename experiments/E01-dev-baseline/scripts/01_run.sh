#!/usr/bin/env bash
# 01_run.sh ARM   one arm's dev run (DESIGN.md) into results/runs/ARM.jsonl, from the repository root.
# Keys come from the repository's .env; a Daytona arm reads its preview URL and token from the box's
# state folder (scripts/daytona/ctl.py), never from a command line. A second call resumes the run:
# it writes ARM.partN.jsonl with --exclude-finished over the earlier files. SMOKE=1 plays the first game of each
# tier into results/runs/smoke/ instead: a connection check, not a measurement (DESIGN.md).
set -euo pipefail
arm=${1:?usage: 01_run.sh ARM}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E01-dev-baseline
set -a; . ./.env; set +a

daytona() {  # daytona BOX: the box's preview URL and token
  local state="$HOME/.cache/zendo-lab/e01-daytona/$1"
  BASE_URL="$(tr -d '\n' < "$state/preview-url.txt")"; BASE_URL="${BASE_URL%/}/v1"
  export DAYTONA_PREVIEW_TOKEN="$(cat "$state/preview-token")" DAYTONA_SKIP_WARNING=true
}
DAYTONA_HEADERS=(--header x-daytona-preview-token=DAYTONA_PREVIEW_TOKEN
                 --header X-Daytona-Skip-Preview-Warning=DAYTONA_SKIP_WARNING)

case "$arm" in
  qwen3.5-2b-mlx)
    args=(--backend mlx --checkpoint-json "$E/scripts/checkpoints/qwen3.5-2b.json" --batch 36 --seed 0) ;;
  qwen3.5-27b-fp8-vllm-h100)
    daytona qwen35
    args=(--backend http --base-url "$BASE_URL" --model qwen3.5-27b-fp8 "${DAYTONA_HEADERS[@]}" --batch auto --keep-reasoning
          --sampling '{"temperature":1.0,"top_p":0.95,"top_k":20,"min_p":0.0,"presence_penalty":1.5,"max_tokens":65536}') ;;
  qwen3.8-27b-fp8-vllm-h100)
    daytona qwen38
    args=(--backend http --base-url "$BASE_URL" --model qwen3.8-27b-fp8 "${DAYTONA_HEADERS[@]}" --batch auto --keep-reasoning
          --sampling '{"temperature":1.0,"top_p":0.95,"top_k":20,"presence_penalty":0.0,"max_tokens":65536,"chat_template_kwargs":{"reasoning_effort":"xhigh"}}') ;;
  deepseek-v4-flash-together)
    args=(--backend http --base-url https://api.together.xyz/v1 --model deepseek-ai/DeepSeek-V4-Flash-0731
          --api-key-env TOGETHER_API_KEY --batch 64 --keep-reasoning --sampling '{"max_tokens":65536}') ;;
  gpt-oss-120b-openrouter-high)
    args=(--backend http --base-url https://openrouter.ai/api/v1 --model openai/gpt-oss-120b
          --api-key-env OPENROUTER_API_KEY --batch 64 --keep-reasoning
          --sampling '{"max_tokens":65536,"reasoning":{"effort":"high"}}') ;;
  gpt-6-luna-openrouter-high)
    args=(--backend http --base-url https://openrouter.ai/api/v1 --model openai/gpt-6-luna
          --api-key-env OPENROUTER_API_KEY --batch 64 --keep-reasoning
          --sampling '{"max_tokens":65536,"reasoning":{"effort":"high"}}') ;;
  *) echo "unknown arm: $arm" >&2; exit 2 ;;
esac

R="$E/results/runs"; resume=()
if [ "${SMOKE:-0}" = 1 ]; then R="$R/smoke"; resume=(--first 1); fi
mkdir -p "$R"
out="$R/$arm.jsonl"
if [ "${SMOKE:-0}" = 1 ]; then rm -f "$out"
elif [ -e "$out" ]; then
  shopt -s nullglob
  earlier=("$out" "$R/$arm".part*.jsonl); n=$(( ${#earlier[@]} + 1 ))
  out="$R/$arm.part$n.jsonl"; resume=(--exclude-finished "${earlier[@]}")
fi
name="$(basename "$out" .jsonl)"
{ echo "arm $arm"; echo "out $out"; echo "zendo-lab $(git rev-parse HEAD) dirty=$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  echo "started $(date -u +%FT%TZ)"; } > "$R/$name.cmd"
set +e
uv run python -m zendo_bench run --manifest dev --arm "$arm" --out "$out" ${resume[@]+"${resume[@]}"} "${args[@]}" \
  > "$R/$name.log" 2>&1
code=$?
set -e
echo "$code" > "$R/$name.exit"
echo "ended $(date -u +%FT%TZ) exit $code" >> "$R/$name.cmd"
exit $code
