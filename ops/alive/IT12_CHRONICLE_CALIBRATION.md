# 0.8 IT12 — CHRONICLE PERSISTENCE CALIBRATION (pre-registered)

IT11 (48c1751) preserved: FAIL on the scored band; carrier
architecture validated. IT12 calibrates the validated carrier.
Architecture frozen = IT6-ALL + Chronicle, nothing else.

## IT12-A — coefficient census (from code; provenance classified)

- Memory.half_life 720d: AUTHORED (docstring rationale) — the
  calibration subject.
- REHEARSAL_BOOST 0.35: AUTHORED — participates in the composite;
  kept at production value, flagged; a pass validates structure with
  this parameter classified authored/unproven (amendment-1 style).
- FORGOTTEN 0.02: authored, immaterial to the 30d window at scored
  half-lives (salience stays ≫ 0.02).
- press coefficient 0.02/day: AUTHORED — sets transfer AMPLITUDE,
  not persistence SHAPE; the scored quantity is the NORMALIZED
  persistence curve (ratio to peak), which is press-invariant in the
  linear regime. Amplitude calibration deferred to effect-size
  evidence in the acceptance program.
- spread rate 0.06: authored; excluded from the scored composite
  (spread disabled in scored arms — recurrence is supplied by the
  frozen external schedule, not endogenous spread).
CONCLUSION: half_life is the scored free parameter; boost enters the
composite and is disclosed as authored; no hidden coefficient.

## Derivations (independent, then combined)

INTRINSIC h*: from the T1 corpus element closest to single-exposure
persistence (one-shot exposure decay class): the day-10 ~50% point
interpreted as predominantly intrinsic ⇒ h* = 10d exactly
(0.5^(10/10) = 0.5). Point estimate; no bracket scored.
RECURRENCE: from news-lifecycle evidence (attention decays over
~1–2 weeks with thinning follow-up coverage): frozen schedule of
similar-signature follow-up events at days {1, 2, 4, 7, 11}
post-event, follow-up salience 0.5 (registered layer scale),
processed through the PRODUCTION rehearsal path
(chronicle.remember: boost +0.35 on the original + layered object).
ANALYTIC COMPOSITE (pre-run, frozen): d30/peak = 0.268 → IN BAND;
intrinsic-only d30 = 0.125 → below band (recurrence is load-bearing
and its necessity is the scientific finding under test). Registered
tension: composite d10/peak ≈ 0.78 vs corpus ~0.5 — attributed to
corpus re-exposure ambiguity; reported as diagnostic, NOT scored.

## Scored test

Canonical FEAR+0.5 clustered-cohort event (IT11 protocol) at day 90
on the frozen architecture, fresh seed 8904:
- INTRINSIC arm: h*=10, no follow-ups, spread off → carrier must
  match analytic decay; d30 expected below band (diagnostic).
- COMPOSITE arm (SCORED): h*=10 + frozen follow-up schedule, spread
  off → normalized day-30 expression residual ∈ [0.2, 0.6].
- REF720: incumbent half-life, unscored pathological reference.
Health gates: all IT6 gates on the composite arm (sat/sdr/rings/α).

## Known answers

IT11 set retained (continuity, carrier-delete, no-decay,
analytic-decay exact, scope, restart, sign) + REHEARSAL SEMANTICS
EXACT: one scheduled similar event ⇒ original salience becomes
min(1, s+0.35) exactly and one layered object appends — executed
values must equal analytic expectation within frozen tolerance
BEFORE the composite is trusted. Any KA failure ⇒ VOID.

## Calibration vs validation (registered)

The T1 corpus is too small to split honestly. h* is therefore
CALIBRATED, not externally validated; an independent persistence
case is REQUIRED during the 0.8 acceptance program. No manufactured
independence.

## Decision

VOID (KA) / FAIL (composite misses band → diagnose which evidence
component failed; no neighboring-h search) / PASS → freeze the exact
Chronicle parameterization (h*=10 for news-class events; 720
retained only if re-derived for its own event class later); no
further persistence tuning; proceed to decay_half_life contract
implementation (separately traced: legacy semantics RECOVERED —
read-time decaying level shift, see DECAY_HALF_LIFE_TRACE.md) and
then FREEZE COMPLETE CANDIDATE → full 0.8 battery.
