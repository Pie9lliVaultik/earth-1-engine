# PRE-REGISTERED — float32 ensemble-consistency gate, V3 (0.7)

Frozen BEFORE execution (founder Ruling A, 2026-08-20). v1 (66a1348)
and v2 (run 2026-08-20T121126Z) remain REJECTED, unrewritten. The
forensic at fb33857 established that paired microscopic tracking is
not a valid fidelity criterion for this chaotic simulator: a one-ULP
perturbation flips a discrete stochastic event at a seed-dependent
onset time, after which f32 is a different sample path on the same
attractor — indistinguishable from a different seed. v3 therefore
asks the correct question:

    P_32(Y, Δ)  ≈?  P_64(Y, Δ)

— does float32 sample the same macroscopic model distribution — via
ensemble consistency (the CESM-ECT lineage: Baker et al. 2015),
never per-member pairing across precisions.

## Ensembles (fresh, unseen seeds; each arm independent)

| arm | executor | pairs | seeds |
|---|---|---|---|
| A (reference) | float64 @ fb33857 | 10 | 730001…730010 |
| B (known-answer PASS control) | float64 @ fb33857 | 10 | 731001…731010 |
| X (candidate) | float32 @ fb33857 | 10 | 732001…732010 |
| C (known-answer FAIL control) | float16-control | 3 | 733001…733003 |

Pair = (control, scenario) sharing the pair's seed; scenario = the v2
headroom intervention (−0.20 FEAR, most populous country). Baseline:
frozen day-1142 snapshot, full 4M, 30 days, horizons {3, 15, 30}.
Observable bundle: unchanged from v1/v2 (earth1/observables.py).

## Criteria (all frozen now)

Per observable row j (scalar × horizon), from ensemble A:
μ_A, σ_A = mean and SD across A's pairs (levels: control arm; effect
rows: per-pair Δ = scenario − control). For test ensemble T:

- margin M_j = max(1.25 × σ_A, RES_j) with the v1-registered RES
  resolutions (margin calibration: under the true null the sampling
  SD of μ_T − μ_A at N=10 is ≈ 0.45 σ_A, so P(false breach) ≈ 0.6%
  per row — chosen so the B-vs-A known-answer control passes with
  high probability WITHOUT weakening f16 discrimination, whose
  observed shifts are 2–10 σ_A)
- row BREACH: |μ_T − μ_A| > M_j; SEVERE: > 2 M_j
- dispersion row breach: variance ratio s_T²/s_A² outside [1/6, 6]
- family-horizon cell FAILS iff (breach fraction > 20% AND ≥ 2
  breaches) OR any severe breach
- effect rows: informative iff |μ_A(Δ)| > RES_j (v2 rule); only
  informative rows are graded; validity floor unchanged (≥ 15
  informative terminal rows across ≥ 3 families, else VOID)
- effect-sign cells (country × channel, terminal): qualify iff
  |mean Δ_A| > max(cell seed SD, 0.01); ≥ 90% sign agreement of
  ensemble-mean effects; < 10 qualifying cells → Spearman decides
- rankings (terminal): Spearman of ensemble-mean country vectors
  (deprivation, FEAR) between T and A ≥ 0.9
- families/RES/observables identical to v1/v2 — no additions, no
  removals after data

## Known-answer controls — the instrument must prove itself

1. B vs A MUST PASS every family-horizon cell. If it does not, the
   instrument is INVALID and the study is VOID (no verdict on f32).
2. C (f16) vs A MUST FAIL at least one family-horizon cell. If it
   passes, the instrument is insufficiently discriminating and the
   study is VOID.

## Decision (hard, no majority voting)

Instrument valid (both known-answer controls behave) AND X passes
every family-horizon cell, signs, rankings, and the validity floor →
**f32 CERTIFIED as a scoped ensemble executor at fb33857**. Any
material family failure → REJECTED. Production and 0.8 remain f64;
f64 stays the permanent reference implementation.

## After certification (founder Ruling B)

The <30-min bar does not move; CPU micro-optimization stops. The
acceleration leg evaluates, in order: higher-bandwidth CPU nodes; GPU
offload of profile-proven bandwidth-dominated kernels only; and
multi-node ensemble distribution (members are independent — the
ensemble is embarrassingly parallel at the member level). Every
candidate runs the SAME frozen protocol with orchestration and data
movement included in wall-clock. CCX33 is never loaded with research
compute.
