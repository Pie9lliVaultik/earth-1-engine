"""CHAOS — the full world step, and the instrument that grades it.

The butterfly test previously ran only the material tick: no force
propagation, no cascades, no feedback. There was no amplifying channel
because none was being run. This module runs the WHOLE loop, which is
the thing that was supposed to be chaotic in the first place:

    1. MATTER      jobs, firms, money, needs                 life.py
    2. INFLUENCE   conviction-conditioned propagation        influence.py
    3. CONVICTION  agreement hardens, isolation softens      influence.py
    4. CASCADE     local thresholds fire, events kick        thresholds.py
    5. FEEDBACK    absorbed force leaves a trait residue     here

Each of the five couples into the next, and step 5 closes the ring back
onto step 1. A closed nonlinear ring with a polarizing operator inside
it is the standard recipe for chaos; the Lyapunov exponent below says
whether this particular one qualifies.
"""
from __future__ import annotations

import numpy as np

from earth1.influence import propagate, update_conviction
from earth1.life import life_tick
from earth1.types import Force

# Feedback rate — construction error #3. It was 0.0005 per layer, which
# is numerically invisible over any horizon a person cares about. This
# is the fitted replacement; chaos is measured across a sweep of it.
RESIDUE_RATE = 0.01

# How hard an agent's actual circumstances pull their force state back
# toward what those circumstances imply. This is the restoring term in a
# forced nonlinear oscillator: the polarizing kernel pushes agents to
# the poles, material life pulls them back to where their life puts
# them, and thresholds kick the whole thing. Push alone saturates and
# freezes; pull alone is a spreadsheet. The tension is the dynamics.
RELAX = 0.25

# Critical mass for a local cascade. Pietro's spec puts it at 0.15,
# below the 0.25 committed-minority anchor, because a cascade should be
# able to START before it has already won.
CRITICAL_FRACTION = 0.15


def world_step(civ, life, rng, *, beta: float = 1.0,
               residue: float = RESIDUE_RATE,
               critical_fraction: float = CRITICAL_FRACTION,
               relax: float = RELAX,
               layers: int = 2, dt_days: float = 1.0) -> dict:
    """One full day of a living world. Every channel, in order."""
    from earth1.life import life_force_target
    from earth1.thresholds import TRANSITION_RULES, _participation

    stats = life_tick(civ, life, rng, dt_days=dt_days, couple_forces=False)
    target = life_force_target(civ, life)

    # ── influence: the polarizing kernel (the PUSH) ──────────────────
    civ.forces = propagate(civ.forces, civ.alpha, civ.adj,
                           beta=beta, layers=layers)
    # ── circumstance: the restoring pull toward the life actually led ─
    civ.forces = np.clip(civ.forces + relax * (target - civ.forces), 0.0, 1.0)
    civ.alpha = update_conviction(civ.forces, civ.alpha, civ.adj)

    # ── cascade: local thresholds fire and KICK the population ───────
    fired = 0
    for rule in TRANSITION_RULES:
        if rule.region_scope != "regional":
            continue
        for ci in np.unique(civ.country):
            m = civ.country == ci
            if m.sum() < 10:
                continue
            if _participation(civ, m, rule) >= critical_fraction:
                fired += 1
                for fname, delta in rule.effects.items():
                    k = getattr(Force, fname.upper(), None)
                    if k is not None:
                        civ.forces[m, k] = np.clip(
                            civ.forces[m, k] + delta, 0.0, 1.0)

    # ── feedback: absorbed force leaves a mark on the person ─────────
    # Traits are what an agent brings to the next question, so a world
    # where force never touches trait is a world with no memory.
    dev = civ.forces - civ.forces.mean(axis=0, keepdims=True)
    civ.openness = np.clip(
        civ.openness + residue * dev[:, Force.CULTURE], 0.0, 1.0)
    civ.doubt = np.clip(
        civ.doubt + residue * dev[:, Force.FEAR], 0.0, 1.0)
    civ.desire_intensity = np.clip(
        civ.desire_intensity + residue * dev[:, Force.DESIRE], 0.0, 1.0)

    stats["cascades_fired"] = fired
    return stats


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


def _state(civ, life) -> np.ndarray:
    """The continuous state coordinates the exponent is measured on."""
    return np.concatenate([civ.forces.ravel(), civ.alpha, life.wealth,
                           civ.openness, civ.doubt, civ.desire_intensity])


def _sync(civ_a, life_a, civ_b, life_b) -> None:
    civ_b.forces = civ_a.forces.copy()
    civ_b.alpha = civ_a.alpha.copy()
    civ_b.openness = civ_a.openness.copy()
    civ_b.doubt = civ_a.doubt.copy()
    civ_b.desire_intensity = civ_a.desire_intensity.copy()
    life_b.wealth = life_a.wealth.copy()


def _renorm(civ_a, life_a, civ_b, life_b, diff, scale) -> None:
    """Pull B back to distance d0 from A along the same direction."""
    n, k = civ_a.n, civ_a.forces.shape[1]
    d = diff * scale
    o = 0
    civ_b.forces = civ_a.forces + d[o:o + n * k].reshape(n, k); o += n * k
    civ_b.alpha = civ_a.alpha + d[o:o + n]; o += n
    life_b.wealth = life_a.wealth + d[o:o + n]; o += n
    civ_b.openness = civ_a.openness + d[o:o + n]; o += n
    civ_b.doubt = civ_a.doubt + d[o:o + n]; o += n
    civ_b.desire_intensity = civ_a.desire_intensity + d[o:o + n]


def lyapunov_benettin(civ_a, life_a, civ_b, life_b, rng_a, rng_b, *,
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
    _sync(civ_a, life_a, civ_b, life_b)
    # Seed the perturbation in WEALTH, not in force. A force-only
    # perturbation is damped straight back out by the restoring term,
    # because two worlds with identical material state have identical
    # force targets: measuring there gives exactly log(1 - relax) and
    # says nothing about the attractor. The exponent is defined on the
    # FULL state space, and in this system the material coordinates are
    # the ones that carry memory forward.
    life_b.wealth[civ_a.n // 2] += d0

    for i in range(steps):
        world_step(civ_a, life_a, rng_a, **step_kw)
        world_step(civ_b, life_b, rng_b, **step_kw)
        if (i + 1) % renorm_every == 0:
            diff = _state(civ_b, life_b) - _state(civ_a, life_a)
            d = float(np.linalg.norm(diff))
            if d <= 0 or not np.isfinite(d):
                continue
            logs.append(np.log(d / d0))
            _renorm(civ_a, life_a, civ_b, life_b, diff, d0 / d)
    if not logs:
        return {"lyapunov": 0.0, "intervals": 0}
    lam = float(np.mean(logs) / renorm_every)
    return {"lyapunov": lam, "intervals": len(logs),
            "per_interval_mean": float(np.mean(logs)),
            "per_interval_std": float(np.std(logs))}
