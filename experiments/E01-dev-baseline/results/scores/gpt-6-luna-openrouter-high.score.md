**gpt-6-luna-openrouter-high** on the dev manifest (6b98d1a59d5f)

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T2 | 60 | 60 | 0 | 0 | 75.0 [60.7, 86.2] | 30 | 0.8% |
| T3 | 150 | 150 | 0 | 0 | 83.3 [76.2, 89.1] | 75 | 1.2% |
| T4 | 60 | 60 | 0 | 0 | 6.7 [1.6, 17.1] | 30 | 2.5% |
| T5 | 100 | 100 | 0 | 0 | 33.0 [23.8, 43.2] | 50 | 1.4% |
| T6 | 60 | 60 | 0 | 0 | 26.7 [15.7, 40.2] | 30 | 2.0% |

Headline (T2–T6, equal weights): 44.9 [40.5, 49.6]
complete: 430 of 430 headline items finished; verified: every finished game replays to its recorded engine record

Diagnostics (not in the headline):

| Tier | Items | Scored | Unscored | Unfinished | Win rate, % [95% CI] | Classes | Malformed rate |
|---|---|---|---|---|---|---|---|
| T1 | 30 | 30 | 0 | 0 | 93.3 [77.8, 99.2] | 15 | 0.3% |

| w0 band (pooled over the headline tiers) | w0=0 | 0<w0<0.5 | w0>=0.5 |
|---|---|---|---|
| estimate | 44.0 [39.4, 48.8] | 55.6 | 75.7 [43.9, 96.7] |

Configurations for gpt-6-luna-openrouter-high:

- 1f7145415780: `{"backend": "openai-chat-completions", "guided": null, "model": "openai/gpt-6-luna", "sampling": {"max_tokens": 65536, "reasoning": {"effort": "high"}}}`

Coverage (scored / manifest): T1: 15/15 classes, 5/5 families; T2: 30/30 classes, 7/7 families; T3: 75/75 classes, 10/10 families; T4: 30/30 classes, 5/5 families; T5: 50/50 classes, 17/17 families; T6: 30/30 classes, 7/7 families.
Seed-only MAP baseline on the scored items: 4.7%. One submission from seeds, no experiments; expected win rate with uniform MAP tie breaking on scored items, equal weight per headline tier.
T1-T4 share the 3-piece catalog prior because their tier is not revealed; T5 and T6 use their registered tier classes.
Rule catalogs are public and include classes used in experiments while this benchmark was developed. Sealed items hide seed pairs, not the rule universe. This benchmark does not establish contamination-free reasoning.
