"""Cube cache — the O(cells) aggregate read.

Discretize the force space into ~5,000 cells. Each cell stores the count and
mean stance of the agents it contains, allowing aggregate reads without
iterating over individual agents.

Three distinct objects the bible disambiguates:
  1. Force space (8-9D continuous) — where projection happens
  2. Soul manifold (~80-D continuous) — full trait vector
  3. Cube cache (~5,000 cells) — discretized force space for fast aggregates
"""
from __future__ import annotations
from typing import Dict, Tuple
import numpy as np
from earth1.types import Civilization, Question, Force, NUM_FORCES
from earth1.forces import project_all


def build_cube(
    civ: Civilization,
    q: Question,
    settled: np.ndarray,
    bins_per_dim: int = 4,
) -> Dict[Tuple[int, ...], dict]:
    """Build a discretized cube cache from settled stances.

    Each key is a tuple of bin indices (one per force dimension).
    Value: {count, mean_stance, force_centroid}.
    """
    # discretize each force dimension into bins
    force_bins = np.clip(
        (civ.forces * bins_per_dim).astype(np.int32), 0, bins_per_dim - 1
    )  # (N, 8)

    cube: Dict[Tuple[int, ...], dict] = {}
    # use structured approach — convert to tuple keys via unique rows
    keys = np.ascontiguousarray(force_bins).view(
        np.dtype((np.void, force_bins.dtype.itemsize * NUM_FORCES))
    ).ravel()

    unique_keys, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)

    for idx in range(len(unique_keys)):
        mask = inverse == idx
        cell_key = tuple(force_bins[np.argmax(mask)])
        cube[cell_key] = {
            "count": int(counts[idx]),
            "mean_stance": float(settled[mask].mean()),
            "force_centroid": civ.forces[mask].mean(axis=0),
        }

    return cube


def aggregate_read(cube: Dict[Tuple[int, ...], dict]) -> dict:
    """O(cells) aggregate — total yes%, weighted by cell population."""
    total = 0
    weighted_stance = 0.0
    for cell in cube.values():
        total += cell["count"]
        weighted_stance += cell["count"] * cell["mean_stance"]
    return {
        "n": total,
        "yes_pct": weighted_stance / max(total, 1),
        "num_cells": len(cube),
    }
