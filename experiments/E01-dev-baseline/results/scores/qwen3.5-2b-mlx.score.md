**qwen3.5-2b-mlx** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 0.0% |
| T3 | 150 | 150 | 0 | 0 | 0.0 [0.0, 4.8] | 75 | 0.0% |
| T4 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 0.0% |
| T5 | 100 | 100 | 0 | 0 | 0.0 [0.0, 7.1] | 50 | 0.0% |
| T6 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 0.0% |

Headline (T2–T6, equal weights): 0.0 [0.0, 4.4]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 6.7 [0.1, 33.2] | 15 | 0.0% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 0.0 [0.0, 4.5] | 0.0 | 0.0 [0.0, 37.3] |

Configurations for qwen3.5-2b-mlx:

- 3e6574cce032: `{"backend": "mlx", "decoding": {"action_allowance": 2048, "action_temperature": 1.0, "min_p": 0.0, "presence_penalty": 1.5, "seed": 0, "temperature": 1.0, "thinking": true, "thinking_budget": 63487, "top_k": 20, "top_p": 0.95}, "local_model": {"model": "Qwen/Qwen3.5-2B", "model_sha256": "94be2130fa9bf7d2aabd56e8eb09f8550dc7062adda4b23e6ba6a473682a0d16", "revision": "15852e8c16360a2fea060d615a32b45270f8a8fc", "tokenizer_sha256": "b060123e43361f30d80090aff95c3abdf6140b2e859e0ccc18222fed6d164528"}, "model": "Qwen/Qwen3.5-2B", "model_sha256": "94be2130fa9bf7d2aabd56e8eb09f8550dc7062adda4b23e6ba6a473682a0d16", "revision": "15852e8c16360a2fea060d615a32b45270f8a8fc", "settings": {"compile_threads": 8, "completion_batch_size": 36, "prefill_batch_size": 1}, "tokenizer_sha256": "b060123e43361f30d80090aff95c3abdf6140b2e859e0ccc18222fed6d164528"}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
