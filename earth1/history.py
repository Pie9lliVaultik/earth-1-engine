"""HISTORY — the append-only record the API reads for anything "over
time" (API-COMPLETE-1, 2026-08-23). Pure observation: the recorder
reads the World after a tick and writes; nothing in the dynamics reads
it. One SQLite file per world home (`history.sqlite`), or ':memory:'
for a branch.

Tables
  person_events   (day, person_id, slot, kind, detail)   discrete life events
  force_samples   (day, person_id, slot, f0..f7, alpha)  every SAMPLE_EVERY days
  locality_daily  (day, loc, pop, f0..f7 means, eff_identity, hot_ic, hot_cs, residues)
  country_daily   (day, iso2, alive, unemployment, deprived, hope, fear,
                   wages, subsistence, rent, durables, wealth)   the flow ledger
  cascades        (id, day, rule, loc, effects, half_life)
  memories        (id, day, label, origin, scope_n, signature)
Event kinds: born, died:<cause>, hired:<firm>, lost_job, firm_changed:<firm>,
illness_onset:<disease>, recovered, migrated:<loc>, homeless, housed,
evicted, widowed, life:<code name>, reborn_slot.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np

SAMPLE_EVERY = 30
FORCE_COLS = [f"f{i}" for i in range(8)]
_SCHEMA = """
CREATE TABLE IF NOT EXISTS person_events(day INTEGER, person_id INTEGER, slot INTEGER, kind TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS pe_pid ON person_events(person_id);
CREATE INDEX IF NOT EXISTS pe_day ON person_events(day);
CREATE TABLE IF NOT EXISTS force_samples(day INTEGER, person_id INTEGER, slot INTEGER,
  f0 REAL,f1 REAL,f2 REAL,f3 REAL,f4 REAL,f5 REAL,f6 REAL,f7 REAL, alpha REAL);
CREATE INDEX IF NOT EXISTS fs_pid ON force_samples(person_id);
CREATE TABLE IF NOT EXISTS locality_daily(day INTEGER, loc INTEGER, pop INTEGER,
  f0 REAL,f1 REAL,f2 REAL,f3 REAL,f4 REAL,f5 REAL,f6 REAL,f7 REAL, eff_identity REAL,
  hot_ic INTEGER, hot_cs INTEGER, residues INTEGER);
CREATE INDEX IF NOT EXISTS ld_loc ON locality_daily(loc);
CREATE TABLE IF NOT EXISTS country_daily(day INTEGER, iso2 TEXT, alive INTEGER, unemployment REAL,
  deprived REAL, hope REAL, fear REAL, wages REAL, subsistence REAL, rent REAL, durables REAL, wealth REAL);
CREATE INDEX IF NOT EXISTS cd_iso ON country_daily(iso2);
CREATE TABLE IF NOT EXISTS cascades(id INTEGER PRIMARY KEY, day INTEGER, rule TEXT, loc INTEGER, effects TEXT, half_life REAL);
CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, day REAL, label TEXT, origin TEXT, scope_n INTEGER, signature TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def open_history(home) -> sqlite3.Connection:
    path = ":memory:" if home in (None, ":memory:") else str(Path(home) / "history.sqlite")
    con = sqlite3.connect(path, check_same_thread=False)
    con.executescript(_SCHEMA)
    return con


class Recorder:
    """Keeps yesterday's discrete state to emit today's events."""

    def __init__(self, con: sqlite3.Connection):
        self.con = con
        self.prev = None
        # Recorder v2 (2026-08-26, founder ruling): a firing is stamped
        # with the PRE-increment day (alive.py writes residues before
        # w.day += 1), so day-equality against the post-tick w.day can
        # never match — that bug dropped every cascade row. Persistence
        # is now keyed by (day, rule, loc), which the cooldown makes
        # unique per firing; restarts and repeat records cannot
        # double-insert. cascade_floor = the day of this recorder's
        # first record: residues fired before attach are NOT
        # backfilled (they remain represented honestly by the tick
        # journals alone).
        self.seen_cascades = {(int(d), r, int(l)) for d, r, l in
                              con.execute("SELECT day, rule, loc FROM cascades")}
        self.cascade_floor = None
        self.seen_mem = {r[0] for r in con.execute("SELECT id FROM memories")}

    # ── discrete state snapshot ──────────────────────────────────────
    @staticmethod
    def _state(w):
        civ, life, h, k = w.civ, w.life, w.health, w.klass
        from earth1.geography import locality_key
        return dict(alive=h.alive.copy(), employed=life.employed.copy(),
                    firm=life.firm.copy(), condition=h.condition.copy(),
                    loc=locality_key(civ), homeless=k.homeless.copy(),
                    evicted=life.evicted.copy() if life.evicted is not None else np.zeros(civ.n, bool),
                    partner=(life.partner.copy() if getattr(life, "partner", None) is not None else np.full(civ.n, -1)),
                    pid=civ.person_id.copy(), n_events=life.n_events.copy(),
                    last_event=life.last_event.copy())

    def record(self, w, st: dict | None = None) -> dict:
        from earth1.alive import effective_forces
        from earth1.health import DISEASES
        from earth1.life import EVENT_CODES
        from earth1.geography import country_codes
        day = int(w.day)
        cur = self._state(w)
        civ, life, h = w.civ, w.life, w.health
        pid = cur["pid"]
        rows = []
        if self.prev is None:
            # first record: everyone alive is "observed" (no synthetic births)
            self.prev = cur
        else:
            p = cur
            q = self.prev
            born = p["alive"] & ~q["alive"]
            died = ~p["alive"] & q["alive"]
            reborn = p["alive"] & q["alive"] & (p["pid"] != q["pid"])
            for i in np.flatnonzero(born | reborn):
                rows.append((day, int(pid[i]), int(i), "born", json.dumps({"parent_id": int(civ.parent_id[i])})))
            for i in np.flatnonzero(died):
                rows.append((day, int(q["pid"][i]), int(i), "died", json.dumps({"cause": self._cause(h.cause_of_death[i], DISEASES)})))
            same = p["alive"] & q["alive"] & (p["pid"] == q["pid"])
            for i in np.flatnonzero(same & p["employed"] & ~q["employed"]):
                rows.append((day, int(pid[i]), int(i), "hired", json.dumps({"firm": int(p["firm"][i])})))
            for i in np.flatnonzero(same & ~p["employed"] & q["employed"]):
                rows.append((day, int(pid[i]), int(i), "lost_job", json.dumps({"firm": int(q["firm"][i])})))
            for i in np.flatnonzero(same & p["employed"] & q["employed"] & (p["firm"] != q["firm"])):
                rows.append((day, int(pid[i]), int(i), "firm_changed", json.dumps({"from": int(q["firm"][i]), "to": int(p["firm"][i])})))
            for i in np.flatnonzero(same & (p["condition"] > 0) & (q["condition"] == 0)):
                rows.append((day, int(pid[i]), int(i), "illness_onset", json.dumps({"disease": self._cause(p["condition"][i], DISEASES)})))
            for i in np.flatnonzero(same & (p["condition"] == 0) & (q["condition"] > 0)):
                rows.append((day, int(pid[i]), int(i), "recovered", json.dumps({"disease": self._cause(q["condition"][i], DISEASES)})))
            for i in np.flatnonzero(same & (p["loc"] != q["loc"])):
                rows.append((day, int(pid[i]), int(i), "migrated", json.dumps({"from": int(q["loc"][i]), "to": int(p["loc"][i])})))
            for i in np.flatnonzero(same & p["homeless"] & ~q["homeless"]):
                rows.append((day, int(pid[i]), int(i), "homeless", "{}"))
            for i in np.flatnonzero(same & ~p["homeless"] & q["homeless"]):
                rows.append((day, int(pid[i]), int(i), "housed", "{}"))
            for i in np.flatnonzero(same & p["evicted"] & ~q["evicted"]):
                rows.append((day, int(pid[i]), int(i), "evicted", "{}"))
            for i in np.flatnonzero(same & (p["partner"] < 0) & (q["partner"] >= 0)):
                rows.append((day, int(pid[i]), int(i), "widowed", json.dumps({"partner_id": int(q["pid"][q["partner"][i]])})))
            for i in np.flatnonzero(same & (p["n_events"] > q["n_events"])):
                rows.append((day, int(pid[i]), int(i), "life", json.dumps({"event": EVENT_CODES.get(int(p["last_event"][i]), str(int(p["last_event"][i])))})))
            self.prev = cur
        if rows:
            self.con.executemany("INSERT INTO person_events VALUES (?,?,?,?,?)", rows)
        # force samples
        if day % SAMPLE_EVERY == 0:
            alive_idx = np.flatnonzero(h.alive)
            F = civ.forces[alive_idx]
            self.con.executemany("INSERT INTO force_samples VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                 [(day, int(pid[i]), int(i), *map(float, F[k]), float(civ.alpha[i])) for k, i in enumerate(alive_idx)])
        # locality daily
        from earth1.geography import locality_key
        loc = cur["loc"]; alive = h.alive
        eff = np.asarray(effective_forces(w))
        u, inv = np.unique(loc[alive], return_inverse=True)
        pop = np.bincount(inv)
        means = np.vstack([np.bincount(inv, weights=civ.forces[alive][:, k]) / pop for k in range(8)]).T
        eff_id = np.bincount(inv, weights=eff[alive][:, 4]) / pop
        ep = getattr(w.chronicle, "cascade_episode_active", None) or set()
        res = getattr(w.chronicle, "cascade_residues", None) or []
        res_count = {}
        for r_ in res:
            res_count[r_["loc"]] = res_count.get(r_["loc"], 0) + 1
        self.con.executemany("INSERT INTO locality_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                             [(day, int(L), int(pop[j]), *map(float, means[j]), float(eff_id[j]),
                               int(("identity_collapse", int(L)) in ep), int(("collective_surge", int(L)) in ep),
                               int(res_count.get(int(L), 0))) for j, L in enumerate(u)])
        # country daily (flow ledger)
        codes = country_codes(); c = civ.country
        rows_c = []
        for ci in np.unique(c[alive]):
            m = alive & (c == ci)
            lf = life.in_lf[m]
            rows_c.append((day, codes[ci], int(m.sum()),
                           float((~life.employed[m] & lf).sum() / max(int(lf.sum()), 1)),
                           float((life.deprivation[m] > 0.5).mean()),
                           float(w.flourishing.hope[m].mean()) if w.flourishing is not None else None,
                           float(civ.forces[m, 0].mean()),
                           float((life.wage[m] * life.employed[m]).sum()), float(life.cost[m].sum()),
                           float(life.rent[m].sum()) if life.rent is not None else 0.0,
                           float(life.durable_spend[m].sum()) if life.durable_spend is not None else 0.0,
                           float(life.wealth[m].sum())))
        self.con.executemany("INSERT INTO country_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows_c)
        # cascades: every not-yet-persisted residue at or after the
        # attach floor (see __init__; recorder v2)
        if self.cascade_floor is None:
            self.cascade_floor = day
        fresh = [r_ for r_ in res
                 if int(r_["day"]) >= self.cascade_floor
                 and (int(r_["day"]), r_["rule"], int(r_["loc"]))
                 not in self.seen_cascades]
        if fresh:
            self.con.executemany("INSERT INTO cascades(day,rule,loc,effects,half_life) VALUES (?,?,?,?,?)",
                                 [(int(r_["day"]), r_["rule"], int(r_["loc"]), json.dumps([float(x) for x in r_["effects"]]), float(r_["h"])) for r_ in fresh])
            self.seen_cascades.update(
                (int(r_["day"]), r_["rule"], int(r_["loc"])) for r_ in fresh)
        for m_ in w.chronicle.events:
            if m_.id not in self.seen_mem:
                self.seen_mem.add(m_.id)
                self.con.execute("INSERT OR IGNORE INTO memories VALUES (?,?,?,?,?,?)",
                                 (m_.id, float(m_.day), m_.label, m_.origin, int(np.asarray(m_.scope).sum()) if m_.scope is not None else 0,
                                  json.dumps([float(x) for x in m_.force_signature])))
        self.con.execute("INSERT OR REPLACE INTO meta VALUES ('last_day', ?)", (str(day),))
        self.con.commit()
        return {"history_events": len(rows), "history_cascades": len(fresh)}

    @staticmethod
    def _cause(code, diseases):
        code = int(code)
        return diseases[code - 1] if 1 <= code <= len(diseases) else ("none" if code == 0 else f"cause_{code}")
