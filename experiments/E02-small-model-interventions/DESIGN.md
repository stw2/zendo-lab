# E02: Stopping or tracking? Interventions on Qwen3.5-4B

Room experiment: [E2](https://thesubstrate.science/experiments/3baea10f-7b1a-44a8-846e-191a8367d1b1), in the Thread [Small models: a stopping problem or a hypothesis-tracking problem?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/18a8a1c9-74d9-491c-98d6-ed67e93fddf9). Locked at the commit that adds this file; changes are dated amendments at the end.

## Question

In E1, Qwen3.5-4B runs 1.91 experiments a game and first submits with a median of 98 rule classes still consistent with the evidence ([P14](https://thesubstrate.science/records/53f39276-69b9-4260-aa09-af060ba7c2ee)). It wins 3.0 on T2-T6 ([P7](https://thesubstrate.science/records/a1427e75-d571-45f4-9513-1276d692d84b)), below the seed-only baseline of 4.7 ([P1](https://thesubstrate.science/records/7f391bde-3e66-43b6-9a50-d299f7b7e5b2)). 177 of its 915 submissions contradict evidence it had already seen.

Is that a stopping problem or a hypothesis-tracking problem?
- **Stopping:** the model would use more evidence if it gathered it, but commits too early.
- **Tracking:** it does not keep track of which rules the evidence still allows, so more evidence does not help.

Two interventions at inference time, with no training, in a 2×2 design, test which. Forcing experiments addresses stopping. Showing the count of consistent rules gives the model an uncertainty estimate. The fourth cell, no intervention, is E1's A8 on the same games.

## Arms

Three new arms and one baseline, one model. The new arms run through one wrapper (`scripts/intervene.py`) and differ only in what it changes.

| Arm | Force: submit only after 16 experiments | Show: count of consistent rules |
|---|---|---|
| E1's A8 (`qwen3.5-4b-mlx`), its 102 games below | no | no |
| `qwen3.5-4b-mlx-force16` | yes | no |
| `qwen3.5-4b-mlx-show` | no | yes |
| `qwen3.5-4b-mlx-force16-show` | yes | yes |

- **A8 as the baseline.** With no intervention the wrapper would pass every request through unchanged (`scripts/00_check.py` checked this byte for byte), so a fourth new run would repeat A8: same model, sampling, hardware, seed and per-call sampler seeds. Its 102 games: 0 of 92 T2-T6 games won, 1.88 experiments a game, a median of 90 classes alive at the first submission, 21.7% of submissions contradicting the evidence. All 12 of A8's T2-T6 wins fall outside the subset (about 2.6 expected by chance).
- **What else differs from A8:** the player label (A8 is `model`, which gives a second attempt after an undecided verifier), the batch composition (102 games in flight rather than 460, so not bit-reproducible) and the run date.

- **Model, backend, sampling:** as E1's `qwen3.5-4b-mlx` (A8).
  - **Model:** `Qwen/Qwen3.5-4B` bf16, revision `851bf6e8` (ZendoBench's built-in checkpoint, `--checkpoint 4B`).
  - **Backend:** the ZendoBench MLX batch driver on an Apple M4 Max 128 GB, 36 games in flight, sampler seed 0.
  - **Sampling:** ZendoBench's Qwen3.5 thinking defaults (temperature 1.0, top-p 0.95, top-k 20, min-p 0, presence penalty 1.5), with a thinking budget of 63,487 plus a 2,048-token answer allowance. A call's cap is 65,536.
- **The wrapper** (`intervene.Intervention`) sits between ZendoBench's game and its MLX engine. It changes a request after the game has rendered it.
  - **Force:** while the player has run fewer than 16 experiments, the observation's `available_actions` is `["experiment"]`. The answer grammar is ZendoBench's experiment-only variant, the one the game itself uses when a submission is unaffordable.
    - The gate also opens if one more experiment would leave the remaining submissions unaffordable (budget 30; an experiment costs 1, a submission 3, at most 2 submissions). At 16 experiments, 14 of the budget is left.
    - The system prompt gains, after its economy line: "In this game you may submit only after you have run 16 experiments; until then the observation's available_actions offers only experiment."
  - **Show:** the observation gains `consistent_rules`, `{"count": N, "of": M}`.
    - **M** is the size of the game's analysis prior: 1,765 classes for T1-T4, 619 for T5, 427 for T6.
    - **N** is the prior's classes consistent with every evidence scene in the message: seeds, experiments and counterexamples. It is `catalog.domain_alive` restricted to the prior, exactly as `diagnose` counts the classes alive at a submission. It is computed from the message alone, never from the hidden rule.
    - The system prompt gains, after "Use the budget, action costs and remaining submissions shown in the observation.": "The observation's consistent_rules: of the candidate rules this game's hidden rule is drawn from (of), how many label every evidence scene as shown (count). The hidden rule is always among those counted."
- **Records:** every call's backend record carries `intervention`: the arm, the experiments run and the gate (force), the count shown (show), and the sha256 of the messages and grammar the model was given. The call's own `messages_sha256` and `grammar_sha256` remain the game's canonical request, which `score --verify` replays: the replay checks that the recorded replies produce the recorded games, not what the model was shown.
- **Player:** `agent-tools`, in every new arm. ZendoBench reserves `model` for a model answering its prompt alone, and keeps the two apart: `compare` pairs arms of one player only, so the comparisons with A8 are computed by `scripts/03_measures.py` with `compare`'s own pairing and statistics. An agent player's game is played once, with no second attempt after an undecided verifier.
- **Held fixed:**
  - ZendoBench 1.0.0 (tag `v1.0.0`, commit `46c192e`), unpatched;
  - the default reply policy, the dev manifest and E1's model, sampling and hardware;
  - the wrapper's source, whose sha256 every run header records with the arm's configuration (`agent`, `agent_source_sha256`, `agent_config`).
- **Before the runs (not measured, not reported):**
  - `scripts/00_check.py` plays one game per tier in each arm, and in a pass-through arm, with a scripted stand-in for the model. Each file must pass `score --verify`. The pass-through arm must give the engine each canonical request unchanged. The force arms must not submit before 16 experiments. The count shown at each submission must equal `diagnose`'s classes alive there.
  - One T1 game of `force16-show` on the 4B (`SMOKE=1`) checks the MLX path.

## Games

- **Manifest:** dev (`bench-v1-dev.json`, file sha256 `e99344a3…a5c2`).
- **Subset:** the first 2 items of each family (`--per-family 2`), 102 games: T1 10, T2 14, T3 20, T4 10, T5 34, T6 14. That is 92 headline games, and every family of every tier is played.
- **Games per arm:** 102, one run per arm, the same games in every arm. A stopped run resumes with `--exclude-finished` into a new file, as the same attempt.
- **Seeds:** episode seeds from the manifest. MLX sampler seed 0; each call's sampler seed is a hash of the session seed, the task, the attempt and the decision. Two arms' calls at the same decision of the same game draw from the same random key, while their prompts differ.

## Hypotheses

Each is tested on this experiment's three runs and A8's same 102 games, and nothing else. They were published in the Room before the experiment was proposed. The comparisons with A8 pair the games by task ID (`scripts/03_measures.py`).

1. **Stopping** ([H1](https://thesubstrate.science/records/08f62061-5bf7-4c7a-816d-e3b9351c89d3)). Forced to run 16 experiments before it may submit, Qwen3.5-4B wins more T2-T6 games than without an intervention. Test: the paired headline difference, force16 minus A8 (`compare`'s pairing and t interval), has a 95% CI above 0.
2. **Tracking** ([H2](https://thesubstrate.science/records/5ff5056d-13ab-4c2a-ac45-a54f32d4153b)). Forced to run 16 experiments, Qwen3.5-4B still submits rules that contradict the evidence it has seen. Test: at least 10% of `force16`'s submissions contradict at least one evidence scene (`diagnose`'s `contradicting`). Every E1 system that ran 10 or more experiments a game stayed below 10%: Luna 8.7%, Qwen3.8-27B 1.2%, DeepSeek 1.7%.
3. **Uncertainty** ([H3](https://thesubstrate.science/records/14476cc5-a5a8-4a5f-8ac0-9519c28292bd)). Shown the count of consistent rules, Qwen3.5-4B runs more experiments a game than without an intervention. Test: the per-game difference in experiments (show minus A8, paired by task over the 102 games) has a mean with a 95% t interval above 0.

## Measures

From `score --verify` (`results/scores/<arm>.score.json`):
- **Headline:** the T2-T6 win rate with its 95% CI.
- **Also:** wins per tier and T1; games scored, unscored, abandoned and unfinished; the malformed rate; the seed-only baseline and the w0 bands.

The paired headline differences:
- `force16 − A8`: forcing;
- `show − A8`: the count alone;
- `force16-show − force16`: the count once evidence has been gathered;
- `force16-show − show`: forcing when the count is shown.

The last two are also run as `compare --verify` (`results/scores/<a>__<b>.compare.json`). All four come from `scripts/03_measures.py`, which pairs the A8 comparisons by task ID.

From `diagnose` (`results/scores/<arm>.diagnose.json`), as in E1:
- **Experimenting:** experiments per game, realized bits per experiment, expected information gain, the share of zero-information experiments, repeats.
- **Committing:** classes alive at the first submission (median), win probability at the first submission (`p_first`, mean), submissions per game, certain-but-wrong submissions.
- **Rules submitted:** submissions contradicting the evidence, uptake of the last counterexample.

From `diagnose`'s per-game records (`scripts/03_measures.py`):
- **Conversion:** among the T2-T6 games with a submission, the wins over the summed `p_first`, the wins an ideal player would expect if it submitted when the model first did. It asks how much of the evidence the model turns into wins. In E1, over every T2-T6 game: Luna 0.88, Qwen3.8-27B 0.86, the 4B (A8) 0.31.
- **The paired experiments-per-game differences** for the four pairs above. The `show − A8` difference is hypothesis 3's.

The results table (`results/runs.md`) has one row per arm, A8 included, with its configuration, these numbers and its run files' sha256. The headline numbers go in `results/metrics.json`.

**How the outcomes read:**

| Hypothesis 1 (stopping) | Hypothesis 2 (tracking) | Reading |
|---|---|---|
| holds | fails | a stopping problem: the 4B uses evidence once it has it |
| fails | holds | a tracking problem: more evidence does not reach its submissions |
| holds | holds | both: forcing helps, but its submissions still contradict the evidence |
| fails | fails | neither as defined; read the conversion and the experiment measures |

- **Hypothesis 3** tells whether the stopping decision responds to an uncertainty estimate.
- **The 2×2 interaction** (`force16-show − force16`) tells whether the count helps once the evidence is there.

**Result that would change our mind:** the forcing did not narrow the evidence. If `force16`'s median classes alive at the first submission is above 10 (E1's leaders reached 2 in 14 to 17 experiments), the forced experiments carried too little information. Neither hypothesis 1 nor hypothesis 2 is then read; the problem is choosing experiments.

## Artifacts ruled out

- **Prior, not experimentation:** each headline is reported beside the seed-only baseline and the w0 bands. `p_first` shows how settled the evidence was at the first submission.
- **Contamination:** as E1. The dev rule catalogs are public, and the show arms also tell the model that its rule comes from a finite set of candidates.
- **Budget:** the forced arms make more calls per game; that is the intervention. Every call has the same cap (65,536 tokens), and calls cut at the cap are reported.
- **Format:** the malformed rate is reported beside each headline, though MLX answers are grammar-constrained.
- **Noise:** 92 headline games per arm, every comparison paired on the same games, one run per arm. A difference whose interval includes 0 is reported as no difference measured, not as no effect. A8's 0 wins on the subset is itself a sample; its 12 wins over all 430 headline games are reported beside it.
- **Degenerate stopping:** no training. Submissions per game are reported, and the gate's own effect is the subject of hypothesis 1.

## Records

- **Run files** (`results/runs/`, git-ignored): every game with its reasoning and each call's `intervention` record. They stay with the owner, and each attempt reports them as restricted outputs with their sha256 and size.
- **Committed:** `results/scores/` (score, compare and diagnose summaries), `results/measures.json` (every measure and the verdicts), `results/metrics.json`, `results/runs.md`.
- **In the Room:** one attempt per new arm, citing A8 as the baseline, and findings for the hypotheses and the measures above, each linked to E02's experiment.

## Amendments
