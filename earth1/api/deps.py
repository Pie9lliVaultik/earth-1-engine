"""Shared dependencies — civilization singleton + optional DB session."""
from __future__ import annotations
import os
from typing import Optional
from earth1.types import Civilization

_civ: Civilization | None = None


def get_civ() -> Civilization:
    global _civ
    if _civ is None:
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
