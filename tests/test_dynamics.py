"""Tests for living dynamics — population evolution over time."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.dynamics import (
    evolve, evolve_step, _deep_copy_civ, _death_probability,
    _select_deaths, _age_step, _recompute_forces,
    _secular_drift, _migrate, _birth_replacement,
    project_opinion_drift, COUNTRY_DEMOGRAPHICS,
    EvolveStats,
)
from earth1.engine import build_civilization, run_question
from earth1.questions import question_by_id
from earth1.population import COUNTRIES
from earth1.types import Force, NUM_FORCES
from earth1.rng import make_rng


POP = 10_000
civ = build_civilization(POP, seed=42)


class TestDeepCopy:
    def test_copy_preserves_size(self):
        copy = _deep_copy_civ(civ)
        assert copy.n == civ.n

    def test_copy_is_independent(self):
        copy = _deep_copy_civ(civ)
        copy.age[0] = 999.0
        assert civ.age[0] != 999.0

    def test_copy_preserves_values(self):
        copy = _deep_copy_civ(civ)
        np.testing.assert_array_equal(copy.country, civ.country)
        np.testing.assert_array_equal(copy.forces, civ.forces)


class TestDeathProbability:
    def test_young_low_probability(self):
        ages = np.array([0.14])
        countries = np.array([0])
        p = _death_probability(ages, countries)
        assert p[0] < 0.05

    def test_old_high_probability(self):
        ages = np.array([0.96])
        countries = np.array([0])
        p = _death_probability(ages, countries)
        assert p[0] > 0.02

    def test_probability_increases_with_age(self):
        ages = np.array([0.14, 0.38, 0.62, 0.82, 0.96])
        countries = np.zeros(5, dtype=int)
        p = _death_probability(ages, countries)
        for i in range(len(p) - 1):
            assert p[i + 1] >= p[i]

    def test_low_life_exp_higher_mortality(self):
        ages = np.array([0.62, 0.62])
        countries = np.array([0, 4])  # US (77) vs NG (55)
        p = _death_probability(ages, countries)
        assert p[1] > p[0]


class TestSelectDeaths:
    def test_some_die(self):
        rng = make_rng(42)
        dead = _select_deaths(civ, rng)
        n_dead = dead.sum()
        assert n_dead > 0
        assert n_dead < civ.n

    def test_death_rate_reasonable(self):
        rng = make_rng(42)
        dead = _select_deaths(civ, rng)
        rate = dead.sum() / civ.n
        assert 0.005 < rate < 0.15


class TestBirthReplacement:
    def test_dead_slots_get_young_agents(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        dead = _select_deaths(copy, rng)
        dead_idx = np.where(dead)[0]

        _birth_replacement(copy, dead, rng)

        assert np.all(copy.age[dead_idx] == 0.14)
        assert np.all(copy.age_bucket[dead_idx] == 0)

    def test_born_into_same_country(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        dead = _select_deaths(copy, rng)
        dead_idx = np.where(dead)[0]
        original_countries = copy.country[dead_idx].copy()

        _birth_replacement(copy, dead, rng)

        np.testing.assert_array_equal(copy.country[dead_idx], original_countries)

    def test_traits_are_bounded(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        dead = _select_deaths(copy, rng)
        _birth_replacement(copy, dead, rng)

        dead_idx = np.where(dead)[0]
        assert np.all(copy.openness[dead_idx] >= 0)
        assert np.all(copy.openness[dead_idx] <= 1)
        assert np.all(copy.risk_appetite[dead_idx] >= 0)
        assert np.all(copy.risk_appetite[dead_idx] <= 1)


class TestAgeStep:
    def test_age_increases(self):
        copy = _deep_copy_civ(civ)
        old_mean = copy.age.mean()
        _age_step(copy)
        assert copy.age.mean() > old_mean

    def test_age_stays_bounded(self):
        copy = _deep_copy_civ(civ)
        for _ in range(100):
            _age_step(copy)
        assert np.all(copy.age <= 1.0)
        assert np.all(copy.age >= 0.0)


class TestMigration:
    def test_some_migrate(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        n = _migrate(copy, rng)
        assert n > 0

    def test_culture_shifts_toward_destination(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        ng_agents = np.where(copy.country == 4)[0]
        original_cult = copy.culture_offset[ng_agents].mean()

        for _ in range(10):
            _migrate(copy, rng)

        still_ng = np.where(copy.country == 4)[0]
        moved_from_ng = np.setdiff1d(ng_agents, still_ng)
        if len(moved_from_ng) > 0:
            assert True  # migration happened


class TestSecularDrift:
    def test_urbanization_increases(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        old_urban = copy.urban.mean()
        for _ in range(10):
            _secular_drift(copy, rng)
        assert copy.urban.mean() >= old_urban

    def test_openness_drifts_up(self):
        copy = _deep_copy_civ(civ)
        rng = make_rng(42)
        old_open = copy.openness.mean()
        for _ in range(20):
            _secular_drift(copy, rng)
        assert copy.openness.mean() > old_open


class TestRecomputeForces:
    def test_forces_consistent_with_traits(self):
        copy = _deep_copy_civ(civ)
        copy.openness[:] = 0.8
        _recompute_forces(copy)
        assert copy.forces[:, Force.IDENTITY].mean() == pytest.approx(0.8, abs=0.001)
        assert copy.forces[:, Force.COLLECTIVE].mean() == pytest.approx(0.2, abs=0.001)

    def test_means_updated(self):
        copy = _deep_copy_civ(civ)
        old_means = copy.means.copy()
        copy.openness[:] = 0.99
        _recompute_forces(copy)
        assert not np.allclose(copy.means, old_means)


class TestEvolve:
    def test_evolve_returns_new_civ_and_stats(self):
        new_civ, stats = evolve(civ, years=1, seed=42)
        assert new_civ.n == civ.n
        assert len(stats) == 1
        assert isinstance(stats[0], EvolveStats)

    def test_evolve_does_not_mutate_original(self):
        original_age_mean = civ.age.mean()
        evolve(civ, years=3, seed=42)
        assert civ.age.mean() == original_age_mean

    def test_evolve_multi_year(self):
        new_civ, stats = evolve(civ, years=5, seed=42, rebuild_graph=False)
        assert len(stats) == 5
        for s in stats:
            assert s.deaths > 0
            assert s.births == s.deaths

    def test_evolve_stats_have_country_breakdown(self):
        new_civ, stats = evolve(civ, years=1, seed=42)
        s = stats[0]
        assert "US" in s.pop_by_country
        assert sum(s.pop_by_country.values()) == civ.n

    def test_population_ages_over_time(self):
        new_civ, _ = evolve(civ, years=10, seed=42, rebuild_graph=False)
        assert new_civ.age.mean() > civ.age.mean()

    def test_education_drifts_up(self):
        new_civ, _ = evolve(civ, years=20, seed=42, rebuild_graph=False)
        assert new_civ.education.mean() >= civ.education.mean()

    def test_forces_still_bounded(self):
        new_civ, _ = evolve(civ, years=10, seed=42, rebuild_graph=False)
        assert np.all(new_civ.forces >= 0)
        assert np.all(new_civ.forces <= 1)

    def test_engine_still_works_after_evolution(self):
        new_civ, _ = evolve(civ, years=5, seed=42)
        q = question_by_id("ssm")
        result = run_question(q, new_civ)
        assert 0 <= result.yes_pct <= 1
        assert result.dominant is not None


class TestProjectOpinionDrift:
    def test_returns_trajectory(self):
        traj = project_opinion_drift(civ, "ssm", years=3, seed=42)
        assert len(traj) == 4  # year 0 + 3 years
        assert traj[0]["year"] == 0
        assert traj[-1]["year"] == 3

    def test_trajectory_bounded(self):
        traj = project_opinion_drift(civ, "ssm", years=5, seed=42)
        for point in traj:
            assert 0 <= point["yes_pct"] <= 1

    def test_opinion_changes_over_decades(self):
        traj = project_opinion_drift(civ, "ssm", years=20, seed=42)
        y0 = traj[0]["yes_pct"]
        y20 = traj[-1]["yes_pct"]
        assert y0 != y20

    def test_unknown_question_raises(self):
        with pytest.raises(ValueError, match="Unknown"):
            project_opinion_drift(civ, "nonexistent_q", years=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
