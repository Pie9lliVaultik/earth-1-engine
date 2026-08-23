"""FROZEN SCORING — Benchmark A. Pure functions over arrays; no model
code. Hash recorded in ops/alive/BENCHMARK_A_PREREG_v1.md at freeze.
"""
from __future__ import annotations

import numpy as np

# ── Task (i)/(ii): errors in percentage points ─────────────────────
def mae_pp(pred, truth) -> float:
    p, t = np.asarray(pred, float), np.asarray(truth, float)
    return float(np.mean(np.abs(p - t)) * 100.0)


def relative_reduction(mae_model: float, mae_baseline: float) -> float:
    """(baseline − model)/baseline; positive = model better."""
    return float((mae_baseline - mae_model) / max(mae_baseline, 1e-12))


def gradient_direction_pct(pred_cells, truth_cells, pred_ref, truth_ref) -> float:
    """Share of held-out cells whose predicted sign of (cell − reference)
    equals the true sign. Cells with |true deviation| < 0.5pp are
    excluded (no direction to get right)."""
    pc, tc = np.asarray(pred_cells, float), np.asarray(truth_cells, float)
    pr, tr = np.asarray(pred_ref, float), np.asarray(truth_ref, float)
    dt = tc - tr; dp = pc - pr
    m = np.abs(dt) >= 0.005
    if m.sum() == 0:
        return float("nan")
    return float(np.mean(np.sign(dp[m]) == np.sign(dt[m])) * 100.0)


# ── Task (iii): energy distance on binary response vectors ─────────
def _pairwise_mean_hamming(A, B, wa=None, wb=None, max_n=4000, rng=None):
    rng = rng or np.random.default_rng(0)
    if A.shape[0] > max_n:
        idx = rng.choice(A.shape[0], max_n, replace=False, p=(wa / wa.sum()) if wa is not None else None); A = A[idx]; wa = None
    if B.shape[0] > max_n:
        idx = rng.choice(B.shape[0], max_n, replace=False, p=(wb / wb.sum()) if wb is not None else None); B = B[idx]; wb = None
    A = A.astype(np.float32); B = B.astype(np.float32)
    # Hamming distance between binary rows = |a|+|b|-2 a·b
    d = A.sum(1)[:, None] + B.sum(1)[None, :] - 2.0 * (A @ B.T)
    if wa is None and wb is None:
        return float(d.mean())
    wa = np.ones(A.shape[0]) if wa is None else wa; wb = np.ones(B.shape[0]) if wb is None else wb
    return float((wa[:, None] * wb[None, :] * d).sum() / (wa.sum() * wb.sum()))


def energy_distance(X, Y, wx=None, wy=None, seed=0) -> float:
    """Energy distance 2E|X−Y| − E|X−X'| − E|Y−Y'| with Hamming metric on
    binary vectors; sample-weighted when weights are given; subsampled
    deterministically for large sets."""
    rng = np.random.default_rng(seed)
    exy = _pairwise_mean_hamming(X, Y, wx, wy, rng=rng)
    exx = _pairwise_mean_hamming(X, X, wx, wx, rng=rng)
    eyy = _pairwise_mean_hamming(Y, Y, wy, wy, rng=rng)
    return float(2 * exy - exx - eyy)


# ── Task (v): cross-wave deltas (registered; data-blocked in v1) ───
def delta_mae_pp(pred_delta, true_delta) -> float:
    return mae_pp(pred_delta, true_delta)


# ── CIs ───────────────────────────────────────────────────────────
def bootstrap_ci(values, stat=np.mean, n_boot=2000, seed=0, alpha=0.05):
    v = np.asarray(values, float); rng = np.random.default_rng(seed)
    if v.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    boots = np.array([stat(v[rng.integers(0, v.size, v.size)]) for _ in range(n_boot)])
    return (float(stat(v)), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2)))


def paired_bootstrap_diff_ci(a, b, n_boot=2000, seed=0, alpha=0.05):
    """CI for mean(a − b) over paired units (e.g. per-question MAEs)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return bootstrap_ci(a - b, n_boot=n_boot, seed=seed, alpha=alpha)


def sha256_of_file(path) -> str:
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()
