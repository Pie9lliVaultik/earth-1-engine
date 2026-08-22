"""Phase 0.5e/f — every product route answers from THE living world.

Semantic proofs: same canonical identity on every response, read-only
routes mutate nothing, branch paths clone the complete civilization,
identity survives snapshot reload, unavailability fails loudly with no
legacy fallback. Sabotage controls prove each check can fail.
"""
import copy
import json

import numpy as np
import pytest

from earth1 import persistence
from earth1.api import deps
from earth1.legacy_gate import (PRODUCTION, QUARANTINED,
                                assert_one_production_earth, scan)


@pytest.fixture
def api_world(tiny_world, tmp_path, monkeypatch):
    """A canonical snapshot on disk + deps pointed at it."""
    rng = np.random.default_rng(9)
    meta = persistence.save_world(tiny_world, tmp_path / "world.pkl",
                                  rng=rng)
    (tmp_path / "state.json").write_text(json.dumps(
        {"day": tiny_world.day, "pop": int(tiny_world.civ.n),
         "alive": int(tiny_world.health.alive.sum()),
         "schema_version": meta["schema_version"],
         "sha256": meta["sha256"], "rng_persisted": True,
         "saved_at": meta["saved_at"]}))
    monkeypatch.setattr(deps, "ALIVE_HOME", tmp_path)
    deps.reset_cache()
    yield tiny_world, tmp_path
    deps.reset_cache()


# ── identity ────────────────────────────────────────────────────────

def test_every_route_shares_one_world_identity(api_world):
    w0, home = api_world
    w1, id1 = deps.get_world()
    w2, id2 = deps.get_world()
    assert w1 is w2, "two calls resolved two worlds"
    assert id1["snapshot_sha256"] == id2["snapshot_sha256"]
    assert id1["world_day"] == w0.day
    assert id1["alive"] == int(w0.health.alive.sum())


def test_identity_survives_snapshot_reload(api_world):
    """A new save on disk is picked up as the SAME civilization,
    advanced — not a different Earth."""
    w0, home = api_world
    w, id1 = deps.get_world()
    from earth1.alive import live_one_day
    wc = copy.deepcopy(w)
    live_one_day(wc, np.random.default_rng(4))
    meta = persistence.save_world(wc, home / "world.pkl",
                                  rng=np.random.default_rng(4))
    (home / "state.json").write_text(json.dumps(
        {"day": wc.day, "pop": int(wc.civ.n),
         "alive": int(wc.health.alive.sum()),
         "schema_version": meta["schema_version"],
         "sha256": meta["sha256"], "rng_persisted": True,
         "saved_at": meta["saved_at"]}))
    _, id2 = deps.get_world()
    assert id2["snapshot_sha256"] == meta["sha256"]
    assert id2["world_day"] == id1["world_day"] + 1


# ── read-only routes mutate nothing ─────────────────────────────────

def test_readouts_do_not_mutate_world_or_rng(api_world):
    from earth1.api.routes import observatory, world as world_routes
    w, _ = deps.get_world()
    before = persistence.world_hash(w)
    rng_before = np.random.get_state()[1].copy()
    world_routes.world_summary()
    world_routes.countries()
    i = int(np.flatnonzero(w.health.alive)[3])
    world_routes.earthling(i)
    observatory.standing_readings()
    assert persistence.world_hash(w) == before, "a readout MUTATED Earth"
    assert np.array_equal(np.random.get_state()[1], rng_before)


def test_mutating_readout_is_detected(api_world, monkeypatch):
    """Sabotage 6: a readout that nudges state must trip the hash."""
    from earth1.api.routes import world as world_routes
    w, _ = deps.get_world()
    before = persistence.world_hash(w)
    real = world_routes.world_summary

    def bad():
        w.flourishing.hope[0] += 1e-9
        return real()

    bad()
    assert persistence.world_hash(w) != before, "control cannot fail"


# ── branch paths clone the COMPLETE civilization ────────────────────

def test_clone_world_is_complete_and_isolated(api_world):
    w, _ = deps.get_world()
    wc, _ = deps.clone_world()
    assert wc is not w
    assert persistence.world_hash(wc) == persistence.world_hash(w)
    for f in persistence.PERSISTENT_FIELDS:
        assert getattr(wc, f, None) is not None, f"clone lost {f}"
    wc.flourishing.hope[0] = 0.123456
    assert w.flourishing.hope[0] != 0.123456, "clone shares memory"


def test_partial_clone_is_detected(api_world, monkeypatch):
    """Sabotage 2: a branch path that clones a reduced world must fail
    the completeness check."""
    w, ident = deps.get_world()

    def partial_clone():
        wc = copy.copy(w)              # shallow — a reduced pretence
        wc.presence = None
        return wc, ident

    wc, _ = partial_clone()
    missing = [f for f in persistence.PERSISTENT_FIELDS
               if getattr(wc, f, None) is None]
    assert missing == ["presence"], "control cannot fail"


# ── fail loudly, never legacy ───────────────────────────────────────

def test_unavailable_world_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.setattr(deps, "ALIVE_HOME", tmp_path / "empty")
    deps.reset_cache()
    with pytest.raises(deps.CanonicalWorldUnavailable,
                       match="no legacy fallback|refuses to fabricate"):
        deps.get_world()


def test_legacy_resolvers_are_dead(api_world):
    """Sabotage 4: the old resolvers can never silently substitute."""
    with pytest.raises(deps.CanonicalWorldUnavailable, match="retired"):
        deps.get_world_state()
    with pytest.raises(deps.CanonicalWorldUnavailable, match="retired"):
        deps.get_living_world()


# ── the one-production-earth source gate ────────────────────────────

def test_no_production_path_reaches_retired_family():
    assert scan() == []
    assert_one_production_earth()


def test_reintroduced_legacy_import_is_refused(tmp_path, monkeypatch):
    """Sabotage 1/5/7: a production file importing the retired family
    (an API handler back on LivingWorld, a new engine import, a
    top-level re-export) must be caught by the scanner."""
    import earth1.legacy_gate as lg
    bad = tmp_path / "handler.py"
    bad.write_text("from earth1.living import LivingWorld\n")
    # pathlib: ROOT / "/absolute" resolves to the absolute path, so an
    # absolute entry stands in for a production file cleanly
    monkeypatch.setattr(lg, "PRODUCTION", [str(bad.resolve())])
    v = lg.scan()
    assert v and "earth1.living" in v[0], "the scanner cannot fail"
    with pytest.raises(RuntimeError, match="ONE-PRODUCTION-EARTH"):
        lg.assert_one_production_earth()


def test_quarantine_list_covers_the_engine_family():
    required = {"earth1.engine", "earth1.tick", "earth1.living",
                "earth1.advance", "earth1.diffusion", "earth1.forces",
                "earth1.legacy_benchmark", "earth1.legacy_predictions",
                "earth1.legacy_answer", "earth1.lab_archive",
                "earth1.dynamics", "earth1.coupling",
                "earth1.graph_dynamics", "earth1.event_generation",
                "earth1.perishability"}
    assert required <= QUARANTINED
