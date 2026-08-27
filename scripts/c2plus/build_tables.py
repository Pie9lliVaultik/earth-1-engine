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
sys.path.insert(0, os.path.join(ROOT, "scripts"))
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
    # ── v2 FRAME REPAIR (2026-08-27, diagnosed before rebuild) ──
    # WVS Q288R is SELF-REPORTED relative income: respondents cluster on
    # "middle" everywhere (DE 77%, US 71%; global 60% mid, top band
    # 38%->11%). genesis.income is a MATERIAL level consumed by
    # life.py's wealth/deprivation machinery, so importing the
    # self-report marginal mis-states material income and produced the
    # Stage-A divergence (deprivation +17.6%, wealth -36%, starvation
    # +32%). Repair: keep the C2+ JOINT STRUCTURE (the proven +24.8%
    # withheld-joint win) but rake the income margin to the incumbent
    # genesis material-income distribution per country. Education is
    # NOT repaired: WVS-measured attainment (43/32/24) is closer to
    # real global adult attainment than the incumbent's income-class
    # guess (26/39/35), so the measured margin is kept.
    from earth1.genesis import genesis as _genesis
    _civ = _genesis(200_000, 4242)
    _inc_marg = {}
    for _ci in range(len(GENESIS_COUNTRIES)):
        _m = _civ.country == _ci
        if _m.sum() >= 30:
            _v = np.bincount(_civ.income[_m], minlength=3).astype(float)
            _inc_marg[GENESIS_COUNTRIES[_ci]["iso2"]] = _v / _v.sum()

    rng = np.random.default_rng(20260827)
    out, meta = {}, {"surveyed": 0, "tier_fallback": 0,
                     "income_frame_repaired": 0}
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
        m_inc = m_inc / m_inc.sum()
        if iso2 in _inc_marg:                 # v2 frame repair
            m_inc = _inc_marg[iso2]
            meta["income_frame_repaired"] += 1
        margins = [m_sex, m_age, m_edu / m_edu.sum(), m_inc, m_urb]
        t, err = ipf(pool, margins)
        assert err <= 1e-6, (iso2, err)
        out[iso2] = np.round(t, 9).tolist()
    path = os.path.join(ROOT, "data", "c2plus_tables_v2.json")
    json.dump({"meta": meta, "shape": list(SHAPE), "bands": BANDS,
               "tables": out}, open(path, "w"))
    print("TABLES BUILT", meta, "->", path)


if __name__ == "__main__":
    main()
