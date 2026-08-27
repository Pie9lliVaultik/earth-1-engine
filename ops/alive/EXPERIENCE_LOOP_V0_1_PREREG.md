# EXPERIENCE LOOP v0.1 — PREREG (frozen before any v0.1 cycle runs)
2026-08-27. Dev-mode iteration of v0 per MISSION v2 ("iterate on the
learner until the improvement is real and stable"), registered fresh:
new sealed truths, amended gates registered BEFORE results. v0's
truths are consumed; nothing from v0 is rescored under these gates.

## Changes vs v0 (each mapped to a v0 failure)
1. **Registered shocks (fixes the arena, v0 cause 1).** Truth AND all
   model worlds receive identical known forcing u_t: at days 240 and
   480, a shock memory (salience 1.0, half-life 60 d, signature
   ECONOMICS −0.12 / FEAR +0.12, scope = all alive). Forcing is known
   to the mechanistic arms by construction (it is u_t, not hidden
   state). Naive arms: (a) naive-blind — unchanged Holt smoother;
   (b) naive-forced — Holt + an additive shock-response vector learned
   from the first shock's residuals and applied at the second.
2. **Statistics (v0 cause 2):** all arm comparisons on paired
   log-CRPS differences (mean log-ratio, 95% CI across WS worlds) plus
   Wilcoxon signed-rank p.
3. **SMC dispersion (v0 cause 3):** post-resample rejuvenation —
   θ-jitter N(0, 0.02²) in u-space, reflected at [0,1], worlds keep
   parent state; predictive intervals and CRPS computed on the
   ensemble augmented with deterministic observation-noise offsets
   (±{0, 0.52, 1.28}·σ_obs, equal weights), σ_obs = causal running RMS
   of weighted-mean-forecast residuals per observable.
4. **Misspecification honesty (v0 cause 4):** ABC bandwidth
   h_t = max(median(d), median NN-distance among particle windows).
   When systematic misfit dominates, weights flatten and the
   posterior stays wide.
Everything else unchanged: 12 fresh sealed truths (8 WS + 4 MIS with
β=3.0, hardship_gain=2.0), seeds 9101–9112, 20k, 24×30 d cycles,
eligible θ = {relax, memory_press}, frozen/experiential/placebo arms,
hash-chained receipts, replay stage.

## Gates (registered)
- G1 log-CRPS: frozen vs experiential, CI excludes 0 favouring exp.
- G1b THE CLAIM: experiential beats **naive-blind** on late cycles
  (13–24), paired log-CRPS CI excludes 0. naive-forced is reported;
  beating it is the stretch goal, not the gate.
- G8 STRUCTURE GATE (new): experiential beats naive-blind on the
  shock-affected cycles {8, 9, 16, 17} specifically — the windows
  where structural knowledge must show.
- G7 placebo: no comparable improvement (as v0).
- G2 coverage 0.80–0.97 (late cycles, WS pooled).
- G3 recovery, G4 MIS-coverage ≥3/4, G5 no-forgetting (weak, recorded),
  G6 replay identical — as v0.
EXPERIENTIAL_LEARNING_DEMONSTRATED = YES iff
G1 ∧ G1b ∧ G8 ∧ G7 ∧ G2 ∧ G6.

## Compute
Same shape as v0 ≈ 2.5–3 h at ≤30 slots, concurrent with the v2 gain
battery (45 slots); 96 cores absorb both.
