"""Shared dependencies — THE world singleton + optional DB session.

"There is only one Earth-1" (2026-08-16 audit): every route serves the
same WorldState. `/ask` reads its civilization; `/world` ticks it; when
the living world exists on disk it IS that state, and ticks persist.
The old design kept a second module-global world inside routes/world.py
— two Earths, one queried, one evolved. That is gone.
"""
from __future__ import annotations
import os
from typing import Optional

from earth1.types import Civilization

_living = None          # LivingWorld when EARTH1_LIVING=1 and one exists
_state = None           # the one WorldState every route shares


def get_world_state():
    """THE world. Living when available; frozen genesis otherwise."""
    global _living, _state
    if _state is None:
        if os.environ.get("EARTH1_LIVING", "0") == "1":
            living_path = os.environ.get(
                "EARTH1_WORLD_PATH", "data/living/earth1")
            if os.path.exists(os.path.join(living_path, "world.json")):
                from earth1.living import LivingWorld
                _living = LivingWorld.load(living_path)
                _state = _living.state
                return _state
        from earth1.tick import WorldState
        pop = int(os.environ.get("EARTH1_POP", "100000"))
        seed = int(os.environ.get("EARTH1_SEED", "42"))
        _state = WorldState.create(pop=pop, seed=seed, min_per_country=100)
    return _state


def get_living_world():
    """The LivingWorld wrapper when the state is persistent, else None.
    Callers that mutate the world use this to save after ticking."""
    get_world_state()
    return _living


def get_civ() -> Civilization:
    return get_world_state().civ


def reset_civ(pop: Optional[int] = None, seed: Optional[int] = None):
    """Drop the singleton (tests / explicit reset). Optionally override
    pop/seed for the rebuild via env until next reset."""
    global _living, _state
    _living = None
    _state = None
    if pop is not None:
        os.environ["EARTH1_POP"] = str(pop)
    if seed is not None:
        os.environ["EARTH1_SEED"] = str(seed)


def get_db():
    from earth1.db import get_session
    session = get_session()
    if session is None:
        yield None
        return
    try:
        yield session
    finally:
        session.close()
