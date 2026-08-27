# EXPERIENCE LOOP v0 — REPORT (scored under frozen gates)
2026-08-27. Prereg EXPERIENCE_LOOP_V0_PREREG.md. 12 sealed truths,
24 cycles, 4 arms, all runs complete, ledger replay IDENTICAL.

## VERDICT: EXPERIENTIAL_LEARNING_DEMONSTRATED = **NO** (as gated)
Reported as a miss under the frozen gates. The diagnostic content is
strong and redirects v0.1 precisely.

## What the run DID demonstrate
- Learning vs frozen is enormous and causal: late-cycle CRPS
  experiential 0.466 vs frozen 99.56 (WS worlds); the shuffled-
  resolution placebo does NOT improve (119.5 — worse than frozen).
  Wrong resolutions ⇒ no learning. Real resolutions ⇒ 200× improvement.
- G3 recovery PASS: final posterior |u-error| 0.027 (relax) / 0.095
  (memory_press).
- G6 replay: bit-identical model-hash chain.
- Misspecified worlds: the learner still improves (0.72 → 0.25) while
  frozen degrades (2.2 → 5.5) — learning under model error works.

## Why the verdict is NO — four precise causes
1. **G1b (the claim that matters): the naive Holt smoother beat the
   mechanistic learner** (late CRPS 0.353 vs 0.466). Founder amendment
   1 anticipated exactly this: v0's truth streams are UNFORCED,
   near-stationary converged worlds — a smoother's best arena. A world
   model earns its keep when the future is NOT like the past. v0.1
   adds registered shocks.
2. **G1 statistic broken by heavy tails**: frozen-arm CRPS spans
   orders of magnitude across worlds (extreme prior θ ⇒ degenerate
   worlds ⇒ z-scores ~100), so the paired t CI is [-125, +323] around
   a +99 mean. The effect is unambiguous; the statistic is wrong for
   the scale. v0.1 registers paired log-CRPS + Wilcoxon.
3. **G2 coverage 0.74**: SMC degeneracy — repeated resampling collapses
   predictive dispersion below the CRN noise floor. v0.1 registers
   post-resample θ-jitter (rejuvenation) + residual-based observation-
   noise inflation of predictive intervals.
4. **G4 3/4 MIS worlds overconfident-wrong**: the median-distance ABC
   bandwidth self-normalizes, so systematic misfit still discriminates
   relatively and the posterior contracts onto biased values. v0.1
   registers a bandwidth FLOOR at the particle NN-distance noise proxy:
   when misfit dominates, the likelihood flattens and uncertainty is
   retained ("an uncertain parameter must remain uncertain").

## Disposition
v0 banked as a diagnostic instrument run. No gate is reinterpreted
post-hoc. v0.1 (EXPERIENCE_LOOP_V0_1_PREREG.md) registers the design
changes BEFORE running, on FRESH sealed truths.
Artifacts: /opt/earth1-data/exploop/{v0_report.json, arms/, streams/,
replay_9001.json}; ledgers hash-chained per arm.
