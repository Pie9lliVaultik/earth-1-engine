# EXPERIENCE LOOP v1 — ROLLING-ORIGIN READINESS (design only; consumes nothing)
2026-08-27. Per founder ruling: prepare, do not consume. No outcome
data fetched; no clean estate touched. This is the design that turns
the synthetic loop into resolved-reality learning the moment v0.x
passes its gates.

## Domain choice — where Earth-1 can learn fastest
Criteria (ruling): frequent resolution, objective outcomes, strong
history, mechanism relevance, clear observation operator H.
**Selected: monthly national labour-market series (unemployment /
employment rates), OECD+Eurostat harmonized, ~40 countries.**
Why it wins on every criterion:
- Frequency: monthly resolutions ⇒ ~480 experiences/decade/country
  pool — two orders more resolution events than annual survey waves.
- Objectivity: statistical-office series; revisions are versioned
  (learn on first-release vintages; score against them, never against
  later revisions — vintage discipline registered here).
- History: 2000–2024 development span available under TRAIN/DEV; the
  post-cutoff stream stays PROSPECTIVE and untouched.
- Mechanism relevance: employment is Earth-1's strongest-coupled
  observable family (life layer, firms, welfare) and the one channel
  the gain battery shows responding to hardship/informal θ.
- H clarity: earth1/assimilate.py already implements
  measure(kind="unemployment") + per-country likelihood — L6 exists
  for exactly this family.
Rejected alternatives (recorded): weekly financial series (frequent
but weakly mechanism-coupled; H undefined); conflict-event counts
(ACLED licence + ontology gap); annual values surveys (resolution far
too slow to draw a learning curve).

## Design
Rolling origin, strict causality: D≤t → M_t → forecast t+1 (1- and
3-month horizons, full predictive distributions per country) → reveal
first-release y_{t+1} → score (CRPS + log score) → update ONLY the
eligible set → M_{t+1}. Origins: monthly, 2010-01 … 2019-12
(120 experiences) as the DEV window; 2020+ reserved (shock era joins
only after the calm-era curve is understood — registered to prevent
"COVID taught the model" artifacts in the first pass).
Arms (paired): frozen Earth; experiential Earth; naive (seasonal
random-walk + drift — the standard M-competition baseline); strongest
practical statistical baseline (auto-ETS/ARIMA per series);
shuffled-resolution placebo.
Eligible updates at v1 start: exactly the v0.x-validated θ set with
their validated estimators, PLUS state assimilation of the aggregate
employment state via the EnKF-on-aggregates layer (v0.2 gate must
pass first — state is where compounding lives). H and u_t error terms
enter as diagnosed components (ruling: never force every error into θ).
Receipts: the earth1/experience.py ledger as-is (proven replayable).

## Roles and estates (registry entries to be created at execution)
- oecd_labour_vintages_2000_2019: TRAIN/DEV (first-release vintages).
- 2020+ stream: PROSPECTIVE — physically excluded until ruled.
- No WVS/EVS/ESS dependency anywhere in v1 ⇒ no licence blocker; the
  series are official-statistics open data (terms to be recorded on
  fetch; OECD/Eurostat reuse terms are permissive with attribution).
- Untouched confirmation estates (B-v2 events, future waves, 5-q
  holdout remainder): NOT involved, preserved.

## Success criterion (same shape as v0.x, real data)
d(Skill)/d(Experience) > 0 for the experiential Earth on future
origins, with the frozen Earth flat and the placebo flat, and the
experiential curve at or above the strongest statistical baseline on
late origins. Calibration maintained. Every update replayable.
