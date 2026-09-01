"""UKR-2022 food-shock run (prereg ops/alive/UKR2022_FOOD_PREREG.md).
usage: ukr2022_run.py worker <i> <n> | assemble"""
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = "/opt/earth1-data/ukr2022"
BASE = "/opt/earth1-data/five/base200k.pkl"
SEEDS = list(range(21, 37))          # 16 seeds, report grade


def scenario():
    from earth1.branch import Scenario
    return Scenario(id="ukr2022_food", label="2022 global food-price spike "
                    "(registered 20% dose, prereg UKR2022_FOOD_PREREG.md)",
                    forces={"fear": 0.10, "economics": -0.10},
                    countries=None, firm_damage=0.0, trade_shock=0.20,
                    persists_days=180)


def worker(i, n):
    from earth1 import persistence
    from earth1.adapters.consequences import _run_pair
    os.makedirs(OUT, exist_ok=True)
    w, _, _ = persistence.load_world(BASE)
    for j, s in enumerate(SEEDS):
        if j % n != i:
            continue
        p = os.path.join(OUT, f"pair_{s}.pkl")
        if os.path.exists(p):
            continue
        pair, _ = _run_pair(scenario(), w, s, 180)
        pickle.dump(pair, open(p, "wb"), protocol=4)
        print("PAIR DONE", s, flush=True)


def assemble():
    from earth1 import persistence
    from earth1.adapters.consequences import build_from_runs
    from earth1.genesis import GENESIS_COUNTRY_CODES
    import numpy as np
    w, _, _ = persistence.load_world(BASE)
    runs = [pickle.load(open(os.path.join(OUT, f"pair_{s}.pkl"), "rb"))
            for s in SEEDS if os.path.exists(os.path.join(OUT, f"pair_{s}.pkl"))]
    rep = build_from_runs({"question_id": "ukr2022_food", "class": "protest",
                           "scenario": scenario()}, runs, [],
                          SEEDS[:len(runs)], int(w.civ.n), float(w.day))
    # per-country hungry deltas at day 90 (M2/M3 need country resolution;
    # snapshot() lacks hungry_by_country, so recompute from destitute_by_
    # country proxy is WRONG — use the recorded per-country force? NO:
    # hungry by country comes from the paired snaps' hungry via... not
    # stored per-country. Registered fallback: per-country force-shift
    # ranking (order1 movers, full list) stands in for geography until a
    # hungry_by_country field is added to snapshot() in v1.1 (named).
    rep["m2_m3_basis"] = ("order1 per-country force-shift ranking; "
                          "hungry_by_country field owed in snapshot() v1.1")
    os.makedirs(os.path.join(ROOT, "ops/alive/consequences"), exist_ok=True)
    outp = os.path.join(ROOT, "ops/alive/consequences/ukr2022_food.json")
    json.dump(rep, open(outp, "w"), indent=1, default=str)
    print("tiers:", rep["tier_counts"])
    print("headline:", rep["headline"][:3])
    print("movers:", [(m["country"], m["force_shift"])
                      for m in rep["order1"]["top_country_movers"][:8]])


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(int(sys.argv[2]), int(sys.argv[3]))
    else:
        assemble()
