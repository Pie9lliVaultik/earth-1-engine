"""Living Dynamics — population evolution over time (G5).

Each year-step:
  1. Death    — age-dependent mortality, country life expectancy
  2. Birth    — dead slots refilled with inherited-but-drifted newborns
  3. Aging    — all agents age by one year
  4. Migration — net flows between countries
  5. Drift    — secular trends (urbanization, education, secularization)
  6. Recompute — forces, means, alpha, graph from updated traits

Population size stays constant (N fixed).  Deaths create slots,
births fill them.  Fully vectorized — no Python per-agent loops.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from scipy import sparse

from earth1.types import Civilization, Force, NUM_FORCES
from earth1.population import (
    COUNTRIES, AGE_BUCKETS, AGE_LABELS, INCOME_ECON,
    _build_graph, generate_population,
)
from earth1.rng import make_rng


COUNTRY_DEMOGRAPHICS = [
    {"birth_rate": 11, "death_rate": 10, "life_exp": 77, "net_mig": 3},   # US
    {"birth_rate": 10, "death_rate": 10, "life_exp": 81, "net_mig": 3},   # GB
    {"birth_rate":  9, "death_rate": 12, "life_exp": 81, "net_mig": 5},   # DE
    {"birth_rate": 13, "death_rate":  7, "life_exp": 76, "net_mig": 0},   # BR
    {"birth_rate": 35, "death_rate": 11, "life_exp": 55, "net_mig": -1},  # NG
    {"birth_rate": 17, "death_rate":  7, "life_exp": 70, "net_mig": -1},  # IN
    {"birth_rate":  7, "death_rate": 11, "life_exp": 85, "net_mig": 1},   # JP
    {"birth_rate": 16, "death_rate":  6, "life_exp": 75, "net_mig": -2},  # MX
    {"birth_rate": 10, "death_rate": 10, "life_exp": 83, "net_mig": 1},   # FR
]

SECULAR_DRIFT = {
    "urbanization": 0.003,
    "education": 0.004,
    "openness": 0.002,
    "secularization": 0.002,
}

TRAIT_INHERIT_NOISE = 0.06


@dataclass
class EvolveStats:
    year: int
    deaths: int
    births: int
    migrants: int
    pop_by_country: Dict[str, int]
    mean_age: float
    mean_openness: float
    mean_education: float
    urbanization_rate: float


def _death_probability(age: np.ndarray, country: np.ndarray) -> np.ndarray:
    life_exp = np.array([d["life_exp"] for d in COUNTRY_DEMOGRAPHICS])
    le = life_exp[country]
    age_years = age * 100.0
    # Gompertz-style: low mortality young, steep past life expectancy
    x = (age_years - le) / (le * 0.15)
    base_rate = np.array([d["death_rate"] for d in COUNTRY_DEMOGRAPHICS])[country] / 1000.0
    p = base_rate * np.exp(np.clip(x, -5, 5))
    return np.clip(p, 0.001, 0.95)


def _select_deaths(civ: Civilization, rng: np.random.Generator) -> np.ndarray:
    p_death = _death_probability(civ.age, civ.country)
    return rng.random(civ.n) < p_death


def _birth_replacement(
    civ: Civilization,
    dead_mask: np.ndarray,
    rng: np.random.Generator,
) -> None:
    dead_idx = np.where(dead_mask)[0]
    n_dead = len(dead_idx)
    if n_dead == 0:
        return

    dead_countries = civ.country[dead_idx]

    parent_idx = np.empty(n_dead, dtype=np.int64)
    for ci in range(len(COUNTRIES)):
        births_in_ci = dead_countries == ci
        n_births = int(births_in_ci.sum())
        if n_births == 0:
            continue
        alive_in_ci = np.where((civ.country == ci) & ~dead_mask)[0]
        if len(alive_in_ci) == 0:
            alive_in_ci = np.where(civ.country == ci)[0]
        parents = rng.choice(alive_in_ci, size=n_births, replace=True)
        parent_idx[births_in_ci] = parents

    noise = TRAIT_INHERIT_NOISE

    civ.openness[dead_idx] = np.clip(
        civ.openness[parent_idx] + rng.normal(0, noise, n_dead), 0, 1)
    civ.risk_appetite[dead_idx] = np.clip(
        civ.risk_appetite[parent_idx] + rng.normal(0, noise, n_dead), 0, 1)
    civ.doubt[dead_idx] = np.clip(
        civ.doubt[parent_idx] + rng.normal(0, noise, n_dead), 0, 1)
    civ.empathy[dead_idx] = np.clip(
        civ.empathy[parent_idx] + rng.normal(0, noise, n_dead), 0, 1)
    civ.desire_intensity[dead_idx] = np.clip(
        rng.normal(0.65, 0.17, n_dead), 0, 1)

    civ.country[dead_idx] = dead_countries
    civ.region[dead_idx] = rng.integers(0, 4, size=n_dead)

    civ.age[dead_idx] = 0.14
    civ.age_bucket[dead_idx] = 0

    c_edu_hi = np.array([c["edu_hi"] for c in COUNTRIES])[dead_countries]
    parent_edu = civ.education[parent_idx]
    edu_boost = np.clip(c_edu_hi + 0.02, 0, 1)
    r_edu = rng.random(n_dead)
    civ.education[dead_idx] = np.where(
        r_edu < edu_boost, np.minimum(parent_edu + 1, 2),
        parent_edu,
    ).astype(np.int32)

    parent_income = civ.income[parent_idx]
    r_inc = rng.random(n_dead)
    civ.income[dead_idx] = np.where(
        r_inc < 0.3, np.clip(parent_income + rng.choice([-1, 0, 1], size=n_dead), 0, 2),
        parent_income,
    ).astype(np.int32)

    c_urban = np.array([c["urban"] for c in COUNTRIES])[dead_countries]
    civ.urban[dead_idx] = rng.random(n_dead) < np.clip(c_urban + 0.02, 0, 1)

    civ.economic_field[dead_idx] = np.clip(
        rng.normal(INCOME_ECON[civ.income[dead_idx]], 0.1), 0, 1)
    civ.culture_offset[dead_idx] = np.array(
        [COUNTRIES[ci]["cult"] for ci in dead_countries])


def _age_step(civ: Civilization) -> None:
    civ.age = np.clip(civ.age + 0.012, 0, 1)
    bucket_mids = np.array([a["mid"] for a in AGE_BUCKETS])
    dists = np.abs(civ.age[:, np.newaxis] - bucket_mids[np.newaxis, :])
    civ.age_bucket = np.argmin(dists, axis=1).astype(np.int32)


def _migrate(
    civ: Civilization,
    rng: np.random.Generator,
    scale: float = 1.0,
) -> int:
    net_mig = np.array([d["net_mig"] for d in COUNTRY_DEMOGRAPHICS])
    receivers = np.where(net_mig > 0)[0]
    senders = np.where(net_mig < 0)[0]

    if len(receivers) == 0 or len(senders) == 0:
        return 0

    total_moved = 0
    sender_pool = np.where(np.isin(civ.country, senders))[0]
    if len(sender_pool) == 0:
        return 0

    for ci in receivers:
        n_to_receive = max(1, int(abs(net_mig[ci]) / 1000.0 * np.sum(civ.country == ci) * scale))
        if n_to_receive == 0:
            continue
        n_to_receive = min(n_to_receive, len(sender_pool))
        chosen = rng.choice(sender_pool, size=n_to_receive, replace=False)

        civ.country[chosen] = ci
        c_data = COUNTRIES[ci]
        dest_cult = c_data["cult"]
        civ.culture_offset[chosen] = (
            0.7 * civ.culture_offset[chosen] + 0.3 * dest_cult
        )
        civ.region[chosen] = rng.integers(0, len(
            [r for r in ["a", "b", "c", "d"]]), size=n_to_receive)

        total_moved += n_to_receive
        remaining = np.isin(sender_pool, chosen, invert=True)
        sender_pool = sender_pool[remaining]

    return total_moved


def _secular_drift(civ: Civilization, rng: np.random.Generator) -> None:
    d = SECULAR_DRIFT
    n = civ.n

    urban_shift = rng.random(n) < d["urbanization"]
    civ.urban = civ.urban | urban_shift

    edu_shift = rng.random(n) < d["education"]
    young_mask = civ.age < 0.4
    civ.education = np.where(
        edu_shift & young_mask & (civ.education < 2),
        civ.education + 1, civ.education,
    ).astype(np.int32)

    civ.openness = np.clip(civ.openness + rng.normal(d["openness"], 0.002, n), 0, 1)

    civ.culture_offset = np.clip(
        civ.culture_offset - rng.normal(d["secularization"], 0.001, n) * 0.1,
        -0.5, 0.5,
    )


def _recompute_forces(civ: Civilization) -> None:
    edu_lift = np.where(civ.education == 2, 0.08,
               np.where(civ.education == 0, -0.06, 0.0))

    civ.forces[:, Force.FEAR] = np.clip(
        (civ.doubt + (1.0 - civ.risk_appetite)) / 2.0, 0, 1)
    civ.forces[:, Force.DESIRE] = civ.desire_intensity
    civ.forces[:, Force.ECONOMICS] = civ.economic_field
    civ.forces[:, Force.COLLECTIVE] = np.clip(1.0 - civ.openness, 0, 1)
    civ.forces[:, Force.IDENTITY] = civ.openness
    civ.forces[:, Force.CULTURE] = np.clip(0.5 + civ.culture_offset, 0, 1)
    civ.forces[:, Force.EXPERIENCE] = civ.age
    civ.forces[:, Force.TEMPERAMENT] = civ.risk_appetite

    civ.alpha = np.clip(0.28 + 0.5 * civ.openness - 0.12 * (1.0 - civ.openness), 0, 1)
    civ.means = civ.forces.mean(axis=0)


def evolve_step(
    civ: Civilization,
    rng: np.random.Generator,
    year: int = 0,
    rebuild_graph: bool = True,
) -> EvolveStats:
    dead_mask = _select_deaths(civ, rng)
    n_deaths = int(dead_mask.sum())

    _birth_replacement(civ, dead_mask, rng)
    _age_step(civ)

    n_migrants = _migrate(civ, rng)
    _secular_drift(civ, rng)
    _recompute_forces(civ)

    if rebuild_graph:
        civ.adj = _build_graph(
            civ.n, civ.openness, civ.forces, civ.culture_offset,
            civ.seed + year + 1000,
        )

    counts = np.bincount(civ.country, minlength=len(COUNTRIES))
    pop_by_country = {
        COUNTRIES[i]["code"]: int(counts[i]) for i in range(len(COUNTRIES))
    }

    return EvolveStats(
        year=year,
        deaths=n_deaths,
        births=n_deaths,
        migrants=n_migrants,
        pop_by_country=pop_by_country,
        mean_age=round(float(civ.age.mean()), 4),
        mean_openness=round(float(civ.openness.mean()), 4),
        mean_education=round(float(civ.education.mean()), 4),
        urbanization_rate=round(float(civ.urban.mean()), 4),
    )


def evolve(
    civ: Civilization,
    years: int = 1,
    seed: Optional[int] = None,
    rebuild_graph: bool = True,
) -> tuple:
    civ = _deep_copy_civ(civ)
    rng = make_rng(seed if seed is not None else civ.seed + 9999)

    stats = []
    for y in range(years):
        s = evolve_step(civ, rng, year=y + 1, rebuild_graph=rebuild_graph)
        stats.append(s)

    return civ, stats


def _deep_copy_civ(civ: Civilization) -> Civilization:
    return Civilization(
        n=civ.n, seed=civ.seed,
        country=civ.country.copy(),
        region=civ.region.copy(),
        age_bucket=civ.age_bucket.copy(),
        age=civ.age.copy(),
        education=civ.education.copy(),
        income=civ.income.copy(),
        urban=civ.urban.copy(),
        openness=civ.openness.copy(),
        empathy=civ.empathy.copy(),
        risk_appetite=civ.risk_appetite.copy(),
        doubt=civ.doubt.copy(),
        desire_intensity=civ.desire_intensity.copy(),
        economic_field=civ.economic_field.copy(),
        culture_offset=civ.culture_offset.copy(),
        forces=civ.forces.copy(),
        alpha=civ.alpha.copy(),
        means=civ.means.copy(),
        adj=civ.adj.copy(),
    )


def project_opinion_drift(
    civ: Civilization,
    question_id: str,
    years: int = 10,
    seed: Optional[int] = None,
) -> List[Dict]:
    from earth1.engine import run_question
    from earth1.questions import question_by_id

    q = question_by_id(question_id)
    if q is None:
        raise ValueError(f"Unknown question: {question_id}")

    civ_copy = _deep_copy_civ(civ)
    rng = make_rng(seed if seed is not None else civ.seed + 9999)

    result_0 = run_question(q, civ_copy)
    trajectory = [{
        "year": 0,
        "yes_pct": round(result_0.yes_pct, 4),
        "dominant": result_0.dominant.name.lower(),
        "conviction": round(result_0.conviction, 4),
        "fragility": round(result_0.fragility, 4),
    }]

    for y in range(1, years + 1):
        evolve_step(civ_copy, rng, year=y, rebuild_graph=(y % 3 == 0))
        r = run_question(q, civ_copy)
        trajectory.append({
            "year": y,
            "yes_pct": round(r.yes_pct, 4),
            "dominant": r.dominant.name.lower(),
            "conviction": round(r.conviction, 4),
            "fragility": round(r.fragility, 4),
        })

    return trajectory
