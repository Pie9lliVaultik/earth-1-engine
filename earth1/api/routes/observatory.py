from __future__ import annotations
from fastapi import APIRouter, Query
from earth1.api.deps import get_civ, get_world_state
from earth1.api.schemas import QuestionSchema
from earth1.questions import QUESTIONS
from earth1.engine import run_question
from earth1.api._serialize import serialize_result

router = APIRouter(prefix="/observatory", tags=["observatory"])


@router.get("/questions", response_model=list[QuestionSchema])
def list_questions():
    return [
        QuestionSchema(
            id=q.id, text=q.text, domain=q.domain, lens=q.lens, note=q.note,
        )
        for q in QUESTIONS
    ]


@router.get("/standing-readings")
def standing_readings(
    epsilon: float = Query(0.18),
    layers: int = Query(8),
):
    """Run all belief-causal questions and return a standing record."""
    state = get_world_state()
    civ = state.civ
    readings = []
    for q in QUESTIONS:
        if q.domain != "belief_causal":
            continue
        result = run_question(q, civ, epsilon=epsilon, layers=layers, event_log=state.event_log, t=state.t)
        readings.append({
            "question_id": q.id,
            "question_text": q.text,
            "yes_pct": result.yes_pct,
            "frac_yes": result.frac_yes,
            "dominant": result.dominant.name.lower(),
            "conviction": result.conviction,
            "fragility": result.fragility,
            "regime": result.regime,
        })
    return readings
