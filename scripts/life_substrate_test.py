"""LIFE SUBSTRATE TEST — does giving them biographies produce a tail?

Prereg: data/life_substrate_prereg.json, including the ways this build
is WRONG regardless of whether it produces tails.

Runs a year of material life on the real population and reports:
  1. does the force distribution widen, and is it a tail or clip-pileup
  2. does max rule participation clear 0.30 (Fix 1's knife-edge)
  3. does the participation sweep stop collapsing
  4. are unemployment and destitution at plausible magnitudes
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.event_log import EventLog
from earth1.genesis import GENESIS_COUNTRIES, genesis
from earth1.life import OCC_NAMES, birth_life, life_tick
from earth1.thresholds import (TRANSITION_RULES, _participation,
                               detect_transitions)
from earth1.types import Force

POP = int(os.environ.get("LIFE_POP", "200000"))
DAYS = int(os.environ.get("LIFE_DAYS", "365"))
SWEEP = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def participation_profile(civ):
    out = {}
    for rule in TRANSITION_RULES:
        if rule.region_scope != "regional":
            continue
        fr = [_participation(civ, civ.country == ci, rule)
              for ci in range(len(GENESIS_COUNTRIES))
              if (civ.country == ci).sum() >= 10]
        fr = np.array(fr)
        out[rule.name] = {"max": round(float(fr.max()), 4),
                          "mean": round(float(fr.mean()), 4),
                          "countries_over_30pct": int((fr >= 0.30).sum())}
    return out


def sweep(civ):
    s = {}
    for p in SWEEP:
        ev, _ = detect_transitions(civ, EventLog(), 0.0, mode="local",
                                   min_participation=p)
        s[str(p)] = len(ev)
    return s


def force_shape(civ):
    f = civ.forces
    return {n.name.lower(): {
        "std": round(float(f[:, n.value].std()), 4),
        "p01": round(float(np.percentile(f[:, n.value], 1)), 4),
        "p99": round(float(np.percentile(f[:, n.value], 99)), 4),
        "at_zero": round(float((f[:, n.value] <= 1e-9).mean()), 4),
        "at_one": round(float((f[:, n.value] >= 1 - 1e-9).mean()), 4),
    } for n in Force}


def main() -> None:
    civ = genesis(POP, 42)
    rng = np.random.default_rng(7)

    before_force = force_shape(civ)
    before_part = participation_profile(civ)
    before_sweep = sweep(civ)

    life = birth_life(civ, seed=42)
    hist = []
    for d in range(DAYS):
        st = life_tick(civ, life, rng, dt_days=1.0)
        if d % 60 == 0 or d == DAYS - 1:
            hist.append({"day": d, "unemployment": round(st["unemployment"], 4),
                         "deprived": round(st["deprived"], 4),
                         "destitute": round(st["destitute"], 4),
                         "median_buffer_days": round(
                             st["median_buffer_days"], 1),
                         "firms_failed": st["firms_failed"]})

    after_force = force_shape(civ)
    after_part = participation_profile(civ)
    after_sweep = sweep(civ)

    unemp = hist[-1]["unemployment"]
    destitute = hist[-1]["destitute"]
    max_part = max(v["max"] for v in after_part.values())
    econ = after_force["economics"]
    clip_pileup = econ["at_zero"] + econ["at_one"]

    # registered failure modes, checked in the order they were written
    fails = []
    if unemp > 0.35 or unemp < 0.02:
        fails.append(f"RUNAWAY: unemployment {unemp:.1%} outside [2%, 35%]")
    if clip_pileup > 0.50:
        fails.append(f"SATURATION NOT TAIL: {clip_pileup:.1%} of agents "
                     f"sit exactly on a clip bound")
    if destitute > 0.25:
        fails.append(f"DESTITUTION RUNAWAY: {destitute:.1%} destitute")
    if max_part < 0.30:
        fails.append(f"NO EFFECT: max participation {max_part:.3f} still "
                     f"under 0.30")
    verdict = "PASS" if not fails else "FAIL: " + "; ".join(fails)

    out = {"prereg": "data/life_substrate_prereg.json", "pop": POP,
           "days": DAYS, "history": hist,
           "force_before": before_force, "force_after": after_force,
           "participation_before": before_part,
           "participation_after": after_part,
           "sweep_before": before_sweep, "sweep_after": after_sweep,
           "occupation_mix": {OCC_NAMES[i]: int((life.occupation == i).sum())
                              for i in range(len(OCC_NAMES))},
           "verdict": verdict}
    json.dump(out, open("data/life_substrate_test.json", "w"), indent=1)

    print(f"\n  {POP:,} agents, {DAYS} days of material life\n")
    print("  LABOUR MARKET")
    for h in hist:
        print(f"    day {h['day']:4d}  unemployment {h['unemployment']:6.1%}"
              f"  deprived {h['deprived']:6.1%}  destitute "
              f"{h['destitute']:6.1%}  buffer {h['median_buffer_days']:7.1f}d"
              f"  firms lost {h['firms_failed']}")
    print("\n  FORCE DISTRIBUTION (std, and pileup on the clip bounds)")
    for k in ["economics", "fear", "desire", "collective"]:
        b, a = before_force[k], after_force[k]
        print(f"    {k:11s} std {b['std']:.4f} -> {a['std']:.4f}   "
              f"p01 {a['p01']:.3f} p99 {a['p99']:.3f}   "
              f"at_0 {a['at_zero']:.1%} at_1 {a['at_one']:.1%}")
    print("\n  PARTICIPATION (max across 194 countries)")
    for k in after_part:
        print(f"    {k:20s} {before_part[k]['max']:.3f} -> "
              f"{after_part[k]['max']:.3f}   countries>=30%: "
              f"{after_part[k]['countries_over_30pct']}")
    print("\n  THRESHOLD SWEEP  (events fired)")
    print(f"    {'p':>6s} {'before':>8s} {'after':>8s}")
    for p in SWEEP:
        print(f"    {p:6.2f} {before_sweep[str(p)]:8d} "
              f"{after_sweep[str(p)]:8d}")
    print(f"\nLIFE SUBSTRATE VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
