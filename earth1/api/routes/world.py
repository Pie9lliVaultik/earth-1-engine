"""/world — readouts of THE living civilization. Phase 0.5e.

Read-only by contract: the daemon is the single writer. The old
/world/tick endpoint advanced a second in-process Earth; evolution via
API is retired — 410, permanently.
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException

from earth1.api.deps import get_world

router = APIRouter(prefix="/world", tags=["world"])


@router.get("")
def world_summary():
    w, identity = get_world()
    alive = w.health.alive
    return {
        "identity": identity,
        "unemployment": round(float((~w.life.employed & w.life.in_lf).sum()
                                    / max(int(w.life.in_lf.sum()), 1)), 5),
        "deprived": round(float((w.life.deprivation > 0.5)[alive].mean()), 5),
        "homeless": round(float(w.klass.homeless[alive].mean()), 5),
        "mean_hope": round(float(w.flourishing.hope[alive].mean()), 4),
        "mean_knowledge": round(float(w.knowledge.stock[alive].mean()), 4),
        "countries_at_war": int((w.gov.at_war_with >= 0).sum() // 2),
    }


@router.get("/countries")
def countries():
    w, identity = get_world()
    from earth1.genesis import GENESIS_COUNTRY_CODES
    alive = w.health.alive
    out = []
    for ci, code in enumerate(GENESIS_COUNTRY_CODES):
        m = (w.civ.country == ci) & alive
        n = int(m.sum())
        if n < 50:
            continue
        out.append({"iso2": code, "alive": n,
                    "unemployment": round(float(
                        (~w.life.employed & w.life.in_lf)[m].sum()
                        / max(int(w.life.in_lf[m].sum()), 1)), 4),
                    "deprived": round(float(
                        (w.life.deprivation[m] > 0.5).mean()), 4),
                    "hope": round(float(w.flourishing.hope[m].mean()), 4)})
    return {"identity": identity, "countries": out}


@router.get("/earthling/{idx}")
def earthling(idx: int):
    w, identity = get_world()
    if not (0 <= idx < w.civ.n):
        raise HTTPException(404, "no such earthling")
    if not bool(w.health.alive[idx]):
        raise HTTPException(404, "this slot is not currently alive")
    from earth1.observe import observe
    view = observe(w.civ, w.life, idx)
    return {"identity": identity, "earthling": view}


@router.post("/tick")
@router.get("/tick")
def tick_retired():
    raise HTTPException(
        410, "evolution via API is retired (0.5e): the daemon "
             "earth1-alive.service is the single writer of the one "
             "living civilization")
