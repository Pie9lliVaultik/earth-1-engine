"""Tests for cross-question coupling — topic interference."""
import numpy as np
import pytest

from earth1.coupling import (
    compute_coupling,
    build_coupling_matrix,
    coupled_field_shift,
    compute_all_shifts,
)
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.questions import QUESTIONS
from earth1.types import Question, RunResult, Force, NUM_FORCES


@pytest.fixture(scope="module")
def civ():
    return genesis(pop=10_000, seed=42, min_per_country=10)


@pytest.fixture(scope="module")
def question_map():
    return {q.id: q for q in QUESTIONS}


class TestComputeCoupling:
    def test_identical_weights_full_coupling(self):
        q = QUESTIONS[0]
        assert abs(compute_coupling(q, q) - 1.0) < 1e-10

    def test_symmetric(self):
        q1, q2 = QUESTIONS[0], QUESTIONS[1]
        assert compute_coupling(q1, q2) == compute_coupling(q2, q1)

    def test_zero_weight_question(self):
        q1 = QUESTIONS[0]
        q_zero = Question(
            id="zero", text="zero", domain="test",
            weights=np.zeros(NUM_FORCES), baseline=0.0,
        )
        assert compute_coupling(q1, q_zero) == 0.0

    def test_orthogonal_weights(self):
        q1 = Question(id="a", text="a", domain="test",
                      weights=np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=float),
                      baseline=0.0)
        q2 = Question(id="b", text="b", domain="test",
                      weights=np.array([0, 1, 0, 0, 0, 0, 0, 0], dtype=float),
                      baseline=0.0)
        assert compute_coupling(q1, q2) == 0.0

    def test_threshold_filters_weak_coupling(self):
        q1 = Question(id="a", text="a", domain="test",
                      weights=np.array([1, 0, 0, 0, 0, 0, 0, 0.1], dtype=float),
                      baseline=0.0)
        q2 = Question(id="b", text="b", domain="test",
                      weights=np.array([0, 0, 0, 0, 0, 0, 0, 1], dtype=float),
                      baseline=0.0)
        # cosine similarity is small; should be filtered by threshold
        assert compute_coupling(q1, q2, threshold=0.5) == 0.0

    def test_real_questions_have_some_coupling(self):
        # At least some question pairs should have non-zero coupling
        n_nonzero = 0
        for i in range(len(QUESTIONS)):
            for j in range(i + 1, len(QUESTIONS)):
                if compute_coupling(QUESTIONS[i], QUESTIONS[j]) != 0.0:
                    n_nonzero += 1
        assert n_nonzero > 0


class TestBuildCouplingMatrix:
    def test_matrix_symmetric(self):
        matrix = build_coupling_matrix(QUESTIONS[:5])
        for (k1, k2), v in matrix.items():
            assert (k2, k1) in matrix
            assert abs(matrix[(k2, k1)] - v) < 1e-10

    def test_excludes_external_substrate(self):
        matrix = build_coupling_matrix(QUESTIONS)
        for (k1, k2) in matrix.keys():
            assert k1 != "rain"
            assert k2 != "rain"

    def test_no_self_coupling(self):
        matrix = build_coupling_matrix(QUESTIONS)
        for (k1, k2) in matrix.keys():
            assert k1 != k2


class TestCoupledFieldShift:
    def test_zero_coupling_no_shift(self, civ):
        q1, q2 = QUESTIONS[0], QUESTIONS[1]
        r = run_question(q1, civ)
        shift = coupled_field_shift(q1, r, q2, coupling=0.0)
        assert np.all(shift == 0)

    def test_shift_shape(self, civ):
        q1, q2 = QUESTIONS[0], QUESTIONS[1]
        r = run_question(q1, civ)
        coupling = compute_coupling(q1, q2)
        shift = coupled_field_shift(q1, r, q2, coupling)
        assert shift.shape == (NUM_FORCES,)

    def test_strong_result_larger_shift(self, civ, question_map):
        q1, q2 = question_map["ssm"], question_map["abortion"]
        r = run_question(q1, civ)
        coupling = compute_coupling(q1, q2)
        assert abs(coupling) > 0.5
        shift_low = coupled_field_shift(q1, r, q2, coupling, gain=0.01)
        shift_high = coupled_field_shift(q1, r, q2, coupling, gain=0.10)
        assert np.linalg.norm(shift_high) > np.linalg.norm(shift_low)

    def test_shift_proportional_to_conviction(self, civ, question_map):
        q1, q2 = question_map["ssm"], question_map["abortion"]
        r = run_question(q1, civ)
        coupling = compute_coupling(q1, q2)
        shift = coupled_field_shift(q1, r, q2, coupling, gain=1.0)
        expected_scale = abs(coupling * r.conviction * (1.0 - r.fragility) * (r.yes_pct - 0.5))
        actual_scale = np.linalg.norm(shift) / np.linalg.norm(r.force_anatomy)
        assert abs(actual_scale - expected_scale) < 0.01


class TestComputeAllShifts:
    def test_no_self_shift(self, civ, question_map):
        q = QUESTIONS[0]
        r = run_question(q, civ)
        matrix = build_coupling_matrix(QUESTIONS)
        shifts = compute_all_shifts(q, r, QUESTIONS, matrix)
        assert q.id not in shifts

    def test_shifts_only_for_coupled_questions(self, civ, question_map):
        q = QUESTIONS[0]
        r = run_question(q, civ)
        matrix = build_coupling_matrix(QUESTIONS)
        shifts = compute_all_shifts(q, r, QUESTIONS, matrix)
        for target_id in shifts:
            assert (q.id, target_id) in matrix

    def test_rain_excluded(self, civ, question_map):
        q = QUESTIONS[0]
        r = run_question(q, civ)
        matrix = build_coupling_matrix(QUESTIONS)
        shifts = compute_all_shifts(q, r, QUESTIONS, matrix)
        assert "rain" not in shifts

    def test_shift_values_are_arrays(self, civ, question_map):
        q = QUESTIONS[0]
        r = run_question(q, civ)
        matrix = build_coupling_matrix(QUESTIONS)
        shifts = compute_all_shifts(q, r, QUESTIONS, matrix)
        for shift in shifts.values():
            assert isinstance(shift, np.ndarray)
            assert shift.shape == (NUM_FORCES,)
