# E02: Stopping or tracking? Interventions on Qwen3.5-4B

Room experiment: [E2](https://thesubstrate.science/experiments/3baea10f-7b1a-44a8-846e-191a8367d1b1). Qwen3.5-4B on 102 dev games in three arms: forced to run 16 experiments before submitting, shown the count of rules still consistent with the evidence, and both. The baseline is E1's A8 on the same games. Design: [DESIGN.md](DESIGN.md). Thread: [Small models: a stopping problem or a hypothesis-tracking problem?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/18a8a1c9-74d9-491c-98d6-ed67e93fddf9).

- **Backend and compute:** MLX on an Apple M4 Max 128 GB, 36 games in flight. Roughly 3 h for `show` and 12-15 h for each forced arm, extrapolated from E1's A8.
- **External artifacts:** the 4B checkpoint ZendoBench pins (`--checkpoint 4B`), fetched from the Hugging Face Hub and checked shard by shard. Run files stay with the owner (`results/runs/`, git-ignored), and so does E1's A8 file, which `03_measures.py` reads.
- **Needs:** `uv sync --extra mlx`.
- **Run:**
  1. **Check:** `uv run python scripts/00_check.py`, the interventions with a scripted stand-in for the model. Then `SMOKE=1 bash scripts/01_run.sh force16-show`, one T1 game on the 4B.
  2. **Every arm:** `bash scripts/01_run.sh ARM`, with ARM one of `force16`, `show` or `force16-show`. A second call resumes a stopped run.
  3. **Scoring:** `bash scripts/02_score.sh ARM` for each arm (score --verify, diagnose), then `bash scripts/02_score.sh pairs` (compare --verify on the two pairs of new arms), then `uv run python scripts/03_measures.py` (the comparisons with A8, the measures and the hypotheses' verdicts) and `uv run python scripts/04_table.py` (results/runs.md).

## Result

Qwen3.5-4B on the 102 games (92 T2-T6), ZendoBench 1.0.0 dev, every game verified by `score --verify`. The no-intervention cell is E1's A8 on the same games. The seed-only baseline on these games is 3.3. Full tables: [results/runs.md](results/runs.md); every measure and verdict: [results/measures.json](results/measures.json).

| Arm | Attempt | T2-T6 win rate [95% CI] | Experiments per game | Classes alive at first submission (median) | Contradicting submissions |
|---|---|---|---|---|---|
| none (E1's A8) | A8 ([P31](https://thesubstrate.science/records/9c6080af-4e48-4962-82be-e9d303ce9238), [P32](https://thesubstrate.science/records/be062a4b-4e6a-4de7-be80-5e98a9ff5053)) | 0.0 [0.0, 17.2] | 1.88 | 90 | 44/203 (21.7%) |
| `show` | A9 ([P29](https://thesubstrate.science/records/8cfab1fc-54aa-4522-8294-e0ec5f06fe4a), [P34](https://thesubstrate.science/records/d3ac9665-67e6-4f7f-af6c-086427122f93)) | 4.9 [1.7, 21.5] | 2.30 | 84.5 | 29/201 (14.4%) |
| `force16` | A10 ([P28](https://thesubstrate.science/records/b4fb1d38-4c66-4640-bfd9-d3f864fa4142), [P33](https://thesubstrate.science/records/4a45cc3f-4aa0-4f61-8c88-164a0a483b54)) | 19.1 [11.4, 34.8] | 16.25 | 2 | 97/189 (51.3%) |
| `force16-show` | A11 ([P30](https://thesubstrate.science/records/43fec666-c5a7-4ca2-8213-93e3110bfa10), [P35](https://thesubstrate.science/records/01bfa348-752c-47a9-a686-072ac7d6a9f5)) | 22.4 [13.6, 38.7] | 16.40 | 2 | 94/184 (51.1%) |

All three pre-registered hypotheses hold, and so does the precondition: forcing narrowed the evidence to a median of 2 classes.

- **H1, stopping ([P36](https://thesubstrate.science/records/3446a2b3-0944-43db-b24d-009be0f3df04)).** Forcing 16 experiments raises the T2-T6 win rate by 19.1 points [9.5, 28.7] against A8.
- **H2, tracking ([P37](https://thesubstrate.science/records/7334ea23-17cf-4b45-b0e0-29c77343dad1)).** Forced, 51.3% of the 4B's submissions contradict evidence it has been shown. The threshold was 10%; A8 on the same games is at 21.7%.
- **H3, uncertainty ([P38](https://thesubstrate.science/records/b571e856-d925-4052-a2d9-f4131060e0fd)).** Shown the count of consistent rules, the 4B runs 0.42 more experiments a game [0.10, 0.74], with no win difference measured: +4.9 [-1.0, 10.7] ([P39](https://thesubstrate.science/records/90028119-acaa-45fe-88dc-0edeb4c8ccf7)).

Once the 4B is forced, the count shows no difference measured: +3.3 [-5.7, 12.2] ([P40](https://thesubstrate.science/records/35e725a3-ef63-4c9c-9ff0-2f54bdd21515)); forcing helps when the count is shown too: +17.5 [7.2, 27.8] ([P41](https://thesubstrate.science/records/01603c0d-e020-457f-8f17-62992068bcfa)). By the design's decision table, the 4B has both a stopping problem and a hypothesis-tracking problem.

Descriptively, after forcing, an ideal player would win with mean probability 0.70 at the 4B's first submission, but the 4B wins 0.29 of the T2-T6 games such a player would be expected to win. E1's leaders win 0.86-0.88 of them, measured over E1's games.

Caveats: one run per arm and 92 headline games. A8 is E1's run, not a fresh control (DESIGN.md, Arms and Amendments). Room records: P28-P41 and the checkpoint in the Thread [Small models: a stopping problem or a hypothesis-tracking problem?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/18a8a1c9-74d9-491c-98d6-ed67e93fddf9).
