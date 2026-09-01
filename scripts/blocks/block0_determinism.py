"""BLOCK 0 — DETERMINISM (paper results block; founder order 2026-09-02).

Six reproducibility guarantees, each verified by hash equality at 20k,
freeze-0.9 flags. A FAIL on any line is a release blocker.

  D1 same-seed rebirth        birth+30d twice -> identical world hash
  D2 save/load continuation   15d + save/load + 15d == uninterrupted 30d
  D3 distress flag baseline   flag on vs off, no scenario -> identical
  D4 branch CRN               two null_branch arms, same seed -> identical
  D5 historical rebirth       birth_at(T) twice (cached news) -> identical
  D6 adapter determinism      same spec twice -> identical verdict
"""
import copy
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = "/opt/earth1-data/block0"
POP, DAYS, SEED = 20000, 30, 4242


def run_days(w, rng, n):
    from earth1.alive import live_one_day
    for _ in range(n):
        live_one_day(w, rng)
    return w


def main():
    from earth1 import persistence
    from earth1.alive import birth_world
    from earth1.branch import apply, null_branch
    os.makedirs(OUT, exist_ok=True)
    wh = persistence.world_hash
    res = {}

    def pair_hash(build):
        a = build()
        b = build()
        return wh(a), wh(b)

    # D1
    def _d1():
        w = birth_world(POP, SEED, substrate="c2plus_v1")
        return run_days(w, np.random.default_rng(SEED), DAYS)
    h1, h2 = pair_hash(_d1)
    res["D1_same_seed_rebirth"] = {"pass": h1 == h2, "hash": h1[:16]}

    # D2
    w = birth_world(POP, SEED, substrate="c2plus_v1")
    rng = np.random.default_rng(SEED)
    run_days(w, rng, 15)
    p = os.path.join(OUT, "d2.pkl")
    persistence.save_world(w, p, rng=rng)
    w2, rs, _ = persistence.load_world(p)
    rng2 = np.random.default_rng()
    if isinstance(rs, dict):
        rng2.bit_generator.state = rs
    elif rs is not None:
        rng2 = rs
    run_days(w2, rng2, 15)
    w3 = birth_world(POP, SEED, substrate="c2plus_v1")
    run_days(w3, np.random.default_rng(SEED), DAYS)
    res["D2_save_load_continuation"] = {"pass": wh(w2) == wh(w3),
                                        "hash": wh(w2)[:16]}

    # D3
    def _d3(flag):
        os.environ["EARTH1_DISTRESS_LAYOFFS"] = flag
        import importlib
        import earth1.life as L
        importlib.reload(L)
        w = birth_world(POP, SEED, substrate="c2plus_v1")
        return run_days(w, np.random.default_rng(SEED), DAYS)
    ha = wh(_d3("on"))
    hb = wh(_d3("off"))
    os.environ["EARTH1_DISTRESS_LAYOFFS"] = "on"
    import importlib
    import earth1.life as L
    importlib.reload(L)
    res["D3_distress_flag_baseline"] = {"pass": ha == hb, "hash": ha[:16]}

    # D4
    def _arm():
        w = birth_world(POP, SEED, substrate="c2plus_v1")
        rng_ = np.random.default_rng(SEED)
        run_days(w, rng_, 10)
        b = copy.deepcopy(w)
        rb = np.random.default_rng(999)
        apply(b, null_branch(), rb)
        return run_days(b, rb, 20)
    h1, h2 = pair_hash(_arm)
    res["D4_branch_crn"] = {"pass": h1 == h2, "hash": h1[:16]}

    # D5
    def _d5():
        from earth1.historical import birth_at
        w_, _ = birth_at("2010-11-25", POP, SEED, warm_days=20)
        return w_
    try:
        h1, h2 = pair_hash(_d5)
        res["D5_historical_rebirth"] = {"pass": h1 == h2, "hash": h1[:16]}
    except Exception as e:
        res["D5_historical_rebirth"] = {"pass": False, "error": repr(e)}

    # D6
    from earth1.adapters import multiverse as mv
    w = birth_world(POP, SEED, substrate="c2plus_v1")
    run_days(w, np.random.default_rng(SEED), 10)
    spec = {"question_id": "b0:d6", "class": "protest",
            "outcomes": ["YES", "NO"], "country": "FR"}
    v1 = mv.answer(dict(spec), copy.deepcopy(w), 777, horizon_days=15)
    v2 = mv.answer(dict(spec), copy.deepcopy(w), 777, horizon_days=15)
    res["D6_adapter_determinism"] = {
        "pass": json.dumps(v1.__dict__, sort_keys=True, default=str)
        == json.dumps(v2.__dict__, sort_keys=True, default=str),
        "p_model": v1.p_model}

    npass = sum(1 for v in res.values() if v["pass"])
    res["_summary"] = f"{npass}/6 PASS"
    json.dump(res, open(os.path.join(
        ROOT, "ops/alive/BLOCK0_DETERMINISM.json"), "w"), indent=1)
    for k, v in res.items():
        print(k, v if isinstance(v, str) else
              ("PASS" if v.get("pass") else f"FAIL {v}"))


if __name__ == "__main__":
    main()
