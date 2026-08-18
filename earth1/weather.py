"""WEATHER — heat, cold, drought, storm. The sky as a correlated shock.

Weather earns its place for one reason: it is the purest example of the
mechanism that made this world come alive. A heat wave does not pick
people at random. It lands on a PLACE, and everyone in that place gets
it in the same week — the neighbours, the household, the whole town.
That is the same correlated-shock structure as a firm failing, and it
is why weather belongs in a model of opinion while quarks do not.

What it does to a person, concretely:

  HEAT      kills. Excess mortality rises steeply above a local
            comfort threshold, and it kills the old, the ill and the
            poor first because they cannot leave and cannot cool down.
            It also makes people irritable and violent — one of the
            most reproducible findings in the literature on temperature
            and aggression.
  COLD      kills more people than heat, worldwide, and quietly. It
            raises heating costs, which is a straight transfer out of
            the survival buffer of whoever has least of it.
  DROUGHT   starves. Where agriculture is a large share of employment,
            a failed harvest is a mass income shock arriving through
            occupation rather than through firms.
  STORM     destroys. Property, firms, and the ability to work, in a
            band across a region in a day.

Climate is per country from latitude and region; anomalies are
generated as a slow spatial field so neighbouring countries share
weather, because they do.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Force

# excess mortality per degree beyond the local comfort band, per day
# Calibrated to real excess mortality, which is ~5M/yr worldwide from
# heat and cold combined — about 0.06% of humanity per year. The first
# values were 300x that and killed 46% of the population annually. A
# heat wave is a mass-casualty event among the FRAIL, not among
# everyone: the frailty multiplier is doing the work, not the base rate.
HEAT_MORTALITY = 5.0e-7
COLD_MORTALITY = 8.0e-7         # cold kills more, worldwide
# aggression rises with heat — among the most replicated findings there is
HEAT_AGGRESSION = 0.020
DROUGHT_HARVEST_LOSS = 0.55     # share of farm income lost in a bad year
STORM_RATE_YR = 0.9             # storms per country-year, tropics weighted


@dataclass
class Climate:
    baseline_temp: np.ndarray    # per country, degrees C annual mean
    comfort: np.ndarray          # per country, the temperature people
                                 # are adapted to — adaptation is why
                                 # 30C is deadly in Oslo and ordinary
                                 # in Lagos
    tropical: np.ndarray         # storm exposure 0..1
    farm_share: np.ndarray       # share of work that is agriculture
    anomaly: np.ndarray          # current temperature anomaly
    soil: np.ndarray             # water in the ground, 0..1
    storm_days: np.ndarray


def birth_climate(seed: int = 0) -> Climate:
    from earth1.genesis import GENESIS_COUNTRIES
    rng = np.random.default_rng(seed ^ 0x5C1)
    nc = len(GENESIS_COUNTRIES)
    region = [str(c.get("region", "")) for c in GENESIS_COUNTRIES]
    # crude latitude proxy from region name, which is what we have
    warm = np.array([
        1.0 if any(k in r for k in ("Africa", "South Asia", "Middle East",
                                    "Latin America", "Caribbean",
                                    "Southeast Asia", "Oceania"))
        else 0.35 if any(k in r for k in ("East Asia", "Central Asia",
                                          "Southern Europe"))
        else 0.0 for r in region])
    base = 6.0 + 22.0 * warm + rng.normal(0, 2.0, nc)
    tier = np.array([{"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}
                     .get(c.get("income", "LMIC"), 2)
                     for c in GENESIS_COUNTRIES])
    return Climate(
        baseline_temp=base,
        comfort=base,                        # people are adapted to home
        tropical=np.clip(warm + rng.normal(0, 0.15, nc), 0, 1),
        farm_share=np.clip(0.03 + 0.16 * tier + rng.normal(0, 0.04, nc),
                           0.01, 0.62),
        anomaly=np.zeros(nc),
        soil=np.full(nc, 0.6),
        storm_days=np.zeros(nc))


def weather_tick(civ, life, health, cl: Climate, rng, dt_days: float = 1.0,
                 alive=None) -> dict:
    """One day of sky, and what it does to the people underneath it."""
    from earth1.genesis import GENESIS_COUNTRIES
    from earth1.life import OCC_NAMES
    nc = len(GENESIS_COUNTRIES)
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)

    # ── the sky: a slow field, shared between neighbours ─────────────
    # anomalies persist and drift rather than being redrawn daily, which
    # is what makes a heat WAVE a wave instead of a coin flip
    # A heat WAVE has to actually be a wave. The first version produced
    # anomalies with a standard deviation near 3.7C against a threshold
    # of +6C, so nothing ever got hot enough to kill anyone. Real heat
    # waves run 5-12C above local normal and persist for days, which is
    # what the slower decay and larger shock produce here.
    shock = rng.normal(0, 1.0, nc)
    cl.anomaly = cl.anomaly * (0.94 ** dt_days) + 3.2 * shock * dt_days ** 0.5
    temp = cl.baseline_temp + cl.anomaly

    # ── soil water: rain in, evaporation out, heat dries it faster ───
    # Rain has to outpace evaporation on average or every country
    # slides into permanent drought — the first version left half the
    # planet parched forever, which is a broken water cycle, not a
    # climate.
    rain = rng.random(nc) < (0.45 + 0.20 * cl.tropical)
    cl.soil = np.clip(cl.soil + 0.06 * rain * dt_days
                      - (0.012 + 0.004 * np.maximum(cl.anomaly, 0))
                      * dt_days, 0.0, 1.0)
    drought = cl.soil < 0.22

    # ── storms ───────────────────────────────────────────────────────
    storming = rng.random(nc) < (STORM_RATE_YR * (0.3 + cl.tropical)
                                 * dt_days / 365.0)
    cl.storm_days += storming

    # ── what the sky does to a person ────────────────────────────────
    over = np.maximum(temp - cl.comfort - 4.0, 0.0)[civ.country]
    under = np.maximum(cl.comfort - temp - 5.0, 0.0)[civ.country]

    # the old, the ill and the poor die first, because they cannot leave
    frailty = (1.0 + 2.5 * civ.age
               + 1.5 * (health.condition > 0).astype(float)
               + 1.2 * np.clip(life.deprivation, 0, 1)
               # someone already in decline after a fall is far more
               # fragile to everything that comes after it — which is
               # how a heat wave finds the people a fall left behind
               + 2.0 * (health.declining
                        if getattr(health, "declining", None) is not None
                        else 0.0))
    p_die = (HEAT_MORTALITY * over + COLD_MORTALITY * under) \
        * frailty * dt_days
    died = live & (rng.random(n) < p_die)
    if died.any():
        health.alive[died] = False
        health.cause_of_death[died] = 6          # the weather

    # cold is also a bill: heating comes straight out of the buffer
    life.wealth -= 0.05 * under * dt_days

    # heat makes people angry. this is not a metaphor, it is one of the
    # most reproducible results in the temperature literature.
    hot = over > 0
    if hot.any():
        civ.forces[hot, Force.FEAR] = np.clip(
            civ.forces[hot, Force.FEAR]
            + HEAT_AGGRESSION * over[hot] * 0.01 * dt_days, 0, 1)

    # ── drought starves the farms ────────────────────────────────────
    farm_occ = np.isin(life.occupation,
                       [OCC_NAMES.index("subsistence_agriculture")])
    hit_farm = live & farm_occ & drought[civ.country]
    if hit_farm.any():
        life.wage[hit_farm] *= (1.0 - DROUGHT_HARVEST_LOSS * 0.01 * dt_days)

    # ── storms wreck the firms and the homes ─────────────────────────
    hit_storm = storming[life.firm_country]
    if hit_storm.any():
        life.firm_health[hit_storm] = np.clip(
            life.firm_health[hit_storm] - 0.15, 0, 1)
    in_storm = live & storming[civ.country]
    if in_storm.any():
        life.wealth[in_storm] -= 3.0

    return {"mean_anomaly": float(cl.anomaly.mean()),
            "countries_in_heat": int((over[np.unique(civ.country,
                                                     return_index=True)[1]]
                                      > 0).sum()) if n else 0,
            "countries_in_drought": int(drought.sum()),
            "storms_today": int(storming.sum()),
            "weather_deaths": int(died.sum()),
            "mean_soil": round(float(cl.soil.mean()), 4)}
