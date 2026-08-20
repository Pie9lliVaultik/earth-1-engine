"""Shared dependencies — THE canonical living world, and nothing else.

Phase 0.5e. Until now this module resolved the retired engine family:
its "living" branch loaded `living.LivingWorld` (the OLD substrate) and
its default built a fresh in-memory `tick.WorldState` — so the product
served a civilization that was not the one the daemon evolves, and 31
handlers answered from a second Earth.

There is one Earth: the daemon's persisted `alive.World`. The API
resolves it from the canonical v1 snapshot, verifies it through the
canonical loader (checksum, schema, wholeness), and carries its
IDENTITY (world day, snapshot sha, schema) on every response so a reader
can always tell WHICH civilization answered.

Fail-loud rule: if the canonical world is unavailable or invalid the
API errors with 503. There is no fallback engine to fall back to — a
silently substituted legacy world is a different universe wearing the
same URL.

Read paths share one in-memory instance and MUST NOT mutate it (proven
by tests/test_api_one_earth.py via whole-world hash). Branch/forecast
paths receive a deep clone of the COMPLETE civilization — never a
reduced representation.
"""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
ALIVE_HOME = Path(os.environ.get("EARTH1_ALIVE_HOME",
                                 ROOT / "data" / "alive"))

_lock = threading.Lock()
_world = None
_identity: Optional[dict] = None


class CanonicalWorldUnavailable(RuntimeError):
    """The living world cannot be resolved. The API fails loudly:
    no legacy engine may silently answer in its place."""


def _load():
    from earth1 import persistence
    pkl = ALIVE_HOME / "world.pkl"
    if not pkl.exists():
        raise CanonicalWorldUnavailable(
            f"no canonical snapshot at {pkl} — the API refuses to "
            f"fabricate a world (and there is no legacy fallback)")
    try:
        w, _rng, info = persistence.load_world(pkl)
    except Exception as e:                       # noqa: BLE001 — surfaced
        raise CanonicalWorldUnavailable(
            f"canonical snapshot failed the loader: {e}") from e
    st = {}
    st_path = ALIVE_HOME / "state.json"
    if st_path.exists():
        st = json.loads(st_path.read_text())
    identity = {"world_day": int(w.day),
                "alive": int(w.health.alive.sum()),
                "population": int(w.civ.n),
                "schema_version": info["schema_version"],
                "snapshot_sha256": st.get("sha256"),
                "checksum": info.get("checksum"),
                "source": str(pkl)}
    return w, identity


def get_world():
    """THE canonical world (shared, read-only by contract) and its
    identity. Reload happens only when the snapshot on disk changes."""
    global _world, _identity
    with _lock:
        st_path = ALIVE_HOME / "state.json"
        current_sha = None
        if st_path.exists():
            try:
                current_sha = json.loads(st_path.read_text()).get("sha256")
            except ValueError:
                pass
        if _world is None or (
                current_sha
                and _identity
                and _identity.get("snapshot_sha256") != current_sha):
            _world, _identity = _load()
        return _world, dict(_identity)


def clone_world():
    """A deep clone of the COMPLETE canonical civilization, for branch
    and forecast paths. Never a reduced representation — the clone is
    the same dataclass with every persistent field."""
    w, identity = get_world()
    return copy.deepcopy(w), identity


def reset_cache():
    """Test hook."""
    global _world, _identity
    with _lock:
        _world, _identity = None, None


# ── retired resolvers: fail loudly, never silently ──────────────────

def get_world_state(*_a, **_k):
    raise CanonicalWorldUnavailable(
        "get_world_state() resolved the retired engine family and is "
        "gone (0.5e). Use get_world()/clone_world() — the canonical "
        "alive.World is the only Earth.")


def get_living_world(*_a, **_k):
    raise CanonicalWorldUnavailable(
        "get_living_world() resolved the retired LivingWorld and is "
        "gone (0.5e). Use get_world()/clone_world().")


# ── DB plumbing (unchanged — not world resolution) ──────────────────

def get_db():
    """Yield a DB session when configured, else None (routes handle)."""
    from earth1.db import get_session, is_enabled
    if not is_enabled():
        yield None
        return
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_civ():
    """Legacy trait-view accessor: now the canonical world's civ."""
    w, _ = get_world()
    return w.civ


def reset_civ():
    """Test hook (legacy name kept for test_api.py)."""
    reset_cache()
