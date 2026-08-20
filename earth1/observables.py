"""The civilization observable bundle — the quantities Earth-1 actually
reports, collected identically for every precision arm of the
pre-registered equivalence study (PRECISION_EQUIVALENCE_PROTOCOL_0_7.md
families 1-13) and reusable by any later readout.

Everything returned is a plain float/int/list so it JSON-serializes;
distributions are summarized as mean + P10/P50/P90 per protocol.
"""
from __future__ import annotations

import numpy as np


def _q(x) -> dict:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {"mean": None, "p10": None, "p50": None, "p90": None}
    return {"mean": float(x.mean()),
            "p10": float(np.percentile(x, 10)),
            "p50": float(np.percentile(x, 50)),
            "p90": float(np.percentile(x, 90))}


def collect(w, cum: dict) -> dict:
    """One observation of the world. `cum` carries the run's cumulative
    journal counters (deaths, births, disease_deaths, migrations,
    rehomed workers, cascades, firms failed, ties_*)."""
    civ, life, h = w.civ, w.life, w.health
    alive = h.alive
    la = alive & life.in_lf
    emp = alive & life.employed
    obs = {
        # 1 demography
        "alive": int(alive.sum()),
        "cum_deaths": int(cum.get("deaths", 0)),
        "cum_births": int(cum.get("births", 0)),
        # 2 labour
        "employment_rate": float(life.employed[la].mean()) if la.any()
        else None,
        "wage_mean_employed": float(life.wage[emp].mean()) if emp.any()
        else None,
        "tenure_mean_employed": float(life.tenure[emp].mean())
        if emp.any() else None,
        # 3 material
        "wealth_mean": float(life.wealth[alive].mean()),
        "deprivation": _q(life.deprivation[alive]),
        "destitute_share": float((life.deprivation[alive] > 0.99).mean()),
        # 4 health
        "cum_disease_deaths": int(cum.get("disease_deaths", 0)),
        "mental_mean": float(life.mental[alive].mean())
        if life.mental is not None else None,
        "physical_mean": float(life.physical[alive].mean())
        if life.physical is not None else None,
        "addiction_mean": float(life.addiction[alive].mean())
        if life.addiction is not None else None,
        # 5 housing/insecurity
        "evicted_share": float(life.evicted[alive].mean())
        if life.evicted is not None else None,
        "arrears_mean": float(life.arrears[alive].mean())
        if life.arrears is not None else None,
        # 6 migration / fabric churn
        "cum_migrants_rehomed": int(cum.get("rehomed_migrants", 0)),
        "cum_workers_rehomed": int(cum.get("rehomed_workers", 0)),
        # 7 institutions
        "policy_net_mean": float(life.policy_net[alive].mean())
        if life.policy_net is not None else None,
        "firm_health_mean": float(life.firm_health.mean()),
        "cum_firms_failed": int(cum.get("firms_failed", 0)),
        # 11 memory/knowledge
        "memories_remembered": len(w.chronicle.events),
        "knowledge_stock_mean": float(w.knowledge.stock[alive].mean())
        if w.knowledge is not None else None,
        # 12 cascades
        "cum_cascades": int(cum.get("cascades_fired", 0)),
    }
    # 8 forces + 9 pole shares, per channel
    f = civ.forces[alive].astype(np.float64)
    obs["force_mean"] = [float(v) for v in f.mean(axis=0)]
    obs["force_sd"] = [float(v) for v in f.std(axis=0)]
    obs["pole_share"] = [float(v) for v in (f > 0.5).mean(axis=0)]
    # 10 network
    for tname in ("friends", "weak"):
        m = w.fabric.by_type[tname].tocsr()
        deg = np.diff(m.indptr)
        obs[f"{tname}_nnz"] = int(m.nnz)
        obs[f"{tname}_degree_mean"] = float(deg.mean())
        obs[f"{tname}_degree_p99"] = float(np.percentile(deg, 99))
        obs[f"{tname}_w_mean"] = float(m.data.mean()) if m.nnz else None
        obs[f"{tname}_w_max"] = float(m.data.max()) if m.nnz else None
    for k in ("ties_strengthened", "ties_weakened", "ties_pruned",
              "ties_rewired"):
        obs[f"cum_{k}"] = int(cum.get(k, 0))
    # 13 rankings: top-20 populous countries — per-country deprivation
    # and FEAR means, in a FIXED country order (by baseline population)
    counts = np.bincount(civ.country[alive])
    top = np.argsort(counts)[::-1][:20]
    obs["rank_countries"] = [int(c) for c in top]
    dep_c, fear_c = [], []
    for c in top:
        m = alive & (civ.country == c)
        dep_c.append(float(life.deprivation[m].mean()) if m.any() else None)
        fear_c.append(float(civ.forces[m, 0].mean()) if m.any() else None)
    obs["country_deprivation"] = dep_c
    obs["country_fear"] = fear_c
    return obs
