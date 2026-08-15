"""Shared dependencies — civilization singleton + optional DB session."""
from __future__ import annotations
import os
from typing import Optional
from earth1.types import Civilization

_civ: Civilization | None = None


def get_civ() -> Civilization:
    global _civ
    if _civ is None:
        # EARTH1_LIVING=1 serves the LIVING world (bible §21.2: the
        # frozen copy is for calibration, the living copy is the
        # product) — the persisted, daily-ticked civilization with
        # receiver signal and generational change. Falls back to a
        # frozen genesis civ when no living world exists on disk.
        if os.environ.get("EARTH1_LIVING", "0") == "1":
            living_path = os.environ.get(
                "EARTH1_WORLD_PATH", "data/living/earth1")
            if os.path.exists(os.path.join(living_path, "world.json")):
                from earth1.living import LivingWorld
                _civ = LivingWorld.load(living_path).state.civ
                return _civ
        pop = int(os.environ.get("EARTH1_POP", "100000"))
        seed = int(os.environ.get("EARTH1_SEED", "42"))
        use_genesis = os.environ.get("EARTH1_GENESIS", "1") == "1"
        if use_genesis:
            from earth1.engine import build_genesis_civilization
            _civ = build_genesis_civilization(pop, seed)
        else:
            from earth1.engine import build_civilization
            _civ = build_civilization(pop, seed)
    return _civ


def reset_civ():
    global _civ
    _civ = None


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
