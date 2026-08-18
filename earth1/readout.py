"""THE READOUT LAYER — shape, not just the mean.

Ported from the old TypeScript engine (vivid-node-forge), which had
the right readout on the wrong substrate while Earth-1 had the right
substrate with the wrong readout. Three functions:

1. counting_vote      — from compute_civilization_answer_v4: center
                        agent scores by the population-weighted mean,
                        then COUNT the fraction above zero. A count is
                        a discrete decision per agent; sigmoid().mean()
                        smears every agent into a fractional opinion
                        and produces a unimodal blob. Measured
                        2026-08-18: real within-cell densities are
                        bimodal (61.5% extreme mass) and the mean
                        readout produces 3.6%.

2. resultant_length   — from predict-with-coherence: the mean resultant
                        length of unit-normalized force vectors.
                        R ~ 1 the camp points one way (concentrated),
                        R ~ 0 scattered (maximal internal disagreement).
                        A genuine directional-statistics concentration
                        parameter, not a variance proxy.

3. camp_diagnostic    — from b_camp_cosine: do the yes-camp and no-camp
                        have DIFFERENT force signatures? If the cosine
                        is near 1 the manifold is empty on this topic
                        and the population is decoration; say so
                        instead of pretending. Returns the regime:
                        'manifold_native' | 'grounding_dependent'.

Also included: born_probability, the amplitude-squared readout
P = R_yes^2 / (R_yes^2 + R_no^2), which scored better than every
unblurred readout in the 2026-08-18 distributional test.
"""
from __future__ import annotations

import numpy as np

# thresholds carried over from the old engine's classification
CAMP_COSINE_DEPENDENT = 0.95    # above this: camps are indistinguishable
CAMP_COSINE_NATIVE = 0.85       # below this: camps genuinely differ


def counting_vote(scores: np.ndarray, weights: np.ndarray | None = None,
                  center: bool = True) -> float:
    """Fraction of agents whose (centered) score is above zero."""
    s = np.asarray(scores, dtype=np.float64)
    if center:
        mu = float(np.average(s, weights=weights)) if weights is not None \
            else float(s.mean())
        s = s - mu
    if weights is None:
        return float((s > 0).mean())
    return float(np.average((s > 0).astype(np.float64), weights=weights))


def resultant_length(forces: np.ndarray) -> float:
    """Mean resultant length of unit-normalized force vectors (0..1)."""
    F = np.asarray(forces, dtype=np.float64)
    if F.size == 0:
        return 0.0
    n = np.linalg.norm(F, axis=1, keepdims=True)
    U = F / np.maximum(n, 1e-12)
    return float(np.linalg.norm(U.mean(axis=0)))


def born_probability(forces: np.ndarray, stances: np.ndarray,
                     split: float = 0.5) -> float:
    """P(yes) = R_yes^2 / (R_yes^2 + R_no^2) — coherence, not headcount.

    Cannot be won by blurring: collapsing spread drives both camps' R
    toward the same value and the answer toward 0.5.
    """
    yes = np.asarray(stances) >= split
    no = ~yes
    if yes.sum() < 3 or no.sum() < 3:
        return float(np.mean(stances))
    r_y = resultant_length(forces[yes])
    r_n = resultant_length(forces[no])
    d = r_y ** 2 + r_n ** 2
    return float(r_y ** 2 / d) if d > 1e-12 else 0.5


def camp_diagnostic(forces: np.ndarray, stances: np.ndarray,
                    split: float = 0.5) -> dict:
    """Is the population contributing, or decorating?

    Returns cosine between camp mean force signatures, the two camps'
    concentrations, and a regime label. The old engine ABSTAINED on
    'grounding_dependent' rather than pretending the manifold spoke.
    """
    yes = np.asarray(stances) >= split
    no = ~yes
    if yes.sum() < 3 or no.sum() < 3:
        return {"cosine": 1.0, "regime": "degenerate",
                "r_yes": 0.0, "r_no": 0.0, "n_yes": int(yes.sum()),
                "n_no": int(no.sum())}
    my = forces[yes].mean(axis=0)
    mn = forces[no].mean(axis=0)
    cos = float(my @ mn / max(np.linalg.norm(my) * np.linalg.norm(mn), 1e-12))
    regime = ("grounding_dependent" if cos >= CAMP_COSINE_DEPENDENT
              else "manifold_native" if cos < CAMP_COSINE_NATIVE
              else "mixed")
    return {"cosine": cos, "regime": regime,
            "r_yes": resultant_length(forces[yes]),
            "r_no": resultant_length(forces[no]),
            "n_yes": int(yes.sum()), "n_no": int(no.sum())}
