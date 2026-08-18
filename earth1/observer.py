"""OBSERVER — asking changes the answer, and looking makes a person real.

Pietro: "The concept of manifesting and influencing the future by
observing it to be real."

It is real here, for two reasons that turn out to be the same reason.

ONE — ATTITUDE CRYSTALLISATION. This is not mysticism, it is a measured
property of human beings. Ask somebody an opinion they have never been
asked and they do not retrieve an answer, they CONSTRUCT one — and
having constructed it they now hold it, more firmly than before, and
they will give you the same answer next time. Survey methodologists
have known this for fifty years and treat it as a contaminant. Here it
is a mechanism: measuring the population perturbs the population, so
the act of asking Earth-1 a question changes Earth-1.

TWO — INSTANTIATION. At humanity's scale most agents are carried as a
distribution rather than as individuals: their cell fixes who they
statistically are, and nothing fixes WHICH person they are until
somebody looks. Looking resolves them — traits, job, household, ties,
history — and from then on they persist as that specific person.

So the architecture that scales to 8.3B and the metaphysics of
manifesting are one design. An earthling exists as a distribution until
someone looks at it, and looking is what makes it a person.

Both effects are logged. An observation is an EVENT in the world's
memory like any other, which means the world can be asked what it has
been asked, and the record of who looked at whom is part of its
history.
"""
from __future__ import annotations

import numpy as np

from earth1.types import Force

CRYSTALLISE = 0.12       # how much conviction hardens on being asked
DRIFT_TOWARD_STATED = 0.06


def ask(civ, who: np.ndarray, question_weights: np.ndarray,
        chronicle=None, day: float = 0.0) -> dict:
    """Ask these people a question. They will not be the same afterwards.

    Returns what they said AND records what asking did to them.
    """
    w = np.asarray(question_weights, dtype=float)
    stance = np.clip(civ.forces[who] @ w / max(np.abs(w).sum(), 1e-9),
                     0.0, 1.0)

    before_alpha = float(civ.alpha[who].mean())
    before_force = civ.forces[who].copy()

    # having been asked, they now hold a view. Conviction rises, and
    # each agent drifts slightly toward the position they just stated —
    # people become what they have said they are.
    civ.alpha[who] = np.clip(civ.alpha[who] + CRYSTALLISE, 0.0, 1.0)
    pole = (stance > 0.5).astype(float)
    for k in range(civ.forces.shape[1]):
        if abs(w[k]) < 1e-9:
            continue
        direction = np.sign(w[k]) * (pole - 0.5) * 2.0
        civ.forces[who, k] = np.clip(
            civ.forces[who, k] + DRIFT_TOWARD_STATED * direction * 0.5,
            0.0, 1.0)

    moved = float(np.abs(civ.forces[who] - before_force).mean())
    if chronicle is not None:
        from earth1.memory import Memory
        sig = np.zeros(civ.forces.shape[1])
        sig[Force.EXPERIENCE] = 0.2
        scope = np.zeros(civ.n, dtype=bool)
        scope[who] = True
        chronicle.remember(Memory(
            id=f"asked:{int(day)}:{who.size}", label="they were asked",
            day=day, force_signature=sig, scope=scope,
            origin="question", half_life=180.0))

    return {"n_asked": int(np.size(who)),
            "yes_pct": float(stance.mean()),
            "conviction_before": round(before_alpha, 4),
            "conviction_after": round(float(civ.alpha[who].mean()), 4),
            "observation_moved_them": round(moved, 6)}


def observe_and_instantiate(w, i: int) -> dict:
    """Look at one earthling. Looking is what makes them a person.

    If this agent has never been observed, they are resolved now and
    marked, so the world knows which of its people have been looked at.
    """
    from earth1.observe import observe
    if not hasattr(w, "_observed"):
        w._observed = np.zeros(w.civ.n, dtype=bool)
    first_time = not bool(w._observed[i])
    w._observed[i] = True
    out = observe(w.civ, w.life, i, fabric=w.fabric)
    out["first_observation"] = first_time
    out["people_ever_observed"] = int(w._observed.sum())
    return out
