"""SCRUB — go to a moment the world actually lived, and walk around in it.

The real world lives once. This one lives once and remembers, so you can
put yourself inside a specific day, look at the state of every country,
pick a person and read their life, and then branch forward from exactly
there.

  scrub.py --list                       what days exist
  scrub.py --at 2020-02-11              stand in that day
  scrub.py --at 2020-02-11 --agent 1823 read one life
  scrub.py --at 2020-02-11 --country NG that country, in that moment
  scrub.py --at 2020-02-11 --branch     fork the future from there

Nobody can do this for the real world. Historians reconstruct,
journalists narrate, economists model. None of them can put you inside
Tuesday 11 February 2020 and let you walk around.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1 import timeline
from earth1.consequences import protest_risk, snapshot
from earth1.observe import observe
from earth1.types import Force


def show_world(w, when: str) -> None:
    from earth1.genesis import GENESIS_COUNTRIES
    s = snapshot(w)
    alive = w.health.alive
    print(f"\n  {'=' * 66}")
    print(f"  EARTH-1 on {when}   (world-day {w.day:,})")
    print(f"  {'=' * 66}")
    print(f"    living            {s['population']:,}")
    print(f"    working           {s['employed']:,}"
          f"    out of work {s['unemployed']:,}")
    print(f"    destitute         {s['destitute']:,}"
          f"    hungry {s['hungry']:,}")
    print(f"    homeless          {s['homeless']:,}"
          f"    displaced {s['migrants']:,}")
    print(f"    countries at war  {s['at_war']}")
    print(f"    median savings    {s['median_buffer']:.0f} days of survival")
    if s["mean_hope"] is not None:
        print(f"    hope              {s['mean_hope']:.3f}")
    if w.chronicle is not None:
        print(f"    remembered events {len(w.chronicle.events)}"
              f"   forgotten {w.chronicle.forgotten}")
        live = sorted(w.chronicle.events, key=lambda m: -m.salience)[:4]
        for m in live:
            print(f"      still felt: {m.label[:52]:54s} "
                  f"salience {m.salience:.3f}")
    # where it hurts most, by country
    names = [c["name"] for c in GENESIS_COUNTRIES]
    share = s["jobless_by_country"] / s["workers_by_country"]
    worst = np.argsort(-share)[:5]
    print("    worst joblessness " + ", ".join(
        f"{names[i]} {share[i]:.0%}" for i in worst if share[i] > 0))
    pr = protest_risk(w)
    hot = np.argsort(-pr)[:5]
    if pr[hot[0]] > 0:
        print("    protest risk      " + ", ".join(
            names[i] for i in hot if pr[i] > 0))


def show_country(w, iso2: str) -> None:
    from earth1.genesis import GENESIS_COUNTRIES
    iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
    if iso2 not in iso:
        print(f"  no country {iso2}")
        return
    i = iso[iso2]
    m = (w.civ.country == i) & w.health.alive
    if not m.any():
        print(f"  nobody alive in {iso2}")
        return
    life, fl = w.life, w.flourishing
    print(f"\n  {GENESIS_COUNTRIES[i]['name']} ({iso2}) — {int(m.sum()):,} people")
    print(f"    unemployment      "
          f"{float((~life.employed[m] & life.in_lf[m]).sum()) / max(life.in_lf[m].sum(), 1):.1%}")
    print(f"    destitute         {float((life.deprivation[m] > 0.99).mean()):.1%}")
    print(f"    homeless          {float(w.klass.homeless[m].mean()):.2%}")
    print(f"    mental illness    {float((life.mental[m] < 0.45).mean()):.1%}")
    if fl is not None:
        print(f"    hungry            {float((fl.hunger[m] > 0.5).mean()):.1%}")
        print(f"    hope              {float(fl.hope[m].mean()):.3f}"
              f"   meaning {float(fl.meaning[m].mean()):.3f}")
    print(f"    government        welfare {w.gov.welfare[i]:.2f}"
          f"  policing {w.gov.policing[i]:.2f}"
          f"  legitimacy {w.gov.legitimacy[i]:.2f}"
          + ("  AT WAR" if w.gov.at_war_with[i] >= 0 else ""))
    print("    forces            " + "  ".join(
        f"{f.name.lower()[:4]} {w.civ.forces[m, f].mean():.2f}" for f in Force))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--at", default=None)
    ap.add_argument("--agent", type=int, default=None)
    ap.add_argument("--country", default=None)
    ap.add_argument("--branch", action="store_true")
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args()

    avail = timeline.available()
    if args.list or not args.at:
        if not avail:
            print(f"\n  no timeline yet. build one:\n"
                  f"    python3 scripts/build_timeline.py\n")
            return
        print(f"\n  {len(avail)} moments you can stand in:")
        print(f"    {avail[0]} ... {avail[-1]}")
        for d in avail[::max(len(avail) // 12, 1)]:
            print(f"      {d}")
        return

    w = timeline.restore(args.at)
    show_world(w, args.at)
    if args.country:
        show_country(w, args.country)
    if args.agent is not None:
        me = observe(w.civ, w.life, args.agent, fabric=w.fabric)
        print(f"\n  EARTHLING #{me['id']} on {args.at}")
        print(json.dumps(me, indent=2)[:2000])
    if args.branch:
        from earth1.branch import Scenario, run
        print(f"\n  branching {args.days} days from {args.at}...")
        sc = [Scenario(id="shock", label="A generic severe shock",
                       forces={"fear": 0.35, "economics": -0.30},
                       countries=None, firm_damage=0.25, trade_shock=0.15)]
        res = run(w, sc, days=args.days, repeats=2, seed=5)
        c = res["branches"]["shock"]["uncertainty"]
        print(f"    jobs lost {c['jobs_lost']['median']:,.0f} "
              f"(range {c['jobs_lost']['low']:,.0f}–"
              f"{c['jobs_lost']['high']:,.0f})")


if __name__ == "__main__":
    main()
