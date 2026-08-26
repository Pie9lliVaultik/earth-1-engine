"""Build per-country C2+ 5-way population tables (substrate v1).

Runs on prime (needs the WVS-7 extract rows.npz). For each of the 194
genesis countries: IPF from the equal-country WVS donor-pool seed to
five margins — sex (census male share), urban (census), age bands
(genesis's own survival-model pyramid, aggregated to the 6 WVS bands),
edu/income (WVS-frame margins where the country is surveyed, income-
tier-pooled WVS margins otherwise). Writes data/c2plus_tables_v1.json.
Licence note: WVS-derived — DEVELOPMENT artifact under the audit's
terms; not clear for commercial deployment until WVSA permission.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.genesis import GENESIS_COUNTRIES, _sample_adult_ages  # noqa
from c2plus.run_bakeoff import A3, SHAPE, ipf, margins_of  # noqa

ROWS = "/opt/earth1-data/c2plus/rows.npz"
BANDS = [25, 35, 45, 55, 65]
TIER_IDX = {"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}


def main():
    rows = np.load(ROWS)
    iso2_of = {}
    tables = {}
    for a3 in rows.files:
        r = rows[a3]
        t = np.zeros(SHAPE)
        np.add.at(t, tuple(r[:, i].astype(int) for i in range(5)), r[:, 5])
        tables[a3] = t / t.sum()
        iso2_of[a3] = A3[a3]
    pool = np.mean(list(tables.values()), axis=0)
    by_iso2 = {iso2_of[a3]: t for a3, t in tables.items()}
    # tier-pooled edu/income margins for unsurveyed countries
    tier_pool = {k: [] for k in TIER_IDX}
    for a3, t in tables.items():
        iso2 = iso2_of[a3]
        c = next((c for c in GENESIS_COUNTRIES if c["iso2"] == iso2), None)
        if c is not None:
            tier_pool.setdefault(c["income"], []).append(t)
    tier_marg = {}
    for k, ts in tier_pool.items():
        if ts:
            tp = np.mean(ts, axis=0)
            tier_marg[k] = (tp.sum(axis=(0, 1, 3, 4)),   # edu
                            tp.sum(axis=(0, 1, 2, 4)))   # income
    default_marg = (pool.sum(axis=(0, 1, 3, 4)), pool.sum(axis=(0, 1, 2, 4)))
    rng = np.random.default_rng(20260827)
    out, meta = {}, {"surveyed": 0, "tier_fallback": 0}
    for ci, c in enumerate(GENESIS_COUNTRIES):
        iso2 = c["iso2"]
        ages = _sample_adult_ages(np.full(20000, ci), rng)
        band = np.digitize(ages, BANDS)
        m_age = np.bincount(band, minlength=6) / 20000.0
        m_sex = np.array([c["male"] / 100.0, 1 - c["male"] / 100.0])
        m_urb = np.array([c["urban"] / 100.0, 1 - c["urban"] / 100.0])
        if iso2 in by_iso2:
            t = by_iso2[iso2]
            m_edu = t.sum(axis=(0, 1, 3, 4))
            m_inc = t.sum(axis=(0, 1, 2, 4))
            meta["surveyed"] += 1
        else:
            m_edu, m_inc = tier_marg.get(c["income"], default_marg)
            meta["tier_fallback"] += 1
        margins = [m_sex, m_age, m_edu / m_edu.sum(), m_inc / m_inc.sum(),
                   m_urb]
        t, err = ipf(pool, margins)
        assert err <= 1e-6, (iso2, err)
        out[iso2] = np.round(t, 9).tolist()
    path = os.path.join(ROOT, "data", "c2plus_tables_v1.json")
    json.dump({"meta": meta, "shape": list(SHAPE), "bands": BANDS,
               "tables": out}, open(path, "w"))
    print("TABLES BUILT", meta, "->", path)


if __name__ == "__main__":
    main()
