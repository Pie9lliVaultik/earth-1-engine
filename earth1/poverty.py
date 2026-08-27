"""H_poverty — Earth-1 material state → World Bank poverty observables.

Founder correction 2026-08-27: `deprivation > 0.5` is an Earth-1 latent
threshold and is NOT a monetary poverty rate. Comparing it to World Bank
figures was an informal analogy, not a measurement. This module makes
the mapping explicit, single-anchored and auditable.

OPERATOR (one declared anchor, no free parameters):
Earth-1 denominates welfare in `life.cost` — the daily budget that buys
survival (food + shelter). The World Bank's extreme line is the cost of
minimal survival consumption. We therefore anchor
    cost  ≡  EXTREME_LINE_PPP  ($/day, 2021 PPP)
and read every agent's welfare as
    welfare_$ = (income / cost) · EXTREME_LINE_PPP
so income == cost lands exactly on the extreme-poverty line. Nothing
else is fitted; the anchor is a definition, declared before scoring.

LINES (World Bank, June 2025 update, 2021 PPP):
  $3.00  extreme poverty
  $4.20  lower-middle-income line
  $8.30  upper-middle-income line
Approximate global reference shares at those lines (World Bank framing,
"about 1 in 10 / almost 1 in 5 / nearly half"): 0.10 / 0.19 / 0.45.
These are reference values for development scoring; a vintage-exact PIP
series must be registered before any confirmatory claim.

Reported: headcount at each line, and the poverty GAP (mean relative
shortfall over the whole population) — depth, not just incidence.
"""
from __future__ import annotations

import numpy as np

EXTREME_LINE_PPP = 3.00
LINES = {"poverty_300_2021ppp": 3.00, "poverty_420_2021ppp": 4.20,
         "poverty_830_2021ppp": 8.30}

_ANCHORS = None


def anchors() -> dict:
    """Real fetched anchors (data/anchors_worldbank.json, produced by
    scripts/fetch_anchors.py from the World Bank open API). No
    reference value in this module is authored by hand — founder ruling
    2026-08-27: benchmark against real data, never against memory."""
    global _ANCHORS
    if _ANCHORS is None:
        import json
        import os
        p = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "data", "anchors_worldbank.json")
        _ANCHORS = json.load(open(p))
    return _ANCHORS


def welfare_ppp(w) -> tuple:
    """Per-agent daily welfare in 2021-PPP dollars, plus census weights.

    Mirrors life_tick's income construction exactly (employed earn the
    wage; the jobless fall back on the better of welfare state and
    informal economy; those outside the labour force are carried)."""
    from earth1.genesis import census_weights
    from earth1.life import INFORMAL, SAFETY_NET, _tier

    civ, life, h = w.civ, w.life, w.health
    alive = h.alive
    keys = ["HIC", "UMIC", "LMIC", "LIC"]
    tier = _tier(civ)
    net = np.array([SAFETY_NET[k] for k in keys])[tier]
    informal = np.array([INFORMAL[k] for k in keys])[tier]
    policy = getattr(life, "policy_net", None)
    if policy is not None:
        net = np.asarray(policy)
    fallback = np.maximum(net, informal)
    fallback = np.where(life.in_lf, fallback, np.maximum(fallback, 0.75))
    income = np.where(life.employed, life.wage, life.wage * fallback)
    # HOUSEHOLD POOLING (2026-08-27, observation-operator repair).
    # World Bank/PIP poverty is measured on HOUSEHOLD PER-CAPITA
    # consumption, not individual earnings: members pool income and
    # share it. Reading individual income against a household-based
    # series over-counted the poor at the bottom (Earth-1 has no
    # single-earner household concept otherwise). Earth-1's household
    # unit is the partnership (earth1/partnership.py); singles are
    # one-person households. Physics is untouched — this changes what
    # the operator MEASURES, not what agents do.
    partner = getattr(life, "partner", None)
    if partner is not None:
        p = np.asarray(partner)
        pooled = income.copy()
        cost_h = np.asarray(life.cost, dtype=float).copy()
        both = (p >= 0) & alive & alive[np.clip(p, 0, len(p) - 1)]
        idx = np.flatnonzero(both)
        if idx.size:
            j = p[idx]
            # per-capita of the two-person household
            pooled[idx] = 0.5 * (income[idx] + income[j])
            cost_h[idx] = 0.5 * (life.cost[idx] + life.cost[j])
        income, cost_used = pooled, cost_h
    else:
        cost_used = life.cost
    ratio = income / np.maximum(cost_used, 1e-9)
    return (ratio[alive] * EXTREME_LINE_PPP), census_weights(civ)[alive]


def poverty_profile(w) -> dict:
    """Headcounts and poverty gaps at the three registered lines."""
    wel, cw = welfare_ppp(w)
    tot = cw.sum()
    A = anchors()["anchors"]
    out = {"anchor_line_ppp": EXTREME_LINE_PPP,
           "reference_source": anchors()["source"]}
    for name, line in LINES.items():
        poor = wel < line
        out[f"{name}_headcount"] = float(cw[poor].sum() / tot)
        gap = np.clip((line - wel) / line, 0.0, 1.0)
        out[f"{name}_gap"] = float((cw * gap).sum() / tot)
        out[f"{name}_reference"] = A[name]["value"] / 100.0
        out[f"{name}_reference_year"] = A[name]["year"]
        out[f"{name}_series_id"] = A[name]["series_id"]
    out["median_welfare_ppp"] = float(np.median(wel))
    return out


AGE_BANDS = ((18, 40), (40, 55), (55, 70), (70, 120))


def mortality_structure(dead_ages: np.ndarray) -> dict:
    """Age distribution of deaths.

    NOT SCORED against any reference: the real adult death-share-by-age
    distribution requires UN WPP or WHO life tables and has not been
    fetched (WHO GHO API unreachable 2026-08-27). The previous version
    of this function compared against constants written from memory —
    removed. Earth-1's shape is reported; the comparison is
    BLOCKED_ON_DATA and must not be called a benchmark until the real
    series is fetched, hashed and registered.

    Note also that Earth-1 is an ADULT-ONLY world (18+), so its death
    rate is not directly comparable to the all-ages crude death rate;
    the adult-population adjustment needs the same missing series.
    """
    if len(dead_ages) == 0:
        return {"n": 0, "scored": False}
    out = {"n": int(len(dead_ages)), "scored": False,
           "reference_status": "BLOCKED_ON_DATA (UN WPP / WHO life tables)"}
    for lo, hi in AGE_BANDS:
        m = (dead_ages >= lo) & (dead_ages < hi)
        out[f"share_{lo}_{hi}"] = float(m.mean())
    out["mean_age_at_death"] = float(dead_ages.mean())
    return out
