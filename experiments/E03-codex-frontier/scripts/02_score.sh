#!/usr/bin/env bash
# 02_score.sh ARM   score --verify and diagnose an arm's run files (ARM.jsonl and any ARM.partN.jsonl).
# Pooled summaries and the run files' sha256 go to results/scores/ (committed); the per-game diagnose
# report stays in results/runs/ (git-ignored) with the run files.
set -euo pipefail
arm=${1:?usage: 02_score.sh ARM}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
E=experiments/E03-codex-frontier; R=$E/results/runs; S=$E/results/scores
mkdir -p "$S"
shopt -s nullglob
files=("$R/$arm.jsonl" "$R/$arm".part*.jsonl)
uv run python -m zendo_bench score --manifest dev --verify --json "$S/$arm.score.json" --markdown "$S/$arm.score.md" "${files[@]}"
uv run python -m zendo_bench diagnose --manifest dev --json "$R/$arm.diagnose.json" --markdown "$S/$arm.diagnose.md" "${files[@]}"
python3 - "$S/$arm.files.json" "${files[@]}" <<'EOF'
import hashlib, json, os, sys
out, files = sys.argv[1], sys.argv[2:]
rows = [dict(file=os.path.basename(f), sha256=hashlib.sha256(open(f, "rb").read()).hexdigest(), bytes=os.path.getsize(f))
        for f in files]
open(out, "w").write(json.dumps(rows, indent=1) + "\n")
print(json.dumps(rows, indent=1))
EOF
