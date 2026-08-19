"""ATTACK THE SIGNAL-TO-NOISE DIRECTLY.

Resolution and sample size both failed to move the country-level noise
floor off zero. That points somewhere else: the effect may simply be
small relative to the churn of a living world over a short horizon, in
which case the fix is not more agents but more SIGNAL and less NOISE.

Two levers, both cheap, neither tried yet:

  HORIZON   a shock's effect ACCUMULATES. Over 45 days a country's
            unemployment barely moves relative to its ordinary daily
            churn; over 360 days the shock has had time to compound
            through firms, savings and government response.
  REPEATS   noise falls as 1/sqrt(n). Each country estimate is
            currently a single run. Averaging several before comparing
            attacks the variance directly, which is what an ensemble is
            for and is exactly how the global aggregates became stable.

Both are measured against the same unchanged diagnostic: the same
scenario, different dice, rank correlation on the FULL country vector.
A rung passes at +0.5.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from earth1.alive import birth_world, live_one_day
from earth1.branch import run
from hormuz import SCENARIOS

SC = SCENARIOS[1]
POP = int(os.environ.get("SNR_POP", "200000"))
PASS_BAR = 0.50


def _spearman(a, b):
    ra = np.argsort(np.argsort(-a)).astype(float)
    rb = np.argsort(np.argsort(-b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.linalg.norm(ra) * np.linalg.norm(rb)
    return float(ra @ rb / d) if d > 0 else 0.0


def floor_at(days: int, repeats: int, warm: int = 45) -> dict:
    w = birth_world(POP, 42)
    rng = np.random.default_rng(11)
    for _ in range(warm):
        live_one_day(w, rng)
    a = run(w, [SC], days=days, repeats=repeats, seed=101)
    b = run(w, [SC], days=days, repeats=repeats, seed=907)

    def vec(res):
        # average the country vector across ALL repeats — this is the
        # variance reduction that a single run cannot have
        runs = res["branches"][SC.id]["runs"]
        arrs = [np.array(r["jobless_rate_change_by_country"]) for r in runs
                if r.get("jobless_rate_change_by_country")]
        if not arrs:
            arrs = [np.array(res["branches"][SC.id]["consequences"]
                             ["jobless_rate_change_by_country"])]
        return np.mean(arrs, axis=0)

    va, vb = vec(a), vec(b)
    keep = (np.abs(va) + np.abs(vb)) > 0
    rc = _spearman(va[keep], vb[keep]) if keep.sum() > 5 else 0.0
    return {"days": days, "repeats": repeats, "units": int(keep.sum()),
            "rank_correlation": round(rc, 4),
            "passes": bool(rc >= PASS_BAR)}


def main() -> None:
    print(f"\n  {POP:,} agents. Attacking signal-to-noise instead of "
          f"resolution.")
    print(f"  Bar: rank correlation >= {PASS_BAR:+.2f} on the full "
          f"country vector.\n")
    print(f"  {'days':>6s} {'repeats':>8s} {'units':>6s} {'rank':>8s}")
    ladder = [(45, 2), (180, 2), (180, 5), (360, 5), (360, 10)]
    rows, winner = [], None
    for days, reps in ladder:
        r = floor_at(days, reps)
        rows.append(r)
        mark = "   <== WORKS" if r["passes"] else ""
        print(f"  {days:6d} {reps:8d} {r['units']:6d} "
              f"{r['rank_correlation']:+8.3f}{mark}", flush=True)
        if r["passes"]:
            winner = r
            break
    json.dump({"bar": PASS_BAR, "pop": POP, "ladder": rows,
               "winner": winner},
              open("data/snr_ladder.json", "w"), indent=1)
    if winner:
        print(f"\n  COUNTRY MAP WORKS at {winner['days']} days x "
              f"{winner['repeats']} repeats — rank correlation "
              f"{winner['rank_correlation']:+.3f}")
    else:
        best = max(rows, key=lambda r: r["rank_correlation"])
        print(f"\n  best so far: {best['days']}d x {best['repeats']} "
              f"= {best['rank_correlation']:+.3f}")


if __name__ == "__main__":
    main()
