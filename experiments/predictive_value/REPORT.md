# Predictive-Value Grid — Report

**Run:** 2026-08-17, earth1-prime. 80 combos (8 variants × 2 benchmark
classes × 5 seeds), 50K agents, spec frozen at `5036ad9` before W5 data
existed. Zero failed combos. Ledger: `ledger.jsonl` (append-only).
Honesty label: W6→W7 is a diagnostic evaluation, NOT blind (§3 of
EXPERIMENT_PLAN.md); sign accuracy is CONTAMINATED by prior inspection.

## Temporal class (W6→W7, 7y, MAE of Δ — primary metric)

| Variant | MAE (±sd over 5 seeds) | Sign acc.* |
|---|---|---|
| no-change (A-0) | 0.02905 | — |
| **B individual** (no social machinery) | **0.02707 ±0.00010** | 0.768 |
| C full civilization | 0.03146 ±0.00065 | 0.535 |
| C − feedback | 0.02702 ±0.00020 | 0.773 |
| C − diffusion | 0.03179 ±0.00072 | 0.528 |
| C − coupling / − rewire / − thresholds / − eventgen | ≈ C full (Δm ≈ 0) | ≈ C |

*contaminated metric, reported per registration.

**Δcivilization = err(B) − err(C) = −0.00439 ±0.00065** — the
civilization machinery makes temporal prediction WORSE by 0.44pp.

**Per-mechanism attribution (Δm = err(C−m) − err(C)):**
- feedback **−0.00444 ±0.00055** — removing feedback recovers B exactly.
  The ENTIRE damage is the feedback ring.
- diffusion +0.00033 (marginal help inside C), coupling −0.00001,
  rewire −0.00000, thresholds +0.00000, eventgen +0.00000 (exercise
  check: zero endogenous events fired — "not exercised", as the Ring-B
  finding predicted).

## Event class (A3 COVID rally, aggregate ratio)

All eight variants: **ratio 0.9704 ±0.0006, 5/5 passes, identical to
four decimals.** The response law does all the work; no social
mechanism contributes measurably to the event-leg aggregate.

## Registered conclusion

The registered space was C>B>A / B>A,C≈B / B≈C≈A. Measured reality is
**outside it and sharper: B > A-0 > C** on the secular class:

1. **B beats no-change** (0.02707 < 0.02905, consistent to ±0.0001
   across seeds): the demographic/generational machinery alone carries
   real temporal signal on this benchmark.
2. **C loses to doing nothing**, and the entire gap is ONE mechanism:
   opinion→trait feedback. This convicts the same ring the threshold-
   envelope diagnostic caught moving national FEAR means 0.16/yr under
   the ordinary tick with zero events.
3. Event class: B ≈ C exactly — the event pass owes nothing to
   emergence.

## What this does NOT conclude

- Whether feedback's drift is a bookkeeping artifact (same-intensity
  nudges compounding unboundedly per question per tick) or intended
  physics that reality contradicts — that is the SAME three-outcome
  adjudication the cohort-inheritance case got, now owed to Ring C.
- Anything about the formative-development channel (Q1) — A6 betas not
  yet fit; those arms run after `fit_secular.py` freezes them.
- B's 0.768 sign accuracy is a contaminated metric and is NOT claimed
  as blind evidence.

## Failures / caveats

- min_obs_delta filter and per-question detail live in the ledger rows.
- Guard-holdout country split not yet broken out (all-pairs shown);
  report.py refinement owed.
- W5-dependent baselines (A-1 trend, A-3 development) not in this run.
