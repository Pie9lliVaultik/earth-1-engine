"""Confidence scoring — algorithmic similarity to the benchmark set.

Bible §36 accuracy regimes:
  calibrated      — similarity ≥ 0.85 to a benchmark question
  transitional    — similarity 0.65–0.85
  forward_estimate — similarity < 0.65

No LLM call.  Pure vector cosine + keyword overlap.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from earth1.types import Question
from earth1.benchmark_questions import BENCHMARK_QUESTIONS, BenchmarkQuestion


@dataclass
class ConfidenceScore:
    regime: str
    similarity: float
    nearest_id: str
    nearest_text: str
    weight_cosine: float
    keyword_overlap: float


def _tokenize(text: str) -> set:
    return set(text.lower().replace("?", "").replace("'", "").split())


_STOP = {"do", "does", "is", "are", "the", "a", "an", "in", "of", "to",
         "and", "or", "for", "with", "your", "their", "that", "it",
         "be", "have", "has", "not", "people", "most", "should", "generally"}


def _content_tokens(text: str) -> set:
    return _tokenize(text) - _STOP


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _keyword_overlap(a: str, b: str) -> float:
    ta = _content_tokens(a)
    tb = _content_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _lens_bonus(lens_a: str, lens_b: str) -> float:
    if lens_a and lens_b and lens_a.lower() == lens_b.lower():
        return 0.1
    return 0.0


def score_confidence(
    question: Question,
    benchmark: Optional[List[BenchmarkQuestion]] = None,
) -> ConfidenceScore:
    if benchmark is None:
        benchmark = BENCHMARK_QUESTIONS

    best_sim = -1.0
    best_bq = benchmark[0]
    best_cosine = 0.0
    best_kw = 0.0

    for bq in benchmark:
        wc = _cosine(question.weights, bq.weights)
        kw = _keyword_overlap(question.text, bq.text)
        lb = _lens_bonus(question.lens, bq.lens)
        sim = 0.55 * wc + 0.30 * kw + 0.15 * lb
        sim = max(0.0, min(1.0, sim))

        if sim > best_sim:
            best_sim = sim
            best_bq = bq
            best_cosine = wc
            best_kw = kw

    if best_sim >= 0.85:
        regime = "calibrated"
    elif best_sim >= 0.65:
        regime = "transitional"
    else:
        regime = "forward_estimate"

    return ConfidenceScore(
        regime=regime,
        similarity=round(best_sim, 4),
        nearest_id=best_bq.id,
        nearest_text=best_bq.text,
        weight_cosine=round(best_cosine, 4),
        keyword_overlap=round(best_kw, 4),
    )
