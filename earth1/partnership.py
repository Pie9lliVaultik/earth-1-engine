"""Romantic partnership — a first-class edge (API-COMPLETE-1, 2026-08-23).

`life.partner[i]` is the slot index of i's partner, -1 when single.
STATE ONLY: no dynamics read it. Genesis pairs adults inside a
household (the two oldest adults of compatible age, deterministic under
the world seed); a death widows the survivor; newborns enter single.
Formation over time is NOT modelled (recorded as the model's honest
limit: partnership is a genesis condition plus dissolution by death).
"""
from __future__ import annotations

import numpy as np

ADULT = 0.02          # civ.age is normalized (0 = 18y); anyone past entry
MAX_AGE_GAP = 0.25    # normalized


def pair_at_genesis(w, rng) -> int:
    civ, life, fab = w.civ, w.life, w.fabric
    if getattr(life, "partner", None) is None or fab is None:
        return 0
    hh = np.asarray(fab.household)
    order = np.lexsort((-civ.age, hh))          # by household, oldest first
    hh_s = hh[order]
    starts = np.flatnonzero(np.r_[True, hh_s[1:] != hh_s[:-1]])
    ends = np.r_[starts[1:], hh_s.size]
    paired = 0
    partner = life.partner
    for a, b in zip(starts, ends):
        if b - a < 2:
            continue
        i, j = int(order[a]), int(order[a + 1])
        if civ.age[i] < ADULT or civ.age[j] < ADULT:
            continue
        if abs(float(civ.age[i] - civ.age[j])) > MAX_AGE_GAP:
            continue
        if rng.random() < 0.15:                   # some households are not couples
            continue
        partner[i] = j; partner[j] = i; paired += 1
    return paired


def dissolve_on_death(life, newly_dead: np.ndarray) -> int:
    """The survivor of a deceased partner becomes single (widowed)."""
    p = getattr(life, "partner", None)
    if p is None:
        return 0
    dead = np.flatnonzero(newly_dead)
    if dead.size == 0:
        return 0
    surv = p[dead]
    surv = surv[surv >= 0]
    p[surv] = -1
    p[dead] = -1
    return int(surv.size)
