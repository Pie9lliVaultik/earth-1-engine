"""Vectorized population generation — 1M agents in ~3 seconds on CPU."""
from __future__ import annotations
import numpy as np
from scipy import sparse
from earth1.types import Civilization, Force, NUM_FORCES
from earth1.culture import HOFSTEDE
from earth1.rng import make_rng


COUNTRIES = [
    # --- Original 9 (indices 0-8 preserved) ---
    {"code": "US", "name": "United States",  "w": 0.042, "open": 0.58, "risk": 0.56, "doubt": 0.50, "cult": 0.12, "urban": 0.82, "edu_hi": 0.44},
    {"code": "GB", "name": "United Kingdom",  "w": 0.008, "open": 0.60, "risk": 0.50, "doubt": 0.48, "cult": 0.08, "urban": 0.84, "edu_hi": 0.46},
    {"code": "DE", "name": "Germany",         "w": 0.011, "open": 0.56, "risk": 0.44, "doubt": 0.46, "cult":-0.02, "urban": 0.77, "edu_hi": 0.40},
    {"code": "BR", "name": "Brazil",          "w": 0.027, "open": 0.52, "risk": 0.58, "doubt": 0.56, "cult": 0.18, "urban": 0.87, "edu_hi": 0.26},
    {"code": "NG", "name": "Nigeria",         "w": 0.028, "open": 0.47, "risk": 0.62, "doubt": 0.62, "cult": 0.24, "urban": 0.53, "edu_hi": 0.18},
    {"code": "IN", "name": "India",           "w": 0.178, "open": 0.49, "risk": 0.55, "doubt": 0.58, "cult": 0.10, "urban": 0.36, "edu_hi": 0.24},
    {"code": "JP", "name": "Japan",           "w": 0.016, "open": 0.50, "risk": 0.38, "doubt": 0.50, "cult":-0.16, "urban": 0.92, "edu_hi": 0.50},
    {"code": "MX", "name": "Mexico",          "w": 0.016, "open": 0.53, "risk": 0.57, "doubt": 0.55, "cult": 0.16, "urban": 0.81, "edu_hi": 0.28},
    {"code": "FR", "name": "France",          "w": 0.008, "open": 0.59, "risk": 0.47, "doubt": 0.52, "cult": 0.02, "urban": 0.81, "edu_hi": 0.43},
    # --- Expansion (indices 9+) ---
    {"code": "CN", "name": "China",           "w": 0.179, "open": 0.44, "risk": 0.48, "doubt": 0.45, "cult":-0.10, "urban": 0.64, "edu_hi": 0.30},
    {"code": "ID", "name": "Indonesia",       "w": 0.035, "open": 0.46, "risk": 0.54, "doubt": 0.55, "cult": 0.14, "urban": 0.57, "edu_hi": 0.20},
    {"code": "PK", "name": "Pakistan",        "w": 0.029, "open": 0.40, "risk": 0.52, "doubt": 0.64, "cult": 0.22, "urban": 0.37, "edu_hi": 0.14},
    {"code": "BD", "name": "Bangladesh",      "w": 0.021, "open": 0.42, "risk": 0.56, "doubt": 0.60, "cult": 0.18, "urban": 0.39, "edu_hi": 0.16},
    {"code": "RU", "name": "Russia",          "w": 0.018, "open": 0.48, "risk": 0.46, "doubt": 0.54, "cult":-0.08, "urban": 0.75, "edu_hi": 0.54},
    {"code": "ET", "name": "Ethiopia",        "w": 0.015, "open": 0.44, "risk": 0.58, "doubt": 0.62, "cult": 0.20, "urban": 0.22, "edu_hi": 0.10},
    {"code": "PH", "name": "Philippines",     "w": 0.014, "open": 0.52, "risk": 0.58, "doubt": 0.54, "cult": 0.16, "urban": 0.47, "edu_hi": 0.28},
    {"code": "EG", "name": "Egypt",           "w": 0.013, "open": 0.42, "risk": 0.50, "doubt": 0.60, "cult": 0.20, "urban": 0.43, "edu_hi": 0.22},
    {"code": "VN", "name": "Vietnam",         "w": 0.013, "open": 0.48, "risk": 0.52, "doubt": 0.50, "cult": 0.06, "urban": 0.38, "edu_hi": 0.22},
    {"code": "TR", "name": "Turkey",          "w": 0.011, "open": 0.46, "risk": 0.50, "doubt": 0.56, "cult": 0.14, "urban": 0.76, "edu_hi": 0.32},
    {"code": "IR", "name": "Iran",            "w": 0.011, "open": 0.45, "risk": 0.48, "doubt": 0.58, "cult": 0.12, "urban": 0.76, "edu_hi": 0.36},
    {"code": "TH", "name": "Thailand",        "w": 0.009, "open": 0.50, "risk": 0.52, "doubt": 0.50, "cult": 0.08, "urban": 0.52, "edu_hi": 0.26},
    {"code": "KR", "name": "South Korea",     "w": 0.007, "open": 0.52, "risk": 0.42, "doubt": 0.48, "cult":-0.14, "urban": 0.81, "edu_hi": 0.50},
    {"code": "IT", "name": "Italy",           "w": 0.008, "open": 0.56, "risk": 0.44, "doubt": 0.50, "cult": 0.04, "urban": 0.71, "edu_hi": 0.38},
    {"code": "ES", "name": "Spain",           "w": 0.006, "open": 0.56, "risk": 0.48, "doubt": 0.50, "cult": 0.06, "urban": 0.81, "edu_hi": 0.40},
    {"code": "CO", "name": "Colombia",        "w": 0.007, "open": 0.50, "risk": 0.56, "doubt": 0.56, "cult": 0.16, "urban": 0.82, "edu_hi": 0.24},
    {"code": "AR", "name": "Argentina",       "w": 0.006, "open": 0.54, "risk": 0.54, "doubt": 0.52, "cult": 0.10, "urban": 0.92, "edu_hi": 0.36},
    {"code": "KE", "name": "Kenya",           "w": 0.007, "open": 0.46, "risk": 0.58, "doubt": 0.58, "cult": 0.20, "urban": 0.28, "edu_hi": 0.16},
    {"code": "ZA", "name": "South Africa",    "w": 0.008, "open": 0.50, "risk": 0.56, "doubt": 0.56, "cult": 0.14, "urban": 0.68, "edu_hi": 0.22},
    {"code": "UA", "name": "Ukraine",         "w": 0.006, "open": 0.48, "risk": 0.46, "doubt": 0.56, "cult":-0.04, "urban": 0.70, "edu_hi": 0.42},
    {"code": "PL", "name": "Poland",          "w": 0.005, "open": 0.52, "risk": 0.46, "doubt": 0.50, "cult": 0.02, "urban": 0.60, "edu_hi": 0.40},
    {"code": "CA", "name": "Canada",          "w": 0.005, "open": 0.60, "risk": 0.52, "doubt": 0.46, "cult": 0.08, "urban": 0.82, "edu_hi": 0.54},
    {"code": "AU", "name": "Australia",       "w": 0.003, "open": 0.60, "risk": 0.54, "doubt": 0.46, "cult": 0.10, "urban": 0.86, "edu_hi": 0.48},
    {"code": "SA", "name": "Saudi Arabia",    "w": 0.005, "open": 0.38, "risk": 0.48, "doubt": 0.60, "cult": 0.20, "urban": 0.84, "edu_hi": 0.32},
    {"code": "PE", "name": "Peru",            "w": 0.004, "open": 0.50, "risk": 0.54, "doubt": 0.56, "cult": 0.14, "urban": 0.78, "edu_hi": 0.22},
    {"code": "CL", "name": "Chile",           "w": 0.003, "open": 0.54, "risk": 0.52, "doubt": 0.50, "cult": 0.08, "urban": 0.88, "edu_hi": 0.34},
    {"code": "MY", "name": "Malaysia",        "w": 0.004, "open": 0.48, "risk": 0.52, "doubt": 0.52, "cult": 0.10, "urban": 0.78, "edu_hi": 0.28},
    {"code": "RO", "name": "Romania",         "w": 0.003, "open": 0.50, "risk": 0.48, "doubt": 0.52, "cult": 0.04, "urban": 0.54, "edu_hi": 0.34},
    {"code": "NL", "name": "Netherlands",     "w": 0.002, "open": 0.62, "risk": 0.50, "doubt": 0.44, "cult": 0.00, "urban": 0.92, "edu_hi": 0.48},
    {"code": "SE", "name": "Sweden",          "w": 0.001, "open": 0.64, "risk": 0.50, "doubt": 0.40, "cult":-0.06, "urban": 0.88, "edu_hi": 0.52},
    {"code": "GH", "name": "Ghana",           "w": 0.004, "open": 0.46, "risk": 0.58, "doubt": 0.58, "cult": 0.22, "urban": 0.58, "edu_hi": 0.18},
    {"code": "IQ", "name": "Iraq",            "w": 0.005, "open": 0.40, "risk": 0.52, "doubt": 0.64, "cult": 0.22, "urban": 0.71, "edu_hi": 0.18},
    {"code": "MA", "name": "Morocco",         "w": 0.005, "open": 0.44, "risk": 0.50, "doubt": 0.56, "cult": 0.16, "urban": 0.64, "edu_hi": 0.22},
    {"code": "SG", "name": "Singapore",       "w": 0.001, "open": 0.56, "risk": 0.48, "doubt": 0.42, "cult":-0.06, "urban": 1.00, "edu_hi": 0.56},
    {"code": "NZ", "name": "New Zealand",     "w": 0.001, "open": 0.62, "risk": 0.54, "doubt": 0.44, "cult": 0.08, "urban": 0.87, "edu_hi": 0.46},
    {"code": "IE", "name": "Ireland",         "w": 0.001, "open": 0.60, "risk": 0.52, "doubt": 0.44, "cult": 0.06, "urban": 0.64, "edu_hi": 0.48},
    {"code": "NO", "name": "Norway",          "w": 0.001, "open": 0.64, "risk": 0.50, "doubt": 0.40, "cult":-0.04, "urban": 0.83, "edu_hi": 0.52},
    {"code": "IL", "name": "Israel",          "w": 0.001, "open": 0.56, "risk": 0.52, "doubt": 0.48, "cult": 0.02, "urban": 0.93, "edu_hi": 0.50},
    {"code": "DK", "name": "Denmark",         "w": 0.001, "open": 0.64, "risk": 0.50, "doubt": 0.38, "cult":-0.06, "urban": 0.88, "edu_hi": 0.50},
    {"code": "CH", "name": "Switzerland",     "w": 0.001, "open": 0.62, "risk": 0.50, "doubt": 0.42, "cult":-0.02, "urban": 0.74, "edu_hi": 0.52},
    {"code": "AE", "name": "UAE",             "w": 0.001, "open": 0.44, "risk": 0.52, "doubt": 0.52, "cult": 0.12, "urban": 0.87, "edu_hi": 0.36},
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
    "CN": ["East", "Central", "West", "Northeast"],
    "ID": ["Java", "Sumatra", "Kalimantan", "Sulawesi"],
    "PK": ["Punjab", "Sindh", "KPK", "Balochistan"],
    "BD": ["Dhaka", "Chittagong", "Rajshahi", "Sylhet"],
    "RU": ["Central", "Urals", "Siberia", "Far East"],
    "ET": ["Addis Ababa", "Amhara", "Oromia", "SNNPR"],
    "PH": ["Luzon", "Visayas", "Mindanao", "Metro Manila"],
    "EG": ["Cairo", "Delta", "Upper Egypt", "Canal"],
    "VN": ["North", "Central", "South", "Highlands"],
    "TR": ["Marmara", "Aegean", "Central", "Southeast"],
    "IR": ["Tehran", "Isfahan", "Fars", "Khorasan"],
    "TH": ["Central", "North", "Northeast", "South"],
    "KR": ["Capital", "Gyeongsang", "Chungcheong", "Jeolla"],
    "IT": ["North", "Central", "South", "Islands"],
    "ES": ["Madrid", "Catalonia", "Andalusia", "Valencia"],
    "CO": ["Andina", "Caribe", "Pacífica", "Orinoquía"],
    "AR": ["Buenos Aires", "Pampa", "Patagonia", "Norte"],
    "KE": ["Nairobi", "Coast", "Rift Valley", "Western"],
    "ZA": ["Gauteng", "KwaZulu-Natal", "Western Cape", "Eastern Cape"],
    "UA": ["Kyiv", "West", "East", "South"],
    "PL": ["Mazovia", "Silesia", "Greater Poland", "Lesser Poland"],
    "CA": ["Ontario", "Quebec", "BC", "Alberta"],
    "AU": ["NSW", "Victoria", "Queensland", "WA"],
    "SA": ["Riyadh", "Makkah", "Eastern", "Madinah"],
    "PE": ["Lima", "Coast", "Sierra", "Selva"],
    "CL": ["Santiago", "Valparaíso", "Biobío", "Araucanía"],
    "MY": ["Peninsular West", "Peninsular East", "Sabah", "Sarawak"],
    "RO": ["Bucharest", "Transylvania", "Moldavia", "Wallachia"],
    "NL": ["Randstad", "North", "South", "East"],
    "SE": ["Stockholm", "Gothenburg", "Malmö", "North"],
    "GH": ["Greater Accra", "Ashanti", "Northern", "Western"],
    "IQ": ["Baghdad", "Kurdistan", "South", "West"],
    "MA": ["Casablanca", "Rabat", "Marrakech", "Fès"],
    "SG": ["Central", "North", "East", "West"],
    "NZ": ["Auckland", "Wellington", "Canterbury", "Waikato"],
    "IE": ["Dublin", "Munster", "Connacht", "Ulster"],
    "NO": ["Oslo", "Western", "Central", "Northern"],
    "IL": ["Tel Aviv", "Jerusalem", "Haifa", "Negev"],
    "DK": ["Copenhagen", "Zealand", "Jutland", "Funen"],
    "CH": ["Zurich", "Geneva", "Bern", "Basel"],
    "AE": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman"],
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

    # --- Big Five beyond openness ---
    conscientiousness = np.clip(rng.normal(0.52 + age * 0.1 + edu_lift * 0.3, 0.15), 0, 1)
    agreeableness = np.clip(rng.normal(0.54 + age * 0.05, 0.15, size=pop), 0, 1)
    extraversion = np.clip(rng.normal(0.50 - age * 0.06, 0.16, size=pop), 0, 1)
    neuroticism = np.clip(rng.normal(0.48 - age * 0.04 - edu_lift * 0.2, 0.16), 0, 1)

    # --- Hofstede-derived per-agent traits (country mean + noise) ---
    codes = [c["code"] for c in COUNTRIES]
    h_pdi = np.array([HOFSTEDE.get(c, {}).get("pdi", 0.5) for c in codes])[country]
    h_idv = np.array([HOFSTEDE.get(c, {}).get("idv", 0.5) for c in codes])[country]
    h_uai = np.array([HOFSTEDE.get(c, {}).get("uai", 0.5) for c in codes])[country]
    h_lto = np.array([HOFSTEDE.get(c, {}).get("lto", 0.5) for c in codes])[country]

    power_distance = np.clip(rng.normal(h_pdi, 0.12), 0, 1)
    individualism = np.clip(rng.normal(h_idv, 0.12), 0, 1)
    uncertainty_avoidance = np.clip(rng.normal(h_uai, 0.12), 0, 1)
    long_term_orientation = np.clip(rng.normal(h_lto, 0.12), 0, 1)

    # --- forces matrix (N, 8) — enriched with new traits ---
    forces = np.empty((pop, NUM_FORCES), dtype=np.float64)
    forces[:, Force.FEAR] = np.clip(
        (doubt + (1.0 - risk_appetite) + neuroticism * 0.3) / 2.3, 0, 1)
    forces[:, Force.DESIRE] = desire_intensity
    forces[:, Force.ECONOMICS] = economic_field
    forces[:, Force.COLLECTIVE] = np.clip(
        (1.0 - openness) * 0.6 + power_distance * 0.4, 0, 1)
    forces[:, Force.IDENTITY] = np.clip(
        openness * 0.5 + individualism * 0.5, 0, 1)
    forces[:, Force.CULTURE] = np.clip(
        0.5 + c_cult + long_term_orientation * 0.1, 0, 1)
    forces[:, Force.EXPERIENCE] = age
    forces[:, Force.TEMPERAMENT] = np.clip(
        risk_appetite * 0.7 + extraversion * 0.3, 0, 1)

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
