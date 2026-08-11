"""Composable scenario branching — fork timelines, chain events, compare futures.

An Event is a named force perturbation (reusable building block).
A ScenarioBranch is an ordered sequence of (day, event) pairs.
A ScenarioTree runs all branches from a shared root question,
then computes divergence, convergence, and contortion between them.

The temporal simulator does the heavy lifting — this module adds
composition, analysis, and the event catalog.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from earth1.types import (
    Civilization, Question, Force, NUM_FORCES, FORCE_NAMES,
)
from earth1.temporal import simulate, Shock, Timeline, TimePoint


@dataclass
class Event:
    id: str
    label: str
    shifts: Dict[int, float]
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_forces(cls, id: str, label: str, tags: Optional[List[str]] = None, **kwargs) -> "Event":
        force_map = {f.name.lower(): f.value for f in Force}
        shifts = {}
        for name, val in kwargs.items():
            if name in force_map:
                shifts[force_map[name]] = float(val)
        return cls(id=id, label=label, shifts=shifts, tags=tags or [])

    def as_shock(self, day: int) -> Shock:
        return Shock(day=day, label=self.label, shifts=dict(self.shifts))

    def scaled(self, factor: float) -> "Event":
        return Event(
            id=f"{self.id}_x{factor}",
            label=f"{self.label} (x{factor})",
            shifts={k: v * factor for k, v in self.shifts.items()},
            tags=self.tags,
        )

    def combined(self, other: "Event", label: Optional[str] = None) -> "Event":
        merged = dict(self.shifts)
        for k, v in other.shifts.items():
            merged[k] = merged.get(k, 0.0) + v
        return Event(
            id=f"{self.id}+{other.id}",
            label=label or f"{self.label} + {other.label}",
            shifts=merged,
            tags=list(set(self.tags + other.tags)),
        )


EVENT_CATALOG: Dict[str, Event] = {}


def _register(*events):
    for e in events:
        EVENT_CATALOG[e.id] = e


_register(
    Event.from_forces("financial_crisis", "Financial crisis",
                      tags=["economics", "crisis"],
                      fear=3.2, economics=-2.4, collective=-1.0, desire=-0.8),
    Event.from_forces("bank_run", "Bank run / bank collapse",
                      tags=["economics", "crisis"],
                      fear=3.8, economics=-1.6, collective=-1.4),
    Event.from_forces("market_boom", "Economic boom / bull market",
                      tags=["economics"],
                      desire=2.0, economics=1.8, fear=-1.0, collective=0.6),
    Event.from_forces("pandemic_onset", "Pandemic outbreak",
                      tags=["health", "crisis"],
                      fear=3.6, collective=2.0, economics=-1.2, experience=0.8),
    Event.from_forces("pandemic_recovery", "Pandemic recovery / reopening",
                      tags=["health"],
                      fear=-2.0, desire=1.6, economics=1.0, collective=-0.8),
    Event.from_forces("war_outbreak", "War / armed conflict begins",
                      tags=["security", "crisis"],
                      fear=3.4, collective=2.2, identity=1.8, economics=-1.4),
    Event.from_forces("peace_deal", "Peace agreement / ceasefire",
                      tags=["security"],
                      fear=-2.4, collective=1.0, desire=1.2, identity=-0.6),
    Event.from_forces("election_polarizing", "Polarizing election result",
                      tags=["politics"],
                      identity=2.8, collective=-1.6, fear=1.2, culture=0.8),
    Event.from_forces("election_unifying", "Unifying election / mandate",
                      tags=["politics"],
                      collective=2.0, identity=-0.8, desire=1.0, fear=-0.6),
    Event.from_forces("tech_breakthrough", "Major tech breakthrough (AI, biotech)",
                      tags=["technology"],
                      desire=2.4, fear=1.6, economics=1.2, experience=-0.8),
    Event.from_forces("tech_scandal", "Tech scandal / privacy breach",
                      tags=["technology", "crisis"],
                      fear=2.2, identity=-1.0, collective=-0.8, economics=-0.6),
    Event.from_forces("climate_disaster", "Major climate disaster",
                      tags=["climate", "crisis"],
                      fear=2.8, experience=1.4, economics=-1.0, collective=0.8),
    Event.from_forces("social_movement", "Mass social movement / protest wave",
                      tags=["social"],
                      identity=2.6, collective=1.8, fear=0.8, culture=-1.0),
    Event.from_forces("cultural_shift", "Cultural norm shift (generational)",
                      tags=["culture"],
                      culture=2.0, identity=1.2, experience=0.8, temperament=0.6),
    Event.from_forces("media_shock", "Viral media event / moral panic",
                      tags=["media"],
                      fear=2.4, collective=1.6, identity=-0.8, culture=0.6),
    Event.from_forces("religious_revival", "Religious revival / awakening",
                      tags=["religion", "culture"],
                      identity=2.2, culture=2.0, collective=1.4, temperament=-0.8),
)


@dataclass
class BranchStep:
    day: int
    event: Event


@dataclass
class ScenarioBranch:
    id: str
    label: str
    steps: List[BranchStep]
    color: str = ""

    def to_shocks(self) -> List[Shock]:
        return [step.event.as_shock(step.day) for step in self.steps]

    @classmethod
    def from_event_ids(
        cls, id: str, label: str,
        steps: List[Tuple[int, str]],
        catalog: Optional[Dict[str, Event]] = None,
    ) -> "ScenarioBranch":
        cat = catalog or EVENT_CATALOG
        branch_steps = []
        for day, event_id in steps:
            if event_id not in cat:
                raise ValueError(f"Unknown event: {event_id}")
            branch_steps.append(BranchStep(day=day, event=cat[event_id]))
        return cls(id=id, label=label, steps=branch_steps)

    def then(self, day: int, event: Event) -> "ScenarioBranch":
        return ScenarioBranch(
            id=f"{self.id}_{event.id}",
            label=f"{self.label} → {event.label}",
            steps=self.steps + [BranchStep(day=day, event=event)],
        )

    def fork(self, day: int, events: List[Event]) -> List["ScenarioBranch"]:
        return [self.then(day, event) for event in events]


@dataclass
class DivergencePoint:
    day: int
    branch_a: str
    branch_b: str
    delta_yes_pct: float
    dominant_differs: bool


@dataclass
class TreeAnalysis:
    max_divergence: float
    max_divergence_day: int
    max_divergence_pair: Tuple[str, str]
    converges: bool
    convergence_day: Optional[int]
    branch_rankings: List[Dict]


@dataclass
class ScenarioTree:
    question: Question
    branches: Dict[str, ScenarioBranch]
    timelines: Dict[str, Timeline]
    analysis: TreeAnalysis


def _find_divergence(
    timelines: Dict[str, Timeline],
    convergence_threshold: float = 0.02,
) -> TreeAnalysis:
    names = list(timelines.keys())
    if len(names) < 2:
        tl = timelines[names[0]]
        return TreeAnalysis(
            max_divergence=0.0, max_divergence_day=0,
            max_divergence_pair=(names[0], names[0]),
            converges=True, convergence_day=0,
            branch_rankings=[{
                "branch": names[0],
                "final_yes_pct": round(tl.time_points[-1].yes_pct, 4),
                "final_dominant": tl.time_points[-1].dominant.name.lower(),
            }],
        )

    tp_maps = {}
    for name, tl in timelines.items():
        tp_maps[name] = {tp.day: tp for tp in tl.time_points}

    all_days = sorted(set().union(*[set(m.keys()) for m in tp_maps.values()]))

    max_div = 0.0
    max_div_day = 0
    max_div_pair = (names[0], names[1])

    last_divergent_day = 0

    for day in all_days:
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = tp_maps[names[i]].get(day)
                b = tp_maps[names[j]].get(day)
                if a and b:
                    delta = abs(a.yes_pct - b.yes_pct)
                    if delta > max_div:
                        max_div = delta
                        max_div_day = day
                        max_div_pair = (names[i], names[j])
                    if delta > convergence_threshold:
                        last_divergent_day = day

    converges = False
    convergence_day = None
    if last_divergent_day < all_days[-1]:
        converges = True
        for day in all_days:
            if day > last_divergent_day:
                convergence_day = day
                break

    rankings = []
    for name, tl in timelines.items():
        final = tl.time_points[-1]
        rankings.append({
            "branch": name,
            "final_yes_pct": round(final.yes_pct, 4),
            "final_dominant": final.dominant.name.lower(),
            "transitions": len(tl.dominant_transitions),
        })
    rankings.sort(key=lambda r: -r["final_yes_pct"])

    return TreeAnalysis(
        max_divergence=round(max_div, 4),
        max_divergence_day=max_div_day,
        max_divergence_pair=max_div_pair,
        converges=converges,
        convergence_day=convergence_day,
        branch_rankings=rankings,
    )


def run_tree(
    question: Question,
    civ: Civilization,
    branches: List[ScenarioBranch],
    duration_days: int = 720,
    step_days: int = 30,
    epsilon: float = 0.18,
    layers: int = 8,
    include_baseline: bool = True,
) -> ScenarioTree:
    all_branches = {}
    timelines = {}

    if include_baseline:
        baseline_branch = ScenarioBranch(id="baseline", label="No events (baseline)", steps=[])
        all_branches["baseline"] = baseline_branch
        timelines["baseline"] = simulate(
            question, civ,
            duration_days=duration_days, step_days=step_days,
            shocks=[], epsilon=epsilon, layers=layers,
        )

    for branch in branches:
        all_branches[branch.id] = branch
        timelines[branch.id] = simulate(
            question, civ,
            duration_days=duration_days, step_days=step_days,
            shocks=branch.to_shocks(),
            epsilon=epsilon, layers=layers,
        )

    analysis = _find_divergence(timelines)

    return ScenarioTree(
        question=question,
        branches=all_branches,
        timelines=timelines,
        analysis=analysis,
    )


def quick_branch(
    question: Question,
    civ: Civilization,
    event_sequences: Dict[str, List[Tuple[int, str]]],
    duration_days: int = 720,
    step_days: int = 30,
    epsilon: float = 0.18,
    layers: int = 8,
) -> ScenarioTree:
    branches = []
    for name, steps in event_sequences.items():
        branch = ScenarioBranch.from_event_ids(name, name, steps)
        branches.append(branch)

    return run_tree(
        question, civ, branches,
        duration_days=duration_days, step_days=step_days,
        epsilon=epsilon, layers=layers,
    )


def get_event(event_id: str) -> Optional[Event]:
    return EVENT_CATALOG.get(event_id)


def list_events(tag: Optional[str] = None) -> List[Event]:
    events = list(EVENT_CATALOG.values())
    if tag:
        events = [e for e in events if tag in e.tags]
    return events
