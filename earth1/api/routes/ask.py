from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from earth1.api.schemas import RunResultSchema, CohortCellSchema
from earth1.api.deps import get_civ
from earth1.engine import run_question, run_segment
from earth1.questions import question_by_id, QUESTIONS
from earth1.types import FORCE_NAMES, NUM_FORCES
from earth1.api._serialize import serialize_result, serialize_cohort

router = APIRouter(prefix="/ask", tags=["ask"])


@router.get("", response_model=RunResultSchema)
def ask(
    q: str = Query(..., description="Question ID"),
    epsilon: float = Query(0.18, ge=0.01, le=1.0),
    layers: int = Query(8, ge=0, le=50),
):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    result = run_question(question, civ, epsilon=epsilon, layers=layers)
    return serialize_result(result)


@router.get("/segment", response_model=list[CohortCellSchema])
def segment(
    q: str = Query(...),
    split_by: str = Query("country", pattern="^(country|age_bucket|education|income)$"),
    epsilon: float = Query(0.18, ge=0.01, le=1.0),
    layers: int = Query(8, ge=0, le=50),
):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    cells = run_segment(question, civ, split_by=split_by, epsilon=epsilon, layers=layers)
    return [serialize_cohort(c) for c in cells]
