"""FIND THE RESOLUTION THAT WORKS. Do not stop at the first failure.

The instruction: build stratified allocation, run the noise floor, and
do not come back until the geography works or is proven impossible. If
stratification does not fix it, use more agents. If more agents do not
fix it, aggregate to regions. If regions do not work, find the
resolution that does and build the product there.

So this escalates through the ladder automatically and reports the
FIRST rung that clears, rather than reporting a failure and stopping:

  1  country, current allocation          (the baseline that failed)
  2  country, high floor  (stratified — every country >= FLOOR agents)
  3  country, high floor + more agents
  4  REGION  (~20 blocs instead of 194 countries)
  5  INCOME TIER (4 blocs) — the coarsest resolution that still says
                  something a decision-maker can act on

A rung PASSES when the noise floor — the same scenario run twice with
different dice — clears +0.5 rank correlation on the FULL vector, which
is the threshold registered before any of this was measured.

The correlation is computed on every unit, never on a top-k list.
Comparing two top-5 lists out of 194 and zero-padding their union
manufactures a large negative number whatever the underlying signal is,
which is what produced the earlier false 'chaotic' verdict.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.alive import birth_world, live_one_day
from earth1.branch import run
from earth1.consequences import snapshot

DAYS = int(os.environ.get("FR_DAYS", "45"))
WARM = int(os.environ.get("FR_WARM", "45"))
PASS_BAR = 0.50

SC = None   # set in main from hormuz


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / d) if d > 0 else 0.0


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(-a)).astype(float)
    rb = np.argsort(np.argsort(-b)).astype(float)
    return _pearson(ra, rb)


def _bloc_map(kind: str) -> np.ndarray:
    """Which bloc each country belongs to, for coarser resolutions."""
    from earth1.genesis import GENESIS_COUNTRIES
    if kind == "country":
        return np.arange(len(GENESIS_COUNTRIES))
    if kind == "region":
        regs = sorted({str(c.get("region", "?")) for c in GENESIS_COUNTRIES})
        idx = {r: i for i, r in enumerate(regs)}
        return np.array([idx[str(c.get("region", "?"))]
                         for c in GENESIS_COUNTRIES])
    if kind == "tier":
        order = ["HIC", "UMIC", "LMIC", "LIC"]
        return np.array([order.index(c.get("income", "LMIC"))
                         if c.get("income") in order else 2
                         for c in GENESIS_COUNTRIES])
    raise ValueError(kind)


def measure_floor(pop: int, floor: int, resolution: str,
                  log=print) -> dict:
    """Noise floor: same scenario, different dice, at this configuration."""
    import earth1.genesis as G

    old_default = G.genesis.__defaults__
    def make():
        return birth_world_with_floor(pop, floor)

    w = make()
    rng = np.random.default_rng(11)
    for _ in range(WARM):
        live_one_day(w, rng)

    a = run(w, [SC], days=DAYS, repeats=2, seed=101)
    b = run(w, [SC], days=DAYS, repeats=2, seed=907)
    va = np.array(a["branches"][SC.id]["consequences"]
                  ["jobless_rate_change_by_country"])
    vb = np.array(b["branches"][SC.id]["consequences"]
                  ["jobless_rate_change_by_country"])

    blocs = _bloc_map(resolution)
    nb = int(blocs.max()) + 1
    # aggregate the RATE change up to the bloc, weighted by agents
    counts = np.bincount(w.civ.country, minlength=len(blocs)).astype(float)
    ga = np.bincount(blocs, weights=va * counts, minlength=nb) / \
        np.maximum(np.bincount(blocs, weights=counts, minlength=nb), 1e-9)
    gb = np.bincount(blocs, weights=vb * counts, minlength=nb) / \
        np.maximum(np.bincount(blocs, weights=counts, minlength=nb), 1e-9)

    keep = (np.bincount(blocs, weights=counts, minlength=nb) > 0)
    rc = _spearman(ga[keep], gb[keep])
    pr = _pearson(ga[keep], gb[keep])
    per_unit = float(np.bincount(blocs, weights=counts,
                                 minlength=nb)[keep].mean())
    return {"pop": pop, "floor": floor, "resolution": resolution,
            "units": int(keep.sum()), "agents_per_unit": round(per_unit, 0),
            "rank_correlation": round(rc, 4),
            "pearson": round(pr, 4),
            "passes": bool(rc >= PASS_BAR)}


def birth_world_with_floor(pop: int, floor: int):
    """A world whose country allocation uses a raised minimum.

    This is stratified allocation: every country gets at least `floor`
    agents so that small countries are estimable at all, and census
    weights (already in genesis) restore population-true global totals.
    """
    import earth1.genesis as G
    orig = G._allocate_countries

    def patched(total, min_per_country=floor):
        return orig(total, floor)

    G._allocate_countries = patched
    try:
        w = birth_world(pop, 42)
    finally:
        G._allocate_countries = orig
    return w


def main() -> None:
    global SC
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hormuz import SCENARIOS
    SC = SCENARIOS[1]

    ladder = [
        ("country", 200_000, 500),      # the baseline that failed
        ("country", 200_000, 1_000),    # stratified
        ("country", 600_000, 3_000),    # stratified + more agents
        ("region", 200_000, 500),       # coarser resolution
        ("tier", 200_000, 500),         # coarsest that still says something
    ]
    print(f"\n  Escalating until the geography works. Bar: rank "
          f"correlation >= {PASS_BAR:+.2f} on the FULL vector.\n")
    print(f"  {'resolution':>10s} {'agents':>9s} {'floor':>7s} {'units':>6s} "
          f"{'per unit':>9s} {'rank':>7s} {'pearson':>8s}")
    rows = []
    winner = None
    for res, pop, floor in ladder:
        r = measure_floor(pop, floor, res)
        rows.append(r)
        mark = "  <== WORKS" if r["passes"] else ""
        print(f"  {res:>10s} {pop:9,d} {floor:7,d} {r['units']:6d} "
              f"{r['agents_per_unit']:9,.0f} {r['rank_correlation']:+7.3f} "
              f"{r['pearson']:+8.3f}{mark}", flush=True)
        if r["passes"] and winner is None:
            winner = r
            break

    out = {"bar": PASS_BAR, "ladder": rows, "winner": winner}
    json.dump(out, open("data/find_the_resolution.json", "w"), indent=1)
    if winner:
        print(f"\n  THE PRODUCT RESOLUTION IS: {winner['resolution'].upper()}"
              f" — {winner['units']} units, "
              f"{winner['agents_per_unit']:,.0f} agents each, "
              f"rank correlation {winner['rank_correlation']:+.3f}")
    else:
        print(f"\n  No rung cleared {PASS_BAR:+.2f}. Best was "
              f"{max(rows, key=lambda r: r['rank_correlation'])}")


if __name__ == "__main__":
    main()
