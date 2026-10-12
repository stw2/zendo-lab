**qwen3.5-4b-mlx-force16-show** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 14 | 0 | 46 | 50.0 [19.4, 80.6] | 7 | 0.0% |
| T3 | 150 | 20 | 0 | 130 | 50.0 [20.3, 79.7] | 10 | 0.0% |
| T4 | 60 | 10 | 0 | 50 | 0.0 [0.0, 52.2] | 5 | 0.5% |
| T5 | 100 | 34 | 0 | 66 | 11.8 [2.1, 32.4] | 17 | 0.0% |
| T6 | 60 | 14 | 0 | 46 | 0.0 [0.0, 41.0] | 7 | 0.0% |

Headline (T2–T6, equal weights): 22.4 [13.6, 38.7]
partial: 92 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 10 | 0 | 20 | 80.0 [44.4, 97.5] | 5 | 0.0% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 21.2 [12.6, 37.7] | – | 33.3 |

Configurations for qwen3.5-4b-mlx-force16-show:

- d0868b7d4930: `{"agent": "e02-intervention-v1", "agent_config": {"arm": "force16-show", "force_experiments": 16, "show_consistent_rules": true}, "agent_source_sha256": "ded59be23e3d236c3c63210803e7e3c1e0c4583663fd9c60c4345b84c275c4b6", "backend": "mlx", "decoding": {"action_allowance": 2048, "action_temperature": 1.0, "min_p": 0.0, "presence_penalty": 1.5, "seed": 0, "temperature": 1.0, "thinking": true, "thinking_budget": 63487, "top_k": 20, "top_p": 0.95}, "local_model": {"model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}, "model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "settings": {"compile_threads": 8, "completion_batch_size": 36, "prefill_batch_size": 1}, "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}`

Coverage (scored / manifest): T1: 5/15 classes, 5/5 families; T2: 7/30 classes, 7/7 families; T3: 10/75 classes, 10/10 families; T4: 5/30 classes, 5/5 families; T5: 17/50 classes, 17/17 families; T6: 7/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 3.3%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
