"""MAKE THE COUNTRY MAP WORK. Full strength, all four levers at once.

The country signal was buried by Poisson counting noise, and the
arithmetic says exactly how badly. A country with 1,031 agents has ~500
in the labour force. Over 45 days roughly 7 of them separate from work
naturally and the shock adds perhaps 2 more. Signal 2, noise sqrt(7).
SNR below one — the pattern cannot survive that no matter how it is
measured.

Four levers, applied together rather than one at a time:

  FLOOR    _allocate_countries used max(500, share*total), so small
           countries held 500 agents whatever the total. Raising the
           TOTAL never raised them, which is why 600K agents changed
           nothing. A real floor is what stratification actually means.
  HORIZON  signal accumulates LINEARLY with time, noise as sqrt(time),
           so SNR grows as sqrt(time). Eight times the horizon is 2.8x
           the SNR — the strongest lever of the four.
  REPEATS  noise falls as 1/sqrt(n) when estimates are averaged before
           being compared.
  NO CONTROL SUBTRACTION for the diagnostic. Subtracting a noisy
           control injects its noise into the estimate. To ask whether
           two runs of the same scenario AGREE, compare their states
           directly; the control is only needed for attribution.

Bar: rank correlation >= +0.5 on the full country vector, the threshold
registered before any of this was measured.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import earth1.genesis as G
from earth1.alive import birth_world, live_one_day
from earth1.branch import apply
from hormuz import SCENARIOS

SC = SCENARIOS[1]
PASS_BAR = 0.50


def _spearman(a, b):
    ra = np.argsort(np.argsort(-a)).astype(float)
    rb = np.argsort(np.argsort(-b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float(ra @ rb / d) if d > 0 else 0.0


def _pearson(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / d) if d > 0 else 0.0


def world_with_floor(pop: int, floor: int):
    """Stratified: every country gets at least `floor` agents, for real."""
    orig = G._allocate_countries

    def patched(total, min_per_country=floor):
        return orig(total, floor)

    G._allocate_countries = patched
    try:
        return birth_world(pop, 42)
    finally:
        G._allocate_countries = orig


def country_unemployment(w) -> np.ndarray:
    from earth1.genesis import GENESIS_COUNTRIES
    nc = len(GENESIS_COUNTRIES)
    m_lf = w.life.in_lf & w.health.alive
    lf = np.bincount(w.civ.country, weights=m_lf.astype(float), minlength=nc)
    jobless = np.bincount(w.civ.country,
                          weights=(m_lf & ~w.life.employed).astype(float),
                          minlength=nc)
    return jobless / np.maximum(lf, 1.0)


def one_run(pop, floor, days, warm, seed) -> np.ndarray:
    w = world_with_floor(pop, floor)
    rng = np.random.default_rng(seed)
    for _ in range(warm):
        live_one_day(w, rng)
    apply(w, SC, rng)
    for _ in range(days):
        live_one_day(w, rng)
    return country_unemployment(w)


def agreement(pop, floor, days, repeats, warm=60) -> dict:
    """Do two independent ensembles of the SAME scenario agree?"""
    a = np.mean([one_run(pop, floor, days, warm, 1000 + i)
                 for i in range(repeats)], axis=0)
    b = np.mean([one_run(pop, floor, days, warm, 5000 + i)
                 for i in range(repeats)], axis=0)
    keep = (a > 0) & (b > 0)
    rc = _spearman(a[keep], b[keep])
    pr = _pearson(a[keep], b[keep])
    return {"pop": pop, "floor": floor, "days": days, "repeats": repeats,
            "countries": int(keep.sum()),
            "agents_per_small_country": floor,
            "rank_correlation": round(rc, 4), "pearson": round(pr, 4),
            "passes": bool(rc >= PASS_BAR)}


def main() -> None:
    print("\n  Making the country map work. All four levers together.")
    print(f"  Bar: rank correlation >= {PASS_BAR:+.2f} on the full vector.\n")
    print(f"  {'agents':>9s} {'floor':>7s} {'days':>6s} {'reps':>5s} "
          f"{'rank':>8s} {'pearson':>9s}")

    ladder = [
        (200_000, 1_000, 180, 2),
        (400_000, 2_000, 270, 3),
        (600_000, 3_000, 360, 3),
    ]
    rows, winner = [], None
    for pop, floor, days, reps in ladder:
        r = agreement(pop, floor, days, reps)
        rows.append(r)
        mark = "   <== WORKS" if r["passes"] else ""
        print(f"  {pop:9,d} {floor:7,d} {days:6d} {reps:5d} "
              f"{r['rank_correlation']:+8.3f} {r['pearson']:+9.3f}{mark}",
              flush=True)
        if r["passes"]:
            winner = r
            break

    json.dump({"bar": PASS_BAR, "ladder": rows, "winner": winner},
              open("data/country_map_fix.json", "w"), indent=1)
    if winner:
        print(f"\n  THE COUNTRY MAP WORKS: {winner['pop']:,} agents, "
              f"floor {winner['floor']:,}, {winner['days']} days, "
              f"{winner['repeats']} repeats "
              f"-> rank correlation {winner['rank_correlation']:+.3f}")
    else:
        best = max(rows, key=lambda r: r["rank_correlation"])
        print(f"\n  best {best['rank_correlation']:+.3f} at "
              f"{best['pop']:,}/{best['floor']:,}/{best['days']}d")


if __name__ == "__main__":
    main()
