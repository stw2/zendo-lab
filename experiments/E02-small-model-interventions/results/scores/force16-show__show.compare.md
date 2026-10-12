**qwen3.5-4b-mlx-force16-show vs qwen3.5-4b-mlx-show** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Difference qwen3.5-4b-mlx-force16-show - qwen3.5-4b-mlx-show, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T2 | 60 | 14 | 0 | 46 | 35.7 [-8.3, 79.7] | 7 |
| T3 | 150 | 20 | 0 | 130 | 40.0 [7.1, 72.9] | 10 |
| T4 | 60 | 10 | 0 | 50 | 0.0 | 5 |
| T5 | 100 | 34 | 0 | 66 | 11.8 [-2.7, 26.2] | 17 |
| T6 | 60 | 14 | 0 | 46 | 0.0 | 7 |

Headline (T2–T6, equal weights): 17.5 [7.2, 27.8]
partial: 92 of 430 headline items finished in both arms; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Difference qwen3.5-4b-mlx-force16-show - qwen3.5-4b-mlx-show, pts [95% CI] | Classes |
|---|---|---|---|---|---|---|
| T1 | 30 | 10 | 0 | 20 | 30.0 [-4.0, 64.0] | 5 |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 16.2 [5.8, 26.5] | – | 33.3 |

A paired interval is unavailable where the observed class differences have zero variance.

Configurations for qwen3.5-4b-mlx-force16-show:

- d0868b7d4930: `{"agent": "e02-intervention-v1", "agent_config": {"arm": "force16-show", "force_experiments": 16, "show_consistent_rules": true}, "agent_source_sha256": "ded59be23e3d236c3c63210803e7e3c1e0c4583663fd9c60c4345b84c275c4b6", "backend": "mlx", "decoding": {"action_allowance": 2048, "action_temperature": 1.0, "min_p": 0.0, "presence_penalty": 1.5, "seed": 0, "temperature": 1.0, "thinking": true, "thinking_budget": 63487, "top_k": 20, "top_p": 0.95}, "local_model": {"model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}, "model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "settings": {"compile_threads": 8, "completion_batch_size": 36, "prefill_batch_size": 1}, "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}`

Configurations for qwen3.5-4b-mlx-show:

- 6438d68b0db0: `{"agent": "e02-intervention-v1", "agent_config": {"arm": "show", "force_experiments": null, "show_consistent_rules": true}, "agent_source_sha256": "ded59be23e3d236c3c63210803e7e3c1e0c4583663fd9c60c4345b84c275c4b6", "backend": "mlx", "decoding": {"action_allowance": 2048, "action_temperature": 1.0, "min_p": 0.0, "presence_penalty": 1.5, "seed": 0, "temperature": 1.0, "thinking": true, "thinking_budget": 63487, "top_k": 20, "top_p": 0.95}, "local_model": {"model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}, "model": "Qwen/Qwen3.5-4B", "model_sha256": "76eef3317d2e81bba118981981c38e0ccbd267fdcda9689e531a20ebdc3703a2", "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", "settings": {"compile_threads": 8, "completion_batch_size": 36, "prefill_batch_size": 1}, "tokenizer_sha256": "2cc0b586a258eb03d2369016d2dbd0422d7eb86ee8a2cfcfb6fe037a11dcc543"}`
