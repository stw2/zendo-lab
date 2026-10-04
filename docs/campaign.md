# Campaign

## Question

Can training teach small open-weight models active rule induction: choosing experiments to find a hidden rule, and committing only when the evidence settles it?

## Observation

In ZendoBench, small open-weight models commit after a handful of experiments, while many rules are still consistent with the evidence, and rarely win. Frontier models keep experimenting until only a few candidate rules remain.

## Questions this Room asks

1. Which training signal improves the behaviour: supervised traces, reinforcement learning on wins, or rewards for the decision to stop?
2. Do gains come from better experimentation, or from learned priors over the benchmark's rules?

## Instrument

ZendoBench 1.0.0. A game is Zendo against a hidden rule over scenes of 1 to N pieces. The player runs experiments (it builds a scene, the rule labels it) and submits rules, within a budget.

- **Tiers:** T2–T6 form the headline, an equal-weight mean. T1 is diagnostics only.
- **Splits:**
  - **train:** for training, sampled with `train-sample`;
  - **dev:** 460 items, for development;
  - **sealed:** for final evaluations only, private.
- **What each game records:** every experiment, submission and verdict. `diagnose` and the analysis fields (p0, w0, the seed-only baseline) separate experimentation from priors: question 2 above.
