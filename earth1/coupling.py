"""Cross-question coupling — questions influence each other through shared forces.

When question A produces a strong result, semantically related questions
feel a field shift proportional to the weight-vector overlap. This creates
interference between topics without explicit programming."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from earth1.types import Question, RunResult, NUM_FORCES


def compute_coupling(q1: Question, q2: Question, threshold: float = 0.15) -> float:
    """Cosine similarity of weight vectors, zeroed below threshold."""
    n1 = np.linalg.norm(q1.weights)
    n2 = np.linalg.norm(q2.weights)
    if n1 < 1e-8 or n2 < 1e-8:
        return 0.0
    cos = float(np.dot(q1.weights, q2.weights) / (n1 * n2))
    if abs(cos) < threshold:
        return 0.0
    return cos


def build_coupling_matrix(questions: List[Question], threshold: float = 0.15) -> Dict[Tuple[str, str], float]:
    """Build sparse coupling matrix between all question pairs."""
    matrix = {}
    for i, q1 in enumerate(questions):
        if q1.domain == "external_substrate":
            continue
        for j, q2 in enumerate(questions):
            if j <= i or q2.domain == "external_substrate":
                continue
            c = compute_coupling(q1, q2, threshold)
            if c != 0.0:
                matrix[(q1.id, q2.id)] = c
                matrix[(q2.id, q1.id)] = c
    return matrix


def coupled_field_shift(
    source_q: Question,
    source_result: RunResult,
    target_q: Question,
    coupling: float,
    gain: float = 0.05,
) -> np.ndarray:
    """Compute field shift from source question's result onto target question.

    The shift is proportional to:
    - coupling strength (cosine similarity)
    - conviction (how stable the source result is)
    - (1 - fragility) (fragile results don't propagate)
    """
    if abs(coupling) < 1e-8:
        return np.zeros(NUM_FORCES)

    strength = coupling * source_result.conviction * (1.0 - source_result.fragility)
    deviation = source_result.yes_pct - 0.5
    shift = source_result.force_anatomy * deviation * strength * gain
    return shift


def compute_all_shifts(
    source_q: Question,
    source_result: RunResult,
    questions: List[Question],
    coupling_matrix: Dict[Tuple[str, str], float],
    gain: float = 0.05,
) -> Dict[str, np.ndarray]:
    """Compute field shifts from one question's result to all coupled questions."""
    shifts = {}
    for target_q in questions:
        if target_q.id == source_q.id or target_q.domain == "external_substrate":
            continue
        coupling = coupling_matrix.get((source_q.id, target_q.id), 0.0)
        if abs(coupling) < 1e-8:
            continue
        shift = coupled_field_shift(source_q, source_result, target_q, coupling, gain)
        if np.any(np.abs(shift) > 1e-6):
            shifts[target_q.id] = shift
    return shifts
