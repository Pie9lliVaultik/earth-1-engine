"""Feed-forward layer: vectorized force projection.

logit(stance) = baseline + (forces - means) @ weights
stance = sigmoid(logit)

At 1M agents this is a single matrix multiply — ~10ms on CPU, <1ms on GPU.

THE ONE LAW (Build 30, 2026-08-17): an external EVENT changes expressed
opinion through exactly one operator — the temporal response law:

    resp = RESPONSE_GAIN * (event_deltas @ question.response_profile)

Events never enter the cross-sectional features (run #9 measured that
path at ratio -0.027, wrong sign) and never enter the social-broadcast
channel (a constructed sign-conflict showed the propagation door
REVERSING the validated law). A question without a response profile
does not react to events at read time: unmodeled response is honest,
wrong-signed response is not.

field_shift is a DIFFERENT physical object: counterfactual/coupled
field state (multiverse rehearsal branches, cross-question coupling).
It keeps cross-sectional semantics — it describes a different world,
not a shock arriving in this one.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Civilization, Question, NUM_FORCES
from earth1.rng import sigmoid


# Named physics configuration. Every published number states this.
# E1-0.4: scalar bounded-confidence diffusion + the one response law.
#   Inheritance basis "current": children inherit the parent's present
#   (age-drifted) state — produces slow endogenous conservative drift,
#   measured over 200y zero-forcing in data/cohort_drift_test.json.
# E1-0.5 (REGISTERED CANDIDATE, not adopted): cohort-entry-basis
#   inheritance ("entry") — age effects stay life-cycle, never becoming
#   heritable cohort effects; stationary by design. Adoption awaits the
#   A/B adjudication against real longitudinal cohort behavior
#   (scripts/inheritance_ab_test.py). Neither drift nor stationarity is
#   a bug by definition — reality decides which ontology is right.
# The force-dynamics path (8-channel propagation) is EXPERIMENTAL until
# it passes a gate on its own — it must never silently serve production.
PHYSICS_VERSION = "E1-0.4"

# Temporal response gain — the one fitted constant of the response law
# (d_logit = GAIN * shock . response_profile). Registered for G5 run #7
# as the leave-COVID-out fit over the other five reaction cases (the
# case run #7 tests never touched this number). LOO folds ranged 2.0-3.1.
RESPONSE_GAIN = 3.1


def project_all(
    civ: Civilization,
    q: Question,
    field_shift: np.ndarray | None = None,
    event_shift: np.ndarray | None = None,
) -> np.ndarray:
    """Project all agents onto a question. Returns (N,) stance array in [0,1].

    field_shift — counterfactual/coupled field state (multiverse,
        coupling): enters the cross-sectional features, because it
        describes a different standing world.
    event_shift — ACTIVE EXTERNAL EVENTS: enters through the temporal
        response law only. No response profile -> no read-time reaction.
    """
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8) - (1, 8)
    if field_shift is not None:
        fs = field_shift[np.newaxis, :] if field_shift.ndim == 1 else field_shift
        centered = centered + fs
    resp_term = 0.0
    if event_shift is not None and q.response_profile is not None:
        es = event_shift[np.newaxis, :] if event_shift.ndim == 1 else event_shift
        resp_term = RESPONSE_GAIN * (es @ q.response_profile)
    z = q.baseline + centered @ q.weights + resp_term  # (N,)
    return sigmoid(z)
