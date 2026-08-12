"""Feed-forward layer: vectorized force projection.

logit(stance) = baseline + (forces - means) @ weights
stance = sigmoid(logit)

At 1M agents this is a single matrix multiply — ~10ms on CPU, <1ms on GPU.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Civilization, Question, NUM_FORCES
from earth1.rng import sigmoid


def project_all(
    civ: Civilization,
    q: Question,
    field_shift: np.ndarray | None = None,
) -> np.ndarray:
    """Project all agents onto a question. Returns (N,) stance array in [0,1]."""
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8) - (1, 8)
    if field_shift is not None:
        if field_shift.ndim == 1:
            centered = centered + field_shift[np.newaxis, :]
        else:
            centered = centered + field_shift
    z = q.baseline + centered @ q.weights  # (N,)
    return sigmoid(z)
