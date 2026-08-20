# 0.4 ACCEPTED — the opinion layer reads the person who lived it

**2026-08-19 · dev gate closed on the frozen protocol · holdout untouched**

## The journey, preserved in full

| iteration | result |
|---|---|
| 1 (`b0c00a4`) | living-26 worse everywhere (paired −0.48pp) — MISS recorded |
| 2 | hierarchical estimator isolated (+0.71pp, R²w −0.75→+0.31); estimator-constant living still −0.27pp — stayed open |
| 3 | contract-C literal (between=legacy, living within-only): best arm on every metric |
| closure | all three pre-committed conditions PASS |

## Closure evidence

**Q1 seed stability** — hybrid−legacy per frozen seed: **+0.010 / +0.049 / +0.025 pp — beneficial sign on all three.**

**Q2 hybrid ablations** (ΔL>0 = earns): addiction +0.011, spells +0.009,
deprivation +0.002, hunger +0.002 **earn positive value**; unemployed and
mental neutral; isolation −0.004, hope −0.001. Per-channel attribution at
these magnitudes is noisy; four of eight earning satisfies the criterion.

**Q3 permutation control** — five fixed within-country shuffles of the
living block (marginals and country identity preserved): **Δ = −0.100,
−0.105, −0.112, −0.128, −0.110 pp — the advantage does not merely
collapse, it inverts.** Destroyed correspondence hurts; real lived state
helps. The gain is bucket↔lived-state correspondence, not dimensions.

## Honest magnitudes

Improvement is currently SMALL: cohort MAE 11.435→11.406 (closure rerun
11.390→11.362); within-country R² 0.3136→0.3466; gradient 82.9→83.3%;
calibration undegraded (0.927). **0.4 is an architectural gate, not
Benchmark A**: it establishes that correctly placed living-state
information carries real incremental signal beyond the legacy
representation. How much value can be extracted is Benchmark A's job.

The accepted architecture is the thesis' shape:
**country structure from legacy · within-country deviations from lived
state.**

## Registered, deliberately untouched

- `in_lf`/retirement defect (N6): evidence-backed next-XI.A candidate;
  excluded from this experiment to keep the comparison frozen.
- Production world inadmissible for scoring (2026 news ingested);
  admissibility table in every artifact.
- Iterations 1–3 + closure artifacts all committed with provenance.

## Mechanics

Provenance frozen (`data/feature_provenance.json`) · release gate
ELIGIBLE · readout-only deploy (live_one_day untouched since `ca95903`,
so the world trajectory is bit-identical when no opinion query is made;
restart continuity verified at deploy) · tag `phase0-0.4` · 0.5 begins.
