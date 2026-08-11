"""Perishability curves — the commercially decisive claim.

Fear-dominant consensus decays in weeks; identity-dominant holds for generations.
Same number today, radically different shelf life.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Force, PERISHABILITY_HALF_LIFE


def decay_curve(
    yes_pct: float,
    dominant: Force,
    months: int = 24,
) -> dict:
    """Generate decay curves for the dominant force and a durable baseline."""
    hl = PERISHABILITY_HALF_LIFE[dominant]
    hl_durable = PERISHABILITY_HALF_LIFE[Force.IDENTITY]

    days = np.arange(0, months * 30 + 1, 30)
    actual = 0.5 + (yes_pct - 0.5) * np.power(0.5, days / hl)
    durable = 0.5 + (yes_pct - 0.5) * np.power(0.5, days / hl_durable)

    return {
        "months": (days / 30).astype(int).tolist(),
        "actual": actual.tolist(),
        "durable_baseline": durable.tolist(),
        "half_life_days": hl,
        "dominant": dominant.name.lower(),
    }
