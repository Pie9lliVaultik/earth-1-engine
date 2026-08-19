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

import os
from typing import Dict, Optional

import numpy as np

from earth1.types import Civilization, Force
from earth1.genesis import GENESIS_COUNTRIES
from earth1.feedback import apply_trait_delta


def _trait_formula_forces(civ: Civilization, idx: np.ndarray) -> np.ndarray:
    """The trait->force formula for selected agents only. Used solely to
    construct NEWBORN forces (plus the country residual); never applied
    to living agents, whose forces evolve incrementally."""
    out = np.zeros((len(idx), 8))
    out[:, int(Force.FEAR)] = (civ.doubt[idx] + (1.0 - civ.risk_appetite[idx])
                               + civ.neuroticism[idx] * 0.3) / 2.3
    out[:, int(Force.DESIRE)] = civ.desire_intensity[idx]
    out[:, int(Force.ECONOMICS)] = civ.economic_field[idx]
    out[:, int(Force.COLLECTIVE)] = ((1.0 - civ.openness[idx]) * 0.6
                                     + civ.power_distance[idx] * 0.4)
    out[:, int(Force.IDENTITY)] = (civ.openness[idx] * 0.5
                                   + civ.individualism[idx] * 0.5)
    out[:, int(Force.CULTURE)] = (0.5 + civ.culture_offset[idx]
                                  + civ.long_term_orientation[idx] * 0.1)
    out[:, int(Force.EXPERIENCE)] = civ.age[idx]
    out[:, int(Force.TEMPERAMENT)] = (civ.risk_appetite[idx] * 0.7
                                      + civ.extraversion[idx] * 0.3)
    return np.clip(out, 0.0, 1.0)


def _build_newborn_forces(civ: Civilization, slots: np.ndarray,
                          dead: np.ndarray) -> None:
    """Forces for newborn slots = trait formula + country residual.

    The residual (survivors' actual forces minus their formula forces,
    per country) carries the genesis conditioning — Hofstede, Inglehart,
    regional deltas — that a bare trait formula would erase."""
    for c in np.unique(civ.country[slots]):
        c_slots = slots[civ.country[slots] == c]
        base = _trait_formula_forces(civ, c_slots)
        survivors = np.flatnonzero((civ.country == c) & ~dead)
        if len(survivors) >= 20:
            resid = (civ.forces[survivors]
                     - _trait_formula_forces(civ, survivors)).mean(axis=0)
        else:
            resid = 0.0
        civ.forces[c_slots] = np.clip(base + resid, 0.0, 1.0)
        civ.forces[c_slots, int(Force.EXPERIENCE)] = civ.age[c_slots]

# Gompertz slope: adult human mortality doubles roughly every 8 years.
GOMPERTZ_B = 0.085

# age encoding (genesis.py): raw years 18..90 -> age = (raw - 18) / 72
_AGE_SPAN = 72.0
_AGE_MIN = 18.0

_INHERITED_TRAITS = (
    "openness", "empathy", "risk_appetite", "doubt", "desire_intensity",
    "conscientiousness", "agreeableness", "extraversion", "neuroticism",
)

# Trait aging (Manifold v2.1): agents slide along the SAME age gradients
# genesis bakes into the cross-section (per normalized age unit, 72y).
# Without this, cohort-anchored births produce runaway youth-ward drift —
# newborns enter young but nobody ever ages — which G5 run #4 caught:
# sign accuracy fell to 39.7%, significantly below chance. With entry
# AND aging, the trait distribution is stationary under a stationary
# pyramid; drift can only emerge from composition change, feedback, or
# exogenous signal — never from the aging machinery itself.
_AGE_GRADIENTS = {
    "openness": -0.08,
    "risk_appetite": -0.12,
    "desire_intensity": -0.30,
    "conscientiousness": +0.10,
    "agreeableness": +0.05,
    "extraversion": -0.06,
    "neuroticism": -0.04,
}


def _age_years(civ: Civilization) -> np.ndarray:
    return _AGE_MIN + civ.age * _AGE_SPAN


def advance_age(civ: Civilization, dt_days: float = 1.0) -> None:
    """Chronological aging — the clock, and ONLY the clock. Phase 0.0a.

    Extracted verbatim from generational_tick's aging block because the
    live world never called that function: `live_one_day` advanced no
    one's age, so every age-dependent hazard — cancer t^5, falls
    x2/decade, the road-death peak at 24, fertility windows,
    conscription, heat frailty — ran on a frozen day-0 age structure
    through every long run ever performed (BIBLE v4.1, R17).

    Scope is fixed by founder ruling (2026-08-19) and deliberately
    excludes the rest of generational_tick:
      - NO trait drift (_AGE_GRADIENTS) — behavioural physics, not a
        correctness fix;
      - NO EXPERIENCE re-assertion — in the living world EXPERIENCE is
        a real dynamical channel written daily by six modules;
        overwriting it from age would erase lived history (N10 is
        adjudicated at the 0.8 A/B, and the question there is decay vs
        accumulation, not overwrite);
      - NO mortality, NO rebirth — the live path has its own in
        health_tick and _be_born; a second demographic authority would
        double deaths and overwrite living people.

    Ages every slot, dead ones included — exactly as the original block
    did. Dead slots are recycled by _be_born with age = 0.0, so their
    drift is inert; skipping them would be a new behaviour, not an
    extraction.
    """
    d_age = (dt_days / 365.0) / _AGE_SPAN
    civ.age = np.clip(civ.age + d_age, 0.0, 1.0)
    civ.age_bucket = np.digitize(_age_years(civ), [30, 45, 60, 75])


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
    inheritance_basis: Optional[str] = None,
) -> Dict[str, int]:
    """One generational step: age, die, be born. Returns {'deaths': n}.

    return_details=True adds 'dead_ages' (years) and 'dead_countries'
    (country indices) arrays — needed by the G5 demography leg.

    inheritance_basis — the ontology of what parents transmit, UNDER
    ADJUDICATION (2026-08-17, A/B vs longitudinal reality):
      "current" (A, incumbent default): children inherit the parent's
        present state, age drift included. Cultural transmission of the
        lived self. Produces slow endogenous conservative drift
        (~ -0.001/yr openness, measured over 200y zero-forcing).
      "entry" (B, registered candidate E1-0.5): parents and cohort
        anchors are de-aged to their cohort-entry values before mixing
        (entry = current - gradient * age). Age effects stay life-cycle,
        never becoming heritable cohort effects. Stationary by design.
    Resolution order: explicit arg > EARTH1_INHERITANCE_BASIS env >
    "current". Whichever arm better reproduces real longitudinal cohort
    behavior becomes the default via a registered build; the loser is
    kept as an experiment flag.
    """
    cohort_drift = cohort_drift or {}
    basis = (inheritance_basis
             or os.environ.get("EARTH1_INHERITANCE_BASIS", "current"))
    dt_years = dt_days / 365.0

    # ── aging ──
    d_age = dt_years / _AGE_SPAN
    civ.age = np.clip(civ.age + d_age, 0.0, 1.0)
    age_years = _age_years(civ)
    civ.age_bucket = np.digitize(age_years, [30, 45, 60, 75])

    # traits age along the genesis gradients (see _AGE_GRADIENTS),
    # propagating into forces through the canonical sensitivities —
    # never a global rebuild (2026-08-16 audit: rebuilds erased priors)
    _all = np.ones(civ.n, dtype=bool)
    for t, g in _AGE_GRADIENTS.items():
        apply_trait_delta(civ, _all, t, g * d_age)
    # experience IS age — identity map, no prior to erase
    civ.forces[:, int(Force.EXPERIENCE)] = civ.age

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

    # Inheritance basis per the ontology under adjudication (see
    # docstring). "entry" de-ages the aging term only — learned
    # components (feedback, events) are always preserved. "current" is
    # a snapshot of present state (identical to pre-parameter behavior).
    if basis == "entry":
        entry_basis = {
            t: (getattr(civ, t) - _AGE_GRADIENTS[t] * civ.age
                if t in _AGE_GRADIENTS else getattr(civ, t))
            for t in _INHERITED_TRAITS
        }
    else:
        entry_basis = {t: getattr(civ, t) for t in _INHERITED_TRAITS}

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
            eb = entry_basis[t]
            ymask = cmask & ~dead & young
            if ymask.sum() >= 20:
                c_mean = float(eb[ymask].mean())
            elif (~dead & cmask).any():
                c_mean = float(eb[cmask & ~dead].mean())
            else:
                c_mean = float(eb[cmask].mean())
            base = (heritability * eb[parents] + (1 - heritability) * c_mean
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

    # newborn forces: trait formula + the country's genesis residual
    # (survivors' actual forces minus their trait-formula forces), so
    # regional/genesis conditioning is inherited instead of erased.
    # Everyone else's forces are untouched — aging already propagated.
    if n_dead > 0:
        _build_newborn_forces(civ, dead_idx, dead)
    civ.means = civ.forces.mean(axis=0)

    if return_details:
        return {"deaths": n_dead, "dead_ages": dead_ages,
                "dead_countries": dead_countries}
    return {"deaths": n_dead}
