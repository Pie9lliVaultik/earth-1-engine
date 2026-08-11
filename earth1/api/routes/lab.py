from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from earth1.api.schemas import OrderEffectSchema, CubeAggregateSchema
from earth1.api.deps import get_civ
from earth1.questions import question_by_id
from earth1.superposition import born_readout, sequential_measurement
from earth1.cube import build_cube, aggregate_read
from earth1.engine import run_question
from earth1.api._serialize import serialize_result

router = APIRouter(prefix="/lab", tags=["lab"])


@router.get("/superposition")
def superposition_readout(q: str = Query(...)):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    p = born_readout(civ, question)
    return {
        "question_id": question.id,
        "born_yes_pct": float(p.mean()),
        "born_frac_yes": float((p >= 0.5).mean()),
    }


@router.get("/order-effect", response_model=OrderEffectSchema)
def order_effect(
    q1: str = Query(...),
    q2: str = Query(...),
):
    question1 = question_by_id(q1)
    question2 = question_by_id(q2)
    if not question1 or not question2:
        raise HTTPException(404, "Unknown question ID")
    civ = get_civ()
    return sequential_measurement(civ, question1, question2)


@router.get("/cube", response_model=CubeAggregateSchema)
def cube_aggregate(
    q: str = Query(...),
    bins: int = Query(4, ge=2, le=8),
    epsilon: float = Query(0.18),
    layers: int = Query(8),
):
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    result = run_question(question, civ, epsilon=epsilon, layers=layers)
    from earth1.diffusion import diffuse
    from earth1.forces import project_all
    s0 = project_all(civ, question)
    snaps = diffuse(s0, civ.alpha, civ.adj, epsilon, layers)
    cube = build_cube(civ, question, snaps[-1], bins_per_dim=bins)
    return aggregate_read(cube)


@router.get("/layer-scrub")
def layer_scrub(
    q: str = Query(...),
    epsilon: float = Query(0.18, ge=0.01, le=1.0),
    layers: int = Query(8, ge=0, le=50),
):
    """Returns distribution at each diffusion layer — shows compression → sharpening."""
    question = question_by_id(q)
    if not question:
        raise HTTPException(404, f"Unknown question: {q}")
    civ = get_civ()
    result = run_question(question, civ, epsilon=epsilon, layers=layers)
    return {
        "question_id": question.id,
        "layers": [
            {"layer": i, "distribution": d.tolist()}
            for i, d in enumerate(result.distribution_by_layer)
        ],
        "params": result.params,
    }
