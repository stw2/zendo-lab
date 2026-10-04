# Evaluations

An evaluation is part of the experiment that pre-registers it: its run files go in `experiments/E<nn>-<slug>/results/runs/`, and its numbers in that experiment's `results/metrics.json`. No evaluation lives outside an experiment.

## Running one

```bash
uv run python -m zendo_bench run --manifest dev --arm ARM --out results/runs/ARM.jsonl --backend http \
    --base-url URL --model MODEL --api-key-env KEY_ENV --sampling '{"max_tokens": 65536}' --no-stream
uv run python -m zendo_bench score --manifest dev --verify results/runs/ARM.jsonl
uv run python -m zendo_bench compare --manifest dev --a results/runs/A.jsonl --b results/runs/B.jsonl
uv run python -m zendo_bench diagnose --manifest dev results/runs/ARM.jsonl
```

- **Subsets:**
  - `--tiers` (T2–T6 for the headline only);
  - `--first N` (a smoke run);
  - `--per-family N`;
  - `--select FILE` (a pre-registered list of task IDs).
- **A stopped run resumes** with `--exclude-finished ARM.jsonl` into a new file. Score the files together.
- **A local checkpoint** runs with `--backend mlx`, or behind a vLLM server sized by `serve-plan`.
- **Sealed evaluations** are the owner's, run outside the repository. Only their scores and run-file hashes come back.

## What every reported number carries

Arm, model and served model, sampling (with `max_tokens`), backend, manifest and subset, games played and scored, verified (yes), ZendoBench version, seed, hardware class.
