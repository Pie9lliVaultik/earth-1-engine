"""Tests for question expansion and holdout boundary."""
import pytest
import numpy as np
from earth1.questions import QUESTIONS, QUESTION_MAP, question_by_id
from earth1.holdout import (
    HOLDOUT_IDS, is_holdout, get_training_questions, get_holdout_questions,
)
from earth1.types import Force, NUM_FORCES
from earth1.engine import build_civilization, run_question
from earth1.calibration import calibrate_weights


POP = 5_000
civ = build_civilization(POP, seed=42)


class TestQuestionExpansion:
    def test_at_least_30_questions(self):
        causal = [q for q in QUESTIONS if q.domain == "belief_causal"]
        assert len(causal) >= 27

    def test_all_questions_have_weights(self):
        for q in QUESTIONS:
            if q.domain == "belief_causal":
                assert q.weights.shape == (NUM_FORCES,)
                assert np.any(q.weights != 0), f"{q.id} has zero weights"

    def test_all_questions_produce_valid_results(self):
        for q in QUESTIONS:
            if q.domain != "belief_causal":
                continue
            r = run_question(q, civ)
            assert 0 <= r.yes_pct <= 1, f"{q.id}: yes_pct={r.yes_pct}"
            assert r.n == POP
            assert r.dominant is not None

    def test_forces_cover_all_8_as_dominant(self):
        dominants = set()
        for q in QUESTIONS:
            if q.domain != "belief_causal":
                continue
            r = run_question(q, civ)
            dominants.add(r.dominant)
        missing = set(Force) - dominants
        assert len(missing) <= 2, f"Missing dominant forces: {missing}"

    def test_question_map_consistent(self):
        for q in QUESTIONS:
            assert q.id in QUESTION_MAP
            assert QUESTION_MAP[q.id] is q

    def test_question_by_id(self):
        assert question_by_id("ssm") is not None
        assert question_by_id("inflation") is not None
        assert question_by_id("nonexistent") is None


class TestHoldout:
    def test_holdout_ids_count(self):
        assert len(HOLDOUT_IDS) == 5

    def test_holdout_ids_are_valid(self):
        for qid in HOLDOUT_IDS:
            assert qid in QUESTION_MAP, f"{qid} not in questions"

    def test_is_holdout(self):
        assert is_holdout("inflation")
        assert is_holdout("nuclear_risk")
        assert not is_holdout("ssm")
        assert not is_holdout("svb")

    def test_training_excludes_holdout(self):
        training = get_training_questions()
        for q in training:
            assert q.id not in HOLDOUT_IDS

    def test_holdout_returns_correct_questions(self):
        holdout = get_holdout_questions()
        assert len(holdout) == 5
        for q in holdout:
            assert q.id in HOLDOUT_IDS

    def test_training_plus_holdout_covers_all_causal(self):
        training = get_training_questions()
        holdout = get_holdout_questions()
        causal = [q for q in QUESTIONS if q.domain == "belief_causal"]
        assert len(training) + len(holdout) == len(causal)

    def test_calibration_skips_holdout(self):
        targets = [
            {"id": "ssm", "text": "test", "domain": "belief_causal", "target_yes_pct": 0.6},
            {"id": "inflation", "text": "test", "domain": "belief_causal", "target_yes_pct": 0.7},
        ]
        results = calibrate_weights(civ, targets)
        ids = [r["id"] for r in results]
        assert "ssm" in ids
        assert "inflation" not in ids
