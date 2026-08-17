"""THE canonical way to advance Earth-1 — one function, every caller.

Audit round 7/8 finding: /world/tick called run_world() directly while
LivingWorld.tick() rebuilt coupling and ran the generational engine —
two ways to advance Earth, one of which left coupling empty and ages
frozen. "There is only one Earth-1" requires there to be only one
passage of time.

advance_world() is that passage: coupling rebuild (deterministic in the
day's questions), the opinion tick, the generational tick, in-process
history compaction. API, cron, replay, and persistence all call this;
LivingWorld.tick() wraps it with save().
"""
from __future__ import annotations

from typing import Dict, List, Optional

from earth1.types import Question
from earth1.tick import WorldState, world_tick

# In-process history bounds (audit round 8: full settled_stances arrays
# retained per tick per question — gigabytes at 1M agents). Older
# entries keep scalars only; the stance arrays live in the newest ticks
# where the polarization detector actually reads them.
_HISTORY_MAX = 60
_STANCES_KEEP = 2


def advance_world(
    state: WorldState,
    questions: List[Question],
    days: int = 1,
    dt: float = 1.0,
    enable_generational: bool = True,
    enable_receiver: bool = False,
    cohort_drift: Optional[Dict[str, float]] = None,
    rebuild_coupling: bool = True,
    **tick_kwargs,
) -> Dict[str, int]:
    """Advance THE world. Returns {'deaths': n}."""
    from earth1.generational import generational_tick
    from earth1.coupling import build_coupling_matrix

    if rebuild_coupling:
        state.coupling_matrix = build_coupling_matrix(questions)

    stats = {"deaths": 0}
    for _ in range(days):
        world_tick(state, questions=questions, dt=dt,
                   enable_receiver=enable_receiver, **tick_kwargs)
        if enable_generational:
            day = generational_tick(state.civ, state.rng, dt_days=dt,
                                    cohort_drift=cohort_drift)
            stats["deaths"] += day["deaths"]
        _compact_history(state)
    return stats


def _compact_history(state: WorldState) -> None:
    """Bound in-process memory: cap history length, strip per-agent
    stance arrays from all but the newest ticks."""
    if len(state.question_history) > _HISTORY_MAX:
        del state.question_history[:-_HISTORY_MAX]
    for tick_results in state.question_history[:-_STANCES_KEEP]:
        for r in tick_results.values():
            if getattr(r, "settled_stances", None) is not None:
                try:
                    r.settled_stances = None
                except AttributeError:
                    pass          # frozen/persisted skeletons have no arrays
