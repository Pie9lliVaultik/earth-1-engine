"""Deterministic seeded PRNG — every run is reproducible."""
from __future__ import annotations
import numpy as np


def make_rng(seed: int = 42) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(seed))


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return np.log(p / (1 - p))
