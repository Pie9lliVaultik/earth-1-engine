"""BACKTEST — let reality grade the consequence layer.

Three events whose outcomes are known. For each: put the world in front
of the event, apply it, live forward, and compare the consequences the
model produces against what was actually recorded.

Scored on DIRECTION, ORDER OF MAGNITUDE and RANKING — not on point
accuracy, because Earth-1's population is a synthetic present rather
than a historically initialised 2019/2008/2011. That limit is stated in
earth1/backtest.py and it is what the score means. Claiming point
accuracy from a world that did not start in the right year would be
the same error as reporting one CV fold as a benchmark.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.alive import birth_world, live_one_day
from earth1.backtest import REGISTRY, ranking_check, score
from earth1.branch import run

POP = int(os.environ.get("BT_POP", "12000"))
REPEATS = int(os.environ.get("BT_REPEATS", "3"))
WARM = int(os.environ.get("BT_WARM", "90"))
DAYS = int(os.environ.get("BT_DAYS", "180"))


def main() -> None:
    scale = 8.3e9 / POP
    print(f"\n  {POP:,} earthlings, scaled to 8.3B for comparison with the "
          f"recorded figures.")
    print(f"  {WARM} days of ordinary life first, then the event.\n",
          flush=True)

    w = birth_world(POP, 42)
    rng = np.random.default_rng(11)
    for _ in range(WARM):
        live_one_day(w, rng)

    scenarios = [e.scenario for e in REGISTRY]
    res = run(w, scenarios, days=DAYS, repeats=REPEATS, seed=13,
              progress=lambda m: print(f"    ...{m}", flush=True))

    scored = []
    for ev in REGISTRY:
        b = res["branches"].get(ev.scenario.id)
        if not b:
            continue
        s = score(ev, b["consequences"], scale)
        scored.append(s)

    print(f"\n{'=' * 74}")
    print("  BACKTEST — the consequence layer against recorded history")
    print(f"{'=' * 74}")
    for s in scored:
        print(f"\n  {s['label']}")
        for c in s["checks"]:
            mark = "ok " if c["within_tolerance"] else "OFF"
            print(f"    {mark} {c['quantity']:24s} model "
                  f"{c['predicted']:>14,.0f}  recorded {c['recorded']:>14,.0f}"
                  f"   {c['orders_of_magnitude_off']:.2f} orders off")
        if s["direction_score"] is not None:
            wrong = [k for k, v in s["direction_correct"].items() if not v]
            print(f"    direction {s['direction_score']:.0%} correct"
                  + (f"   WRONG: {', '.join(wrong)}" if wrong else ""))
        if s.get("governments_fell_recorded"):
            print(f"    governments: {s['governments_at_risk_predicted']} "
                  f"flagged at risk vs {s['governments_fell_recorded']} "
                  f"that actually fell")

    rank = ranking_check(scored)
    print(f"\n{'=' * 74}")
    print("  RANKING — the strongest test that does not need a historically")
    print("  initialised world: whatever the absolute figures, the pandemic")
    print("  should come out worse than the financial crisis, because it was.")
    print(f"{'=' * 74}")
    print(f"    expected  {rank['expected_order_by_job_losses']}")
    print(f"    model     {rank['model_order']}")
    print(f"    ORDER {'CORRECT' if rank['order_correct'] else 'WRONG'}")

    ds = [s["direction_score"] for s in scored
          if s["direction_score"] is not None]
    ms = [s["magnitude_score"] for s in scored
          if s["magnitude_score"] is not None]
    out = {"pop": POP, "scale": scale, "horizon_days": DAYS,
           "repeats": REPEATS, "scored": scored, "ranking": rank,
           "mean_direction_score": round(float(np.mean(ds)), 3) if ds else None,
           "mean_magnitude_score": round(float(np.mean(ms)), 3) if ms else None,
           "limit": ("scored on direction, order of magnitude and ranking "
                     "only — the population is a synthetic present, not a "
                     "historically initialised year")}
    json.dump(out, open("data/backtest.json", "w"), indent=1, default=str)

    print(f"\n  direction {out['mean_direction_score']}   "
          f"magnitude {out['mean_magnitude_score']}   "
          f"ranking {'pass' if rank['order_correct'] else 'fail'}")
    print("  Every recorded figure in the registry is an APPROXIMATE ANCHOR "
          "and\n  needs verification against its primary source before any "
          "published claim.\n")


if __name__ == "__main__":
    main()
