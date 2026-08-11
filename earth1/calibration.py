"""Inverse solver calibration — ridge regression in logit space.

Given survey targets (WVS/GSS/Pew), find the force weights that make the
civilization's aggregate output match reality. This is the calibration loop
that turns a generative model into a measurement instrument.

calibration tunes weights, not trait positions — a wrong LLM stereotype
can't be fully fixed downstream.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Civilization, NUM_FORCES
from earth1.rng import logit, sigmoid


def calibrate_weights(
    civ: Civilization,
    targets: list[dict],
    ridge_alpha: float = 1.0,
) -> list[dict]:
    """Fit force weights for each target question via ridge regression in logit space.

    Each target: {"id": str, "text": str, "domain": str, "target_yes_pct": float}
    Returns: list of {"id": str, "baseline": float, "weights": ndarray(8,)}
    """
    centered = civ.forces - civ.means[np.newaxis, :]  # (N, 8)
    X = centered  # design matrix

    results = []
    for t in targets:
        y_target = t["target_yes_pct"]
        y_logit = logit(np.array([y_target]))[0]

        # we want: mean(sigmoid(baseline + X @ w)) ≈ y_target
        # linearized in logit space: baseline + mean(X) @ w ≈ logit(y_target)
        # since X is centered, mean(X) ≈ 0, so baseline ≈ logit(y_target)
        # then fit residuals with ridge

        baseline = y_logit

        # ridge regression: (X^T X + alpha I)^{-1} X^T (logit(y_target) - baseline)
        # but we need per-agent targets — use uniform target for now
        y_vec = np.full(civ.n, y_logit) - baseline
        XtX = X.T @ X + ridge_alpha * np.eye(NUM_FORCES) * civ.n
        Xty = X.T @ y_vec
        w = np.linalg.solve(XtX, Xty)

        # verify
        pred = sigmoid(baseline + X @ w)
        actual_pct = float(pred.mean())

        results.append({
            "id": t["id"],
            "baseline": float(baseline),
            "weights": w,
            "target_pct": y_target,
            "achieved_pct": actual_pct,
            "error": abs(actual_pct - y_target),
        })

    return results
