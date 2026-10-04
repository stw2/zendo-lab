# Requirements

## ZendoBench pin

`zendo-engine` 1.0.0 and `zendo-bench` 1.0.0, installed from the tag `v1.0.0` of https://github.com/stw2/zendo-bench (commit `46c192e`). `pyproject.toml` names the tag, and `uv.lock` records the commit. Scores are comparable only on the same ZendoBench version; every run header records it.

To move to a later ZendoBench, change the tag in `pyproject.toml`, run `uv lock`, and say so in the experiments that run on it.

## Backends

| Backend | Install | Notes |
|---|---|---|
| Any OpenAI-compatible HTTP endpoint (hosted providers, vLLM, Ollama) | `uv sync` | `--backend http`. `--sampling` must state `max_tokens` (65,536 by default in the docs). |
| Self-hosted vLLM, sized by `zendo_bench serve-plan` | `uv sync` | `run --batch auto` sizes the games in flight from the server's metrics. |
| Grammared vLLM (`--guided`) | `uv sync --extra grammar` | Brings XGrammar, torch and transformers. |
| Local MLX on Apple silicon | `uv sync --extra mlx` | `--backend mlx`; the thinking budget defaults to 63,487. |
| A Python agent | `uv sync` | `zendo_bench.play(agent, player=...)`. |
| RL rollouts on train items | `uv sync` | `zendo_bench.bench.rl.Episode` and `rollout(policy, item)`. Training libraries are added by the experiment that needs them. |

## Secrets

- **API keys:** from the environment (`--api-key-env NAME`).
- **The Substrate credential:** `SUBSTRATE_TOKEN`, from the environment.
- **ZendoBench's sealed set:** needs the private salt in `~/.zendo-bench-v1.0.0`. Only the owner runs sealed evaluations, and their run files stay outside any git repository.
