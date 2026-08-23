# PRE-REGISTERED — float32 ensemble-mode equivalence gate (0.7)

Frozen BEFORE any float32 result exists (founder ruling, 2026-08-20).
Committed at the SHA this file first appears in; analysis code may gain
bugfixes, but observables, margins, horizons, N, and pass criteria may
not move after f32 data is seen.

## Claim under test

`EARTH1_PRECISION=float32` is a numerical EXECUTION MODE of the same
Earth — not a cheaper alternate Earth. Representation changes; model
semantics do not: no parameter retuning, no altered thresholds, no
fewer agents, no fewer subsystems, no reduced graph, no lower horizon,
no alternate loop, no changed stochastic laws. Production (CCX33) and
0.8 remain float64. f64 is the reference implementation forever; any
optimized executor is judged against it.

## Design

Baseline: the frozen day-1142 snapshot (sha `379212b2…`), canonical
loader, full 4M scale — identical to ENSEMBLE_PROTOCOL_0_7.md.

Matched quadruples with common random numbers, i = 1…N, N = 8:

    (control_i^64, scenario_i^64, control_i^32, scenario_i^32)

all four under `np.random.default_rng(710000 + i)`; scenario = the
frozen +0.20 FEAR shock. The scientific quantity is the PAIRED EFFECT

    Δ_i^p = obs(scenario_i^p) − obs(control_i^p),  p ∈ {64, 32}

and the gate compares Δ^32 against Δ^64 — individual-agent identity is
explicitly NOT the test (chaos amplifies ULPs by design).

Horizons: observables recorded at day 3 (early), day 15 (middle), and
day 30 (terminal — the frozen workload's horizon). A mode harmless at
day 3 and unacceptable at day 30 fails.

## Observable bundle (families j)

Scalars unless noted; distributions compared by mean + P10/P50/P90.

1.  demography: alive, cumulative deaths, cumulative births
2.  labour: employment rate, mean wage (employed), mean tenure
3.  material: mean wealth, deprivation mean + deciles, share
    deprivation > 0.99
4.  health: cumulative disease deaths, mean mental, mean physical,
    mean addiction
5.  housing/insecurity: evicted share, mean arrears (crime has no
    direct channel in the current World; insecurity is its recorded
    proxy family)
6.  migration/fabric churn: cumulative rehomed_migrants,
    rehomed_workers
7.  institutions: policy_net mean, firm_health mean, firms failed
    (journal)
8.  forces: per-channel (8) mean and SD across alive agents
9.  readout/opinion: share force > 0.5 per channel (the pole
    fractions the opinion path consumes)
10. network: nnz, degree mean/P99, weight mean/max for friends+weak;
    ties strengthened/weakened/pruned/rewired (journal, terminal day)
11. memory/knowledge: memories remembered, people_under_memory
12. cascades: cumulative cascades_fired
13. rankings: Spearman rank correlation of the top-20 most populous
    countries ranked by (a) mean deprivation, (b) mean FEAR — f32
    ranking vs f64 ranking on the SAME seed, plus scenario-effect sign
    agreement per country
14. effects: every scalar family above as Δ (scenario − control)

## Pre-registered margins and criteria

Two independent references per family, fixed before any f32 run:

- SD_seed(j): the f64 seed-to-seed standard deviation of family j
  across the N=8 f64 pairs (for Δ families, the SD of Δ_i^64).
- RES(j): scientific resolution floors, set now: opinion/pole shares
  3.0pp (WVS-band resolution, BIBLE Benchmark A); demographic counts
  0.1% of population; rates/shares 0.5pp absolute; means of bounded
  [0,1] quantities 0.01; network counts 1%; rank correlations ≥ 0.9
  admissible, effect-sign agreement ≥ 90% of country-channel cells
  with |Δ^64| above its own seed noise.

Primary metric per family and horizon:

    R_j = RMSE_i(obs^32_i − obs^64_i) / SD_seed(j)

PASS requires, at EVERY horizon:
- R_j ≤ 0.5 for every scalar family (precision error comfortably
  subordinate to stochastic uncertainty);
- paired TOST-style check: the 95% CI of mean(obs^32 − obs^64) lies
  within ±max(SD_seed(j), RES(j));
- Δ-family criteria identical, applied to Δ^32 − Δ^64;
- ranking and sign criteria of family 13 met at the terminal horizon.

FAIL of any single criterion rejects float32. No post-hoc margin
adjustment: if a margin proves ill-posed (e.g. SD_seed ≈ 0 for a
degenerate observable), the observable is reported, the anomaly
documented, and the gate decided on the remaining families ONLY if the
degenerate case is shown to be identically zero in both precisions;
otherwise FAIL.

## Failure control (Standing Rule 2)

The instrument must be able to reject. A deliberately degraded
executor — state quantized through float16 at load
(`EARTH1_PRECISION=float16-control`), M = 3 pairs, same seeds — must
FAIL the same gate. If the degraded control passes, the gate is too
weak and the study is void regardless of the f32 result.

## Compute plan

8 pairs × 2 arms × 2 precisions × 30 days = 960 world-days, plus
3 × 4 × 30 = 360 for the f16 control. Runner: scripts/precision_ab.py
(observables recorded at days 3/15/30 in-run). Manifests record
precision explicitly — a float32 artifact can never masquerade as
float64. All artifacts + manifests committed.

## Decision

PASS → float32 certified as an admissible ensemble executor for the
scoped workload → saturation curve re-run under f32 → the exact frozen
20-pair job, bar unchanged (<30 min wall-to-wall). Misses the bar →
continue machine/performance work; the bar does not move.
FAIL → float32 rejected, result preserved, back to performance
engineering/hardware options. Fidelity is not traded for throughput.
