# CALIBRATION CYCLES — the production loop at 20k
One named change per cycle; gates per the locked ruling (attitudes /
anchors / mortality structure / cascade sanity). Provenance per row:
flag set + substrate-table, anchors, income-calibration hashes.

| cycle | change | cohortMAE vs floor | median | $8.30 | CDR | ageAtDeath | 65+ | casc× | verdict | flags | provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c001 | baseline: candidate 0.9 flag set (scorer v2) | 10.95 vs 10.09✗ | $8.49✓ | 52.0%✗ | 0.015✗ | 0.501✓ | — | — | 0.501✓ | **MISS** | (pre-hardening row: no age gates/provenance) | — |
| c002 | income calibration re-derived under C2+ fram | 11.11 vs 9.85✗ | $10.71✗ | 44.2%✓ | 0.015✓ | 49.6✗ | 14.2%✓ | 0.492✓ | **MISS** | MODE=gradient;CALIBRATION=v1;FLAG=c2plus_v1;TABLES=off | t:256fe63229 a:39d484d65f i:1db1b15de3 |
| c003 | income level fixed-point iteration 2 (2.6617 | 10.94 vs 9.88✗ | $9.24✓ | 49.1%✓ | 0.013✓ | 46.0✗ | 14.2%✓ | 0.512✓ | **MISS** | MODE=gradient;CALIBRATION=v1;FLAG=c2plus_v1;TABLES=c2plus_tables_v2.json | t:256fe63229 a:39d484d65f i:89be94309c |
