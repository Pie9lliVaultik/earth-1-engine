from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from earth1.api.schemas import RunResultSchema, CohortCellSchema, FreetextRequest, FreetextResponse, GatewaySchema
from earth1.api.deps import get_civ
from earth1.engine import run_question, run_segment, run_freetext
from earth1.questions import question_by_id, QUESTIONS
from earth1.types import FORCE_NAMES, NUM_FORCES
from earth1.api._serialize import serialize_result, serialize_cohort, _force_dict

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


@router.post("/freetext", response_model=FreetextResponse)
def ask_freetext(req: FreetextRequest):
    """Ask any question in natural language. The LLM estimates force weights; the engine runs the math."""
    civ = get_civ()
    try:
        out = run_freetext(
            req.question, civ,
            epsilon=req.epsilon, layers=req.layers,
            provider=req.provider, model=req.model,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    gw = out["gateway"]
    return {
        "gateway": {
            "premise_valid": gw.premise_valid,
            "premise_reason": gw.premise_reason,
            "confidence": gw.confidence,
            "lens": gw.question.lens,
            "estimated_weights": _force_dict(gw.question.weights),
            "baseline": gw.question.baseline,
        },
        "result": serialize_result(out["result"]),
    }
