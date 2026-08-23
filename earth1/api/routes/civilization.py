"""THE ADDRESSABLE CIVILIZATION — API-COMPLETE-1 (2026-08-23).
Every entity Earth-1 models, by id, on the live canonical Earth.
Read-only; every response carries the world identity."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from earth1.api import readouts as R
from earth1.api.deps import get_world, get_history

router = APIRouter(tags=["civilization"])


def _nf(fn, *a, **k):
    try:
        return fn(*a, **k)
    except R.NotFound as e:
        raise HTTPException(404, str(e))


def _slot(w, person_id: int) -> int:
    return _nf(R.slot_of, w, person_id)


# ── identity / metadata ───────────────────────────────────────────
@router.get("/epochs/current")
def epoch_current():
    """The live epoch: uuid, seed, genesis hash, physics, born_at."""
    import json
    from earth1.api.deps import ALIVE_HOME
    w, identity = get_world()
    ep = {}
    try:
        ep = json.loads((ALIVE_HOME / "EPOCH.json").read_text())
    except (OSError, ValueError):
        pass
    return {"identity": identity, "epoch": ep, "policy": "ops/alive/EPOCH_POLICY.md"}


@router.get("/snapshots/current")
def snapshot_current():
    """The snapshot every surface is serving right now."""
    _, identity = get_world()
    return {"identity": identity}


@router.get("/physics")
def physics():
    """Physics version, canonical parameters, cascade rules, step order, production modules."""
    _, identity = get_world()
    return {"identity": identity, **R.physics_view()}


# ── geography ─────────────────────────────────────────────────────
@router.get("/continents")
def continents():
    w, identity = get_world()
    import numpy as np
    codes = R.country_codes(); alive = w.health.alive
    out = []
    for c in R.CONTINENTS:
        cis = [i for i, code in enumerate(codes) if R.CONTINENT[code] == c]
        m = np.isin(w.civ.country, cis) & alive
        out.append({"name": c, "countries": [codes[i] for i in cis], "population_alive": int(m.sum()),
                    "forces_mean": {f: round(float(w.civ.forces[m, k].mean()), 5) for k, f in enumerate(R.FORCES)} if m.any() else None})
    return {"identity": identity, "continents": out}


@router.get("/continents/{name}")
def continent(name: str):
    w, identity = get_world()
    import numpy as np
    if name not in R.CONTINENTS:
        raise HTTPException(404, f"no continent {name}; one of {R.CONTINENTS}")
    codes = R.country_codes(); cis = [i for i, code in enumerate(codes) if R.CONTINENT[code] == name]
    m = np.isin(w.civ.country, cis) & w.health.alive
    return {"identity": identity, "name": name, "countries": [R.country_view(w, None, codes[i]) | {"regions": None} for i in cis],
            "population_alive": int(m.sum())}


@router.get("/countries")
def countries_list():
    w, identity = get_world()
    import numpy as np
    codes = R.country_codes(); alive = w.health.alive
    cnt = np.bincount(w.civ.country[alive], minlength=len(codes))
    return {"identity": identity, "countries": [{"iso2": c, "continent": R.continent_of(c), "population_alive": int(cnt[i])} for i, c in enumerate(codes)]}


@router.get("/countries/{iso2}")
def country(iso2: str):
    w, identity = get_world()
    return {"identity": identity, **_nf(R.country_view, w, get_history(), iso2.upper())}


@router.get("/countries/{iso2}/regions")
def country_regions(iso2: str):
    w, identity = get_world()
    v = _nf(R.country_view, w, None, iso2.upper())
    return {"identity": identity, "iso2": iso2.upper(), "regions": v["regions"]}


@router.get("/regions/{iso2}/{index}")
def region(iso2: str, index: int):
    w, identity = get_world()
    import numpy as np
    prof = R.region_profile(iso2.upper(), index)
    if prof is None:
        raise HTTPException(404, "no such region")
    ci = R.country_codes().index(iso2.upper())
    m = (w.civ.country == ci) & (w.civ.region == index) & w.health.alive
    return {"identity": identity, "iso2": iso2.upper(), "index": index, "code": prof.code, "name": prof.name,
            "population_share_genesis": prof.population_share, "historical_layers": list(prof.historical_layers),
            "economic_type": prof.economic_type, "economic_detail": prof.economic_detail, "geographic_type": prof.geographic_type,
            "force_deltas": dict(prof.force_deltas), "population_alive": int(m.sum()),
            "localities": [int(ci * 1000 + index * 2 + u) for u in (0, 1)]}


@router.get("/countries/{iso2}/localities")
def country_localities(iso2: str):
    w, identity = get_world()
    v = _nf(R.country_view, w, None, iso2.upper())
    return {"identity": identity, "iso2": iso2.upper(), "localities": [R.locality_view(w, None, L) for L in v["localities"]]}


@router.get("/countries/{iso2}/flows")
def country_flows(iso2: str):
    """The daily flow ledger: wages, subsistence, rent, durables, wealth, alive, unemployment…"""
    _, identity = get_world()
    return {"identity": identity, "iso2": iso2.upper(), "series": R.country_flows(get_history(), iso2.upper())}


@router.get("/countries/{iso2}/mortality")
def country_mortality(iso2: str):
    w, identity = get_world()
    return {"identity": identity, **R.country_mortality(w, get_history(), iso2.upper())}


@router.get("/countries/{iso2}/needs")
def country_needs(iso2: str):
    w, identity = get_world()
    import numpy as np
    ci = R.country_codes().index(iso2.upper()); m = (w.civ.country == ci) & w.health.alive; fl = w.flourishing
    return {"identity": identity, "iso2": iso2.upper(), "population_alive": int(m.sum()),
            "needs_mean": {n: round(float(getattr(fl, n)[m].mean()), 4) for n in ("hunger", "thirst", "breath", "hope", "meaning", "belonging", "satisfaction")} if m.any() else None,
            "deprived": float((w.life.deprivation[m] > 0.5).mean()) if m.any() else None,
            "food_system": R.needs(w, int(np.flatnonzero(m)[0]))["country_food_system"] if m.any() else None}


@router.get("/localities")
def localities(limit: int = 2000):
    w, identity = get_world()
    from earth1.geography import localities as _loc
    u, c = _loc(w)
    return {"identity": identity, "count": int(u.size),
            "localities": [{"id": int(L), "name": R.locality_name(int(L)), "population_alive": int(n), "urban": bool(int(L) % 2)} for L, n in zip(u[:limit], c[:limit])]}


@router.get("/localities/{loc}")
def locality(loc: int):
    w, identity = get_world()
    return {"identity": identity, **_nf(R.locality_view, w, get_history(), loc)}


@router.get("/localities/{loc}/population")
def locality_population(loc: int, limit: int = 1000):
    w, identity = get_world()
    return {"identity": identity, **R.locality_population(w, loc, limit)}


@router.get("/localities/{loc}/forces/history")
def locality_force_history(loc: int):
    _, identity = get_world()
    return {"identity": identity, "locality": loc, "series": R.locality_force_history(get_history(), loc)}


@router.get("/localities/{loc}/cascades")
def locality_cascades(loc: int):
    w, identity = get_world()
    return {"identity": identity, "locality": loc, "firings": R.cascade_list(w, loc=loc)}


@router.get("/localities/{loc}/events")
def locality_events(loc: int, limit: int = 500):
    """Person events recorded in this locality (by current residence) plus cascade firings."""
    w, identity = get_world()
    import numpy as np
    hist = get_history()
    idx = np.flatnonzero(R.locality_key(w.civ) == int(loc))
    ev = []
    if hist is not None and idx.size:
        hist.execute("CREATE TEMP TABLE IF NOT EXISTS _slots(slot INTEGER PRIMARY KEY)"); hist.execute("DELETE FROM _slots")
        hist.executemany("INSERT INTO _slots VALUES (?)", [(int(x),) for x in idx])
        ev = [{"day": d, "person_id": p, "kind": k, "detail": dt} for d, p, k, dt in hist.execute(
            "SELECT day, person_id, kind, detail FROM person_events WHERE slot IN (SELECT slot FROM _slots) ORDER BY day DESC LIMIT ?", (limit,)).fetchall()]
    return {"identity": identity, "locality": loc, "person_events": ev, "cascades": R.cascade_list(w, loc=loc)}


@router.get("/cities")
def cities(limit: int = 2000):
    w, identity = get_world()
    from earth1.geography import localities as _loc
    u, c = _loc(w)
    urb = [(int(L), int(n)) for L, n in zip(u, c) if int(L) % 2 == 1]
    return {"identity": identity, "count": len(urb), "definition": "a city is the urban locality of a genesis region",
            "cities": [{"id": L, "name": R.city_name(L), "country": R.country_codes()[L // 1000], "population_alive": n} for L, n in urb[:limit]]}


@router.get("/cities/{loc}")
def city(loc: int):
    w, identity = get_world()
    if int(loc) % 2 != 1:
        raise HTTPException(404, "not a city (rural locality)")
    return {"identity": identity, **_nf(R.locality_view, w, get_history(), loc)}


# ── earthlings ────────────────────────────────────────────────────
@router.get("/earthlings")
def earthlings(country: Optional[str] = None, locality: Optional[int] = None, alive: Optional[bool] = True,
               employed: Optional[bool] = None, min_age: Optional[float] = None, max_age: Optional[float] = None,
               limit: int = Query(200, le=5000), offset: int = 0):
    """List/search Earthlings by country, locality, alive, employment, age."""
    w, identity = get_world()
    import numpy as np
    m = np.ones(w.civ.n, bool)
    if alive is not None: m &= (w.health.alive == alive)
    if country: m &= (w.civ.country == R.country_codes().index(country.upper()))
    if locality is not None: m &= (R.locality_key(w.civ) == int(locality))
    if employed is not None: m &= (w.life.employed == employed)
    age_y = 18 + w.civ.age * 82
    if min_age is not None: m &= age_y >= min_age
    if max_age is not None: m &= age_y <= max_age
    idx = np.flatnonzero(m)[offset:offset + limit]
    return {"identity": identity, "total": int(m.sum()), "offset": offset, "limit": limit,
            "earthlings": [{"person_id": int(w.civ.person_id[i]), "slot": int(i), "country": R.country_codes()[int(w.civ.country[i])],
                            "age_years": round(float(age_y[i]), 1), "alive": bool(w.health.alive[i])} for i in idx]}


@router.get("/earthlings/{person_id}")
def earthling(person_id: int):
    w, identity = get_world()
    return {"identity": identity, **R.earthling(w, get_history(), _slot(w, person_id))}


@router.get("/earthlings/slot/{slot}")
def earthling_by_slot(slot: int):
    w, identity = get_world()
    if not (0 <= slot < w.civ.n):
        raise HTTPException(404, "no such slot")
    return {"identity": identity, **R.earthling(w, get_history(), slot)}


@router.get("/earthlings/{person_id}/status")
def earthling_status(person_id: int):
    w, identity = get_world()
    return {"identity": identity, **R.person_status(w, get_history(), _slot(w, person_id))}


@router.get("/earthlings/{person_id}/history")
def earthling_history(person_id: int, kind: Optional[str] = None):
    w, identity = get_world()
    _slot(w, person_id)
    return {"identity": identity, "person_id": person_id, "events": R.person_history(get_history(), person_id, kind)}


@router.get("/earthlings/{person_id}/forces")
def earthling_forces(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.forces(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/forces/history")
def earthling_force_history(person_id: int):
    w, identity = get_world()
    _slot(w, person_id)
    return {"identity": identity, "person_id": person_id, "samples": R.force_history(get_history(), person_id)}


@router.get("/earthlings/{person_id}/memories")
def earthling_memories(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, "memories": R.memories_for(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/events")
def earthling_events(person_id: int):
    """Everything that happened to this person: life events (history) and the memories/cascades acting on them now."""
    w, identity = get_world()
    s = _slot(w, person_id)
    return {"identity": identity, "person_id": person_id, "history": R.person_history(get_history(), person_id),
            "memories_now": R.memories_for(w, s), "cascades_now": R.cascade_list(w, loc=int(R.locality_key(w.civ)[s]))}


@router.get("/earthlings/{person_id}/relationships")
def earthling_relationships(person_id: int, scope: str = "all"):
    w, identity = get_world()
    return {"identity": identity, **R.relationships(w, _slot(w, person_id), scope)}


@router.get("/earthlings/{person_id}/family")
def earthling_family(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.family(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/work")
def earthling_work(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.work(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/work/history")
def earthling_work_history(person_id: int):
    w, identity = get_world()
    _slot(w, person_id)
    ev = [e for e in R.person_history(get_history(), person_id) if e["kind"] in ("hired", "lost_job", "firm_changed")]
    return {"identity": identity, "person_id": person_id, "events": ev}


@router.get("/earthlings/{person_id}/health")
def earthling_health(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.health(w, get_history(), _slot(w, person_id))}


@router.get("/earthlings/{person_id}/health/history")
def earthling_health_history(person_id: int):
    w, identity = get_world()
    _slot(w, person_id)
    ev = [e for e in R.person_history(get_history(), person_id) if e["kind"] in ("illness_onset", "recovered", "died")]
    return {"identity": identity, "person_id": person_id, "events": ev}


@router.get("/earthlings/{person_id}/consumption")
def earthling_consumption(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.consumption(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/consumption/history")
def earthling_consumption_history(person_id: int):
    """Wealth/conviction trajectory from the force samples plus work events — the person's material history."""
    w, identity = get_world()
    _slot(w, person_id)
    return {"identity": identity, "person_id": person_id, "samples": R.force_history(get_history(), person_id),
            "work_events": [e for e in R.person_history(get_history(), person_id) if e["kind"] in ("hired", "lost_job", "firm_changed", "homeless", "housed", "evicted")]}


@router.get("/earthlings/{person_id}/needs")
def earthling_needs(person_id: int):
    w, identity = get_world()
    return {"identity": identity, "person_id": person_id, **R.needs(w, _slot(w, person_id))}


@router.get("/earthlings/{person_id}/presence")
def earthling_presence(person_id: int):
    w, identity = get_world()
    s = _slot(w, person_id)
    return {"identity": identity, "person_id": person_id, **R.presence(w, s),
            "moves": [e for e in R.person_history(get_history(), person_id) if e["kind"] == "migrated"]}


@router.get("/social-graph/{person_id}/ego")
def social_graph_ego(person_id: int, depth: int = 1, living_only: bool = True):
    w, identity = get_world()
    return {"identity": identity, **R.ego(w, _slot(w, person_id), depth, living_only)}


@router.get("/households/{hid}")
def household(hid: int):
    w, identity = get_world()
    import numpy as np
    members = np.flatnonzero(w.fabric.household == int(hid))
    if members.size == 0:
        raise HTTPException(404, "no such household")
    return {"identity": identity, "id": hid, "members": [{"person_id": int(w.civ.person_id[j]), "slot": int(j), "alive": bool(w.health.alive[j]),
                                                          "age_years": round(18 + float(w.civ.age[j]) * 82, 1)} for j in members]}


# ── memories / cascades ───────────────────────────────────────────
@router.get("/memories")
def memories():
    w, identity = get_world()
    return {"identity": identity, "standing": [R.memory_view(w, m) for m in w.chronicle.events],
            "forgotten_total": int(w.chronicle.forgotten), "total_ever": int(w.chronicle.total_ever)}


@router.get("/memories/{mid}")
def memory(mid: str):
    w, identity = get_world()
    for m in w.chronicle.events:
        if m.id == mid:
            return {"identity": identity, **R.memory_view(w, m)}
    hist = get_history()
    if hist is not None:
        r = hist.execute("SELECT id, day, label, origin, scope_n, signature FROM memories WHERE id=?", (mid,)).fetchone()
        if r:
            return {"identity": identity, "id": r[0], "day": r[1], "label": r[2], "origin": r[3], "scope_n": r[4], "force_signature": r[5], "status": "forgotten (historical record)"}
    raise HTTPException(404, "no such memory")


@router.get("/memories/{mid}/impacts")
def memory_impacts(mid: str):
    w, identity = get_world()
    for m in w.chronicle.events:
        if m.id == mid:
            return {"identity": identity, **R.memory_impacts(w, m)}
    raise HTTPException(404, "no standing memory with that id")


@router.get("/cascades")
def cascades(rule: Optional[str] = None):
    w, identity = get_world()
    hist = get_history()
    recorded = int(hist.execute("SELECT COUNT(*) FROM cascades").fetchone()[0]) if hist is not None else None
    return {"identity": identity, "active_residues": R.cascade_list(w, rule=rule), "firings_recorded_all_time": recorded,
            "episodes_open": sorted([[r, int(L)] for (r, L) in (getattr(w.chronicle, "cascade_episode_active", None) or ())])}


@router.get("/cascades/{firing_index}/impacts")
def cascade_impacts(firing_index: int):
    w, identity = get_world()
    return {"identity": identity, **_nf(R.cascade_impact, w, get_history(), firing_index)}


@router.get("/cascades/history")
def cascade_history(loc: Optional[int] = None, limit: int = 1000):
    _, identity = get_world()
    hist = get_history()
    if hist is None:
        return {"identity": identity, "firings": []}
    q = "SELECT id, day, rule, loc, effects, half_life FROM cascades" + (" WHERE loc=?" if loc is not None else "") + " ORDER BY day DESC LIMIT ?"
    rows = hist.execute(q, ((loc, limit) if loc is not None else (limit,))).fetchall()
    return {"identity": identity, "firings": [{"id": r[0], "day": r[1], "rule": r[2], "locality": r[3], "effects": r[4], "half_life": r[5]} for r in rows]}


# ── firms ─────────────────────────────────────────────────────────
@router.get("/firms")
def firms(country: Optional[str] = None, limit: int = 500):
    w, identity = get_world()
    return {"identity": identity, "firms": R.firms(w, country.upper() if country else None, limit)}


@router.get("/firms/{fid}")
def firm(fid: int):
    w, identity = get_world()
    return {"identity": identity, **_nf(R.firm_view, w, fid)}


@router.get("/firms/{fid}/employees")
def firm_employees(fid: int):
    w, identity = get_world()
    v = _nf(R.firm_view, w, fid)
    return {"identity": identity, "id": fid, "employees": v["employees"], "person_ids": v["employee_person_ids"]}
