"""Tests for the §14 placebo harness + receiver activation."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.types import Question, NUM_FORCES
from earth1.receiver import (
    ForceActivation, GeoScope, ReceiverConfig, SourceConfig,
    aggregate_activations, compute_country_field_shift,
    compute_relevance, _init_default_adapters,
)
from earth1.placebo import (
    _synthetic_activations,
    _shuffle_geography,
    _per_country_shift_magnitude,
    _geographic_specificity,
    placebo_test_source,
    run_placebo_gate,
)


@pytest.fixture(autouse=True)
def init_adapters():
    _init_default_adapters()


def _make_q(qid="test_q", dominant_force=0):
    w = np.zeros(NUM_FORCES)
    w[dominant_force] = 0.8
    w[(dominant_force + 1) % NUM_FORCES] = -0.3
    return Question(
        id=qid, text="test question", domain="belief_causal",
        baseline=0.5, weights=w, lens="wvs",
    )


COUNTRIES = ["US", "CN", "IN", "BR", "NG", "DE", "JP", "MX"]


def test_synthetic_activations_vary_by_country():
    rng = np.random.default_rng(42)
    mags = np.array([0.2, 0.5, 0.8, 1.0, 0.3, 0.6, 0.9, 0.4])
    acts = _synthetic_activations("gdelt", COUNTRIES, mags, rng)
    assert len(acts) == len(COUNTRIES)
    norms = [np.linalg.norm(a.forces) for a in acts]
    assert max(norms) > 2 * min(norms)


def test_shuffle_geography_preserves_forces():
    rng = np.random.default_rng(0)
    mags = np.linspace(0.2, 1.0, len(COUNTRIES))
    acts = _synthetic_activations("gdelt", COUNTRIES, mags, rng)
    shuffled = _shuffle_geography(acts, rng)

    orig_norms = sorted(np.linalg.norm(a.forces) for a in acts)
    shuf_norms = sorted(np.linalg.norm(a.forces) for a in shuffled)
    np.testing.assert_allclose(orig_norms, shuf_norms, atol=1e-10)

    orig_codes = sorted(a.scope.country_code for a in acts)
    shuf_codes = sorted(a.scope.country_code for a in shuffled)
    assert orig_codes == shuf_codes


def test_shuffle_geography_changes_assignment():
    rng = np.random.default_rng(1)
    mags = np.linspace(0.2, 1.0, len(COUNTRIES))
    acts = _synthetic_activations("gdelt", COUNTRIES, mags, rng)
    any_different = False
    for _ in range(10):
        shuffled = _shuffle_geography(acts, rng)
        orig_pairs = [(a.scope.country_code, np.linalg.norm(a.forces)) for a in acts]
        shuf_pairs = [(a.scope.country_code, np.linalg.norm(a.forces)) for a in shuffled]
        if orig_pairs != shuf_pairs:
            any_different = True
            break
    assert any_different


def test_geographic_specificity_perfect_correlation():
    intended = np.array([0.2, 0.4, 0.6, 0.8, 1.0])
    observed = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    rho = _geographic_specificity(intended, observed)
    assert rho > 0.9


def test_geographic_specificity_zero_for_constant():
    intended = np.array([0.2, 0.4, 0.6, 0.8, 1.0])
    observed = np.full(5, 0.3)
    rho = _geographic_specificity(intended, observed)
    assert rho == 0.0


def test_per_country_shift_varies_with_activations():
    rng = np.random.default_rng(42)
    mags = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    acts = _synthetic_activations("gdelt", COUNTRIES, mags, rng)
    q = _make_q(dominant_force=2)
    shifts = _per_country_shift_magnitude(acts, q, COUNTRIES)
    assert shifts[0] > 0 or shifts.sum() > 0


def test_placebo_test_source_passes_for_geographic_source():
    """GDELT with country-specific signals should pass the placebo gate
    because correct geography routes signals to the right countries."""
    q = _make_q(dominant_force=2)
    result = placebo_test_source(
        "gdelt", [q],
        countries=COUNTRIES,
        n_perms=50, seed=42,
    )
    assert result.source_id == "gdelt"
    assert result.n_questions == 1
    assert result.n_countries == len(COUNTRIES)
    assert result.real_specificity > result.placebo_mean


def test_placebo_gate_runs_all_sources():
    q = _make_q(dominant_force=2)
    passport = run_placebo_gate(
        [q],
        source_ids=["gdelt", "acled"],
        countries=COUNTRIES,
        n_perms=30, seed=42,
    )
    assert "gdelt" in passport.results
    assert "acled" in passport.results
    assert passport.timestamp


def test_receiver_config_persists_in_living_world(tmp_path):
    from earth1.living import LivingWorld

    rc = ReceiverConfig(
        global_gain=0.1,
        min_confidence=0.15,
        sources=[
            SourceConfig("gdelt", enabled=True, gain=0.1, decay_half_life=3.0),
            SourceConfig("fred", enabled=False, gain=0.08, decay_half_life=60.0),
        ],
    )
    world = LivingWorld.create(tmp_path / "w", pop=1000, seed=42,
                               receiver_config=rc)
    assert world.state.receiver_config is not None
    assert len(world.state.receiver_config.sources) == 2

    loaded = LivingWorld.load(tmp_path / "w")
    assert loaded.state.receiver_config is not None
    assert loaded.state.receiver_config.global_gain == 0.1
    assert loaded.state.receiver_config.min_confidence == 0.15
    assert len(loaded.state.receiver_config.sources) == 2
    assert loaded.state.receiver_config.sources[0].source_id == "gdelt"
    assert loaded.state.receiver_config.sources[0].enabled is True
    assert loaded.state.receiver_config.sources[1].source_id == "fred"
    assert loaded.state.receiver_config.sources[1].enabled is False


def test_living_world_tick_with_receiver_flag(tmp_path):
    from earth1.living import LivingWorld

    world = LivingWorld.create(tmp_path / "w", pop=1000, seed=42)
    q = _make_q()
    stats = world.tick([q], days=1, enable_receiver=False, save=False)
    assert "deaths" in stats
