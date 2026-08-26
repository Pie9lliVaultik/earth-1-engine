# BENCHMARK A — REPORT v2 (confirmation, one shot)

Prereg: BENCHMARK_A_PREREG_v2.md frozen @509a1ce; pre-result amendments
@8e8e121 (task-iv unit, deterministic binarization) — all recorded before
any confirmation number existed. Confirmation set: 98 genuinely untouched
WVS-7 items (targets built after the freeze, sha 659a6675…). Baselines
committed before any Earth-1 v2 readout. One harness VOID (fixed
bisection bracket pinned on 2 of ~18,000 cells at extreme anchor × wide
spread) repaired with an extended KA and the stage rerun before scoring.
Worlds: the three frozen 200k Epoch-3-physics labs. Leakage guard ran on
every scored row (fails closed); zero violations.

## HEADLINE

**With the level supplied by out-of-sample MRP and all leakage removed,
Earth-1's agent structure currently adds nothing measurable beyond the
statistical baseline — on cohorts, on joint dependence, and on zero-shot
transfer.** The v2 architecture itself works exactly as designed (the
hybrid inherits the MRP marginal to 0.0 error and preserves agent
heterogeneity); what it reveals is that the structure inside today's
26-feature living readout does not yet carry incremental empirical
signal. It also reclassifies v1's one bright spot: the "110× better
joint dependence" was an artifact of marginal-matching against the
OBSERVED target marginals; with MRP-anchored marginals in both arms the
advantage collapses to noise.

## Scoreboard (untouched confirmation set, evaluated once)

| task | Earth-1 | strongest baseline | CI | gate |
|---|---|---|---|---|
| (i) level inheritance (sanity, no credit) | max |hybrid − anchor| = **0.0** across all cells; KA worst 1.0e-9 | — | — | **PASS** |
| (ii) cohort cells (164,997 cell-evals) | 10.58 pp, gradient 50.5 % | global-gradient 9.92 pp, 68.5 % (cohort-MRP 10.06 pp, 63.9 %) | strongest − E1 = −0.65 pp (−0.67, −0.63) | **FAIL** (rel. reduction −6.6 %; gradient at coin-flip) |
| (iii) joint dependence, MRP-anchored marginals both arms (63 countries, Q7–Q15) | median energy 0.1848 | independence 0.1858 | indep − E1 = −0.0023 (−0.0077, +0.0034) | **FAIL** (CI includes 0; the shared MRP marginal error dominates both arms) |
| (iv) zero-shot cohort cells (4,188 cells, 8 items) | 21.28 pp | national-copy (= transfer anchor) 21.09 pp | −0.19 (−0.33, −0.05) | **FAIL** (E1 significantly *worse* by 0.19 pp) |
| (v) cross-wave | — | — | — | **BLOCKED-ON-DATA** |

Feature treatment (frozen pre-confirmation): hunger dropped (r = 0.999
with deprivation), 25 columns kept, condition number 160. Compression
trace: raw latent spread 4.44 (logit) → published spread 0.451; no
stage after mean-preservation altered any marginal; abstentions counted
(cells with <30 agents dropped).

## What this settles, and what it does not

- The **calibration architecture is right and now proven mechanically**:
  level from data, structure from agents, exact mean preservation,
  leakage-clean anchors, honest decomposition (`calibration_source`).
  This is the serving architecture regardless of today's structure score.
- The **structure itself is the deficit**. Cohort gradient at 50.5 %
  says the living features carry essentially no real age-band signal for
  these items; the joint result says their cross-item dependence is not
  distinguishable from independence once marginals are equalized
  fairly. v1's contrary joint signal is reclassified as leakage-adjacent
  (observed-marginal matching).
- Claims inventory: "agent structure carries joint-distribution signal"
  E2-PARTIAL → **E2-NEGATIVE (confirmation, leakage-clean)**. "Cohort
  heterogeneity" stays E2-NEGATIVE, now on untouched data. The
  calibration-layer architecture itself: **E3 (mechanically verified,
  KA + leakage controls, one-shot confirmed sanity)**.
- Where value must come from now (unchanged by any of this, and untested
  here): **event response** — Benchmark B's domain. The cross-sectional
  levels are conceded to the statistical layer by design; static
  structure has now twice failed to beat simple baselines; the remaining
  scientific bet is dynamics under perturbation, which no statistical
  baseline models.

## Answer block (founder format)

- exact architecture: logit p_i = logit p_MRP(OOS) + Δ_i − K; K bisected (adaptive bracket) to ≤1e-9
- what MRP supplies: every absolute level (country, transfer anchor, joint marginals)
- what Earth-1 must earn: cohort deviations, dependence, zero-shot structure — it earned none on confirmation
- mean-preservation proof: KA 200 cases ≤1e-9 + extreme-regime test; confirmation max error 0.0
- leakage controls: per-row anchor provenance, fails closed; zero violations; observed-marginal variant demoted to diagnostic
- cohort strategy: country anchor + agent deviations (weighted aggregate exact); baselines incl. cohort-MRP
- joint strategy: MRP-anchored marginals both arms; dependence-only comparison
- held-out-question strategy: neighbour-weight transfer + neighbour's OOS MRP anchor, scored on cohort cells
- redundant/orthogonalized features: hunger dropped (r 0.999); 25 kept; cond 160; country axes removed by centering
- v1 holdout status: CONSUMED (development only)
- genuinely untouched v2 holdout: 98 items, used once, now also consumed
- v2 ready to execute: was YES; executed; **result: architecture PASS, structure FAIL**

STOP. /ask remains locked (nothing here justifies opening it). The
evidence points the program at Benchmark B (pre-authorized "GO B") and
at feature/structure work — not at more cross-sectional calibration.
