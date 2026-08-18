"""Meet an earthling. Follow their life. Read their possible futures."""
from __future__ import annotations
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from earth1.chaos import world_step
from earth1.fabric import build_fabric
from earth1.genesis import GENESIS_COUNTRIES, genesis
from earth1.life import EVENT_CODES, birth_life, life_tick
from earth1.observe import futures, observe

POP = int(os.environ.get("ME_POP", "20000"))
WARM = int(os.environ.get("ME_WARM", "180"))
BRANCHES = int(os.environ.get("ME_BRANCHES", "60"))
HORIZON = int(os.environ.get("ME_HORIZON", "180"))
ISO = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}

def main():
    civ = genesis(POP, 42); life = birth_life(civ, seed=42)
    fab = build_fabric(civ, life, seed=42); civ.adj = fab.adj
    rng = np.random.default_rng(7)
    kw = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)

    # let the world live for six months so people have histories
    diary = {}
    target = ISO.get(os.environ.get("ME_COUNTRY", "NG"))
    pool = np.flatnonzero((civ.country == target) & life.in_lf)
    who = int(pool[len(pool) // 3])
    for d in range(WARM):
        world_step(civ, life, rng, **kw)
        ev = int(life.last_event[who])
        if ev and (d == 0 or ev != diary.get("last")):
            diary.setdefault("events", []).append((d, EVENT_CODES[ev]))
            diary["last"] = ev

    me = observe(civ, life, who, fabric=fab)
    print(f"\n  {'='*66}")
    print(f"  EARTHLING #{me['id']} — {me['country']}, {me['age']:.0f} years old")
    print(f"  {'='*66}")
    print(f"  works as        {me['work']['occupation']}"
          f"{'' if me['work']['employed'] else '  (OUT OF WORK)'}")
    print(f"  in this job     {me['work']['years_in_job']:.1f} years"
          f"   | lost work {me['work']['times_lost_work']}x")
    print(f"  earns           {me['money']['wage_vs_survival_cost']:.2f}x "
          f"what survival costs")
    print(f"  savings         {me['money']['savings_days']:.0f} days of survival")
    s = me.get("self", {})
    if s:
        print(f"  health          mental {s['mental_health']:.2f}  "
              f"physical {s['physical_health']:.2f}"
              + (f"  ADDICTION {s['addiction']:.2f}" if s['addiction'] > 0.05 else ""))
        print(f"  connection      relationship {s['relationship']:.2f}  "
              f"unmet social need {s['unmet_social_need']:.2f}")
        print(f"  life has marked them {s['marks_left_by_life']} times; "
              f"last: {s['last_thing_that_happened']}")
    print(f"  knows           " + ", ".join(
        f"{v} {k}" for k, v in me["connections"].items() if v))
    print(f"  believes        " + "  ".join(
        f"{k[:4]} {v:.2f}" for k, v in me["forces"].items()))
    print(f"  conviction      {me['conviction']:.2f}")
    if diary.get("events"):
        print(f"\n  WHAT HAPPENED TO THEM (last {WARM} days)")
        for d, e in diary["events"][:8]:
            print(f"    day {d:3d}   {e}")

    print(f"\n  {BRANCHES} POSSIBLE FUTURES, {HORIZON} days each")
    f = futures(civ, life, who, n_branches=BRANCHES, days=HORIZON, step_kw=kw)
    print(f"    still employed at the end      {f['P_employed_at_end']:6.1%}")
    print(f"    jobless at some point          {f['P_ever_jobless']:6.1%}")
    print(f"    destitute at some point        {f['P_ever_destitute']:6.1%}")
    print(f"    isolated at the end            {f['P_isolated_at_end']:6.1%}")
    sv = f["savings_days"]
    print(f"    savings          p10 {sv['p10']:.0f}d | median "
          f"{sv['median']:.0f}d | p90 {sv['p90']:.0f}d")
    print(f"    fear             median {f['fear']['median']:.3f}  "
          f"(p10-p90 {f['fear']['spread_p10_p90'][0]:.3f}-"
          f"{f['fear']['spread_p10_p90'][1]:.3f})")
    if f["fear_if_destitute"] is not None:
        print(f"    fear if destitute {f['fear_if_destitute']:.3f} "
              f"vs {f['fear_if_not']:.3f} if not")
    json.dump(f, open("data/meet_an_earthling.json", "w"), indent=1)

if __name__ == "__main__":
    main()
