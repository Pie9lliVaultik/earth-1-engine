"""FIX 1 TEST — local thresholds vs national-mean thresholds.

Prereg: data/fix1_local_thresholds_prereg.json (registered before this
ran, including the failure modes).

Identical population, identical rules, identical t. The ONLY difference
is whether a rule is evaluated against the country's force MEAN or
against the fraction of agents who personally satisfy it.

Reports the sweep over min_participation so it is visible whether the
result depends on the chosen 0.25.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.event_log import EventLog
from earth1.genesis import GENESIS_COUNTRIES, genesis
from earth1.thresholds import (MIN_PARTICIPATION, TRANSITION_RULES,
                               _participation, detect_transitions)

POP = int(os.environ.get("FIX1_POP", "200000"))
SWEEP = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40]


def main() -> None:
    civ = genesis(POP, 42)
    n_reg = sum(1 for r in TRANSITION_RULES if r.region_scope == "regional")
    n_countries = len(GENESIS_COUNTRIES)
    pairs = n_reg * n_countries

    nat, _ = detect_transitions(civ, EventLog(), 0.0, mode="national")
    loc, _ = detect_transitions(civ, EventLog(), 0.0, mode="local")

    # the participation distribution itself — this is what the mean hid
    per_rule = {}
    for rule in TRANSITION_RULES:
        if rule.region_scope != "regional":
            continue
        fr = []
        for ci in range(n_countries):
            m = civ.country == ci
            if m.sum() >= 10:
                fr.append(_participation(civ, m, rule))
        fr = np.array(fr)
        per_rule[rule.name] = {
            "max_country_participation": round(float(fr.max()), 4),
            "mean_country_participation": round(float(fr.mean()), 4),
            "countries_over_25pct": int((fr >= 0.25).sum()),
            "n_countries": int(len(fr))}

    sweep = {}
    for p in SWEEP:
        ev, _ = detect_transitions(civ, EventLog(), 0.0,
                                   mode="local", min_participation=p)
        sweep[str(p)] = {"fired": len(ev),
                         "pct_of_rule_country_pairs": round(
                             len(ev) / max(pairs, 1), 4)}

    fired_frac = len(loc) / max(pairs, 1)
    fires_on_everything = fired_frac > 0.50
    fires_on_nothing = len(loc) == 0
    # knife-edge: does the fire count collapse across the 0.20-0.30 band?
    a, b = sweep["0.2"]["fired"], sweep["0.3"]["fired"]
    knife_edge = (a > 0 and b == 0) or (a > 0 and b / max(a, 1) < 0.10)

    verdict = ("FAIL: fires on everything" if fires_on_everything else
               "FAIL: fires on nothing" if fires_on_nothing else
               "FAIL: knife-edge on the free parameter" if knife_edge else
               "PASS")

    out = {"prereg": "data/fix1_local_thresholds_prereg.json", "pop": POP,
           "min_participation": MIN_PARTICIPATION,
           "rule_country_pairs": pairs,
           "national_fired": len(nat), "local_fired": len(loc),
           "local_fired_pct_of_pairs": round(fired_frac, 4),
           "participation_by_rule": per_rule, "sweep": sweep,
           "verdict": verdict}
    json.dump(out, open("data/fix1_local_thresholds.json", "w"), indent=1)

    print(f"  population {POP:,} | {pairs} (rule x country) pairs\n")
    print("  PARTICIPATION — what the national mean was hiding:")
    for k, v in per_rule.items():
        print(f"    {k:20s} max {v['max_country_participation']:.3f}  "
              f"mean {v['mean_country_participation']:.3f}  "
              f"countries>=25%: {v['countries_over_25pct']}/"
              f"{v['n_countries']}")
    print(f"\n  NATIONAL-MEAN detector fired : {len(nat)}")
    print(f"  LOCAL detector fired         : {len(loc)} "
          f"({fired_frac:.1%} of pairs)")
    print("\n  SWEEP over min_participation:")
    for p, v in sweep.items():
        print(f"    {p:>5s} -> {v['fired']:4d} events "
              f"({v['pct_of_rule_country_pairs']:.1%} of pairs)")
    print(f"\nFIX 1 VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
