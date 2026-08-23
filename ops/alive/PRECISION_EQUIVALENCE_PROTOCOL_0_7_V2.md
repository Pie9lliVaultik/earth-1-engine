# PRE-REGISTERED — float32 equivalence gate, V2 (0.7)

Frozen BEFORE execution (founder ruling, 2026-08-20). V1
(PRECISION_EQUIVALENCE_PROTOCOL_0_7.md, run `2026-08-20T112035Z`,
commit 66a1348) remains an OFFICIAL REJECTED ATTEMPT, preserved
unchanged and never reinterpreted. What v1 diagnosed: part of the
instrument was non-identifiable — the frozen +0.20 FEAR intervention
is a null effect on a world whose FEAR channel sits at 0.978
(saturated against the upper bound), so effect ratios divided by
denominators that had collapsed to numerical dust. V2 repairs the
instrument; it does not soften the decision.

Unchanged from v1: the claim under test, the baseline snapshot
(day-1142, sha 379212b2…), full 4M scale, N = 8 quadruples + 3-pair
degraded control, 30 days, horizons {3, 15, 30}, the observable
bundle, LEVEL criteria (R_level ≤ 0.5 with TOST-in-margin — the
criteria that rejected f16 with 153 breaches), ranking criteria, the
f16-control validity requirement, and the hard decision rule. The
frozen 20-pair PERFORMANCE workload is untouched by this document.

## V2 corrections

1. **Discriminating intervention, selected by rule.** The perturbation
   is applied on the registered force channel in the direction of
   greatest baseline headroom from its [0,1] bounds, magnitude 0.20,
   same target (most populous country of the frozen snapshot). For the
   day-1142 snapshot this resolves deterministically to **−0.20 FEAR**
   (headroom 0.978 downward vs 0.022 upward). Scenario members:
   `forces[alive & country==TARGET, FEAR] -= 0.20`, clipped to [0,1].

2. **Fresh randomness.** SEED_BASE_V2 = 720000 (v1 used 710000) —
   the amended criteria are judged on randomness no analysis has seen.

3. **No division by dust.** For every effect row (observable j,
   horizon h):
       D_j = max(SD(Δ64_j), RES_j)
       R_eff_j = RMSE(Δ32_j − Δ64_j) / D_j
   with the v1-registered RES resolutions. Classification BEFORE
   grading: a row is **INFORMATIVE** iff |mean(Δ64_j)| > RES_j;
   otherwise UNINFORMATIVE — reported, not graded, never PASS or FAIL.
   Study VALIDITY floor (pre-registered): ≥ 15 informative effect rows
   at the terminal horizon spanning ≥ 3 observable families, else the
   study is VOID (instrument still non-identifiable) and f32 remains
   uncertified without being newly rejected.

4. **Deterministic quantities get numerical tolerance, not bit
   identity.** Rows with SD_seed(f64) = 0 (deterministic in the
   reference, e.g. the 2.0 weight cap) PASS iff
   RMSE ≤ 1e-6 × max(1, |level|) (≈10× f32 epsilon) AND ≤ RES_j where
   RES_j > 0; else FAIL. No post-hoc adjustment.

5. **Sign agreement on informative cells only.** A country-channel
   cell qualifies iff |mean(Δ64)| > max(per-cell seed SD, 0.01).
   Agreement ≥ 90% of qualifying cells; if fewer than 10 cells
   qualify, family 13 is decided by the Spearman criterion alone.

## Decision (unchanged in hardness)

f32 passes EVERY informative pre-registered family at every horizon,
the deterministic-tolerance rows, rankings, and the validity floor is
met, AND the f16 control FAILS the same v2 machinery → CERTIFIED.
Any informative breach → REJECTED. No majority voting. If the f16
control passes v2, v2 itself is void.

## Standing note for 0.8 (not actioned here)

Production FEAR ≈ 0.978 is a high-priority 0.8 diagnostic: is the
saturation empirically justified by the world state and information
stream, or is ingestion/force-loading/decay/feedback pinning the
population? It is investigated with evidence in 0.8 — never "fixed"
inside a performance experiment.
