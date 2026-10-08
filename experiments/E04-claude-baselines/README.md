# E04: Claude baselines at high effort

[E4 in Substrate](https://thesubstrate.science/experiments/f8519620-4f56-49b5-a14a-4ca9b3e4ecee). See [DESIGN.md](DESIGN.md) for the prospective protocol and E3 comparability limits.

- **Order:** Haiku 5.5 → Sonnet 5.5 → Opus 5.5 → Fable 5.1; high effort, 12 concurrent calls within one arm.
- **Backend:** pinned Claude Code 2.1.293, dedicated subscription login, no model tools, exact benchmark prompts, guarded requests and macOS file sandbox.
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

## Result

Pending. No model measurements have been made for E4.
