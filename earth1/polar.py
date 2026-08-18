"""POLAR interaction — attraction toward poles, not toward means.

EXPERIMENTAL (2026-08-18). Never in a production path; adoption would
require a registered build. Prereg: data/polar_interaction_prereg.json

Why it exists: Earth-1's bounded-confidence diffusion is an AVERAGING
operator. Measured against 4,728 real within-cell response densities,
every layers/epsilon setting moved mass AWAY from the extremes
(0.036 -> 0.026) while reality holds 0.647 there. Averaging cannot
manufacture extremes; only a pole-directed operator can.

Mechanism (one round):
  - hubs = top `hub_fraction` of agents by degree (scale-free-ish tail
    of the genesis graph)
  - a random `fire_rate` share of hubs emit an influence event
  - each event reaches the hub's neighbours; a neighbour is pulled
    TOWARD THE POLE the hub sits on (1.0 if hub >= 0.5 else 0.0) by
    `attraction`, scaled by how convinced the hub is
  - if |target - hub| > `repulsion_threshold`, the neighbour instead
    moves AWAY from that pole by `repulsion_strength` (backfire)
Vectorized over events; O(edges touched) per round.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def polar_round(
    s: np.ndarray,
    adj: sparse.csr_matrix,
    degree: np.ndarray,
    rng: np.random.Generator,
    hub_fraction: float = 0.20,
    fire_rate: float = 0.01,
    attraction: float = 0.10,
    repulsion_threshold: float = 0.60,
    repulsion_strength: float = 0.05,
) -> np.ndarray:
    """One round of pole-directed influence. Returns updated stances."""
    n = len(s)
    k = max(1, int(n * hub_fraction))
    hubs = np.argpartition(degree, -k)[-k:]
    n_fire = max(1, int(len(hubs) * fire_rate))
    firing = rng.choice(hubs, size=n_fire, replace=False)

    out = s.copy()
    indptr, indices = adj.indptr, adj.indices
    for h in firing:
        nb = indices[indptr[h]:indptr[h + 1]]
        if len(nb) == 0:
            continue
        pole = 1.0 if s[h] >= 0.5 else 0.0
        conviction = abs(s[h] - 0.5) * 2.0          # 0..1
        gap = np.abs(out[nb] - s[h])
        pull = gap <= repulsion_threshold
        # attraction: move toward the hub's pole
        out[nb[pull]] += (attraction * conviction
                          * (pole - out[nb[pull]]))
        # repulsion: move away from that pole (backfire)
        push = ~pull
        if push.any():
            out[nb[push]] -= (repulsion_strength * conviction
                              * (pole - out[nb[push]]))
    return np.clip(out, 0.0, 1.0)


def polar_settle(
    s0: np.ndarray,
    adj: sparse.csr_matrix,
    seed: int = 42,
    rounds: int = 20,
    **params,
) -> np.ndarray:
    """Run `rounds` of polar influence from initial stances s0."""
    degree = np.asarray((adj != 0).sum(axis=1)).ravel()
    rng = np.random.default_rng(seed)
    s = s0.copy()
    for _ in range(rounds):
        s = polar_round(s, adj, degree, rng, **params)
    return s
