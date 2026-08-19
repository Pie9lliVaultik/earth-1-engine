"""The daemon's startup contract — every path, including the empty one.

Written because a real crash shipped through a green suite: adding the
`info` return value to `load_world` left the fresh-birth branch
returning a 2-tuple, so `w, rng_state, load_info = load_world()` would
raise ValueError on any world with no snapshot on disk. Nothing caught
it, because no test had ever started the daemon from an empty data
directory — the one situation a brand-new deployment is guaranteed to
be in.

An AST arity check found it. These tests make it a real, permanent
control.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1 import persistence
from earth1.alive import live_one_day


@pytest.fixture
def daemon(monkeypatch, tmp_path):
    """world_alive, pointed at a scratch state dir with a tiny population."""
    import scripts.world_alive as wa
    monkeypatch.setattr(wa, "HOME", tmp_path)
    monkeypatch.setattr(wa, "WORLD_PKL", tmp_path / "world.pkl")
    monkeypatch.setattr(wa, "LEGACY_ADJ", tmp_path / "adj.npz")
    monkeypatch.setattr(wa, "JOURNAL", tmp_path / "journal.jsonl")
    monkeypatch.setattr(wa, "POP", 2_000)
    return wa


def test_load_world_births_when_nothing_on_disk(daemon):
    """THE REGRESSION: a fresh deployment has no snapshot.

    This is the exact call shape main() uses. A 2-tuple here raises
    ValueError and the daemon never starts.
    """
    w, rng_state, info = daemon.load_world()          # must unpack to 3
    assert w.civ.n == 2_000
    assert w.day == 0
    assert rng_state is None
    assert info["born"] is True
    assert info["schema_version"] is None
    # a born world is whole: the gating subsystems must exist, or the
    # very first tick runs reduced physics
    for name in persistence.PHYSICS_GATING_FIELDS:
        assert getattr(w, name) is not None


def test_load_world_arity_is_uniform(daemon):
    """Every branch of load_world returns the same shape.

    Belt and braces alongside the two behavioural tests: an arity drift
    is exactly the failure that slipped through once already.
    """
    import ast
    import inspect
    src = inspect.getsource(daemon.load_world)
    tree = ast.parse(src.lstrip())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    arities = {len(r.value.elts) if isinstance(r.value, ast.Tuple) else 1
               for r in ast.walk(fn) if isinstance(r, ast.Return)}
    assert arities == {3}, f"load_world returns mixed arities: {arities}"


def test_born_world_saves_and_reloads_exactly(daemon):
    """Birth -> save -> reload is the first restart a deployment ever does."""
    w, _, _ = daemon.load_world()
    rng = np.random.default_rng(3)
    live_one_day(w, rng)
    daemon.save_world(w, rng)

    back, rng_state, info = daemon.load_world()
    assert info["schema_version"] == persistence.SCHEMA_VERSION
    assert rng_state is not None
    assert persistence.world_hash(back) == persistence.world_hash(w)


def test_state_json_records_the_provenance_fields(daemon):
    w, _, _ = daemon.load_world()
    meta = daemon.save_world(w, np.random.default_rng(1))
    st = json.loads((daemon.HOME / "state.json").read_text())
    for k in ("day", "pop", "seed", "alive", "schema_version", "sha256",
              "rng_persisted", "saved_at"):
        assert k in st, f"state.json missing {k}"
    assert st["schema_version"] == persistence.SCHEMA_VERSION
    assert st["rng_persisted"] is True
    assert st["sha256"] == meta["sha256"]


def test_continuity_break_is_journaled_once_and_is_explicit(daemon):
    """The epoch boundary must be findable, and self-describing."""
    w, _, _ = daemon.load_world()
    rec = daemon.journal_continuity_break(
        w, {"lost": ["presence", "mobility"]})

    assert rec["bit_continuous"] is False
    assert rec["epoch"] == 1
    assert rec["reason"] == "legacy_v0_missing_presence_mobility"
    assert "causal benchmark" in rec["note"]

    lines = [json.loads(x) for x in
             daemon.JOURNAL.read_text().splitlines() if x.strip()]
    breaks = [r for r in lines if r.get("event") == "continuity_break"]
    assert len(breaks) == 1
    assert breaks[0]["fields_not_carried"] == ["presence", "mobility"]


def test_v0_snapshot_is_refused_without_the_override(daemon, monkeypatch):
    """Fail closed by default, even inside the daemon's own loader."""
    from tests.test_persistence_roundtrip import _write_v0_daemon_snapshot
    w, _, _ = daemon.load_world()
    _write_v0_daemon_snapshot(w, daemon.WORLD_PKL)
    monkeypatch.delenv("EARTH1_MIGRATE_V0", raising=False)
    with pytest.raises(persistence.SnapshotError, match="pre-schema"):
        daemon.load_world()


def test_v0_snapshot_migrates_only_with_the_override(daemon, monkeypatch):
    from tests.test_persistence_roundtrip import _write_v0_daemon_snapshot
    w, _, _ = daemon.load_world()
    _write_v0_daemon_snapshot(w, daemon.WORLD_PKL)
    monkeypatch.setenv("EARTH1_MIGRATE_V0", "1")
    back, rng_state, info = daemon.load_world()
    assert info["schema_version"] == 0
    assert rng_state is None
    assert set(persistence.PHYSICS_GATING_FIELDS) <= set(info["lost"])
    assert back.day == w.day
