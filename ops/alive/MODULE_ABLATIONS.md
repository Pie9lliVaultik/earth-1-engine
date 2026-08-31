# MODULE ABLATIONS — acceptance test (iv), v4.2 §4.2.3
Each mechanism touched this week, disabled on the benchmark built to
exercise it. Paired artifacts in data/cycles/ablations/ + named files.

| mechanism | exercised gate | OFF -> ON | pair provenance |
|---|---|---|---|
| hardship gradient | dep>0.5 share | 0.388 -> 0.116 | cliff pair (seed 4242, paired CRN) |
| C2+ substrate | pov$3 headcount | 0.365 -> 0.411 | substrate pair (paired CRN) |
| income calibration | median $/day | 3.77 -> 9.24 | OFF run tonight vs final |
| GM mortality | frozen-cell attitude MAE (side-check) | 12.00 -> 11.88 | frozen scorer pair |
| WANT->RR fold | starved external deaths | 36 -> 0 | OFF run tonight vs fold |
| weather scale | ageAtDeath (200k census) | 63.7 -> 67.2 | FP4 vs cweather, paired seed |

All six mechanisms move their own gate; none was inert in ablation.
(The c006 demo-force gradient was INERT and its flag is OFF — recorded
in its own row; not part of the candidate.)
