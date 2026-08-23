"""DOES THE CHAOS HAVE GEOGRAPHY?

Pietro, 2026-08-18: "A job loss in Lagos should propagate differently
from one in Stockholm, through different network structures, at
different speeds, along different force channels."

Same physics, same perturbation, different country. The population is
built on the structured social fabric, so household size, workplace
structure and locality all vary the way they vary on Earth.

Then ABLATION: rerun with one tie type removed at a time. Whatever the
removal costs is what that channel was carrying.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 0.2 MIGRATION NOTE: this instrument now steps THE canonical loop
# (chaos.world_step delegates to alive.live_one_day over a full World).
# Its numbers are NOT comparable with any measured before 0.2 - the
# instrument itself changed. 0.8 re-runs every measurement from scratch.
from earth1.chaos import world_step
from earth1.fabric import build_fabric
from earth1.alive import birth_world
from earth1.genesis import GENESIS_COUNTRIES

POP = int(os.environ.get("PG_POP", "60000"))
DAYS = int(os.environ.get("PG_DAYS", "25"))
LIVING = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)
ISO = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
TFR = {c["iso2"]: c.get("tfr") for c in GENESIS_COUNTRIES}
COUNTRIES = ["NE", "NG", "IN", "US", "SE", "JP"]


def build(drop=None, keep=None):
    w = birth_world(POP, 42)
    civ, life = w.civ, w.life
    fab = build_fabric(civ, life, seed=42)
    if keep:
        civ.adj = fab.by_type[keep].tocsr()
    elif drop:
        tot = None
        for k, m in fab.by_type.items():
            if k == drop:
                continue
            tot = m if tot is None else tot + m
        civ.adj = tot.tocsr()
    else:
        civ.adj = fab.adj
    w.fabric = fab
    return w


def probe(iso2, drop=None, keep=None):
    ci = ISO[iso2]
    wA = build(drop, keep); wB = build(drop, keep)
    cA, lA, cB, lB = wA.civ, wA.life, wB.civ, wB.life
    rA = np.random.default_rng(1234); rB = np.random.default_rng(1234)
    here = np.flatnonzero((cB.country == ci) & lB.employed)
    if here.size == 0:
        return None
    who = int(here[len(here) // 2])
    lB.employed[who] = False; lB.firm[who] = -1
    lB.tenure[who] = 0.0; lB.spells[who] += 1
    hm = cA.country == ci
    home_curve, world_curve = [], []
    for _ in range(DAYS):
        world_step(wA, rA, **LIVING); world_step(wB, rB, **LIVING)
        d = np.abs(cA.forces - cB.forces).max(axis=1) > 1e-12
        home_curve.append(float(d[hm].mean()))
        world_curve.append(float(d.mean()))
    hc = np.array(home_curve)
    t50 = int(np.argmax(hc >= 0.5)) + 1 if (hc >= 0.5).any() else None
    return {"country": iso2, "tfr": TFR.get(iso2),
            "n_agents": int(hm.sum()),
            "days_to_half_of_home": t50,
            "max_home_reach": round(float(hc.max()), 4),
            "max_world_reach": round(float(max(world_curve)), 4),
            "day3_home": round(float(hc[2]), 4)}


def main():
    print(f"\n  {POP:,} agents on the structured fabric. One person "
          f"loses their job.\n")
    print(f"  {'':4s} {'tfr':>5s} {'agents':>7s} {'day3 home':>10s} "
          f"{'t->50% home':>12s} {'max home':>9s} {'max world':>10s}")
    rows = []
    for cc in COUNTRIES:
        r = probe(cc)
        if not r:
            continue
        rows.append(r)
        t = f"{r['days_to_half_of_home']}d" if r["days_to_half_of_home"] else "never"
        print(f"  {cc:4s} {str(r['tfr']):>5s} {r['n_agents']:7,d} "
              f"{r['day3_home']:9.1%} {t:>12s} {r['max_home_reach']:8.1%} "
              f"{r['max_world_reach']:9.1%}", flush=True)

    # KEEP-ONLY ablation. Removing one channel of five leaves four
    # redundant paths and tells you almost nothing. Isolating a single
    # channel tells you what that channel can carry ON ITS OWN, which is
    # the question worth asking.
    abl = []
    for cc in ("NG", "SE"):
        print(f"\n  KEEP-ONLY — what each channel carries alone ({cc}, "
              f"tfr {TFR.get(cc)})")
        print(f"  {'only channel':>13s} {'day3 home':>10s} "
              f"{'t->50% home':>12s} {'max home':>9s} {'max world':>10s}")
        for keep in [None, "household", "colleagues", "neighbours",
                     "friends", "weak"]:
            r = probe(cc, keep=keep)
            if not r:
                continue
            r["only"] = keep or "all channels"
            abl.append(r)
            t = f"{r['days_to_half_of_home']}d" if r["days_to_half_of_home"] else "never"
            print(f"  {r['only']:>13s} {r['day3_home']:9.1%} {t:>12s} "
                  f"{r['max_home_reach']:8.1%} {r['max_world_reach']:9.1%}",
                  flush=True)

    json.dump({"pop": POP, "days": DAYS, "countries": rows,
               "ablation_NG": abl},
              open("data/propagation_geography.json", "w"), indent=1)
    fast = min((r for r in rows if r["days_to_half_of_home"]),
               key=lambda r: r["days_to_half_of_home"], default=None)
    slow = max((r for r in rows if r["days_to_half_of_home"]),
               key=lambda r: r["days_to_half_of_home"], default=None)
    if fast and slow:
        print(f"\nGEOGRAPHY VERDICT: fastest {fast['country']} "
              f"({fast['days_to_half_of_home']}d, tfr {fast['tfr']}), "
              f"slowest {slow['country']} ({slow['days_to_half_of_home']}d, "
              f"tfr {slow['tfr']})")

if __name__ == "__main__":
    main()
