"""/branches — futures as addressable objects (API-COMPLETE-1).
Create, inspect, advance, compare, delete; and query any entity INSIDE
a branch with the same readouts as the live Earth."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from earth1.api import branches as B
from earth1.api import readouts as R
from earth1.api.deps import get_world

router = APIRouter(prefix="/branches", tags=["branches"])


class ScenarioIn(BaseModel):
    id: str = "scenario"
    label: Optional[str] = None
    forces: dict = {}
    countries: Optional[list] = None
    firm_damage: float = 0.0
    trade_shock: float = 0.0
    persists_days: int = 30


class BranchIn(BaseModel):
    scenario: Optional[ScenarioIn] = None
    seed: Optional[int] = None


def _get(bid):
    try:
        return B.get(bid)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.get("")
def list_branches():
    _, identity = get_world()
    return {"identity": identity, "max_branches": B.MAX_BRANCHES, "branches": B.listing()}


@router.post("")
def create_branch(body: BranchIn):
    """Clone the complete canonical world and apply a scenario on day 0 of the branch."""
    try:
        return B.create(body.scenario.model_dump() if body.scenario else None, body.seed)
    except B.BranchLimit as e:
        raise HTTPException(429, str(e))


@router.get("/{bid}")
def inspect(bid: str):
    _get(bid); return B.meta(bid)


@router.delete("/{bid}")
def delete(bid: str):
    _get(bid); B.delete(bid); return {"deleted": bid}


@router.post("/{bid}/advance")
def advance(bid: str, days: int = 1):
    _get(bid)
    if not (1 <= days <= 365):
        raise HTTPException(400, "days must be 1..365")
    return B.advance(bid, days)


@router.get("/{bid}/compare")
def compare(bid: str, against: Optional[str] = None):
    _get(bid)
    try:
        return B.compare(bid, against)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.get("/{bid}/history")
def history(bid: str, limit: int = 1000):
    b = _get(bid); con = b["recorder"].con
    rows = con.execute("SELECT day, person_id, slot, kind, detail FROM person_events ORDER BY day DESC LIMIT ?", (limit,)).fetchall()
    return {"branch": bid, "events": [{"day": r[0], "person_id": r[1], "slot": r[2], "kind": r[3], "detail": r[4]} for r in rows],
            "cascades": [{"day": r[0], "rule": r[1], "locality": r[2]} for r in con.execute("SELECT day, rule, loc FROM cascades ORDER BY day").fetchall()]}


# ── queries inside a branch (same readouts) ─────────────────────────
def _ctx(bid):
    b = _get(bid); return b["world"], b["recorder"].con, B.meta(bid)


@router.get("/{bid}/world")
def b_world(bid: str):
    w, _, m = _ctx(bid); return R.world_summary(w, {"branch": m})


@router.get("/{bid}/earthlings/{person_id}")
def b_earthling(bid: str, person_id: int):
    w, h, m = _ctx(bid)
    try:
        return {"branch": m, **R.earthling(w, h, R.slot_of(w, person_id))}
    except R.NotFound as e:
        raise HTTPException(404, str(e))


@router.get("/{bid}/earthlings/{person_id}/forces")
def b_forces(bid: str, person_id: int):
    w, h, m = _ctx(bid)
    try:
        return {"branch": m, **R.forces(w, R.slot_of(w, person_id))}
    except R.NotFound as e:
        raise HTTPException(404, str(e))


@router.get("/{bid}/earthlings/{person_id}/history")
def b_history(bid: str, person_id: int):
    w, h, m = _ctx(bid)
    return {"branch": m, "person_id": person_id, "events": R.person_history(h, person_id)}


@router.get("/{bid}/countries/{iso2}")
def b_country(bid: str, iso2: str):
    w, h, m = _ctx(bid)
    try:
        return {"branch": m, **R.country_view(w, h, iso2.upper())}
    except R.NotFound as e:
        raise HTTPException(404, str(e))


@router.get("/{bid}/localities/{loc}")
def b_locality(bid: str, loc: int):
    w, h, m = _ctx(bid)
    try:
        return {"branch": m, **R.locality_view(w, h, loc)}
    except R.NotFound as e:
        raise HTTPException(404, str(e))


@router.get("/{bid}/localities/{loc}/forces/history")
def b_locality_history(bid: str, loc: int):
    w, h, m = _ctx(bid)
    return {"branch": m, "locality": loc, "series": R.locality_force_history(h, loc)}


@router.get("/{bid}/cascades")
def b_cascades(bid: str):
    w, h, m = _ctx(bid)
    return {"branch": m, "active_residues": R.cascade_list(w)}


@router.get("/{bid}/memories")
def b_memories(bid: str):
    w, h, m = _ctx(bid)
    return {"branch": m, "standing": [R.memory_view(w, x) for x in w.chronicle.events]}
