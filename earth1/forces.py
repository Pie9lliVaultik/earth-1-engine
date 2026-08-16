"""Feed-forward layer: vectorized force projection.

logit(stance) = baseline + (forces - means) @ weights
stance = sigmoid(logit)

At 1M agents this is a single matrix multiply — ~10ms on CPU, <1ms on GPU.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Civilization, Question, NUM_FORCES
from earth1.rng import sigmoid


# Temporal response gain — the one fitted constant of the response law
# (d_logit = GAIN * shock . response_profile). Registered for G5 run #7
# as the leave-COVID-out fit over the other five reaction cases (the
# case run #7 tests never touched this number). LOO folds ranged 2.0-3.1.
RESPONSE_GAIN = 3.1


def project_all(
    civ: Civilization,
    q: Question,
    field_shift: np.ndarray | None = None,
) -> np.ndarray:
    """Project all agents onto a question. Returns (N,) stance array in [0,1].

    Two laws, two paths for field_shift:
      - response_profile set  -> TEMPORAL law: events move opinion through
        the question's signed response profile (validated on historical
        reaction cases; sign structure LLM-authored blind to outcomes)
      - response_profile None -> legacy: events perturb the cross-sectional
        projection (the path G5 run #6 proved cannot reproduce measured
        reactions — kept for questions without a profile)
    """
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8) - (1, 8)
    resp_term = 0.0
    if field_shift is not None:
        fs = field_shift[np.newaxis, :] if field_shift.ndim == 1 else field_shift
        if q.response_profile is not None:
            resp_term = RESPONSE_GAIN * (fs @ q.response_profile)
        else:
            centered = centered + fs
    z = q.baseline + centered @ q.weights + resp_term  # (N,)
    return sigmoid(z)
