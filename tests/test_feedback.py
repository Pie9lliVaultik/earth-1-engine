"""Tests for opinion-trait feedback — the inner learning loop."""
import numpy as np
import pytest
import copy

from earth1.feedback import opinion_feedback, _recompute_forces
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.questions import QUESTIONS
from earth1.types import Force, NUM_FORCES


def _mutable_civ(pop=5_000, seed=42):
    """Create a civilization with writable arrays."""
    civ = genesis(pop=pop, seed=seed, min_per_country=10)
    # Make arrays writable by copying
    for attr in ["openness", "empathy", "risk_appetite", "doubt",
                 "desire_intensity", "economic_field", "culture_offset",
                 "conscientiousness", "agreeableness", "extraversion",
                 "neuroticism", "power_distance", "individualism",
                 "uncertainty_avoidance", "long_term_orientation",
                 "forces", "alpha", "means", "age"]:
        arr = getattr(civ, attr)
        if isinstance(arr, np.ndarray) and not arr.flags.writeable:
            object.__setattr__(civ, attr, arr.copy())
    return civ


class TestOpinionFeedback:
    def test_feedback_returns_stats(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        r = run_question(q, civ)
        settled = np.full(civ.n, r.yes_pct)
        stats = opinion_feedback(civ, settled, q, r.force_anatomy)
        assert "n_strong_yes" in stats
        assert "n_strong_no" in stats
        assert "dominant_force" in stats

    def test_strong_positions_shift_traits(self):
        civ = _mutable_civ()
        # Force extreme stances
        settled = np.zeros(civ.n)
        settled[:2500] = 0.9  # strong yes
        settled[2500:] = 0.1  # strong no

        openness_before = civ.openness.copy()
        q = QUESTIONS[0]  # ssm — identity dominant
        r = run_question(q, civ)
        opinion_feedback(civ, settled, q, r.force_anatomy, learning_rate=0.1)

        # Traits should have shifted
        assert not np.array_equal(civ.openness, openness_before)

    def test_ambivalent_agents_get_more_doubt(self):
        civ = _mutable_civ()
        settled = np.full(civ.n, 0.5)  # all ambivalent
        doubt_before = civ.doubt.mean()
        q = QUESTIONS[0]
        r = run_question(q, civ)
        opinion_feedback(civ, settled, q, r.force_anatomy)
        assert civ.doubt.mean() > doubt_before

    def test_forces_recomputed_after_feedback(self):
        civ = _mutable_civ()
        forces_before = civ.forces.copy()
        settled = np.zeros(civ.n)
        settled[:2500] = 0.9
        settled[2500:] = 0.1
        q = QUESTIONS[0]
        r = run_question(q, civ)
        opinion_feedback(civ, settled, q, r.force_anatomy, learning_rate=0.1)
        assert not np.array_equal(civ.forces, forces_before)

    def test_feedback_bounded(self):
        civ = _mutable_civ()
        settled = np.full(civ.n, 0.95)
        q = QUESTIONS[0]
        r = run_question(q, civ)
        for _ in range(50):
            opinion_feedback(civ, settled, q, r.force_anatomy, learning_rate=0.1)
        # All traits should stay bounded [0, 1]
        for attr in ["openness", "doubt", "risk_appetite", "individualism"]:
            arr = getattr(civ, attr)
            assert arr.min() >= 0, f"{attr} min={arr.min()}"
            assert arr.max() <= 1, f"{attr} max={arr.max()}"

    def test_repeated_feedback_produces_drift(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        initial_result = run_question(q, civ)

        for _ in range(20):
            r = run_question(q, civ)
            settled = np.where(np.random.default_rng(42).random(civ.n) < r.yes_pct, 0.85, 0.15)
            opinion_feedback(civ, settled, q, r.force_anatomy, learning_rate=0.05)

        final_result = run_question(q, civ)
        assert abs(final_result.yes_pct - initial_result.yes_pct) > 0.001

    def test_alpha_reinforcement(self):
        civ = _mutable_civ()
        # Set openness high so computed alpha > 0.6
        civ.openness[:] = 0.9
        _recompute_forces(civ)
        assert civ.alpha.mean() > 0.6
        settled = np.full(civ.n, 0.8)  # all agree (majority = yes)
        q = QUESTIONS[0]
        r = run_question(q, civ)
        alpha_before = civ.alpha.mean()
        opinion_feedback(civ, settled, q, r.force_anatomy)
        assert civ.alpha.mean() > alpha_before


class TestRecomputeForces:
    def test_forces_match_formulas(self):
        civ = _mutable_civ()
        _recompute_forces(civ)
        expected_fear = np.clip(
            (civ.doubt + (1.0 - civ.risk_appetite) + civ.neuroticism * 0.3) / 2.3, 0, 1)
        assert np.allclose(civ.forces[:, Force.FEAR], expected_fear, atol=1e-10)

    def test_experience_is_age(self):
        civ = _mutable_civ()
        _recompute_forces(civ)
        assert np.allclose(civ.forces[:, Force.EXPERIENCE], civ.age)

    def test_means_updated(self):
        civ = _mutable_civ()
        civ.openness[:] = 0.9
        _recompute_forces(civ)
        assert civ.means[Force.IDENTITY] > 0.6
