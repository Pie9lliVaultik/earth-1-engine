"""Phase 0.4 structural proofs — opinion reads the person who lived it.

The causal contract: civilization state -> individual lived state ->
opinion. Never: country stereotype -> opinion. Six required proofs and
the sabotage controls that show each check can fail.
"""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from earth1 import calibration, persistence
from earth1.calibration import (LIVING_FEATURES, MissingLivingState,
                                living_feature_names, living_features,
                                write_feature_provenance)

ROOT = Path(__file__).resolve().parents[1]
N_LIVING = len(LIVING_FEATURES)


# ── proof 1: within-unit variation exists ───────────────────────────

def test_identical_demographics_different_lives_differ(tiny_world):
    """Two Earthlings with identical country/demographic/static inputs
    but different lived states must produce different feature rows."""
    w = tiny_world
    c = w.civ
    a, b = 10, 11
    # make the STATIC inputs identical
    for f in ("country", "region", "urban", "education", "income",
              "age", "age_bucket", "openness", "empathy", "risk_appetite",
              "doubt", "desire_intensity", "conscientiousness",
              "agreeableness", "extraversion", "neuroticism",
              "power_distance", "individualism", "uncertainty_avoidance",
              "long_term_orientation"):
        getattr(c, f)[b] = getattr(c, f)[a]
    c.forces[b] = c.forces[a]
    c.alpha[b] = c.alpha[a]
    # ...and the LIVES maximally different
    w.life.deprivation[a], w.life.deprivation[b] = 0.05, 0.95
    w.life.employed[a], w.life.employed[b] = True, False
    w.life.in_lf[[a, b]] = True
    w.flourishing.hunger[a], w.flourishing.hunger[b] = 0.02, 0.9
    w.life.mental[a], w.life.mental[b] = 0.9, 0.1
    w.flourishing.hope[a], w.flourishing.hope[b] = 0.9, 0.1

    X = living_features(w)
    assert not np.allclose(X[a], X[b]), \
        "identical demographics produced identical features — the " \
        "readout is still a stereotype"
    # and the difference lives in the living block, not the static one
    n_static = X.shape[1] - N_LIVING
    np.testing.assert_allclose(X[a][:n_static], X[b][:n_static])


def test_country_mean_replacement_is_detected(tiny_world, monkeypatch):
    """Sabotage: replace within-unit features with country means — the
    within-unit variation proof must fail."""
    real = calibration._living_matrix

    def country_meaned(w):
        m = real(w)
        for c in np.unique(w.civ.country):
            mask = w.civ.country == c
            m[mask] = m[mask].mean(axis=0)
        return m

    monkeypatch.setattr(calibration, "_living_matrix", country_meaned)
    w = tiny_world
    a, b = 10, 11
    w.civ.country[b] = w.civ.country[a]
    w.life.deprivation[a], w.life.deprivation[b] = 0.05, 0.95
    X = living_features(w)
    n_static = X.shape[1] - N_LIVING
    assert np.allclose(X[a][n_static:], X[b][n_static:]), \
        "control cannot fail: country-meaning did not equalize rows"


# ── proof 2: counterfactual sensitivity is causal and local ─────────

def test_counterfactual_changes_only_its_channel(tiny_world):
    w = tiny_world
    X0 = living_features(w)
    w.flourishing.hunger[42] += 0.3
    X1 = living_features(w)
    names = living_feature_names()
    changed = {names[j] for j in np.flatnonzero(
        ~np.isclose(X0[42], X1[42], atol=1e-12))}
    assert changed == {"hunger"}, f"non-local sensitivity: {changed}"
    # other agents' rows move only through the centering constant —
    # their RAW state is untouched; verify one other row changed only
    # in the hunger column too
    other_changed = {names[j] for j in np.flatnonzero(
        ~np.isclose(X0[7], X1[7], atol=1e-12))}
    assert other_changed <= {"hunger"}


def test_miswired_channel_is_detected(tiny_world, monkeypatch):
    """Sabotage: wire hunger from thirst — locality proof must fail."""
    spec = dict(LIVING_FEATURES)
    spec["hunger"] = ("flourishing", "thirst", "flourishing_tick")
    monkeypatch.setattr(calibration, "LIVING_FEATURES", spec)
    w = tiny_world
    X0 = living_features(w)
    w.flourishing.hunger[42] += 0.3
    X1 = living_features(w)
    assert np.allclose(X0[42], X1[42]), \
        "control cannot fail: miswiring was invisible"


# ── proof 3: readout is non-mutating ────────────────────────────────

def test_readout_mutates_nothing(tiny_world):
    w = tiny_world
    before = persistence.world_hash(w)
    rng_before = np.random.get_state()[1].copy()
    living_features(w)
    living_features(w, extended=False)
    write_feature_provenance()
    assert persistence.world_hash(w) == before, "the readout TOUCHED " \
        "the world — observation must not change the observed"
    assert np.array_equal(np.random.get_state()[1], rng_before)


def test_mutating_readout_is_detected(tiny_world, monkeypatch):
    """Sabotage: a feature builder that nudges hope must trip the hash."""
    real = calibration._living_matrix

    def mutating(w):
        w.flourishing.hope[0] += 1e-9
        return real(w)

    monkeypatch.setattr(calibration, "_living_matrix", mutating)
    w = tiny_world
    before = persistence.world_hash(w)
    living_features(w)
    assert persistence.world_hash(w) != before, "control cannot fail"


# ── proof 4: no silent fallback ─────────────────────────────────────

def test_missing_subsystem_fails_loudly(tiny_world):
    w = copy.deepcopy(tiny_world)
    w.flourishing = None
    with pytest.raises(MissingLivingState, match="refusing to fake"):
        living_features(w)


def test_silent_zero_is_impossible_by_construction(tiny_world):
    """Sabotage the field itself: a None array raises, never zeros."""
    w = copy.deepcopy(tiny_world)
    w.life.mental = None
    with pytest.raises(MissingLivingState):
        living_features(w)


# ── proof 5: no duplicate physics ───────────────────────────────────

def test_no_recomputation_of_state():
    """The builder reads canonical fields; it must not re-derive
    unemployment/deprivation/isolation with its own formulas. Allowed
    computation: the declared boolean combine and normalizations."""
    import inspect
    src = inspect.getsource(calibration._living_matrix)
    for forbidden in ("bincount", "adj", "wage", "rent", "firm_health",
                      "policing", "welfare"):
        assert forbidden not in src, \
            f"_living_matrix recomputes physics ({forbidden!r})"


# ── proof 6: determinism ────────────────────────────────────────────

def test_same_world_same_features(tiny_world, tmp_path):
    persistence.save_world(tiny_world, tmp_path / "w.pkl")
    a, _, _ = persistence.load_world(tmp_path / "w.pkl")
    b, _, _ = persistence.load_world(tmp_path / "w.pkl")
    np.testing.assert_array_equal(living_features(a), living_features(b))


# ── the leakage gate ────────────────────────────────────────────────

def test_provenance_table_is_complete_and_clean(tiny_world):
    """Machine-readable provenance for EVERY feature, no target-derived
    entries, regenerated (never hand-maintained) each run."""
    table = write_feature_provenance()
    names = set(living_feature_names())
    assert set(table["features"]) == names, \
        f"provenance out of sync: {names ^ set(table['features'])}"
    for f, row in table["features"].items():
        assert row["leakage_status"] == "clean", f"{f}: {row}"
        assert "world-time t" in row["availability"], \
            f"{f} not available at prediction time"
        for banned in ("survey", "target", "wave", "holdout",
                       "benchmark-derived"):
            assert banned not in row["canonical_writer"].lower(), \
                f"{f} written by {row['canonical_writer']}"


def test_target_derived_feature_is_refused(monkeypatch, tiny_world):
    """Sabotage: introduce a feature whose writer is the survey target —
    the provenance audit must fail."""
    spec = dict(LIVING_FEATURES)
    spec["goqa_answer"] = ("life", "deprivation", "survey target Q164")
    monkeypatch.setattr(calibration, "LIVING_FEATURES", spec)
    table = write_feature_provenance(path="/tmp/prov_sab.json")
    bad = [f for f, r in table["features"].items()
           if "target" in r["canonical_writer"].lower()]
    assert bad == ["goqa_answer"], "control cannot fail"


def test_adjacency_gate_still_governs_injected_traits():
    """The existing convicted-feature gate stays in force: a banned
    injected trait cannot enter the matrix whatever EARTH1_INJECT says."""
    banned = calibration._banned_features()
    active = set(calibration._active_traits())
    assert not (banned & active), f"banned features active: {banned & active}"


# ── legacy-path restoration control ─────────────────────────────────

def test_living_block_is_present_and_sized():
    """Sabotage-detector for 'accidentally restored the country-only
    path': the living readout must carry exactly the declared channels
    after the static block."""
    names = living_feature_names()
    assert names[-N_LIVING:] == list(LIVING_FEATURES), \
        "the living block is missing or reordered — the legacy " \
        "country-only path is back"
    assert {"deprivation", "unemployed", "hunger", "mental", "addiction",
            "relationship", "hope"} <= set(names)
