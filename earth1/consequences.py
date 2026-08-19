"""CONSEQUENCES — what happened to people, in the language people use.

Pietro, 2026-08-18: "Nobody gives a shit about a fear heat map. They
want to know how many people lose their jobs. Which countries go into
recession. Where food prices spike. Which governments fall. Where
protests erupt. Where refugees go. Who starves."

He is right, and the distinction is the whole product. The forces are
the engine; consequences are the dashboard. Nobody who drives a car
wants to see the combustion cycle — they want to know how fast they are
going and whether they are about to hit the wall.

Everything below is already computed by the world. This module does no
new physics whatsoever. It reads the state and states what it means in
the only units a minister, a CEO or a journalist can act on:

    jobs lost              recession           governments at risk
    people pushed under    refugee pressure    protest risk
    recovery timeline      permanent scarring  who specifically suffers

Two rules hold everywhere in here.

ALWAYS AGAINST A COUNTERFACTUAL. "Four million lost their jobs" is
meaningless without "compared to what". Every number is a DIFFERENCE
between a branch and the same world that did not receive the shock, so
the figure is attributable to the event rather than to the ordinary
churn of a living world.

ALWAYS WITH ITS UNCERTAINTY. The world is chaotic — measured, FSLE
+0.13/day — so a single branch is one sample, not a forecast. Numbers
come with the spread across branches, and where the spread is wide that
IS the finding: the honest statement is not a point estimate, it is
"here is where the uncertainty lives and how wide it is".
"""
from __future__ import annotations

import numpy as np

from earth1.types import Force

# ── THE COUNTRY MAP IS REFUSED ───────────────────────────────────────
# Measured 2026-08-19, registered in
# data/stratified_allocation_prereg.json before the run.
#
# The noise floor — two runs of the IDENTICAL scenario differing only in
# dice — sits at rank correlation -0.6 and set overlap 0.11, and it does
# not move with sample size:
#
#     50,000 agents   (258/country)   -0.583
#    200,000 agents  (1031/country)   -0.600
#    600,000 agents  (3093/country)   -0.617
#
# A twelve-fold increase in agents per country changed nothing. Country
# rankings are not sample-limited, they are GENUINELY CHAOTIC — which is
# the butterfly effect (FSLE +0.13/day, measured independently) showing
# up as a limit on what can be forecast. It is the same limit weather
# models live with: the response to forcing is predictable, the
# trajectory is not.
#
# So country-level detail is computed and RETURNED BEHIND A FLAG, never
# in the headline. Anyone who wants it must pass
# include_unstable_country_detail=True and will get the noise floor
# attached to it. This is a structural refusal, not a caveat in a
# footnote, because a caveat gets dropped when a chart is made.
COUNTRY_MAP_IS_STABLE = False
COUNTRY_NOISE_FLOOR_RANK_CORR = -0.60

# a country is called into recession when this share of its workers
# lose income relative to the counterfactual
RECESSION_JOB_LOSS = 0.02
# governments below this legitimacy, falling, are flagged at risk
GOV_AT_RISK = 0.25
PROTEST_FEAR = 0.72          # fear level at which unrest becomes likely
PROTEST_PARTICIPATION = 0.20  # share of a locality needed to show it


def _by_country(civ, mask, nc: int) -> np.ndarray:
    return np.bincount(civ.country, weights=mask.astype(np.float64),
                       minlength=nc)


def snapshot(w) -> dict:
    """The raw quantities a consequence report is computed from.

    EVERY GLOBAL FIGURE IS CENSUS-WEIGHTED. Agents are allocated with a
    per-country floor so that small countries are estimable at all,
    which means Palau holds as many agents as its floor allows while
    India holds a share far below its true 17.9% of humanity. Counting
    agents unweighted therefore does not describe humanity, it describes
    the sampling frame — and the harder we stratify to fix the country
    map, the more wrong those totals get.

    genesis.census_weights() already carries the correction; it simply
    was not being applied here.
    """
    from earth1.genesis import GENESIS_COUNTRIES, census_weights
    nc = len(GENESIS_COUNTRIES)
    civ, life, h = w.civ, w.life, w.health
    alive = h.alive
    fl = w.flourishing

    cw = census_weights(civ)

    def wcount(mask) -> float:
        """Population-true count: agents weighted back to census shares."""
        return float((cw * (mask & alive)).sum())

    return {
        "population": wcount(np.ones(civ.n, dtype=bool)),
        "employed": wcount(life.employed),
        "unemployed": wcount(~life.employed & life.in_lf),
        "destitute": wcount(life.deprivation > 0.99),
        "hungry": wcount(fl.hunger > 0.5) if fl else 0.0,
        "homeless": wcount(w.klass.homeless),
        "evicted": float((cw * life.evicted).sum())
        if life.evicted is not None else 0.0,
        "migrants": float((cw * w.klass.migrated).sum()),
        "at_war": int((w.gov.at_war_with >= 0).sum()),
        "dead": float((cw * ~alive).sum()),
        "median_buffer": float(np.median(life.wealth[alive])) if alive.any() else 0.0,
        # weighted, like every other global read — an unweighted mean
        # is the mood of the sampling frame, not of humanity
        "mean_hope": (float(np.average(fl.hope[alive], weights=cw[alive]))
                      if fl and alive.any() else None),
        # Per country, for the map. These stay UNWEIGHTED on purpose:
        # inside a country every agent represents the same number of
        # real people, so a weight would cancel. The weights only matter
        # when comparing or summing ACROSS countries.
        "jobless_by_country": _by_country(
            civ, (~life.employed & life.in_lf & alive), nc),
        "destitute_by_country": _by_country(
            civ, (life.deprivation > 0.99) & alive, nc),
        "workers_by_country": np.maximum(
            _by_country(civ, life.in_lf & alive, nc), 1.0),
        # how many real people each agent stands for, per country —
        # needed to turn a country rate back into a headcount
        "people_per_agent_by_country": np.array([
            (float(np.mean(cw[civ.country == i])) if (civ.country == i).any()
             else 0.0) for i in range(nc)]),
        "legitimacy": w.gov.legitimacy.copy(),
        "fear_by_country": (np.bincount(
            civ.country, weights=civ.forces[:, Force.FEAR], minlength=nc)
            / np.maximum(np.bincount(civ.country, minlength=nc), 1)),
    }


def protest_risk(w) -> np.ndarray:
    """Where unrest is likely: enough angry people in the same place.

    Uses the same participation logic as a cascade, because a protest IS
    a threshold crossing — it needs a critical mass in one locality, not
    a high national average.
    """
    civ = w.civ
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))
    _, li = np.unique(loc, return_inverse=True)
    nl = int(li.max()) + 1
    angry = ((civ.forces[:, Force.FEAR] > PROTEST_FEAR)
             & (w.life.deprivation > 0.4) & w.health.alive)
    frac = (np.bincount(li, weights=angry.astype(np.float64), minlength=nl)
            / np.maximum(np.bincount(li, minlength=nl), 1))
    hot = frac >= PROTEST_PARTICIPATION
    from earth1.genesis import GENESIS_COUNTRIES
    nc = len(GENESIS_COUNTRIES)
    out = np.zeros(nc)
    for l_id in np.flatnonzero(hot):
        members = np.flatnonzero(li == l_id)
        if members.size:
            out[civ.country[members[0]]] += 1
    return out


def compare(baseline: dict, branch: dict, w_branch, days: int,
            include_unstable_country_detail: bool = False) -> dict:
    """What this branch did to people, ATTRIBUTABLE to the event.

    Every figure is a difference against the world that did not receive
    the shock, which is the only way a number like "job losses" means
    anything in a world that is always churning.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    names = [c["name"] for c in GENESIS_COUNTRIES]
    iso = [c["iso2"] for c in GENESIS_COUNTRIES]

    # A country's extra jobless in AGENTS becomes real people only after
    # multiplying by what an agent there stands for. Skipping this made
    # a small country's agent count directly comparable to a large one's
    # — which is precisely how Palau ended up outranking India.
    ppa = branch.get("people_per_agent_by_country")
    raw_jobless = branch["jobless_by_country"] - baseline["jobless_by_country"]
    extra_jobless = raw_jobless * ppa if ppa is not None else raw_jobless
    share = raw_jobless / baseline["workers_by_country"]
    recession = np.flatnonzero(share >= RECESSION_JOB_LOSS)

    leg_fall = baseline["legitimacy"] - branch["legitimacy"]
    at_risk = np.flatnonzero((branch["legitimacy"] < GOV_AT_RISK)
                             & (leg_fall > 0.02))

    protests = protest_risk(w_branch)

    extra_destitute = int(branch["destitute"] - baseline["destitute"])
    extra_dead = int(branch["dead"] - baseline["dead"])
    extra_migrants = int(branch["migrants"] - baseline["migrants"])
    extra_homeless = int(branch["homeless"] - baseline["homeless"])

    def top(arr, k=5, minimum=1.0):
        idx = np.argsort(-arr)[:k]
        return [{"country": names[i], "iso2": iso[i], "value": float(arr[i])}
                for i in idx if arr[i] >= minimum]

    return {
        "horizon_days": days,
        # Only the countries that LOST jobs count. Summing signed
        # changes across countries let hires in one place cancel losses
        # in another, and max(0, ...) then floored the whole figure to
        # zero — which is how a branch reported 0 jobs lost while
        # pushing 193 million people into destitution. A person who lost
        # a job in Vietnam is not un-lost by a hire in Brazil.
        "jobs_lost": int(round(float(np.maximum(extra_jobless, 0).sum()))),
        "jobs_gained_elsewhere": int(round(float(
            np.maximum(-extra_jobless, 0).sum()))),
        # country detail: measured to be noise, so it is suppressed by
        # default and labelled when requested
        "jobs_lost_where": (top(extra_jobless)
                            if include_unstable_country_detail else []),
        "countries_in_recession": ([names[i] for i in recession]
                                   if include_unstable_country_detail else []),
        # THE FULL COUNTRY VECTOR, always returned. The diagnostic that
        # declared country consequences "chaotic" was comparing two
        # TOP-FIVE lists out of 194 countries — zero-padding two
        # near-disjoint supports produces a large negative correlation
        # as pure arithmetic, with no bearing on whether the underlying
        # signal is stable. Stability has to be measured on the whole
        # vector, so the whole vector has to be available.
        "jobs_by_country_vector": extra_jobless.tolist(),
        "jobless_rate_change_by_country": (
            raw_jobless / baseline["workers_by_country"]).tolist(),
        "country_iso2": iso,
        "country_detail_suppressed": not include_unstable_country_detail,
        "country_detail_note": (
            "country-level rankings are not reportable: two runs of the "
            "same scenario diverge at rank correlation -0.60, unchanged "
            "from 258 to 3,093 agents per country. Global aggregates are "
            "stable and are the product."),
        "people_pushed_into_destitution": max(0, extra_destitute),
        "people_made_homeless": max(0, extra_homeless),
        "excess_deaths": max(0, extra_dead),
        "displaced": max(0, extra_migrants),
        "governments_at_risk": ([
            {"country": names[i], "legitimacy": round(float(
                branch["legitimacy"][i]), 3),
             "fell_by": round(float(leg_fall[i]), 3)} for i in at_risk]
            if include_unstable_country_detail else []),
        "governments_at_risk_count": int(at_risk.size),
        "protest_risk_where": (top(protests, minimum=1.0)
                               if include_unstable_country_detail else []),
        "countries_at_war": branch["at_war"] - baseline["at_war"],
        "hope_change": (round(branch["mean_hope"] - baseline["mean_hope"], 4)
                        if branch["mean_hope"] is not None else None),
        "savings_change_days": round(
            branch["median_buffer"] - baseline["median_buffer"], 2),
    }


def with_uncertainty(reports: list) -> dict:
    """Collapse repeated branches into a figure AND its spread.

    The world is chaotic, so one branch is a sample. Where the spread is
    wide, that width is the finding.
    """
    if not reports:
        return {}
    keys = ["jobs_lost", "people_pushed_into_destitution", "excess_deaths",
            "displaced", "people_made_homeless"]
    out = {}
    for k in keys:
        v = np.array([float(r.get(k, 0) or 0) for r in reports])
        out[k] = {"median": float(np.median(v)),
                  "low": float(np.percentile(v, 10)),
                  "high": float(np.percentile(v, 90)),
                  "spread_ratio": (float(np.percentile(v, 90)
                                         / max(np.percentile(v, 10), 1.0)))}
    # a country counts as "in recession" by how often it lands there
    from collections import Counter
    rec = Counter()
    for r in reports:
        rec.update(r.get("countries_in_recession", []))
    out["recession_probability"] = {
        c: round(n / len(reports), 2) for c, n in rec.most_common(10)}
    gov = Counter()
    for r in reports:
        gov.update(g["country"] for g in r.get("governments_at_risk", []))
    out["government_at_risk_probability"] = {
        c: round(n / len(reports), 2) for c, n in gov.most_common(10)}
    return out
