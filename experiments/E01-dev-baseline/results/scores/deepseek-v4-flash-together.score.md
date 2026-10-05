**deepseek-v4-flash-together** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 55.0 [41.3, 68.1] | 30 | 5.2% |
| T3 | 150 | 150 | 0 | 0 | 52.0 [43.6, 60.4] | 75 | 6.3% |
| T4 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 24.1% |
| T5 | 100 | 100 | 0 | 0 | 9.0 [4.1, 16.7] | 50 | 10.8% |
| T6 | 60 | 60 | 0 | 0 | 15.0 [6.8, 27.3] | 30 | 17.2% |

Headline (T2–T6, equal weights): 26.2 [22.5, 31.0]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 90.0 [73.5, 97.9] | 15 | 2.2% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 25.1 [21.3, 30.2] | 0.0 | 57.6 [29.6, 79.1] |

Configurations for deepseek-v4-flash-together:

- ea021325cd47: `{"backend": "openai-chat-completions", "guided": null, "model": "deepseek-ai/DeepSeek-V4-Flash-0731", "sampling": {"max_tokens": 65536}}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
