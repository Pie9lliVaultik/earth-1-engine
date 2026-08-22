"""Candidate conviction laws — 0.8 experimental arms ONLY.

Nothing here is wired into production. The battery patches
`alive.update_conviction` per arm (spawn-isolated processes), the
same pattern the 0.8-A ablation used. Laws and their rationale are
pre-registered in ops/alive/CANDIDATE_LAW_EXPERIMENT_0_8.md; their
coefficients are fit ONLY against registry target T1 and then frozen.

Signature contract: each law matches update_conviction(forces, alpha,
adj) -> new alpha, so the daily loop needs no other change. Anchors
(alpha0) ride on a module-level holder set once per world by the
battery (the World object carries no new persistent fields in the
lab phase).
"""
from __future__ import annotations

import numpy as np

GAIN_INCUMBENT = 0.06

# set by the battery per world: the agent's own genesis conviction
ALPHA0 = None


def _pole_agreement(forces, adj, deg):
    pole = (forces > 0.5).astype(forces.dtype)
    nb_pole = (adj @ pole) / deg[:, None]
    return 1.0 - np.abs(nb_pole - pole).mean(axis=1)


def _distance_agreement(forces, adj, deg):
    """Continuous-distance agreement: 1 − 2·(mean neighbor |Δf|).
    Computed exactly: for each channel, E|f_i − f_j| is expensive per
    edge; the mean over neighbors of f_j is cheap, so we use the
    dispersion-corrected proxy
        d_i = mean_c ( |f_i,c − nbmean_i,c| + nbsd_i,c · κ )
    with κ = 0 (first moment only) — the first-moment distance to the
    neighborhood mean. This registers disagreement continuously and
    costs two matvecs. A railed-unanimous neighborhood at the SAME
    pole as the agent gives d = 0 (true agreement); an agent displaced
    from its neighborhood registers d > 0 regardless of poles."""
    nbmean = (adj @ forces) / deg[:, None]
    d = np.abs(forces - nbmean).mean(axis=1)
    return 1.0 - 2.0 * np.clip(d, 0.0, 0.5)


def c1_anchored_pole(forces, alpha, adj, gain=GAIN_INCUMBENT,
                     lam=0.02):
    """C1 — FJ-family: incumbent pole agreement + reversion to the
    agent's own genesis conviction."""
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    agr = _pole_agreement(forces, adj, deg)
    out = alpha + gain * (agr - 0.5) * 2.0 - lam * (alpha - ALPHA0)
    return np.clip(out, 0.02, 1.0)


def c2_anchored_distance(forces, alpha, adj, gain=GAIN_INCUMBENT,
                         lam=0.02):
    """C2 — continuous-distance agreement + genesis anchor."""
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    agr = _distance_agreement(forces, adj, deg)
    out = alpha + gain * (agr - 0.5) * 2.0 - lam * (alpha - ALPHA0)
    return np.clip(out, 0.02, 1.0)


def c3_logodds_symmetric(forces, alpha, adj, gain=0.10, lam=0.0):
    """C3 — endogenous symmetric confidence in log-odds space: bounds
    are asymptotes, not absorbing rails; no anchor. lam unused (kept
    for a uniform fitting interface)."""
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    agr = _distance_agreement(forces, adj, deg)
    a = np.clip(alpha, 0.02, 0.98)
    logit = np.log(a / (1.0 - a))
    logit = logit + gain * (agr - 0.5) * 2.0
    out = 1.0 / (1.0 + np.exp(-logit))
    return np.clip(out, 0.02, 1.0)


def nc2_excessive_reversion(forces, alpha, adj, gain=GAIN_INCUMBENT,
                            lam=0.02):
    """NC2 — the winning family's law with lambda x10. The battery
    must FAIL this arm."""
    return c1_anchored_pole(forces, alpha, adj, gain=gain,
                            lam=10.0 * lam)


def nc3_frozen(forces, alpha, adj, gain=0.0, lam=0.02):
    """NC3 — no social hardening at all: alpha relaxes to the anchor
    and never responds. The battery must FAIL this arm (T6/T7)."""
    out = alpha - lam * (alpha - ALPHA0)
    return np.clip(out, 0.02, 1.0)


LAWS = {"c1": c1_anchored_pole, "c2": c2_anchored_distance,
        "c3": c3_logodds_symmetric,
        "nc2": nc2_excessive_reversion, "nc3": nc3_frozen}
