"""/observatory — standing readings of the living civilization. 0.5e."""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter

from earth1.api.deps import get_world

router = APIRouter(prefix="/observatory", tags=["observatory"])


@router.get("/standing-readings")
def standing_readings():
    w, identity = get_world()
    from earth1.chaos import entropy
    alive = w.health.alive
    wealth = w.life.wealth[alive]
    srt = np.sort(np.clip(wealth, 0, None))
    cum = np.cumsum(srt)
    gini = float(1 - 2 * (cum / max(cum[-1], 1e-9)).mean()) if len(srt) \
        else 0.0
    return {
        "identity": identity,
        "entropy": round(entropy(w.civ.forces), 4),
        "wealth_gini": round(gini, 4),
        "mean_conviction": round(float(w.civ.alpha[alive].mean()), 4),
        "mental_ill": round(float((w.life.mental[alive] < 0.3).mean()), 4),
        "isolated": round(float(
            (w.life.relationship[alive] < 0.25).mean()), 4),
        "memories_standing": len(w.chronicle.events),
    }
