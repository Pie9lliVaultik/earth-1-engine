"""Flagship population genesis — 194 countries, regional identity, Grounding Stack.

Replaces generate_population() with a richer pipeline:
  Layer 1: Demographic skeleton from census_country_targets (194 countries)
  Layer 2: Cultural dimensions from force_norms + within-country distributions
  Layer 3: Regional identity with historical force deltas
  Layer 4: Soul scalars (15 traits conditioned on demo + culture + region)
  Layer 5: 8-force computation with regional culture delta

Output is the same Civilization dataclass — all downstream code works unchanged."""

from __future__ import annotations

import os
import numpy as np
from scipy import sparse
from earth1.types import Civilization, Force, NUM_FORCES
from earth1.census import (
    CENSUS_TARGETS, effective_force_norms, get_within_country,
)
from earth1.regions import get_regions, sample_region
from earth1.culture import INGLEHART
from earth1.rng import make_rng


GENESIS_COUNTRIES = CENSUS_TARGETS
GENESIS_COUNTRY_CODES = [c["iso2"] for c in GENESIS_COUNTRIES]
GENESIS_COUNTRY_NAMES = {c["iso2"]: c["name"] for c in GENESIS_COUNTRIES}

INCOME_ECON = np.array([0.32, 0.55, 0.80])

_INCOME_CLASS_EDU = {"HIC": 0.42, "UMIC": 0.28, "LMIC": 0.18, "LIC": 0.10}
_INCOME_CLASS_OPEN = {"HIC": 0.56, "UMIC": 0.48, "LMIC": 0.44, "LIC": 0.42}
_INCOME_CLASS_RISK = {"HIC": 0.50, "UMIC": 0.52, "LMIC": 0.54, "LIC": 0.56}
_INCOME_CLASS_DOUBT = {"HIC": 0.46, "UMIC": 0.52, "LMIC": 0.58, "LIC": 0.62}


def census_weights(civ) -> np.ndarray:
    """Per-agent census weights for population-true global aggregation.

    The genesis floor (min_per_country) guarantees statistical
    representation but distorts population shares — at 100k agents,
    174/194 countries sit AT the floor and India holds 11.2% of agents
    vs 17.9% of humanity. weight_i = census_share(country_i) /
    agent_share(country_i), normalized to mean 1.0, so
    np.average(x, weights=census_weights(civ)) is a population-true
    world read while per-country reads stay unweighted.
    """
    shares = np.array([c["pop"] for c in GENESIS_COUNTRIES])
    shares = shares / shares.sum()
    counts = np.bincount(civ.country, minlength=len(GENESIS_COUNTRIES))
    agent_share = counts / counts.sum()
    ratio = np.divide(shares, agent_share,
                      out=np.zeros_like(shares), where=agent_share > 0)
    w = ratio[civ.country]
    return w / w.mean()


# ── Manifold v2: demographically coherent adult ages ──────────────────
#
# The v1 sampler drew adult ages from normal(all-ages census median, 12),
# which (a) used a median that includes children as the ADULT mean and
# (b) had almost no mass past 65 — the world had no elderly (G5 run #2/#3
# finding: p90 age 51 vs ~68 real; adult CDR 3.6/1000 vs ~10 real).
#
# v2 derives each country's adult age pyramid from first principles:
# stable-population density  f(x) ∝ exp(-r·x) · S(x), where S is the
# country's own Gompertz survival (the same curve the generational tick
# kills with — one mortality physics, one pyramid) and the growth rate r
# is solved so the under-18 share matches the census u18 target. Two
# census inputs, zero free parameters.

_AGE_GRID = np.arange(0.0, 110.0, 0.5)
_ADULT_AGE_CACHE: dict = {}


# global life expectancy has risen ~0.2y per calendar year for six
# decades; an agent aged x lived under lower LE than today's — using
# current LE for every cohort over-populates the elderly (G5 run #4:
# adult CDR 16/1000 vs [6,15] band). Older cohorts get an LE discount,
# capped at 12y.
_COHORT_LE_SLOPE = 0.1
_COHORT_LE_CAP = 6.0


def _survival_from_18(ages: np.ndarray, le: float) -> np.ndarray:
    """Cohort-adjusted Gompertz survival (child mortality ignored:
    S=1 below 18). Stepwise cumulative hazard over the age grid, with
    each age's hazard drawn from that cohort's effective LE."""
    from earth1.generational import _gompertz_a, GOMPERTZ_B
    le_eff = le - np.minimum(_COHORT_LE_SLOPE * np.maximum(ages - 18.0, 0.0),
                             _COHORT_LE_CAP)
    a = np.array([_gompertz_a(v) for v in np.round(le_eff, 1)])
    hazard = np.where(ages > 18.0,
                      a * np.exp(GOMPERTZ_B * (ages - 18.0)), 0.0)
    steps = np.diff(ages, prepend=ages[0])
    return np.exp(-np.cumsum(hazard * steps))


def _adult_age_distribution(u18: float, le: float) -> tuple:
    """(ages, probabilities) for adults under the stable-population model.

    r is bisected so that the modelled under-18 share matches census u18.
    """
    key = (round(u18, 4), round(le, 1))
    if key in _ADULT_AGE_CACHE:
        return _ADULT_AGE_CACHE[key]

    surv = _survival_from_18(_AGE_GRID, le)
    child = _AGE_GRID < 18.0

    def u18_share(r: float) -> float:
        dens = np.exp(-r * _AGE_GRID) * surv
        return float(dens[child].sum() / dens.sum())

    lo, hi = -0.05, 0.10   # covers shrinking Japan to booming Niger
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if u18_share(mid) < u18:
            lo = mid
        else:
            hi = mid
    # floor r at replacement level: low-fertility countries backfill
    # working ages through immigration (DE, JP, IT), so their age
    # structure tracks r≈0 far better than stable-shrinking, which
    # over-ages them badly (Germany came out 44% over-65 among adults
    # vs ~30% real). u18 then over-shoots census for those countries —
    # acceptable: only the adult portion is sampled.
    r = float(np.clip(0.5 * (lo + hi), 0.0, 0.10))

    dens = np.exp(-r * _AGE_GRID) * surv
    adult_mask = ~child
    ages = _AGE_GRID[adult_mask]
    p = dens[adult_mask] / dens[adult_mask].sum()
    _ADULT_AGE_CACHE[key] = (ages, p)
    return _ADULT_AGE_CACHE[key]


def _sample_adult_ages(country: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Per-agent adult ages (raw years, clipped to the [18, 90] encoding)."""
    out = np.empty(len(country))
    for ci in np.unique(country):
        c = GENESIS_COUNTRIES[int(ci)]
        ages, p = _adult_age_distribution(
            float(c.get("u18", 0.25)), float(c.get("le", 72.0)))
        mask = country == ci
        out[mask] = rng.choice(ages, size=int(mask.sum()), p=p)
    return np.clip(out, 18.0, 90.0)


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
            min_per_country: int = 500,
            substrate: str | None = None) -> Civilization:
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

    # Age (Manifold v2): stable-population adult pyramid per country,
    # derived from census u18 + the same Gompertz survival the
    # generational tick uses. Normalized to [0,1] where 0=18, 1=90.
    age_raw = _sample_adult_ages(country, rng)
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

    # ── C2+ substrate v1 (MISSION v2 WS1): joint demographic draw ──
    # Replaces the independent draws above AFTER they have consumed the
    # main rng stream, so the default path stays byte-identical and the
    # downstream layers see an unchanged stream position. Uses its own
    # spawned rng. Adds a sex axis (civ.sex).
    _sex = None
    if substrate == "c2plus_v1":
        from earth1.popsynth import draw_c2plus
        _iso2 = [c["iso2"] for c in GENESIS_COUNTRIES]
        _sex, _age_raw, education, income, urban = draw_c2plus(
            country, seed, _iso2)
        age_raw = _age_raw
        age = (age_raw - 18.0) / 72.0
        age_bucket = np.digitize(age_raw, [30, 45, 60, 75])
    elif substrate is not None:
        raise ValueError(f"unknown substrate {substrate!r}")

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
    # ABLATION (EARTH1_NO_HOFSTEDE=1): neutralize the Hofstede channel
    # (0.5 = no modulation) for the feature-attribution table
    import os as _os2
    if _os2.environ.get("EARTH1_NO_HOFSTEDE", "0") == "1":
        for _a in (h_pdi, h_idv, h_mas, h_uai, h_lto, h_ind):
            _a[:] = 0.5

    power_distance = np.clip(rng.normal(h_pdi, 0.12), 0, 1)
    individualism = np.clip(rng.normal(h_idv, 0.12), 0, 1)
    uncertainty_avoidance = np.clip(rng.normal(h_uai, 0.12), 0, 1)
    long_term_orientation = np.clip(rng.normal(h_lto, 0.12), 0, 1)

    # Inglehart-Welzel dimensions (wider cross-country range than Hofstede)
    _ING_DEFAULT = {"trad_sec": 0.45, "surv_self": 0.45}
    # LEAKAGE ABLATION (EARTH1_NO_INGLEHART=1): Inglehart coordinates
    # derive from WVS answers to the very items GOQA benchmarks (God,
    # religion, abortion, homosexuality, pride, trust). LOO-country CV
    # cannot remove information already baked into the held country's
    # coordinates. This flag neutralizes the channel (0.5 = no
    # modulation) so the benchmark can be run leakage-clean.
    import os as _os
    _no_ing = _os.environ.get("EARTH1_NO_INGLEHART", "0") == "1"
    ing_trad_sec = np.array([INGLEHART.get(c["iso2"], _ING_DEFAULT)["trad_sec"]
                             for c in GENESIS_COUNTRIES])[country]
    ing_surv_self = np.array([INGLEHART.get(c["iso2"], _ING_DEFAULT)["surv_self"]
                              for c in GENESIS_COUNTRIES])[country]
    if _no_ing:
        ing_trad_sec = np.full_like(ing_trad_sec, 0.5)
        ing_surv_self = np.full_like(ing_surv_self, 0.5)

    # Culture offset: derived from Hofstede IND (indulgence) centered at 0.5
    culture_offset = (h_ind - 0.5) * 0.4 + region_culture_delta

    # ── Layer 4: Soul scalars ──

    c_open = np.array([_INCOME_CLASS_OPEN.get(c["income"], 0.48)
                        for c in GENESIS_COUNTRIES])[country]
    c_risk = np.array([_INCOME_CLASS_RISK.get(c["income"], 0.52)
                        for c in GENESIS_COUNTRIES])[country]
    c_doubt = np.array([_INCOME_CLASS_DOUBT.get(c["income"], 0.54)
                         for c in GENESIS_COUNTRIES])[country]

    # Modulate base rates by Hofstede + Inglehart dimensions
    c_open = c_open + (h_idv - 0.5) * 0.15 + (ing_surv_self - 0.5) * 0.20
    c_risk = c_risk + (h_ind - 0.5) * 0.1 + (h_mas - 0.5) * 0.10
    c_doubt = c_doubt + (h_uai - 0.5) * 0.15 - (ing_trad_sec - 0.5) * 0.12

    edu_lift = np.where(education == 2, 0.08, np.where(education == 0, -0.06, 0.0))

    openness = np.clip(rng.normal(c_open + edu_lift - age * 0.08, 0.16), 0, 1)
    risk_appetite = np.clip(rng.normal(c_risk - age * 0.12, 0.17), 0, 1)
    doubt = np.clip(rng.normal(c_doubt - edu_lift * 0.5, 0.16), 0, 1)
    empathy = np.clip(rng.normal(0.55 + (ing_surv_self - 0.5) * 0.15, 0.16), 0, 1)
    desire_intensity = np.clip(rng.normal(0.5 + (0.6 - age) * 0.3 + (h_mas - 0.5) * 0.12, 0.17), 0, 1)
    economic_field = np.clip(rng.normal(INCOME_ECON[income], 0.1), 0, 1)

    conscientiousness = np.clip(rng.normal(0.52 + age * 0.1 + edu_lift * 0.3, 0.15), 0, 1)
    agreeableness = np.clip(rng.normal(0.54 + age * 0.05 + (ing_trad_sec - 0.5) * 0.10, 0.15), 0, 1)
    extraversion = np.clip(rng.normal(0.50 - age * 0.06 + (h_ind - 0.5) * 0.12, 0.16), 0, 1)
    neuroticism = np.clip(rng.normal(0.48 - age * 0.04 - edu_lift * 0.2 + (h_uai - 0.5) * 0.10, 0.16), 0, 1)

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

    # ── C2 genesis-v3: real within-country religiosity structure ──
    # EARTH1_RELIGIOSITY=1 draws each agent's religiosity from the WVS7
    # measured P(religious | country, age bucket, education) — the first
    # agent property that carries information no country mean contains.
    # Flag off (default) => None => every existing number unchanged.
    # ── C2 genesis-v3: REAL within-country structure from WVS7 ──
    # EARTH1_RELIGIOSITY=1 injects per-agent properties drawn from the
    # measured P(property | country, age bucket, education) — the first
    # agent information no country mean contains. Binary vars are drawn
    # Bernoulli; continuous vars take the cell value plus small noise.
    # Flag off (default) => all None => every existing number unchanged.
    religiosity = marital = employed = ideology = social_class = None
    if os.environ.get("EARTH1_RELIGIOSITY") == "1":
        import json as _json
        from pathlib import Path as _Path
        _root = _Path(__file__).resolve().parents[1] / "data"
        _rng_inj = np.random.default_rng(seed + 99)

        def _draw(prior: dict, binary: bool):
            p_vec = np.full(actual_pop, np.nan)
            for _ci, _code in enumerate(GENESIS_COUNTRY_CODES):
                _e = prior.get(_code)
                if _e is None:
                    continue
                _cm = country == _ci
                if not _cm.any():
                    continue
                p_vec[_cm] = _e["marginal"]
                for _key, _p in _e["cells"].items():
                    _a, _ed = _key.split("_")
                    _ab = int(_a)
                    _mask = _cm & (education == int(_ed)) & (
                        (age_bucket == _ab) if _ab < 3
                        else (age_bucket >= 3))
                    p_vec[_mask] = _p
            # fallback for the 130 countries WVS7 never surveyed:
            # 'neutral' (0.5) measured better than 'globalmean' — an
            # uninformative default beats importing survey-sample bias
            _fb = os.environ.get("EARTH1_INJECT_FALLBACK", "neutral")
            _glob = (0.5 if _fb == "neutral"
                     else (np.nanmean(p_vec) if np.isfinite(p_vec).any()
                           else 0.5))
            p_vec = np.where(np.isnan(p_vec), _glob, p_vec)
            if binary:
                return (_rng_inj.random(actual_pop) < p_vec).astype(np.float64)
            return np.clip(p_vec + _rng_inj.normal(0, 0.08, actual_pop), 0, 1)

        _rp = _root / "religiosity_priors.json"
        if _rp.exists():
            religiosity = _draw(_json.loads(_rp.read_text()), True)
        _jp = _root / "joint_priors.json"
        if _jp.exists():
            _pri = _json.loads(_jp.read_text())
            if "marital" in _pri:
                marital = _draw(_pri["marital"], True)
            if "employed" in _pri:
                employed = _draw(_pri["employed"], True)
            if "ideology" in _pri:
                ideology = _draw(_pri["ideology"], False)
            if "social_class" in _pri:
                social_class = _draw(_pri["social_class"], False)

    civ = Civilization(
        n=actual_pop, seed=seed,
        person_id=np.arange(actual_pop, dtype=np.int64),
        parent_id=np.full(actual_pop, -1, dtype=np.int64),
        person_counter=int(actual_pop),
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
        religiosity=religiosity, marital=marital,
        employed=employed, ideology=ideology,
        social_class=social_class,
    )
    if _sex is not None:
        civ.sex = _sex          # C2+ substrate: new demographic axis
    return civ


def _build_graph(
    n: int,
    openness: np.ndarray,
    forces: np.ndarray,
    culture_offset: np.ndarray,
    region_idx: np.ndarray,
    country: np.ndarray,
    seed: int,
    k_local: int = 8,
    k_cross: int = 2,
    cross_weight: float = 0.3,
) -> sparse.csr_matrix:
    """Country-stratified social graph.

    ~80% of edges connect agents within the same country (local homophily).
    ~20% are cross-country links at reduced weight. Diffusion primarily
    operates within countries, preserving per-country opinion structure
    while still allowing cross-border influence.
    """
    rng = make_rng(seed)

    # Within-country position: trait-based similarity (no country/region terms)
    pos = (0.30 * openness
         + 0.20 * forces[:, Force.ECONOMICS]
         + 0.15 * (1.0 - forces[:, Force.FEAR])
         + 0.20 * np.clip(0.5 + culture_offset, 0, 1)
         + 0.15 * forces[:, Force.EXPERIENCE])

    pos_range = pos.max() - pos.min()
    if pos_range > 0:
        pos = (pos - pos.min()) / pos_range

    # Sort by (country, position) — nearest neighbors stay within-country
    composite = country.astype(np.float64) * 2.0 + pos
    order = np.argsort(composite)
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)

    half = max(1, k_local // 2)
    rows = []
    cols = []
    weights = []

    for d in range(1, half + 1):
        valid_fwd = rank + d < n
        src_fwd = np.where(valid_fwd)[0]
        dst_fwd = order[rank[src_fwd] + d]
        same = country[src_fwd] == country[dst_fwd]
        rows.append(src_fwd[same])
        cols.append(dst_fwd[same])
        weights.append(np.ones(same.sum(), dtype=np.float32))

        valid_bwd = rank - d >= 0
        src_bwd = np.where(valid_bwd)[0]
        dst_bwd = order[rank[src_bwd] - d]
        same = country[src_bwd] == country[dst_bwd]
        rows.append(src_bwd[same])
        cols.append(dst_bwd[same])
        weights.append(np.ones(same.sum(), dtype=np.float32))

    # Cross-country links at reduced weight
    for _ in range(k_cross):
        src_all = np.arange(n)
        dst_all = rng.integers(0, n, size=n)
        mask = (dst_all != src_all) & (country[dst_all] != country[src_all])
        rows.append(src_all[mask])
        cols.append(dst_all[mask])
        weights.append(np.full(mask.sum(), cross_weight, dtype=np.float32))

    row = np.concatenate(rows)
    col = np.concatenate(cols)
    data = np.concatenate(weights)
    adj = sparse.csr_matrix((data, (row, col)), shape=(n, n))
    return adj


def genesis_country_name(code_idx: int) -> str:
    return GENESIS_COUNTRIES[code_idx]["name"]


def genesis_country_code(code_idx: int) -> str:
    return GENESIS_COUNTRIES[code_idx]["iso2"]
