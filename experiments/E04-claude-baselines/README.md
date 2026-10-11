# E04: Claude baselines at high effort

[E4 in Substrate](https://thesubstrate.science/experiments/f8519620-4f56-49b5-a14a-4ca9b3e4ecee). See [DESIGN.md](DESIGN.md) for the prospective protocol and E3 comparability limits.

- **Execution:** all four high-effort baselines are complete. The owner-approved scheduling amendments allowed overlapping arms, with at most 12 concurrent calls per arm; see DESIGN.md. Completed games were retained across continuation parts.
- **Backend:** pinned Claude Code 2.1.293, dedicated subscription login, no model tools, unchanged benchmark prompts plus one fixed SDK identity sentence, guarded requests and macOS file sandbox. The prompt difference is documented in the design amendments.
- **Compute:** hosted Anthropic inference, provider hardware unknown; local Apple M4 Max, 128 GB.
- **Data:** ZendoBench 1.0.0 dev, 460 games per arm; manifest episode seeds, models unseeded.
- **Sampling:** provider defaults, adaptive thinking, `max_tokens=128000`.
- **Transcripts:** every exposed request/response, thinking block, partial event and retry stays private in `results/runs/`, with hashes and trace IDs.

## Run

1. `uv run python experiments/E04-claude-baselines/scripts/00_setup.py`; complete its isolated Claude subscription login.
2. `uv run pytest` and `uv run python experiments/E04-claude-baselines/scripts/00_check.py` (offline).
3. Commit/push design and source; accept the Room plan and register attempts.
4. `bash experiments/E04-claude-baselines/scripts/01_all.sh` is the original sequential entry point. The approved overlap and reviewed continuations used `scripts/07_parallel.py`, as recorded in DESIGN.md and the attempts. The existing baselines are complete; a deliberate new evaluation requires a new attempt and separate outputs.
5. `uv run python experiments/E04-claude-baselines/scripts/03_table.py` generates public summaries after scoring.

Runtime state is outside the repository. Existing E2/E3 state is never reused. Resume parts exclude finished games; deliberate reruns require new Room attempts.

The corrected arms end in `-claude-high-v2`. This marks the harness revision, not a different model version. They start with fresh smoke and full-run files; original attempts and their transcripts remain unchanged.

## Result

All four `-claude-high-v2` arms completed all 460 dev games. Every finished game passed `score --verify`; each arm has zero unscored or unfinished games. Transcript audits found zero missing joins and zero unfinished trace records. The four attempts are recorded as succeeded in Substrate. Scores, file hashes and exact configurations are in [results/runs.md](results/runs.md); the attempt and plan mapping is in [results/provenance.json](results/provenance.json).

The headline is the equally weighted mean over T2–T6, with the benchmark's 95% confidence interval. T1 is diagnostic and excluded from that headline. These are the native Claude CLI function-backend runs described above: provider-default sampling, high effort, adaptive summarized thinking, `max_tokens=128000`, manifest episode seeds and no model seed; hosted inference hardware is unknown, with local Apple M4 Max 128 GB orchestration.

| Model | Attempt | Headline T2–T6, % [95% CI] | Wins across all 460 games | Unscored | Unfinished |
|---|---|---|---|---|---|
| `claude-haiku-5-5` | [A31](https://thesubstrate.science/attempts/ca2b3271-a293-4b3e-a0af-bf80bab566ba) | 39.1 [34.7, 44.0] | 214 | 0 | 0 |
| `claude-sonnet-5-5` | [A35](https://thesubstrate.science/attempts/79436501-f7f0-49bb-b380-197973eb319d) | 72.2 [67.6, 76.4] | 362 | 0 | 0 |
| `claude-opus-5-5` | [A36](https://thesubstrate.science/attempts/e6384132-1f55-4727-be14-f2eaa70c7886) | 90.8 [85.5, 93.9] | 429 | 0 | 0 |
| `claude-fable-5-1` | [A38](https://thesubstrate.science/attempts/1a64177d-1299-4087-8197-e5262dd1b613) | 94.1 [89.6, 96.4] | 441 | 0 | 0 |

Fable has the highest observed Claude headline. In the paired comparison with E3's GPT-6 Astra, the difference is −0.2 percentage points [−3.8, +3.4]. That interval includes zero and does not establish equivalence. All 20 verified Claude–Codex comparisons, including their paired intervals, are in [results/comparisons.md](results/comparisons.md).

Format and output limits materially affect interpretation. Malformed-decision rates over the headline tiers are 26.82% for Haiku, 12.18% for Sonnet, 0.036% for Opus and 0.022% for Fable. Across all retained episode calls, including interrupted games, the respective output-cap counts are 894, 71, 0 and 1. The call totals and their scope are in results/runs.md. Complete malformed or capped replies were retained and never resampled.

Cross-provider comparisons remain descriptive. Claude receives one fixed SDK identity sentence in addition to the benchmark messages; sampling defaults and output caps differ from Codex. High effort is model-specific and does not imply equal compute. This public dev benchmark and unknown training corpora do not establish contamination-free reasoning; model IDs are provider names rather than immutable weight snapshots. The 20 comparison intervals are individual 95% intervals without a multiple-comparison adjustment.

A27's 83 verified games remain a separate partial result, excluded from every v2 headline; see [partial provenance](results/partial-a27.json) and the design amendments. Runtime interruptions did not turn unfinished games into losses: continuation parts excluded completed games and restarted only unfinished games. The original runs, failed tries and complete exposed transcripts remain private. Public comparison JSONs replace local file paths with repository-relative paths; [the sanitization manifest](results/comparisons/provenance.json) preserves the original and public digests and documents that all other values are unchanged.
