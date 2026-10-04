# E01: Baseline on dev

Six models on ZendoBench 1.0.0's full dev set (460 games): [DESIGN.md](DESIGN.md). Room experiment: [E1](https://thesubstrate.science/experiments/68717b8a-db66-4b17-a98d-672fddbaa9a9).

- **Backend and compute:**
  - **MLX:** Apple M4 Max 128 GB for the 2B.
  - **Daytona:** one on-demand H100 80 GB per Qwen 27B model, vLLM 0.30.0, about 21-30 h each.
  - **APIs:** Together for DeepSeek; OpenRouter for gpt-oss-120b and GPT-6 Luna.
- **External artifacts:** model weights from the Hugging Face Hub at pinned revisions, checked file by file against the Hub's hashes (`scripts/daytona/setup.sh`, `scripts/checkpoints/`). Run files stay with the owner (`results/runs/`, git-ignored); `results/scores/<arm>.files.json` holds their sha256.
- **Needs:**
  - **`.env`:** `OPENROUTER_API_KEY`, `TOGETHER_API_KEY`, `DAYTONA_ORG`.
  - **Daytona:** the CLI's login.
  - **MLX:** `uv sync --extra mlx`.
- **Run:**
  1. **Daytona arms:** `uv run --with daytona==0.220.0 python scripts/daytona/ctl.py BOX up` (`qwen35`, `qwen38`), then the guard in the background: `uv run --with daytona==0.220.0 python scripts/daytona/guard.py BOX ARM`.
  2. **Every arm:** `bash scripts/01_run.sh ARM`. `SMOKE=1` first for a one-game-per-tier connection check; a second call resumes a stopped run.
  3. **Scoring:** `bash scripts/02_score.sh ARM`, then the table (`results/runs.md`, `results/metrics.json`).

## Result

<filled in after the runs: results/runs.md and results/metrics.json>
