"""Vectorized population generation — 1M agents in ~3 seconds on CPU."""
from __future__ import annotations
import numpy as np
from scipy import sparse
from earth1.types import Civilization, Force, NUM_FORCES
from earth1.rng import make_rng


COUNTRIES = [
    {"code": "US", "name": "United States",  "w": 0.13, "open": 0.58, "risk": 0.56, "doubt": 0.50, "cult": 0.12, "urban": 0.82, "edu_hi": 0.44},
    {"code": "GB", "name": "United Kingdom",  "w": 0.08, "open": 0.60, "risk": 0.50, "doubt": 0.48, "cult": 0.08, "urban": 0.84, "edu_hi": 0.46},
    {"code": "DE", "name": "Germany",         "w": 0.09, "open": 0.56, "risk": 0.44, "doubt": 0.46, "cult":-0.02, "urban": 0.77, "edu_hi": 0.40},
    {"code": "BR", "name": "Brazil",          "w": 0.12, "open": 0.52, "risk": 0.58, "doubt": 0.56, "cult": 0.18, "urban": 0.87, "edu_hi": 0.26},
    {"code": "NG", "name": "Nigeria",         "w": 0.11, "open": 0.47, "risk": 0.62, "doubt": 0.62, "cult": 0.24, "urban": 0.53, "edu_hi": 0.18},
    {"code": "IN", "name": "India",           "w": 0.16, "open": 0.49, "risk": 0.55, "doubt": 0.58, "cult": 0.10, "urban": 0.36, "edu_hi": 0.24},
    {"code": "JP", "name": "Japan",           "w": 0.09, "open": 0.50, "risk": 0.38, "doubt": 0.50, "cult":-0.16, "urban": 0.92, "edu_hi": 0.50},
    {"code": "MX", "name": "Mexico",          "w": 0.10, "open": 0.53, "risk": 0.57, "doubt": 0.55, "cult": 0.16, "urban": 0.81, "edu_hi": 0.28},
    {"code": "FR", "name": "France",          "w": 0.12, "open": 0.59, "risk": 0.47, "doubt": 0.52, "cult": 0.02, "urban": 0.81, "edu_hi": 0.43},
]

COUNTRY_CODES = [c["code"] for c in COUNTRIES]
COUNTRY_NAMES = {c["code"]: c["name"] for c in COUNTRIES}

REGIONS = {
    "US": ["Northeast", "South", "Midwest", "West"],
    "GB": ["England", "Scotland", "Wales", "N. Ireland"],
    "DE": ["North", "South", "East", "West"],
    "BR": ["Southeast", "Northeast", "South", "North"],
    "NG": ["South-West", "North", "South-East", "South-South"],
    "IN": ["North", "South", "East", "West"],
    "JP": ["Kanto", "Kansai", "Chubu", "Kyushu"],
    "MX": ["Centro", "Norte", "Sur", "Bajío"],
    "FR": ["Île-de-France", "South", "West", "East"],
}

AGE_BUCKETS = [
    {"label": "18-29", "mid": 0.14, "w": 0.24},
    {"label": "30-44", "mid": 0.38, "w": 0.29},
    {"label": "45-59", "mid": 0.62, "w": 0.24},
    {"label": "60-74", "mid": 0.82, "w": 0.16},
    {"label": "75+",   "mid": 0.96, "w": 0.07},
]
AGE_LABELS = [a["label"] for a in AGE_BUCKETS]

INCOME_ECON = np.array([0.32, 0.55, 0.80])  # low, mid, high


def generate_population(pop: int = 1_000_000, seed: int = 42) -> Civilization:
    rng = make_rng(seed)
    nc = len(COUNTRIES)

    # --- country assignment (weighted) ---
    weights = np.array([c["w"] for c in COUNTRIES])
    weights /= weights.sum()
    country = rng.choice(nc, size=pop, p=weights)

    # lookup tables indexed by country
    c_open   = np.array([c["open"]   for c in COUNTRIES])[country]
    c_risk   = np.array([c["risk"]   for c in COUNTRIES])[country]
    c_doubt  = np.array([c["doubt"]  for c in COUNTRIES])[country]
    c_cult   = np.array([c["cult"]   for c in COUNTRIES])[country]
    c_urban  = np.array([c["urban"]  for c in COUNTRIES])[country]
    c_edu_hi = np.array([c["edu_hi"] for c in COUNTRIES])[country]

    # --- region (uniform within country) ---
    region_counts = np.array([len(REGIONS[c["code"]]) for c in COUNTRIES])
    region = (rng.random(pop) * region_counts[country]).astype(np.int32)

    # --- age bucket (weighted) ---
    age_w = np.array([a["w"] for a in AGE_BUCKETS])
    age_w /= age_w.sum()
    age_bucket = rng.choice(len(AGE_BUCKETS), size=pop, p=age_w)
    age_mids = np.array([a["mid"] for a in AGE_BUCKETS])
    age = age_mids[age_bucket]

    # --- income (conditioned on country education rate) ---
    r_inc = rng.random(pop)
    low_thresh = np.clip(0.34 - c_edu_hi * 0.2, 0, 1)
    high_bias = 0.2 + c_edu_hi * 0.5
    mid_thresh = low_thresh + np.clip(0.66 - high_bias, 0, 1)
    income = np.where(r_inc < low_thresh, 0,
             np.where(r_inc < mid_thresh, 1, 2)).astype(np.int32)

    # --- education (conditioned on income + national rate) ---
    base_edu = c_edu_hi + np.where(income == 2, 0.28,
                           np.where(income == 1, 0.08, -0.14))
    r_edu = rng.random(pop)
    hi_thresh = np.clip(base_edu, 0, 1)
    education = np.where(r_edu < hi_thresh, 2,
                np.where(r_edu < hi_thresh + 0.4, 1, 0)).astype(np.int32)

    # --- urban ---
    urban = rng.random(pop) < c_urban

    # --- traits (conditioned on country + education + age) ---
    edu_lift = np.where(education == 2, 0.08, np.where(education == 0, -0.06, 0.0))

    openness = np.clip(rng.normal(c_open + edu_lift - age * 0.08, 0.16), 0, 1)
    risk_appetite = np.clip(rng.normal(c_risk - age * 0.12, 0.17), 0, 1)
    doubt = np.clip(rng.normal(c_doubt - edu_lift * 0.5, 0.16), 0, 1)
    empathy = np.clip(rng.normal(0.55, 0.16, size=pop), 0, 1)
    desire_intensity = np.clip(rng.normal(0.5 + (0.6 - age) * 0.3, 0.17), 0, 1)
    economic_field = np.clip(rng.normal(INCOME_ECON[income], 0.1), 0, 1)

    # --- forces matrix (N, 8) ---
    forces = np.empty((pop, NUM_FORCES), dtype=np.float64)
    forces[:, Force.FEAR] = np.clip((doubt + (1.0 - risk_appetite)) / 2.0, 0, 1)
    forces[:, Force.DESIRE] = desire_intensity
    forces[:, Force.ECONOMICS] = economic_field
    forces[:, Force.COLLECTIVE] = np.clip(1.0 - openness, 0, 1)
    forces[:, Force.IDENTITY] = openness
    forces[:, Force.CULTURE] = np.clip(0.5 + c_cult, 0, 1)
    forces[:, Force.EXPERIENCE] = age
    forces[:, Force.TEMPERAMENT] = risk_appetite

    # --- conviction (residual strength) ---
    alpha = np.clip(0.28 + 0.5 * openness - 0.12 * (1.0 - openness), 0, 1)

    # --- population means (8,) ---
    means = forces.mean(axis=0)

    # --- social graph ---
    adj = _build_graph(pop, openness, forces, c_cult, seed + 1)

    return Civilization(
        n=pop, seed=seed,
        country=country, region=region, age_bucket=age_bucket, age=age,
        education=education, income=income, urban=urban,
        openness=openness, empathy=empathy, risk_appetite=risk_appetite,
        doubt=doubt, desire_intensity=desire_intensity,
        economic_field=economic_field, culture_offset=c_cult,
        forces=forces, alpha=alpha, means=means, adj=adj,
    )


def _build_graph(
    n: int,
    openness: np.ndarray,
    forces: np.ndarray,
    culture_offset: np.ndarray,
    seed: int,
    k: int = 8,
    long_links: int = 2,
) -> sparse.csr_matrix:
    """Homophily ring + small-world long links as sparse CSR."""
    rng = make_rng(seed)

    # homophily position — weighted blend of opinion-shaping traits
    pos = (0.42 * openness
         + 0.24 * forces[:, Force.ECONOMICS]
         + 0.16 * (1.0 - forces[:, Force.FEAR])
         + 0.18 * (0.5 + culture_offset))
    order = np.argsort(pos)
    rank = np.empty(n, dtype=np.int64)
    rank[order] = np.arange(n)

    half = max(1, k // 2)
    # ring neighbors in sorted order
    rows = []
    cols = []
    for d in range(1, half + 1):
        # forward ring
        valid_fwd = rank + d < n
        src_fwd = np.where(valid_fwd)[0]
        dst_fwd = order[rank[src_fwd] + d]
        rows.append(src_fwd)
        cols.append(dst_fwd)
        # backward ring
        valid_bwd = rank - d >= 0
        src_bwd = np.where(valid_bwd)[0]
        dst_bwd = order[rank[src_bwd] - d]
        rows.append(src_bwd)
        cols.append(dst_bwd)

    # small-world long links
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


def country_name(code_idx: int) -> str:
    return COUNTRIES[code_idx]["name"]


def country_code(code_idx: int) -> str:
    return COUNTRIES[code_idx]["code"]
