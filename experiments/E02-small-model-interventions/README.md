# E02: Stopping or tracking? Interventions on Qwen3.5-4B

Room experiment: [E2](https://thesubstrate.science/experiments/3baea10f-7b1a-44a8-846e-191a8367d1b1). Qwen3.5-4B on 102 dev games in three arms: forced to run 16 experiments before submitting, shown the count of rules still consistent with the evidence, and both. The baseline is E1's A8 on the same games. Design: [DESIGN.md](DESIGN.md). Thread: [Small models: a stopping problem or a hypothesis-tracking problem?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/18a8a1c9-74d9-491c-98d6-ed67e93fddf9).

- **Backend and compute:** MLX on an Apple M4 Max 128 GB, 36 games in flight. Roughly 3 h for `show` and 12-15 h for each forced arm, extrapolated from E1's A8.
- **External artifacts:** the 4B checkpoint ZendoBench pins (`--checkpoint 4B`), fetched from the Hugging Face Hub and checked shard by shard. Run files stay with the owner (`results/runs/`, git-ignored), and so does E1's A8 file, which `03_measures.py` reads.
- **Needs:** `uv sync --extra mlx`.
- **Run:**
  1. **Check:** `uv run python scripts/00_check.py`, the interventions with a scripted stand-in for the model. Then `SMOKE=1 bash scripts/01_run.sh force16-show`, one T1 game on the 4B.
  2. **Every arm:** `bash scripts/01_run.sh ARM`, with ARM one of `force16`, `show` or `force16-show`. A second call resumes a stopped run.
  3. **Scoring:** `bash scripts/02_score.sh ARM` for each arm (score --verify, diagnose), then `bash scripts/02_score.sh pairs` (compare --verify on the two pairs of new arms), then `uv run python scripts/03_measures.py` (the comparisons with A8, the measures and the hypotheses' verdicts).

## Result

<filled in after the runs>
