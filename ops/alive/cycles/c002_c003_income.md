# CYCLE c002+c003 — income calibration v1 under the C2+ frame
_Retroactive XI.A.2 report (BIBLE.md v4.2 §4.2.3). One named change in two
steps: c002 derivation (WAGE_LEVEL 2.6617, WAGE_LOG_SD 1.2196), c003
fixed-point rescale (WAGE_LEVEL 2.6617 → 2.3038, WAGE_LOG_SD unchanged)._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | median, $8.30 headcount, CDR, cohortMAE-vs-floor, ageAtDeath, 65+ share, cascade ratio |
| number(s) | median $10.71 (c002) → $9.24 (c003), seed σ $0.061; $8.30 hc 44.2% → 49.1%, σ 0.7pp |
| target | median $9.27 (fetched PIP, interpolated from $8.30 hc 0.4607 / $9.50 hc 0.5094); $8.30 real 46.1% — UNTARGETED; gate-table prereg hash TODO-VERIFY |
| gap | median −0.03 (≈0.5σ); $8.30 +3.0pp (untargeted consequence, recorded pass per gate band) |
| agents / seeds | 20000 × 180d; seed 4242 per cycle; c003 replicated ×4 (4242/5151/6363/7777) |
| flag set | EARTH1_HARDSHIP_MODE=gradient; EARTH1_INCOME_CALIBRATION=v1; EARTH1_SUBSTRATE_FLAG=c2plus_v1; EARTH1_C2PLUS_TABLES="" (c002) / c2plus_tables_v2.json (c003) |
| hashes | tables 256fe63229 · anchors 39d484d65f · income-cal 1db1b15de3 (c002) / 89be94309c (c003) · concordance TODO-VERIFY |
| host / commit / wall-clock | host TODO-VERIFY · commit 7ab258b · 2026-08-27T14:22:38Z (27.2s) / 14:23:42Z (26.5s) |

## INSTRUMENT
Ground truth: data/anchors_worldbank.json, fetched 2026-08-27T13:20:36Z from
api.worldbank.org (v2 + PIP); series SI.POV.UMIC ($8.30 hc 46.1, 2024), PIP
pip-grp WLD mean 21.6153, median 9.27 interpolated from fetched headcounts at
$8.30 (0.4607) and $9.50 (0.5094); short hash a:39d484d65f (full sha256
TODO-VERIFY). Units: 2021-PPP daily household per-capita consumption on both
sides — the model side is measured through the household-pooled operator, per
the incumbent file's recalibration_note (the operator repair that moved the
measured median 9.91 → 10.96 is exactly the failure this check reports: fit
against the unpooled individual median and the gate misses; c002 shows the
instrument reporting the analogous overshoot, $10.71✗). Leakage: only the
fetched median and the mean/median-implied total log-sd 1.3012 are targets;
all headcounts are read for scoring only. Canonical path: constants load in
earth1/life.py:168-184 into the shipping wage draw (life.py:322-323) on the
unified loop — not a script-level assembly. Known-answer guards: missing
calibration file raises RuntimeError (life.py:173-177); substrate-tag
mismatch raises RuntimeError (life.py:179-182), so the incumbent fit
(WAGE_LEVEL 2.1306) can never silently load under c2plus_v1.

## DIAGNOSIS
Causal path: data/income_calibration.c2plus_v1.json → life.py:183-184 →
wage = OCC_WAGE[occ] · exp(N(0, WAGE_LOG_SD)) / cost_share · WAGE_LEVEL
(life.py:322-323) → household pooling → PIP-style median/headcounts.
C2+ frame with calibration off measures median $3.48, mean $4.10, implied
total log-sd 0.573 (income_calibration.c2plus_v1.json). c002 set
WAGE_LEVEL = 9.27/3.483 = 2.6617 and raised WAGE_LOG_SD to 1.2196 so total
log-sd matches the fetched 1.3012 holding non-wage variance fixed; the
dispersion raise lifts the POOLED median nonlinearly (same effect as in the
incumbent derivation), landing $10.71 — a +1.44 miss wholly attributable to
that nonlinearity: class (c) parameter, known because a pure rescale removes
it. c003 rescaled level by 9.27/10.71 → 2.3038, landing $9.24 (gap −0.03 ≈
0.5σ). Residual +3.0pp on the untargeted $8.30 headcount is single-lognormal
tail-shape mismatch. The cycle-level reds (cohortMAE 10.94 vs floor 9.875;
ageAtDeath 46.0 vs band 63.5–83.5) are untouched by this lever — later
diagnostic cycles c004/c005 classified them (d) structurally missing
channels (age physics), per CALIBRATION_CYCLES.md.

## RESEARCH
(1) Two-parameter lognormal income fitting — Gibrat (1931), law of
proportionate effect; Aitchison & Brown (1957); log-normality of
consumption specifically supported by Battistin, Blundell & Lewbel (2009).
Selected: the engine's within-occupation draw is already lognormal
(life.py:322), and exactly two moments are fetched (median; mean/median
skew ⇒ implied log-sd 1.3012), so a two-constant fit is exactly identified.
(2) Pareto upper tail on a lognormal body — Pareto (1897); parametric
alternatives Singh & Maddala (1976). Rejected: no fetched top-tail anchor
exists to identify a third parameter, and the scored $8.30 gate sits in the
body, not the tail; the +3.0pp headcount residual is retained as the named
cost of this rejection. (3) Household equivalence/pooling for the
H_poverty operator — per-capita household pooling per Deaton (1997),
matching World Bank/PIP practice; OECD-modified equivalence scales
(Buhmann, Rainwater, Schmaus & Smeeding 1988) rejected because the fetched
PIP targets are defined per-capita — an equivalized operator would score
the model against a target with a different definition.

## IMPLEMENTATION
Two constants in a substrate-keyed data file
(data/income_calibration.c2plus_v1.json): WAGE_LEVEL 2.3038, WAGE_LOG_SD
1.2196. Loaded at life.py:168-184 behind EARTH1_INCOME_CALIBRATION=v1,
default OFF (defaults 1.0 / 0.35, life.py:186). Provenance: both DERIVED —
WAGE_LEVEL by fixed-point against the fetched median (9.27/3.483, then
× 9.27/10.71 on the measured pooled median, seed 4242); WAGE_LOG_SD by the
variance identity matching fetched total log-sd 1.3012. No constant fitted
on scored data; headcounts never entered the derivation. Substrate tag
c2plus_v1, enforced at load (life.py:179-182). Smallest change: two numbers
in one data file, zero code-path changes, fully reversible by flag.

## ABLATION
Paired runs on disk: data/cycles/c002.json vs data/cycles/c003.json —
identical seed 4242, identical substrate/flags except the level rescale
(income-cal sha 1db1b15de3 → 89be94309c; tables off → v2). Attribution of
the level change alone: median 10.71 → 9.24 (−$1.47 ≈ 24σ at σ$0.061);
$8.30 hc 44.2% → 49.1%. Two-point sensitivity: Δmedian/ΔWAGE_LEVEL ≈
1.47/0.358 ≈ $4.1 per unit level. Regression check on the same pair:
cohortMAE 11.108 → 10.94 (improved), CDR 0.0147 → 0.0128 (in band),
ageAtDeath 49.6 → 46.0 (−3.6yr ≈ 1.1σ at σ3.237 — within 2σ, not VOID),
65+ 14.17% → 14.17%, cascade 0.492 → 0.512 (σ0.02 row-level; both pass).
MISSING PAIR: no scored CALIBRATION=off run on substrate c2plus_v1 exists
in data/cycles/ (only the unscored derivation measurement, median $3.48).
Owed: one rerun — EARTH1_INCOME_CALIBRATION=off, EARTH1_SUBSTRATE_FLAG=
c2plus_v1, seed 4242, 20000×180d through the cycle runner, paired against
data/cycles/c003.json.

## RETEST
Same frozen anchors (a:39d484d65f), same seed 4242, unchanged gates —
before (c002) → after (c003): median $10.71✗ → $9.24✓; $8.30 44.2%✓ →
49.1%✓; CDR 0.0147✓ → 0.0128✓; cohortMAE 11.108✗ → 10.94✗ (floors 9.85 /
9.875); ageAtDeath 49.6✗ → 46.0✗; 65+ 14.2%✓ → 14.2%✓; cascade 0.492✓ →
0.512✓. Seed replication (c003 config ×4, data/cycles/noise_floor.json +
c003_s5151/s6363/s7777.json): median 9.315±0.061, $8.30 48.1%±0.7pp, CDR
0.012±0.002, ageAtDeath 50.075±3.237, cohortMAE 10.761±0.155 vs floor
9.705±0.246, cascade 0.523±0.02. 200k owed (20k median moved ≥0.3pp in the
right direction) and run at the 200k rung (CALIBRATION_CYCLES.md): median
$8.97✓ (−2.9%), $8.30 48.3%✓, CDR 0.013✓ — no sign flips at scale.

## STATUS
**ITERATING.** The income gates land green (median 9.24 vs 9.27, ≈0.5σ;
untargeted $8.30 at 49.1% vs real 46.1% recorded pass; CDR, 65+, cascade
green) but both cycle rows are MISS on cohortMAE-vs-floor and ageAtDeath,
so PASS is refused. Next hypothesis (one line): decompose the cohort miss
by axis to name the worst under-modulated channel — executed as c004
(named: age). Constants retained; one OFF-pair rerun owed per ABLATION.
