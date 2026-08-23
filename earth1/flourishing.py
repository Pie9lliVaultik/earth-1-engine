"""FLOURISHING — the body's demands, and the reasons to keep going.

Pietro, 2026-08-18: "How do scientific discoveries give them hope and
curiosity and excitement as well as art and food and family? Do they
feel hunger? Do they need to drink?"

He is pointing at a real hole. Everything built so far is harm — fear,
deprivation, crime, illness, war, homelessness. A population modelled
only by what damages it is not a population, it is a casualty list. The
other half is what this module is.

THE BODY MAKES DEMANDS, and they are not the same demand.

  HUNGER   builds over days. It is the slowest and the most political:
           you can be hungry for a long time and stay alive, which is
           exactly why hunger produces unrest rather than only death.
  THIRST   builds over HOURS and kills in days. It is not a slower
           hunger, it is a different clock, and drought reaches a person
           through it before it reaches them through food.
  BREATH   is the demand nobody notices until it is denied. Air quality
           and altitude tax the body continuously, and the tax is
           invisible to the person paying it — which is precisely why
           it is worth modelling. Nobody appreciates oxygen. They are
           simply diminished without it.

A body under any of these is a body that cannot think about anything
else. Unmet need CROWDS OUT everything above it: learning stops,
creation stops, curiosity closes, the horizon shrinks to the next meal.
That is the coupling, and it is why hunger belongs in a model of
opinion.

AND THEN THE REASONS.

  HOPE        that tomorrow can be better than today. Fed by
              discovery, by a society that is learning, by welfare that
              arrives, by a job found. Hope is what makes a person
              willing to bear the present.
  CURIOSITY   the appetite for what you do not yet know. Fed by
              discovery and by being near people who know things.
              Killed by exhaustion and by fear.
  MEANING     that your life refers to something beyond itself. Fed by
              art — made or received — and by belief, and by work worth
              doing.
  BELONGING   that there are people who are yours. Fed by family, by a
              household, by ties that hold.
  SATISFACTION the plain animal contentment of a full stomach, a warm
              room, a body that does not hurt.

These are not decoration on top of the misery. They are load-bearing:
an agent with hope tolerates hardship that breaks an agent without it,
and that difference changes what a population does when it is squeezed.
A world with only suffering in it predicts revolution everywhere. The
real one does not, because people have reasons to hold on.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Force

# how fast each demand builds with nothing coming in
HUNGER_PER_DAY = 0.16          # days, not hours — hunger is slow
THIRST_PER_DAY = 0.85          # thirst is fast and it kills fast
BREATH_TAX = 0.02              # continuous, invisible, always there

# Daily hazard at MAXIMUM hunger/thirst. The first values (0.020 and
# 0.090) meant a maximally hungry person died with ~99.9% probability
# within a year, which collapsed the population by half in five years.
# Most hungry people do not starve to death — that is precisely why
# hunger is politically potent rather than merely fatal. Famine
# mortality even at its worst is a few percent per year of the affected.
STARVATION_DEATH = 1.2e-4
DEHYDRATION_DEATH = 6.0e-4


@dataclass
class Flourishing:
    # the body's demands, 0 = met, 1 = desperate
    hunger: np.ndarray
    thirst: np.ndarray
    breath: np.ndarray
    # the reasons, 0..1
    hope: np.ndarray
    curiosity: np.ndarray
    meaning: np.ndarray
    belonging: np.ndarray
    satisfaction: np.ndarray
    # what a person has actually received
    art_received: np.ndarray
    lifetime_joy: np.ndarray


def birth_flourishing(civ, life, seed: int = 0) -> Flourishing:
    rng = np.random.default_rng(seed ^ 0xF10)
    n = civ.n
    # air is worse where industry is dense and regulation is thin
    from earth1.genesis import GENESIS_COUNTRIES
    tier = np.array([{"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}
                     .get(c.get("income", "LMIC"), 2)
                     for c in GENESIS_COUNTRIES])[civ.country]
    air = np.clip(0.04 + 0.07 * tier + 0.05 * civ.urban
                  + rng.normal(0, 0.02, n), 0.0, 0.5)
    return Flourishing(
        hunger=np.clip(rng.beta(1.6, 7.0, n), 0, 1),
        thirst=np.clip(rng.beta(1.2, 9.0, n), 0, 1),
        breath=air,
        hope=np.clip(rng.beta(4.0, 3.0, n), 0, 1),
        curiosity=np.clip(0.3 + 0.5 * civ.openness
                          + rng.normal(0, 0.10, n), 0, 1),
        meaning=np.clip(rng.beta(3.5, 3.0, n), 0, 1),
        belonging=np.clip(life.relationship
                          if life.relationship is not None
                          else rng.beta(3, 3, n), 0, 1),
        satisfaction=np.clip(rng.beta(3.0, 3.0, n), 0, 1),
        art_received=np.zeros(n),
        lifetime_joy=np.zeros(n))


def _water_access(civ, soil) -> np.ndarray:
    """Can this person reach clean water today?

    Infrastructure sets the floor; the water in the ground moves it.
    A drought reaches a rich country as a headline and a poor one as
    thirst, which is the whole difference.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    tier = np.array([{"HIC": 0, "UMIC": 1, "LMIC": 2, "LIC": 3}
                     .get(c.get("income", "LMIC"), 2)
                     for c in GENESIS_COUNTRIES])[civ.country]
    infra = np.array([0.995, 0.96, 0.86, 0.68])[tier]
    infra = np.where(civ.urban, infra, infra - 0.12)
    if soil is not None:
        infra = infra * (0.55 + 0.45 * np.clip(soil[civ.country] / 0.6,
                                               0, 1))
    return np.clip(infra, 0.0, 1.0)


def flourishing_tick(civ, life, fl: Flourishing, kn, health, rng,
                     dt_days: float = 1.0, alive=None, adj=None,
                     discoveries_today: int = 0,
                     works_today: int = 0,
                     welfare: np.ndarray | None = None,
                     soil: np.ndarray | None = None) -> dict:
    """The body's demands, then the reasons, then what they do to opinion."""
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)
    dep = np.clip(life.deprivation, 0, 1)

    # ── the body ─────────────────────────────────────────────────────
    # what you can buy is what you can eat. Deprivation is exactly the
    # inability to meet today's needs, so it is the input here.
    fl.hunger = np.clip(fl.hunger + (HUNGER_PER_DAY * dep
                                     - 0.40 * (1 - dep)) * dt_days, 0, 1)
    # THIRST IS NOT SLOW HUNGER. Driving both off deprivation made them
    # the same variable twice, and they came out numerically identical.
    # Hunger is an INCOME problem — you cannot afford food. Thirst is an
    # INFRASTRUCTURE problem — there is no clean water within reach,
    # which is why it tracks the country you live in and the water in
    # its ground rather than the money in your pocket.
    water = _water_access(civ, soil)
    fl.thirst = np.clip(fl.thirst + (THIRST_PER_DAY * (1.0 - water)
                                     - 1.20 * water) * dt_days, 0, 1)

    starving = live & (rng.random(n) < STARVATION_DEATH * fl.hunger ** 3
                       * dt_days)
    parched = live & (rng.random(n) < DEHYDRATION_DEATH * fl.thirst ** 3
                      * dt_days)
    gone = starving | parched
    if gone.any() and health is not None:
        health.alive[gone] = False
        from earth1.types import CauseOfDeath
        health.cause_of_death[gone] = int(CauseOfDeath.WANT)

    # breathing is a continuous tax nobody notices paying
    life.physical = np.clip(life.physical - BREATH_TAX * fl.breath
                            * dt_days * 0.01, 0, 1)

    # ── CROWDING OUT: an unmet body cannot think about anything else ──
    # this is the coupling that makes hunger political rather than only
    # fatal. The horizon shrinks to the next meal.
    need = np.clip(0.6 * fl.hunger + 0.4 * fl.thirst, 0, 1)
    headroom = 1.0 - need

    # ── the reasons ──────────────────────────────────────────────────
    # HOPE: the world is learning, help arrived, work was found
    world_learning = min(1.0, discoveries_today / max(n * 2e-5, 1e-9))
    help_arrived = welfare if welfare is not None else np.full(n, 0.4)
    found_work = (life.last_event == 2) if life.last_event is not None \
        else np.zeros(n, dtype=bool)
    hope_target = np.clip(0.20 + 0.25 * world_learning + 0.30 * help_arrived
                          + 0.25 * (1 - dep) + 0.20 * found_work, 0, 1)
    fl.hope += 0.05 * (hope_target * headroom - fl.hope) * dt_days

    # CURIOSITY: fed by discovery and by proximity to people who know
    # POSTHUMOUS rule: near-knowing and art received through one's
    # circle are current-social reads; the caller passes the living view.
    # (Durable works persist through knowledge.living_works/global_stock.)
    adj = civ.adj if adj is None else adj
    deg = np.maximum(np.asarray(adj.sum(axis=1)).ravel(), 1.0)
    near_knowing = np.asarray(adj @ kn.stock).ravel() / deg
    cur_target = np.clip(0.35 * civ.openness + 0.35 * near_knowing
                         + 0.30 * world_learning, 0, 1)
    fl.curiosity += 0.04 * (cur_target * headroom
                            * (1 - 0.5 * civ.forces[:, Force.FEAR])
                            - fl.curiosity) * dt_days

    # MEANING: art made and art received, plus work worth doing
    made = (kn.works_made > 0)
    art_flow = np.asarray(adj @ made.astype(adj.dtype)).ravel() / deg
    fl.art_received += art_flow * dt_days * 0.01
    mean_target = np.clip(0.25 + 0.35 * np.clip(fl.art_received, 0, 1)
                          + 0.20 * kn.status + 0.20 * fl.belonging, 0, 1)
    fl.meaning += 0.03 * (mean_target - fl.meaning) * dt_days

    # BELONGING: family, household, ties that hold
    fl.belonging = np.clip(
        0.6 * (life.relationship if life.relationship is not None
               else fl.belonging)
        + 0.4 * np.clip(deg / 20.0, 0, 1), 0, 1)

    # SATISFACTION: a full stomach, a warm room, a body that works
    sat_target = np.clip(0.5 * (1 - need) + 0.3 * life.physical
                         + 0.2 * (1 - dep), 0, 1)
    fl.satisfaction += 0.08 * (sat_target - fl.satisfaction) * dt_days

    fl.lifetime_joy += (fl.hope + fl.meaning + fl.satisfaction) / 3.0 \
        * dt_days * 0.01

    for a in (fl.hope, fl.curiosity, fl.meaning, fl.satisfaction):
        np.clip(a, 0, 1, out=a)

    # ── what all of it does to opinion ───────────────────────────────
    # An agent with hope tolerates hardship that breaks an agent without
    # it. That is the whole point of building this half: a world with
    # only suffering in it predicts revolt everywhere, and the real one
    # does not, because people have reasons to hold on.
    # CANONICAL (candidate 76a574c): flourishing does NOT write forces.
    # The incumbent wrote these five terms as unconditional daily
    # increments — the accumulation contradiction found by the 0.8
    # census ("LEVEL MAP, NOT ACCUMULATION", probe 1). The terms now
    # live where the architecture says they belong: as bounded LEVEL
    # contributions inside life.life_force_target (flourishing=...).

    return {"hungry": float((fl.hunger[live] > 0.5).mean()),
            "no_safe_water": float((_water_access(civ, soil)[live] < 0.85).mean()),
            "thirsty": float((fl.thirst[live] > 0.5).mean()),
            "starved_or_parched": int(gone.sum()),
            "hope": round(float(fl.hope[live].mean()), 4),
            "curiosity": round(float(fl.curiosity[live].mean()), 4),
            "meaning": round(float(fl.meaning[live].mean()), 4),
            "belonging": round(float(fl.belonging[live].mean()), 4),
            "satisfaction": round(float(fl.satisfaction[live].mean()), 4)}
