"""Mean-preserving hybrid (Benchmark A v2, frozen).

    logit(p_i) = logit(p_anchor) + Delta_i - K

K is solved numerically (bisection) so that the weighted synthetic
population mean equals the permitted anchor to |err| <= TOL. No sigmoid
averaging may shift the calibrated marginal: the KA below proves it.
Earth-1 receives zero credit for the anchored marginal by construction.
"""
from __future__ import annotations

import numpy as np

TOL = 1e-9
_L = 1e-6


def _logit(p):
    p = np.clip(p, _L, 1 - _L)
    return np.log(p / (1 - p))


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def solve_K(anchor: float, delta: np.ndarray, w: np.ndarray | None = None,
            tol: float = TOL, max_iter: int = 200):
    """Return (K, p_i) with sum(w_i p_i)/sum(w_i) == anchor within tol."""
    delta = np.asarray(delta, float)
    w = np.ones_like(delta) if w is None else np.asarray(w, float)
    w = w / w.sum()
    base = float(_logit(np.asarray([anchor]))[0])

    def mean_at(K):
        return float(np.sum(w * _sig(base + delta - K)))

    lo, hi = -30.0, 30.0
    if not (mean_at(hi) - anchor <= 0 <= mean_at(lo) - anchor):
        # mean_at is decreasing in K; widen defensively (bounded domain)
        lo, hi = -60.0, 60.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        m = mean_at(mid)
        if abs(m - anchor) <= tol:
            return mid, _sig(base + delta - mid)
        if m > anchor:
            lo = mid
        else:
            hi = mid
    mid = 0.5 * (lo + hi)
    return mid, _sig(base + delta - mid)


def center_latent(latent: np.ndarray, w: np.ndarray | None = None) -> np.ndarray:
    """Delta_i: the agent latent with its weighted mean removed. The
    LEVEL degree of freedom belongs to the anchor and K, never to the
    structure (the VNF unpenalized-intercept lesson, per cell)."""
    latent = np.asarray(latent, float)
    w = np.ones_like(latent) if w is None else np.asarray(w, float)
    return latent - float(np.sum(w * latent) / w.sum())


def ka_mean_preservation(seed: int = 0, n_cases: int = 200) -> dict:
    """Deterministic KA: across anchors in (0.02..0.98), heavy-tailed and
    skewed deltas, and non-uniform weights, the weighted mean equals the
    anchor to TOL, and the ordering of p_i equals the ordering of Delta_i
    (structure preserved)."""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for _ in range(n_cases):
        n = int(rng.integers(50, 5000))
        anchor = float(rng.uniform(0.02, 0.98))
        kind = rng.integers(0, 3)
        d = (rng.normal(0, rng.uniform(0.1, 3.0), n) if kind == 0
             else rng.standard_t(3, n) * rng.uniform(0.2, 2.0) if kind == 1
             else rng.exponential(1.5, n) - 1.5)
        w = rng.uniform(0.2, 5.0, n)
        d = center_latent(d, w)
        K, p = solve_K(anchor, d, w)
        err = abs(float(np.sum((w / w.sum()) * p)) - anchor)
        worst = max(worst, err)
        order_ok = bool(np.all(np.diff(p[np.argsort(d)]) >= -1e-15))
        if not order_ok:
            return {"pass": False, "reason": "ordering broken"}
    return {"pass": bool(worst <= 1e-8), "worst_abs_mean_error": worst, "n_cases": n_cases}
