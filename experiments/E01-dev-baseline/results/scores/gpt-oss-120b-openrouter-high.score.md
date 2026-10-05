**gpt-oss-120b-openrouter-high** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 31.7 [20.2, 45.1] | 30 | 0.5% |
| T3 | 150 | 150 | 0 | 0 | 28.7 [21.5, 36.7] | 75 | 2.1% |
| T4 | 60 | 60 | 0 | 0 | 0.0 [0.0, 11.6] | 30 | 1.8% |
| T5 | 100 | 100 | 0 | 0 | 5.0 [1.2, 13.0] | 50 | 1.3% |
| T6 | 60 | 60 | 0 | 0 | 5.0 [0.4, 19.9] | 30 | 3.6% |

Headline (T2–T6, equal weights): 14.1 [11.1, 19.2]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 76.7 [52.3, 92.5] | 15 | 0.4% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 13.6 [10.6, 19.0] | 0.0 | 54.9 [24.1, 77.3] |

Configurations for gpt-oss-120b-openrouter-high:

- 521fe0c4e6c4: `{"backend": "openai-chat-completions", "guided": null, "model": "openai/gpt-oss-120b", "sampling": {"max_tokens": 65536, "reasoning": {"effort": "high"}}}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
