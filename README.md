# Zendo lab: learning to test hypotheses

Can training teach small open-weight models active rule induction: choosing experiments to find a hidden rule, and committing only when the evidence settles it?

The game is Zendo against a hidden rule, close to exact learning from membership and equivalence queries. Zendo is a game by Kory Heath, published by Looney Labs; this project is not affiliated with them. The benchmark is [ZendoBench](https://github.com/stw2/zendo-bench) 1.0.0: the packages `zendo-engine` (the game) and `zendo-bench` (tiers, prompts, model backends, runs, scoring, training data).

This repository holds each experiment's pre-registered design, code, configurations, raw results and report. Hypotheses, experiments, plans, attempts, materials and findings are in the Substrate research Room [**Learning to test hypotheses**](https://thesubstrate.science/rooms/learning-to-test-hypotheses-da73e44a), which is authoritative where the two disagree. The project website is at [https://www.wiland.ai/projects/zendorl/](wiland.ai/projects/zendorl)

## Where things live

| What | Where |
|---|---|
| One experiment | `experiments/E<nn>-<slug>/`, from [`docs/experiment-template/`](docs/experiment-template/) |
| The question and why it matters | [`docs/campaign.md`](docs/campaign.md) |
| Rules, splits, artifacts to rule out, experiment folders | [`docs/conventions.md`](docs/conventions.md) |
| The ZendoBench pin, backends, extras, secrets | [`docs/requirements.md`](docs/requirements.md) |
| How evaluations are run and reported | [`evals/README.md`](evals/README.md) |
| Instructions for agents (Claude Code, Codex) | [`AGENTS.md`](AGENTS.md) |

## Setup

```bash
uv sync                      # Python 3.12+, ZendoBench 1.0.0 from its v1.0.0 tag
uv run pytest                # checks the pin and plays one game
uv run python -m zendo_bench --help
```

Extras: `uv sync --extra mlx` (local inference on Apple silicon), `uv sync --extra grammar` (grammared vLLM runs).
