"""Latent read: distribution, force anatomy, camps, conviction, fragility."""
from __future__ import annotations
import numpy as np
from earth1.types import (
    Civilization, Question, Force, FORCE_KEYS, NUM_FORCES,
    CampAnatomy,
)


def histogram(s: np.ndarray, bin_count: int = 20) -> np.ndarray:
    bins = np.clip((s * bin_count).astype(int), 0, bin_count - 1)
    return np.bincount(bins, minlength=bin_count)


def anatomize(
    civ: Civilization,
    s: np.ndarray,
    q: Question,
) -> dict:
    """Full decomposition: force anatomy, camps, conviction, fragility."""
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8)
    contrib = centered * q.weights[np.newaxis, :]       # (N, 8) element-wise
    abs_contrib = np.abs(contrib)

    # global force anatomy (normalized)
    total_abs = abs_contrib.sum(axis=0)  # (8,)
    s_all = total_abs.sum()
    force_anatomy = total_abs / max(s_all, 1e-12)
    dominant = Force(int(np.argmax(force_anatomy)))

    # camps
    yes_mask = s >= 0.5
    no_mask = ~yes_mask
    yes_n = int(yes_mask.sum())
    no_n = int(no_mask.sum())

    def camp_anatomy(mask: np.ndarray, n: int) -> CampAnatomy:
        if n == 0:
            return CampAnatomy(0, 0.0, Force.IDENTITY, np.zeros(NUM_FORCES))
        mean_stance = float(s[mask].mean())
        c = abs_contrib[mask].mean(axis=0)
        dom = Force(int(np.argmax(c)))
        return CampAnatomy(n, mean_stance, dom, c)

    camps = {
        "yes": camp_anatomy(yes_mask, yes_n),
        "no": camp_anatomy(no_mask, no_n),
    }

    # conviction — mean alpha of majority camp
    majority_mask = yes_mask if yes_n >= no_n else no_mask
    majority_n = max(yes_n, no_n)
    conviction = float(civ.alpha[majority_mask].mean()) if majority_n > 0 else 0.0

    # fragility — share near threshold + conformist
    near = np.abs(s - 0.5) < 0.12
    conformist = civ.alpha < 0.5
    near_conf = int((near & conformist & majority_mask).sum())
    fragility = min(1.0, (near_conf / max(majority_n, 1)) * 1.6)

    return {
        "force_anatomy": force_anatomy,
        "dominant": dominant,
        "camps": camps,
        "conviction": conviction,
        "fragility": fragility,
    }
