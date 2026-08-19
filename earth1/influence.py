"""INFLUENCE — the conviction-conditioned kernel. The amplifying channel.

Construction error #2, named by Pietro: "an averaging kernel that can
only contract distributions. Mathematically proven by sweep — no
parameter setting can manufacture extremes."

He is right, and the proof is trivial once stated: if every agent moves
toward the mean of its neighbours, the variance of the population is a
non-increasing function of time. An averaging operator is a contraction.
No amount of tuning makes a contraction expand. That is why the world
absorbed a perturbation and reconverged, and why the tails were empty.

THE FIX — people do not average, they ALIGN.

When someone who is certain talks to someone who is unsure, the unsure
person does not move to the midpoint. They move toward the certain
person's SIDE. Conviction is what converts a conversation into a
recruitment. That single change turns the operator from a contraction
into an expansion, because agents above the midline are pulled to 1 and
agents below it are pulled to 0.

    alignment = conviction ** beta
    target moves toward the source's POLE     with weight alignment
    target moves toward the source's VALUE    with weight 1 - alignment

beta = 0 recovers the old averaging law exactly, so the old behaviour is
a special case rather than something deleted. beta > 0 opens the
polarizing channel. This is the parameter that decides whether the world
is chaotic, and it is measured rather than assumed — see earth1/chaos.py.

CONVICTION IS ALSO EARNED. An agent whose neighbours agree with it grows
more certain; an agent surrounded by disagreement grows less so. That is
the second amplifier, and it is what makes clusters harden into camps
instead of relaxing back into the mean.
"""
from __future__ import annotations

import numpy as np

BETA = 1.0            # conviction exponent; 0 = pure averaging (legacy)
ETA = 0.18            # propagation rate per layer
CONVICTION_GAIN = 0.06    # how fast agreement hardens conviction
CONVICTION_DECAY = 0.02   # 0.8 A/B arm-B value ONLY - decay is DISABLED in production


def propagate(forces: np.ndarray, alpha: np.ndarray, adj,
              beta: float = BETA, eta: float = ETA,
              layers: int = 1,
              susceptibility: np.ndarray | None = None) -> np.ndarray:
    """One or more layers of conviction-conditioned force propagation.

    forces (N, K), alpha (N,) conviction in [0, 1], adj sparse (N, N).
    Returns the NEW forces; does not mutate the input.

    Vectorized entirely through sparse matmul — every agent talks to
    every neighbour simultaneously, which is what makes this affordable
    at population scale.
    """
    f = forces.copy()
    deg = np.asarray(adj.sum(axis=1)).ravel()
    safe_deg = np.maximum(deg, 1.0)
    a = np.clip(alpha, 0.0, 1.0) ** beta        # alignment weight
    inv_a = 1.0 - a

    for _ in range(max(1, layers)):
        # each neighbour's POLE: which side of the midline they are on.
        # this is the term that expands — a source at 0.61 does not pull
        # you to 0.61, it pulls you toward 1.0
        pole = (f > 0.5).astype(np.float64)

        # weighted sums over neighbours, all at once
        align_num = adj @ (a[:, None] * pole)      # (N, K)
        align_den = np.asarray(adj @ a).ravel()    # (N,)
        avg_num = adj @ (inv_a[:, None] * f)       # (N, K)
        avg_den = np.asarray(adj @ inv_a).ravel()  # (N,)

        pull_pole = align_num - f * align_den[:, None]
        pull_mean = avg_num - f * avg_den[:, None]

        move = eta * (pull_pole + pull_mean) / safe_deg[:, None]
        # SUSCEPTIBILITY: the same push does not move two people the
        # same distance. This is where mental health, addiction, age,
        # conviction and hunger decide who is movable — see
        # earth1/susceptibility.py.
        if susceptibility is not None:
            move = move * susceptibility
        f = np.clip(f + move, 0.0, 1.0)
    return f


def update_conviction(forces: np.ndarray, alpha: np.ndarray, adj,
                      gain: float = CONVICTION_GAIN,
                      _experimental_decay_0_8_ab: float = 0.0) -> np.ndarray:
    """Agreement hardens conviction; disagreement softens it.

    The second amplifier. Without it, clusters form and then relax. With
    it, a cluster that agrees becomes a cluster that is CERTAIN, which
    by the kernel above makes it better at recruiting — and that loop is
    what produces cascades that do not simply decay.

    ISOLATION DECAY IS DISABLED. The original code carried a
    `- decay * 0.0` no-op while the docstring claimed isolation softens
    conviction — implementation and documentation disagreed, and alpha
    has been a ratchet for the world's entire history. Making the term
    real changes the conviction kernel, propagation, polarization and
    possibly the chaotic regime — that is physics, not a bug fix, so
    it is adjudicated by the registered 0.8 A/B (arm A: disabled, as
    here; arm B: `_experimental_decay_0_8_ab=CONVICTION_DECAY`), never
    switched on silently. Production output is bit-identical to the
    pre-0.1 code.
    """
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    pole = (forces > 0.5).astype(np.float64)
    # fraction of neighbours sharing this agent's side, averaged over
    # every force channel
    nb_pole = (adj @ pole) / deg[:, None]
    agreement = 1.0 - np.abs(nb_pole - pole).mean(axis=1)   # (N,) in [0,1]
    out = alpha + gain * (agreement - 0.5) * 2.0
    if _experimental_decay_0_8_ab:
        # THE REGISTERED 0.8 A/B ARM — never taken in production. The
        # isolation channel softens conviction for the unconnected.
        isolation = 1.0 / (1.0 + deg)
        out = out - _experimental_decay_0_8_ab * isolation
    return np.clip(out, 0.02, 1.0)
