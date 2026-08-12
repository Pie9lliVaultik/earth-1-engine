"""Tests for census data layer — 194 countries, Hofstede norms, within-country distributions."""
import pytest

from earth1.census import (
    CENSUS_TARGETS, FORCE_NORMS, WITHIN_COUNTRY, WORLD_REGIONS,
    get_census, get_force_norms, get_within_country, get_region,
    list_countries, countries_in_region, regional_force_norms,
    effective_force_norms,
)


class TestCensusTargets:
    def test_194_countries(self):
        assert len(CENSUS_TARGETS) == 194

    def test_all_have_required_fields(self):
        required = {"iso2", "name", "region", "pop", "med_age", "urban",
                     "male", "u18", "tfr", "le", "income"}
        for c in CENSUS_TARGETS:
            missing = required - set(c.keys())
            assert not missing, f"{c['iso2']} missing {missing}"

    def test_population_shares_sum_near_one(self):
        total = sum(c["pop"] for c in CENSUS_TARGETS)
        assert 0.99 < total < 1.01

    def test_iso2_codes_unique(self):
        codes = [c["iso2"] for c in CENSUS_TARGETS]
        assert len(codes) == len(set(codes))

    def test_sorted_by_population_descending(self):
        pops = [c["pop"] for c in CENSUS_TARGETS]
        assert pops == sorted(pops, reverse=True)

    def test_top_countries_present(self):
        codes = {c["iso2"] for c in CENSUS_TARGETS}
        for big in ["IN", "CN", "US", "ID", "PK", "NG", "BR", "BD", "RU", "MX"]:
            assert big in codes

    def test_median_age_plausible(self):
        for c in CENSUS_TARGETS:
            assert 14 < c["med_age"] < 60, f"{c['iso2']} med_age={c['med_age']}"

    def test_urban_percent_range(self):
        for c in CENSUS_TARGETS:
            assert 0 < c["urban"] <= 100, f"{c['iso2']} urban={c['urban']}"

    def test_income_classes_valid(self):
        valid = {"HIC", "UMIC", "LMIC", "LIC"}
        for c in CENSUS_TARGETS:
            assert c["income"] in valid, f"{c['iso2']} income={c['income']}"

    def test_life_expectancy_plausible(self):
        for c in CENSUS_TARGETS:
            assert 45 < c["le"] < 90, f"{c['iso2']} le={c['le']}"


class TestForceNorms:
    def test_at_least_100_countries(self):
        assert len(FORCE_NORMS) >= 100

    def test_hofstede_six_dimensions(self):
        for iso2, norms in FORCE_NORMS.items():
            for dim in ["pdi", "idv", "mas", "uai", "lto", "ind"]:
                assert dim in norms, f"{iso2} missing {dim}"

    def test_values_in_range(self):
        for iso2, norms in FORCE_NORMS.items():
            for dim, val in norms.items():
                assert 0 <= val <= 120, f"{iso2}.{dim}={val}"

    def test_known_values(self):
        us = FORCE_NORMS["US"]
        assert us["idv"] == 91
        assert us["pdi"] == 40
        jp = FORCE_NORMS["JP"]
        assert jp["mas"] == 95
        assert jp["uai"] == 92


class TestWithinCountry:
    def test_coverage_at_least_100(self):
        assert len(WITHIN_COUNTRY) >= 100

    def test_proportions_sum_near_one(self):
        for iso2, dims in WITHIN_COUNTRY.items():
            for dim, cats in dims.items():
                total = sum(p for _, p in cats)
                assert 0.9 < total < 1.1, (
                    f"{iso2}.{dim} sums to {total}")

    def test_india_religion(self):
        wc = WITHIN_COUNTRY.get("IN", {})
        assert "religion" in wc
        cats = {c: p for c, p in wc["religion"]}
        assert "Hindu" in cats
        assert cats["Hindu"] > 0.7

    def test_us_religion(self):
        wc = WITHIN_COUNTRY.get("US", {})
        assert "religion" in wc
        cats = {c: p for c, p in wc["religion"]}
        assert "Christian" in cats
        assert cats["Christian"] > 0.5

    def test_dimensions_are_valid(self):
        valid = {"income_decile", "worldview", "age_bucket", "religion",
                 "occupation", "education", "urban_rural"}
        for iso2, dims in WITHIN_COUNTRY.items():
            for dim in dims:
                assert dim in valid, f"{iso2} has unknown dim {dim}"


class TestWorldRegions:
    def test_eleven_regions(self):
        assert len(WORLD_REGIONS) == 11

    def test_all_countries_have_valid_region(self):
        for c in CENSUS_TARGETS:
            assert c["region"] in WORLD_REGIONS, f"{c['iso2']}: {c['region']}"


class TestLookupFunctions:
    def test_get_census_found(self):
        c = get_census("IT")
        assert c is not None
        assert c["name"] == "Italy"
        assert c["region"] == "Western Europe"

    def test_get_census_not_found(self):
        assert get_census("XX") is None

    def test_get_force_norms_found(self):
        n = get_force_norms("DE")
        assert n is not None
        assert "pdi" in n

    def test_get_force_norms_not_found(self):
        assert get_force_norms("XX") is None

    def test_get_within_country(self):
        wc = get_within_country("US")
        assert wc is not None
        assert "religion" in wc

    def test_get_region(self):
        assert get_region("JP") == "East Asia"
        assert get_region("BR") == "Latin America"
        assert get_region("XX") is None

    def test_list_countries(self):
        codes = list_countries()
        assert len(codes) == 194
        assert "US" in codes

    def test_countries_in_region(self):
        ea = countries_in_region("East Asia")
        assert "CN" in ea
        assert "JP" in ea
        assert len(ea) == 6


class TestRegionalFallback:
    def test_regional_force_norms_known_region(self):
        norms = regional_force_norms("East Asia")
        assert "pdi" in norms
        assert 0 < norms["pdi"] < 100

    def test_regional_force_norms_empty_region(self):
        norms = regional_force_norms("Nonexistent")
        assert norms == {"pdi": 50, "idv": 50, "mas": 50,
                         "uai": 50, "lto": 50, "ind": 50}

    def test_effective_force_norms_published(self):
        norms = effective_force_norms("US")
        assert norms["idv"] == 91.0

    def test_effective_force_norms_fallback(self):
        norms = effective_force_norms("TL")
        assert "pdi" in norms
        for v in norms.values():
            assert isinstance(v, float)

    def test_effective_force_norms_unknown(self):
        norms = effective_force_norms("XX")
        assert norms["pdi"] == 50.0


class TestCensusAlignmentWithExistingCulture:
    """Verify census force norms align with our existing culture.py Hofstede data."""

    def test_us_alignment(self):
        from earth1.culture import get_hofstede
        existing = get_hofstede("US")
        census_norms = effective_force_norms("US")
        if existing:
            assert abs(existing["pdi"] - census_norms["pdi"] / 100) < 0.03
            assert abs(existing["idv"] - census_norms["idv"] / 100) < 0.03

    def test_japan_alignment(self):
        from earth1.culture import get_hofstede
        existing = get_hofstede("JP")
        census_norms = effective_force_norms("JP")
        if existing:
            assert abs(existing["mas"] - census_norms["mas"] / 100) < 0.03
