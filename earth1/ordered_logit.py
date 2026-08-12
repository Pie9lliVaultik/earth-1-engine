"""Ordered-logit distribution mapping for multi-option survey questions.

Maps per-agent continuous stances (0,1) to K-option response distributions
via learned cut-points. For a K-option question, K-1 cut-points θ partition
the latent stance space:

  P(option k | agent i) = σ(θ_k - z_i) - σ(θ_{k-1} - z_i)

where z_i = logit(stance_i) and θ_0 = -∞, θ_K = +∞.

Different country sub-populations have different stance distributions
(from genesis → calibration → diffusion), so the same cut-points produce
different response distributions per country — which is exactly what we need.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from earth1.rng import logit, sigmoid


def _cutpoints_from_raw(raw: np.ndarray) -> np.ndarray:
    """Convert unconstrained raw parameters to ordered cut-points.

    θ_0 = raw_0
    θ_k = θ_{k-1} + softplus(raw_k) for k > 0

    Guarantees strict ordering.
    """
    out = np.empty_like(raw)
    out[0] = raw[0]
    for k in range(1, len(raw)):
        out[k] = out[k - 1] + np.log1p(np.exp(raw[k]))
    return out


def _raw_from_cutpoints(cutpoints: np.ndarray) -> np.ndarray:
    """Inverse of _cutpoints_from_raw — for initialization."""
    raw = np.empty_like(cutpoints)
    raw[0] = cutpoints[0]
    for k in range(1, len(cutpoints)):
        gap = cutpoints[k] - cutpoints[k - 1]
        raw[k] = np.log(np.expm1(max(gap, 1e-6)))
    return raw


def predict_agent_probs(z: np.ndarray, cutpoints: np.ndarray) -> np.ndarray:
    """Per-agent option probabilities.

    Args:
        z: (N,) logit-transformed stances
        cutpoints: (K-1,) ordered cut-points

    Returns:
        (N, K) probability matrix
    """
    K = len(cutpoints) + 1
    N = len(z)

    cum = sigmoid(cutpoints[np.newaxis, :] - z[:, np.newaxis])  # (N, K-1)

    probs = np.empty((N, K))
    probs[:, 0] = cum[:, 0]
    if K > 2:
        probs[:, 1:-1] = np.diff(cum, axis=1)
    probs[:, -1] = 1.0 - cum[:, -1]

    np.clip(probs, 1e-12, 1.0, out=probs)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs


def predict_distribution(stances: np.ndarray, cutpoints: np.ndarray) -> np.ndarray:
    """Predict population-level response distribution.

    Args:
        stances: (N,) agent stances in (0, 1)
        cutpoints: (K-1,) ordered cut-points

    Returns:
        (K,) predicted distribution (sums to 1)
    """
    z = logit(stances)
    probs = predict_agent_probs(z, cutpoints)
    return probs.mean(axis=0)


def predict_country_distributions(
    stances: np.ndarray,
    country: np.ndarray,
    cutpoints: np.ndarray,
    country_indices: dict[str, int],
) -> dict[str, np.ndarray]:
    """Predict response distribution per country.

    Args:
        stances: (N,) post-diffusion stances
        country: (N,) integer country indices
        cutpoints: (K-1,) cut-points
        country_indices: {iso2 -> index in country array}

    Returns:
        {iso2 -> (K,) distribution}
    """
    z = logit(stances)
    result = {}
    for code, idx in country_indices.items():
        mask = country == idx
        if mask.sum() < 10:
            continue
        probs = predict_agent_probs(z[mask], cutpoints)
        result[code] = probs.mean(axis=0)
    return result


def _jsd(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence between two distributions."""
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)
    p = np.clip(p, 1e-12, None)
    q = np.clip(q, 1e-12, None)
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    kl_pm = np.sum(p * np.log(p / m))
    kl_qm = np.sum(q * np.log(q / m))
    return 0.5 * (kl_pm + kl_qm)


def calibrate_cutpoints(
    stances: np.ndarray,
    country: np.ndarray,
    country_targets: dict[str, np.ndarray],
    country_indices: dict[str, int],
    n_options: int,
    max_iter: int = 200,
) -> np.ndarray:
    """Learn cut-points to minimize JSD across countries.

    Args:
        stances: (N,) post-diffusion stances
        country: (N,) integer country index per agent
        country_targets: {iso2 -> (K,) actual response distribution}
        country_indices: {iso2 -> integer index}
        n_options: K, number of response options
        max_iter: L-BFGS-B iterations

    Returns:
        (K-1,) calibrated cut-points
    """
    n_cuts = n_options - 1

    z_by_country = {}
    valid_targets = {}
    for code, target_dist in country_targets.items():
        if code not in country_indices:
            continue
        idx = country_indices[code]
        mask = country == idx
        if mask.sum() < 10:
            continue
        target = np.asarray(target_dist, dtype=np.float64)
        if target.sum() < 0.01 or len(target) != n_options:
            continue
        target = target / target.sum()
        z_by_country[code] = logit(stances[mask])
        valid_targets[code] = target

    if len(valid_targets) < 2:
        return np.linspace(-2.0, 2.0, n_cuts)

    # Initialize cut-points from global stance quantiles
    all_z = logit(stances)
    quantiles = np.linspace(0, 1, n_options + 1)[1:-1]
    init_cuts = np.quantile(all_z, quantiles)
    if n_cuts == 1:
        init_cuts = np.array([np.median(all_z)])
    init_raw = _raw_from_cutpoints(init_cuts)

    def objective(raw):
        cuts = _cutpoints_from_raw(raw)
        total_jsd = 0.0
        for code, target in valid_targets.items():
            z_c = z_by_country[code]
            pred = predict_agent_probs(z_c, cuts).mean(axis=0)
            total_jsd += _jsd(pred, target)
        return total_jsd / len(valid_targets)

    result = minimize(
        objective, init_raw,
        method='L-BFGS-B',
        options={'maxiter': max_iter, 'ftol': 1e-10},
    )

    return _cutpoints_from_raw(result.x)


def calibrate_cutpoints_global(
    stances: np.ndarray,
    global_target: np.ndarray,
    n_options: int,
    max_iter: int = 100,
) -> np.ndarray:
    """Learn cut-points from a single global target distribution.

    Simpler variant when per-country distributions aren't available.
    """
    n_cuts = n_options - 1
    z = logit(stances)

    target = np.asarray(global_target, dtype=np.float64)
    target = target / target.sum()

    quantiles = np.linspace(0, 1, n_options + 1)[1:-1]
    init_cuts = np.quantile(z, quantiles)
    if n_cuts == 1:
        init_cuts = np.array([np.median(z)])
    init_raw = _raw_from_cutpoints(init_cuts)

    def objective(raw):
        cuts = _cutpoints_from_raw(raw)
        pred = predict_agent_probs(z, cuts).mean(axis=0)
        return _jsd(pred, target)

    result = minimize(
        objective, init_raw,
        method='L-BFGS-B',
        options={'maxiter': max_iter, 'ftol': 1e-10},
    )

    return _cutpoints_from_raw(result.x)
