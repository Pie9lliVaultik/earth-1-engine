# THREE-TRACK STOP REPORT (founder ruling 2026-08-26 "GO")
All three tracks landed. Format per ruling.

## SBI GATE
- planted parameters: relax, critical_fraction, conviction_gain_dyadic,
  memory_press, hardship_mortality_gain, informal_floor_scale (A1 priors)
- summaries: S20=16 / S200=28, frozen post-screen, pre-θ*
- fidelity used: 20k (3,000 sims) + 200k (600 sims); classification
  evidence-based per A5; cascade cliff measured (sign flip)
- recovery: relax 5/5 (sd_u 0.017), memory_press 5/5 (0.026),
  critical_fraction 5/5 @200k (0.19), conviction 4/5 (≈prior width),
  hardship 4/5@20k-prior-width / 3/5@200k, informal NOT recovered
- SBC: uniform for all banked cells; coverage in-band; ZERO
  false-confidence violations
- confounding: hardship×informal posterior corr ≈ 0 (no ridge at 90 d)
- **REAL_DATA_THETA_INFERENCE_ELIGIBLE: YES** — scope-limited to
  relax / memory_press / critical_fraction (+conviction, wide);
  gains BLOCKED pending registered battery upgrade (more 200k sims,
  180-d windows, deprivation/death-structure summaries)

## C2+
- methods: M0 independence, M1 incumbent genesis, M2 IPF equal-country
  seed, M3 GREG respondent-pooled, M4 chained conditionals
- supplied margins: five 1-way (sex, age, edu, income, urban),
  verified per-constraint ≤1e-6 (multi-margin raking; scalar-K not
  misapplied)
- withheld joint tests: all 10 two-way + 10 three-way, 65 countries,
  leave-country-out, 200 bootstraps; instrument KA (shuffled method
  loses to M0) 65/65
- current genesis result: WORSE THAN INDEPENDENCE (median 7.47pp vs
  0.99pp 2-way); deficit ≈ all margin error; joints add nothing
  (raked-to-true-margins still loses to M0 in 45/63); sex
  CANNOT_EXPRESS
- best candidate: M2 (IPF, equal-country pooled donor seed)
- improvement: +24.8% median withheld-joint MAE reduction (2-way AND
  3-way), beats M0 p≤2.4e-13, beats M1 63/63 p=1.1e-19
- **C2_INJECTION_ELIGIBLE: YES** (= class-2 substrate battery entry
  only; no injection, no epoch)

## DATA / LICENCE
- role registry: LIVE and fail-closed (earth1/dataroles.py, sealed
  hashes, 8 KAs incl. tamper detection); operational before the first
  scored A/B result, per ruling
- physical isolation: sealed θ* bundle chmod 400 on prime, HOLDOUT
  role refuses all purposes except final_scoring; hash committed to
  repo before any result was read
- GSS consumed set: 79 variables, GSS 2022–2024 pooled (WTSSNRPS),
  R1-COHORT political×age cells — enumerated + sealed in registry
- WVS: standard terms NON-PROFIT ONLY → negotiated WVSA permission
  required for commercial calibration (founder email; counsel review
  of deployed WVS-fitted H flagged)
- EVS: PROHIBITED (GESIS: commercial + AI-processing bans)
- ESS: PERMISSION_REQUIRED — defined path (ESS ERIC Art. 23,
  ess@city.ac.uk)
- GSS: commercially usable now (citation + responsible use;
  confirmation email to NORC recommended)
- ANES: commercially usable now (research/statistical purposes; no
  respondent re-identification)
- IPUMS-International: PROHIBITED (do not register) — household/
  fine-geography joints stay BLOCKED_ON_DATA
- datasets legally usable for latent-z TODAY: **GSS + ANES (US-only)**;
  cross-country legality awaits WVS/ESS permissions

## WHAT EACH TRACK ELIMINATED
- SBI: the fear that Earth-1's physics is not inferable from its
  observable consequences. It is — with calibrated uncertainty and no
  false confidence — for fast-geometry parameters today; the two
  response-gain parameters need a bigger battery, not a new idea.
- C2+: the possibility that the initial-population problem is subtle.
  It is gross (margins + absent joints + missing sex axis), and a
  boring, proven method already rebuilds a quarter of withheld joint
  structure from margins alone.
- DATA: ambiguity about what fuel is legal and what is sealed. The
  boundary is now mechanical (registry) and legal (audit).

## NEXT DECISION (recommendation, awaiting ruling)
**Single highest-information next experiment: the C2+ class-2
substrate battery** — build the M2 substrate (IPF donor pool + census
margins + a sex axis), then Stage-A health regression, byte-identical
dynamics KA, and A-v2 DEVELOPMENT-fold scoring on the new substrate.
It is the first red→green attempt on a registered target (A-v2
structure metrics), attacks the worst proven bottleneck, uses only
TRAIN/DEV evidence, and costs ~a day on prime.
In parallel (cheap, mechanical): the SBI battery upgrade for the two
gain parameters (200k 600→2000 sims, 180-d windows, deprivation/death
summaries) — the validated gain-estimator is the prerequisite for
legitimately fitting the ×4 mortality overshoot, per the mortality
decomposition ruling (Deaths = baseline + hardship + epidemic, each
term earning its magnitude separately).
Also landed this session (founder-ordered, out-of-band): recorder v2
on production — cascade history now persists (45 rows, days 3000–3001);
Epoch 3 continuity verified (same UUID, rng_continued, commit-matched).
