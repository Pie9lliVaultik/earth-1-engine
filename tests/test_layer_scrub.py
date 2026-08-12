"""Tests for layer-scrub analysis module."""
import sys
sys.path.insert(0, ".")

import numpy as np
from earth1.layer_scrub import layer_scrub, _bimodality_coefficient, _measure_sharpening
from earth1.engine import build_civilization
from earth1.questions import question_by_id
from earth1.population import COUNTRIES

POP = 10_000
civ = build_civilization(POP, seed=42)


def test_layer_scrub_basic():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    assert r["population"] == POP
    assert len(r["layers"]) == 9
    assert r["n_core"] + r["n_crust"] == POP


def test_layer_scrub_layers_have_all_fields():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    for layer in r["layers"]:
        assert "all" in layer
        assert "core" in layer
        assert "crust" in layer
        assert "core_crust_gap" in layer
        assert "yes_pct" in layer["all"]
        assert "std" in layer["all"]
        assert "histogram" in layer["all"]
        assert "histogram" in layer["core"]
        assert "histogram" in layer["crust"]


def test_layer_scrub_histograms_sum():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q, n_bins=20)
    for layer in r["layers"]:
        core_sum = sum(layer["core"]["histogram"])
        crust_sum = sum(layer["crust"]["histogram"])
        assert core_sum == r["n_core"]
        assert crust_sum == r["n_crust"]


def test_layer_scrub_country_filter():
    q = question_by_id("ssm")
    br_idx = [i for i, c in enumerate(COUNTRIES) if c["code"] == "BR"][0]
    r = layer_scrub(civ, q, country_idx=br_idx)
    assert r["population"] < POP
    assert r["population"] > 0


def test_sharpening_verdict_ssm():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    assert r["sharpening"]["verdict"] in ["flat_to_sharp_confirmed", "partial"]


def test_std_decreases_over_layers():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    stds = [layer["all"]["std"] for layer in r["layers"]]
    assert stds[-1] <= stds[0], "Std should decrease (sharpen) over layers"


def test_core_holds_position():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    core_0 = r["layers"][0]["core"]["yes_pct"]
    core_8 = r["layers"][-1]["core"]["yes_pct"]
    assert abs(core_0 - core_8) < 0.05, "Core should hold its position"


def test_crust_drifts_toward_core():
    q = question_by_id("ssm")
    r = layer_scrub(civ, q)
    core_8 = r["layers"][-1]["core"]["yes_pct"]
    crust_0 = r["layers"][0]["crust"]["yes_pct"]
    crust_8 = r["layers"][-1]["crust"]["yes_pct"]
    assert abs(crust_8 - core_8) < abs(crust_0 - core_8), "Crust should drift toward core"


def test_bimodality_coefficient():
    uniform = np.random.uniform(0, 1, 10000)
    bc_uniform = _bimodality_coefficient(uniform)
    bimodal = np.concatenate([np.random.normal(0.2, 0.05, 5000), np.random.normal(0.8, 0.05, 5000)])
    bc_bimodal = _bimodality_coefficient(bimodal)
    assert bc_bimodal > bc_uniform


def test_all_countries_flat_to_sharp():
    """G1 gate: every country should show flat -> sharp for SSM."""
    q = question_by_id("ssm")
    for i, c in enumerate(COUNTRIES):
        r = layer_scrub(civ, q, country_idx=i)
        if r["population"] < 100:
            continue
        stds = [layer["all"]["std"] for layer in r["layers"]]
        assert stds[-1] <= stds[0] + 0.01, f"{c['code']}: std should decrease"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
