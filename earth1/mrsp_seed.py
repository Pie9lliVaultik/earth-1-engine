"""MrsP AS INITIALIZER — the composed architecture's first layer.

Division of labour (2026-08-18, after MrsP parity 0.0856 beat the
engine's 0.1059 and the hybrid 0.0842 beat MrsP alone):

    MrsP owns LEVELS      — where each country sits right now, with
                            partial pooling and regularization
    Earth-1 owns SHAPE    — the within-country distribution
    Earth-1 owns DYNAMICS — what happens next (MrsP has no next)

This module re-anchors the engine's per-agent stances so the country
MEAN equals the MrsP estimate while the engine's within-country
STRUCTURE is preserved exactly. The shift is applied in logit space,
which preserves the shape of the distribution up to a translation and
keeps every stance in (0, 1).

Nothing here changes production defaults; it is a composition helper
used by the experiments that test the composed system.
"""
from __future__ import annotations

import numpy as np

from earth1.rng import logit, sigmoid


def reanchor(stances: np.ndarray, mask: np.ndarray,
             target_mean: float) -> np.ndarray:
    """Shift a country's stances in logit space so their mean equals
    `target_mean`, preserving within-country structure.

    Returns a copy of `stances` with only `mask` positions changed.
    """
    s = np.clip(stances[mask], 1e-4, 1 - 1e-4)
    z = logit(s)
    lo, hi = -12.0, 12.0
    tgt = float(np.clip(target_mean, 1e-4, 1 - 1e-4))
    for _ in range(60):                       # bisection on the shift
        mid = 0.5 * (lo + hi)
        if float(sigmoid(z + mid).mean()) < tgt:
            lo = mid
        else:
            hi = mid
    out = stances.copy()
    out[mask] = sigmoid(z + 0.5 * (lo + hi))
    return out


def compose(stances: np.ndarray, country: np.ndarray,
            code_to_idx: dict, level_by_country: dict) -> np.ndarray:
    """Re-anchor every country present in `level_by_country`."""
    out = stances
    for cc, lvl in level_by_country.items():
        if cc not in code_to_idx:
            continue
        m = country == code_to_idx[cc]
        if m.sum() >= 10:
            out = reanchor(out, m, lvl)
    return out
