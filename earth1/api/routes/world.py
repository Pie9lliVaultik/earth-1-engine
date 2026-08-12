"""API routes for the living world — tick, state, emergence, receiver control."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from earth1.questions import QUESTIONS
from earth1.types import Force

router = APIRouter(prefix="/world", tags=["world"])

_world_state = None


def _get_or_create_state(pop: int = 100_000, seed: int = 42):
    global _world_state
    if _world_state is None:
        from earth1.tick import WorldState
        _world_state = WorldState.create(pop=pop, seed=seed, min_per_country=100)
    return _world_state


class TickRequest(BaseModel):
    n_ticks: int = 1
    use_force_dynamics: bool = True
    enable_receiver: bool = False
    batch_size: int = 5
    dt: float = 1.0


class ReceiverToggleRequest(BaseModel):
    enabled: bool = True
    sources: Optional[List[str]] = None


class InjectEventRequest(BaseModel):
    force_deltas: dict
    region_pattern: str = "*"
    decay_half_life: float = 30.0
    source: str = "manual"


@router.post("/tick")
def advance_world(req: TickRequest):
    """Advance the world by N ticks."""
    from earth1.tick import world_tick, run_world

    state = _get_or_create_state()
    qs = [q for q in QUESTIONS if q.domain != "external_substrate"]

    results = []
    for tick_result in run_world(
        state, n_ticks=req.n_ticks, questions=qs,
        dt=req.dt, batch_size=req.batch_size,
        use_force_dynamics=req.use_force_dynamics,
        enable_receiver=req.enable_receiver,
    ):
        results.append({
            "tick": tick_result.tick,
            "t": round(tick_result.t, 1),
            "questions_run": tick_result.questions_run,
            "events_fired": tick_result.events_fired,
            "graph_stats": tick_result.graph_stats,
        })

    return {
        "ticks_run": req.n_ticks,
        "current_tick": state.tick_count,
        "current_t": round(state.t, 1),
        "total_events": len(state.event_log),
        "results": results,
    }


@router.get("/state")
def world_state():
    """Return current world state summary."""
    state = _get_or_create_state()

    from earth1.engine import run_question
    qs = [q for q in QUESTIONS if q.domain != "external_substrate"]

    force_means = {}
    for f in Force:
        force_means[f.name.lower()] = round(float(state.civ.forces[:, f].mean()), 4)

    question_snapshot = []
    for q in qs[:10]:
        r = run_question(q, state.civ, event_log=state.event_log, t=state.t)
        question_snapshot.append({
            "id": q.id, "yes_pct": round(r.yes_pct, 4),
            "dominant": r.dominant.name.lower(),
            "conviction": round(r.conviction, 4),
        })

    receiver_active = (
        state.receiver_config is not None
        and hasattr(state.receiver_config, 'sources')
        and len(state.receiver_config.sources) > 0
    )

    receiver_events = sum(
        1 for e in state.event_log.events()
        if e.source.startswith("receiver:")
    )

    return {
        "tick": state.tick_count,
        "t": round(state.t, 1),
        "population": state.civ.n,
        "total_events": len(state.event_log),
        "receiver_events": receiver_events,
        "receiver_active": receiver_active,
        "force_means": force_means,
        "questions": question_snapshot,
    }


@router.get("/emergence")
def emergence_metrics():
    """Return emergence metrics vs genesis baseline."""
    state = _get_or_create_state()

    from earth1.genesis import genesis
    from earth1.observatory import measure_emergence
    qs = [q for q in QUESTIONS if q.domain != "external_substrate"]

    baseline = genesis(pop=state.civ.n, seed=state.civ.seed, min_per_country=100)
    metrics = measure_emergence(
        state.civ, baseline, questions=qs,
        event_log=state.event_log, t=state.t,
        tick_count=state.tick_count,
    )

    return {
        "tick": state.tick_count,
        "surprise_index": round(metrics.surprise_index, 6),
        "trait_drift_magnitude": round(metrics.trait_drift_magnitude, 4),
        "entropy": round(metrics.entropy, 4),
        "n_unprogrammed_events": metrics.n_unprogrammed_events,
        "graph_n_edges": metrics.graph_n_edges,
        "graph_mean_degree": round(metrics.graph_mean_degree, 2),
    }


@router.post("/receiver/enable")
def enable_receiver(req: ReceiverToggleRequest):
    """Enable or disable live source polling."""
    state = _get_or_create_state()

    if req.enabled:
        from earth1.receiver import ReceiverConfig
        config = ReceiverConfig.default()
        if req.sources:
            config.sources = [s for s in config.sources if s.source_id in req.sources]
        state.receiver_config = config
        return {
            "status": "enabled",
            "sources": [s.source_id for s in config.sources],
        }
    else:
        state.receiver_config = None
        return {"status": "disabled", "sources": []}


@router.post("/inject")
def inject_event(req: InjectEventRequest):
    """Manually inject a world event."""
    state = _get_or_create_state()

    from earth1.event_log import WorldEvent
    event = WorldEvent.create(
        timestamp=state.t,
        force_deltas=req.force_deltas,
        region_pattern=req.region_pattern,
        decay_half_life=req.decay_half_life,
        source=req.source,
    )
    state.event_log.append(event)

    return {
        "event_id": event.id,
        "timestamp": event.timestamp,
        "force_deltas": event.force_deltas,
        "total_events": len(state.event_log),
    }


@router.post("/reset")
def reset_world(pop: int = Query(100_000), seed: int = Query(42)):
    """Reset the world to genesis state."""
    global _world_state
    from earth1.tick import WorldState
    _world_state = WorldState.create(pop=pop, seed=seed, min_per_country=100)
    return {"status": "reset", "population": pop, "seed": seed}
