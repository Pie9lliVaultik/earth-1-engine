# EXPERIENCE LOOP v0 — PREREG (frozen before any cycle runs)
2026-08-27. Founder ruling: EXPERIENCE LOOP v0 is the PRIMARY mission
(C2+ and SBI-gain run parallel, serving it). All four founder
amendments adopted: (1) structure-free naive learner as a third arm —
the claim that matters is experiential Earth beating it; (2)
misspecified-truth condition; (3) plateau expectation + paired CI
across ≥10 worlds; explicit state-assimilation scope; (4) compute gate
first with the reduced-fidelity fallback as primary.

## COMPUTE GATE (amendment 4 — first return)
v0 (this prereg): 20k fidelity, eligible θ = {relax, memory_press}.
12 hidden worlds × 720 days; learner = 64-particle SMC-ABC free-running
worlds; arms exp/placebo = 64 worlds each, frozen = 20-member prior
ensemble; truth streams simulated once.
Estimate: ≈ 2.0×10^5 CPU-s ≈ **2.5–3 h wall at ≤30 slots, ~60 GB RAM**
on prime. critical_fraction enters at v0.1 (200k, ~10× — a half-day
run) ONLY after the v0 verdict.

## STATE-ASSIMILATION SCOPE (amendment 3 — explicit)
v0 learns **θ only**. x0 is shared truth↔learner by construction
(same genesis seed); no state assimilation occurs; model worlds
free-run, so state error accumulates honestly. Consequence accepted:
the v0 curve is EXPECTED TO PLATEAU once θ posteriors converge — the
plateau height (vs frozen and vs naive) IS the v0 result, not a
failure. The compounding "smarter every day" curve lives in state
assimilation (x_t) and enters at v0.2/v1 via the EnKF layer; v0 does
not claim it.

## Hidden truths (sealed)
12 worlds, genesis seeds 9001–9012, 20k agents, 720 days.
- 8 WELL-SPECIFIED: θ* = {relax, memory_press} ~ prior (A1 ranges),
  all else canonical.
- 4 MISSPECIFIED (seeds 9009–9012): additionally beta = 3.0 (canonical
  2.0) and hardship_mortality_gain = 2.0 — physics error OUTSIDE the
  learner's eligible set; the learner cannot represent it.
Sealing: theta bundle written by plant stage, SHA-256 committed before
any learner runs; truth streams contain ONLY window observables (no θ);
learner processes read streams, never truth files. Unseal at score.
Memory probes (registered, θ-independent, identical in every truth and
model world): A4.1 probe at days 10, 190, 370, 550 (salience decay
would otherwise starve memory_press observability late in the run).

## Cycles and observables
24 cycles × 30-day windows. Per-window observable vector (frozen):
window-mean employment_rate, destitute_share, deprivation mean; end-of-
window force_mean[8], force_sd[8], pole_share[8]; window delta of
force_mean[8] — 38 values. Proper score: CRPS per observable
(z-scored by truth-stream pooled sd), averaged; skill = −CRPS.
Forecasts are always for the NEXT unseen window; improvement is never
scored on the observation that produced the update.

## Arms (per hidden world; paired by world)
- FROZEN: 20 model worlds, θ drawn once from prior (seeded), free-run;
  predictive = ensemble of window observables. Never updates.
- EXPERIENTIAL: SMC-ABC over u(relax, memory_press): 64 particles from
  prior, each with its own free-running world; per cycle weights ×=
  exp(−d²/2h²) (d = z-scored distance particle-window vs revealed
  window; h = median-distance heuristic); ESS<32 ⇒ systematic
  resample (world deep-copied from parent). Predictive = weighted
  particle ensemble.
- NAIVE (structure-free, amendment 1): Holt exponential smoothing per
  observable (α=0.5, β_trend=0.3, residual sd from expanding window)
  fed the identical revealed stream; Gaussian CRPS closed form.
- PLACEBO (shuffled resolution, primary causal control): identical SMC
  learner but update distances computed against a DERANGED world's
  stream (σ: 9001→9002→…→9001 within spec class); forecasts scored
  against its OWN truth.

## Experience receipts
Every (world, arm=experiential/placebo, cycle): immutable Experience
record (earth1/experience.py): experience_id, forecast_emitted_at,
forecast_world_hash, model/inference version, observation_cutoff,
predicted distribution (per-observable ensemble quantiles),
uncertainty, resolution rule, resolution, resolution source, score,
prior posterior (particle summary), eligible update evidence, posterior,
update diff (weight/resample delta), next model hash. Hash-chained
JSONL; replaying the ledger from M0 must reproduce every M_t hash.

## Success gates (verdicts at score time; plateau expected)
Primary pair (amendment: placebo sits beside learning):
- G1 LEARNING: paired (frozen − experiential) mean CRPS over cycles
  13–24, 95% CI across the 8 WS worlds excludes 0 in favour of
  experiential.
- G7 CAUSALITY: placebo shows no comparable improvement (its paired
  improvement CI includes 0, or is significantly below experiential's).
- G1b BEATS-NAIVE (the claim that matters): experiential CRPS <
  naive CRPS on cycles 13–24, paired CI across WS worlds excludes 0.
  If naive matches experiential, v0 demonstrates calibration, not the
  thing we want — report as such.
- G2 CALIBRATION: 90% predictive-interval coverage pooled over WS
  worlds/cycles 13–24 ∈ [0.80, 0.97].
- G3 RECOVERY (WS): posterior mean |u-error| for relax & memory_press
  < 0.5 × prior sd by cycle 24; posterior sd non-increasing trend.
- G4 NO FALSE LEARNING (MIS): 90% posterior CI covers true relax &
  memory_press in ≥3/4 misspecified worlds (misspecification must not
  produce confident wrong θ).
- G5 NO FORGETTING: weak evidence with 2 θ (recorded, not retired):
  no observable family's CRPS degrades >20% from its cycle-1–6 mean
  while overall skill improves.
- G6 REPLAYABILITY: ledger replay of one world reproduces all model
  hashes exactly.
EXPERIENTIAL_LEARNING_DEMONSTRATED = YES iff G1 ∧ G1b ∧ G7 ∧ G2 ∧ G6
(G3 expected on WS; G4 mandatory-honest on MIS; failures reported).
Misspecified-world skill curves are reported SEPARATELY — they predict
v1 behaviour under model error.

## Dev-mode note
This is development: learner hyperparameters (h heuristic, resample
threshold, α/β of naive) may be iterated ON DEV RERUNS with the change
log recorded; gates themselves and the sealed truths never move.
No holdout/prospective data is touched anywhere in v0.
