"""Candidate propagation operators — 0.8 IT3 experimental arms ONLY.

Nothing here touches production. The IT3 runner patches
`alive.propagate` per arm in spawn-isolated processes. Laws follow
PROPAGATION_LAW_EXPERIMENT_0_8_IT3.md (frozen 4b44e93).

Every operator here records per-pass contraction into PASS_LOG:
(day_counter, layer, var_before, var_after) — the registered inside-
pass instrumentation. The incumbent is re-implemented WITH hooks so
C0 and candidates are measured by the same instrument (clarity over
micro-optimization at 200k lab scale).
"""
from __future__ import annotations

import numpy as np

ETA_INCUMBENT = 0.18
PASS_LOG = []          # cleared by the runner each recording window
_DAY = [0]             # runner increments daily; P3 uses it for rng


def _record(layer, before, after):
    PASS_LOG.append((int(_DAY[0]), int(layer),
                     float(before), float(after)))


def _incumbent_layer(f, a, inv_a, adj, safe_deg, eta, susceptibility,
                     pole_on=True):
    pole = (f > 0.5).astype(f.dtype)
    if pole_on:
        align_tgt = pole
    else:
        align_tgt = None               # value-averaging arm
    nb_val_num = adj @ (inv_a[:, None] * f)
    nb_val_den = np.asarray(adj @ inv_a).ravel()
    if pole_on:
        align_num = adj @ (a[:, None] * pole)
        align_den = np.asarray(adj @ a).ravel()
        pull_pole = align_num - f * align_den[:, None]
    else:
        align_num = adj @ (a[:, None] * f)
        align_den = np.asarray(adj @ a).ravel()
        pull_pole = align_num - f * align_den[:, None]
    pull_mean = nb_val_num - f * nb_val_den[:, None]
    move = eta * (pull_pole + pull_mean) / safe_deg[:, None]
    if susceptibility is not None:
        move = move * susceptibility
    return np.clip(f + move, 0.0, 1.0)


def make_operator(eta=ETA_INCUMBENT, layers=2, pole_on=True,
                  gate_delta=None, exposure_p=None):
    """Build a propagate(forces, alpha, adj, ...) replacement."""

    def op(forces, alpha, adj, beta=1.0, eta_=None, layers_=None,
           susceptibility=None, **kw):
        f = forces.copy()
        deg = np.asarray(adj.sum(axis=1)).ravel()
        safe_deg = np.maximum(deg, 1.0)
        a = np.clip(alpha, 0.0, 1.0) ** beta
        inv_a = 1.0 - a

        active = None
        if exposure_p is not None:
            rng = np.random.default_rng(910_000 + _DAY[0])
            active = rng.random(f.shape[0]) < exposure_p

        adj_use = adj
        for L in range(max(1, layers)):
            vb = float(f.var())
            if gate_delta is not None:
                nf = _gated_layer(f, a, inv_a, adj, safe_deg, eta,
                                  susceptibility, gate_delta, pole_on)
            else:
                nf = _incumbent_layer(f, a, inv_a, adj_use, safe_deg,
                                      eta, susceptibility, pole_on)
            if active is not None:
                nf = np.where(active[:, None], nf, f)
            f = nf
            _record(L, vb, float(f.var()))
        return f

    return op


def _gated_layer(f, a, inv_a, adj, safe_deg, eta, susceptibility,
                 delta, pole_on):
    """Bounded-confidence: per channel, only neighbors within |Δf|<=
    delta contribute. Edge-explicit at lab scale."""
    coo = adj.tocoo()
    r, c, w = coo.row, coo.col, coo.data
    n, k = f.shape
    out = f.copy()
    for ch in range(k):
        fi, fj = f[r, ch], f[c, ch]
        gate = np.abs(fi - fj) <= delta
        wg = w * gate
        if pole_on:
            tgt = (fj > 0.5).astype(f.dtype)
        else:
            tgt = fj
        num = np.bincount(r, weights=wg * (a[c] * tgt + inv_a[c] * fj),
                          minlength=n)
        den = np.bincount(r, weights=wg * (a[c] + inv_a[c]),
                          minlength=n)
        nb = np.where(den > 0, num / np.maximum(den, 1e-12), f[:, ch])
        move = eta * (nb - f[:, ch]) * (den > 0)
        if susceptibility is not None:
            s = susceptibility[:, ch] if susceptibility.ndim == 2 \
                else susceptibility
            move = move * s
        out[:, ch] = np.clip(f[:, ch] + move, 0.0, 1.0)
    return out


def randomized_graph(adj, seed=911):
    """KA4: approximate degree-preserving randomization — permute the
    column endpoints of the COO representation. Detection control
    only (mixing accelerates), not a scientific arm."""
    from scipy import sparse
    coo = adj.tocoo()
    rng = np.random.default_rng(seed)
    cols = coo.col.copy()
    rng.shuffle(cols)
    m = sparse.csr_matrix((coo.data, (coo.row, cols)),
                          shape=adj.shape)
    m.setdiag(0.0)
    m.eliminate_zeros()
    return m
