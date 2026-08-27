"""C2+ population substrate v1 (MISSION v2, workstream 1).

Draws each agent's (sex, age, education, income, urban) jointly from
the per-country IPF table in data/c2plus_tables_v1.json instead of the
incumbent independent-ish draws. Consumes its OWN rng stream (spawned
from the genesis seed) so the main genesis stream is untouched — the
default substrate path stays byte-identical (KA in
tests/test_popsynth.py).
"""
import json
import os

import numpy as np

_TABLES = None
_TABLE_FILE = os.environ.get("EARTH1_C2PLUS_TABLES", "c2plus_tables_v2.json")
BAND_EDGES = [(18, 25), (25, 35), (35, 45), (45, 55), (55, 65), (65, 90)]


def _tables():
    global _TABLES
    if _TABLES is None:
        p = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "data", _TABLE_FILE)
        _TABLES = json.load(open(p))
    return _TABLES


def draw_c2plus(country: np.ndarray, seed: int, iso2_list):
    """Joint demographic draw per agent. Returns sex, age_raw(years),
    education, income, urban arrays."""
    tab = _tables()
    rng = np.random.default_rng([seed, 777])
    n = len(country)
    sex = np.zeros(n, np.int8)
    band = np.zeros(n, np.int64)
    edu = np.zeros(n, np.int32)
    inc = np.zeros(n, np.int32)
    urb = np.zeros(n, bool)
    shape = tuple(tab["shape"])
    for ci in np.unique(country):
        m = country == ci
        t = np.asarray(tab["tables"][iso2_list[ci]], dtype=np.float64)
        flat = t.ravel()
        idx = rng.choice(flat.size, size=int(m.sum()), p=flat / flat.sum())
        s, b, e, i, u = np.unravel_index(idx, shape)
        sex[m], band[m], edu[m], inc[m], urb[m] = s, b, e, i, u.astype(bool)
    lo = np.array([e[0] for e in BAND_EDGES])[band]
    hi = np.array([e[1] for e in BAND_EDGES])[band]
    age_raw = lo + rng.random(n) * (hi - lo)
    return sex, age_raw, edu, inc, urb
