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
        # High-alpha agents in the majority get conviction reinforcement
        civ.alpha[:] = 0.7
        settled = np.full(civ.n, 0.8)  # all agree (majority = yes)
        q = QUESTIONS[0]
        r = run_question(q, civ)
        alpha_before = civ.alpha.mean()
        opinion_feedback(civ, settled, q, r.force_anatomy)
        assert civ.alpha.mean() > alpha_before


class TestRecomputeForcesRetired:
    def test_global_rebuild_raises(self):
        """2026-08-16 audit: the global rebuild erased genesis/regional
        priors for ~84% of agents with zero trait changes. Retirement is
        pinned — reviving it must fail loudly."""
        import pytest
        civ = _mutable_civ()
        with pytest.raises(RuntimeError, match="retired"):
            _recompute_forces(civ)


class TestAuditSemantics:
    """External audit (2026-08-16): sign-aware reinforcement + prior
    preservation. These are semantic tests — they check the physics
    means what it claims, not just that shapes line up."""

    def _civ(self):
        from earth1.genesis import genesis
        from earth1.tick import _make_mutable
        return _make_mutable(genesis(4000, seed=11))

    def test_no_strong_agents_is_identity_on_forces(self):
        import numpy as np
        from earth1.feedback import opinion_feedback
        from earth1.types import Question
        civ = self._civ()
        before = civ.forces.copy()
        settled = np.full(civ.n, 0.7)          # nobody strong, nobody ambivalent
        q = Question(id="t", text="t", domain="belief_causal",
                     baseline=0.5, weights=np.ones(8))
        opinion_feedback(civ, settled, q, np.ones(8))
        assert np.allclose(civ.forces, before), \
            "feedback with no eligible agents must not touch forces"

    def _reinforcement_helps(self, weight_sign):
        """Strong-YES agents' predicted stance must not DECREASE after
        reinforcement — for BOTH weight polarities."""
        import numpy as np
        from earth1.feedback import opinion_feedback
        from earth1.forces import project_all
        from earth1.types import Question, Force
        civ = self._civ()
        weights = np.zeros(8)
        weights[int(Force.FEAR)] = 6.0 * weight_sign
        q = Question(id="t", text="t", domain="belief_causal",
                     baseline=0.5, weights=weights)
        stance = project_all(civ, q)
        strong_yes = stance > 0.8
        if strong_yes.sum() < 10:
            # engineer some strong-yes agents by construction
            settled = np.where(np.arange(civ.n) % 3 == 0, 0.95, 0.5)
        else:
            settled = stance
        anatomy = np.zeros(8); anatomy[int(Force.FEAR)] = 1.0
        yes_mask = settled > 0.8
        before = project_all(civ, q)[yes_mask].mean()
        opinion_feedback(civ, settled, q, anatomy, learning_rate=0.05)
        after = project_all(civ, q)[yes_mask].mean()
        assert after >= before - 1e-9, (
            f"reinforcement moved strong-YES agents AWAY from YES "
            f"(weight_sign={weight_sign}: {before:.4f} -> {after:.4f})")

    def test_reinforcement_positive_weight(self):
        self._reinforcement_helps(+1.0)

    def test_reinforcement_negative_weight(self):
        """The audit's measured bug: negative-weight dominant force made
        'reinforced' agents LESS aligned with their own stance."""
        self._reinforcement_helps(-1.0)

    def test_regional_priors_survive_feedback(self):
        """Only nudged agents' affected channels change — the ~84%-of-
        agents force rewrite from the retired global rebuild is gone."""
        import numpy as np
        from earth1.feedback import opinion_feedback
        from earth1.types import Question, Force
        civ = self._civ()
        before = civ.forces.copy()
        settled = np.full(civ.n, 0.5)
        settled[:100] = 0.95                    # only 100 strong-yes agents
        settled[100:] = 0.7                     # rest untouched (not ambivalent)
        weights = np.zeros(8); weights[int(Force.FEAR)] = 3.0
        anatomy = np.zeros(8); anatomy[int(Force.FEAR)] = 1.0
        q = Question(id="t", text="t", domain="belief_causal",
                     baseline=0.5, weights=weights)
        opinion_feedback(civ, settled, q, anatomy)
        untouched = np.arange(civ.n) >= 100
        assert np.allclose(civ.forces[untouched], before[untouched]), \
            "agents outside the nudged set had their forces rewritten"
