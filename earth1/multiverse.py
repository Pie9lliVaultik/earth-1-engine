"""The multiverse engine — Phase 4 foresight (bible §20.1, §13).

A branch is the same graph and weights with a different authored
information field, so branching is cheap: N identical forward passes on
N authored fields. Each branch's conviction/fragility anatomy is scored;
the reading is the branch the present is already shaped like — minimum
contortion from the present's measured belief field, weighted by
fragility.

This is NOT the temporal weight-decay simulator (which failed Phase 4
benchmarking and belongs to Phase 5 dynamics). Rehearsal compares
structural plausibility of authored futures against the present — it
never claims to know when.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, RunResult, Branch, Force, NUM_FORCES
from earth1.engine import run_question
from earth1.scenarios import Event, ScenarioBranch, EVENT_CATALOG


# Catalog event magnitudes live on the shock scale (±4); forces live in
# [0,1]. The receiver applies observed activations at gain 0.1
# (receiver.compute_field_shift) — rehearsal uses the same gain so an
# authored future lands with the intensity a real observed event would.
FIELD_GAIN = 0.1


def _field_shift(branch: ScenarioBranch) -> np.ndarray:
    """Collapse a branch's authored events into one force-field shift.

    Rehearsal is atemporal (§20.1): the field is applied whole. The day
    markers on the branch's steps matter to Phase 5 dynamics, not here.
    """
    shift = np.zeros(NUM_FORCES)
    for step in branch.steps:
        for fi, d in step.event.shifts.items():
            shift[int(fi)] += float(d)
    return shift * FIELD_GAIN


def _shifted_anatomy(civ: Civilization, q: Question, shift: np.ndarray) -> np.ndarray:
    """Force anatomy with the authored field in the decomposition.

    Mirrors decompose.anatomize's global anatomy, but the information
    field enters the contribution — the same way it enters project_all —
    so different futures produce different decompositions.
    """
    centered = (civ.forces - civ.means[np.newaxis, :]) + shift[np.newaxis, :]
    abs_contrib = np.abs(centered * q.weights[np.newaxis, :])
    total = abs_contrib.sum(axis=0)
    return total / max(total.sum(), 1e-12)


def contortion(branch_anatomy: np.ndarray, present_anatomy: np.ndarray) -> float:
    """How far a branch's force decomposition must bend from the present's.

    Euclidean distance between normalized anatomies — 0 means the present
    is already shaped like that future.
    """
    return float(np.linalg.norm(branch_anatomy - present_anatomy))


@dataclass
class Rehearsal:
    question: Question
    present: RunResult
    branches: List[Branch]
    reading: Branch                 # min contortion — the future the present is shaped like
    fragility_weights: Dict[str, float]  # per-branch plausibility weights

    def ranked(self) -> List[Branch]:
        return sorted(self.branches, key=lambda b: b.contortion)


def rehearse(
    q: Question,
    civ: Civilization,
    branches: List[ScenarioBranch],
    epsilon: float = 0.18,
    layers: int = 8,
    attention_frac: Optional[float] = None,
) -> Rehearsal:
    """Run the multiverse: one forward pass per authored branch.

    The present's fragility gates how far futures can plausibly diverge:
    a fragile present makes distant branches live possibilities; a
    convicted present discounts them. Branch weights are
    exp(-contortion / fragility-scaled temperature), normalized.
    """
    present = run_question(q, civ, epsilon=epsilon, layers=layers,
                           attention_frac=attention_frac)

    out: List[Branch] = []
    is_future: List[bool] = []
    for sb in branches:
        shift = _field_shift(sb)
        if np.any(shift):
            r = run_question(q, civ, epsilon=epsilon, layers=layers,
                             field_shift=shift, attention_frac=attention_frac)
            anatomy = _shifted_anatomy(civ, q, shift)
            is_future.append(True)
        else:
            r = present  # status quo branch is the present itself
            anatomy = present.force_anatomy
            is_future.append(False)
        out.append(Branch(
            id=sb.id, label=sb.label,
            yes_pct=r.yes_pct, dominant=Force(int(np.argmax(anatomy))),
            fragility=r.fragility,
            contortion=contortion(anatomy, present.force_anatomy),
            force_anatomy=anatomy,
        ))

    # fragility-scaled plausibility: temperature grows with the present's
    # fragility, flattening the distribution when the present is unstable
    temp = 0.05 + 0.5 * float(present.fragility)
    scores = np.array([np.exp(-b.contortion / temp) for b in out])
    total = scores.sum()
    weights = scores / total if total > 0 else np.ones(len(out)) / max(len(out), 1)

    # The reading is the FUTURE the present is already shaped like — the
    # status quo (zero shift, contortion 0 by construction) is the
    # reference frame, never a candidate reading.
    futures = [b for b, f in zip(out, is_future) if f]
    reading = min(futures or out, key=lambda b: b.contortion)
    return Rehearsal(
        question=q, present=present, branches=out, reading=reading,
        fragility_weights={b.id: float(w) for b, w in zip(out, weights)},
    )


def rehearse_question(
    q: Question,
    civ: Civilization,
    k: int = 4,
    catalog: Optional[Dict[str, Event]] = None,
    epsilon: float = 0.18,
    layers: int = 8,
    attention_frac: Optional[float] = None,
) -> Rehearsal:
    """Author-then-rehearse: Phase 3's mind authors the branches (§19.2),
    Phase 4 rehearses them (§20.1). One call from question to multiverse."""
    from earth1.central_mind import author
    branches = author(q, k=k, catalog=catalog)
    return rehearse(q, civ, branches, epsilon=epsilon, layers=layers,
                    attention_frac=attention_frac)
