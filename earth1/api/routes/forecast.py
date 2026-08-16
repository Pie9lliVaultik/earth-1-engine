from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from earth1.api.schemas import (
    MultiverseSchema, DecayCurveSchema,
    TimelineSchema, TimelineRequest, ScenarioRequest,
    TreeRequest, ScenarioTreeSchema, EventSchema,
)
from earth1.api.deps import get_civ, get_world_state
from earth1.engine import run_multiverse
from earth1.questions import question_by_id
from earth1.perishability import decay_curve
from earth1.temporal import simulate, compare_scenarios, Shock
from earth1.scenarios import (
    run_tree, ScenarioBranch, BranchStep,
    EVENT_CATALOG, list_events, get_event,
)
from earth1.types import Force, FORCE_NAMES
from earth1.api._serialize import serialize_result, serialize_branch, _force_dict

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
    state = get_world_state()
    civ = state.civ
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
    state = get_world_state()
    civ = state.civ
    from earth1.engine import run_question
    result = run_question(question, civ, epsilon=epsilon, layers=layers, event_log=state.event_log, t=state.t)
    curve = decay_curve(result.yes_pct, result.dominant)
    return curve


def _serialize_timepoint(tp) -> dict:
    return {
        "day": tp.day,
        "yes_pct": round(tp.yes_pct, 4),
        "frac_yes": round(tp.frac_yes, 4),
        "dominant": tp.dominant.name.lower(),
        "force_anatomy": _force_dict(tp.force_anatomy),
        "conviction": round(tp.conviction, 4),
        "fragility": round(tp.fragility, 4),
        "effective_weights": _force_dict(tp.effective_weights),
        "active_shocks": tp.active_shocks,
    }


def _serialize_timeline(tl) -> dict:
    return {
        "question_id": tl.question_id,
        "question_text": tl.question_text,
        "duration_days": tl.duration_days,
        "step_days": tl.step_days,
        "time_points": [_serialize_timepoint(tp) for tp in tl.time_points],
        "shocks": [
            {"day": s.day, "label": s.label, "shifts": {FORCE_NAMES[Force(k)]: v for k, v in s.shifts.items()}}
            for s in tl.shocks
        ],
        "weight_trajectories": tl.weight_trajectories,
        "dominant_transitions": tl.dominant_transitions,
    }


def _parse_shocks(shock_defs) -> list:
    if not shock_defs:
        return []
    force_map = {f.name.lower(): f.value for f in Force}
    shocks = []
    for sd in shock_defs:
        shifts = {}
        for name, val in sd.shifts.items():
            if name.lower() in force_map:
                shifts[force_map[name.lower()]] = float(val)
        shocks.append(Shock(day=sd.day, label=sd.label, shifts=shifts))
    return shocks


@router.post("/timeline", response_model=TimelineSchema)
def timeline(req: TimelineRequest):
    """Simulate opinion evolution over time with optional shocks."""
    question = question_by_id(req.question_id)
    if not question:
        raise HTTPException(404, f"Unknown question: {req.question_id}")
    state = get_world_state()
    civ = state.civ
    shocks = _parse_shocks(req.shocks)
    tl = simulate(
        question, civ,
        duration_days=req.duration_days,
        step_days=req.step_days,
        shocks=shocks,
        epsilon=req.epsilon,
        layers=req.layers,
    )
    return _serialize_timeline(tl)


@router.post("/scenarios")
def scenarios(req: ScenarioRequest):
    """Compare multiple shock scenarios against a baseline."""
    question = question_by_id(req.question_id)
    if not question:
        raise HTTPException(404, f"Unknown question: {req.question_id}")
    state = get_world_state()
    civ = state.civ

    force_map = {f.name.lower(): f.value for f in Force}
    parsed_scenarios = []
    for sc in req.scenarios:
        shocks = []
        for sd in sc.get("shocks", []):
            shifts = {}
            for name, val in sd.get("shifts", {}).items():
                if name.lower() in force_map:
                    shifts[force_map[name.lower()]] = float(val)
            shocks.append(Shock(day=sd["day"], label=sd["label"], shifts=shifts))
        parsed_scenarios.append({"label": sc["label"], "shocks": shocks})

    results = compare_scenarios(
        question, civ,
        scenarios=parsed_scenarios,
        duration_days=req.duration_days,
        step_days=req.step_days,
        epsilon=req.epsilon,
        layers=req.layers,
    )
    return {name: _serialize_timeline(tl) for name, tl in results.items()}


@router.get("/events", response_model=list[EventSchema])
def events(tag: str = None):
    """List available events from the catalog, optionally filtered by tag."""
    evts = list_events(tag=tag)
    return [
        {
            "id": e.id,
            "label": e.label,
            "shifts": {FORCE_NAMES[Force(k)]: v for k, v in e.shifts.items()},
            "tags": e.tags,
        }
        for e in evts
    ]


@router.post("/tree", response_model=ScenarioTreeSchema)
def tree(req: TreeRequest):
    """Run a scenario tree: multiple branches forking from a shared question."""
    question = question_by_id(req.question_id)
    if not question:
        raise HTTPException(404, f"Unknown question: {req.question_id}")
    state = get_world_state()
    civ = state.civ

    branches = []
    for b in req.branches:
        steps = []
        for s in b.steps:
            event = get_event(s.event_id)
            if not event:
                raise HTTPException(400, f"Unknown event: {s.event_id}")
            steps.append(BranchStep(day=s.day, event=event))
        branches.append(ScenarioBranch(id=b.id, label=b.label, steps=steps))

    result = run_tree(
        question, civ, branches,
        duration_days=req.duration_days,
        step_days=req.step_days,
        epsilon=req.epsilon,
        layers=req.layers,
        include_baseline=req.include_baseline,
    )

    timelines_data = {
        name: _serialize_timeline(tl)
        for name, tl in result.timelines.items()
    }

    branches_data = {}
    for name, branch in result.branches.items():
        branches_data[name] = {
            "id": branch.id,
            "label": branch.label,
            "steps": [
                {"day": s.day, "event_id": s.event.id, "event_label": s.event.label}
                for s in branch.steps
            ],
        }

    analysis = result.analysis
    return {
        "question_id": result.question.id,
        "question_text": result.question.text,
        "branches": branches_data,
        "timelines": timelines_data,
        "analysis": {
            "max_divergence": analysis.max_divergence,
            "max_divergence_day": analysis.max_divergence_day,
            "max_divergence_pair": list(analysis.max_divergence_pair),
            "converges": analysis.converges,
            "convergence_day": analysis.convergence_day,
            "branch_rankings": analysis.branch_rankings,
        },
    }
