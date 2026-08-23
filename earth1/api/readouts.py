"""READOUTS — every API answer, as a function of (world, history).
API-COMPLETE-1 (2026-08-23). The same functions serve the live
canonical Earth (`/…`) and any branch (`/branches/{id}/…`), so a query
means the same thing in a future as in the present. Read-only: no
function here mutates the world.
"""
from __future__ import annotations

import json
from typing import Optional

import numpy as np

from earth1.types import Force
from earth1.geography import (CONTINENT, CONTINENTS, city_name, continent_of,
                              country_codes, locality_key, locality_name,
                              region_profile, split_key)

FORCES = [f.name.lower() for f in Force]


class NotFound(KeyError):
    pass


# ── identity / lookup ──────────────────────────────────────────────
def slot_of(w, person_id: int) -> int:
    pid = w.civ.person_id
    hits = np.flatnonzero(pid == int(person_id))
    if hits.size == 0:
        raise NotFound(f"no earthling with person_id {person_id}")
    return int(hits[0])


def person_status(w, hist, slot: int) -> dict:
    civ, h = w.civ, w.health
    pid = int(civ.person_id[slot])
    alive = bool(h.alive[slot])
    out = {"person_id": pid, "slot": int(slot), "alive": alive,
           "status": "alive" if alive else "deceased",
           "cause_of_death": (_cause(h.cause_of_death[slot]) if not alive else None),
           "parent_id": int(civ.parent_id[slot]),
           "generation": "genesis" if int(civ.parent_id[slot]) < 0 else "born_in_world"}
    if hist is not None:
        r = hist.execute("SELECT MIN(day), MAX(day) FROM person_events WHERE person_id=?", (pid,)).fetchone()
        out["first_recorded_day"], out["last_recorded_day"] = r
        prev = hist.execute("SELECT person_id FROM person_events WHERE slot=? AND person_id<>? AND kind='died' ORDER BY day DESC LIMIT 1", (slot, pid)).fetchone()
        out["slot_previous_occupant_person_id"] = prev[0] if prev else None
    return out


def _cause(code):
    from earth1.health import DISEASES
    code = int(code)
    return DISEASES[code - 1] if 1 <= code <= len(DISEASES) else ("none" if code == 0 else f"cause_{code}")


# ── earthling ─────────────────────────────────────────────────────
def earthling(w, hist, slot: int) -> dict:
    from earth1.life import OCC_NAMES, EVENT_CODES
    civ, life, h, fl, k, kn = w.civ, w.life, w.health, w.flourishing, w.klass, w.knowledge
    i = int(slot)
    iso2 = country_codes()[int(civ.country[i])]
    loc = int(locality_key(civ)[i])
    prof = region_profile(iso2, int(civ.region[i]))
    d = {"identity": person_status(w, hist, i),
         "demographics": {"country": iso2, "continent": continent_of(iso2),
                          "region": {"index": int(civ.region[i]), "code": prof.code if prof else None, "name": prof.name if prof else None},
                          "locality": {"id": loc, "name": locality_name(loc)},
                          "urban": bool(civ.urban[i]), "age_years": round(18 + float(civ.age[i]) * 82, 1),
                          "education": ["low", "mid", "high"][int(civ.education[i])],
                          "income_tier": ["low", "mid", "high"][int(civ.income[i])]},
         "traits": {t: round(float(getattr(civ, t)[i]), 4) for t in
                    ("openness", "empathy", "risk_appetite", "doubt", "desire_intensity", "conscientiousness",
                     "agreeableness", "extraversion", "neuroticism", "power_distance", "individualism",
                     "uncertainty_avoidance", "long_term_orientation", "culture_offset", "economic_field")},
         "forces": forces(w, i),
         "work": work(w, i),
         "health": health(w, hist, i),
         "needs": needs(w, i),
         "housing": {"owns_home": bool(life.owns_home[i]), "rent": float(life.rent[i]), "arrears": float(life.arrears[i]),
                     "evicted": bool(life.evicted[i]), "homeless": bool(k.homeless[i]), "days_homeless": int(k.days_homeless[i])},
         "social": {"household_id": int(w.fabric.household[i]) if w.fabric is not None else None,
                    "partner_id": (int(civ.person_id[life.partner[i]]) if life.partner is not None and life.partner[i] >= 0 else None),
                    "tie_counts": tie_counts(w, i),
                    "relationship_quality": round(float(life.relationship[i]), 4),
                    "unmet_social_need": round(float(life.social_need[i]), 4),
                    "political_engagement": round(float(life.political[i]), 4)},
         "knowledge": {"stock": round(float(kn.stock[i]), 4), "status": round(float(kn.status[i]), 4),
                       "connected": bool(kn.connected[i]), "works_made": int(kn.works_made[i]), "discoveries": int(kn.discoveries[i])},
         "class": {"criminal": bool(k.criminal[i]), "crimes_committed": int(k.crimes_committed[i]), "migrated": bool(k.migrated[i])},
         "presence": presence(w, i),
         "last_life_event": {"event": EVENT_CODES.get(int(life.last_event[i]), None), "day": float(life.last_event_day[i]),
                             "lifetime_events": int(life.n_events[i])}}
    return d


def forces(w, slot: int) -> dict:
    from earth1.alive import effective_forces, cascade_residue_levels
    from earth1.susceptibility import compute as sus_of
    civ = w.civ; i = int(slot)
    stored = civ.forces[i]
    eff = np.asarray(effective_forces(w))[i]
    loc = int(locality_key(civ)[i])
    res = [r for r in (getattr(w.chronicle, "cascade_residues", None) or []) if r["loc"] == loc]
    levels, _ = cascade_residue_levels(res, w.day)
    overlay = {}
    for (r, lv) in zip(res, [l[1] for l in levels]) if levels else []:
        overlay.setdefault(r["rule"], np.zeros(8)); overlay[r["rule"]] += np.asarray(lv)
    mem = np.zeros(8)
    for m in w.chronicle.events:
        if m.scope is not None and m.scope[i]:
            mem += m.salience * np.asarray(m.force_signature) * 0.02
    try:
        sus = sus_of(civ, w.life, w.flourishing)[i]
    except Exception:  # noqa: BLE001
        sus = None
    return {"stored": {f: round(float(stored[k]), 5) for k, f in enumerate(FORCES)},
            "effective": {f: round(float(eff[k]), 5) for k, f in enumerate(FORCES)},
            "cascade_overlay_by_rule": {r: {f: round(float(v[k]), 5) for k, f in enumerate(FORCES)} for r, v in overlay.items()},
            "memory_press_today": {f: round(float(mem[k]), 6) for k, f in enumerate(FORCES)},
            "conviction": round(float(civ.alpha[i]), 5),
            "susceptibility": ({f: round(float(sus[k]), 5) for k, f in enumerate(FORCES)} if sus is not None else None),
            "locality": loc}


def force_history(hist, person_id: int) -> list:
    if hist is None:
        return []
    rows = hist.execute("SELECT day, f0,f1,f2,f3,f4,f5,f6,f7, alpha FROM force_samples WHERE person_id=? ORDER BY day", (int(person_id),)).fetchall()
    return [{"day": r[0], "forces": {f: r[1 + k] for k, f in enumerate(FORCES)}, "conviction": r[9]} for r in rows]


def person_history(hist, person_id: int, kind: Optional[str] = None) -> list:
    if hist is None:
        return []
    q = "SELECT day, slot, kind, detail FROM person_events WHERE person_id=?" + (" AND kind=?" if kind else "") + " ORDER BY day"
    rows = hist.execute(q, (int(person_id), kind) if kind else (int(person_id),)).fetchall()
    return [{"day": r[0], "slot": r[1], "kind": r[2], "detail": json.loads(r[3] or "{}")} for r in rows]


def work(w, slot: int) -> dict:
    from earth1.life import OCC_NAMES
    life = w.life; i = int(slot)
    return {"occupation": OCC_NAMES[int(life.occupation[i])], "employed": bool(life.employed[i]),
            "in_labour_force": bool(life.in_lf[i]), "firm_id": (int(life.firm[i]) if life.firm[i] >= 0 else None),
            "tenure_days": float(life.tenure[i]), "job_losses": int(life.spells[i]),
            "money": {"wage_daily": float(life.wage[i]), "wealth_days_of_cost": float(life.wealth[i]),
                      "daily_cost": float(life.cost[i]), "deprivation": float(life.deprivation[i]),
                      "durables": float(life.durables[i]), "policy_net": float(life.policy_net[i])}}


def consumption(w, slot: int) -> dict:
    """Today's receipt: what the person earned, what staying alive cost,
    what housing cost, what went to durables, what remained."""
    life = w.life; i = int(slot)
    wage = float(life.wage[i]) * bool(life.employed[i])
    sub = float(life.cost[i]); rent = float(life.rent[i]) * (not bool(life.owns_home[i])); dur = float(life.durable_spend[i])
    return {"day": int(w.day), "income": wage, "subsistence": sub, "housing": rent, "durables": dur,
            "net": round(wage - sub - rent - dur, 5), "savings_days": float(life.wealth[i]),
            "welfare_transfer": float(life.policy_net[i]), "units": "daily cost of living = 1.0"}


def health(w, hist, slot: int) -> dict:
    from earth1.health import DISEASES
    h, life = w.health, w.life; i = int(slot)
    c = int(h.condition[i])
    out = {"alive": bool(h.alive[i]), "condition": (DISEASES[c - 1] if c > 0 else None), "diagnosed_day": float(h.diagnosed_day[i]),
           "in_treatment": bool(h.in_treatment[i]), "declining": float(h.declining[i]), "falls": int(h.falls[i]),
           "lifetime_illnesses": int(h.lifetime_illnesses[i]), "cause_of_death": (_cause(h.cause_of_death[i]) if not h.alive[i] else None),
           "mental": round(float(life.mental[i]), 4), "physical": round(float(life.physical[i]), 4), "addiction": round(float(life.addiction[i]), 4)}
    return out


def needs(w, slot: int) -> dict:
    fl, life, cl, civ = w.flourishing, w.life, w.climate, w.civ; i = int(slot)
    ci = int(civ.country[i])
    return {"hunger": float(fl.hunger[i]), "thirst": float(fl.thirst[i]), "air": float(fl.breath[i]),
            "deprivation": float(life.deprivation[i]), "hope": float(fl.hope[i]), "meaning": float(fl.meaning[i]),
            "belonging": float(fl.belonging[i]), "satisfaction": float(fl.satisfaction[i]), "curiosity": float(fl.curiosity[i]),
            "country_food_system": {"farm_share": float(cl.farm_share[ci]), "soil": float(cl.soil[ci]),
                                    "temperature_anomaly": float(cl.anomaly[ci]), "storm_days": float(cl.storm_days[ci])} if cl is not None else None}


def presence(w, slot: int) -> dict:
    p, mob = w.presence, w.mobility; i = int(slot)
    out = {"locality": int(p.locality[i]) if p is not None else None, "density": float(p.density[i]) if p is not None else None,
           "gathering": int(p.gathering[i]) if p is not None else None}
    if mob is not None:
        out.update({"owns_car": bool(mob.owns_car[i]), "flights_per_year": float(mob.flies_per_year[i]),
                    "commute_minutes": float(mob.commute_minutes[i]), "trips_taken": int(mob.travelled[i])})
    return out


def tie_counts(w, slot: int) -> dict:
    fab = w.fabric; i = int(slot)
    return {t: int(m.getrow(i).nnz) for t, m in fab.by_type.items()} if fab is not None else {}


def relationships(w, slot: int, scope: str = "all") -> dict:
    """Direct ties with person ids, type and weight. scope=living hides
    deceased alters (the view the dynamics use); scope=all keeps them."""
    fab, civ, h, life = w.fabric, w.civ, w.health, w.life; i = int(slot)
    ties = []
    for t, m in fab.by_type.items():
        row = m.getrow(i)
        for j, wgt in zip(row.indices, row.data):
            if scope == "living" and not h.alive[j]:
                continue
            ties.append({"person_id": int(civ.person_id[j]), "slot": int(j), "type": t, "weight": float(wgt), "alive": bool(h.alive[j])})
    fam = family(w, i)
    return {"person_id": int(civ.person_id[i]), "scope": scope, "ties": ties, "partner": fam["partner"], "household": fam["household"],
            "edge_semantics": "edges into deceased alters are kept as history and carry zero weight in today's dynamics"}


def family(w, slot: int) -> dict:
    civ, life, fab, h = w.civ, w.life, w.fabric, w.health; i = int(slot)
    hh = int(fab.household[i]) if fab is not None else None
    members = [int(j) for j in np.flatnonzero(fab.household == hh)] if hh is not None else []
    partner = int(life.partner[i]) if life.partner is not None else -1
    children = np.flatnonzero(civ.parent_id == civ.person_id[i])
    return {"household": {"id": hh, "members": [{"person_id": int(civ.person_id[j]), "slot": int(j), "alive": bool(h.alive[j])} for j in members]},
            "partner": ({"person_id": int(civ.person_id[partner]), "slot": partner, "alive": bool(h.alive[partner])} if partner >= 0 else None),
            "parent": ({"person_id": int(civ.parent_id[i])} if civ.parent_id[i] >= 0 else None),
            "children": [{"person_id": int(civ.person_id[j]), "slot": int(j), "alive": bool(h.alive[j])} for j in children]}


def ego(w, slot: int, depth: int = 1, living_only: bool = True) -> dict:
    from scipy import sparse
    adj = w.civ.adj.tocsr(); h = w.health
    front = {int(slot)}; seen = {int(slot)}; layers = []
    for _ in range(max(1, min(depth, 3))):
        nxt = set()
        for i in front:
            row = adj.getrow(i)
            for j in row.indices:
                j = int(j)
                if living_only and not h.alive[j]:
                    continue
                if j not in seen:
                    nxt.add(j)
        seen |= nxt; layers.append(sorted(nxt)); front = nxt
    return {"person_id": int(w.civ.person_id[slot]), "depth": depth, "layer_sizes": [len(l) for l in layers],
            "layers": [[int(w.civ.person_id[j]) for j in l[:500]] for l in layers], "truncated_at": 500}


def memories_for(w, slot: int) -> list:
    return [memory_view(w, m) for m in w.chronicle.events if m.scope is not None and m.scope[int(slot)]]


def memory_view(w, m) -> dict:
    return {"id": m.id, "label": m.label, "day": float(m.day), "origin": m.origin, "salience": float(m.salience),
            "half_life_days": float(m.half_life), "rehearsals": int(m.rehearsals),
            "force_signature": {f: round(float(m.force_signature[k]), 5) for k, f in enumerate(FORCES)},
            "scope_n": int(np.asarray(m.scope).sum()) if m.scope is not None else 0}


def memory_impacts(w, m) -> dict:
    """The receipt: who carries it, what it presses on them today, and
    where (by locality) it is concentrated."""
    sc = np.asarray(m.scope) if m.scope is not None else np.zeros(w.civ.n, bool)
    press = float(m.salience) * np.asarray(m.force_signature) * 0.02
    loc = locality_key(w.civ)[sc]
    u, c = np.unique(loc, return_counts=True)
    top = np.argsort(-c)[:25]
    return {"id": m.id, "carriers": int(sc.sum()), "carriers_alive": int((sc & w.health.alive).sum()),
            "daily_press_per_carrier": {f: round(float(press[k]), 6) for k, f in enumerate(FORCES)},
            "localities": [{"id": int(u[k]), "name": locality_name(int(u[k])), "carriers": int(c[k])} for k in top],
            "carrier_person_ids": [int(x) for x in w.civ.person_id[np.flatnonzero(sc)[:1000]]]}


def cascade_list(w, loc: Optional[int] = None, rule: Optional[str] = None) -> list:
    from earth1.alive import cascade_residue_levels
    res = getattr(w.chronicle, "cascade_residues", None) or []
    levels, _ = cascade_residue_levels(res, w.day)
    lv = {id(r): l[1] for r, l in zip(res, levels)} if levels else {}
    out = []
    for k, r in enumerate(res):
        if loc is not None and r["loc"] != int(loc):
            continue
        if rule is not None and r["rule"] != rule:
            continue
        out.append({"firing_index": k, "rule": r["rule"], "locality": int(r["loc"]), "locality_name": locality_name(int(r["loc"])),
                    "day": int(r["day"]), "half_life_days": float(r["h"]),
                    "effects": {f: round(float(r["effects"][j]), 5) for j, f in enumerate(FORCES)},
                    "current_level": {f: round(float(lv[id(r)][j]), 5) for j, f in enumerate(FORCES)} if id(r) in lv else None})
    return out


def cascade_impact(w, hist, firing_index: int) -> dict:
    res = getattr(w.chronicle, "cascade_residues", None) or []
    if not (0 <= firing_index < len(res)):
        raise NotFound("no such cascade firing in the active set")
    r = res[firing_index]
    loc = int(r["loc"]); lk = locality_key(w.civ)
    exposed = np.flatnonzero((lk == loc) & w.health.alive)
    view = cascade_list(w, loc=loc)[[x["firing_index"] for x in cascade_list(w, loc=loc)].index(firing_index)]
    series = []
    if hist is not None:
        series = [{"day": d, "eff_identity_mean": e, "residues": n} for d, e, n in
                  hist.execute("SELECT day, eff_identity, residues FROM locality_daily WHERE loc=? AND day>=? ORDER BY day", (loc, int(r["day"]))).fetchall()]
    return {**view, "exposed_alive": int(exposed.size), "exposed_person_ids": [int(x) for x in w.civ.person_id[exposed[:1000]]],
            "downstream_locality_series": series}


def locality_view(w, hist, loc: int) -> dict:
    civ, h, life, fl = w.civ, w.health, w.life, w.flourishing
    lk = locality_key(civ); m = (lk == int(loc)) & h.alive
    if not m.any() and not (lk == int(loc)).any():
        raise NotFound(f"no locality {loc}")
    ci, ri, urb = split_key(loc); iso2 = country_codes()[ci]; prof = region_profile(iso2, ri)
    ep = getattr(w.chronicle, "cascade_episode_active", None) or set()
    out = {"id": int(loc), "name": locality_name(loc), "country": iso2, "continent": continent_of(iso2),
           "region": {"index": ri, "code": prof.code if prof else None, "name": prof.name if prof else None}, "urban": bool(urb),
           "is_city": bool(urb), "city_name": city_name(loc) if urb else None,
           "population_alive": int(m.sum()), "population_deceased_slots": int(((lk == int(loc)) & ~h.alive).sum()),
           "forces_mean": {f: round(float(civ.forces[m, k].mean()), 5) for k, f in enumerate(FORCES)} if m.any() else None,
           "unemployment": float((~life.employed[m] & life.in_lf[m]).sum() / max(int(life.in_lf[m].sum()), 1)) if m.any() else None,
           "deprived": float((life.deprivation[m] > 0.5).mean()) if m.any() else None,
           "hope": float(fl.hope[m].mean()) if m.any() and fl is not None else None,
           "episodes_open": [r for (r, L) in ep if L == int(loc)],
           "active_cascade_residues": len(cascade_list(w, loc=loc))}
    return out


def locality_population(w, loc: int, limit: int = 1000) -> dict:
    lk = locality_key(w.civ); idx = np.flatnonzero((lk == int(loc)) & w.health.alive)
    return {"locality": int(loc), "count": int(idx.size), "person_ids": [int(x) for x in w.civ.person_id[idx[:limit]]], "limit": limit}


def locality_force_history(hist, loc: int) -> list:
    if hist is None:
        return []
    rows = hist.execute("SELECT day,pop,f0,f1,f2,f3,f4,f5,f6,f7,eff_identity,hot_ic,hot_cs,residues FROM locality_daily WHERE loc=? ORDER BY day", (int(loc),)).fetchall()
    return [{"day": r[0], "pop": r[1], "forces": {f: r[2 + k] for k, f in enumerate(FORCES)}, "eff_identity": r[10],
             "episode_identity_collapse": bool(r[11]), "episode_collective_surge": bool(r[12]), "residues": r[13]} for r in rows]


def country_view(w, hist, iso2: str) -> dict:
    codes = country_codes()
    if iso2 not in codes:
        raise NotFound(f"no country {iso2}")
    ci = codes.index(iso2); civ, h, life, fl, g, cl, k = w.civ, w.health, w.life, w.flourishing, w.gov, w.climate, w.klass
    m = (civ.country == ci) & h.alive
    from earth1.genesis import GENESIS_COUNTRIES
    from earth1.regions import get_regions
    lk = locality_key(civ); u = np.unique(lk[m])
    out = {"iso2": iso2, "name": GENESIS_COUNTRIES[ci]["name"], "continent": continent_of(iso2),
           "population_alive": int(m.sum()), "deceased_slots": int(((civ.country == ci) & ~h.alive).sum()),
           "regions": [{"index": j, "code": r.code, "name": r.name, "population_share": r.population_share, "economic_type": r.economic_type,
                        "geographic_type": r.geographic_type} for j, r in enumerate(get_regions(iso2))],
           "localities": [int(x) for x in u],
           "government": {"tax": float(g.tax[ci]), "welfare": float(g.welfare[ci]), "policing": float(g.policing[ci]), "legitimacy": float(g.legitimacy[ci]),
                          "at_war_with": (codes[int(g.at_war_with[ci])] if g.at_war_with[ci] >= 0 else None), "war_days": float(g.war_days[ci]),
                          "unrest": float(g.unrest_norm[ci]), "deprivation_norm": float(g.dep_norm[ci])},
           "climate": ({"baseline_temp": float(cl.baseline_temp[ci]), "anomaly": float(cl.anomaly[ci]), "soil": float(cl.soil[ci]), "farm_share": float(cl.farm_share[ci]),
                        "storm_days": float(cl.storm_days[ci]), "comfort": float(cl.comfort[ci])} if cl is not None else None)}
    if m.any():
        out.update({"forces_mean": {f: round(float(civ.forces[m, kk].mean()), 5) for kk, f in enumerate(FORCES)},
                    "unemployment": float((~life.employed[m] & life.in_lf[m]).sum() / max(int(life.in_lf[m].sum()), 1)),
                    "deprived": float((life.deprivation[m] > 0.5).mean()), "homeless": float(k.homeless[m].mean()),
                    "hope": float(fl.hope[m].mean()) if fl is not None else None, "mean_knowledge": float(w.knowledge.stock[m].mean()),
                    "wealth_gini": _gini(life.wealth[m])})
    out["mortality"] = country_mortality(w, hist, iso2)
    return out


def country_flows(hist, iso2: str) -> list:
    if hist is None:
        return []
    rows = hist.execute("SELECT day, alive, unemployment, deprived, hope, fear, wages, subsistence, rent, durables, wealth FROM country_daily WHERE iso2=? ORDER BY day", (iso2,)).fetchall()
    return [dict(zip(("day", "alive", "unemployment", "deprived", "hope", "fear", "wages", "subsistence", "rent", "durables", "wealth"), r)) for r in rows]


def country_mortality(w, hist, iso2: str) -> dict:
    codes = country_codes(); ci = codes.index(iso2); civ, h = w.civ, w.health
    dead = (civ.country == ci) & ~h.alive
    causes = {}
    for c in h.cause_of_death[dead]:
        causes[_cause(c)] = causes.get(_cause(c), 0) + 1
    out = {"iso2": iso2, "deceased_slots_now": int(dead.sum()), "by_cause_now": causes}
    if hist is not None:
        # slots never change country (rebirth inherits it), so the
        # country's recorded deaths are the deaths on its slots
        slots = np.flatnonzero(civ.country == ci)
        hist.execute("CREATE TEMP TABLE IF NOT EXISTS _slots(slot INTEGER PRIMARY KEY)")
        hist.execute("DELETE FROM _slots")
        hist.executemany("INSERT INTO _slots VALUES (?)", [(int(x),) for x in slots])
        rows = hist.execute("SELECT json_extract(detail,'$.cause') c, COUNT(*) FROM person_events "
                            "WHERE kind='died' AND slot IN (SELECT slot FROM _slots) GROUP BY c").fetchall()
        out["deaths_recorded_by_cause"] = {c: n for c, n in rows}
        out["deaths_recorded"] = int(sum(n for _, n in rows))
    return out


def firms(w, iso2: Optional[str] = None, limit: int = 500) -> list:
    life = w.life; codes = country_codes()
    emp = np.bincount(life.firm[(life.firm >= 0) & w.health.alive], minlength=life.firm_health.size)
    out = []
    for f in range(life.firm_health.size):
        c = codes[int(life.firm_country[f])]
        if iso2 and c != iso2:
            continue
        out.append({"id": f, "country": c, "health": float(life.firm_health[f]), "employees": int(emp[f])})
        if len(out) >= limit:
            break
    return out


def firm_view(w, fid: int, hist=None) -> dict:
    life = w.life
    if not (0 <= fid < life.firm_health.size):
        raise NotFound(f"no firm {fid}")
    m = (life.firm == fid) & w.health.alive
    return {"id": int(fid), "country": country_codes()[int(life.firm_country[fid])], "health": float(life.firm_health[fid]),
            "employees": int(m.sum()), "employee_person_ids": [int(x) for x in w.civ.person_id[np.flatnonzero(m)[:1000]]],
            "payroll_daily": float((life.wage[m]).sum()), "mean_tenure_days": float(life.tenure[m].mean()) if m.any() else None}


def world_summary(w, identity) -> dict:
    civ, h, life, fl, k, kn, g = w.civ, w.health, w.life, w.flourishing, w.klass, w.knowledge, w.gov
    alive = h.alive
    lk = locality_key(civ)
    return {"identity": identity, "day": int(w.day), "population": int(civ.n), "alive": int(alive.sum()), "deceased_slots": int((~alive).sum()),
            "persons_ever": int(civ.person_counter),
            "unemployment": float((~life.employed & life.in_lf)[alive].sum() / max(int(life.in_lf[alive].sum()), 1)),
            "deprived": float((life.deprivation > 0.5)[alive].mean()), "homeless": float(k.homeless[alive].mean()),
            "forces_mean": {f: round(float(civ.forces[alive, i].mean()), 5) for i, f in enumerate(FORCES)},
            "flourishing": {n: round(float(getattr(fl, n)[alive].mean()), 4) for n in ("hope", "meaning", "belonging", "satisfaction", "hunger", "thirst")} if fl is not None else None,
            "knowledge": {"mean_stock": float(kn.stock[alive].mean()), "global_stock": float(kn.global_stock), "living_works": float(kn.living_works)},
            "countries_at_war": int((g.at_war_with >= 0).sum() // 2), "countries": len(country_codes()),
            "localities_occupied": int(np.unique(lk[alive]).size), "cities": int(np.unique(lk[alive & civ.urban]).size),
            "memories_standing": len(w.chronicle.events), "cascade_residues_active": len(getattr(w.chronicle, "cascade_residues", None) or []),
            "episodes_open": len(getattr(w.chronicle, "cascade_episode_active", None) or ()),
            "wealth_gini": _gini(life.wealth[alive])}


def physics_view() -> dict:
    from earth1.alive import PHYSICS_VERSION, CANONICAL_DAY, EPISODE_ENTRY_RULES
    from earth1.thresholds import TRANSITION_RULES
    from earth1.legacy_gate import PRODUCTION
    return {"physics_version": PHYSICS_VERSION, "canonical_day": dict(CANONICAL_DAY),
            "cascade_rules": [{"name": r.name, "conditions": [(f.name.lower(), op, t) for f, op, t in r.conditions], "effects": r.effects,
                               "cooldown_days": r.cooldown_days, "decay_half_life": r.decay_half_life,
                               "semantics": "episode-entry" if r.name in EPISODE_ENTRY_RULES else "level+cooldown"} for r in TRANSITION_RULES],
            "production_modules": sorted(PRODUCTION),
            "step_order": ["govern", "policy_and_war", "advance_age", "life_tick", "health_tick", "class_tick", "rehome", "knowledge_tick", "weather_tick",
                           "flourishing_tick", "life_force_target", "propagate (dyadic, living view)", "contagion", "mobility", "feed", "relax", "conviction",
                           "plasticity", "memory", "cascade (episode-entry for identity rules)", "feedback", "posthumous restore", "births"]}


def _gini(x):
    x = np.sort(np.asarray(x, float)); n = x.size
    if n == 0 or x.sum() <= 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))
