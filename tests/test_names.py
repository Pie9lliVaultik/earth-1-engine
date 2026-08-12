"""Tests for name pools — country-specific and regional fallback names."""
import numpy as np
import pytest

from earth1.names import get_name_pool, sample_name, _NAMES, _REGION_NAMES
from earth1.census import CENSUS_TARGETS


class TestNamePools:
    def test_direct_pool_for_major_countries(self):
        for iso2 in ["US", "CN", "IN", "JP", "BR", "DE", "FR", "GB", "IT", "ES"]:
            pool = get_name_pool(iso2, "")
            assert "m" in pool
            assert "f" in pool
            assert "last" in pool
            assert len(pool["m"]) >= 10
            assert len(pool["f"]) >= 10
            assert len(pool["last"]) >= 10

    def test_regional_fallback(self):
        pool = get_name_pool("FI", "Western Europe")
        assert pool == _REGION_NAMES["Western Europe"]

    def test_unknown_region_falls_back(self):
        pool = get_name_pool("XX", "Unknown Region")
        assert pool == _REGION_NAMES["Western Europe"]

    def test_all_pools_have_required_keys(self):
        for iso2, pool in _NAMES.items():
            assert "m" in pool, f"{iso2} missing male names"
            assert "f" in pool, f"{iso2} missing female names"
            assert "last" in pool, f"{iso2} missing last names"

    def test_all_region_pools_have_required_keys(self):
        for region, pool in _REGION_NAMES.items():
            assert "m" in pool, f"{region} missing male names"
            assert "f" in pool, f"{region} missing female names"
            assert "last" in pool, f"{region} missing last names"


class TestSampling:
    def test_sample_male_name(self):
        rng = np.random.default_rng(42)
        first, last = sample_name("US", "North America", True, rng)
        assert isinstance(first, str)
        assert isinstance(last, str)
        assert len(first) > 0
        assert len(last) > 0

    def test_sample_female_name(self):
        rng = np.random.default_rng(42)
        first, last = sample_name("JP", "East Asia", False, rng)
        assert isinstance(first, str)
        assert isinstance(last, str)

    def test_deterministic(self):
        rng1 = np.random.default_rng(99)
        n1 = sample_name("IT", "Western Europe", True, rng1)
        rng2 = np.random.default_rng(99)
        n2 = sample_name("IT", "Western Europe", True, rng2)
        assert n1 == n2

    def test_variety(self):
        rng = np.random.default_rng(42)
        names = {sample_name("IN", "South Asia", True, rng) for _ in range(100)}
        assert len(names) > 10

    def test_fallback_sampling(self):
        rng = np.random.default_rng(42)
        first, last = sample_name("FI", "Western Europe", False, rng)
        assert isinstance(first, str)
        assert len(first) > 0


class TestCoverage:
    def test_top_countries_have_pools(self):
        top_20 = [c["iso2"] for c in CENSUS_TARGETS[:20]]
        missing = [iso2 for iso2 in top_20 if iso2 not in _NAMES]
        assert len(missing) <= 5, f"Missing pools for top-20 countries: {missing}"

    def test_all_world_regions_covered(self):
        regions = {c["region"] for c in CENSUS_TARGETS}
        for r in regions:
            pool = get_name_pool("XX", r)
            assert "m" in pool
