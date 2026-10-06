**qwen3.8-27b-fp8-vllm-h100** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 83.3 [70.7, 92.1] | 30 | 0.3% |
| T3 | 150 | 150 | 0 | 0 | 78.7 [71.1, 85.1] | 75 | 0.6% |
| T4 | 60 | 60 | 0 | 0 | 8.3 [2.6, 18.8] | 30 | 1.2% |
| T5 | 100 | 100 | 0 | 0 | 34.0 [24.7, 44.3] | 50 | 0.9% |
| T6 | 60 | 60 | 0 | 0 | 18.3 [9.3, 30.9] | 30 | 1.0% |

Headline (T2–T6, equal weights): 44.5 [40.4, 49.0]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 96.7 [82.4, 99.9] | 15 | 0.9% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 44.0 [39.7, 48.5] | 44.4 | 74.7 [43.2, 95.7] |

Configurations for qwen3.8-27b-fp8-vllm-h100:

- 2003cab037b8: `{"backend": "openai-chat-completions", "guided": null, "model": "qwen3.8-27b-fp8", "sampling": {"chat_template_kwargs": {"reasoning_effort": "xhigh"}, "max_tokens": 65536, "presence_penalty": 0.0, "temperature": 1.0, "top_k": 20, "top_p": 0.95}}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
