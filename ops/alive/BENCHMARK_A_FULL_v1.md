# BENCHMARK A — FULL TABLE v1 (cycle A-FULL-1, measurement only)

**Date:** 2026-08-31 · **Change:** none (B1: measure, do not fix)
**Flag set (recorded at run):** EARTH1_SUBSTRATE=c2plus_v1 · C2PLUS_TABLES=c2plus_tables_v2.json ·
HARDSHIP_MODE=gradient · INCOME_CALIBRATION=v1 (joint-MSM θ) · MORTALITY=gompertz ·
GM_OTHER_SHARE=0.2141 · WANT_MODE=rr (RR 4.934) · WEATHER_SCALE=0.0203
**Protocol:** 200k agents · world seeds (42, 20260901, 20260902) · warm 60d · sb1 seeds (4242, 5151, 6363), 180d
**Commit:** 13761ff (run) / assembled 6402aa1 · table artifact `/opt/earth1-data/benchmark_a_full1/AFULL_TABLE.json`
**Estate sha256:** wvs_heldout 659a6675… · pew_frame_dev 7750165 2… · goqa_dev = SAME sha as pew_frame_dev (alias — see notes)
**Tiers:** ACCEPT ≤7.0pp · GOOD ≤5.0 · WIN ≤3.5. Baselines per B0 (no LLM baselines).

## THE TABLE (15 cells: 5 scored, 10 NOT_RUN with reasons, 0 pending)

| task | estate | metric | Earth-1 | baselines | verdict |
|---|---|---|---|---|---|
| i | wvs_heldout | national MAE pp (leave-one-country-out) | **11.84** | MrsP 11.18 · naive 12.80 · region-copy 9.70 | **MISS** (beats naive only) |
| i | pew_frame_dev | national MAE pp | **12.01** | MrsP 11.06 · naive 12.02 · region-copy 10.31 | **MISS** (≈ naive) |
| i | goqa_dev | — | — | — | NOT_RUN: alias of pew_frame_dev (same 469 items, same sha) |
| ii | wvs_heldout | cohort-cell MAE pp (frozen 18,333-cell frame; 164,997 scored cells) | **10.49** | national-copy 10.08 · global-gradient 9.92 · cohort-MRP 10.06 | **MISS** (below every floor) |
| ii | pew_frame_dev | — | — | — | NOT_RUN: cohort cells are WVS-only (campaign order) |
| ii | goqa_dev | — | — | — | NOT_RUN: cohort cells are WVS-only |
| iii | wvs_heldout | joint energy distance (median over 63 countries) | **0.1896** | independent-marginal MRP 0.1858 | **LOSS** — joints are anti-signal |
| iii | pew_frame_dev | — | — | — | NOT_RUN: no respondent-level/crosstab joints exist for the Pew frame |
| iii | goqa_dev | — | — | — | NOT_RUN: same |
| iv | wvs_heldout | zeroshot cohort-cell MAE pp (transfer, 4,188 cells) | **21.32** | national-copy 21.09 · neighbour-offset 21.21 | **MISS** (transfer adds nothing) |
| iv | pew_frame_dev | — | — | — | NOT_RUN: task iv is registered within-WVS |
| iv | goqa_dev | — | — | — | NOT_RUN: same |
| v | wvs_heldout | cross-wave delta MAE | — | — | NOT_RUN: BLOCKED-ON-DATA (no verifiable W6 aggregates on disk; engine has no wave-6-conditioned state — delta undefined without leaking W7 truth) |
| v | pew_frame_dev | — | — | — | NOT_RUN: second Pew wave not on disk (pew2019_judge is HOLDOUT, untouchable) |
| v | goqa_dev | — | — | — | NOT_RUN: same |

## READING (no spin)

Earth-1's opinion readout currently loses to every informed baseline on every scored
task: ~2pp behind region-copy at national level on both estates (the standing ~5pp
gap to ACCEPT confirmed on the A frame), cohort deviations WORSE than predicting none
(consistent with the frozen-cell R-D finding), 2D joint structure slightly farther
from survey joints than shuffled marginals, and zeroshot item transfer nil. This is
the honest starting board for the B2 level campaign.

## B2 QUEUE (top-3 error cells, share-weighted, task i wvs_heldout)

1. family=other · Middle East/N. Africa · LMIC (weighted MAE 5210, n=372)
2. family=other · Latin America · UMIC (5087, n=502)
3. family=other · Western Europe · HIC (4546, n=376)

Worst-5 single cells: TJ 80.1pp, CZ 75.0, MM 73.3, DE 71.6, CN 69.6 (religion/values).
Pew worst-5: BR economy 95.7, UA democracy 88.7, JO democracy 86.5, CN 78.8, DE 73.3.

## PROVENANCE NOTES

- Joints registration: 8 confirm joint items (Q7–Q15) → 28 pairs; registration and
  per-pair results in `/opt/earth1-data/benchmark_a_full1/joints.json` (registered
  before scoring by construction of the harness).
- Task iv split as recorded in the artifact: deterministic stride split of the 98
  confirm items, neighbour ridge at seed 42 (items Q7, Q20, Q47, Q63, Q83, Q135,
  Q166, Q195 held out). Deviation from the planned default_rng(20260831) 70/30 split
  is recorded here, not hidden.
- Assembler discrepancy log (verbatim in artifact): EARTH1_COHORT_READOUT env has no
  consumer (reliability weighting is intrinsic to frozen_score.py); goqa_dev estate
  has no loader distinct from pew_frame_dev; score_sb1 filenames label pew_frame_dev
  as "goqa_dev".
- The c-SHOCK distress-layoff channel (in calibration tonight) is bitwise-zero in
  scenario-free worlds: this table can never need a SUPERSEDED rerun for it.
