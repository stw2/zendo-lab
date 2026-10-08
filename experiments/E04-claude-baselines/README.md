# E04: Claude baselines at high effort

[E4 in Substrate](https://thesubstrate.science/experiments/f8519620-4f56-49b5-a14a-4ca9b3e4ecee). See [DESIGN.md](DESIGN.md) for the prospective protocol and E3 comparability limits.

- **Order:** Haiku 5.5 → Sonnet 5.5 → Opus 5.5 → Fable 5.1; high effort, 12 concurrent calls within one arm.
- **Backend:** pinned Claude Code 2.1.293, dedicated subscription login, no model tools, unchanged benchmark prompts plus one fixed SDK identity sentence, guarded requests and macOS file sandbox. The prompt difference is documented in the design amendments.
- **Compute:** hosted Anthropic inference, provider hardware unknown; local Apple M4 Max, 128 GB.
- **Data:** ZendoBench 1.0.0 dev, 460 games per arm; manifest episode seeds, models unseeded.
- **Sampling:** provider defaults, adaptive thinking, `max_tokens=128000`.
- **Transcripts:** every exposed request/response, thinking block, partial event and retry stays private in `results/runs/`, with hashes and trace IDs.

## Run

1. `uv run python experiments/E04-claude-baselines/scripts/00_setup.py`; complete its isolated Claude subscription login.
2. `uv run pytest` and `uv run python experiments/E04-claude-baselines/scripts/00_check.py` (offline).
3. Commit/push design and source; accept the Room plan and register attempts.
4. `bash experiments/E04-claude-baselines/scripts/01_all.sh` runs smoke then full arms sequentially and verifies each.
5. `uv run python experiments/E04-claude-baselines/scripts/03_table.py` generates public summaries after scoring.

Runtime state is outside the repository. Existing E2/E3 state is never reused. Resume parts exclude finished games; deliberate reruns require new Room attempts.

For the registered Haiku continuation described in the latest design amendment, use `01_run.sh claude-haiku-5-5-claude-high` after restoring its isolated login and resolving the archived preflight flags. A23's verified smoke is carried forward explicitly; the original smoke exit code is preserved. The fresh-start chain above would otherwise repeat that smoke.

## Result

Full results are pending. A27 retained 83 verified Haiku games (T1: 30, T2: 53) before infrastructure and authentication stops. The remaining 377 games require the source-pinned continuation in DESIGN.md; no completed game is replayed. See [partial provenance](results/partial-a27.json). Other models have not started. No full-arm headline is available.
