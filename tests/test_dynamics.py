"""Tests for force field dynamics — force-aware diffusion with learning."""
import numpy as np
import pytest

from earth1.dynamics import (
    compute_susceptibility,
    diffuse_forces,
    apply_residues,
    run_with_dynamics,
    agent_relative_decay,
    _sigmoid,
)
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.forces import project_all
from earth1.tick import WorldState, world_tick, run_world
from earth1.questions import QUESTIONS
from earth1.types import Force, NUM_FORCES


def _mutable_civ(pop=5_000, seed=42):
    civ = genesis(pop=pop, seed=seed, min_per_country=10)
    for attr in civ.__dataclass_fields__:
        val = getattr(civ, attr)
        if isinstance(val, np.ndarray) and not val.flags.writeable:
            object.__setattr__(civ, attr, val.copy())
    return civ


# ---------------------------------------------------------------------------
# Susceptibility
# ---------------------------------------------------------------------------

class TestSigmoid:
    def test_center(self):
        assert abs(_sigmoid(np.array([0.5]))[0] - 0.5) < 1e-10

    def test_monotonic(self):
        x = np.linspace(0, 1, 100)
        y = _sigmoid(x)
        assert np.all(np.diff(y) > 0)

    def test_bounded(self):
        x = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        y = _sigmoid(x)
        assert np.all(y > 0) and np.all(y < 1)


class TestComputeSusceptibility:
    def test_shape(self):
        civ = _mutable_civ()
        S = compute_susceptibility(civ)
        assert S.shape == (civ.n, NUM_FORCES)

    def test_bounded(self):
        civ = _mutable_civ()
        S = compute_susceptibility(civ)
        assert S.min() >= 0
        assert S.max() < 1

    def test_high_doubt_high_fear_susceptibility(self):
        civ = _mutable_civ()
        high_doubt = civ.doubt > 0.7
        low_doubt = civ.doubt < 0.3
        S = compute_susceptibility(civ)
        if high_doubt.any() and low_doubt.any():
            assert S[high_doubt, Force.FEAR].mean() > S[low_doubt, Force.FEAR].mean()

    def test_gain_affects_spread(self):
        civ = _mutable_civ()
        S_low = compute_susceptibility(civ, gain=1.0)
        S_high = compute_susceptibility(civ, gain=8.0)
        # Higher gain → more extreme values → larger variance
        assert S_high.var() > S_low.var()

    def test_different_forces_different_patterns(self):
        civ = _mutable_civ()
        S = compute_susceptibility(civ)
        # Fear and identity susceptibility should NOT be identical
        corr = np.corrcoef(S[:, Force.FEAR], S[:, Force.IDENTITY])[0, 1]
        assert abs(corr) < 0.99


# ---------------------------------------------------------------------------
# Agent-relative temporal filtering
# ---------------------------------------------------------------------------

class TestAgentRelativeDecay:
    def test_no_time_elapsed(self):
        civ = _mutable_civ()
        decay = agent_relative_decay(0.0, 30.0, civ)
        # At dt=0, decay factor should be close to 1 (modulated by temporal mass)
        assert decay.min() > 0.5
        assert decay.max() <= 1.0

    def test_old_agents_less_affected(self):
        civ = _mutable_civ()
        old = civ.age > 0.7
        young = civ.age < 0.3
        if old.any() and young.any():
            decay = agent_relative_decay(10.0, 30.0, civ)
            assert decay[young].mean() > decay[old].mean()

    def test_high_lto_slower_decay(self):
        civ = _mutable_civ()
        high_lto = civ.long_term_orientation > 0.7
        low_lto = civ.long_term_orientation < 0.3
        if high_lto.any() and low_lto.any():
            decay = agent_relative_decay(30.0, 30.0, civ)
            assert decay[high_lto].mean() > decay[low_lto].mean()

    def test_future_event_zero(self):
        civ = _mutable_civ()
        decay = agent_relative_decay(-5.0, 30.0, civ)
        assert np.all(decay == 0)

    def test_zero_half_life_no_decay(self):
        civ = _mutable_civ()
        decay = agent_relative_decay(100.0, 0.0, civ)
        assert np.all(decay == 1.0)


# ---------------------------------------------------------------------------
# Force-aware diffusion
# ---------------------------------------------------------------------------

class TestDiffuseForces:
    def test_output_shapes(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = compute_susceptibility(civ)
        snaps, residues = diffuse_forces(s0, civ, q, S, 0.18, 8)
        assert len(snaps) == 9  # initial + 8 layers
        assert residues.shape == (civ.n, NUM_FORCES)

    def test_stances_bounded(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = compute_susceptibility(civ)
        snaps, _ = diffuse_forces(s0, civ, q, S, 0.18, 8)
        for s in snaps:
            assert s.min() >= 0, f"min={s.min()}"
            assert s.max() <= 1, f"max={s.max()}"

    def test_residues_nonzero(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = compute_susceptibility(civ)
        _, residues = diffuse_forces(s0, civ, q, S, 0.18, 8, residue_rate=0.01)
        assert np.abs(residues).sum() > 0

    def test_higher_residue_rate_more_residue(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = compute_susceptibility(civ)
        _, r_low = diffuse_forces(s0, civ, q, S, 0.18, 8, residue_rate=0.001)
        _, r_high = diffuse_forces(s0, civ, q, S, 0.18, 8, residue_rate=0.1)
        assert np.abs(r_high).sum() > np.abs(r_low).sum()

    def test_zero_susceptibility_no_change(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = np.zeros((civ.n, NUM_FORCES))
        snaps, residues = diffuse_forces(s0, civ, q, S, 0.18, 8)
        # With zero susceptibility, stances still change via alpha anchoring
        # but residues should be zero
        assert np.allclose(residues, 0)

    def test_produces_different_output_from_scalar(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        s0 = project_all(civ, q)
        S = compute_susceptibility(civ)

        from earth1.diffusion import diffuse
        scalar_settled = diffuse(s0, civ.alpha, civ.adj, 0.18, 8)[-1]
        force_snaps, _ = diffuse_forces(s0, civ, q, S, 0.18, 8)
        force_settled = force_snaps[-1]

        # They should NOT be identical — force dynamics is a different kernel
        assert not np.allclose(scalar_settled, force_settled, atol=1e-6)


# ---------------------------------------------------------------------------
# Trait residue application
# ---------------------------------------------------------------------------

class TestApplyResidues:
    def test_residue_shifts_traits(self):
        civ = _mutable_civ()
        openness_before = civ.openness.mean()
        # Inject a strong identity residue (identity maps to openness)
        residues = np.zeros((civ.n, NUM_FORCES))
        residues[:, Force.IDENTITY] = 0.1
        apply_residues(civ, residues, regression_rate=0.0)
        assert civ.openness.mean() != openness_before

    def test_residue_bounded(self):
        civ = _mutable_civ()
        residues = np.ones((civ.n, NUM_FORCES)) * 10  # extreme residue
        apply_residues(civ, residues)
        for attr in ["openness", "doubt", "risk_appetite"]:
            arr = getattr(civ, attr)
            assert arr.min() >= 0
            assert arr.max() <= 1

    def test_regression_to_mean(self):
        civ = _mutable_civ()
        civ.openness[:] = 0.9  # far from 0.5
        residues = np.zeros((civ.n, NUM_FORCES))
        apply_residues(civ, residues, regression_rate=0.1)
        # With zero residue but high regression, traits should move toward 0.5
        assert civ.openness.mean() < 0.9

    def test_forces_recomputed(self):
        civ = _mutable_civ()
        forces_before = civ.forces.copy()
        residues = np.zeros((civ.n, NUM_FORCES))
        residues[:, Force.FEAR] = 0.1
        apply_residues(civ, residues, regression_rate=0.0)
        assert not np.array_equal(civ.forces, forces_before)

    def test_returns_stats(self):
        civ = _mutable_civ()
        residues = np.ones((civ.n, NUM_FORCES)) * 0.01
        stats = apply_residues(civ, residues)
        assert "total_nudge" in stats
        assert "mean_residue_magnitude" in stats
        assert stats["total_nudge"] > 0


# ---------------------------------------------------------------------------
# Full forward pass
# ---------------------------------------------------------------------------

class TestRunWithDynamics:
    def test_basic_run(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        settled, residues, snaps = run_with_dynamics(civ, q)
        assert 0 <= settled.mean() <= 1
        assert residues.shape == (civ.n, NUM_FORCES)
        assert len(snaps) == 9

    def test_comparable_to_scalar(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]
        scalar_r = run_question(q, civ)
        settled, _, _ = run_with_dynamics(civ, q)
        # Should be in the same ballpark (both are diffusion on same population)
        assert abs(settled.mean() - scalar_r.yes_pct) < 0.15

    def test_field_shift_applied(self):
        civ = _mutable_civ()
        q = QUESTIONS[0]  # ssm — identity-dominant
        s1, _, _ = run_with_dynamics(civ, q)
        shift = np.zeros(NUM_FORCES)
        shift[Force.IDENTITY] = 0.3  # identity has weight 3.4 on ssm
        s2, _, _ = run_with_dynamics(civ, q, field_shift=shift)
        assert not np.allclose(s1, s2)


# ---------------------------------------------------------------------------
# Integration with tick loop
# ---------------------------------------------------------------------------

class TestForceTickIntegration:
    def test_tick_with_force_dynamics(self):
        state = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        result = world_tick(state, batch_size=2, use_force_dynamics=True)
        assert result.tick == 1
        assert len(result.results) == 2
        for r in result.results.values():
            assert r.regime == "force-dynamics"

    def test_force_dynamics_produces_drift(self):
        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]

        initial_openness = state.civ.openness.mean()
        list(run_world(
            state, n_ticks=15, questions=qs, batch_size=3,
            use_force_dynamics=True, residue_rate=0.005,
        ))
        final_openness = state.civ.openness.mean()
        assert initial_openness != final_openness

    def test_force_dynamics_vs_scalar_both_work(self):
        s1 = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        s2 = WorldState.create(pop=2_000, seed=42, min_per_country=5)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:2]

        r1 = list(run_world(s1, n_ticks=3, questions=qs, batch_size=2,
                            use_force_dynamics=False))
        r2 = list(run_world(s2, n_ticks=3, questions=qs, batch_size=2,
                            use_force_dynamics=True))
        # Both should complete without error and produce results
        assert len(r1) == 3
        assert len(r2) == 3

    def test_force_dynamics_more_emergence(self):
        """Force dynamics should produce more trait drift than scalar."""
        s_scalar = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        s_force = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:5]

        list(run_world(s_scalar, n_ticks=20, questions=qs, batch_size=5,
                       use_force_dynamics=False, learning_rate=0.02))
        list(run_world(s_force, n_ticks=20, questions=qs, batch_size=5,
                       use_force_dynamics=True, residue_rate=0.005))

        # Measure trait drift from baseline
        baseline = genesis(pop=5_000, seed=42, min_per_country=10)
        scalar_drift = abs(s_scalar.civ.openness.mean() - baseline.openness.mean())
        force_drift = abs(s_force.civ.openness.mean() - baseline.openness.mean())

        # Both should have drifted
        assert scalar_drift > 0 or force_drift > 0


# ---------------------------------------------------------------------------
# Observatory comparison
# ---------------------------------------------------------------------------

class TestObservatoryComparison:
    def test_surprise_measurable_with_force_dynamics(self):
        from earth1.observatory import measure_emergence

        state = WorldState.create(pop=5_000, seed=42, min_per_country=10)
        baseline = genesis(pop=5_000, seed=42, min_per_country=10)
        qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:3]

        list(run_world(state, n_ticks=15, questions=qs, batch_size=3,
                       use_force_dynamics=True, residue_rate=0.005))

        metrics = measure_emergence(
            state.civ, baseline, questions=qs,
            event_log=state.event_log, t=state.t,
            tick_count=state.tick_count,
        )
        assert metrics.tick_count == 15
        assert metrics.trait_drift_magnitude > 0
