"""Review M01b regression — ONE age convention everywhere.

The external review (EXTERNAL_REVIEW_VERIFICATION_2026-09-08, M01b)
found FOUR age scales at a=0.5: engine 18+72a=54.0y (canonical,
generational._age_years), profile readout 18+82a=59.0y
(api/readouts.py, api/routes/civilization.py), model filter
87.6a=43.8y (models.select_population), answer cohort 100a=50.0y
(answer_living.py). This file reproduces the review probe
(review_verify/m01_probe.py) and asserts every interface now reads the
canonical years, and that boundary predicates (65+, under-30) select
the SAME person set through models.select_population and the
civilization route filters.
"""
import copy
import json
import os
import types
import uuid

import numpy as np
import pytest

A_HALF = 0.5           # probe agent: canonical years = 18 + 72*0.5
CANON_YEARS = 54.0


def _stub_world(age):
    civ = types.SimpleNamespace(age=np.array([age]), country=np.array([0]))
    health = types.SimpleNamespace(alive=np.array([True]))
    return types.SimpleNamespace(civ=civ, health=health, life=None)


# ── the canonical scale itself ─────────────────────────────────────
def test_engine_scale_is_18_plus_72a():
    from earth1.generational import _age_years
    assert float(_age_years(types.SimpleNamespace(
        age=np.array([A_HALF])))[0]) == pytest.approx(CANON_YEARS)


# ── one world, served everywhere ───────────────────────────────────
@pytest.fixture(scope="module")
def api_home(tmp_path_factory, _tiny_template):
    """The tiny world, with slot 0 pinned to a=0.5, saved as the
    canonical snapshot the API serves (test_api_complete pattern)."""
    d = tmp_path_factory.mktemp("age_home")
    os.environ["EARTH1_ALIVE_HOME"] = str(d)
    os.environ["EARTH1_RATE_LIMIT"] = "100000"
    from earth1 import persistence
    from earth1.alive import live_one_day
    w = copy.deepcopy(_tiny_template)
    rng = np.random.default_rng(3)
    for _ in range(2):     # populate tick-born life fields (durables…)
        live_one_day(w, rng)
    w.civ.age[0] = A_HALF
    w.health.alive[0] = True
    meta = persistence.save_world(w, d / "world.pkl",
                                  rng=np.random.default_rng(1))
    ep = {"epoch": 1, "world_uuid": str(uuid.uuid4()), "seed": 42,
          "physics_version": "test"}
    (d / "EPOCH.json").write_text(json.dumps(ep))
    (d / "state.json").write_text(json.dumps(
        {"day": w.day, "sha256": meta["sha256"], "epoch": 1,
         "world_uuid": ep["world_uuid"]}))
    from earth1.api import deps
    deps._world = None; deps._identity = None; deps._history = None
    deps.ALIVE_HOME = d
    return d, w


@pytest.fixture(scope="module")
def client(api_home):
    from fastapi.testclient import TestClient
    from earth1.api.main import app
    return TestClient(app)


def test_profile_readout_reads_engine_scale(api_home):
    from earth1.api import readouts as R
    _, w = api_home
    prof = R.earthling(w, None, 0)
    assert prof["demographics"]["age_years"] == pytest.approx(CANON_YEARS)


def test_earthling_route_reads_engine_scale(api_home, client):
    _, w = api_home
    pid = int(w.civ.person_id[0])
    r = client.get(f"/earthlings/{pid}")
    assert r.status_code == 200
    assert r.json()["demographics"]["age_years"] == pytest.approx(CANON_YEARS)
    # and through the list filter's own age_y column
    r = client.get("/earthlings", params={"min_age": 53.9, "max_age": 54.1,
                                          "limit": 5000})
    rows = r.json()["earthlings"]
    assert any(e["person_id"] == pid for e in rows)
    assert all(e["age_years"] == pytest.approx(CANON_YEARS, abs=0.11)
               for e in rows)


def test_household_route_reads_engine_scale(api_home, client):
    from earth1.generational import _age_years
    _, w = api_home
    hid = int(w.fabric.household[0])
    r = client.get(f"/households/{hid}")
    assert r.status_code == 200
    yrs = _age_years(w.civ)
    for m in r.json()["members"]:
        assert m["age_years"] == pytest.approx(
            round(float(yrs[m["slot"]]), 1))


def test_boundary_predicates_select_same_person_set(api_home, client):
    """65+ and under-30 pick the SAME people through
    models.select_population and the /earthlings age filters."""
    from earth1.models import select_population
    _, w = api_home
    for pred, params in ((([65.0, 500.0]), {"min_age": 65.0}),
                         (([0.0, 30.0]), {"max_age": 30.0})):
        mask = select_population(w, {"age": pred})
        ids_model = {int(p) for p in w.civ.person_id[mask]}
        assert 0 < len(ids_model) <= 5000
        r = client.get("/earthlings", params={**params, "limit": 5000})
        body = r.json()
        assert body["total"] == len(ids_model)
        assert {e["person_id"] for e in body["earthlings"]} == ids_model


# ── model filter: canonical default, legacy env still honoured ─────
def test_select_population_default_is_canonical(monkeypatch):
    monkeypatch.delenv("EARTH1_AGE_SCALE_YEARS", raising=False)
    from earth1.models import select_population
    w = _stub_world(A_HALF)
    assert bool(select_population(w, {"age": [54.0, 54.0]})[0])
    # the review's 87.6-scale reading (43.8y at a=0.5) must be gone
    assert not bool(select_population(w, {"age": [43.8, 43.8]})[0])


def test_select_population_env_override_still_works(monkeypatch):
    from earth1.models import select_population
    monkeypatch.setenv("EARTH1_AGE_SCALE_YEARS", "87.6")
    w = _stub_world(A_HALF)
    assert bool(select_population(w, {"age": [43.8, 43.8]})[0])
    assert not bool(select_population(w, {"age": [54.0, 54.0]})[0])


# ── answer cohorts: bucket by canonical years ──────────────────────
def test_answer_cohorts_bucket_by_engine_years(tiny_world):
    """a=0.2 is 32.4 canonical years -> '30 to 55'. The old age*100
    read it as 20y and bucketed the same person 'under 30'."""
    from earth1.answer_living import readout
    w = tiny_world
    w.civ.age[:] = 0.2
    out = readout(w, np.eye(8)[0])
    alive = int(w.health.alive.sum())
    assert out["by_cohort"]["30 to 55"]["n"] == alive
    assert "under 30" not in out["by_cohort"]
    assert "over 55" not in out["by_cohort"]
