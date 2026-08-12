"""Tests for cultural data layer — Hofstede + Inglehart-Welzel."""
import pytest
from earth1.culture import (
    HOFSTEDE, INGLEHART, get_culture, get_hofstede, get_inglehart,
    list_countries_with_culture, list_hofstede_countries, list_inglehart_countries,
    _HOFSTEDE_KEYS, _INGLEHART_KEYS,
)


class TestHofstedeData:
    def test_at_least_76_countries(self):
        assert len(HOFSTEDE) >= 76

    def test_all_six_dimensions_present(self):
        for code, dims in HOFSTEDE.items():
            for key in _HOFSTEDE_KEYS:
                assert key in dims, f"{code} missing {key}"

    def test_values_in_range(self):
        for code, dims in HOFSTEDE.items():
            for key, val in dims.items():
                assert -0.01 <= val <= 1.01, f"{code}.{key} = {val} out of range"

    def test_known_values_us(self):
        us = HOFSTEDE["US"]
        assert abs(us["pdi"] - 0.40) < 0.05
        assert abs(us["idv"] - 0.91) < 0.05
        assert abs(us["mas"] - 0.62) < 0.05

    def test_known_values_jp(self):
        jp = HOFSTEDE["JP"]
        assert abs(jp["mas"] - 0.95) < 0.05
        assert abs(jp["uai"] - 0.92) < 0.05
        assert abs(jp["lto"] - 0.88) < 0.05

    def test_no_extra_keys(self):
        for code, dims in HOFSTEDE.items():
            extra = set(dims.keys()) - set(_HOFSTEDE_KEYS)
            assert not extra, f"{code} has extra keys: {extra}"


class TestInglehartData:
    def test_at_least_76_countries(self):
        assert len(INGLEHART) >= 76

    def test_both_dimensions_present(self):
        for code, dims in INGLEHART.items():
            for key in _INGLEHART_KEYS:
                assert key in dims, f"{code} missing {key}"

    def test_values_in_range(self):
        for code, dims in INGLEHART.items():
            for key, val in dims.items():
                assert 0.0 <= val <= 1.0, f"{code}.{key} = {val} out of range"

    def test_sweden_high_on_both(self):
        se = INGLEHART["SE"]
        assert se["trad_sec"] > 0.7
        assert se["surv_self"] > 0.8

    def test_nigeria_low_on_both(self):
        ng = INGLEHART["NG"]
        assert ng["trad_sec"] < 0.2
        assert ng["surv_self"] < 0.3


class TestGetCulture:
    def test_returns_merged_dict(self):
        c = get_culture("US")
        assert c is not None
        assert "pdi" in c
        assert "trad_sec" in c
        assert len(c) == 8

    def test_unknown_country_returns_none(self):
        assert get_culture("XX") is None

    def test_get_hofstede(self):
        h = get_hofstede("JP")
        assert h is not None
        assert len(h) == 6

    def test_get_inglehart(self):
        i = get_inglehart("BR")
        assert i is not None
        assert len(i) == 2


class TestListCountries:
    def test_list_with_culture(self):
        countries = list_countries_with_culture()
        assert len(countries) >= 76
        assert "US" in countries
        assert "JP" in countries
        assert countries == sorted(countries)

    def test_hofstede_and_inglehart_same_set(self):
        h = set(list_hofstede_countries())
        i = set(list_inglehart_countries())
        assert h == i

    def test_all_original_countries_present(self):
        for code in ["US", "GB", "DE", "BR", "NG", "IN", "JP", "MX", "FR"]:
            assert code in HOFSTEDE
            assert code in INGLEHART
