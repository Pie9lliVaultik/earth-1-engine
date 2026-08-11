from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from earth1.api.schemas import (
    RunResultSchema, CohortCellSchema, FreetextRequest, FreetextResponse,
    GatewaySchema, MindRequest, MindResponse,
)
from earth1.api.deps import get_civ, get_db
from earth1.engine import run_question, run_segment, run_freetext
from earth1.central_mind import think
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


@router.post("/mind", response_model=MindResponse)
def ask_mind(req: MindRequest, db=Depends(get_db)):
    """G3 Central Mind — full pipeline with narration and confidence scoring."""
    civ = get_civ()
    try:
        mind = think(
            req.question, civ,
            epsilon=req.epsilon, layers=req.layers,
            provider=req.provider, model=req.model,
            skip_narration=req.skip_narration,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    gw = mind.gateway
    gateway_data = {
        "premise_valid": gw.premise_valid,
        "premise_reason": gw.premise_reason,
        "confidence": gw.confidence,
        "lens": gw.question.lens,
        "estimated_weights": _force_dict(gw.question.weights),
        "baseline": gw.question.baseline,
    }

    conf = mind.confidence
    confidence_data = {
        "regime": conf.regime,
        "similarity": conf.similarity,
        "nearest_id": conf.nearest_id,
        "nearest_text": conf.nearest_text,
        "weight_cosine": conf.weight_cosine,
        "keyword_overlap": conf.keyword_overlap,
    }

    country_data = None
    if mind.country_splits:
        country_data = [serialize_cohort(c) for c in mind.country_splits]

    if db is not None and not mind.abstained:
        try:
            from earth1.db.store import save_run
            save_run(
                db,
                run_type="mind",
                question_text=mind.question_text,
                binary_question=mind.binary_question,
                question_id=mind.result.question.id,
                country_scope=mind.country_scope,
                temporal_context=mind.temporal_context,
                yes_pct=mind.result.yes_pct,
                frac_yes=mind.result.frac_yes,
                dominant=mind.result.dominant.name.lower(),
                conviction=mind.result.conviction,
                fragility=mind.result.fragility,
                confidence_regime=conf.regime,
                confidence_similarity=conf.similarity,
                force_anatomy=_force_dict(mind.result.force_anatomy),
                parameters={"epsilon": req.epsilon, "layers": req.layers},
                narration=mind.narration,
                country_splits=country_data,
                gateway_raw=gw.raw,
            )
        except Exception:
            pass

    return {
        "question_text": mind.question_text,
        "binary_question": mind.binary_question,
        "country_scope": mind.country_scope,
        "temporal_context": mind.temporal_context,
        "gateway": gateway_data,
        "result": serialize_result(mind.result),
        "confidence": confidence_data,
        "narration": mind.narration,
        "country_splits": country_data,
        "abstained": mind.abstained,
    }
