"""HEALTH — disease, cancer, hospitals, and dying of something specific.

"What is the formula of cancer?" There is one, and it is old and good.

ARMITAGE-DOLL MULTISTAGE (1954). A cell becomes cancerous only after k
independent mutational hits accumulate. If each hit arrives at a
roughly constant rate, the probability of having collected all k by age
t goes as t^(k-1), so incidence rises as a POWER of age, not linearly
and not exponentially. Fit to real registry data, k comes out around 6
for most solid tumours — six things have to go wrong in the same cell.

    incidence(t) = c * t^(k-1)

That single line reproduces the shape of nearly every cancer incidence
curve ever measured, which is why it survived seventy years. It is
implemented here literally, with c set per country from real crude
incidence and modulated by the two exposures the model already tracks:
substance dependence (the smoking channel) and deprivation (late
presentation, worse everything).

The rest of the burden follows the same discipline: cardiovascular
disease as the largest killer everywhere, infectious disease weighted
to poor countries, injury weighted to young men. Treatment access is a
function of country income and personal wealth, so the same tumour is
survivable in Stockholm and fatal in Niamey — which is true, and is one
of the sharpest inequalities on Earth.

Death here is not a counter. It removes a person from the graph and
leaves bereavement on everyone tied to them, which is how a death
becomes a social event rather than a decrement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.life import OCC_NAMES

# ── the Armitage-Doll exponent ───────────────────────────────────────
# k = number of mutational hits required. ~6 for most solid tumours,
# fitted to registry incidence curves; the model uses k-1 as the power.
CANCER_STAGES = 6
CANCER_POWER = CANCER_STAGES - 1

# crude annual incidence per person at age 70, by country income tier.
# Rich countries record MORE cancer, because people live long enough to
# get it and because it is actually looked for.
CANCER_BASE_70 = {"HIC": 0.0125, "UMIC": 0.0080, "LMIC": 0.0055,
                  "LIC": 0.0040}

# annual hazard scales for the other big killers
CVD_BASE = {"HIC": 0.0090, "UMIC": 0.0105, "LMIC": 0.0120, "LIC": 0.0135}
INFECT_BASE = {"HIC": 0.0004, "UMIC": 0.0012, "LMIC": 0.0035, "LIC": 0.0080}
INJURY_BASE = {"HIC": 0.0004, "UMIC": 0.0007, "LMIC": 0.0011, "LIC": 0.0016}

# probability a diagnosed condition is actually treated
TREATMENT_ACCESS = {"HIC": 0.92, "UMIC": 0.72, "LMIC": 0.45, "LIC": 0.22}
# survival given treatment, and given none
SURVIVE_TREATED = {"cancer": 0.68, "cvd": 0.82, "infection": 0.95,
                   "injury": 0.90, "fall": 0.93}
SURVIVE_UNTREATED = {"cancer": 0.18, "cvd": 0.42, "infection": 0.60,
                     "injury": 0.65, "fall": 0.72}

# ── FALLS ────────────────────────────────────────────────────────────
# Gravity is a constant, so it contributes no variance and cannot on its
# own differentiate two people. FALLING is not a constant. Roughly
# 684,000 people die from falls each year — the second leading cause of
# unintentional injury death — and the risk is steeply graded by age,
# frailty, alcohol and occupation. A roofer and an accountant live under
# the same gravitational constant with completely different fall risk.
#
# That distinction is what licences falls and excludes quarks: the
# question is never whether a quantity varies, it is whether the
# quantity's INTERACTION with a person varies.
FALL_DEATHS_PER_100K = {"HIC": 9.0, "UMIC": 8.0, "LMIC": 11.0, "LIC": 13.0}
# a fall at 80 is not a fall at 25 — the hazard roughly doubles every
# decade past 65, which is one of the steepest age gradients in medicine
FALL_AGE_DOUBLING_YEARS = 10.0
# occupations that work at height
FALL_RISK_OCCUPATIONS = ("manual_labour", "trades")
# For an older person a fall is frequently the START OF DECLINE rather
# than a discrete event: loss of independence, then isolation, then
# mortality. That cascade is one of the most common real trajectories
# into a nursing home and it was entirely absent.
FALL_DECLINE_AGE = 0.60        # normalised age above which a fall cascades

DISEASES = ("cancer", "cvd", "infection", "injury", "fall")
TIERS = ["HIC", "UMIC", "LMIC", "LIC"]


@dataclass
class Health:
    condition: np.ndarray      # 0 none, 1 cancer, 2 cvd, 3 infect, 4 injury, 5 fall
    diagnosed_day: np.ndarray  # world-day of onset, -1 if well
    in_treatment: np.ndarray   # bool
    alive: np.ndarray          # bool
    cause_of_death: np.ndarray # int, 0 = still alive
    lifetime_illnesses: np.ndarray
    # once an older person falls they often never fully return. This is
    # a permanent multiplier on frailty, not a temporary condition.
    declining: np.ndarray = None
    falls: np.ndarray = None


def birth_health(n: int) -> Health:
    return Health(condition=np.zeros(n, dtype=np.int8),
                  diagnosed_day=np.full(n, -1.0),
                  in_treatment=np.zeros(n, dtype=bool),
                  alive=np.ones(n, dtype=bool),
                  cause_of_death=np.zeros(n, dtype=np.int8),
                  lifetime_illnesses=np.zeros(n, dtype=np.int16),
                  declining=np.zeros(n),
                  falls=np.zeros(n, dtype=np.int16))


def _tier_idx(civ) -> np.ndarray:
    from earth1.genesis import GENESIS_COUNTRIES
    per = np.array([TIERS.index(c.get("income", "LMIC"))
                    if c.get("income") in TIERS else 2
                    for c in GENESIS_COUNTRIES])
    return per[civ.country]


def cancer_hazard(age_years: np.ndarray, tier: np.ndarray,
                  addiction: np.ndarray | None = None,
                  deprivation: np.ndarray | None = None) -> np.ndarray:
    """Armitage-Doll. incidence(t) = c * t^(k-1), calibrated at age 70.

    This is the formula, applied literally. The age term is doing all
    the work: a 70-year-old is not twice as likely as a 35-year-old,
    they are 2^5 = 32 times as likely, and that is what the registries
    actually show.
    """
    base = np.array([CANCER_BASE_70[t] for t in TIERS])[tier]
    shape = (np.maximum(age_years, 1.0) / 70.0) ** CANCER_POWER
    h = base * shape
    if addiction is not None:          # the smoking channel
        h = h * (1.0 + 1.8 * addiction)
    if deprivation is not None:        # later presentation, worse odds
        h = h * (1.0 + 0.5 * deprivation)
    return h


def health_tick(civ, life, health: Health, rng, day: float,
                dt_days: float = 1.0) -> dict:
    """One day of bodies. Returns what happened, including who died."""
    n = civ.n
    dt_yr = dt_days / 365.0
    tier = _tier_idx(civ)
    age_years = 18.0 + civ.age * 72.0
    well = health.alive & (health.condition == 0)

    u = rng.random((len(DISEASES) + 1, n))

    dep = np.clip(life.deprivation, 0, 1) if life is not None else 0.0
    add = life.addiction if (life is not None and life.addiction is not None) \
        else np.zeros(n)
    ment = life.mental if (life is not None and life.mental is not None) \
        else np.ones(n) * 0.7

    haz = {
        "cancer": cancer_hazard(age_years, tier, add, dep),
        "cvd": (np.array([CVD_BASE[t] for t in TIERS])[tier]
                * (np.maximum(age_years, 1.0) / 60.0) ** 2.6
                * (1.0 + 0.6 * dep) * (1.0 + 0.5 * (1.0 - ment))),
        "infection": (np.array([INFECT_BASE[t] for t in TIERS])[tier]
                      * (1.0 + 1.2 * dep)
                      * (1.0 + 0.8 * (age_years > 65))),
        "injury": (np.array([INJURY_BASE[t] for t in TIERS])[tier]
                   * (1.0 + 1.5 * add) * (1.0 + 0.7 * dep)),
        # FALLS. Gravity is constant; the interaction is not. Doubling
        # every decade past 65 is one of the steepest age gradients in
        # medicine, and working at height is its own exposure.
        "fall": (np.array([FALL_DEATHS_PER_100K[t] for t in TIERS])[tier]
                 / 1e5 * 365.0
                 * 2.0 ** (np.maximum(age_years - 65.0, 0.0)
                           / FALL_AGE_DOUBLING_YEARS)
                 * (1.0 + 2.0 * add)                     # alcohol
                 * (1.0 + 1.5 * (1.0 - life.physical
                                 if life is not None
                                 and life.physical is not None else 0.3))
                 * (1.0 + 0.8 * np.isin(
                     life.occupation,
                     [OCC_NAMES.index(o) for o in FALL_RISK_OCCUPATIONS
                      if o in OCC_NAMES]).astype(float)
                    if life is not None else 1.0)
                 * (1.0 + 2.5 * health.declining
                    if health.declining is not None else 1.0)),
    }

    onsets = {}
    for j, d in enumerate(DISEASES):
        hit = well & (u[j % u.shape[0]] < haz[d] * dt_yr)
        onsets[d] = int(hit.sum())
        health.condition[hit] = j + 1
        health.diagnosed_day[hit] = day
        health.lifetime_illnesses[hit] += 1
        if d == "fall" and health.falls is not None:
            health.falls[hit] += 1
            # THE CASCADE. For an older person a fall is usually not a
            # discrete event — it is the beginning of decline. They lose
            # confidence and mobility, then they stop going out, then
            # the isolation does the rest. This is the most common real
            # road into a nursing home and the model had no version of
            # it: a fall was simply an injury that healed.
            cascading = hit & (civ.age > FALL_DECLINE_AGE)
            if cascading.any() and health.declining is not None:
                health.declining[cascading] = np.clip(
                    health.declining[cascading] + 0.35, 0.0, 1.0)
                if life is not None:
                    # they stop going out
                    if life.social_need is not None:
                        life.social_need[cascading] = np.clip(
                            life.social_need[cascading] + 0.25, 0, 1)
                    if life.relationship is not None:
                        life.relationship[cascading] = np.clip(
                            life.relationship[cascading] - 0.15, 0, 1)
                    if life.physical is not None:
                        life.physical[cascading] = np.clip(
                            life.physical[cascading] - 0.20, 0, 1)
                    if life.in_lf is not None:
                        life.in_lf[cascading] = False   # out of work for good
        well = well & ~hit

    # ── treatment: can this person actually get care ─────────────────
    newly_ill = health.alive & (health.condition > 0) & ~health.in_treatment \
        & (health.diagnosed_day == day)
    if newly_ill.any():
        access = np.array([TREATMENT_ACCESS[t] for t in TIERS])[tier]
        # money buys care even where the system does not provide it
        buys = np.clip(life.wealth / 400.0, 0.0, 0.35) if life is not None \
            else 0.0
        p = np.clip(access + buys, 0.0, 0.98)
        # u[5] is the row allocated for this and never used; u[4] is the
        # FALL-ONSET row, and reusing it meant a faller's necessarily
        # small draw also passed the treatment gate — every faller was
        # treated, and SURVIVE_UNTREATED for falls was never sampled
        # (audit D4-b / 0.1a).
        health.in_treatment[newly_ill & (u[5] < p)] = True

    # ── resolution: recover, or die of something specific ────────────
    ill = health.alive & (health.condition > 0)
    resolve_p = np.where(health.condition == 1, 1.0 / 540.0, 1.0 / 45.0)
    resolving = ill & (rng.random(n) < resolve_p * dt_days)
    died = np.zeros(n, dtype=bool)
    if resolving.any():
        idx = np.flatnonzero(resolving)
        surv = np.empty(idx.size)
        for j, d in enumerate(DISEASES):
            m = health.condition[idx] == j + 1
            surv[m] = np.where(health.in_treatment[idx][m],
                               SURVIVE_TREATED[d], SURVIVE_UNTREATED[d])
        lived = rng.random(idx.size) < surv
        health.condition[idx[lived]] = 0
        health.in_treatment[idx[lived]] = False
        health.diagnosed_day[idx[lived]] = -1.0
        dead_idx = idx[~lived]
        health.alive[dead_idx] = False
        health.cause_of_death[dead_idx] = health.condition[dead_idx]
        health.condition[dead_idx] = 0
        died[dead_idx] = True

    # ── a death is a SOCIAL event ────────────────────────────────────
    # everyone tied to the person who died is bereaved. This is what
    # makes mortality part of the society rather than a counter.
    bereaved_n = 0
    if died.any() and life is not None and life.social_need is not None:
        touched = np.asarray(civ.adj @ died.astype(np.float64)).ravel() > 0
        touched &= health.alive
        bereaved_n = int(touched.sum())
        life.social_need[touched] = np.clip(
            life.social_need[touched] + 0.15, 0.0, 1.0)
        life.mental[touched] = np.clip(life.mental[touched] - 0.08, 0.0, 1.0)

    return {"onsets": onsets,
            "falls_total": (int(health.falls.sum())
                            if health.falls is not None else 0),
            "in_decline_after_a_fall": (
                float((health.declining[health.alive] > 0).mean())
                if health.declining is not None and health.alive.any() else 0.0),
            "ill": int((health.alive & (health.condition > 0)).sum()),
            "in_treatment": int(health.in_treatment.sum()),
            "deaths": int(died.sum()),
            "bereaved_by_death": bereaved_n,
            "alive": int(health.alive.sum())}
