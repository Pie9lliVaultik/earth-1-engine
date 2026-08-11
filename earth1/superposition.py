"""Born-rule superposition readout.

Replace sigmoid with: P(yes) = |<yes|psi>|^2 / (|<yes|psi>|^2 + |<no|psi>|^2)

Sequential measurement gives interference/order effects — the commercially
decisive differentiator from classical polling. If this doesn't beat classical
on human order-effect data, it's cosine with a fancy name.
"""
from __future__ import annotations
import numpy as np
from earth1.types import Civilization, Question, NUM_FORCES


def born_readout(civ: Civilization, q: Question) -> np.ndarray:
    """Born-rule stance for all agents. Returns (N,) in [0, 1]."""
    centered = civ.forces - civ.means[np.newaxis, :]
    z = q.baseline + centered @ q.weights

    # amplitude model: yes-amplitude proportional to exp(z/2), no to exp(-z/2)
    amp_yes_sq = np.exp(np.clip(z, -500, 500))
    amp_no_sq = np.exp(np.clip(-z, -500, 500))
    p_yes = amp_yes_sq / (amp_yes_sq + amp_no_sq)
    return p_yes


def sequential_measurement(
    civ: Civilization,
    q1: Question,
    q2: Question,
) -> dict:
    """Measure q1 then q2 — order effects emerge from the projection.

    Returns both orderings so the difference reveals interference.
    """
    # q1 first, then q2
    p1 = born_readout(civ, q1)
    # after measuring q1, the "state" is updated — agents who said yes to q1
    # have their force field shifted slightly toward q1's weight direction
    shift_magnitude = 0.05
    shift = q1.weights * shift_magnitude
    # q2 conditioned on q1 measurement
    centered_shifted = (civ.forces - civ.means[np.newaxis, :]) + shift[np.newaxis, :] * (p1[:, np.newaxis] - 0.5)
    z2_given_1 = q2.baseline + centered_shifted @ q2.weights
    amp_y2 = np.exp(np.clip(z2_given_1, -500, 500))
    amp_n2 = np.exp(np.clip(-z2_given_1, -500, 500))
    p2_given_1 = amp_y2 / (amp_y2 + amp_n2)

    # reverse order: q2 first, then q1
    p2_first = born_readout(civ, q2)
    shift2 = q2.weights * shift_magnitude
    centered_shifted2 = (civ.forces - civ.means[np.newaxis, :]) + shift2[np.newaxis, :] * (p2_first[:, np.newaxis] - 0.5)
    z1_given_2 = q1.baseline + centered_shifted2 @ q1.weights
    amp_y1 = np.exp(np.clip(z1_given_2, -500, 500))
    amp_n1 = np.exp(np.clip(-z1_given_2, -500, 500))
    p1_given_2 = amp_y1 / (amp_y1 + amp_n1)

    return {
        "q1_then_q2": {
            "q1_yes": float(p1.mean()),
            "q2_yes_given_q1": float(p2_given_1.mean()),
        },
        "q2_then_q1": {
            "q2_yes": float(p2_first.mean()),
            "q1_yes_given_q2": float(p1_given_2.mean()),
        },
        "order_effect_q2": float(p2_given_1.mean() - p2_first.mean()),
        "order_effect_q1": float(p1_given_2.mean() - p1.mean()),
    }
