# E01: Baseline on dev

Room experiment: [E1](https://thesubstrate.science/experiments/68717b8a-db66-4b17-a98d-672fddbaa9a9), in the Thread [Campaign: can training teach small models to test hypotheses?](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a/threads/6cdedae4-ec06-4e7c-9462-ccf16fec373b). Locked at the commit that adds this file; changes are dated amendments at the end.

## Question

Where do small and strong models stand on ZendoBench 1.0.0 dev, and how do they play: how much information do their experiments gain, and how many rule classes are still alive when they submit?

E01 is descriptive: it tests no hypothesis. It fixes the reference points the training experiments are compared with.

## Arms

| Arm | Model | Backend and hardware | Sampling |
|---|---|---|---|
| `qwen3.5-2b-mlx` | `Qwen/Qwen3.5-2B` bf16, revision `15852e8c`, shard hash in `scripts/checkpoints/qwen3.5-2b.json` | ZendoBench MLX batch driver, Apple M4 Max 128 GB, 36 games in flight, sampler seed 0 | ZendoBench's Qwen3.5 thinking defaults: temperature 1.0, top-p 0.95, top-k 20, min-p 0, presence penalty 1.5; thinking budget 63,487 + 2,048-token answer allowance (the default; a call's cap is 65,536) |
| `qwen3.5-27b-fp8-vllm-h100` | `Qwen/Qwen3.5-27B-FP8`, revision `97f5941b` | vLLM 0.30.0, one H100 80 GB (Daytona, on-demand), games in flight `--batch auto` | temperature 1.0, top-p 0.95, top-k 20, min-p 0, presence penalty 1.5 (as the 2B); `max_tokens` 65,536 |
| `qwen3.8-27b-fp8-vllm-h100` | `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7a` | as above | temperature 1.0, top-p 0.95, top-k 20, presence penalty 0, `reasoning_effort` xhigh (the template's default); `max_tokens` 65,536 |
| `deepseek-v4-flash-together` | `deepseek-ai/DeepSeek-V4-Flash-0731` | Together serverless, 64 calls in flight | the provider's defaults; `max_tokens` 65,536 |
| `gpt-oss-120b-openrouter-high` | `openai/gpt-oss-120b` | OpenRouter, default provider routing, 64 calls in flight | reasoning effort high; `max_tokens` 65,536 |
| `gpt-6-luna-openrouter-high` | `openai/gpt-6-luna` | OpenRouter, 64 calls in flight | reasoning effort high; `max_tokens` 65,536 |

Each model runs at its publisher's recommended thinking settings; the two Qwen 27B arms therefore differ in presence penalty as well as in training.

**Held fixed:** ZendoBench 1.0.0 (tag `v1.0.0`, commit `46c192e`), player `model`, the default reply policy, one output cap of 65,536 tokens a call, the dev manifest, reasoning kept in the run file (`--keep-reasoning` over HTTP; the MLX driver keeps it).

**Recorded, not held fixed:** games or calls in flight, the provider a router picked, the vLLM server's flags (`scripts/daytona/serve.sh`, from `zendo_bench serve-plan`).

**Before each arm:** a server or connection check, not a measurement and not reported: the Daytona boxes check the model's files against the Hub's hashes and answer one short chat completion before the run starts.

## Games

- **Manifest:** dev (`bench-v1-dev.json`, file sha256 `e99344a3…a5c2`, manifest hash `6b98d1a5…`), all 460 items: T1 30, T2 60, T3 150, T4 60, T5 100, T6 60.
- **Games per arm:** 460, one run per arm. A stopped run resumes with `--exclude-finished` into a new file, and the files are scored together; a resumed run is the same attempt.
- **Seeds:** the episode seeds come from the manifest. The MLX sampler uses seed 0; the APIs and vLLM are not seeded.

## Measures

From `score --verify` (`results/scores/<arm>.score.json`):

- **Headline:** the equal-weight mean win rate over T2-T6 with its 95% CI.
- Wins per tier and T1; games scored, unscored and unfinished; the malformed rate; the seed-only baseline and the w0 bands beside the headline.

From `diagnose` (`results/scores/<arm>.diagnose.md`; all games, wins, losses and each tier):

- **Experimenting:** experiments per game, realized bits per experiment, expected information gain, the share of zero-information experiments, repeats.
- **Committing:** classes alive and the win probability at the first submission, submissions per game, certain-but-wrong submissions.
- **Rules submitted:** node count against the truth's, simpler classes passed over, excess `or`, relational operators outside the tier, rules contradicting the evidence, uptake of counterexamples.

From the run files: tokens in, out and reasoning; calls cut at `max_tokens`; wall time; cost at list price (Daytona from its ledger).

`results/runs.md` holds one row per arm with its configuration, these numbers and its run files' sha256; `results/metrics.json` holds the headline numbers.

**Result that would change our mind.** The campaign assumes that small models submit early, with many classes alive, and rarely win. If `qwen3.5-2b-mlx` submits first with few classes alive (median `alive_first` at most 2, or `p_first` at least 0.5) or its headline lies inside a 27B arm's CI, the premise fails on this benchmark and the training experiments need another target.

## Artifacts ruled out

- **Prior, not experimentation:** each headline is reported beside the seed-only baseline and the w0 bands, and `p_first` shows how much of a win was decided before experimenting.
- **Contamination:** the dev rule catalogs are public, and ZendoBench's exposure note applies. E01 makes no claim of contamination-free reasoning.
- **Budget:** one output cap for every arm. Tokens per game and calls cut at the cap are reported. Reasoning effort differs by model as listed.
- **Format:** the malformed rate is reported beside each headline.
- **Noise:** 460 games per arm; arms are compared only where CIs separate.
- **Degenerate stopping:** no training here; submissions per game and `p_first` are reported for later comparison.

## Records

- **Run files** (`results/runs/`, git-ignored): every game with the reasoning. They stay with the owner; each attempt reports them as restricted outputs with their sha256 and size.
- **Committed:** `results/scores/` (score and diagnose summaries), `results/runs.md`, `results/metrics.json`.
- **Budget:** about $300-370 at list price. Each Daytona box stops at $200 or 34 hours, whichever comes first ($240 for A5 from 2026-10-05, see Amendments), and its server-side TTL is renewed only while its guard runs.

## Amendments

- **2026-10-06, corrections found in review, before any finding was published.**
  - **Providers:** the run files do not record which provider OpenRouter routed each call to. "The provider a router picked" under *Recorded, not held fixed* was wrong. The gpt-oss and Luna arms are "OpenRouter default routing, provider not recorded"; the harness logged only system fingerprint changes.
  - **Malformed rates across backends:** ZendoBench's MLX driver constrains the 2B and 4B arms' answers to valid actions and force-stops thinking at the budget. Their malformed rate (0) and cap hits (0) are therefore not comparable with the HTTP arms'.
  - **Scope of the behaviour measures:** `diagnose` covers all 460 games, including T1, while the headline covers T2-T6 (430). `alive_first` is a median and `p_first` a mean, over games with at least one submission.
  - **DeepSeek:** its headline is limited by the output cap. 708 of 6,146 calls were cut, and they account for 702 of its 721 malformed headline turns.

- **2026-10-05, A5 (`qwen3.8-27b-fp8-vllm-h100`): box replaced.**
  - **What happened:** at 05:58Z the first H100 box stopped answering. Its Daytona preview returned HTTP 502 (5 games exhausted their retries), then timed out, and its command channel returned 502. The harness's breaker stopped the run with exit 4. 129 games had finished; the 31 unfinished games are replayed.
  - **Recovery:** the box was deleted at 06:03Z; Daytona still showed it destroying at 07:20Z. A new box with the same image, model revision, vLLM version and server flags was set up at 07:27Z, and the run resumed into `qwen3.8-27b-fp8-vllm-h100.part2.jsonl` with `--exclude-finished`, as the same attempt.
  - **Script change:** `scripts/daytona/ctl.py` now gives each sandbox a numbered name, because the replaced box may still hold the old one. Nothing that affects a measurement changed.
  - **Cap:** the $200 cap covers both boxes together.
- **2026-10-05, A5's cost cap raised to $240.** At 19:36Z the three boxes had spent $97.36, and the remaining 177 games (T4-T6, the longest) projected to about $96 more, close to the $200 stop. At the owner's request the cap is now $240 (the guard stops at $238). Nothing else changed.
- **2026-10-05, A5 (`qwen3.8-27b-fp8-vllm-h100`): second box lost; resumed on a third.**
  - **What happened:** the guard's Daytona credential (the CLI's 24-hour login) expired at 09:36Z, so the box's server-side TTL was no longer renewed, and Daytona destroyed the box at about 12:30Z. The run's breaker then stopped part 2. 223 games had finished across parts 1 and 2; the rest are replayed.
  - **Recovery:** a third box with the same image, model revision, vLLM version and server flags was set up at 14:40Z, and the run resumed into `.part3` with `--exclude-finished` over parts 1 and 2, as the same attempt.
  - **Script changes:** `scripts/daytona/ctl.py` takes a non-expiring `DAYTONA_API_KEY` from `.env` before the CLI login, and `guard.py` rebuilds its client after an authentication error. Nothing that affects a measurement changed.
  - **Lost process:** part 2's wrapper and its guard ended without writing exit records; the cause is not known.
- **2026-10-05, a seventh arm: `qwen3.5-4b-mlx`.**
  - **Model:** `Qwen/Qwen3.5-4B` bf16, revision `851bf6e8`, ZendoBench's built-in checkpoint (`--checkpoint 4B`, shard hashes pinned in ZendoBench).
  - **Settings:** as `qwen3.5-2b-mlx`: ZendoBench MLX batch driver, Apple M4 Max 128 GB, 36 games in flight, sampler seed 0, the same Qwen3.5 thinking sampling and default thinking budget (63,487 + 2,048; a call's cap is 65,536), all 460 dev games.
  - **When:** added at the owner's request after the first six arms had started, and before any 4B game was played. It is registered as its own attempt under a revised plan; the other arms are unchanged.
