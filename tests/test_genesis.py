"""Tests for the flagship genesis pipeline — 194 countries, regional identity."""
import numpy as np
import pytest

from earth1.genesis import (
    genesis, _allocate_countries,
    GENESIS_COUNTRIES, GENESIS_COUNTRY_CODES,
    genesis_country_name, genesis_country_code,
)
from earth1.types import Force, NUM_FORCES
from earth1.census import CENSUS_TARGETS
from earth1.regions import get_regions


@pytest.fixture(scope="module")
def civ():
    return genesis(pop=50_000, seed=42, min_per_country=50)


class TestAllocation:
    def test_allocate_sums_to_total(self):
        counts = _allocate_countries(1_000_000, min_per_country=500)
        assert counts.sum() == 1_000_000

    def test_allocate_min_floor(self):
        counts = _allocate_countries(1_000_000, min_per_country=500)
        assert counts.min() >= 400  # close to 500 after rescaling

    def test_allocate_194_countries(self):
        counts = _allocate_countries(1_000_000)
        assert len(counts) == 194

    def test_proportionality(self):
        counts = _allocate_countries(1_000_000, min_per_country=100)
        shares = np.array([c["pop"] for c in GENESIS_COUNTRIES])
        india_idx = next(i for i, c in enumerate(GENESIS_COUNTRIES) if c["iso2"] == "IN")
        china_idx = next(i for i, c in enumerate(GENESIS_COUNTRIES) if c["iso2"] == "CN")
        assert counts[india_idx] > counts[china_idx] * 0.8


class TestCivilizationShape:
    def test_population_size(self, civ):
        assert 49_000 < civ.n < 51_000

    def test_forces_shape(self, civ):
        assert civ.forces.shape == (civ.n, NUM_FORCES)

    def test_alpha_shape(self, civ):
        assert civ.alpha.shape == (civ.n,)

    def test_means_shape(self, civ):
        assert civ.means.shape == (NUM_FORCES,)

    def test_adj_shape(self, civ):
        assert civ.adj.shape == (civ.n, civ.n)

    def test_all_trait_arrays_correct_length(self, civ):
        for attr in ["openness", "empathy", "risk_appetite", "doubt",
                     "desire_intensity", "economic_field", "culture_offset",
                     "conscientiousness", "agreeableness", "extraversion",
                     "neuroticism", "power_distance", "individualism",
                     "uncertainty_avoidance", "long_term_orientation"]:
            arr = getattr(civ, attr)
            assert arr.shape == (civ.n,), f"{attr} has wrong shape"


class TestCountryCoverage:
    def test_194_country_codes(self):
        assert len(GENESIS_COUNTRY_CODES) == 194

    def test_all_census_countries_present(self):
        census_codes = {c["iso2"] for c in CENSUS_TARGETS}
        genesis_codes = set(GENESIS_COUNTRY_CODES)
        assert census_codes == genesis_codes

    def test_every_country_has_agents(self, civ):
        unique = np.unique(civ.country)
        assert len(unique) == 194

    def test_country_names(self):
        assert genesis_country_name(0) == GENESIS_COUNTRIES[0]["name"]
        assert genesis_country_code(0) == GENESIS_COUNTRIES[0]["iso2"]


class TestTraitBounds:
    def test_forces_bounded(self, civ):
        assert civ.forces.min() >= 0
        assert civ.forces.max() <= 1

    def test_alpha_bounded(self, civ):
        assert civ.alpha.min() >= 0
        assert civ.alpha.max() <= 1

    def test_traits_bounded(self, civ):
        for attr in ["openness", "empathy", "risk_appetite", "doubt",
                     "desire_intensity", "economic_field",
                     "conscientiousness", "agreeableness", "extraversion",
                     "neuroticism", "power_distance", "individualism",
                     "uncertainty_avoidance", "long_term_orientation"]:
            arr = getattr(civ, attr)
            assert arr.min() >= 0, f"{attr} min={arr.min()}"
            assert arr.max() <= 1, f"{attr} max={arr.max()}"


class TestRegionalIdentity:
    def test_region_indices_valid(self, civ):
        for ci in range(len(GENESIS_COUNTRIES)):
            mask = civ.country == ci
            if not mask.any():
                continue
            iso2 = GENESIS_COUNTRIES[ci]["iso2"]
            n_regions = len(get_regions(iso2))
            max_ridx = civ.region[mask].max()
            assert max_ridx < n_regions, (
                f"{iso2}: max region idx {max_ridx} >= {n_regions}")

    def test_italy_has_multiple_regions(self, civ):
        it_idx = next(i for i, c in enumerate(GENESIS_COUNTRIES) if c["iso2"] == "IT")
        mask = civ.country == it_idx
        unique_regions = np.unique(civ.region[mask])
        assert len(unique_regions) >= 3

    def test_regional_culture_delta_varies(self, civ):
        it_idx = next(i for i, c in enumerate(GENESIS_COUNTRIES) if c["iso2"] == "IT")
        mask = civ.country == it_idx
        culture_vals = civ.culture_offset[mask]
        assert culture_vals.std() > 0.01


class TestDemographics:
    def test_age_range(self, civ):
        assert civ.age.min() >= 0
        assert civ.age.max() <= 1

    def test_education_values(self, civ):
        assert set(np.unique(civ.education)).issubset({0, 1, 2})

    def test_income_values(self, civ):
        assert set(np.unique(civ.income)).issubset({0, 1, 2})

    def test_urban_is_boolean(self, civ):
        assert civ.urban.dtype == bool


class TestForceFormulas:
    def test_fear_formula(self, civ):
        expected = np.clip(
            (civ.doubt + (1.0 - civ.risk_appetite) + civ.neuroticism * 0.3) / 2.3, 0, 1)
        actual = civ.forces[:, Force.FEAR]
        # Regional deltas may shift, so check correlation
        corr = np.corrcoef(expected, actual)[0, 1]
        assert corr > 0.95

    def test_economics_is_economic_field_based(self, civ):
        corr = np.corrcoef(civ.economic_field, civ.forces[:, Force.ECONOMICS])[0, 1]
        assert corr > 0.95

    def test_experience_is_age(self, civ):
        assert np.allclose(civ.forces[:, Force.EXPERIENCE], civ.age)


class TestDeterminism:
    def test_same_seed_same_result(self):
        c1 = genesis(pop=5000, seed=99, min_per_country=10)
        c2 = genesis(pop=5000, seed=99, min_per_country=10)
        assert np.array_equal(c1.forces, c2.forces)
        assert np.array_equal(c1.country, c2.country)

    def test_different_seed_different_result(self):
        c1 = genesis(pop=5000, seed=99, min_per_country=10)
        c2 = genesis(pop=5000, seed=100, min_per_country=10)
        assert not np.array_equal(c1.forces, c2.forces)


class TestSocialGraph:
    def test_adj_nonzero(self, civ):
        assert civ.adj.nnz > 0

    def test_mean_degree(self, civ):
        mean_deg = civ.adj.nnz / civ.n
        assert 8 < mean_deg < 14


class TestHofstedeDrivenDifferences:
    """Verify that countries with different Hofstede profiles produce different force distributions."""

    def test_us_vs_japan_individualism(self):
        c = genesis(pop=10000, seed=42, min_per_country=200)
        us_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "US")
        jp_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "JP")
        us_idv = c.individualism[c.country == us_idx].mean()
        jp_idv = c.individualism[c.country == jp_idx].mean()
        assert us_idv > jp_idv + 0.1

    def test_japan_vs_us_power_distance(self):
        c = genesis(pop=10000, seed=42, min_per_country=200)
        us_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "US")
        jp_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "JP")
        us_pdi = c.power_distance[c.country == us_idx].mean()
        jp_pdi = c.power_distance[c.country == jp_idx].mean()
        assert jp_pdi > us_pdi

    def test_nigeria_higher_collective_than_sweden(self):
        c = genesis(pop=10000, seed=42, min_per_country=200)
        ng_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "NG")
        se_idx = next(i for i, ct in enumerate(GENESIS_COUNTRIES) if ct["iso2"] == "SE")
        ng_coll = c.forces[c.country == ng_idx, Force.COLLECTIVE].mean()
        se_coll = c.forces[c.country == se_idx, Force.COLLECTIVE].mean()
        assert ng_coll > se_coll + 0.05


class TestCompatibility:
    """Verify genesis output works with existing engine functions."""

    def test_project_all(self):
        from earth1.forces import project_all
        from earth1.questions import QUESTIONS
        c = genesis(pop=5000, seed=42, min_per_country=10)
        q = QUESTIONS[0]
        stances = project_all(c, q)
        assert stances.shape == (c.n,)
        assert 0 <= stances.min()
        assert stances.max() <= 1

    def test_run_question(self):
        from earth1.engine import run_question
        c = genesis(pop=5000, seed=42, min_per_country=10)
        from earth1.questions import QUESTIONS
        result = run_question(QUESTIONS[0], c)
        assert 0 <= result.yes_pct <= 1
        assert result.dominant in list(Force)


class TestManifoldV2AgePyramid:
    """Manifold v2: adult ages from the stable-population model
    (census u18 + Gompertz survival), not normal(all-ages median, 12).
    Locks the fix for the G5 run #2/#3 finding: the world had no elderly."""

    def test_world_has_elderly(self, civ):
        age = 18 + civ.age * 72
        over65 = (age > 65).mean()
        assert 0.10 < over65 < 0.25, f"world over-65 share {over65:.3f}"
        assert np.percentile(age, 90) > 65

    def test_old_countries_older_than_young_ones(self, civ):
        from earth1.genesis import GENESIS_COUNTRY_CODES
        age = 18 + civ.age * 72
        de = age[civ.country == GENESIS_COUNTRY_CODES.index("DE")]
        ng = age[civ.country == GENESIS_COUNTRY_CODES.index("NG")]
        assert de.mean() > ng.mean() + 10
        assert (de > 65).mean() > 0.20
        assert (ng > 65).mean() < 0.10
