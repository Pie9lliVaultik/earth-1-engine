"""API-COMPLETE-1: every addressable entity answers, on the live Earth
and inside a branch; stable person ids survive rebirth; history is
queryable."""
import json
import os
import uuid

import numpy as np
import pytest


@pytest.fixture(scope="module")
def home(tmp_path_factory):
    d = tmp_path_factory.mktemp("alive")
    os.environ["EARTH1_ALIVE_HOME"] = str(d)
    os.environ["EARTH1_RATE_LIMIT"] = "100000"        # the product limiter is not under test here
    from earth1.alive import birth_world, live_one_day
    from earth1 import persistence
    from earth1.history import open_history, Recorder
    from earth1.memory import Memory
    w = birth_world(2500, 21); rng = np.random.default_rng(21)
    rec = Recorder(open_history(d)); rec.record(w)
    # a memory and some deaths so every family of record has rows
    sig = np.zeros(8); sig[0] = 1.0
    scope = np.zeros(w.civ.n, bool); scope[:300] = True
    w.chronicle.remember(Memory(id="m-test", label="test shock", day=0.0, force_signature=sig, scope=scope))
    for d_ in range(35):
        if d_ == 3:
            w.health.alive[:20] = False; w.health.cause_of_death[:20] = 2
        st = live_one_day(w, rng); rec.record(w, st)
    rec.con.close()
    meta = persistence.save_world(w, d / "world.pkl", rng=rng)
    ep = {"epoch": 9, "world_uuid": str(uuid.uuid4()), "seed": 21, "physics_version": "test"}
    (d / "EPOCH.json").write_text(json.dumps(ep))
    (d / "state.json").write_text(json.dumps({"day": w.day, "sha256": meta["sha256"], "epoch": 9, "world_uuid": ep["world_uuid"]}))
    from earth1.api import deps
    deps._world = None; deps._identity = None; deps._history = None
    deps.ALIVE_HOME = d
    return d


@pytest.fixture(scope="module")
def client(home):
    from fastapi.testclient import TestClient
    from earth1.api.main import app
    return TestClient(app)


def _ok(c, url, **kw):
    r = c.get(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def test_identity_and_physics(client):
    e = _ok(client, "/epochs/current"); assert e["epoch"]["epoch"] == 9
    assert _ok(client, "/snapshots/current")["identity"]["world_uuid"]
    p = _ok(client, "/physics"); assert p["physics_version"] and len(p["cascade_rules"]) == 5


def test_geography(client):
    c = _ok(client, "/continents"); assert {x["name"] for x in c["continents"]} >= {"Africa", "Asia", "Europe"}
    _ok(client, "/continents/Asia")
    cs = _ok(client, "/countries"); assert len(cs["countries"]) == 194
    iso = next(x["iso2"] for x in cs["countries"] if x["population_alive"] >= 8)
    cv = _ok(client, f"/countries/{iso}"); assert cv["regions"] and cv["government"] and cv["localities"]
    _ok(client, f"/countries/{iso}/regions"); _ok(client, f"/regions/{iso}/0")
    _ok(client, f"/countries/{iso}/localities"); _ok(client, f"/countries/{iso}/needs")
    fl = _ok(client, f"/countries/{iso}/flows"); assert len(fl["series"]) >= 30
    _ok(client, f"/countries/{iso}/mortality")
    locs = _ok(client, "/localities"); L = locs["localities"][0]["id"]
    lv = _ok(client, f"/localities/{L}"); assert lv["population_alive"] > 0
    _ok(client, f"/localities/{L}/population"); _ok(client, f"/localities/{L}/cascades"); _ok(client, f"/localities/{L}/events")
    h = _ok(client, f"/localities/{L}/forces/history"); assert len(h["series"]) >= 30
    cities = _ok(client, "/cities"); assert cities["count"] > 0
    _ok(client, f"/cities/{cities['cities'][0]['id']}")
    assert client.get(f"/cities/{L - (L % 2)}").status_code in (200, 404)


def test_earthling_surfaces(client):
    lst = _ok(client, "/earthlings", params={"limit": 50, "offset": 100}); pid = lst["earthlings"][0]["person_id"]
    e = _ok(client, f"/earthlings/{pid}")
    for k in ("identity", "demographics", "traits", "forces", "work", "health", "needs", "housing", "social", "knowledge", "presence"):
        assert k in e
    assert e["forces"]["stored"] and e["forces"]["effective"]
    for sub in ("status", "history", "forces", "forces/history", "memories", "events", "relationships", "family", "work",
                "work/history", "health", "health/history", "consumption", "consumption/history", "needs", "presence"):
        _ok(client, f"/earthlings/{pid}/{sub}")
    fh = _ok(client, f"/earthlings/{pid}/forces/history"); assert len(fh["samples"]) >= 2
    rel = _ok(client, f"/earthlings/{pid}/relationships", params={"scope": "living"}); assert all(t["alive"] for t in rel["ties"])
    _ok(client, f"/social-graph/{pid}/ego", params={"depth": 2})
    hh = e["social"]["household_id"]; _ok(client, f"/households/{hh}")
    _ok(client, f"/earthlings/slot/{e['identity']['slot']}")
    assert client.get("/earthlings/999999999").status_code == 404
    # the deceased are addressable
    dead = _ok(client, "/earthlings", params={"alive": False, "limit": 3})
    assert dead["total"] > 0
    ds = _ok(client, f"/earthlings/{dead['earthlings'][0]['person_id']}/status")
    assert ds["status"] == "deceased" and ds["cause_of_death"]


def test_memories_cascades_firms(client):
    m = _ok(client, "/memories"); assert any(x["id"] == "m-test" for x in m["standing"])
    imp = _ok(client, "/memories/m-test/impacts"); assert imp["carriers"] > 0 and imp["localities"]
    _ok(client, "/cascades"); _ok(client, "/cascades/history")
    f = _ok(client, "/firms", params={"limit": 5}); fid = f["firms"][0]["id"]
    _ok(client, f"/firms/{fid}"); _ok(client, f"/firms/{fid}/employees")


def test_stable_person_id_across_rebirth():
    from earth1.alive import birth_world, live_one_day
    w = birth_world(2000, 33); rng = np.random.default_rng(33)
    victims = np.flatnonzero(w.health.alive)[:30]
    old_ids = w.civ.person_id[victims].copy()
    w.health.alive[victims] = False
    for _ in range(80):
        live_one_day(w, rng)
    reborn = victims[w.health.alive[victims]]
    assert reborn.size > 0
    assert (w.civ.person_id[reborn] >= 2000).all()            # fresh ids
    gone = old_ids[w.health.alive[victims]]                  # ids of the reborn slots' previous occupants
    assert not np.isin(gone, w.civ.person_id).any()           # never reused
    assert (w.civ.parent_id[reborn] >= 0).all()
    assert w.civ.person_counter == 2000 + int((w.civ.person_id >= 2000).sum())


def test_branches(client):
    r = client.post("/branches", json={"scenario": {"id": "fear", "forces": {"fear": 0.2}, "persists_days": 5}, "seed": 5})
    assert r.status_code == 200, r.text; bid = r.json()["id"]
    assert bid in {b["id"] for b in _ok(client, "/branches")["branches"]}
    m = client.post(f"/branches/{bid}/advance", params={"days": 3}).json(); assert m["days_advanced"] == 3
    cmp_ = _ok(client, f"/branches/{bid}/compare"); assert cmp_["comparable_persons"] > 0 and cmp_["branch_day"] == cmp_["control_day"] + 3
    pid = _ok(client, "/earthlings", params={"limit": 1})["earthlings"][0]["person_id"]
    be = _ok(client, f"/branches/{bid}/earthlings/{pid}"); assert be["branch"]["id"] == bid
    _ok(client, f"/branches/{bid}/earthlings/{pid}/forces"); _ok(client, f"/branches/{bid}/earthlings/{pid}/history")
    _ok(client, f"/branches/{bid}/world"); _ok(client, f"/branches/{bid}/cascades"); _ok(client, f"/branches/{bid}/memories")
    iso = be["demographics"]["country"]; _ok(client, f"/branches/{bid}/countries/{iso}")
    L = be["demographics"]["locality"]["id"]; _ok(client, f"/branches/{bid}/localities/{L}")
    h = _ok(client, f"/branches/{bid}/localities/{L}/forces/history"); assert len(h["series"]) == 4
    _ok(client, f"/branches/{bid}/history")
    # the live world is untouched by the branch
    live_day = _ok(client, "/world")["identity"]["world_day"]; assert live_day == cmp_["control_day"]
    assert client.delete(f"/branches/{bid}").status_code == 200
    assert client.get(f"/branches/{bid}").status_code == 404


def test_openapi_lists_everything(client):
    spec = _ok(client, "/openapi.json"); paths = set(spec["paths"])
    for p in ("/earthlings/{person_id}", "/earthlings/{person_id}/forces/history", "/countries/{iso2}", "/localities/{loc}",
              "/cities/{loc}", "/continents/{name}", "/memories/{mid}/impacts", "/cascades/{firing_index}/impacts",
              "/branches", "/branches/{bid}/advance", "/branches/{bid}/compare", "/branches/{bid}/earthlings/{person_id}",
              "/epochs/current", "/snapshots/current", "/physics", "/firms/{fid}", "/households/{hid}"):
        assert p in paths, p


def test_history_coverage_and_historical_person(client):
    h = _ok(client, "/earthlings", params={"limit": 1, "offset": 100})["earthlings"][0]["person_id"]
    r = _ok(client, f"/earthlings/{h}/forces/history")
    cov = r["coverage"]; assert cov["history_available"] and cov["history_available_from_day"] == 0 and cov["force_sampling_interval_days"] == 30
    assert cov["force_samples_are_continuous"] is False and cov["backfilled"] is False
    # a person whose slot was reused is still addressable from the record
    import sqlite3, os
    from earth1.api import deps
    con = sqlite3.connect(str(deps.ALIVE_HOME / "history.sqlite"))
    gone = [p for (p,) in con.execute("SELECT person_id FROM person_events WHERE kind='died'")]
    from earth1.api.deps import get_world
    w, _ = get_world()
    import numpy as np
    reused = [p for p in gone if not (w.civ.person_id == p).any()]
    if reused:
        hp = _ok(client, f"/earthlings/{reused[0]}")
        assert hp["status"] == "historical" and hp["cause_of_death"] and hp["events"]
    assert client.get("/earthlings/777777777").status_code == 404
