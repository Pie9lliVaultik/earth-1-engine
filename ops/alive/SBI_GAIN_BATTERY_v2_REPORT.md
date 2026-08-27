# SBI GAIN BATTERY v2 — REPORT
2026-08-27. Prereg SBI_GAIN_BATTERY_v2_PREREG.md. 200k×180d, 2,000
training sims, mortality-structure summaries, fresh sealed truths
(hash aca8ca48 logged at plant, pre-inference).

## GATE: MORTALITY_GAIN_LEARNING_ELIGIBLE = **YES**
hardship_mortality_gain: **RECOVERED by all three methods, 5/5 sealed
exams each** — ABC cov 0.88 sd 0.80×prior; **NPE cov 0.875 sd 0.64×
prior (meets the registered <0.7× contraction gate; BANKED)**; NRE cov
0.875 sd 0.69×. The observation redesign did it (the 90d/600-sim v1
battery had this parameter at prior width / 3-of-5 exams).
informal_floor_scale: NOT eligible — NRE passes the tree at 0.99×prior
(calibrated but uninformative); no method contracts. Its identifiable
content at these scales is ~nil; further pursuit needs a different
observable (household/welfare-flow summaries), not more sims.
Also banked: critical_fraction NPE 0.56×prior at 180d (stronger than
v1); relax/memory_press remain strongly identified (0.06×/0.09× where
coverage holds; ABC/NRE over-cover conservatively as before).

## Binding caveat (founder ruling, standing)
Eligibility is banked UNDER THE PHYSICS IT TESTED — the v4.1 binary-
hardship cliff. The 0.9 candidate replaces that transfer function, and
the distribution feeding the gain changes with it. Before any
real-data fitting of hardship_mortality_gain on the candidate physics,
identifiability must be RE-EARNED under the gradient (same battery,
gradient flag on). Do not port the estimator across physics.
