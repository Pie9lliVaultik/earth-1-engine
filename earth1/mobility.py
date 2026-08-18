"""MOBILITY — flights and cars, in only for what they actually change.

The test applied here is the one that survived the argument about
gravity: does the interaction between this thing and a person VARY, and
does that variation reach their life? Both of these pass, but for
narrow, specific reasons — and the narrowness is the point. Neither is
in here as scenery.

FLIGHTS earn their place on two channels and no others:

  DISEASE IMPORT   air travel is how a local outbreak becomes a
                   pandemic. COVID reached every continent by aircraft
                   in weeks, and the countries hit first were the ones
                   with the most connections, not the nearest ones.
                   Flight volume is therefore a real epidemiological
                   coupling and it varies enormously by country wealth.
  CULTURAL MIXING  people who travel meet norms other than their own
                   and carry them home. This is one of the few
                   mechanisms that moves an agent's culture channel
                   toward somewhere else's rather than toward their own
                   neighbours', which matters because every other
                   channel in this model is homophilous and therefore
                   convergent.

CARS earn their place on three:

  ROAD DEATHS      about 1.19 million a year, and the leading cause of
                   death for people aged 5 to 29. That is not a
                   rounding error, it is one of the largest single
                   killers of the young in the world, and it is steeply
                   graded by country income — the same crash is far more
                   survivable in one place than another.
  COMMUTE          time in a car is time not spent with people.
                   Commuting is a direct tax on the social ties that
                   every other part of this model depends on.
  FUEL EXPOSURE    a household with a car is exposed to fuel prices in
                   a way a household without one is not, which turns an
                   energy shock into a household budget shock for some
                   people and not others.

What is NOT modelled: the car as an object, the flight as an itinerary,
traffic as a flow. Those would be scenery. What is modelled is the
consequence that reaches a person.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Force

TIERS = ["HIC", "UMIC", "LMIC", "LIC"]

# flights per person per year, by country income tier
FLIGHTS_PER_CAPITA_YR = {"HIC": 1.60, "UMIC": 0.45, "LMIC": 0.10,
                         "LIC": 0.02}
# share of households with a car
CAR_OWNERSHIP = {"HIC": 0.82, "UMIC": 0.48, "LMIC": 0.18, "LIC": 0.05}
# road deaths per 100k per year — WHO: the gradient is the story, poor
# countries carry triple the rate on a fraction of the vehicles
ROAD_DEATHS_PER_100K = {"HIC": 8.3, "UMIC": 18.0, "LMIC": 24.0,
                        "LIC": 27.0}
# daily minutes commuting, and the share of it spent alone in a car
COMMUTE_MIN = {"HIC": 62, "UMIC": 70, "LMIC": 78, "LIC": 84}

CULTURAL_MIXING = 0.020        # how far a traveller's culture channel moves
FUEL_SHARE_OF_BUDGET = 0.08    # for a car-owning household


@dataclass
class Mobility:
    owns_car: np.ndarray
    flies_per_year: np.ndarray
    commute_minutes: np.ndarray
    travelled: np.ndarray        # lifetime trips abroad
    imported_disease: int = 0
    road_deaths: int = 0


def _tier(civ) -> np.ndarray:
    from earth1.genesis import GENESIS_COUNTRIES
    per = np.array([TIERS.index(c.get("income", "LMIC"))
                    if c.get("income") in TIERS else 2
                    for c in GENESIS_COUNTRIES])
    return per[civ.country]


def birth_mobility(civ, life, seed: int = 0) -> Mobility:
    rng = np.random.default_rng(seed ^ 0x40B1)
    n = civ.n
    t = _tier(civ)
    own_p = np.array([CAR_OWNERSHIP[k] for k in TIERS])[t]
    # a car follows money as much as country
    money = np.clip(life.wage / max(float(np.median(life.wage)), 1e-6), 0, 3)
    owns = rng.random(n) < np.clip(own_p * (0.5 + 0.5 * money), 0, 0.97)
    fly = np.array([FLIGHTS_PER_CAPITA_YR[k] for k in TIERS])[t] * \
        np.clip(money, 0, 4) * (1.0 + 0.6 * civ.urban)
    com = np.array([COMMUTE_MIN[k] for k in TIERS])[t] * \
        np.where(civ.urban, 1.25, 0.7) * rng.uniform(0.4, 1.6, n)
    return Mobility(owns_car=owns, flies_per_year=fly,
                    commute_minutes=com,
                    travelled=np.zeros(n, dtype=np.int32))


def mobility_tick(civ, life, mob: Mobility, health, fl, rng,
                  dt_days: float = 1.0, alive=None,
                  fuel_price: float = 1.0) -> dict:
    """One day of moving around, and what it costs."""
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)
    dt_yr = dt_days / 365.0
    t = _tier(civ)

    # ── ROAD DEATHS ──────────────────────────────────────────────────
    # the leading killer of the young, so the age profile is the point:
    # peak risk in the late teens and twenties, not in old age
    age_years = 18.0 + civ.age * 72.0
    young_risk = 1.0 + 1.8 * np.exp(-((age_years - 24.0) / 12.0) ** 2)
    base = np.array([ROAD_DEATHS_PER_100K[k] for k in TIERS])[t] / 1e5
    exposure = np.where(mob.owns_car, 1.0, 0.45)      # pedestrians die too
    drink = 1.0 + 1.5 * (life.addiction if life.addiction is not None else 0)
    p = base * young_risk * exposure * drink * dt_yr
    killed = live & (rng.random(n) < p)
    if killed.any():
        health.alive[killed] = False
        health.cause_of_death[killed] = 8            # the road
        mob.road_deaths += int(killed.sum())
        # a road death is a social event like any other death
        touched = np.asarray(civ.adj @ killed.astype(np.float64)).ravel() > 0
        touched &= health.alive
        if life.social_need is not None and touched.any():
            life.social_need[touched] = np.clip(
                life.social_need[touched] + 0.12, 0, 1)
            life.mental[touched] = np.clip(life.mental[touched] - 0.06, 0, 1)

    # ── COMMUTE: a direct tax on the ties everything else needs ──────
    lost_hours = mob.commute_minutes / 60.0
    if life.relationship is not None:
        life.relationship = np.clip(
            life.relationship - 0.0008 * lost_hours * dt_days, 0, 1)
    if fl is not None:
        fl.belonging = np.clip(
            fl.belonging - 0.0006 * lost_hours * dt_days, 0, 1)

    # ── FUEL: an energy shock is a budget shock, for some people ─────
    if abs(fuel_price - 1.0) > 1e-9:
        extra = FUEL_SHARE_OF_BUDGET * (fuel_price - 1.0)
        life.cost = np.where(mob.owns_car, life.cost * (1.0 + extra),
                             life.cost)

    # ── FLIGHTS: who leaves the country today ────────────────────────
    p_fly = np.clip(mob.flies_per_year * dt_yr, 0, 1)
    flying = live & (rng.random(n) < p_fly)
    n_fly = int(flying.sum())
    imported = 0
    if n_fly:
        mob.travelled[flying] += 1

        # CULTURAL MIXING — the only channel in this model that moves an
        # agent toward somewhere ELSE's culture rather than their own
        # neighbours'. Every other channel is homophilous and therefore
        # convergent; this one is the sole source of genuine mixing.
        idx = np.flatnonzero(flying)
        dest = rng.integers(0, n, idx.size)
        civ.forces[idx, Force.CULTURE] = np.clip(
            civ.forces[idx, Force.CULTURE]
            + CULTURAL_MIXING * (civ.forces[dest, Force.CULTURE]
                                 - civ.forces[idx, Force.CULTURE]), 0, 1)
        civ.forces[idx, Force.EXPERIENCE] = np.clip(
            civ.forces[idx, Force.EXPERIENCE] + 0.01, 0, 1)

        # DISEASE IMPORT — how a local outbreak becomes a pandemic. A
        # traveller from a place with active infection carries it home,
        # which is why the countries hit first are the most CONNECTED
        # ones rather than the nearest ones.
        sick_there = health.condition[dest] == 3         # infection
        catches = idx[sick_there & (rng.random(idx.size) < 0.10)]
        catches = catches[health.condition[catches] == 0]
        if catches.size:
            health.condition[catches] = 3
            health.diagnosed_day[catches] = -1.0
            imported = int(catches.size)
            mob.imported_disease += imported

    return {"road_deaths_today": int(killed.sum()),
            "road_deaths_total": mob.road_deaths,
            "flew_today": n_fly,
            "disease_imported_today": imported,
            "disease_imported_total": mob.imported_disease,
            "car_ownership": float(mob.owns_car[live].mean()),
            "mean_commute_min": round(float(mob.commute_minutes[live].mean()), 1)}
