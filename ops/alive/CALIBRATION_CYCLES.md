# CALIBRATION CYCLES — the production loop at 20k
One named change per cycle; gates per the locked ruling (attitudes /
anchors / mortality structure / cascade sanity). Provenance per row:
flag set + substrate-table, anchors, income-calibration hashes.

| cycle | change | cohortMAE vs floor | median | $8.30 | CDR | ageAtDeath | 65+ | casc× | verdict | flags | provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c001 | baseline: candidate 0.9 flag set (scorer v2) | 10.95 vs 10.09✗ | $8.49✓ | 52.0%✗ | 0.015✗ | 0.501✓ | — | — | 0.501✓ | **MISS** | (pre-hardening row: no age gates/provenance) | — |
| c002 | income calibration re-derived under C2+ fram | 11.11 vs 9.85✗ | $10.71✗ | 44.2%✓ | 0.015✓ | 49.6✗ | 14.2%✓ | 0.492✓ | **MISS** | MODE=gradient;CALIBRATION=v1;FLAG=c2plus_v1;TABLES=off | t:256fe63229 a:39d484d65f i:1db1b15de3 |
| c003 | income level fixed-point iteration 2 (2.6617 | 10.94 vs 9.88✗ | $9.24✓ | 49.1%✓ | 0.013✓ | 46.0✗ | 14.2%✓ | 0.512✓ | **MISS** | MODE=gradient;CALIBRATION=v1;FLAG=c2plus_v1;TABLES=c2plus_tables_v2.json | t:256fe63229 a:39d484d65f i:89be94309c |
| c003×4 | seed-noise floor (4242/5151/6363/7777) | σ(MAE)=0.155, gap 1.06pp = 6.8σ REAL | σ$0.06 | σ0.7pt | σ.002 | σ3.2 | σ0.3pt | σ.02 | — | (noise row) | data/cycles/noise_floor.json |
| c004 | DECOMPOSITION, no fix: cohort miss by axis | age +0.91 > income +0.73 > sex +0.72 > age×edu +0.65 > edu +0.48 (broad under-modulation, age worst) | — | — | — | — | — | — | **NAMED: age** | same flags | data/cycles/c004_decomposition.json |
| c005 | SLOPE DIAGNOSTIC, no fix (+4-seed pooling discriminator) | slopes DIFFER by axis: sex 0.05/r.01, income 0.29/r.19, age 0.31/r.21, edu 0.36/r.26; model dev sd > WVS sd; pooling 4x left r unchanged ⇒ PHYSICS not noise, not global readout shrinkage. Sex coupling nonexistent (mechanism absent); age/income/edu present but ~3x weak + wrong-pattern | — | — | — | — | — | — | **NAMED: physics, age first; sex needs a mechanism (own cycle)** | same flags | data/cycles/c005_slope_diag.json |
