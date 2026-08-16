from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from earth1.api.schemas import (
    RunResultSchema, CohortCellSchema, FreetextRequest, FreetextResponse,
    GatewaySchema, MindRequest, MindResponse,
)
from earth1.api.deps import get_civ, get_db, get_world_state
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
    # Civilization is the population substrate; WorldState is Earth-1.
    # Every read consults the event log at world time (re-audit P0:
    # event-blind /ask diverged 24.5pp from the event-aware world read).
    state = get_world_state()
    result = run_question(question, state.civ, epsilon=epsilon, layers=layers,
                          event_log=state.event_log, t=state.t)
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
    state = get_world_state()
    cells = run_segment(question, state.civ, split_by=split_by,
                        epsilon=epsilon, layers=layers,
                        event_log=state.event_log, t=state.t)
    return [serialize_cohort(c) for c in cells]


@router.post("/freetext", response_model=FreetextResponse)
def ask_freetext(req: FreetextRequest):
    """Ask any question in natural language. The LLM estimates force weights; the engine runs the math."""
    state = get_world_state()
    try:
        out = run_freetext(
            req.question, state.civ,
            epsilon=req.epsilon, layers=req.layers,
            provider=req.provider, model=req.model,
            event_log=state.event_log, t=state.t,
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


_corpus = None


def _get_corpus():
    """The retrieval-first corpus (G3 §19.1) — production was skipping
    it entirely, sending every question to the LLM (2026-08-16 audit)."""
    global _corpus
    if _corpus is None:
        import os
        from earth1.corpus import QuestionCorpus
        path = os.environ.get("EARTH1_CORPUS_PATH", "data/corpus/goqa_seed")
        # the corpus is stored as <base>.json + <base>.npz — test a real
        # file, not the suffixless base (re-audit: the base-path check
        # made this whole wiring a silent no-op)
        if os.path.exists(path + ".json"):
            _corpus = QuestionCorpus.load(path)
    return _corpus


@router.post("/mind", response_model=MindResponse)
def ask_mind(req: MindRequest, db=Depends(get_db)):
    """G3 Central Mind — full pipeline with narration and confidence scoring."""
    state = get_world_state()
    try:
        mind = think(
            req.question, state.civ,
            epsilon=req.epsilon, layers=req.layers,
            provider=req.provider, model=req.model,
            skip_narration=req.skip_narration,
            corpus=_get_corpus(),
            event_log=state.event_log, t=state.t,
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
