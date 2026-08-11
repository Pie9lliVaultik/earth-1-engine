"""Temporal simulator — opinion evolution over time.

Each force's weight decays at its own half-life (bible §21):
  weights_at_t[i] = weights_0[i] * 2^(-t / half_life[i])

Fear-driven consensus fades in weeks.  Identity-driven holds for years.
Same number today, radically different shelf life.

Shocks inject force perturbations at specific time points.  Each shock's
contribution decays from its injection time onward.

At each time step, the full engine runs: projection → diffusion → readout.
This means opinion doesn't just fade — the *structure* changes as fast
forces peel away and slow forces dominate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.types import (
    Civilization, Question, RunResult, Force, FORCE_KEYS,
    NUM_FORCES, PERISHABILITY_HALF_LIFE, FORCE_NAMES,
)
from earth1.engine import run_question, run_segment
from earth1.decompose import anatomize


@dataclass
class Shock:
    day: int
    label: str
    shifts: Dict[int, float]

    @classmethod
    def from_forces(cls, day: int, label: str, **kwargs) -> "Shock":
        force_map = {f.name.lower(): f.value for f in Force}
        shifts = {}
        for name, val in kwargs.items():
            if name in force_map:
                shifts[force_map[name]] = float(val)
        return cls(day=day, label=label, shifts=shifts)


@dataclass
class TimePoint:
    day: int
    yes_pct: float
    frac_yes: float
    dominant: Force
    force_anatomy: np.ndarray
    conviction: float
    fragility: float
    effective_weights: np.ndarray
    active_shocks: List[str]


@dataclass
class Timeline:
    question_id: str
    question_text: str
    duration_days: int
    step_days: int
    time_points: List[TimePoint]
    shocks: List[Shock]
    weight_trajectories: Dict[str, List[float]]
    dominant_transitions: List[Dict]


_HALF_LIVES = np.array([
    PERISHABILITY_HALF_LIFE[Force(i)] for i in range(NUM_FORCES)
], dtype=np.float64)


def _decay_weights(
    base_weights: np.ndarray,
    t: float,
    shocks: List[Shock],
) -> np.ndarray:
    decayed = base_weights * np.power(0.5, t / _HALF_LIVES)

    for shock in shocks:
        if t >= shock.day:
            dt = t - shock.day
            shock_vec = np.zeros(NUM_FORCES)
            for idx, val in shock.shifts.items():
                shock_vec[idx] = val
            decayed += shock_vec * np.power(0.5, dt / _HALF_LIVES)

    return decayed


def simulate(
    question: Question,
    civ: Civilization,
    duration_days: int = 720,
    step_days: int = 30,
    shocks: Optional[List[Shock]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
) -> Timeline:
    if shocks is None:
        shocks = []

    days = list(range(0, duration_days + 1, step_days))
    if days[-1] != duration_days:
        days.append(duration_days)

    time_points = []
    weight_trajectories = {FORCE_NAMES[Force(i)]: [] for i in range(NUM_FORCES)}
    prev_dominant = None
    dominant_transitions = []

    for day in days:
        eff_weights = _decay_weights(question.weights, float(day), shocks)

        q_t = Question(
            id=question.id,
            text=question.text,
            domain=question.domain,
            baseline=question.baseline,
            weights=eff_weights,
            lens=question.lens,
        )

        result = run_question(q_t, civ, epsilon=epsilon, layers=layers)

        active = [s.label for s in shocks if day >= s.day]

        tp = TimePoint(
            day=day,
            yes_pct=result.yes_pct,
            frac_yes=result.frac_yes,
            dominant=result.dominant,
            force_anatomy=result.force_anatomy,
            conviction=result.conviction,
            fragility=result.fragility,
            effective_weights=eff_weights,
            active_shocks=active,
        )
        time_points.append(tp)

        for i in range(NUM_FORCES):
            weight_trajectories[FORCE_NAMES[Force(i)]].append(round(float(eff_weights[i]), 4))

        if prev_dominant is not None and result.dominant != prev_dominant:
            dominant_transitions.append({
                "day": day,
                "from": prev_dominant.name.lower(),
                "to": result.dominant.name.lower(),
            })
        prev_dominant = result.dominant

    return Timeline(
        question_id=question.id,
        question_text=question.text,
        duration_days=duration_days,
        step_days=step_days,
        time_points=time_points,
        shocks=shocks,
        weight_trajectories=weight_trajectories,
        dominant_transitions=dominant_transitions,
    )


def simulate_country(
    question: Question,
    civ: Civilization,
    duration_days: int = 720,
    step_days: int = 30,
    shocks: Optional[List[Shock]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
) -> Dict[str, List[Dict]]:
    if shocks is None:
        shocks = []

    days = list(range(0, duration_days + 1, step_days))
    if days[-1] != duration_days:
        days.append(duration_days)

    country_series: Dict[str, List[Dict]] = {}

    for day in days:
        eff_weights = _decay_weights(question.weights, float(day), shocks)

        q_t = Question(
            id=question.id,
            text=question.text,
            domain=question.domain,
            baseline=question.baseline,
            weights=eff_weights,
            lens=question.lens,
        )

        cells = run_segment(q_t, civ, "country", epsilon=epsilon, layers=layers)
        for cell in cells:
            if cell.label not in country_series:
                country_series[cell.label] = []
            country_series[cell.label].append({
                "day": day,
                "yes_pct": round(cell.yes_pct, 4),
                "dominant": cell.dominant.name.lower(),
            })

    return country_series


def compare_scenarios(
    question: Question,
    civ: Civilization,
    scenarios: List[Dict],
    duration_days: int = 720,
    step_days: int = 30,
    epsilon: float = 0.18,
    layers: int = 8,
) -> Dict[str, Timeline]:
    results = {}

    results["baseline"] = simulate(
        question, civ,
        duration_days=duration_days, step_days=step_days,
        shocks=[], epsilon=epsilon, layers=layers,
    )

    for scenario in scenarios:
        label = scenario["label"]
        shocks = scenario["shocks"]
        results[label] = simulate(
            question, civ,
            duration_days=duration_days, step_days=step_days,
            shocks=shocks, epsilon=epsilon, layers=layers,
        )

    return results
