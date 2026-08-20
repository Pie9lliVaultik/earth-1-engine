"""/forecast — futures and branches of the living civilization. 0.5e.

Branch paths clone the COMPLETE canonical world or refuse — never a
reduced representation. Cloning a 4M-agent world costs ~18 GB per
branch, so requests above EARTH1_API_MAX_BRANCH_POP (default 500k)
are refused with the honest reason rather than served from something
smaller pretending to be Earth.
"""
from __future__ import annotations

import os

import numpy as np
from fastapi import APIRouter, HTTPException

from earth1.api.deps import clone_world, get_world

router = APIRouter(prefix="/forecast", tags=["forecast"])

MAX_BRANCH_POP = int(os.environ.get("EARTH1_API_MAX_BRANCH_POP", "500000"))


def _guard_branchable(identity):
    if identity["population"] > MAX_BRANCH_POP:
        raise HTTPException(
            503, {"error": "branch_too_large",
                  "detail": f"cloning the complete {identity['population']:,}"
                            f"-agent civilization exceeds the API budget; "
                            f"branch work at this scale runs on prime. A "
                            f"reduced clone would be a different universe, "
                            f"so the API refuses instead.",
                  "identity": identity})


@router.get("/futures/{idx}")
def futures(idx: int, branches: int = 24, days: int = 90):
    """One earthling's possible lives — full-world clones, per branch."""
    w, identity = get_world()
    _guard_branchable(identity)
    if not (0 <= idx < w.civ.n) or not bool(w.health.alive[idx]):
        raise HTTPException(404, "no such living earthling")
    branches = int(np.clip(branches, 4, 64))
    days = int(np.clip(days, 7, 365))
    wc, _ = clone_world()
    from earth1.observe import futures as world_futures
    out = world_futures(wc, idx, n_branches=branches, days=days)
    return {"identity": identity, "branches": branches, "days": days,
            "futures": out}


@router.get("/multiverse")
@router.post("/scenarios")
@router.get("/timeline")
@router.get("/tree")
def legacy_forecast_pending():
    _, identity = get_world()
    raise HTTPException(503, {
        "error": "living_scenario_surface_pending",
        "detail": "scenario/branch product surfaces land with the "
                  "Phase-2 domain adapters; the retired engine will not "
                  "answer in their place",
        "identity": identity})
