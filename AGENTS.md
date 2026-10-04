# Instructions for agents

This repository serves the Substrate research Room **Learning to test hypotheses**: https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a. The Room is authoritative; read it before you work.

## Connect to the Room

1. **The credential** is in `SUBSTRATE_TOKEN`; the owner issues it in the Room's **Agent access** sidebar. Never print it, write it to a file, commit it or put it in a record.
2. **The skill:** install it once, if `~/.claude/skills/substrate-research/SKILL.md` is missing:
   ```bash
   mkdir -p ~/.claude/skills/substrate-research
   curl -fsSL https://thesubstrate.science/api/research/skill -o ~/.claude/skills/substrate-research/SKILL.md
   ```
3. **First reads:** use the `substrate-research` skill against https://thesubstrate.science with `SUBSTRATE_TOKEN`. Read your identity, then the Room's research context, before proposing or recording anything.

## Work

- **Follow [`docs/conventions.md`](docs/conventions.md):** take the experiment in the Room first, commit `DESIGN.md` before measuring, and record reruns as new attempts.
- **Experiments go in `experiments/E<nn>-<slug>/`,** copied from `docs/experiment-template/`.
- **Splits:** train only on the train split; dev is for development; sealed is the owner's, for final results only.
- **Score every run with `--verify`.** Report the arm, model, sampling, backend, manifest, number of games, seed and hardware class with every number.
- **Don't patch ZendoBench.** It is pinned to its `v1.0.0` tag. If it needs a change, open an issue at https://github.com/stw2/zendo-bench.
- **No credentials, host names, home-directory paths or private data** in any commit or Room record.

## Commands

```bash
uv sync                                            # setup (extras: --extra mlx, --extra grammar)
uv run pytest                                      # checks the ZendoBench pin and plays one game
uv run python -m zendo_bench train-sample --n 60 --seed 1 --out train.json
uv run python -m zendo_bench run --manifest dev --arm ARM --out run.jsonl --backend http \
    --base-url URL --model MODEL --api-key-env KEY_ENV --sampling '{"max_tokens": 65536}' --keep-reasoning
uv run python -m zendo_bench score --manifest dev --verify run.jsonl
```
