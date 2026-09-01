"""Five end-to-end consequence reports at 200k x 8 seeds (founder
ruling 2026-09-01 item 4). Reports -> ops/alive/consequences/.

usage: five_scenarios.py warm            (200k base world, warm 60d)
       five_scenarios.py worker <s> <n>  (shard: one (scenario,seed) pair per slot)
       five_scenarios.py assemble        (build the five reports)
"""
import json
import os
import pickle
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.environ.get("FIVE_OUT", "/opt/earth1-data/five")
BASE = os.path.join(OUT, "base200k.pkl")
SEEDS = list(range(11, 19))          # 8 seeds
MENA = ["EG", "TN", "LY", "YE", "SY", "JO", "MA", "DZ", "IQ", "LB", "SA"]


def scenarios():
    from earth1.branch import Scenario
    return {
        "a_rate_hike_us": {
            "class": "rate_decision", "calibrated": False,
            "scenario": Scenario(
                id="five:a", label="300bp emergency hike, US",
                forces={"economics": -0.3, "fear": 0.2, "desire": -0.15},
                countries=["US"], firm_damage=0.1, trade_shock=0.05,
                persists_days=90)},
        "b_bank_failure_us": {
            "class": "market_cascade", "calibrated": False,
            "scenario": Scenario(
                id="five:b", label="SVB-scale bank failure, US",
                forces={"fear": 0.3, "economics": -0.25},
                countries=["US"], firm_damage=0.2, trade_shock=0.0,
                persists_days=60)},
        "c_contested_election_br": {
            "class": "election", "calibrated": False,
            "scenario": Scenario(
                id="five:c", label="contested election result, Brazil",
                forces={"identity": 0.3, "collective": 0.25, "fear": 0.25},
                countries=["BR"], firm_damage=0.05, trade_shock=0.0,
                persists_days=90)},
        "d_food_spike_mena": {
            "class": "protest", "calibrated": False,
            "scenario": Scenario(
                id="five:d", label="20% food-price spike, MENA",
                forces={"fear": 0.15, "economics": -0.2},
                countries=MENA, firm_damage=0.0, trade_shock=0.2,
                persists_days=120)},
        "e_earthquake_megacity_jp": {
            "class": "disaster", "calibrated": False,
            "scenario": Scenario(
                id="five:e", label="major earthquake, Japanese megacity",
                forces={"fear": 0.4, "economics": -0.15, "collective": 0.2},
                countries=["JP"], firm_damage=0.15, trade_shock=0.05,
                persists_days=60)},
    }


def warm():
    from earth1.alive import birth_world, live_one_day
    from earth1 import persistence
    os.makedirs(OUT, exist_ok=True)
    w = birth_world(200_000, 515151, substrate="c2plus_v1")
    rng = np.random.default_rng(515151)
    for _ in range(60):
        live_one_day(w, rng)
    persistence.save_world(w, BASE, rng=rng)
    print("WARM SAVED 200k", persistence.world_hash(w)[:16])


def worker(shard, nshards):
    from earth1 import persistence
    from earth1.adapters.consequences import _run_pair
    w, _, _ = persistence.load_world(BASE)
    jobs = [(name, s) for name in sorted(scenarios()) for s in SEEDS]
    for i, (name, seed) in enumerate(jobs):
        if i % nshards != shard:
            continue
        p = os.path.join(OUT, f"pair_{name}_{seed}.pkl")
        if os.path.exists(p):
            continue
        cfg = scenarios()[name]
        pair, fork = _run_pair(cfg["scenario"], w, seed, 180)
        pickle.dump(pair, open(p, "wb"), protocol=4)
        if seed == SEEDS[0] and fork is not None:
            persistence.save_world(fork, os.path.join(
                OUT, f"fork_{name}.pkl"))
        print("PAIR DONE", name, seed, flush=True)


def assemble():
    from earth1 import persistence
    from earth1.adapters.consequences import _run_pair, build_from_runs
    os.makedirs(os.path.join(ROOT, "ops/alive/consequences"), exist_ok=True)
    w, _, _ = persistence.load_world(BASE)
    for name, cfg in sorted(scenarios().items()):
        runs = []
        for s in SEEDS:
            p = os.path.join(OUT, f"pair_{name}_{s}.pkl")
            if os.path.exists(p):
                runs.append(pickle.load(open(p, "rb")))
        fp = os.path.join(OUT, f"fork_{name}.pkl")
        forks = []
        if os.path.exists(fp):
            fw, _, _ = persistence.load_world(fp)
            forks = [fw]
        spec = {"question_id": f"five:{name}", "class": cfg["class"],
                "scenario": cfg["scenario"]}
        rep = build_from_runs(spec, runs, forks, SEEDS[:len(runs)],
                              int(w.civ.n), float(w.day),
                              cfg["calibrated"])
        outp = os.path.join(ROOT, "ops/alive/consequences", f"{name}.json")
        json.dump(rep, open(outp, "w"), indent=1, default=str)
        print(name, "tiers", rep["tier_counts"], "| headline:",
              rep["headline"][:2])


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "warm":
        warm()
    elif m == "worker":
        worker(int(sys.argv[2]), int(sys.argv[3]))
    else:
        assemble()
