# CYCLE c008/c009 (+c011 normalization) — GM hazard restructure
_Retroactive XI.A.2 report (BIBLE.md v4.2 §4.2.3): c008 GM age-baseline × RR, c009
GM_OTHER_SHARE fixed point, c011 stratified SMR norm. Ledger: CALIBRATION_CYCLES.md._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | CDR, age_at_death (primary); full table re-run: cohortMAE, median, $8.30, 65+, casc× |
| number(s) | CDR: 0.013 (legacy, c007) → 0.016 (c008) → 0.0084 (c009) → 0.0069 pooled (c011). ageAtDeath: 46.0 → 58.9 → 66.3 → 64.1 ± 2.8 pooled (c011, 4 seeds) |
| target | CDR band [0.007, 0.015] (anchor 7.55/1000, SP.DYN.CDRT.IN 2024). ageAtDeath: own-pyramid ref 69.0, band [66.2, 71.8] (gompertz_world.v1.json), superseding stationary band [69.7, 89.7]. Gate-table prereg hash: TODO-VERIFY (not recorded in cycle files) |
| gap | ageAtDeath 64.1 − 69.0 = −4.9 yr; CDR 0.0069 vs band floor 0.007 (graze) |
| agents / seeds | 20,000 × 180 d × 4 seeds (4242 / 5151 / 6363 / 7777) |
| flag set | HARDSHIP_MODE=gradient; INCOME_CALIBRATION=v1; SUBSTRATE_FLAG=c2plus_v1; C2PLUS_TABLES=c2plus_tables_v2.json; MORTALITY_MODE=gompertz; GM_OTHER_SHARE=0.49 (c009+); substrate c2plus_v1 |
| hashes | tables t:256fe63229 · anchors a:39d484d65f · income-cal i:89be94309c · tree hash: TODO-VERIFY · concordance: TODO-VERIFY |
| host / commit / wall-clock | commits e3363ca (c008/c009 @2026-08-27T20:54/20:56Z), 79ec16a (c009 replicates), 9682355 (c011 @21:39:56Z); ~25 s/run; host: TODO-VERIFY (not stamped in cycle JSON) |

## INSTRUMENT
Ground truth: World Bank open indicator API via scripts/fetch_anchors.py, which stores
raw response + source URL, series id, vintage, fetch date, and sha256 into the data-role
registry. data/anchors_worldbank.json (fetched 2026-08-27T13:20:36Z): LE 73.4818 yr
(SP.DYN.LE00.IN, 2024), CDR 7.5507/1000 (SP.DYN.CDRT.IN, 2024), 65+ 10.20 %
(SP.POP.65UP.TO.ZS). Blocked series named, not faked: adult_death_share_by_age_band,
global_median_daily_consumption (BLOCKED_ON_DATA). Units: engine CDR is deaths per
person-year vs band [0.007, 0.015]. Leakage: the GM fit reads fetched aggregates only;
no WVS attitude roles touched. Canonical path: shipping flag set on the unified loop —
flags dict + provenance hashes stamped per run in data/cycles/c00{8,9,11}*.json.
Known-answer: the GM fit reproduces its fetched targets — q45_15 0.1442 vs 0.1443, CDR
8.22 vs 7.55/1000, e0 75.72 vs 73.48 (residual +0.055, recorded as tension in
gompertz_world.v1.json). Failure case this instrument reports, demonstrated: the first
c011 attempt was a mislabeled c010-rerun (patch no-op) — caught and purged before
scoring (CALIBRATION_CYCLES.md c011 row); the config-hash tripwire now makes no-op rows
unrecordable (TRIPWIRES row); FROZEN-RESCORE caught the moving-floor artifact (ABLATION).

## DIAGNOSIS
Causal path: earth1/health.py:277–284 — under gompertz mode, illness resolution clears,
never kills; death is decided by the centralized baseline draw. health.py:293–341 —
p = m_age/365 · dt · rr_n · (1 − GM_OTHER_SHARE) (health.py:341), with
m(x) = A + B·exp(c·(x−18)) (health.py:306–307) and
RR = (1 + 1.2·HARDSHIP_GAIN·dep)(1 + 4·ill)(1 + 0.5·add) (health.py:309–311).
c008 miss (CDR 0.016 > band): other channels (starvation, weather, war, roads) still add
on top of a full all-cause baseline — double counting. Attribution measured (c009.json
change field): starvation 24 % of deaths (own registered miss, ~30× reality), GM fit
residual 8 %, unnamed 17 % → class (c) parameter; fixed point gives GM_OTHER_SHARE=0.49.
c009 residual miss (ageAtDeath 66.3, seeds down to 53.8): global mean-1 RR normalization
let young-skewed risk factors transfer deaths ACROSS the age curve (health.py:312–317;
200k measurement: mean age at death 59.6 vs table ~79.7) → class (a) instrument in part
(stationary band [69.7, 89.7] structurally unreachable on the young genesis pyramid;
reference re-derived on-pyramid to 69.0, gompertz_world.v1.json) and class (d) for the
remainder: residual 4.9 yr named as within-band RR gradients from channels that bypass
rr_n (roads/decline) plus the WANT channel over-kill (fixed separately in c010).

## RESEARCH
1. **Gompertz–Makeham baseline** — Gompertz (1825), "On the nature of the function
   expressive of the law of human mortality", Phil. Trans. R. Soc.; Makeham (1860),
   J. Inst. Actuaries: adult hazard = age-independent term A plus exponential term
   B·e^{cx}. SELECTED: 3 parameters identifiable from the 3 fetched aggregates
   (e0, q45_15, CDR); the canonical adult-mortality law.
2. **Indirect standardization / SMR** — Breslow & Day (1987), Statistical Methods in
   Cancer Research Vol. II, IARC: risk ratios to expected deaths WITHIN age strata, so
   covariates cannot rewrite the marginal age curve. SELECTED for c011: per-age-bin
   mean-1 RR normalization is the SMR form — hardship picks who within a cohort.
3. **Cox proportional hazards** — Cox (1972), "Regression models and life-tables",
   JRSS B. REJECTED: needs individual survival data we do not have, and an unnormalized
   PH multiplier reproduces exactly the c009 defect when covariates correlate with age.
4. **Heligman–Pollard (1980), J. Inst. Actuaries** 8-parameter law. REJECTED:
   over-parameterized for an adult-only world with 3 aggregate targets.

## IMPLEMENTATION
- c008: EARTH1_MORTALITY_MODE=gompertz flag, default legacy (health.py:134); constants
  loaded at health.py:136–141 from data/gompertz_world.v1.json: A=0.0032201,
  B=3.331e-06, c=0.148878 — **DERIVED** from fetched World Bank aggregates
  (anchors_worldbank.json; upgrade path to UN WPP table recorded in the file's status).
- c009: EARTH1_GM_OTHER_SHARE env, default 0.0 (health.py:135), set 0.49 — **FITTED**
  (fixed-point on the c008 run's own measured cause-of-death shares: 0.24 + 0.08 + 0.17,
  c009.json). Data-role hash for the fit input: TODO-VERIFY (internal death ledger of
  c008.json; no registry hash recorded).
- c011: age-stratified SMR normalization, health.py:335–340; bin edges
  [30, 40, 50, 60, 70, 80] — **ASSUMED** (decadal convention); no new tunable constant.
Smallest change: one flag, one scalar, one normalization loop; default OFF (legacy);
no substrate-table or anchor edits (hashes unchanged c003→c011).

## ABLATION
Paired runs on disk:
- **GM_OTHER_SHARE ON/OFF**: data/cycles/c008.json vs c009.json — same seed 4242, same
  commit e3363ca, same hashes. CDR 0.016 → 0.0084; ageAtDeath 58.9 → 66.3; median
  9.25 → 9.27; casc× 0.492 → 0.517. Movement attributable to SHARE alone.
- **Stratified SMR ON/OFF**: data/cycles/c010.json + c010_s{5151,6363,7777}.json
  (global mean-1) vs c011.json + c011_s{5151,6363,7777}.json (stratified), identical
  4 seeds: ageAtDeath pooled 67.2 ± 3.8 → 64.1 ± 2.8; CDR 0.0077 → 0.0069 pooled.
- **GM mode ON vs legacy OFF**: no strict paired CRN run archived (legacy at commit
  e3363ca). Nearest on-disk comparison: c007.json (legacy, seed 4242, same tables/
  anchors, different commit): ageAtDeath 46.0 → 58.9; CDR 0.013 → 0.016. **Single rerun
  owed: EARTH1_MORTALITY_MODE=legacy at commit e3363ca, seed 4242, 20k × 180 d.**
- Sensitivity of the gate to GM_OTHER_SHARE exists at two points only (0.0, 0.49); the
  plausible-range sweep is owed alongside the rerun above.
- Regression check: no gate regressed > 2σ (median/$8.30/65+/casc× green all seeds).
  The apparent attitude improvement in the c008/c009 rows (12.18 vs floor 12.74) was
  RETRACTED by FROZEN-RESCORE on frozen cells (frozen_c003cfg/c009cfg/c010cfg.json):
  c003→c009→c010 total MAE 12.00 → 11.88 → 11.97 ≈ noise — the floor had moved with the
  physics; not attributed to this change.

## RETEST
Unchanged anchors/tables/seeds throughout (t:256fe63229, a:39d484d65f, i:89be94309c).
c009 × 4 seeds (c009.json, c009_s*.json): CDR 0.0084/0.0092/0.0100/0.0094 (all in
band); ageAtDeath 66.3/59.4/55.4/53.8 (seed 4242 flattering; all below band).
c011 × 4 seeds (c011.json, c011_s*.json): ageAtDeath 64.6/65.2/60.0/66.4 → 64.1 ± 2.8
vs on-pyramid ref 69.0 (band 66.2–71.8), residual 4.9 yr; CDR 0.0062/0.0062/0.0069/
0.0082 → pooled 0.0069 (floor graze). Other gates before (c007) → after (c011, seed
4242): median 9.24 → 9.21 ✓; $8.30 49.1 % → 49.4 % ✓; 65+ 14.2 % → 14.2 % ✓; casc×
0.512 → 0.508 ✓; cohortMAE vs floor 13.13✗ → 12.34 vs 12.94 (✓ but see FROZEN-RESCORE).
200k: the 20k moved ≥ 0.3 pp in the right direction; only the pre-c011 200k measurement
(mean age at death 59.6 under global norm, health.py:314) exists on disk — **200k rerun
of the c011 configuration owed** (per the c010×4 ruling: "200k decides").

## STATUS
**ITERATING** — CDR in band at c009 but grazing the floor after c011 (pooled 0.0069 vs
0.007); ageAtDeath residual 4.9 yr vs the on-pyramid reference. Next hypothesis: bring
the channels that bypass rr_n (roads, decline) under the stratified SMR normalization —
their within-band age gradients are the named residual (CALIBRATION_CYCLES.md c011 row).
