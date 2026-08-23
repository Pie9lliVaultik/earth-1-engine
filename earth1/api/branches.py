"""BRANCH STORE — futures as first-class, addressable objects
(API-COMPLETE-1). A branch is a complete deep clone of the canonical
world (never a reduced one), a scenario applied on its first day, its
own RNG stream, and its own in-memory history. The live world is never
touched. Memory-bounded: EARTH1_API_MAX_BRANCHES (default 2).
"""
from __future__ import annotations

import copy
import os
import threading
import time
import uuid

import numpy as np

MAX_BRANCHES = int(os.environ.get("EARTH1_API_MAX_BRANCHES", "2"))
_lock = threading.Lock()
_store: dict = {}


class BranchLimit(RuntimeError):
    pass


def create(scenario: dict | None, seed: int | None = None) -> dict:
    from earth1.api.deps import clone_world
    from earth1.branch import Scenario, apply
    from earth1.history import open_history, Recorder
    with _lock:
        if len(_store) >= MAX_BRANCHES:
            raise BranchLimit(f"branch store full ({MAX_BRANCHES}); delete one first")
        w, identity = clone_world()
        bid = str(uuid.uuid4())
        rng = np.random.default_rng(int(seed) if seed is not None else int(time.time()) % (2 ** 31))
        sc = None
        if scenario:
            sc = Scenario(id=scenario.get("id", "scenario"), label=scenario.get("label", scenario.get("id", "scenario")),
                          forces=scenario.get("forces", {}), countries=scenario.get("countries"),
                          firm_damage=float(scenario.get("firm_damage", 0.0)), trade_shock=float(scenario.get("trade_shock", 0.0)),
                          persists_days=int(scenario.get("persists_days", 30)))
            apply(w, sc, rng)
        rec = Recorder(open_history(":memory:")); rec.record(w)
        _store[bid] = {"id": bid, "world": w, "rng": rng, "recorder": rec, "scenario": scenario, "seed": seed,
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "parent": identity,
                       "branched_at_day": int(w.day), "days_advanced": 0}
        return meta(bid)


def get(bid: str) -> dict:
    b = _store.get(bid)
    if b is None:
        raise KeyError(f"no branch {bid}")
    return b


def meta(bid: str) -> dict:
    b = get(bid)
    from earth1.alive import PHYSICS_VERSION
    return {"id": bid, "created_at": b["created_at"], "scenario": b["scenario"], "seed": b["seed"],
            "parent": b["parent"], "branched_at_day": b["branched_at_day"], "day": int(b["world"].day),
            "days_advanced": b["days_advanced"], "alive": int(b["world"].health.alive.sum()),
            "physics_version": PHYSICS_VERSION, "history": "in-memory (per branch)"}


def advance(bid: str, days: int) -> dict:
    from earth1.alive import live_one_day
    b = get(bid)
    with _lock:
        for _ in range(int(days)):
            st = live_one_day(b["world"], b["rng"])
            b["recorder"].record(b["world"], st)
            b["days_advanced"] += 1
    return meta(bid)


def delete(bid: str) -> None:
    with _lock:
        _store.pop(bid, None)


def listing() -> list:
    return [meta(k) for k in list(_store)]


def compare(bid: str, against: str | None) -> dict:
    """Branch vs control: aggregates, per-country, per-force, and the
    people whose stored forces moved most."""
    from earth1.api.deps import get_world
    from earth1.api.readouts import FORCES, country_codes, _gini
    wb = get(bid)["world"]
    if against in (None, "live"):
        wc, _ = get_world(); label = "live"
    else:
        wc = get(against)["world"]; label = against
    alive = wb.health.alive & wc.health.alive
    same = alive & (wb.civ.person_id == wc.civ.person_id)
    df = wb.civ.forces[same] - wc.civ.forces[same]
    codes = country_codes(); per_c = []
    for ci in np.unique(wb.civ.country[same]):
        m = same & (wb.civ.country == ci)
        per_c.append({"iso2": codes[ci], "n": int(m.sum()), "delta_forces": {f: round(float((wb.civ.forces[m, k] - wc.civ.forces[m, k]).mean()), 5) for k, f in enumerate(FORCES)},
                      "delta_unemployment": round(float((~wb.life.employed[m] & wb.life.in_lf[m]).mean() - (~wc.life.employed[m] & wc.life.in_lf[m]).mean()), 5)})
    mag = np.abs(df).max(axis=1); top = np.argsort(-mag)[:50]; idx = np.flatnonzero(same)[top]
    return {"branch": bid, "control": label, "branch_day": int(wb.day), "control_day": int(wc.day),
            "comparable_persons": int(same.sum()),
            "delta_forces_mean": {f: round(float(df[:, k].mean()), 6) for k, f in enumerate(FORCES)},
            "delta_forces_abs_mean": {f: round(float(np.abs(df[:, k]).mean()), 6) for k, f in enumerate(FORCES)},
            "frac_persons_moved_gt_0.01": float((mag > 0.01).mean()),
            "delta_unemployment": float((~wb.life.employed & wb.life.in_lf)[same].mean() - (~wc.life.employed & wc.life.in_lf)[same].mean()),
            "delta_wealth_gini": _gini(wb.life.wealth[same]) - _gini(wc.life.wealth[same]),
            "per_country": sorted(per_c, key=lambda r: -max(abs(v) for v in r["delta_forces"].values()))[:50],
            "most_moved_persons": [{"person_id": int(wb.civ.person_id[i]), "max_abs_delta": float(mag[t])} for i, t in zip(idx, top)]}
