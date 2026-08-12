"""World tick — the autonomous heartbeat of the civilization.

Each tick: sense → apply → run → feedback → couple → detect → rewire → age → record.
This is the WWM loop: World → Weight model → Mind → back to World."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Generator

import numpy as np

from earth1.types import Civilization, Question, RunResult, Force, NUM_FORCES
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.event_log import EventLog, WorldEvent
from earth1.feedback import opinion_feedback, _recompute_forces
from earth1.coupling import build_coupling_matrix, compute_all_shifts
from earth1.thresholds import detect_and_append
from earth1.graph_dynamics import update_graph, graph_stats
from earth1.event_generation import detect_emergent_events
from earth1.dynamics import compute_susceptibility, run_with_dynamics, apply_residues
from earth1.questions import QUESTIONS


@dataclass
class TickResult:
    tick: int
    t: float
    questions_run: List[str]
    results: Dict[str, RunResult]
    events_fired: int
    graph_stats: dict
    feedback_stats: List[dict]


@dataclass
class WorldState:
    civ: Civilization
    event_log: EventLog
    t: float
    tick_count: int
    question_history: List[Dict[str, RunResult]]
    coupling_matrix: Dict
    last_fired: Dict[str, float]
    rng: np.random.Generator
    receiver_config: object = None

    @staticmethod
    def create(
        pop: int = 100_000,
        seed: int = 42,
        min_per_country: int = 100,
        questions: Optional[List[Question]] = None,
    ) -> WorldState:
        civ = genesis(pop=pop, seed=seed, min_per_country=min_per_country)
        civ = _make_mutable(civ)
        qs = questions or [q for q in QUESTIONS if q.domain != "external_substrate"]
        coupling = build_coupling_matrix(qs)
        return WorldState(
            civ=civ,
            event_log=EventLog(),
            t=0.0,
            tick_count=0,
            question_history=[],
            coupling_matrix=coupling,
            last_fired={},
            rng=np.random.default_rng(seed),
        )


def _make_mutable(civ: Civilization) -> Civilization:
    """Copy read-only arrays so they can be mutated during ticks."""
    kwargs = {}
    for attr in civ.__dataclass_fields__:
        val = getattr(civ, attr)
        if isinstance(val, np.ndarray) and not val.flags.writeable:
            kwargs[attr] = val.copy()
    if not kwargs:
        return civ
    updates = {k: v for k, v in kwargs.items()}
    new_civ = civ
    for k, v in updates.items():
        object.__setattr__(new_civ, k, v)
    return new_civ


def _select_questions(
    tick: int,
    questions: List[Question],
    batch_size: int = 5,
) -> List[Question]:
    """Round-robin question selection."""
    qs = [q for q in questions if q.domain != "external_substrate"]
    n = len(qs)
    if n <= batch_size:
        return qs
    start = (tick * batch_size) % n
    indices = [(start + i) % n for i in range(batch_size)]
    return [qs[i] for i in indices]


def world_tick(
    state: WorldState,
    questions: Optional[List[Question]] = None,
    dt: float = 1.0,
    batch_size: int = 5,
    learning_rate: float = 0.02,
    enable_feedback: bool = True,
    enable_coupling: bool = True,
    enable_thresholds: bool = True,
    enable_rewire: bool = True,
    enable_event_generation: bool = True,
    enable_receiver: bool = False,
    use_force_dynamics: bool = False,
    residue_rate: float = 0.0005,
    susceptibility_gain: float = 4.0,
) -> TickResult:
    """One heartbeat of the civilization.

    When use_force_dynamics=True, agents communicate through force signatures
    instead of scalar stances. Learning happens through trait residue from
    absorbed forces — no explicit feedback needed.

    When enable_receiver=True, polls external sources (GDELT, ACLED, FRED,
    Google Trends) and injects their signals as events into the event log.
    """
    # Step 0: Sense — poll external sources
    if enable_receiver and state.receiver_config is not None:
        from earth1.receiver import sense_sources, activations_to_events
        activations = sense_sources(state.receiver_config, state.tick_count)
        receiver_events = activations_to_events(activations, state.t, state.receiver_config)
        for ev in receiver_events:
            state.event_log.append(ev)

    qs = questions or [q for q in QUESTIONS if q.domain != "external_substrate"]
    selected = _select_questions(state.tick_count, qs, batch_size)

    results = {}
    feedback_stats = []
    accumulated_shifts: Dict[str, np.ndarray] = {}
    total_residues = np.zeros((state.civ.n, NUM_FORCES), dtype=np.float64)

    susceptibility = None
    if use_force_dynamics:
        susceptibility = compute_susceptibility(state.civ, gain=susceptibility_gain)

    for q in selected:
        extra_shift = accumulated_shifts.get(q.id)

        # Compute effective event log shift
        effective_shift = extra_shift
        if state.event_log is not None and len(state.event_log) > 0:
            event_deltas = state.event_log.effective_deltas_vectorized(state.t, state.civ)
            if effective_shift is not None:
                effective_shift = effective_shift + event_deltas
            else:
                effective_shift = event_deltas

        if use_force_dynamics:
            settled, residues, snaps = run_with_dynamics(
                state.civ, q,
                susceptibility=susceptibility,
                field_shift=effective_shift,
                residue_rate=residue_rate,
                gain=susceptibility_gain,
            )
            total_residues += residues

            from earth1.decompose import anatomize, histogram
            anat = anatomize(state.civ, settled, q)
            dists = [histogram(s) for s in snaps]
            frac_yes = float((settled >= 0.5).mean())
            r = RunResult(
                question=q, n=state.civ.n,
                yes_pct=float(settled.mean()),
                frac_yes=frac_yes,
                regime="force-dynamics",
                distribution_by_layer=dists,
                final_distribution=dists[-1],
                force_anatomy=anat["force_anatomy"],
                dominant=anat["dominant"],
                conviction=anat["conviction"],
                fragility=anat["fragility"],
                camps=anat["camps"],
                params={"epsilon": 0.18, "layers": 8,
                        "residue_rate": residue_rate,
                        "susceptibility_gain": susceptibility_gain},
            )
        else:
            r = run_question(
                q, state.civ,
                event_log=state.event_log,
                t=state.t,
                field_shift=extra_shift,
            )

        results[q.id] = r

        if enable_feedback and not use_force_dynamics:
            from earth1.diffusion import diffuse
            s0 = np.full(state.civ.n, r.yes_pct)
            settled = diffuse(s0, state.civ.alpha, state.civ.adj, 0.18, 8)[-1]
            fb = opinion_feedback(
                state.civ, settled, q, r.force_anatomy,
                learning_rate=learning_rate,
            )
            feedback_stats.append(fb)

        if enable_coupling:
            shifts = compute_all_shifts(
                q, r, qs, state.coupling_matrix, gain=0.05,
            )
            for target_id, shift in shifts.items():
                if target_id in accumulated_shifts:
                    accumulated_shifts[target_id] = accumulated_shifts[target_id] + shift
                else:
                    accumulated_shifts[target_id] = shift

    if use_force_dynamics and np.any(total_residues != 0):
        residue_stats = apply_residues(state.civ, total_residues)
        feedback_stats.append(residue_stats)

    n_events = 0
    if enable_thresholds:
        n_events, state.last_fired = detect_and_append(
            state.civ, state.event_log, state.t, state.last_fired,
        )

    if enable_event_generation:
        emergent = detect_emergent_events(
            state.civ, state.event_log, state.t, state.question_history,
        )
        for e in emergent:
            state.event_log.append(e)
        n_events += len(emergent)

    if enable_rewire and results:
        avg_settled = np.mean(
            [r.yes_pct for r in results.values()]
        )
        proxy_stances = np.full(state.civ.n, avg_settled)
        for q_id, r in results.items():
            proxy_stances += (r.yes_pct - 0.5) * 0.1
        proxy_stances = np.clip(proxy_stances, 0, 1)
        new_adj = update_graph(state.civ.adj, proxy_stances, state.rng)
        object.__setattr__(state.civ, "adj", new_adj)

    state.t += dt
    state.tick_count += 1
    state.question_history.append(results)

    gs = graph_stats(state.civ.adj)

    return TickResult(
        tick=state.tick_count,
        t=state.t,
        questions_run=[q.id for q in selected],
        results=results,
        events_fired=n_events,
        graph_stats=gs,
        feedback_stats=feedback_stats,
    )


def run_world(
    state: WorldState,
    n_ticks: int,
    questions: Optional[List[Question]] = None,
    dt: float = 1.0,
    **kwargs,
) -> Generator[TickResult, None, None]:
    """Run multiple ticks, yielding results after each."""
    for _ in range(n_ticks):
        result = world_tick(state, questions=questions, dt=dt, **kwargs)
        yield result
