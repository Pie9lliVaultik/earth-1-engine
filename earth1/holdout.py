"""Holdout boundary — questions reserved for out-of-sample validation."""
from __future__ import annotations
from typing import List
from earth1.questions import QUESTIONS
from earth1.types import Question

HOLDOUT_IDS = {"inflation", "nuclear_risk", "abortion", "genetic_editing", "democracy_trust"}


def is_holdout(question_id: str) -> bool:
    return question_id in HOLDOUT_IDS


def get_training_questions() -> List[Question]:
    return [q for q in QUESTIONS if q.domain == "belief_causal" and q.id not in HOLDOUT_IDS]


def get_holdout_questions() -> List[Question]:
    return [q for q in QUESTIONS if q.id in HOLDOUT_IDS]
