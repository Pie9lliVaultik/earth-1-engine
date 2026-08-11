"""Shared dependencies — the civilization singleton."""
from __future__ import annotations
import os
from earth1.types import Civilization

_civ: Civilization | None = None


def get_civ() -> Civilization:
    global _civ
    if _civ is None:
        from earth1.engine import build_civilization
        pop = int(os.environ.get("EARTH1_POP", "100000"))
        seed = int(os.environ.get("EARTH1_SEED", "42"))
        _civ = build_civilization(pop, seed)
    return _civ


def reset_civ():
    global _civ
    _civ = None
