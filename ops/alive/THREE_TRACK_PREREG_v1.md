# THREE-TRACK PREREG v1 — SBI Synthetic Twin ∥ C2+ Bake-off ∥ Data Governance
Registered: 2026-08-26, BEFORE any track has produced a scored result.
Founder ruling: GO with four refinements adopted (mechanical θ* blinding;
sensitivity pre-screen on INDEPENDENT design perturbations, never around
the sealed θ*; evidence-based fidelity classification; C2+ scope
correction). Physics untouched: canonical Epoch 3 (v4.1) is never
modified by any track. No real-data θ inference, no canonical C2
injection, no latent-z production training, no MF-SBI, no live
assimilation, no new epoch, no /ask unlock.

Interpretation rules (founder): C2+ WVS-7 evidence is DEVELOPMENT/
VALIDATION only — success does not become new E-class evidence.
C2_INJECTION_ELIGIBLE=YES means only "may enter the class-2 substrate
battery." Track-C role enforcement must be operational before the first
scored A/B result is written.

────────────────────────────────────────────────────────────────────
## TRACK A — SBI SYNTHETIC-TWIN RECOVERY GATE

### A1. Planted parameter set θ (6, all from the §6 calibratable inventory)
| # | name | canonical | locus | prior |
|---|------|-----------|-------|-------|
| 1 | relax | 0.045 | live_one_day kwarg (alive.py CANONICAL_DAY) | U(0.015, 0.135) |
| 2 | critical_fraction | 0.12 | live_one_day kwarg | U(0.06, 0.24) |
| 3 | conviction_gain_dyadic | 0.003 | influence.py CONVICTION_GAIN_DYADIC | logU(0.001, 0.009) |
| 4 | memory_press | 0.02 | memory.py press coefficient (line "…* 0.02") | logU(0.005, 0.08) |
| 5 | hardship_mortality_gain | 1.0 | scale s multiplying ALL deprivation coefficients in health.py hazards (0.5 cancer, 0.6 cvd, 1.2 infection, 0.7 injury, 0.7 fall-dep) | logU(0.33, 3.0) |
| 6 | informal_floor_scale | 1.0 | scale on life.py INFORMAL {HIC .18, UMIC .35, LMIC .55, LIC .70}, clipped ≤ 0.95 | U(0.5, 1.3) |

Injection: experiment harness only (scripts/sbi/), via kwargs (1–2) and
process-local module-constant override (3–6). Canonical files unmodified.

### A2. Injection KAs (must pass before anything else; Standing Rule 2)
- KA-0 identity: θ = canonical ⇒ trajectory identical to un-patched engine, same seed (hash match on daily observables).
- KA-1 determinism: same (θ, seed) twice ⇒ identical output.
- KA-2 leverage: for each θ_i at its prior 90th pct (others canonical), at least one raw daily observable differs from canonical. A harness in which some θ_i changes nothing is BROKEN and the test fails.

### A3. Candidate summary vector (frozen; from observables.collect over 90d)
Levels at day 90 and mean over days 61–90, plus slope 31–90 where
marked (s): employment_rate(s), destitute_share(s), deprivation.mean,
wealth_mean(s), cum_deaths, cum_disease_deaths, mental_mean,
addiction_mean, evicted_share, arrears_mean, policy_net_mean,
firm_health_mean, cum_firms_failed, knowledge_stock_mean,
memories_remembered, cum_cascades, force_mean[8], force_sd[8],
pole_share[8]. (~46 raw candidates.)

### A4. Sensitivity pre-screen — INDEPENDENT design worlds (never θ*)
θ* does not exist yet at screen time; it is drawn only after A5 freeze.
Design: one-at-a-time, each θ_i ∈ {prior p10, canonical, prior p90},
others canonical ⇒ 13 configs × 3 CRN seeds (101, 103, 107), at BOTH
20k×90d and 200k×90d. Plus canonical noise pool: 10 extra seeds per
fidelity. Sensitivity rule: summary j is SENSITIVE to θ_i at fidelity F
iff |median paired Δ_j(p90 vs canonical)| > 2·sd_CRN,j(F) or same for
p10. Verdict per θ_i: OBSERVATION_UNINFORMATIVE at F iff NO summary is
sensitive to it at F.

### A5. Fidelity classification (evidence-based; frozen rule)
TRANSFER_SAFE_AT_20K for summary j iff, for every θ_i to which j is
sensitive at 200k: sign(Δ_20k) = sign(Δ_200k) AND the standardized
effect ratio ∈ [1/3, 3]. Any summary sensitive at 200k but not 20k, or
sign-flipped, or ratio outside band ⇒ REQUIRES_200K. cum_cascades and
any cascade-gated summary defaults to REQUIRES_200K unless the paired
test proves otherwise. The accepted summary set S20 (transfer-safe) and
S200 (all sensitive summaries) are frozen after the screen, before θ*.

### A6. Mechanical blinding
After A5 freeze: scripts/sbi/plant.py draws M=5 truth vectors θ*_1..5
from the prior under one fresh OS-entropy seed, writes
sealed/theta_star_v1.json (values + the seed), prints only the SHA-256.
The hash is committed to this repo (sealed/theta_star_v1.sha256) BEFORE
any inference code runs. The file is registered role=HOLDOUT in the
data-role registry: open_data() refuses it for any purpose except
purpose="final_scoring". Inference/estimator code imports only the
registry API. Unsealing happens once, in the scoring script, which
verifies the hash first. y_obs: each θ*_m simulated at 3 observation
seeds (601,607,613) per required fidelity — seeds disjoint from
training seeds.

### A7. Inference battery
Training sims: N=3000 prior draws at 20k×90d (summaries S20);
N=600 prior draws at 200k×90d (summaries S200). Training seeds
2000+i / 5000+i. Methods (all three run; no post-hoc method dropping):
- ABC reference: rejection, top 1% by Euclidean distance on
  z-scored summaries (μ,σ from training set).
- NPE: masked-autoregressive/MDN posterior q(θ|s) (torch, CPU).
- NRE: binary classifier ratio estimator, posterior via prior × ratio
  on a θ grid/MCMC.
Primary analysis = 20k battery on S20; the 200k battery is scored
identically and reported alongside (it is the authority for any θ_i
whose only sensitive summaries are REQUIRES_200K).

### A8. Validation gates (per method, per battery)
- SBC: 200 held-out prior draws; rank uniformity per θ_i, KS p > 0.01.
- Coverage: central 90% credible interval covers truth in 85–95% of the
  200 held-out draws (per θ_i).
- Posterior predictive: for each sealed exam, sims at 20 posterior
  draws; observed summary distance within the 95th pct of the
  posterior-predictive distance distribution.
- False-confidence gate: for any θ_i ruled OBSERVATION_UNINFORMATIVE at
  the battery's fidelity, posterior sd must be ≥ 80% of prior sd. A
  contraction beyond that on an uninformative parameter is a
  FALSE_CONFIDENCE failure of the method regardless of other gates.
- Confounded-control expectation (registered now): hardship_mortality_
  gain and informal_floor_scale are expected PARTIALLY CONFOUNDED in
  death summaries and separated by destitute_share/deprivation; the
  joint posterior correlation must be REPORTED, and a method claiming
  independent tight recovery of both while the screen shows shared
  summaries only is treated with suspicion in the report.

### A9. Verdict tree (per θ_i; sealed exams = 5 truths × best method)
- Screen flat at both fidelities ⇒ OBSERVATION_DESIGN_FAILURE
  (OBSERVATION_UNINFORMATIVE recorded; not an estimator fault).
- Screen sensitive, but truth outside 90% CI in ≥2/5 sealed exams, or
  SBC/coverage fail ⇒ ESTIMATOR_FAILURE.
- Truth within 90% CI in ≥4/5 exams AND SBC pass AND coverage pass ⇒
  RECOVERED.
- Recovered only as a documented combination (ridge) ⇒
  PARTIALLY_IDENTIFIABLE (report the ridge direction).
REAL_DATA_THETA_INFERENCE_ELIGIBLE = YES iff ≥4 of 6 θ are RECOVERED or
PARTIALLY_IDENTIFIABLE with calibrated uncertainty AND no
FALSE_CONFIDENCE failure in the reported method. Otherwise BLOCKED,
with the failure class named.

────────────────────────────────────────────────────────────────────
## TRACK B — C2+ POPULATION-SYNTHESIS BAKE-OFF

### B1. Data and roles
Source: WVS-7 microdata (wvs7.duckdb on prime; 97,220 rows), weights
W_WEIGHT×S018. Roles: train-country microdata = TRAIN; held-out-country
joints = VALIDATION. WVS-7 remains CONSUMED for confirmation purposes:
nothing here is E-class evidence.
HOUSEHOLD_JOINTS = BLOCKED_ON_DATA. FINE_GEOGRAPHY_JOINTS =
BLOCKED_ON_DATA (IPUMS-International added to Track-C audit). No proxy
substitution to fill the scoreboard.

### B2. Variables (frozen; recodes registered before any scoring)
sex = Q260 (2) · age = X003R (6 bands) · education = Q275R (3:
lower/middle/higher) · income = Q288R (3: low/mid/high) · urban =
H_URBRURAL (2). Rows with missing/negative codes on any of the 5
dropped (count reported). Countries with ≥800 retained rows enter the
fold set.

### B3. Design — leave-country-out
For each held-out country: methods receive ONLY its five 1-way weighted
margins (role INPUT) plus TRAIN-country microdata. Withheld targets:
all 10 two-way and all 10 three-way weighted joint tables of the held-
out country. No method sees held-out joints. Margin verification: every
supplied margin reproduced to |err| ≤ 1e-6 per cell by every method
that claims it (verified individually per constraint, per the
multi-margin correction — scalar-K is NOT applied outside its
single-margin domain).

### B4. Methods (frozen)
- M0 independence null: product of supplied margins. Every method must
  beat this to claim any joint structure.
- M1 incumbent genesis: current earth1 genesis population for the
  country, mapped to the 5 variables where genesis expresses them; axes
  genesis cannot express are recorded as CANNOT_EXPRESS and scored as
  independence on that axis (that itself is a finding, not a repair).
- M2 IPF/raking: seed table = pooled weighted 5-way joint of TRAIN
  countries; raked to the 5 target margins to convergence.
- M3 GREG/calibration weighting: TRAIN-country pooled respondents
  reweighted (raking calibration) to the 5 target margins.
- M4 conditional synthesis: sequential categorical conditionals fitted
  on TRAIN countries, frozen order sex → age|sex → edu|age,sex →
  income|edu,age(,sex) → urban|income,edu,age; then per-variable
  post-raking to target margins (re-verified).

### B5. Scoring (frozen)
Truth: held-out country weighted joint tables. Metrics per country:
mean absolute error (percentage points) over all two-way cells;
same over all three-way cells; improvement_m = (MAE_M0 − MAE_m)/MAE_M0.
Uncertainty: 200 respondent bootstraps per held-out country. Aggregate:
median and IQR of improvement across countries; paired sign test
(method vs M0, method vs M1).
Instrument KA (Standing Rule 2): a deliberately broken method
(cell-shuffled M2) must score WORSE than M0; if it does not, the scorer
is defective and results are VOID.

### B6. Gate
C2_INJECTION_ELIGIBLE = YES iff one method beats BOTH M0 and M1 on
two-way AND three-way median improvement, paired sign test p < 0.01,
relative MAE reduction ≥ 10%. YES means only: enter the class-2
substrate battery (Stage-A health regression, byte-identical dynamics
KA, A-v2 development scoring on the new substrate) under
VALIDATION_INHERITANCE_POLICY. It does not mean injection.

────────────────────────────────────────────────────────────────────
## TRACK C — DATA GOVERNANCE + LICENSING

### C1. Role registry (before first scored A/B result)
earth1/dataroles.py + data/data_roles.json. Roles: TRAIN, VALIDATION,
HOLDOUT, PROSPECTIVE, INPUT_EXPOSURE, EVALUATION_OUTCOME. API:
open_data(name, purpose) — fail-closed: HOLDOUT/PROSPECTIVE refuse
every purpose except final_scoring; EVALUATION_OUTCOME refuses
training/model_selection; unregistered paths refuse everything.
Sealed bundles: sha256 recorded at registration; open_data verifies
hash on read, refuses on mismatch. Feature-lineage graph:
data/feature_lineage.json (feature → source dataset/items/roles);
the existing correlation/adjacency gate (data/feature_adjacency.json,
scripts/feature_adjacency_gate.py) is PRESERVED INDEPENDENTLY — lineage
adds, never replaces. KAs (tests/test_dataroles.py): illegal-purpose
read raises; unregistered read raises; tampered bundle raises; legal
read returns bytes; adjacency gate still runs standalone.

### C2. Consumed-estate ledger (corrections of record)
GSS: PARTIALLY_CONSUMED — R1-COHORT consumed 79 GSS variables, GSS
2022–2024 pooled (weight WTSSNRPS), as political×age cohort fit/score
cells (enumerated in data/data_roles.json entry gss_r1_consumed).
WVS-7: CONSUMED for confirmation (GOQA-40, 98-item set, v1 holdout);
usable as TRAIN/VALIDATION only. ANES, ESS: clean (subject to C3).

### C3. Licence audit (in flight, workflow wf_47f3ea9d-cb1)
WVS, EVS, ESS, GSS, ANES, IPUMS-International: commercial use, derived-
model (training) use, redistribution, registration, founder actions.
Rule: no source is classified commercially deployable unless its terms
support that conclusion; ambiguity resolves restrictive.

────────────────────────────────────────────────────────────────────
## ASSIMILATION POLICY AMENDMENT — DRAFTED, NOT ACTIVE
A registered observation-driven current-state correction is an
epoch-preserving assimilation transaction, not a physics change,
provided: explicit timestamp; all pre-cutoff snapshots/history
immutable; prior and posterior world hashes recorded in a correction
receipt; future lineage traceable from the analysis state
(World_forecast → assimilation(y_t), receipt → World_analysis).
Assimilation never silently rewrites personal history. ACTIVATION
requires a founder ruling; recorded here so EPOCH_POLICY.md is amended
in one move when Layer 7 exists.

## STOP POINT
All three tracks report: SBI per-parameter verdicts + eligibility; C2+
incumbent-vs-candidates on withheld structure with a winner or NONE;
registry/licence/consumed-ledger status. Then: which uncertainty each
track eliminated and the single highest-information next experiment.
Founder ruling before anything further.

────────────────────────────────────────────────────────────────────
## AMENDMENT A4.1 — observation probe event (2026-08-26, PRE-θ*)
Registered after the design-world screen and BEFORE θ* exists or any
estimator has run. The first screen pass (archived at
/opt/earth1-data/sbi/screen_VOID.json) fired the registered KA-2 VOID:
memory_press moved NOTHING at 200k — diagnosis: canonical cold-start
90-day worlds generate ZERO chronicle memories (memories_remembered=0
in every canonical run; both press arms bit-identical to canonical,
0/46 summaries differ), so θ₄ multiplies objects the twin never
creates. The unit KA proves PRESS is consumed when a memory exists;
this is OBSERVATION_DESIGN_FAILURE of the twin window, repaired here.
Repair: every twin simulation (screen, training, sealed exams, y_obs)
injects ONE registered probe memory after day 10: id="obs_probe",
salience 0.8, half_life 180 d, force_signature +0.06 on all 8 channels,
scope = all agents alive at day 10. θ-independent, identical across
configs and seeds; RNG consumption identical ⇒ CRN pairing preserved.
The screen reruns in full under the probe; A4/A5 rules unchanged.
critical_fraction leverage was already proven in the first pass
(cum_cascades 948 vs 1100 paired) — the probe does not alter that KA.
