"""Genesis manifold — run all questions, validate holdout, freeze as versioned manifold.

Usage:
    from earth1.genesis_manifold import freeze_genesis_manifold
    report = freeze_genesis_manifold(pop=1_000_000, seed=42)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Force, NUM_FORCES
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.questions import QUESTIONS
from earth1.holdout import HOLDOUT_IDS, get_holdout_questions, get_training_questions
from earth1.calibration import calibrate_weights


@dataclass
class QuestionResult:
    id: str
    text: str
    domain: str
    yes_pct: float
    dominant: str
    conviction: float
    fragility: float
    is_holdout: bool


@dataclass
class ManifoldReport:
    pop: int
    seed: int
    country_count: int
    pop_hash: str
    results: List[QuestionResult]
    holdout_mae: float
    training_mae: float
    calibration: List[dict]
    passed: bool


def _pop_hash(civ: Civilization) -> str:
    return hashlib.sha256(civ.forces.tobytes()).hexdigest()


def run_all_questions(civ: Civilization) -> List[QuestionResult]:
    results = []
    for q in QUESTIONS:
        if q.domain == "external_substrate":
            continue
        r = run_question(q, civ)
        results.append(QuestionResult(
            id=q.id,
            text=q.text,
            domain=q.domain,
            yes_pct=r.yes_pct,
            dominant=r.dominant.name,
            conviction=r.conviction,
            fragility=r.fragility,
            is_holdout=q.id in HOLDOUT_IDS,
        ))
    return results


def compute_holdout_mae(results: List[QuestionResult]) -> float:
    holdout = [r for r in results if r.is_holdout]
    if not holdout:
        return 0.0
    errors = [abs(r.yes_pct - 0.5) for r in holdout]
    return float(np.mean(errors))


def compute_training_mae(results: List[QuestionResult]) -> float:
    training = [r for r in results if not r.is_holdout]
    if not training:
        return 0.0
    errors = [abs(r.yes_pct - 0.5) for r in training]
    return float(np.mean(errors))


def freeze_genesis_manifold(
    pop: int = 1_000_000,
    seed: int = 42,
    min_per_country: int = 500,
    mae_threshold: float = 0.15,
) -> ManifoldReport:
    civ = genesis(pop, seed, min_per_country)

    results = run_all_questions(civ)

    holdout_mae = compute_holdout_mae(results)
    training_mae = compute_training_mae(results)

    training_targets = []
    for q in get_training_questions():
        training_targets.append({
            "id": q.id,
            "text": q.text,
            "domain": q.domain,
            "target_yes_pct": 0.5,
        })
    cal = calibrate_weights(civ, training_targets)

    country_count = len(np.unique(civ.country))

    return ManifoldReport(
        pop=civ.n,
        seed=seed,
        country_count=country_count,
        pop_hash=_pop_hash(civ),
        results=results,
        holdout_mae=holdout_mae,
        training_mae=training_mae,
        calibration=cal,
        passed=holdout_mae < mae_threshold,
    )


def save_frozen_manifold(
    report: ManifoldReport,
    session,
) -> Optional[str]:
    if session is None:
        return None

    from earth1.db.store import save_manifold, save_holdout_result
    from earth1.genesis import genesis

    civ = genesis(report.pop, report.seed)

    mv = save_manifold(
        session, civ, kind="frozen",
        metadata={
            "genesis": True,
            "holdout_mae": report.holdout_mae,
            "training_mae": report.training_mae,
            "passed": report.passed,
            "question_count": len(report.results),
        },
    )

    for r in report.results:
        if r.is_holdout:
            save_holdout_result(
                session, mv.id,
                question_id=r.id,
                yes_pct=r.yes_pct,
                dominant=r.dominant,
                conviction=r.conviction,
            )

    return mv.id
