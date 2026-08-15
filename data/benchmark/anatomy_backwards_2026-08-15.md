# Anatomy backwards — G5 run #6 per-question autopsy (2026-08-15)

Resolved outcomes (WVS W6->W7 deltas) vs the engine's per-question
temporal performance, attributed through calibrated force weights.

## Finding: failure concentrates in high-|w| questions
- max|w| >= 1.0: engine loses to no-change 6/7
  (homosexuality 2.38, religion 1.90, trust 1.29, abortion 1.14,
   men_leaders 1.20, two_parent 1.13, divorce 1.02; only army_rule wins)
- max|w| <  1.0: engine wins 6/7
  (tech 0.32, hard_work 0.34, death_penalty 0.46, life_sat 0.74,
   democracy 0.80; only environment 0.55 loses)

## Mechanism
Large weights amplify endogenous drift noise into overshoot. The
strongly culture-structured questions are where aimless drift does the
most damage — and simultaneously where real change is cohort-driven
(signal the world does not yet receive).

## Candidate mechanism (for A3 pre-registration, NOT yet built)
Uncertainty shrinkage: temporal delta prediction shrunk toward
no-change proportional to weight-scaled drift variance, estimated from
t0 calibration residuals ONLY (never the held-out wave).

## Force-level tally (dominant force -> engine wins/losses)
collective 2/5 · identity 2/3 · culture 2/0 · experience 1/0
