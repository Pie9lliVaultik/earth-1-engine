"""CONTAGION — bodies in the same place. A different physics from opinion.

Pietro asked about energy passing between people. The literal
electromagnetic version is not buildable honestly — the body's field at
conversational distance is roughly a millionth of Earth's ambient field
and there is no replicated evidence of person-to-person EM signalling
changing behaviour. Building it would put something unevidenced inside a
model we are trying to validate against reality.

But the phenomenon is real, and it was missing. Energy does pass between
co-present people, and the channels that carry it are well evidenced:

  CHEMOSIGNAL   human sweat carries stress signals that measurably
                alter a recipient's amygdala response. Replicated, and
                the closest real thing to what he was describing.
  MIMICRY       facial and postural, sub-second, automatic
  PROSODY       affect transmits through tone independent of words
  SYNCHRONY     heart rate and respiration genuinely entrain between
                interacting people, and across audiences

All of it is EMOTIONAL CONTAGION, and it has three properties the
conviction kernel does not have:

  it runs on PHYSICAL CO-PRESENCE, not on network ties
  it is FAST — within a day, not across days
  it transmits AFFECT, not opinion

That third point is why this module exists. Conviction spreads opinion
between minds along the social fabric. Contagion spreads arousal between
bodies in a shared space. They are different mechanisms with different
geometry, and a model with only the first cannot produce crowds.

AND THAT IS THE STRUCTURAL HOLE THIS FILLS. A protest is not a graph
phenomenon. Neither is a panic, a riot, a stampede, a stadium, or a
queue that turns ugly. They are all CO-PRESENCE phenomena and they
depend on physical density, not on who follows whom. Earth-1 had a
social fabric and no notion of bodies being in the same place at the
same time, which meant it could not produce crowd behaviour at all.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Force

# Affect contagion is fast and pre-cognitive. This gain is per DAY but
# represents many sub-second exchanges, which is why it dwarfs the
# opinion-propagation rate.
CONTAGION_GAIN = 0.30
# Only the arousing channels are contagious. You catch fear from a
# frightened crowd; you do not catch their economic analysis.
CONTAGIOUS = {Force.FEAR: 1.00, Force.COLLECTIVE: 0.80,
              Force.IDENTITY: 0.45, Force.DESIRE: 0.30}

# gatherings: where bodies actually pile up
GATHER_KINDS = {
    # name: (share of population per day, density multiplier)
    "workplace": (0.42, 1.0),
    "transit": (0.30, 2.2),
    "market": (0.35, 1.6),
    "worship": (0.11, 2.0),
    "stadium": (0.02, 4.0),
}

# A crowd turns into an EVENT when enough co-present people are angry.
#
# The first values produced 22 riots a day in a world of twelve thousand
# people. The threshold had been set against an imagined fear
# distribution rather than the one this world actually runs, where mean
# fear sits near 0.85 — so almost every locality cleared the bar almost
# every day. Calibrated against reality instead: a few hundred notable
# riots worldwide per year, so roughly one a day across the whole model.
#
# And a riot needs GRIEVANCE, not merely arousal. Frightened people do
# not riot; frightened people with nothing left to lose do. Requiring
# deprivation alongside fear is what separates a nervous crowd from an
# angry one.
CROWD_AROUSAL = 0.82
CROWD_GRIEVANCE = 0.35
CROWD_FRACTION = 0.38
RIOT_ESCALATION = 0.02        # per crowd-day, not per crowd

# Share of the population out among other people on a given day. The
# rest are at home, ill, retired, or simply not going anywhere — and
# they are the ones contagion cannot reach, which is most of what
# isolation physically means.
OUT_AMONG_PEOPLE = 0.72


# ── SHARED ATTENTION ─────────────────────────────────────────────────
# Sport earns its place as a THIRD GEOMETRY, distinct from both of the
# others. A World Cup final is not a network phenomenon and not a
# locality phenomenon — it is millions of people in one country having
# the same emotional experience in the same hour. Synchrony at national
# scale, with no physical co-presence and no social tie required.
#
# The effect is measurable rather than romantic: national team results
# move consumer confidence and, in several studied cases, incumbent vote
# share. Winning raises collective identity; losing raises fear and
# depresses mood for days. It is one of the few mechanisms that produces
# a genuinely SIMULTANEOUS national mood shift, which makes it a clean
# natural experiment inside the model as well as a real force.
NATIONAL_EVENT_RATE_YR = 14.0     # matches, ceremonies, finals
ATTENTION_REACH = 0.55            # share of a country watching
WIN_IDENTITY = 0.05
LOSS_FEAR = 0.035


def shared_attention(civ, pres, rng, dt_days: float = 1.0,
                     alive=None, susceptibility=None) -> dict:
    """A whole country feels the same thing in the same hour."""
    from earth1.genesis import GENESIS_COUNTRIES
    nc = len(GENESIS_COUNTRIES)
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)

    having_event = rng.random(nc) < NATIONAL_EVENT_RATE_YR * dt_days / 365.0
    if not having_event.any():
        return {"national_events_today": 0, "watching": 0}

    won = rng.random(nc) < 0.5
    watching = live & having_event[civ.country] \
        & (rng.random(n) < ATTENTION_REACH)
    if not watching.any():
        return {"national_events_today": int(having_event.sum()),
                "watching": 0}

    victory = watching & won[civ.country]
    defeat = watching & ~won[civ.country]
    g = np.ones(n) if susceptibility is None else susceptibility[:, Force.IDENTITY]
    civ.forces[victory, Force.IDENTITY] = np.clip(
        civ.forces[victory, Force.IDENTITY] + WIN_IDENTITY * g[victory], 0, 1)
    civ.forces[victory, Force.COLLECTIVE] = np.clip(
        civ.forces[victory, Force.COLLECTIVE] + WIN_IDENTITY * 0.8, 0, 1)
    civ.forces[defeat, Force.FEAR] = np.clip(
        civ.forces[defeat, Force.FEAR] + LOSS_FEAR, 0, 1)
    return {"national_events_today": int(having_event.sum()),
            "watching": int(watching.sum()),
            "celebrating": int(victory.sum()),
            "grieving": int(defeat.sum())}


@dataclass
class Presence:
    """Where bodies are, which is not the same as who they know."""
    locality: np.ndarray      # int, the place this agent physically is
    density: np.ndarray        # per agent, how crowded their place is
    gathering: np.ndarray      # int code of today's gathering, -1 = none
    crowd_events: int = 0
    riots: int = 0


def birth_presence(civ, seed: int = 0) -> Presence:
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))
    _, li = np.unique(loc, return_inverse=True)
    counts = np.bincount(li)
    # density is people per place, normalised — cities are dense, and
    # that is most of what being urban means physically
    dens = counts[li].astype(np.float64)
    dens = dens / max(float(np.percentile(dens, 95)), 1.0)
    dens = np.clip(dens * np.where(civ.urban, 1.6, 0.5), 0.02, 3.0)
    return Presence(locality=li, density=dens,
                    gathering=np.full(civ.n, -1, dtype=np.int8))


def contagion_tick(civ, life, pres: Presence, rng, susceptibility=None,
                   dt_days: float = 1.0, alive=None) -> dict:
    """One day of bodies affecting bodies.

    Two passes. First the ordinary background of being among people in
    your locality. Then GATHERINGS — the places where density spikes and
    contagion becomes strong enough to produce collective events.
    """
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)
    nl = int(pres.locality.max()) + 1
    pop = np.maximum(np.bincount(pres.locality, minlength=nl), 1)

    # ── who is out among people today ────────────────────────────────
    # The listed shares are per-KIND attendance and they sum past 1.0,
    # because a person can be at work and on transit on the same day.
    # Assigning one gathering each from a cumulative range therefore put
    # EVERYONE somewhere and left nobody at home. Rescale so the shares
    # partition a realistic fraction of the population and the rest of
    # the day is spent out of any crowd.
    kinds = list(GATHER_KINDS)
    shares = np.array([GATHER_KINDS[k][0] for k in kinds], dtype=float)
    shares = shares / shares.sum() * OUT_AMONG_PEOPLE
    u = rng.random(n)
    pres.gathering[:] = -1
    acc = 0.0
    for i, k in enumerate(kinds):
        sel = live & (u >= acc) & (u < acc + shares[i])
        pres.gathering[sel] = i
        acc += shares[i]

    before = civ.forces.copy()

    # ── pass 1: the ambient mood of your locality ────────────────────
    for f, weight in CONTAGIOUS.items():
        col = civ.forces[:, f]
        local_mean = (np.bincount(pres.locality, weights=col, minlength=nl)
                      / pop)[pres.locality]
        gain = CONTAGION_GAIN * weight * pres.density * 0.25 * dt_days
        if susceptibility is not None:
            gain = gain * susceptibility[:, f]
        civ.forces[:, f] = np.clip(col + gain * (local_mean - col), 0, 1)

    # ── pass 2: gatherings, where density spikes ─────────────────────
    # inside a gathering you are pressed against people, so contagion is
    # multiplied by the density of that kind of place
    for k, (_, mult) in GATHER_KINDS.items():
        here = live & (pres.gathering == kinds.index(k))
        if not here.any():
            continue
        for f, weight in CONTAGIOUS.items():
            col = civ.forces[:, f]
            # the mood of the people you are actually pressed against:
            # same locality AND same gathering
            key = pres.locality * len(kinds) + kinds.index(k)
            nk = int(key.max()) + 1
            cnt = np.maximum(np.bincount(key[here], minlength=nk), 1)
            mean = (np.bincount(key[here], weights=col[here], minlength=nk)
                    / cnt)[key]
            g = CONTAGION_GAIN * weight * mult * 0.20 * dt_days
            if susceptibility is not None:
                g = g * susceptibility[:, f]
                civ.forces[here, f] = np.clip(
                    col[here] + g[here] * (mean[here] - col[here]), 0, 1)
            else:
                civ.forces[here, f] = np.clip(
                    col[here] + g * (mean[here] - col[here]), 0, 1)

    # ── crowds: when enough co-present bodies are aroused at once ────
    # This is a THRESHOLD on physical co-presence, which is why it can
    # produce a riot in one city while the country as a whole is calm.
    aroused = (live & (civ.forces[:, Force.FEAR] > CROWD_AROUSAL)
               & (np.clip(life.deprivation, 0, 1) > CROWD_GRIEVANCE)
               & (pres.gathering >= 0))
    frac = (np.bincount(pres.locality, weights=aroused.astype(np.float64),
                        minlength=nl) / pop)
    crowd = (frac >= CROWD_FRACTION) & (pop >= 20)
    n_crowd = int(crowd.sum())
    n_riot = 0
    if n_crowd:
        pres.crowd_events += n_crowd
        in_crowd = crowd[pres.locality] & live
        # a crowd amplifies itself — this is the collective feeling that
        # nobody in it produced alone
        civ.forces[in_crowd, Force.COLLECTIVE] = np.clip(
            civ.forces[in_crowd, Force.COLLECTIVE] + 0.08 * dt_days, 0, 1)
        civ.forces[in_crowd, Force.IDENTITY] = np.clip(
            civ.forces[in_crowd, Force.IDENTITY] + 0.05 * dt_days, 0, 1)
        # some crowds turn
        riot_loc = np.flatnonzero(crowd)[
            rng.random(n_crowd) < RIOT_ESCALATION * dt_days]
        n_riot = int(riot_loc.size)
        if n_riot:
            pres.riots += n_riot
            rioting = np.isin(pres.locality, riot_loc) & live
            civ.forces[rioting, Force.FEAR] = np.clip(
                civ.forces[rioting, Force.FEAR] + 0.10, 0, 1)
            if life.mental is not None:
                life.mental[rioting] = np.clip(
                    life.mental[rioting] - 0.02, 0, 1)

    moved = float(np.abs(civ.forces - before).mean())
    return {"contagion_moved": round(moved, 6),
            "in_a_gathering": float((pres.gathering >= 0)[live].mean()),
            "crowds_today": n_crowd,
            "riots_today": n_riot,
            "crowd_events_total": pres.crowd_events,
            "riots_total": pres.riots,
            "mean_density": round(float(pres.density[live].mean()), 4)}
