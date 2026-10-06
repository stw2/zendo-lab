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
  3. **Scoring:** `bash scripts/02_score.sh ARM`, then the table (`uv run python scripts/03_table.py`: `results/runs.md`, `results/metrics.json`) and the rank agreement (`uv run python scripts/04_rank_agreement.py`).

## Result

All 460 dev games per arm, every game verified by `score --verify` (ZendoBench 1.0.0, `max_tokens` 65,536 a call; settings per arm in [DESIGN.md](DESIGN.md)). The seed-only baseline, one submission from the two seed scenes, wins 4.7 ([P1](https://thesubstrate.science/records/7f391bde-3e66-43b6-9a50-d299f7b7e5b2)).

| Arm | Attempt | Headline T2-T6 [95% CI] | Experiments per game | Classes alive at first submission (median) | Room records |
|---|---|---|---|---|---|
| `gpt-6-luna-openrouter-high` | A2 | 44.9 [40.5, 49.6] | 16.70 | 2 | [P2](https://thesubstrate.science/records/4afb1318-33ab-4d14-9f47-5bbeb4c6e769), [P9](https://thesubstrate.science/records/14fbeacc-5178-44b1-aa46-0593126c8f6a) |
| `qwen3.8-27b-fp8-vllm-h100` | A5 | 44.5 [40.4, 49.0] | 13.80 | 2 | [P3](https://thesubstrate.science/records/9f72911f-8a38-4906-90c6-2bb0d3637236), [P10](https://thesubstrate.science/records/da204c2b-aed5-4f7c-ae35-56745141f111) |
| `deepseek-v4-flash-together` | A4 | 26.2 [22.5, 31.0] | 10.00 | 7 | [P4](https://thesubstrate.science/records/f4d4ccd3-23dc-4b95-b06f-788b853ee24f), [P11](https://thesubstrate.science/records/40b19c65-c17d-44ab-97f8-b73331ad4443) |
| `gpt-oss-120b-openrouter-high` | A3 | 14.1 [11.1, 19.2] | 6.67 | 12 | [P5](https://thesubstrate.science/records/4abd87e2-3745-4e85-8857-70705d976a05), [P12](https://thesubstrate.science/records/a68c0e7e-0f62-4632-9cf5-8c098b7f4e1d) |
| `qwen3.5-27b-fp8-vllm-h100` | A6 | 10.4 [7.8, 15.1] | 5.36 | 27 | [P6](https://thesubstrate.science/records/c7096cbf-a84e-4c7d-b719-6fea1e79ca98), [P13](https://thesubstrate.science/records/f164a7c1-d061-4a5f-83ea-e6980601af35) |
| `qwen3.5-4b-mlx` | A8 | 3.0 [1.5, 7.4] | 1.91 | 98 | [P7](https://thesubstrate.science/records/a1427e75-d571-45f4-9513-1276d692d84b), [P14](https://thesubstrate.science/records/53f39276-69b9-4260-aa09-af060ba7c2ee) |
| `qwen3.5-2b-mlx` | A1 | 0.0 [0.0, 4.4] | 0.21 | 188 | [P8](https://thesubstrate.science/records/e3552371-0135-40d4-ac20-412b614ce6f2), [P15](https://thesubstrate.science/records/cd29dc79-e65d-4baa-a036-42920fbc748b) |

Across the seven systems, ranking by experiments per game matches ranking by win rate exactly (Spearman rho 1.00; classes alive at the first submission -0.99). This describes these systems only and is not a causal claim ([P16](https://thesubstrate.science/records/da8d956f-13f3-4dbc-b0e0-bb886394b401); `results/rank_agreement.json`). The two small Qwen models submit almost at once, with many rule classes still consistent with the evidence, and do not beat the seed-only baseline (the 2B's interval lies entirely below it).

Full table: [results/runs.md](results/runs.md). Records and digests: [results/findings.json](results/findings.json). Caveats (OpenRouter routing, DeepSeek's output cap, grammar-constrained MLX answers, A5's resumed run): DESIGN.md amendments.
