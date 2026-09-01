"""HISTORICAL BIRTH — birth_at(T) (BIBLE v4.2.2 refinement 10).

Genesis parameterised by date T: every anchor and national input is
resolved to the latest vintage <= T where a versioned series exists on
disk; unversioned inputs are carried with an explicit VINTAGE_MISMATCH
flag in the vintage report that travels with every payload. The warm
runs on the GDELT 1.0 archive (monthly files, cached on the lab)
filtered to date <= T through the registered event->force map. A
mechanical assert refuses any consumed row whose date field exceeds T.

v1 honesty table (what actually versions tonight):
  RESOLVED <= T : UNGA ideal points (per-year rows); WB unemployment
                  series (2005-2024); GDELT news warm
  MISMATCH flags: C2+ tables (WVS-7), income calibration (2021 PPP),
                  GM mortality (current), religiosity (Factbook
                  current), WB poverty/CDR/LE anchors (latest fetch)
Every flag is in the report; nothing silent.
"""
import csv
import io
import json
import os
import zipfile
from datetime import date, timedelta

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDELT_DIR = "/opt/earth1-data/gdelt"

# registered GDELT QuadClass -> force map (v1; XI.A.2 owed with the
# battery's first scored event)
QUAD_FORCES = {1: {},                                  # verbal coop
               2: {"desire": 0.02, "collective": 0.01},  # material coop
               3: {"fear": 0.04, "doubt": 0.02},         # verbal conflict
               4: {"fear": 0.08, "collective": 0.04,     # material conflict
                   "economics": -0.02}}
FIPS = json.load(open(os.path.join(_ROOT, "data/geo/fips_to_iso2.json")))["map"]


def _vintage_geopol(T_year: int):
    """UNGA ideal points capped at year <= T — a REAL vintage."""
    path = "/opt/earth1-data/unga_idealpoints_july2025.tab"
    if not os.path.exists(path):
        return None, "unga file absent on this host"
    latest = {}
    with open(path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                yr = int(float(row["year"]))
                ip = float(row["idealpointall"])
            except (ValueError, KeyError):
                continue
            if yr > T_year:
                continue                       # the mechanical cutoff
            iso3 = row["iso3c"]
            if iso3 not in latest or yr > latest[iso3][0]:
                latest[iso3] = (yr, ip)
    assert all(v[0] <= T_year for v in latest.values())
    return latest, None


def _vintage_unemployment(T_year: int):
    p = os.path.join(_ROOT, "data/anchors_unemployment_series.v1.json")
    d = json.load(open(p))
    hist = {int(k): v for k, v in d["history_pct_lf"].items()}
    ok = {y: v for y, v in hist.items() if y <= T_year}
    if not ok:
        return None, f"series starts {min(hist)} > T"
    y = max(ok)
    return {"year": y, "value": ok[y], "sha": d["raw_sha256"][:16]}, None


def gdelt_day_aggregates(T: date, warm_days: int = 90):
    """Per (day, iso2): mention-weighted QuadClass counts from the
    monthly archives, dates strictly <= T (assert enforced). Cached —
    a 16-seed battery parses each archive once, not sixteen times."""
    cache = os.path.join(GDELT_DIR, f"agg_{T.isoformat()}_{warm_days}.json")
    if os.path.exists(cache):
        d = json.load(open(cache))
        return {tuple(k.split("|")): v for k, v in d["aggs"].items()}, \
            d["missing"]
    need_months = sorted({(T - timedelta(days=i)).strftime("%Y%m")
                          for i in range(warm_days + 1)})
    out = {}
    missing = []
    for m in need_months:
        zp = os.path.join(GDELT_DIR, f"gdelt_{m}.zip")
        if not os.path.exists(zp):
            missing.append(m)
            continue
        with zipfile.ZipFile(zp) as z:
            name = z.namelist()[0]
            with z.open(name) as f:
                for raw in io.TextIOWrapper(f, errors="replace"):
                    cols = raw.rstrip("\n").split("\t")
                    if len(cols) < 55:
                        continue
                    try:
                        d = date(int(cols[1][:4]), int(cols[1][4:6]),
                                 int(cols[1][6:8]))
                    except (ValueError, IndexError):
                        continue
                    assert d <= T or (_ for _ in ()).throw(
                        AssertionError(f"news item {d} > T={T}"))
                    if (T - d).days > warm_days:
                        continue
                    try:
                        quad = int(cols[29])
                        mentions = int(cols[31])
                        fips = cols[51][:2] if len(cols) > 51 else ""
                    except (ValueError, IndexError):
                        continue
                    iso2 = FIPS.get(fips)
                    if iso2 is None or quad not in QUAD_FORCES:
                        continue
                    key = (d.isoformat(), iso2)
                    out.setdefault(key, [0, 0, 0, 0])[quad - 1] += mentions
    json.dump({"aggs": {f"{k[0]}|{k[1]}": v for k, v in out.items()},
               "missing": missing}, open(cache, "w"))
    return out, missing


def birth_at(T_str: str, pop: int, seed: int, substrate="c2plus_v1",
             warm_days: int = 90):
    """Returns (world, vintage_report). The warm replays <=T GDELT news
    through the memory channel day by day."""
    from earth1.alive import birth_world, live_one_day
    from earth1.genesis import GENESIS_COUNTRY_CODES
    from earth1.memory import Memory
    from earth1.types import Force
    T = date.fromisoformat(T_str)
    report = {"T": T_str, "resolved": {}, "vintage_mismatch": [
        "c2plus_tables (WVS-7 joint structure)",
        "income_calibration (2021 PPP joint-MSM)",
        "gompertz mortality (current fit)",
        "religiosity_factbook (current snapshot)",
        "wb poverty/CDR/LE anchors (latest fetch)"]}
    geo, err = _vintage_geopol(T.year)
    report["resolved"]["unga_ideal_points"] = (
        {"countries": len(geo), "capped_at": T.year} if geo else err)
    un, err = _vintage_unemployment(T.year)
    report["resolved"]["wb_unemployment"] = un or err

    w = birth_world(pop, seed, substrate=substrate)
    rng = np.random.default_rng(seed)

    aggs, missing = gdelt_day_aggregates(T, warm_days)
    report["resolved"]["gdelt_warm"] = {
        "day_country_rows": len(aggs), "months_missing": missing}
    if missing:
        report["vintage_mismatch"].append(
            f"gdelt months missing {missing} (warm partial)")
    iso_idx = {iso: i for i, iso in enumerate(GENESIS_COUNTRY_CODES)}
    by_day = {}
    for (ds, iso2), quads in aggs.items():
        by_day.setdefault(ds, []).append((iso2, quads))
    days_sorted = sorted(by_day)
    # normalise volume: a country-day's mentions vs the warm's p95
    all_m = [sum(q) for rows in by_day.values() for _, q in rows]
    p95 = float(np.percentile(all_m, 95)) if all_m else 1.0

    start = T - timedelta(days=warm_days)
    for i in range(warm_days):
        d = start + timedelta(days=i + 1)
        live_one_day(w, rng)
        for iso2, quads in by_day.get(d.isoformat(), []):
            ci = iso_idx.get(iso2)
            if ci is None:
                continue
            vol = min(1.0, sum(quads) / max(p95, 1.0))
            sig = np.zeros(len(Force))
            for qi, cnt in enumerate(quads):
                if cnt <= 0:
                    continue
                share = cnt / max(sum(quads), 1)
                for fname, val in QUAD_FORCES[qi + 1].items():
                    sig[getattr(Force, fname.upper())] += val * share * vol
            if not np.any(sig):
                continue
            scope = w.civ.country == ci
            if not scope.any():
                continue
            w.chronicle.remember(Memory(
                id=f"gdelt:{d.isoformat()}:{iso2}",
                label=f"news {d.isoformat()} {iso2}",
                day=float(w.day), force_signature=sig, scope=scope,
                origin="historical_news", half_life=14.0))
    return w, report
