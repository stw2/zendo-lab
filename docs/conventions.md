# Conventions

## Rules

1. **Splits are fixed.**
   - Train only on the train split (`zendo_bench train-sample`, `zendo_bench.bench.rl.Episode`, which refuses anything else).
   - Develop on dev.
   - Evaluate on sealed only for a final result.
   - Never train on dev or sealed items or their rules.
2. **Score with `--verify`.** Report unscored and unfinished counts beside the headline.
3. **Every number carries its context:** arm, model, sampling (with `max_tokens`), backend, manifest and subset, games, seed, hardware class.
4. **A surprising result is an artifact until ruled out.** Check the list below.
5. **No credentials, host names, home paths or private data** in commits or Room records. Keys and `SUBSTRATE_TOKEN` come from the environment, and the ZendoBench secret folder never enters a repository.
6. **Trajectories stay on this machine.** Run files hold every game and its reasoning (`--keep-reasoning` on HTTP; MLX keeps it already). They go in `results/runs/`, which git ignores. Git and the Room get their statistics and their sha256. A run file is never edited after it is hashed.

## Artifacts to rule out

- **Prior, not experimentation:** the gain comes from guessing likely rules. Compare with the seed-only baseline and the p0/w0 bands.
- **Contamination:** the rules were seen in training or pretraining. Check the exposure counts ZendoBench ships.
- **Budget:** more tokens or thinking explain the gain.
- **Format:** the gain is fewer malformed replies, not better play.
- **Noise:** a small n across many arms.
- **Degenerate stopping:** a stopping reward learned as "never submit" or "submit at once".

## Experiments

- **One folder per experiment,** `experiments/E<nn>-<slug>/`, copied from [`docs/experiment-template/`](experiment-template/).
- **Take the experiment in the Room first, then commit its `DESIGN.md` before measuring.** Changes after that are dated amendments at the end of the file. Results come in later commits.
- **`scripts/`** are numbered in run order and write into `results/`. Run files go in `results/runs/` and stay out of git. Committed beside them:
  - `results/runs.md`: one row per run, with its configuration, results and run-file sha256;
  - `results/scores/`: each run's `score --verify --json` and `diagnose` output;
  - `results/metrics.json`: the headline numbers (flat, name to number).
- **Large or re-fetchable artifacts, such as checkpoints, stay out of git.** A script fetches or rebuilds them.
- **A rerun is a new attempt in the Room, not an edit.**
