"""Tests for regional identity profiles — sub-national regions with force deltas."""
import numpy as np
import pytest

from earth1.regions import (
    RegionalProfile, get_regions, get_region_by_code, all_regions,
    tier1_countries, tier2_countries, region_force_deltas, sample_region,
)
from earth1.census import CENSUS_TARGETS


class TestCoverage:
    def test_all_194_countries_have_regions(self):
        for c in CENSUS_TARGETS:
            regions = get_regions(c["iso2"])
            assert len(regions) >= 1, f"{c['iso2']} has no regions"

    def test_tier1_at_least_25_countries(self):
        assert len(tier1_countries()) >= 25

    def test_tier2_fills_gap(self):
        t1 = set(tier1_countries())
        t2 = set(tier2_countries())
        assert len(t1 & t2) == 0

    def test_total_regions_reasonable(self):
        total = len(all_regions())
        assert 400 < total < 1000


class TestRegionalProfile:
    def test_sicily_exists(self):
        p = get_region_by_code("IT-SIC")
        assert p is not None
        assert p.name == "Sicily"
        assert p.country == "IT"

    def test_sicily_historical_layers(self):
        p = get_region_by_code("IT-SIC")
        assert "Greek colonization" in p.historical_layers
        assert "Arab Emirate" in p.historical_layers
        assert "Norman Kingdom" in p.historical_layers
        assert len(p.historical_layers) >= 6

    def test_sicily_force_deltas(self):
        p = get_region_by_code("IT-SIC")
        assert p.force_deltas["collective"] > 0
        assert p.force_deltas["culture"] > 0
        assert p.force_deltas["identity"] > 0

    def test_tokyo_kanto(self):
        p = get_region_by_code("JP-KAN")
        assert p is not None
        assert p.force_deltas["economics"] > 0

    def test_texas(self):
        regions = get_regions("US")
        codes = [r.code for r in regions]
        assert "US-SW" in codes or "US-MR" in codes

    def test_mumbai_west_india(self):
        p = get_region_by_code("IN-WES")
        assert p is not None
        assert "finance" in p.economic_detail.lower() or "Bollywood" in p.economic_detail


class TestPopulationShares:
    def test_shares_sum_to_one(self):
        for c in CENSUS_TARGETS:
            regions = get_regions(c["iso2"])
            total = sum(r.population_share for r in regions)
            assert abs(total - 1.0) < 0.02, (
                f"{c['iso2']}: shares sum to {total}")

    def test_all_shares_positive(self):
        for r in all_regions():
            assert r.population_share > 0, f"{r.code} has share={r.population_share}"


class TestForceDeltas:
    def test_deltas_bounded(self):
        for r in all_regions():
            for force, delta in r.force_deltas.items():
                assert -0.15 <= delta <= 0.15, (
                    f"{r.code}: {force}={delta}")

    def test_valid_force_names(self):
        valid = {"fear", "desire", "economics", "collective",
                 "identity", "culture", "experience", "temperament"}
        for r in all_regions():
            for force in r.force_deltas:
                assert force in valid, f"{r.code}: unknown force {force}"

    def test_region_force_deltas_helper(self):
        deltas = region_force_deltas("IT-SIC")
        assert "culture" in deltas
        assert deltas["culture"] > 0

    def test_missing_region_returns_empty(self):
        assert region_force_deltas("XX-YY") == {}


class TestSampling:
    def test_sample_deterministic(self):
        rng = np.random.default_rng(42)
        r1 = sample_region("IT", rng)
        rng = np.random.default_rng(42)
        r2 = sample_region("IT", rng)
        assert r1.code == r2.code

    def test_sample_covers_all_regions(self):
        rng = np.random.default_rng(42)
        seen = set()
        for _ in range(10000):
            r = sample_region("IT", rng)
            seen.add(r.code)
        regions = get_regions("IT")
        for r in regions:
            assert r.code in seen, f"{r.code} never sampled"

    def test_sample_single_region_country(self):
        rng = np.random.default_rng(42)
        r = sample_region("VA", rng)
        assert r is not None

    def test_sample_unknown_country_raises(self):
        rng = np.random.default_rng(42)
        with pytest.raises(ValueError):
            sample_region("XX", rng)


class TestTier2Templates:
    def test_tier2_countries_have_3_regions(self):
        for iso2 in tier2_countries():
            regions = get_regions(iso2)
            assert len(regions) == 3, f"{iso2} has {len(regions)} regions"

    def test_tier2_codes_follow_pattern(self):
        for iso2 in tier2_countries():
            regions = get_regions(iso2)
            for r in regions:
                assert r.code.startswith(iso2), f"{r.code} doesn't start with {iso2}"

    def test_tier2_has_economic_type(self):
        for iso2 in tier2_countries():
            regions = get_regions(iso2)
            types = {r.economic_type for r in regions}
            assert len(types) >= 2


class TestDataIntegrity:
    def test_all_regions_have_history(self):
        for r in all_regions():
            assert len(r.historical_layers) >= 1

    def test_economic_types_valid(self):
        valid = {"agriculture", "industry", "services", "mixed", "extractive"}
        for r in all_regions():
            assert r.economic_type in valid, f"{r.code}: {r.economic_type}"

    def test_geographic_types_valid(self):
        valid = {"coastal", "mountain", "plains", "island", "desert", "tropical"}
        for r in all_regions():
            assert r.geographic_type in valid, f"{r.code}: {r.geographic_type}"

    def test_frozen_dataclass(self):
        r = get_region_by_code("IT-SIC")
        with pytest.raises(AttributeError):
            r.name = "changed"
