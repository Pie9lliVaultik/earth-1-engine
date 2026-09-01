"""Historical event runner (HISTORICAL_EVENTS_v1.json protocol).

usage: run_event.py <event_id> warm
       run_event.py <event_id> worker <i> <n>
       run_event.py <event_id> assemble     (freezes output; NO judge here)
"""
import hashlib
import json
import os
import pickle
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT_BASE = "/opt/earth1-data/historical"
SEEDS = list(range(51, 67))          # 16 seeds

EVENTS = {
    "arab_spring": {
        "T": "2010-12-16", "horizon": 90, "warm": 90, "class": "protest",
        "scenario": "registry:arab_spring_2011",
        "forecast": None},           # geography IS the forecast (onsets by country)
    "svb_2023": {
        "T": "2023-03-08", "horizon": 30, "warm": 90,
        "class": "market_cascade",
        "scenario": {"forces": {"fear": 0.3, "economics": -0.25},
                     "countries": ["US"], "firm_damage": 0.2,
                     "trade_shock": 0.0, "persists_days": 60},
        "forecast": {"question": "contagion to >=2 further banks within "
                                 "30d", "outcomes": ["YES", "NO"],
                     "country": "US"}},
}


def _scenario(ev_id):
    from earth1.branch import Scenario
    spec = EVENTS[ev_id]["scenario"]
    if isinstance(spec, str) and spec.startswith("registry:"):
        from earth1.backtest import REGISTRY
        return {e.id: e for e in REGISTRY}[spec.split(":", 1)[1]].scenario
    return Scenario(id=f"hist:{ev_id}", label=f"historical {ev_id}",
                    forces=spec["forces"], countries=spec.get("countries"),
                    firm_damage=spec.get("firm_damage", 0.0),
                    trade_shock=spec.get("trade_shock", 0.0),
                    persists_days=spec.get("persists_days", 60))


def _paths(ev_id):
    d = os.path.join(OUT_BASE, ev_id)
    os.makedirs(d, exist_ok=True)
    return d, os.path.join(d, "base.pkl")


def warm(ev_id):
    from earth1 import persistence
    from earth1.historical import birth_at
    ev = EVENTS[ev_id]
    d, base = _paths(ev_id)
    seed = int(hashlib.sha256(ev_id.encode()).hexdigest()[:6], 16) % 90000
    w, rep = birth_at(ev["T"], 200_000, seed, warm_days=ev["warm"])
    persistence.save_world(w, base)
    rep["base_world_hash"] = persistence.world_hash(w)[:16]
    json.dump(rep, open(os.path.join(d, "vintage_report.json"), "w"),
              indent=1)
    print("WARM SAVED", ev_id, rep["base_world_hash"],
          "| mismatch flags:", len(rep["vintage_mismatch"]))


def worker(ev_id, i, n):
    from earth1 import persistence
    from earth1.adapters.consequences import _run_pair
    ev = EVENTS[ev_id]
    d, base = _paths(ev_id)
    w, _, _ = persistence.load_world(base)
    sc = _scenario(ev_id)
    for j, s in enumerate(SEEDS):
        if j % n != i:
            continue
        p = os.path.join(d, f"pair_{s}.pkl")
        if os.path.exists(p):
            continue
        pair, _ = _run_pair(sc, w, s, ev["horizon"])
        pickle.dump(pair, open(p, "wb"), protocol=4)
        print("PAIR DONE", ev_id, s, flush=True)


def assemble(ev_id):
    from earth1 import persistence
    from earth1.adapters.consequences import build_from_runs
    from earth1.adapters import multiverse as mv
    ev = EVENTS[ev_id]
    d, base = _paths(ev_id)
    w, _, _ = persistence.load_world(base)
    runs = [pickle.load(open(os.path.join(d, f"pair_{s}.pkl"), "rb"))
            for s in SEEDS if os.path.exists(os.path.join(d, f"pair_{s}.pkl"))]
    rep = build_from_runs({"question_id": f"hist:{ev_id}",
                           "class": ev["class"], "scenario": _scenario(ev_id)},
                          runs, [], SEEDS[:len(runs)], int(w.civ.n),
                          float(w.day))
    rep["vintage_report"] = json.load(open(os.path.join(
        d, "vintage_report.json")))
    fc = ev.get("forecast")
    if fc:
        v = mv.answer({"question_id": f"hist:{ev_id}:forecast",
                       "class": ev["class"], "outcomes": fc["outcomes"],
                       "country": fc.get("country")}, w,
                      seed=SEEDS[0], horizon_days=ev["horizon"])
        rep["forecast"] = {"question": fc["question"],
                           "p_model": v.p_model, "abstain": v.abstain,
                           "abstain_reason": v.abstain_reason,
                           "distances": v.distances}
    outp = os.path.join(ROOT, "ops/alive/historical")
    os.makedirs(outp, exist_ok=True)
    json.dump(rep, open(os.path.join(outp, f"{ev_id}_frozen.json"), "w"),
              indent=1, default=str)
    print("FROZEN", ev_id, "| tiers", rep["tier_counts"],
          "| geography basis", rep["order2_geography"]["basis"],
          "| forecast", rep.get("forecast", {}).get("p_model"))


if __name__ == "__main__":
    ev_id, mode = sys.argv[1], sys.argv[2]
    if mode == "warm":
        warm(ev_id)
    elif mode == "worker":
        worker(ev_id, int(sys.argv[3]), int(sys.argv[4]))
    else:
        assemble(ev_id)
