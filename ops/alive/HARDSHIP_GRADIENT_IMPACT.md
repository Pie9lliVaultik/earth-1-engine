# HARDSHIP GRADIENT — CHANGE IMPACT (classified BEFORE deployment)
2026-08-27. Bible v4.1 loop: MISS → VERIFY → DIAGNOSE → RESEARCH →
IMPLEMENT → CALIBRATE → ABLATE → RETEST → PASS → FREEZE.

## REGISTERED MISS
Living-baseline poverty and mortality: destitution ~30% of population
(real extreme poverty ~9%); hardship mortality ×4 over the WHO anchor
(PHASE_2A, RESPONSE_GAIN + MISSING_CHANNEL); cascade over-firing.

## MEASURED CAUSE (new, 2026-08-27)
Deprivation was BINARY, not graded. Measured at 20k×90d,
population-weighted: destitute (dep>0.99) 30.5%, deprived (dep>0.5)
31.0% — i.e. only 0.5% of humanity lived anywhere between. Cause is the
formula itself: `covers = income >= cost` is a hard step (99% of cost
scores identically to zero income) and DESTITUTE_BUFFER=3 days empties
immediately, pinning every uncovered agent at ≈1.0. Every downstream
hardship consumer (mortality hazards ×(1+k·dep), cascade entry via
deprivation-driven forces) therefore read "universal catastrophe".

## ADMISSIBLE CALIBRATION CHANGE
Depth-of-shortfall with reserve cushion, replacing the binary gate:
  gap = clip((cost − income)/cost, 0, 1)
  cushion = clip(wealth / DESTITUTE_BUFFER, 0, 1)
  deprivation = where(covers, 0, gap · (1 − cushion))
Structural (a better functional form), not a fit-to-outcome tune: no
constant was tuned against any target. Same zero point, same maximum,
same inputs.

## MEASURED RESULT (20k×90d, population-weighted)
| config | dep>0.99 | dep>0.5 | mild 0.05–0.5 | deaths/yr |
|---|---|---|---|---|
| REAL ANCHOR | — | ~9% (extreme poverty) | (~44% under $6.85) | 0.76% |
| incumbent + cliff (canonical) | 30.5% | 31.0% | 0.5% | 2.07% |
| incumbent + GRADIENT | 0.0% | 7.9% | 24.0% | 0.99% |
| C2+v2 + GRADIENT | 0.0% | 10.7% | 24.5% | 0.99% |
Mortality: 2.7× → 1.3× the real rate with NO mortality parameter
touched — confirming the ×4 overshoot was substantially deprivation-
driven, not purely a hazard-gain defect.

## KNOWN OPEN ITEM (reported, not hidden)
The dep>0.99 bucket is now empty by construction (requires literally
zero income AND zero reserves). The `destitute_share` observable is
threshold-defined at >0.99 and must be re-anchored (>0.5 = severe
hardship) — an OBSERVATION-OPERATOR change to be registered separately;
until then destitute_share is not comparable across the two forms.

## CLASSIFICATION AND STATUS
Class **3 — foundational** (deprivation is consumed by mortality,
cascades, institutions, flourishing, migration). Requires broad
revalidation before any deployment. Therefore:
- default remains `cliff` (canonical v4.1); the gradient is opt-in via
  EARTH1_HARDSHIP_MODE=gradient. Epoch 3 is untouched.
- owed before promotion: full living-baseline battery, Benchmark B DEV
  event retest (magnitude gates were computed under the cliff form),
  A-v2 DEV (attitudes are downstream of deprivation), cascade-rate
  regression, and a paired ablation isolating gradient vs C2+v2.
- no HOLDOUT evidence touched.
