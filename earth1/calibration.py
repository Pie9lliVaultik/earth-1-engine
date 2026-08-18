"""Weight calibration — per-country ridge regression in logit space.

Given survey targets by country (WVS/Pew/Gallup), find force weights that make
each country's sub-population predict its own target. Different countries have
different force profiles, so the same weight vector produces different predictions
per country — this cross-country variation is the signal the solver uses.

Extended calibration uses forces + raw traits (18 features) for stronger
cross-country differentiation. Standard calibration uses 8 force channels only.
"""
from __future__ import annotations

import numpy as np
from earth1.types import Civilization, NUM_FORCES
from earth1.rng import logit, sigmoid


_EXTENDED_TRAITS = [
    'openness', 'risk_appetite', 'doubt', 'empathy', 'desire_intensity',
    'agreeableness', 'extraversion', 'neuroticism',
    'individualism', 'power_distance',
    # C2: real within-country structure from WVS7 microdata. Absent
    # (None) unless EARTH1_RELIGIOSITY=1 at genesis -> no feature, no
    # change to any recorded number.
    'religiosity',
]


def _build_features(civ: Civilization, extended: bool = False) -> np.ndarray:
    """Build centered feature matrix for calibration.

    extended=False: (N, 8) centered forces only
    extended=True:  (N, 8+T) centered forces + centered traits
    """
    forces_centered = civ.forces - civ.means[np.newaxis, :]
    if not extended:
        return forces_centered

    trait_arrays = []
    for name in _EXTENDED_TRAITS:
        arr = getattr(civ, name, None)
        if arr is not None:
            trait_arrays.append(arr)
    if not trait_arrays:
        return forces_centered

    traits = np.column_stack(trait_arrays)
    traits_centered = traits - traits.mean(axis=0, keepdims=True)
    return np.hstack([forces_centered, traits_centered])


def _get_country_index(civ: Civilization):
    """Return (code_to_idx dict, country_codes list) for the civilization."""
    try:
        from earth1.genesis import GENESIS_COUNTRY_CODES
        if int(civ.country.max()) >= 50:
            return ({c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)},
                    GENESIS_COUNTRY_CODES)
    except ImportError:
        pass
    from earth1.population import COUNTRY_CODES as ALL_CODES
    return {c: i for i, c in enumerate(ALL_CODES)}, ALL_CODES


def calibrate_single(
    civ: Civilization,
    baseline: float,
    country_targets: dict,
    ridge_alpha: float = 1.0,
    extended: bool = False,
) -> np.ndarray:
    """Learn weights for one question from country-level survey targets.

    extended=True uses forces + raw traits (18d) for stronger differentiation.

    Returns the learned weight vector (NUM_FORCES,) or (NUM_FORCES+T,).
    """
    code_to_idx, _ = _get_country_index(civ)
    features = _build_features(civ, extended=extended)
    n_feat = features.shape[1]
    baseline_logit = logit(np.array([baseline]))[0]

    X_rows = []
    y_rows = []
    for code, target_pct in country_targets.items():
        if code not in code_to_idx:
            continue
        mask = civ.country == code_to_idx[code]
        if mask.sum() < 10:
            continue
        X_rows.append(features[mask].mean(axis=0))
        y_rows.append(logit(np.array([target_pct]))[0] - baseline_logit)

    if len(X_rows) < 3:
        return np.zeros(n_feat)

    X = np.array(X_rows)
    y = np.array(y_rows)

    XtX = X.T @ X + ridge_alpha * np.eye(n_feat)
    Xty = X.T @ y
    return np.linalg.solve(XtX, Xty)


def predict_country(
    civ: Civilization,
    baseline: float,
    weights: np.ndarray,
    country_code: str,
    extended: bool = False,
) -> float | None:
    """Predict yes_pct for a specific country using given weights."""
    code_to_idx, _ = _get_country_index(civ)
    if country_code not in code_to_idx:
        return None
    mask = civ.country == code_to_idx[country_code]
    if mask.sum() == 0:
        return None
    features = _build_features(civ, extended=extended)
    baseline_logit = logit(np.array([baseline]))[0]
    s = sigmoid(baseline_logit + features[mask] @ weights)
    return float(s.mean())


def predict_countries(
    civ: Civilization,
    baseline: float,
    weights: np.ndarray,
    country_codes: list[str],
    extended: bool = False,
) -> dict[str, float]:
    """Predict yes_pct for multiple countries."""
    result = {}
    for code in country_codes:
        pred = predict_country(civ, baseline, weights, code, extended=extended)
        if pred is not None:
            result[code] = pred
    return result


def evaluate_weights(
    civ: Civilization,
    baseline: float,
    weights: np.ndarray,
    country_targets: dict[str, float],
    extended: bool = False,
) -> dict:
    """Evaluate how well weights predict country targets. Returns MAE and per-country errors."""
    preds = predict_countries(civ, baseline, weights, list(country_targets.keys()),
                              extended=extended)
    errors = {}
    for code, target in country_targets.items():
        if code in preds:
            errors[code] = {
                "predicted": round(preds[code], 4),
                "target": target,
                "error": round(abs(preds[code] - target), 4),
            }
    mae = float(np.mean([e["error"] for e in errors.values()])) if errors else None
    return {"mae": mae, "countries": errors, "n": len(errors)}


def calibrate_weights(
    civ: Civilization,
    targets: list[dict],
    ridge_alpha: float = 1.0,
) -> list[dict]:
    """Backward-compatible wrapper: learn weights per question from global targets.

    Uses per-country sub-populations when country_targets are available,
    otherwise falls back to global-only baseline fit.
    """
    from earth1.holdout import is_holdout

    centered = civ.forces - civ.means[np.newaxis, :]
    results = []

    for t in targets:
        if is_holdout(t["id"]):
            continue

        y_target = t["target_yes_pct"]
        baseline_logit = logit(np.array([y_target]))[0]

        ct = t.get("country_targets", {})
        if ct and len(ct) >= 3:
            w = calibrate_single(civ, y_target, ct, ridge_alpha=ridge_alpha)
        else:
            w = np.zeros(NUM_FORCES)

        pred = sigmoid(baseline_logit + centered @ w)
        actual_pct = float(pred.mean())

        results.append({
            "id": t["id"],
            "baseline": float(baseline_logit),
            "weights": w,
            "target_pct": y_target,
            "achieved_pct": actual_pct,
            "error": abs(actual_pct - y_target),
        })

    return results


def calibrate_single_aggregated(
    civ: Civilization,
    baseline: float,
    country_targets: dict,
    ridge_alpha: float = 0.1,
    extended: bool = True,
    max_iter: int = 60,
) -> np.ndarray:
    """Estimator B — fit w against the AGGREGATED prediction.

    Minimizes  sum_c ( mean_i sigmoid(bl + x_ci . w) - target_c )^2
               + ridge_alpha * ||w||^2
    by Gauss-Newton with the analytic jacobian through the aggregation.

    This is a RESTORATION, not an invention: the original TypeScript
    engine (_shared/sim_solver.ts, vaultik-x) fitted exactly this loss
    with backprop through mean-of-sigmoids. The numpy migration swapped
    it for closed-form ridge in logit space on mean features — fast,
    but objective != metric: Jensen compression toward 0.5 measured at
    0.44pp on the GOQA headline (external aggregation audit,
    2026-08-18). Warm-started from the production ridge solution.
    """
    code_to_idx, _ = _get_country_index(civ)
    features = _build_features(civ, extended=extended)
    bl = logit(np.array([baseline]))[0]
    groups, targets = [], []
    for code, t in country_targets.items():
        if code not in code_to_idx:
            continue
        mask = civ.country == code_to_idx[code]
        if mask.sum() < 10:
            continue
        groups.append(features[mask])
        targets.append(float(t))
    n_feat = features.shape[1]
    if len(targets) < 3:
        return np.zeros(n_feat)
    y = np.array(targets)
    w = calibrate_single(civ, baseline, country_targets,
                         ridge_alpha=ridge_alpha, extended=extended)
    lam = ridge_alpha
    for _ in range(max_iter):
        preds = np.empty(len(groups))
        J = np.empty((len(groups), n_feat))
        for i, X in enumerate(groups):
            s = sigmoid(bl + X @ w)
            preds[i] = s.mean()
            J[i] = ((s * (1.0 - s))[:, None] * X).mean(axis=0)
        r = y - preds
        A = J.T @ J + lam * np.eye(n_feat)
        g = J.T @ r - lam * w
        step = np.linalg.solve(A, g)
        w = w + step
        if float(np.linalg.norm(step)) < 1e-8:
            break
    return w
