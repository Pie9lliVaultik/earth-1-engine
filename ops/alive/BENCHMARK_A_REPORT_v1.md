# BENCHMARK A (PHASE 1) — REPORT v1

Prereg: BENCHMARK_A_PREREG_v1.md, frozen at 0de71e5 (amendment 838ba1c,
recorded before any Earth-1 readout). Scoring, targets, folds, baselines:
frozen; baselines committed BEFORE Earth-1 ran; holdout evaluated ONCE.
Artifacts: data/benchmark_a/ (targets_v1, baselines_v1, earth1_v1,
scoreboard_v1). Worlds: three 200k Epoch-3-physics lab worlds
(seeds 42/20260901/20260902, 60 lived days; hashes in earth1_v1.json).
One harness VOID recorded (quantile clip; repaired and the stage rerun
before any scoring).

## HEADLINE (written first, per the frozen reporting rule)

**Earth-1 v1 adds no measurable value over the best statistical
baseline on any primary Benchmark-A gate.** The strong MRP baseline is
better at country means by 5.6 pp; simple baselines are better at
cohort cells; the held-out-question and joint-dependence increments are
inside their confidence intervals. Per Bible §11, MRP therefore becomes
the calibration layer and any Earth-1 claim must come from where agent
structure matters — and in v1 the structural tasks did not clear their
frozen gates either.

## Five-task scoreboard (Earth-1 vs every baseline, holdout, one shot)

| task | Earth-1 | best baseline | gate | verdict |
|---|---|---|---|---|
| (i) country means (40 items × ~60 countries, 3 CV seeds) | E1-national **15.21 pp**; E1-hybrid 15.18 pp | **MRP 9.57 pp** (naive 12.73) | ≤0.5 pp excess over MRP or hybrid gain CI>0 | **FAIL** — excess +5.64 pp; hybrid − MRP CI (-6.72, -4.45) pp entirely negative |
| (ii) cohort cells (66,924 cell-evaluations) | E1 16.17 pp, grad 43.8 %; E1-hybrid 16.06 pp, 46.8 % | **global-gradient 9.89 pp**, 70.8 % (national-copy 10.08 pp) | ≥10 % rel. reduction AND ≥75 % gradient | **FAIL** — relative reduction −62 %; gradient below 75 % everywhere |
| (iii) joint distributions (8 items, 63 countries) | raw energy median 0.390; **marginal-matched 1.4e-05** | independent-marginal 1.5e-03 | E1 < independent, paired CI excluding 0 | **FAIL** primary (raw marginals are off, energy 260× worse). Registered secondary (marginal-matched): median 110× BETTER than independence, but paired CI (-0.00004, 0.00197) includes 0 → **FAIL by the frozen rule** (a minority of countries where matched agents overshoot dependence drag the tail) |
| (iv) held-out questions (8 frozen items) | E1-transfer 25.62 pp | semantic-neighbour (gte-base) 25.93 pp; LLM NOT RUN (authorization) | beat baseline, CI excluding 0 | **FAIL** — diff CI (-2.68, 3.91) pp includes 0. Both arms are poor; Q51 (gone-without-food) is >79 pp wrong for both — neither transfers to material-deprivation items |
| (v) cross-wave deltas | — | no-change / trend | — | **BLOCKED-ON-DATA** (WVS/EVS Trend file not in the estate; in-repo W5/W6 numbers are inadmissible estimates) |

Misses are reported as misses. No arm was added, removed, or re-run
after seeing a number.

## What the evidence actually says

1. The 26-feature living readout does not encode enough between-country
   signal: its CV national MAE (15.2 pp) is worse than its own 0.4-era
   dev figure (10.5–11.3 pp on the old unweighted targets) and far from
   MRP (9.57 pp on the new weighted targets). The weighted targets are
   harder for it, not easier.
2. The hybrid arm as frozen (MRP logit offset + centered Earth-1
   spread) DAMAGED the MRP level rather than preserving it: sigmoid
   averaging over the agent spread shifts the national mean (a
   construction property, visible only after the one-shot run; recorded
   as analysis, not excuse — the arm ran exactly as registered).
3. The one structural signal: given correct marginals, Earth-1's agents
   reproduce cross-item DEPENDENCE far better than independence in the
   median country (1.4e-05 vs 1.5e-03 energy) — but not uniformly
   enough to clear a CI gate. This is the only place the agent
   structure showed measurable value, and it is exactly the place the
   Bible predicted the claim would move to.
4. Nothing here validates or invalidates the event-response operator
   (Benchmark B); this was the cross-sectional leg only.

## Calibration weights and the /ask lock

calibration_source (what answer_living WOULD carry if the founder
unlocked): `wvs7_v6.0_microdata_weighted/targets_v1@6c2f97fa/folds@cv_folds.json/scorer@9ad644b0/commit@a458c7f8067d`.
Recommendation embedded in the evidence: **the lock stays** — the
readout's national numbers are 5.6 pp behind the statistical
state-of-the-art, and serving them would misrepresent fidelity. If a
serving path is wanted now, it is MRP-as-calibration-layer with
Earth-1 abstaining on levels (below).

## Abstention map (the abstention is the brand)

Post-v1, Earth-1 ABSTAINS on: national opinion LEVELS (defer to
MRP/survey layer); cohort levels and age gradients; new-question
levels (transfer unproven; catastrophic on material-deprivation
items); anything cross-wave (no admissible data). Earth-1 may SPEAK,
with the marginal-matched caveat attached, on: joint/co-occurrence
structure given externally supplied marginals (median-country evidence,
CI not clean). Everything else on the capability matrix stays priced
work, not claims.

## Claims-inventory update (E0–E5)

- "Earth-1 predicts national survey means" — E1 (dev-era) → **E2-NEGATIVE
  (measured, loses to MRP by 5.6 pp on frozen holdout)**.
- "Earth-1 reproduces cohort gradients" — E1 → **E2-NEGATIVE** (43.8 % direction).
- "Agent structure carries joint-distribution signal" — E0 → **E2-PARTIAL**
  (median 110× better than independence given marginals; CI includes 0).
- "Earth-1 generalizes to unseen questions" — E0 → **E2-NEGATIVE at
  parity with a semantic-neighbour copy**.
- "Earth-1 tracks cross-wave change" — stays **E0 / untestable in estate**.
- Chaos/sensitivity chapter (0.8) untouched by this benchmark.

## Priced work queue (gaps, not claims)

1. WVS/EVS Trend microdata acquisition (founder licence action) —
   unlocks task (v) and honest cohort-over-time claims.
2. MRP-as-calibration-layer done at the AGENT level (poststratified
   offsets, mean-preserving) — the registered next hybrid; new prereg
   required (v2), zero physics.
3. Dependence-structure benchmark v2: per-country CI design (larger
   respondent subsamples, more items) to turn the median joint win
   into a CI-clean claim — measurement design, zero physics.
4. Feature work for between-country signal (gate-clean covariates
   only) — the 26 features are the binding constraint, not the folds.
5. LLM baseline execution (frozen prompt) — awaits authorization.

STOP. The /ask unlock, calibration_source deployment, and any external
circulation are founder rulings. GO B remains pre-authorized and
untouched by this result.
