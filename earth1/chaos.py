"""CHAOS — the estimators, and a compatibility wrapper over THE loop.

THERE IS ONE DEFINITION OF A CIVILIZATION DAY: `alive.live_one_day`.

Until 0.2 this module carried a second simulator — `world_step` ran
matter, influence, conviction, cascade and feedback over a bare
(civ, life) pair, omitting NINE live subsystems (health, institutions,
weather, flourishing, contagion, mobility, feed, memory, births), with
its own copy of the cascade block and its own divergent constants
(beta 1.0 vs the world's 2.0; residue 0.01 vs 0.02;
critical_fraction 0.15 vs 0.12). Every chaos, FSLE, butterfly and
consciousness number ever published was measured on that reduced
system — which is why they all carry the R2 caveat and are re-measured
from scratch in 0.8.

`world_step` is now ONLY a wrapper: it takes a World and delegates to
`live_one_day` with the canonical configuration. It cannot drift,
because it has no physics of its own to drift with. The estimators
below (entropy, Rosenstein fit, Benettin renormalization) are pure
instrument mathematics and are unchanged.

DO NOT compare post-0.2 chaos numbers with pre-0.2 ones: this change
replaces the measuring instrument itself. 0.8 re-runs everything.
"""
from __future__ import annotations

import numpy as np


def world_step(w, rng, **step_kw) -> dict:
    """One civilization day — the canonical one. Compatibility wrapper.

    Takes a World (the old (civ, life) form is gone WITH the reduced
    physics: there is no way to step a civilization that does not
    exist). Defaults come from `alive.CANONICAL_DAY`; explicit
    overrides are for registered experiments (e.g. the 0.8 sweeps),
    never a second standing configuration.
    """
    from earth1.alive import live_one_day
    return live_one_day(w, rng, **step_kw)


def entropy(forces: np.ndarray, bins: int = 50) -> float:
    """Mean Shannon entropy across force channels."""
    tot = 0.0
    for k in range(forces.shape[1]):
        h, _ = np.histogram(forces[:, k], bins=bins, range=(0, 1))
        p = h / max(h.sum(), 1)
        p = p[p > 0]
        tot += float(-(p * np.log(p)).sum())
    return tot / forces.shape[1]


def lyapunov_from(series) -> float:
    """Largest Lyapunov exponent from a divergence curve.

    Fitted on the INITIAL LINEAR REGION of log-divergence, which is the
    standard construction (Rosenstein et al. 1993). Fitting the whole
    pre-peak window instead mixes the exponential phase with the
    saturation ramp and systematically underestimates the exponent —
    and does so worse the larger the population, because a bigger world
    takes longer to saturate. That is a property of the estimator, not
    of the dynamics, and it has to be excluded rather than tolerated.

    The growth region is taken between 5% and 60% of the total
    log-divergence range, which is inside the exponential phase and
    clear of both the noise floor and the plateau.
    """
    y = np.asarray(series, dtype=float)
    y = y[y > 0]
    if y.size < 8:
        return 0.0
    ly = np.log(y)
    lo, hi = ly.min(), ly.max()
    if not np.isfinite(lo) or hi - lo < 1e-9:
        return 0.0
    band = (ly >= lo + 0.05 * (hi - lo)) & (ly <= lo + 0.60 * (hi - lo))
    idx = np.flatnonzero(band)
    if idx.size < 5:
        idx = np.arange(min(len(ly), max(8, len(ly) // 4)))
    # keep the contiguous run starting at the earliest qualifying point
    start = int(idx[0])
    end = int(idx[-1]) + 1
    seg, t = ly[start:end], np.arange(end - start)
    if seg.size < 5:
        return 0.0
    return float(np.polyfit(t, seg, 1)[0])


def _state(w) -> np.ndarray:
    """The continuous state coordinates the exponent is measured on."""
    civ, life = w.civ, w.life
    return np.concatenate([civ.forces.ravel(), civ.alpha, life.wealth,
                           civ.openness, civ.doubt, civ.desire_intensity])


def _sync(w_a, w_b) -> None:
    civ_a, life_a, civ_b, life_b = w_a.civ, w_a.life, w_b.civ, w_b.life
    civ_b.forces = civ_a.forces.copy()
    civ_b.alpha = civ_a.alpha.copy()
    civ_b.openness = civ_a.openness.copy()
    civ_b.doubt = civ_a.doubt.copy()
    civ_b.desire_intensity = civ_a.desire_intensity.copy()
    life_b.wealth = life_a.wealth.copy()


def _renorm(w_a, w_b, diff, scale) -> None:
    """Pull B back to distance d0 from A along the same direction."""
    civ_a, life_a, civ_b, life_b = w_a.civ, w_a.life, w_b.civ, w_b.life
    n, k = civ_a.n, civ_a.forces.shape[1]
    d = diff * scale
    o = 0
    civ_b.forces = civ_a.forces + d[o:o + n * k].reshape(n, k); o += n * k
    civ_b.alpha = civ_a.alpha + d[o:o + n]; o += n
    life_b.wealth = life_a.wealth + d[o:o + n]; o += n
    civ_b.openness = civ_a.openness + d[o:o + n]; o += n
    civ_b.doubt = civ_a.doubt + d[o:o + n]; o += n
    civ_b.desire_intensity = civ_a.desire_intensity + d[o:o + n]


def lyapunov_benettin(w_a, w_b, rng_a, rng_b, *,
                      steps: int = 240, renorm_every: int = 5,
                      d0: float = 1e-6, **step_kw) -> dict:
    """Largest Lyapunov exponent by the Benettin algorithm.

    The naive approach — perturb once, fit a line to log divergence — is
    only valid while separation grows freely. On a BOUNDED attractor,
    which is what a real society is, separation saturates against the
    size of the state space and the fit then measures the saturation
    rather than the dynamics. Every long-run estimate is dragged toward
    zero for a reason that has nothing to do with whether the system is
    chaotic.

    Benettin (1980) is the standard fix and is what is used here: let
    the two trajectories separate for a short interval, measure the
    growth over that interval alone, then RENORMALIZE the second
    trajectory back to distance d0 along the same direction and repeat.
    The exponent is the mean log growth per unit time, and it stays
    valid on a bounded attractor because separation is never allowed to
    saturate.

    lambda > 0 means nearby histories diverge exponentially: the world
    is chaotic, and no amount of measurement of the present pins down
    the future.
    """
    logs = []
    _sync(w_a, w_b)
    # Seed the perturbation in WEALTH, not in force. A force-only
    # perturbation is damped straight back out by the restoring term,
    # because two worlds with identical material state have identical
    # force targets: measuring there gives exactly log(1 - relax) and
    # says nothing about the attractor. The exponent is defined on the
    # FULL state space, and in this system the material coordinates are
    # the ones that carry memory forward.
    w_b.life.wealth[w_a.civ.n // 2] += d0

    for i in range(steps):
        world_step(w_a, rng_a, **step_kw)
        world_step(w_b, rng_b, **step_kw)
        if (i + 1) % renorm_every == 0:
            diff = _state(w_b) - _state(w_a)
            d = float(np.linalg.norm(diff))
            if d <= 0 or not np.isfinite(d):
                continue
            logs.append(np.log(d / d0))
            _renorm(w_a, w_b, diff, d0 / d)
    if not logs:
        return {"lyapunov": 0.0, "intervals": 0}
    lam = float(np.mean(logs) / renorm_every)
    return {"lyapunov": lam, "intervals": len(logs),
            "per_interval_mean": float(np.mean(logs)),
            "per_interval_std": float(np.std(logs))}
