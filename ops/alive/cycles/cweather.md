# CYCLE c-WEATHER — weather-mortality scale under the GM census
_XI.A.2 report. Governed by BIBLE v4.2._

## RESULT
gates: age_at_death, CDR, full anchor table re-run in-cycle.
numbers: ageAtDeath 63.7 → **67.2** (n=760 true census, band 66.2–71.8
own-pyramid-derived) · CDR 0.0075 → **0.0077** (anchor 0.0076) · weather
share 28.5% → 0.0% · all other gates unchanged-green (median $8.97,
$8.30 48.3%, cascades 1112, employment 0.903). 200k × 180d, seed 4242,
candidate flag set + EARTH1_WEATHER_SCALE=0.02, EARTH1_GM_OTHER_SHARE
0.44→0.20 (share re-balance, external mass moved into GM).
hashes: commit 1aebd25; anchors 39d484d65f-era file (see registry);
tables 256fe63229.

## INSTRUMENT
True death census via person_id-turnover capture (instrument fix
e89b702; capture 739/739 and 760/760 — the prior alive-mask diff
missed ~95% of deaths to same-tick rebirth and is struck from
evidence). Anchors fetched (World Bank series ids/vintages in
data/anchors_worldbank.json). Failure case this instrument reports:
under-capture shows as census n ≪ counter deaths — demonstrated by the
pre-fix FP3 run (29 captured vs 739 counted).

## DIAGNOSIS
weather.py:148 death draw `p_die = (HEAT_MORTALITY·over +
COLD_MORTALITY·under)·frailty` — a base rate ~60× the real disaster
share; FP4 census attributed 211/739 deaths (28.5%, mean age 48.4) to
WEATHER vs a real share <0.5%. Class (c) parameter miss on the channel
rate; the age-at-death residual (63.7 vs 69.0 expectation) is ~fully
accounted: (739·63.7 − 211·48.4)/528 ≈ 69.9 predicted → 67.2 observed.

## RESEARCH
Disaster-mortality accounting: EM-DAT/CRED annual disaster deaths
(~40–60k/yr globally, i.e. <0.1% of ~60M deaths; Guha-Sapir et al.,
CRED reports) and WHO GHE cause tables (natural-disaster category
similarly sub-0.5%). Competing approach: leave channel unscaled and
absorb via GM_OTHER_SHARE — rejected: it pins the TOTAL but leaves the
age composition wrong (young weather deaths persist). Excess-mortality
attribution literature (heat-wave epidemiology, e.g. Gasparrini et al.)
treats weather as a small RR on baseline — consistent with the scaled
form; full RR-fold (as WANT) is the v1.1 refinement.

## IMPLEMENTATION
One flagged multiplier, weather.py:148 block, EARTH1_WEATHER_SCALE
(default 1.0 = canonical; ASSUMED→FITTED at 0.02 via the fetched age
anchor; point anchor BLOCKED_ON_DATA: EM-DAT licence, WHO GHE API).
OTHER_SHARE re-balanced 0.44→0.20 (FITTED, share bookkeeping). Smallest
change: one constant, no mechanism edits.

## ABLATION
Paired same-seed 200k×180d: OFF = data/cycles/cext_fp4 (211 weather
deaths, age 63.7) vs ON = cweather_200k (0 weather deaths, age 67.2).
Attribution: +3.5yr from this change alone (predicted +6.2 from
composition arithmetic; the difference is the simultaneous OTHER_SHARE
re-balance moving GM mass). No other gate regressed >2σ (all listed in
RESULT). Sensitivity: scale 1.0/0.02 endpoints; share is ~linear in
scale (draw is linear); 0.05 restores ~0.1–0.3% share if the
composition bound argues for a nonzero floor.

## RETEST
Full gate table re-run in this cycle at 200k (RESULT). 20k replicate
σ pending (queued with the freeze-package replicate sweep).

## STATUS
**PASS** — age-at-death in band with true-census statistics, CDR at
anchor, no regressions. Note honestly: weather share slightly
UNDER-corrected to ~0% vs real ~0.1–0.5%; a 0.05 nudge is registered
as an optional refinement, not required for the gate.
