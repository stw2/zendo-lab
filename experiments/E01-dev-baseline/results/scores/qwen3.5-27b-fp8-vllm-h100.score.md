**qwen3.5-27b-fp8-vllm-h100** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 25.0 [14.6, 38.1] | 30 | 5.5% |
| T3 | 150 | 150 | 0 | 0 | 20.0 [13.8, 27.5] | 75 | 7.5% |
| T4 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 8.7% |
| T5 | 100 | 100 | 0 | 0 | 7.0 [2.6, 14.7] | 50 | 7.3% |
| T6 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 9.9% |

Headline (T2–T6, equal weights): 10.4 [7.8, 15.1]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 46.7 [25.9, 68.4] | 15 | 7.0% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 10.6 [7.9, 15.5] | 0.0 | 19.8 [2.9, 49.3] |

Configurations for qwen3.5-27b-fp8-vllm-h100:

- e5ac48d097c0: `{"backend": "openai-chat-completions", "guided": null, "model": "qwen3.5-27b-fp8", "sampling": {"max_tokens": 65536, "min_p": 0.0, "presence_penalty": 1.5, "temperature": 1.0, "top_k": 20, "top_p": 0.95}}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
