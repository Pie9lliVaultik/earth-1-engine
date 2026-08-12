"""Emergence observatory — quantify how far the system has drifted from baseline.

The surprise index is the key metric: run the same questions on a fresh genesis
population vs the current evolved population. The KL divergence between their
stance distributions measures how much unprogrammed structure has developed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from earth1.types import Civilization, Question, RunResult, Force, NUM_FORCES
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.graph_dynamics import graph_stats
from earth1.questions import QUESTIONS


@dataclass
class EmergenceMetrics:
    entropy: float
    surprise_index: float
    trait_drift_magnitude: float
    n_unprogrammed_events: int
    graph_mean_degree: float
    graph_n_edges: int
    tick_count: int
    question_divergences: Dict[str, float]


def _stance_entropy(yes_pct: float) -> float:
    """Shannon entropy of binary stance distribution."""
    if yes_pct <= 0 or yes_pct >= 1:
        return 0.0
    return -(yes_pct * np.log2(yes_pct) + (1 - yes_pct) * np.log2(1 - yes_pct))


def _kl_divergence(p: float, q: float) -> float:
    """KL divergence D(p || q) for binary distributions."""
    p = np.clip(p, 1e-8, 1 - 1e-8)
    q = np.clip(q, 1e-8, 1 - 1e-8)
    return float(p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q)))


def measure_emergence(
    evolved_civ: Civilization,
    baseline_civ: Civilization,
    questions: Optional[List[Question]] = None,
    event_log=None,
    t: float = 0.0,
    tick_count: int = 0,
) -> EmergenceMetrics:
    """Quantify how far the system has drifted from its programmed baseline."""
    qs = questions or [q for q in QUESTIONS if q.domain != "external_substrate"]

    baseline_results = {}
    evolved_results = {}
    for q in qs:
        baseline_results[q.id] = run_question(q, baseline_civ)
        evolved_results[q.id] = run_question(q, evolved_civ, event_log=event_log, t=t)

    divergences = {}
    total_kl = 0.0
    total_entropy = 0.0
    for qid in baseline_results:
        b = baseline_results[qid].yes_pct
        e = evolved_results[qid].yes_pct
        kl = _kl_divergence(e, b)
        divergences[qid] = kl
        total_kl += kl
        total_entropy += _stance_entropy(e)

    n_qs = len(qs)
    surprise_index = total_kl / n_qs if n_qs > 0 else 0.0
    avg_entropy = total_entropy / n_qs if n_qs > 0 else 0.0

    trait_attrs = [
        "openness", "empathy", "risk_appetite", "doubt",
        "desire_intensity", "economic_field", "conscientiousness",
        "agreeableness", "extraversion", "neuroticism",
        "power_distance", "individualism", "uncertainty_avoidance",
        "long_term_orientation",
    ]
    drift_sq = 0.0
    for attr in trait_attrs:
        ev = getattr(evolved_civ, attr).mean()
        bl = getattr(baseline_civ, attr).mean()
        drift_sq += (ev - bl) ** 2
    trait_drift = float(np.sqrt(drift_sq))

    n_unprogrammed = 0
    if event_log is not None:
        for e in event_log.events():
            if e.source.startswith("emergent:") or e.source.startswith("threshold:"):
                n_unprogrammed += 1

    gs = graph_stats(evolved_civ.adj)

    return EmergenceMetrics(
        entropy=avg_entropy,
        surprise_index=surprise_index,
        trait_drift_magnitude=trait_drift,
        n_unprogrammed_events=n_unprogrammed,
        graph_mean_degree=gs["mean_degree"],
        graph_n_edges=gs["n_edges"],
        tick_count=tick_count,
        question_divergences=divergences,
    )


def detect_surprises(
    evolved_civ: Civilization,
    baseline_civ: Civilization,
    questions: Optional[List[Question]] = None,
    event_log=None,
    t: float = 0.0,
    min_divergence: float = 0.01,
) -> List[Dict]:
    """Find questions where current output diverges most from baseline."""
    qs = questions or [q for q in QUESTIONS if q.domain != "external_substrate"]

    surprises = []
    for q in qs:
        b = run_question(q, baseline_civ)
        e = run_question(q, evolved_civ, event_log=event_log, t=t)
        kl = _kl_divergence(e.yes_pct, b.yes_pct)
        delta = e.yes_pct - b.yes_pct
        if kl >= min_divergence:
            surprises.append({
                "question_id": q.id,
                "question_text": q.text,
                "baseline_yes": b.yes_pct,
                "evolved_yes": e.yes_pct,
                "delta": delta,
                "kl_divergence": kl,
                "evolved_dominant": e.dominant.name,
                "baseline_dominant": b.dominant.name,
            })

    surprises.sort(key=lambda s: -s["kl_divergence"])
    return surprises
