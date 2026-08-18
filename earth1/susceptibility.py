"""SUSCEPTIBILITY — how much a force MOVES you, which is not how much you have.

This is in Pietro's Layer 1 spec and was silently skipped in the build:

    civ.susceptibility[:, Force.FEAR] *= (1.0 + 0.5 * (1.0 - mental))
    civ.susceptibility[:, Force.IDENTITY] *= (0.5 + 0.5 * mental)

Mental health was coupled to force LEVELS instead, and that is a
different claim. A level says how frightened you are. A susceptibility
says how much the next frightening thing will move you. Two people can
carry identical fear and respond to a bomb completely differently, and
the difference between them is this array.

It is the natural home for everything that makes a person more or less
movable:

  MENTAL HEALTH  low mental health raises fear susceptibility and
                 lowers identity susceptibility — a person in distress
                 is easier to frighten and harder to reach with an
                 appeal to who they are
  ADDICTION      LOCKS the desire channel. An addicted agent stops
                 responding to collective pressure, which is the
                 clinical picture and a real dynamical consequence
  AGE            the young move, the old hold. Attitude stability rises
                 sharply through the twenties and then plateaus, which
                 is one of the most robust findings in political
                 socialisation
  CONVICTION     the certain are hard to move by construction
  HUNGER         a body in want is movable on fear and immovable on
                 anything abstract

Susceptibility is why the same event produces revolution in one
population and a shrug in another that carries identical force levels.
"""
from __future__ import annotations

import numpy as np

from earth1.types import Force, NUM_FORCES


def compute(civ, life=None, flourishing=None) -> np.ndarray:
    """Per-agent, per-channel gain on incoming force. Shape (N, 8)."""
    n = civ.n
    s = np.ones((n, NUM_FORCES))

    # the young move, the old hold
    plasticity = np.clip(1.35 - 0.7 * civ.age, 0.45, 1.4)
    s *= plasticity[:, None]

    # the certain are hard to move
    s *= (1.25 - 0.5 * np.clip(civ.alpha, 0, 1))[:, None]

    if life is not None and life.mental is not None:
        m = np.clip(life.mental, 0, 1)
        # distress: easier to frighten, harder to reach through identity
        s[:, Force.FEAR] *= (1.0 + 0.6 * (1.0 - m))
        s[:, Force.IDENTITY] *= (0.5 + 0.5 * m)
        s[:, Force.CULTURE] *= (0.6 + 0.4 * m)
        # addiction LOCKS desire and deafens the agent to the group
        a = np.clip(life.addiction, 0, 1)
        s[:, Force.DESIRE] *= (1.0 - 0.75 * a)
        s[:, Force.COLLECTIVE] *= (1.0 - 0.6 * a)
        # isolation makes identity the loudest channel a person has
        if life.social_need is not None:
            s[:, Force.IDENTITY] *= (1.0 + 0.5 * life.social_need)

    if flourishing is not None:
        need = np.clip(0.6 * flourishing.hunger + 0.4 * flourishing.thirst,
                       0, 1)
        # a body in want hears fear and nothing abstract
        s[:, Force.FEAR] *= (1.0 + 0.8 * need)
        s[:, Force.CULTURE] *= (1.0 - 0.6 * need)
        s[:, Force.EXPERIENCE] *= (1.0 - 0.5 * need)
        # hope opens a person to everything
        s *= (0.85 + 0.3 * np.clip(flourishing.hope, 0, 1))[:, None]

    return np.clip(s, 0.05, 3.0)
