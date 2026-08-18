"""DIRECTION-VS-RATE susceptibility — candidate original physics.

EXPERIMENTAL (2026-08-18), flag-gated, never in a production path.
Prereg: data/direction_susceptibility_prereg.json (written first).

The distinction: every operator in the field moves agents toward
something shared and lets susceptibility set HOW FAST. Here each
agent's susceptibility sets WHERE it moves in force space.

Today's response law (uniform direction):
    d_logit_i = GAIN * (shock . profile)                 same for all i
This operator:
    d_logit_i = GAIN * ((shock * s_i) . profile)
where s_i is agent i's per-FORCE susceptibility vector, built from its
own traits, and normalized so that

    mean_i(s_i) == 1  (per force)

which makes the POPULATION-MEAN response identical to the uniform law.
The aggregate that already validates (ratio 0.97) is preserved by
construction; only the DISTRIBUTION of directions changes — which is
the quantity that fails (variance ratio 0.16, rank corr -0.41).

Susceptibility model (parameters fitted, never authored):
    s_i[f] = 1 + sum_t beta[f, t] * z_i[t]
with z the standardized agent traits and beta the fitted matrix;
clipped at zero and renormalized to preserve the mean.
"""
from __future__ import annotations

import numpy as np

SUSC_TRAITS = ("openness", "doubt", "risk_appetite", "empathy",
               "desire_intensity", "neuroticism", "extraversion",
               "individualism")


def trait_matrix(civ) -> np.ndarray:
    cols = []
    for t in SUSC_TRAITS:
        a = getattr(civ, t, None)
        if a is not None:
            cols.append(np.asarray(a, dtype=np.float64))
    Z = np.column_stack(cols)
    mu, sd = Z.mean(axis=0), Z.std(axis=0)
    return (Z - mu) / np.where(sd > 1e-9, sd, 1.0)


def susceptibility(civ, beta: np.ndarray) -> np.ndarray:
    """(N, NUM_FORCES) per-agent per-force susceptibility, mean 1."""
    Z = trait_matrix(civ)                       # (N, T)
    S = 1.0 + Z @ beta.T                        # (N, F)
    S = np.clip(S, 0.0, None)
    m = S.mean(axis=0, keepdims=True)
    return S / np.where(m > 1e-9, m, 1.0)       # mean exactly 1 per force


def directional_response(
    civ,
    shock: np.ndarray,
    profile: np.ndarray,
    beta: np.ndarray,
    gain: float = 3.1,
) -> np.ndarray:
    """Per-agent logit shift under direction-heterogeneous response.

    With beta = 0 this reduces EXACTLY to the current uniform law
    (S == 1), so the operator is a strict generalization and the
    flag-off path is bit-identical.
    """
    S = susceptibility(civ, beta)               # (N, F), mean 1
    return gain * ((S * shock[np.newaxis, :]) @ profile)
