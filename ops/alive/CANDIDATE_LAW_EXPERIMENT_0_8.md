# 0.8 CANDIDATE-LAW EXPERIMENT — pre-registration (Deliverable C)

FROZEN with the empirical registry, before any candidate produces a
number. The registry (EMPIRICAL_TARGET_REGISTRY_0_8.md) decides;
no candidate wins by architectural elegance.

## Candidate families (three concrete laws + the incumbent)

All candidates modify ONLY `update_conviction` (and, where stated,
its agreement input). `life_force_target` relax=0.25/day is
UNTOUCHED in this experiment by founder ruling. Coefficients (gain,
λ) are FIT exclusively against registry target T1 (information-shock
force half-life 5–15 days, residual 0.2–0.6 at day 30) via the
A5-style tau instrument on 200k worlds — then frozen before any
validation target is scored.

- **C1 — heterogeneous anchoring (Friedkin–Johnsen family):**
  α_i ← clip(α_i + gain·(agr_i − 0.5)·2 − λ·(α_i − α0_i)), with
  α0_i = the agent's OWN genesis conviction (no new trait
  dependence; `doubt` is deliberately NOT used pending independent
  justification). Pole-based agreement unchanged.
- **C2 — continuous-distance agreement + anchoring:** as C1, but
  agr_i = 1 − 2·(weighted mean neighbor |Δf| across channels) —
  disagreement registers as continuous distance, not pole fractions
  (a railed unanimous world no longer reads as agreement 1.0 by
  construction of the distance on real-valued forces).
- **C3 — endogenous symmetric confidence (no anchor):** α updated in
  log-odds space (bounds become asymptotes, not absorbing rails)
  with symmetric hardening/softening driven by continuous-distance
  agreement; no per-agent anchor term.
- **C0 — incumbent law** (the production ratchet) runs alongside as
  the known-pathological reference.

## Negative controls (the instrument must catch all three)

- NC1 planted ratchet = C0 itself → battery MUST fail it (absorbing
  α, railing, tau ≪ registry band).
- NC2 excessive mean reversion = winning-family λ × 10 → battery
  MUST fail it (tau below T1 band; T6/T7 structure violations).
- NC3 absent persistence/dynamics = gain 0 (α frozen at anchor) →
  battery MUST fail it (T6: certainty cannot move; T7 structure).

If any NC passes, the battery is too weak and the experiment is
VOID before any candidate verdict.

## Evaluation battery (identical for every arm; exact 0.8-A
instruments + registry scoring)

1. 730-day no-news 200k endogeny (shared seeds across arms): α
   trajectory, per-channel census, saturation shares.
2. Registry T5: sd collapse >50% or growth >100%, or saturation
   share >20% on any channel → FAIL.
3. Registry T6: forced-disagreement probe (relocate a 1k cohort into
   maximally-disagreeing neighborhoods; α must fall within weeks);
   absorbing-state scan (no α bound reached irreversibly) → FAIL if
   violated.
4. Registry T7: median-agent averaging-term contribution bounded
   away from zero → FAIL if dead.
5. T1 CALIBRATION: info-shock tau map — fit gain/λ, freeze.
6. VALIDATION (scored after freeze, no refits): T2 two-component
   FEAR decay shape after an event-scale shock; T3 material-shock
   persistence class (month-scale + residual, via a mini outcome
   probe); T4 within-agent force autocorrelation at lag ~365d
   ∈ [0.5, 0.9] on non-railed channels.
7. All NCs detected.

A candidate that needs refitting after seeing step-6 results is a
NEW candidate and re-registers.

## Registered decision rule

PASS = structural constraints (2–4) + T1 in band + validations
within registry uncertainty + NCs caught. Multiple passers →
registered tiebreak: fewest parameters, then best T3/T4 joint score.
Zero passers → XI.A: diagnose, research, NEW registration; no quiet
coefficient surgery.

## Prohibitions (founder ruling, verbatim intent)

- No coefficient chosen because a histogram looks healthy.
- No `doubt` dependence merely because the field exists.
- No tuning toward making the India opinion result move — the probe
  retest happens ONLY for an already-accepted candidate, and its
  desired outcome is a NON-PATHOLOGICAL computed response, including
  zero if that is what the corrected state implies.
- No change to relax=0.25/day in this experiment.
- Production (CCX33) untouched; Epoch 2 is NOT created as part of
  this experiment — initialization/replay design is a separate
  founder decision after acceptance.
