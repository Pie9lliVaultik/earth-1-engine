# SEMANTICS — THE BINARY READOUT (what the served number IS)

Founder ruling 2026-09-08: emergence experiment — ruling 3, first step
(external review M07a; options and verification in
RULING_REQUEST_BINARY_READOUT.md). Scope of this step: establish the
readout's semantics and make the served surface say what the number is.
No formula change, no physics change; p_model and every computed value
byte-identical. The founder's standard applies: relabel-alone is only
enough if the quantity is valid; a construction that cannot represent
the observable must be redesigned. This document shows the quantity IS
valid — for a different observable than the one its old name claimed —
and names the redesign track for the observable it cannot carry.

## 1. The registered construction (nothing here is new)

As registered in the module docstring of earth1/adapters/multiverse.py:

    binary:  P(YES) = d_NO / (d_YES + d_NO)
    d_X = Euclidean distance between the null world's and world_X's
          census-weighted scoped 8-force mean at horizon end.

world_X is a real Earth-1 branch in which outcome X is injected as an
accomplished fact and evolved to the horizon under common random
numbers; the null branch is the same world, unforced. No constant or
formula beyond that registration is used or revealed here.

## 2. What p IS

d_YES and d_NO are displacement magnitudes: how far the world's
aggregate force state is moved by imposing each outcome, relative to
the world's own unforced evolution. Therefore

p = d_NO / (d_YES + d_NO) is a NORMALIZED RELATIVE BRANCH-DISPLACEMENT:
the share of the total hypothesized-consequence displacement
(d_YES + d_NO) carried by the NO branch.

Read as proximity, equivalently: p is large exactly when the YES-world
stays close to the null world's own evolution relative to the NO-world.
It is a proximity/consistency measure between the null world's
evolution and each outcome's modelled consequences — which outcome's
aftermath is more consistent with where the unforced world was already
going. Served name: `branch_consistency`.

Immediate structural properties:

- p is in [0,1] and p_YES + p_NO = 1 — an artifact of normalization,
  not evidence of a probability model.
- p depends only on the ratio d_YES/d_NO: scaling both modelled
  consequences by any common factor leaves p untouched. There is no
  magnitude-of-evidence channel.
- Likelihood appears nowhere. Both branches condition on the outcome
  having already happened; nothing in the construction observes the
  mechanism that selects between the outcomes.

## 3. Why this construction CANNOT represent an event probability

The direction-blindness argument. Hold d_NO fixed. p_YES =
d_NO / (d_YES + d_NO) is strictly decreasing in d_YES. But d_YES is the
modelled CONSEQUENCE magnitude of YES, not its likelihood. So, by
construction: the larger an outcome's modelled consequence, the smaller
the number assigned to it — independent of how likely the event is. An
event probability must be free to move with likelihood at fixed
consequence and to stay put at fixed likelihood; this quantity can do
neither, because likelihood is not an input.

Minimal numeric example (the reviewer's shape: disruptive but likely).
Take an event that is near-certain and world-changing, whose
non-occurrence is a non-event:

    d_YES = 0.9   (YES massively displaces the world)
    d_NO  = 0.1   (the NO-world is nearly the null world)
    p_YES = 0.1 / (0.9 + 0.1) = 0.10

A near-certain event is served at 10%. Swap the magnitudes and a
world-changing but near-impossible event is served at 90%. With
symmetric consequences (d_YES = d_NO) the readout pins 0.50 for ANY
true likelihood. The failure is in the map, not in a calibration
constant: no relabeling of inputs, rescaling, or per-class temperature
makes this construction an event probability, because the quantity that
an event probability measures is absent from it.

Live illustration at payload level (tiny world, 2k agents, c2plus_v1,
class market_cascade, 8-day horizon; distances are served fields): the
crash outcome's own consequence dominates, d_YES ≈ 3 × d_NO, and the
readout serves p ≈ 0.25 — the number is low BECAUSE the modelled
consequence is large, exactly the constructional bias.

The two frozen under-calls on resolved-YES events carry this signature:
SVB (p_model 0.302, banking contagion within 30d, resolved YES) and
Sri Lanka (p_model 0.3985, government fall within 120d, resolved YES).
Both outcomes had large modelled consequences; a big consequence pushes
d_YES up and p down. The readout's shape is a verified partial
explanation of both misses (RULING_REQUEST_BINARY_READOUT.md),
alongside the separately named missing physics channels.

## 4. What p CAN validly represent

- RELATIVE CONSEQUENCE-CONSISTENCY: which outcome's modelled aftermath
  is closer to the null world's own evolution, and by what share of the
  total displacement. This quantity is registered, deterministic,
  reproducible to seven decimals, and every committed forecast — misses
  included — is on the record under sealed protocol. Under its honest
  name, the number is valid as served.
- An ORDINAL SIGNAL over the underlying force geometry, whose ordering
  the pre-committed protest register partially validated: real
  protest-onset countries rank above quiet controls at Spearman
  ρ = 0.552 (p = 0.0052), Mann-Whitney p = 0.0044 — with the register's
  own caveat standing: the ORDERING is real; the probabilities are not
  calibrated (no significant Brier improvement over base rate). The
  same status holds here: within-class order may carry signal; the
  number's location on [0,1] is not an event frequency.

## 5. The three ruling options (as put to the founder)

Per RULING_REQUEST_BINARY_READOUT.md:

- Option A — KEEP the formula, RELABEL the served output honestly;
  event probabilities withheld until a calibrated mapping exists.
- Option B — CALIBRATE a monotone map p = g(d_YES, d_NO) on resolved
  events only; keeps the substrate signal and earns the word
  probability empirically.
- Option C — REDESIGN the readout (e.g. counted agent-response
  fractions instead of distance ratios); a named cycle of its own, with
  frozen-forecast revalidation from scratch.

This document plus the additive serving fields execute the A-shaped
first step of ruling 3: the analysis and the honest surface. Relabeling
is sufficient for the observable the construction validly computes
(branch consistency); it is NOT sufficient for event probability — that
observable requires the track below.

## 6. What the served surface now says (additive; values untouched)

Binary forecast payloads from earth1/adapters/multiverse.py ask()
carry, next to p_model:

    "semantics": "branch_consistency"
    "semantics_note": "normalized branch-displacement ratio;
        not a calibrated event probability
        (see SEMANTICS_BINARY_READOUT.md)"

p_model, p_by_outcome, distances, and every other computed value are
byte-identical to the pre-ruling payload (regression with a captured
pre-change expectation: tests/test_review_semantics.py). Historical
frozen artifacts and the registered-forecast display path are
unaffected.

## 7. The redesign track and its blocker (per the ruling)

The path to a number that MAY be called an event probability is a
SEPARATE LEARNED CALIBRATION/READOUT:

- a monotone map g(d_YES, d_NO) → p (Option B; Option C only if B
  fails), TRAINED ON PROSPECTIVE RESOLUTIONS as the register accrues
  them;
- kept OUTSIDE the canonical engine: a calibration layer over the
  served distances, never inside the frozen physics and never a silent
  edit to the registered adapter formula;
- EVALUATED ON HELD-OUT RESOLUTIONS before serving — fit on TRAIN/DEV,
  verify on HOLDOUT; no served probability before the held-out check
  passes.

BLOCKER, stated as of 2026-09-08: the resolution count. The prospective
register (ops/alive/PROSPECTIVE_REGISTER.jsonl) holds 293 registered
forecasts and 0 resolutions to date. Resolved binary events with frozen
forecasts exist only in the historical battery — single digits (the
ruling request's own count), including the two under-calls above.
Single-digit n cannot support both fitting a map and holding out
resolutions to verify it. Until the register accumulates resolutions,
this document and the served semantics fields are the serving contract.
