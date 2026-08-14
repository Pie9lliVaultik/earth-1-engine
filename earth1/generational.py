"""Generational dynamics — aging, mortality, births, inheritance (bible §21.1).

The mechanism of slow secular change. Weight decay models how shock
reactions fade; generational replacement models why societies drift —
younger cohorts enter with different values than the elders they replace.

Mechanics (vectorized, fixed-N slot replacement):
  Aging      — every agent ages with the tick clock.
  Mortality  — Gompertz hazard calibrated per country so the modal age
               at death tracks the census life expectancy.
  Birth      — a death frees a slot; a newborn adult (18) fills it in
               the same country. Population count and graph topology
               stay fixed — the newborn inherits the household's social
               position; composition and values change.
  Inheritance — child traits = heritability x parent + (1-h) x country
               mean, plus an optional per-trait cohort drift and noise.
               Education/income inherit with mobility noise.

Default cohort_drift is ZERO: secular drift should emerge from
inheritance, feedback, and the receiver — not from a hand-authored
prior. The parameter exists for controlled experiments.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from earth1.types import Civilization
from earth1.genesis import GENESIS_COUNTRIES
from earth1.feedback import _recompute_forces

# Gompertz slope: adult human mortality doubles roughly every 8 years.
GOMPERTZ_B = 0.085

# age encoding (genesis.py): raw years 18..90 -> age = (raw - 18) / 72
_AGE_SPAN = 72.0
_AGE_MIN = 18.0

_INHERITED_TRAITS = (
    "openness", "empathy", "risk_appetite", "doubt", "desire_intensity",
    "conscientiousness", "agreeableness", "extraversion", "neuroticism",
)


def _age_years(civ: Civilization) -> np.ndarray:
    return _AGE_MIN + civ.age * _AGE_SPAN


def _cohort_mean_age_at_death(a: float, b: float = GOMPERTZ_B) -> float:
    """Mean age at death for a cohort entering at 18 under Gompertz
    hazard h(x) = a * exp(b * (x - 18)), by discrete survival sum."""
    years = np.arange(0.0, 122.0 - _AGE_MIN)
    # cumulative hazard from 18 to 18+n: (a/b) * (exp(b*n) - 1)
    cum_h = (a / b) * (np.exp(b * years) - 1.0)
    survival = np.exp(-cum_h)
    return _AGE_MIN + float(survival.sum())


def _gompertz_a(life_expectancy: float) -> float:
    """Baseline hazard such that the COHORT mean age at death matches
    the census life expectancy.

    The previous calibration pinned the *modal* age at death to LE,
    which left the mid-life hazard several times the real rate and
    dragged mean age at death ~25 years under LE (G5 run #2 finding).
    Solved numerically; cached per LE value.
    """
    le = round(float(life_expectancy), 1)
    if le in _GOMPERTZ_A_CACHE:
        return _GOMPERTZ_A_CACHE[le]
    lo, hi = 1e-8, 0.1
    for _ in range(60):
        mid = np.sqrt(lo * hi)  # log-scale bisection
        if _cohort_mean_age_at_death(mid) > le:
            lo = mid
        else:
            hi = mid
    _GOMPERTZ_A_CACHE[le] = float(np.sqrt(lo * hi))
    return _GOMPERTZ_A_CACHE[le]


_GOMPERTZ_A_CACHE: Dict[float, float] = {}


def generational_tick(
    civ: Civilization,
    rng: np.random.Generator,
    dt_days: float = 1.0,
    heritability: float = 0.4,
    cohort_drift: Optional[Dict[str, float]] = None,
    mobility: float = 0.3,
    return_details: bool = False,
) -> Dict[str, int]:
    """One generational step: age, die, be born. Returns {'deaths': n}.

    return_details=True adds 'dead_ages' (years) and 'dead_countries'
    (country indices) arrays — needed by the G5 demography leg.
    """
    cohort_drift = cohort_drift or {}
    dt_years = dt_days / 365.0

    # ── aging ──
    civ.age = np.clip(civ.age + dt_years / _AGE_SPAN, 0.0, 1.0)
    age_years = _age_years(civ)
    civ.age_bucket = np.digitize(age_years, [30, 45, 60, 75])

    # ── mortality: per-country Gompertz ──
    le_by_country = np.array([c.get("le", 72.0) for c in GENESIS_COUNTRIES])
    a = np.array([_gompertz_a(le) for le in le_by_country])[civ.country]
    hazard_yr = a * np.exp(GOMPERTZ_B * (age_years - _AGE_MIN))
    p_death = np.clip(hazard_yr * dt_years, 0.0, 1.0)
    dead = rng.random(civ.n) < p_death
    n_dead = int(dead.sum())
    if n_dead == 0:
        if return_details:
            return {"deaths": 0, "dead_ages": np.array([]),
                    "dead_countries": np.array([], dtype=int)}
        return {"deaths": 0}

    dead_idx = np.flatnonzero(dead)
    dead_ages = age_years[dead_idx].copy()
    dead_countries = civ.country[dead_idx].copy()

    # ── birth into the freed slots, same country ──
    # parent pool: adults 30-60 in the same country (weighted by presence)
    parent_ok = (age_years >= 30) & (age_years <= 60) & ~dead
    # cohort anchor (Manifold v2): newborns regress toward the YOUNG
    # cohort's mean, not the all-ages mean. Genesis conditions traits on
    # age (younger = more open, more risk-appetite); anchoring births to
    # the all-ages mean erased that gradient every turnover and made
    # liberalization drift impossible (G5 run #2/#3: t_homosexuality
    # predicted -4pp vs observed +4pp). The young-cohort mean is
    # empirical and evolves with the world — emergent, not authored.
    young = age_years <= 30.0
    for c in np.unique(civ.country[dead_idx]):
        slots = dead_idx[civ.country[dead_idx] == c]
        pool = np.flatnonzero(parent_ok & (civ.country == c))
        parents = (rng.choice(pool, size=len(slots))
                   if len(pool) > 0 else None)
        cmask = civ.country == c

        for t in _INHERITED_TRAITS:
            arr = getattr(civ, t)
            ymask = cmask & ~dead & young
            if ymask.sum() >= 20:
                c_mean = float(arr[ymask].mean())
            elif (~dead & cmask).any():
                c_mean = float(arr[cmask & ~dead].mean())
            else:
                c_mean = float(arr[cmask].mean())
            base = (heritability * arr[parents] + (1 - heritability) * c_mean
                    if parents is not None else np.full(len(slots), c_mean))
            drift = float(cohort_drift.get(t, 0.0))
            arr[slots] = np.clip(
                base + drift + rng.normal(0.0, 0.08, len(slots)), 0, 1)

        # demographic slots
        civ.age[slots] = 0.0                       # 18 years old
        civ.age_bucket[slots] = 0
        if parents is not None:
            keep = rng.random(len(slots)) > mobility
            civ.education[slots] = np.where(
                keep, civ.education[parents],
                rng.integers(0, 3, len(slots)))
            civ.income[slots] = np.where(
                keep, civ.income[parents],
                rng.integers(0, 3, len(slots)))
            civ.urban[slots] = civ.urban[parents]
        # conviction starts young: genesis formula from openness
        civ.alpha[slots] = np.clip(
            0.28 + 0.5 * civ.openness[slots]
            - 0.12 * (1.0 - civ.openness[slots]), 0, 1)

    # newborn (and everyone's) forces follow from current traits
    _recompute_forces(civ)
    civ.means = civ.forces.mean(axis=0)

    if return_details:
        return {"deaths": n_dead, "dead_ages": dead_ages,
                "dead_countries": dead_countries}
    return {"deaths": n_dead}
