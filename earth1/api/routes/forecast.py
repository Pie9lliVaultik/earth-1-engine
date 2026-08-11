from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from earth1.api.schemas import MultiverseSchema, DecayCurveSchema
from earth1.api.deps import get_civ
from earth1.engine import run_multiverse
from earth1.questions import question_by_id
from earth1.perishability import decay_curve
from earth1.api._serialize import serialize_result, serialize_branch

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/multiverse", response_model=MultiverseSchema)
def multiverse(
    q: str = Query(...),
    epsilon: float = Query(0.18),
    layers: int = Query(8),
):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    mv = run_multiverse(question, civ, epsilon=epsilon, layers=layers)
    return {
        "present": serialize_result(mv["present"]),
        "branches": [serialize_branch(b) for b in mv["branches"]],
    }


@router.get("/perishability", response_model=DecayCurveSchema)
def perishability(
    q: str = Query(...),
    epsilon: float = Query(0.18),
    layers: int = Query(8),
):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    from earth1.engine import run_question
    result = run_question(question, civ, epsilon=epsilon, layers=layers)
    curve = decay_curve(result.yes_pct, result.dominant)
    return curve
