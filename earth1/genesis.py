"""Flagship population genesis — 194 countries, regional identity, Grounding Stack.

Replaces generate_population() with a richer pipeline:
  Layer 1: Demographic skeleton from census_country_targets (194 countries)
  Layer 2: Cultural dimensions from force_norms + within-country distributions
  Layer 3: Regional identity with historical force deltas
  Layer 4: Soul scalars (15 traits conditioned on demo + culture + region)
  Layer 5: 8-force computation with regional culture delta

Output is the same Civilization dataclass — all downstream code works unchanged."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from earth1.types import Civilization, Force, NUM_FORCES
from earth1.census import (
    CENSUS_TARGETS, effective_force_norms, get_within_country,
)
from earth1.regions import get_regions, sample_region
from earth1.rng import make_rng


GENESIS_COUNTRIES = CENSUS_TARGETS
GENESIS_COUNTRY_CODES = [c["iso2"] for c in GENESIS_COUNTRIES]
GENESIS_COUNTRY_NAMES = {c["iso2"]: c["name"] for c in GENESIS_COUNTRIES}

INCOME_ECON = np.array([0.32, 0.55, 0.80])

_INCOME_CLASS_EDU = {"HIC": 0.42, "UMIC": 0.28, "LMIC": 0.18, "LIC": 0.10}
_INCOME_CLASS_OPEN = {"HIC": 0.56, "UMIC": 0.48, "LMIC": 0.44, "LIC": 0.42}
_INCOME_CLASS_RISK = {"HIC": 0.50, "UMIC": 0.52, "LMIC": 0.54, "LIC": 0.56}
_INCOME_CLASS_DOUBT = {"HIC": 0.46, "UMIC": 0.52, "LMIC": 0.58, "LIC": 0.62}


def _allocate_countries(total: int, min_per_country: int = 500) -> np.ndarray:
    """Allocate agent counts across 194 countries with minimum floor."""
    nc = len(GENESIS_COUNTRIES)
    shares = np.array([c["pop"] for c in GENESIS_COUNTRIES])

    raw = np.maximum(min_per_country, np.round(total * shares).astype(int))
    scale = total / raw.sum()
    counts = np.round(raw * scale).astype(int)

    diff = total - counts.sum()
    if diff != 0:
        largest = np.argsort(shares)[::-1]
        for i in range(abs(diff)):
            counts[largest[i % nc]] += 1 if diff > 0 else -1

    return counts


def genesis(pop: int = 1_000_000, seed: int = 42,
            min_per_country: int = 500) -> Civilization:
    """Generate a civilization with 194 countries, regional identity, and enriched traits."""
    rng = make_rng(seed)
    nc = len(GENESIS_COUNTRIES)

    # ── Layer 1: Demographic skeleton ──

    counts = _allocate_countries(pop, min_per_country)
    country = np.repeat(np.arange(nc), counts)
    actual_pop = len(country)

    norms_per_country = []
    for c in GENESIS_COUNTRIES:
        norms_per_country.append(effective_force_norms(c["iso2"]))

    c_urban_rate = np.array([c["urban"] / 100.0 for c in GENESIS_COUNTRIES])[country]
    c_male_rate = np.array([c["male"] / 100.0 for c in GENESIS_COUNTRIES])[country]
    c_med_age = np.array([c["med_age"] for c in GENESIS_COUNTRIES])[country]
    c_income_class = np.array([c["income"] for c in GENESIS_COUNTRIES])

    edu_hi = np.array([_INCOME_CLASS_EDU.get(c["income"], 0.25)
                       for c in GENESIS_COUNTRIES])[country]

    # Age: normal around country median, normalized to [0,1] where 0=18, 1=90
    age_raw = np.clip(rng.normal(c_med_age, 12.0), 18, 90)
    age = (age_raw - 18.0) / 72.0

    age_bucket = np.digitize(age_raw, [30, 45, 60, 75])

    # Urban/rural
    urban = rng.random(actual_pop) < c_urban_rate

    # Income (conditioned on country income class)
    c_ic_idx = np.array([{"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}.get(
        c["income"], 2) for c in GENESIS_COUNTRIES])[country]
    r_inc = rng.random(actual_pop)
    low_thresh = np.clip(0.34 - edu_hi * 0.2, 0, 1)
    high_bias = 0.2 + edu_hi * 0.5
    mid_thresh = low_thresh + np.clip(0.66 - high_bias, 0, 1)
    income = np.where(r_inc < low_thresh, 0,
             np.where(r_inc < mid_thresh, 1, 2)).astype(np.int32)

    # Education (conditioned on income + national rate)
    base_edu = edu_hi + np.where(income == 2, 0.28,
                         np.where(income == 1, 0.08, -0.14))
    r_edu = rng.random(actual_pop)
    hi_thresh = np.clip(base_edu, 0, 1)
    education = np.where(r_edu < hi_thresh, 2,
                np.where(r_edu < hi_thresh + 0.4, 1, 0)).astype(np.int32)

    # ── Layer 3: Regional identity ──

    region_idx = np.empty(actual_pop, dtype=np.int32)
    region_culture_delta = np.zeros(actual_pop, dtype=np.float64)
    region_force_deltas = np.zeros((actual_pop, NUM_FORCES), dtype=np.float64)

    force_name_to_idx = {
        "fear": Force.FEAR, "desire": Force.DESIRE,
        "economics": Force.ECONOMICS, "collective": Force.COLLECTIVE,
        "identity": Force.IDENTITY, "culture": Force.CULTURE,
        "experience": Force.EXPERIENCE, "temperament": Force.TEMPERAMENT,
    }

    offset = 0
    for ci in range(nc):
        n_agents = counts[ci]
        if n_agents == 0:
            continue
        iso2 = GENESIS_COUNTRIES[ci]["iso2"]
        regions = get_regions(iso2)

        if len(regions) == 1:
            region_idx[offset:offset + n_agents] = 0
            for fname, delta in regions[0].force_deltas.items():
                fidx = force_name_to_idx.get(fname)
                if fidx is not None:
                    region_force_deltas[offset:offset + n_agents, fidx] = delta
            if "culture" in regions[0].force_deltas:
                region_culture_delta[offset:offset + n_agents] = regions[0].force_deltas["culture"]
        else:
            shares = np.array([r.population_share for r in regions])
            shares /= shares.sum()
            ridx = rng.choice(len(regions), size=n_agents, p=shares)
            region_idx[offset:offset + n_agents] = ridx
            for ri, reg in enumerate(regions):
                mask = ridx == ri
                for fname, delta in reg.force_deltas.items():
                    fidx = force_name_to_idx.get(fname)
                    if fidx is not None:
                        region_force_deltas[offset:offset + n_agents][mask, fidx] = delta
                if "culture" in reg.force_deltas:
                    region_culture_delta[offset:offset + n_agents][mask] = reg.force_deltas["culture"]

        offset += n_agents

    # ── Layer 2: Cultural dimensions (Hofstede per agent) ──

    h_pdi = np.array([n["pdi"] / 100.0 for n in norms_per_country])[country]
    h_idv = np.array([n["idv"] / 100.0 for n in norms_per_country])[country]
    h_mas = np.array([n["mas"] / 100.0 for n in norms_per_country])[country]
    h_uai = np.array([n["uai"] / 100.0 for n in norms_per_country])[country]
    h_lto = np.array([n["lto"] / 100.0 for n in norms_per_country])[country]
    h_ind = np.array([n["ind"] / 100.0 for n in norms_per_country])[country]

    power_distance = np.clip(rng.normal(h_pdi, 0.12), 0, 1)
    individualism = np.clip(rng.normal(h_idv, 0.12), 0, 1)
    uncertainty_avoidance = np.clip(rng.normal(h_uai, 0.12), 0, 1)
    long_term_orientation = np.clip(rng.normal(h_lto, 0.12), 0, 1)

    # Culture offset: derived from Hofstede IND (indulgence) centered at 0.5
    culture_offset = (h_ind - 0.5) * 0.4 + region_culture_delta

    # ── Layer 4: Soul scalars ──

    c_open = np.array([_INCOME_CLASS_OPEN.get(c["income"], 0.48)
                        for c in GENESIS_COUNTRIES])[country]
    c_risk = np.array([_INCOME_CLASS_RISK.get(c["income"], 0.52)
                        for c in GENESIS_COUNTRIES])[country]
    c_doubt = np.array([_INCOME_CLASS_DOUBT.get(c["income"], 0.54)
                         for c in GENESIS_COUNTRIES])[country]

    # Modulate base rates by Hofstede dimensions
    c_open = c_open + (h_idv - 0.5) * 0.15
    c_risk = c_risk + (h_ind - 0.5) * 0.1
    c_doubt = c_doubt + (h_uai - 0.5) * 0.15

    edu_lift = np.where(education == 2, 0.08, np.where(education == 0, -0.06, 0.0))

    openness = np.clip(rng.normal(c_open + edu_lift - age * 0.08, 0.16), 0, 1)
    risk_appetite = np.clip(rng.normal(c_risk - age * 0.12, 0.17), 0, 1)
    doubt = np.clip(rng.normal(c_doubt - edu_lift * 0.5, 0.16), 0, 1)
    empathy = np.clip(rng.normal(0.55, 0.16, size=actual_pop), 0, 1)
    desire_intensity = np.clip(rng.normal(0.5 + (0.6 - age) * 0.3, 0.17), 0, 1)
    economic_field = np.clip(rng.normal(INCOME_ECON[income], 0.1), 0, 1)

    conscientiousness = np.clip(rng.normal(0.52 + age * 0.1 + edu_lift * 0.3, 0.15), 0, 1)
    agreeableness = np.clip(rng.normal(0.54 + age * 0.05, 0.15, size=actual_pop), 0, 1)
    extraversion = np.clip(rng.normal(0.50 - age * 0.06, 0.16, size=actual_pop), 0, 1)
    neuroticism = np.clip(rng.normal(0.48 - age * 0.04 - edu_lift * 0.2, 0.16), 0, 1)

    # ── Layer 5: Force computation ──

    forces = np.empty((actual_pop, NUM_FORCES), dtype=np.float64)

    forces[:, Force.FEAR] = np.clip(
        (doubt + (1.0 - risk_appetite) + neuroticism * 0.3) / 2.3
        + region_force_deltas[:, Force.FEAR], 0, 1)

    forces[:, Force.DESIRE] = np.clip(
        desire_intensity + region_force_deltas[:, Force.DESIRE], 0, 1)

    forces[:, Force.ECONOMICS] = np.clip(
        economic_field + region_force_deltas[:, Force.ECONOMICS], 0, 1)

    forces[:, Force.COLLECTIVE] = np.clip(
        (1.0 - openness) * 0.6 + power_distance * 0.4
        + region_force_deltas[:, Force.COLLECTIVE], 0, 1)

    forces[:, Force.IDENTITY] = np.clip(
        openness * 0.5 + individualism * 0.5
        + region_force_deltas[:, Force.IDENTITY], 0, 1)

    forces[:, Force.CULTURE] = np.clip(
        0.5 + culture_offset + long_term_orientation * 0.1
        + region_force_deltas[:, Force.CULTURE], 0, 1)

    forces[:, Force.EXPERIENCE] = age

    forces[:, Force.TEMPERAMENT] = np.clip(
        risk_appetite * 0.7 + extraversion * 0.3
        + region_force_deltas[:, Force.TEMPERAMENT], 0, 1)

    # Conviction
    alpha = np.clip(0.28 + 0.5 * openness - 0.12 * (1.0 - openness), 0, 1)

    # Population means
    means = forces.mean(axis=0)

    # Social graph (enhanced homophily)
    adj = _build_graph(actual_pop, openness, forces, culture_offset,
                       region_idx, country, seed + 1)

    return Civilization(
        n=actual_pop, seed=seed,
        country=country, region=region_idx, age_bucket=age_bucket, age=age,
        education=education, income=income, urban=urban,
        openness=openness, empathy=empathy, risk_appetite=risk_appetite,
        doubt=doubt, desire_intensity=desire_intensity,
        economic_field=economic_field, culture_offset=culture_offset,
        conscientiousness=conscientiousness, agreeableness=agreeableness,
        extraversion=extraversion, neuroticism=neuroticism,
        power_distance=power_distance, individualism=individualism,
        uncertainty_avoidance=uncertainty_avoidance,
        long_term_orientation=long_term_orientation,
        forces=forces, alpha=alpha, means=means, adj=adj,
    )


def _build_graph(
    n: int,
    openness: np.ndarray,
    forces: np.ndarray,
    culture_offset: np.ndarray,
    region_idx: np.ndarray,
    country: np.ndarray,
    seed: int,
    k: int = 8,
    long_links: int = 2,
) -> sparse.csr_matrix:
    """Enhanced homophily graph with region and age dimensions."""
    rng = make_rng(seed)

    region_norm = region_idx.astype(np.float64)
    if region_norm.max() > 0:
        region_norm = region_norm / region_norm.max()

    country_norm = country.astype(np.float64)
    if country_norm.max() > 0:
        country_norm = country_norm / country_norm.max()

    pos = (0.25 * openness
         + 0.15 * forces[:, Force.ECONOMICS]
         + 0.10 * (1.0 - forces[:, Force.FEAR])
         + 0.15 * (0.5 + culture_offset)
         + 0.10 * country_norm
         + 0.10 * region_norm
         + 0.15 * forces[:, Force.EXPERIENCE])

    order = np.argsort(pos)
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)

    half = max(1, k // 2)
    rows = []
    cols = []
    for d in range(1, half + 1):
        valid_fwd = rank + d < n
        src_fwd = np.where(valid_fwd)[0]
        dst_fwd = order[rank[src_fwd] + d]
        rows.append(src_fwd)
        cols.append(dst_fwd)

        valid_bwd = rank - d >= 0
        src_bwd = np.where(valid_bwd)[0]
        dst_bwd = order[rank[src_bwd] - d]
        rows.append(src_bwd)
        cols.append(dst_bwd)

    for _ in range(long_links):
        src_all = np.arange(n)
        dst_all = rng.integers(0, n, size=n)
        mask = dst_all != src_all
        rows.append(src_all[mask])
        cols.append(dst_all[mask])

    row = np.concatenate(rows)
    col = np.concatenate(cols)
    data = np.ones(len(row), dtype=np.float32)
    adj = sparse.csr_matrix((data, (row, col)), shape=(n, n))
    return adj


def genesis_country_name(code_idx: int) -> str:
    return GENESIS_COUNTRIES[code_idx]["name"]


def genesis_country_code(code_idx: int) -> str:
    return GENESIS_COUNTRIES[code_idx]["iso2"]
