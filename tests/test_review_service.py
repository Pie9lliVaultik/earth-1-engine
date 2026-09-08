"""Serving-layer regressions for external review M02c, S03a, S02.

Reproduces the verification probes (review_verify/
probe_m02c_api_freeze_label.py and verify_m08_s01_s02_s03.py) as
committed tests and asserts the fixed behaviour:

  M02c — the served freeze tag derives from configstamp.stamp() instead
         of a hardcoded literal; a mismatched process serves
         'unfrozen-dev:<n>' and /health marks the physics stamp
         'degraded' after the startup-style check runs.
  S03a — _auth fails CLOSED on an empty EARTH1_API_KEYS allowlist (503)
         unless EARTH1_DEV_OPEN=1 explicitly enables anonymous dev use.
  S02  — async path bounded: EARTH1_MAX_JOBS semaphore (429 when full),
         TTL eviction of finished jobs, horizon/seed clamps.

In-process TestClient only — no network servers. Worlds are tiny fakes
behind a stubbed loader; no snapshots, no sealed paths are touched.
"""
import os
import sys
import threading
import time
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from earth1 import configstamp
from earth1.api import v1


# ---------------------------------------------------------------- fixtures

@pytest.fixture(autouse=True)
def _reset_v1_state(monkeypatch, tmp_path):
    """Fresh module state per test; question log confined to tmp."""
    monkeypatch.setattr(v1, "_stamp_state", None)
    monkeypatch.setattr(v1, "_worlds", {})
    monkeypatch.setattr(v1, "_jobs", {})
    monkeypatch.setattr(v1, "_jobs_running", 0)
    monkeypatch.setattr(v1, "_rate", {})
    monkeypatch.setattr(v1, "_cache", {})
    monkeypatch.setattr(v1, "QLOG", str(tmp_path / "qlog.jsonl"))


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(v1.router)
    return TestClient(app, raise_server_exceptions=False)


class _TinyWorld:
    """Just enough world for the serving envelope."""
    day = 12.0


@pytest.fixture
def fake_world(monkeypatch, tmp_path):
    """Point both fidelities at a stubbed loader + existing tmp file."""
    snap = tmp_path / "tiny_probe_snapshot.pkl"
    snap.write_bytes(b"stub")
    monkeypatch.setitem(v1._FIDELITY, "20k", str(snap))
    monkeypatch.setitem(v1._FIDELITY, "200k", str(snap))
    from earth1 import persistence
    monkeypatch.setattr(persistence, "load_world",
                        lambda p, **kw: (_TinyWorld(), None, None))


@pytest.fixture
def fake_adapters(monkeypatch):
    """Stub earth1.adapters.router.answer_any; optionally blocking."""
    state = {"calls": [], "block": False,
             "started": threading.Event(), "release": threading.Event()}

    def answer_any(q, w, seed=None, horizon_days=None):
        state["calls"].append({"horizon_days": horizon_days})
        if state["block"]:
            state["started"].set()
            state["release"].wait(timeout=30)
        return {"ok": True, "horizon_days": horizon_days}

    fake_pkg = types.ModuleType("earth1.adapters")
    fake_pkg.router = types.SimpleNamespace(answer_any=answer_any)
    monkeypatch.setitem(sys.modules, "earth1.adapters", fake_pkg)
    yield state
    state["release"].set()   # never leave a blocked worker behind


def _wait_done(client, jid, headers, timeout=10.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get(f"/v1/jobs/{jid}", headers=headers)
        if r.status_code == 200 and r.json()["status"] in ("done", "error"):
            return r.json()
        time.sleep(0.02)
    raise AssertionError(f"job {jid} never finished")


KEY = {"Authorization": "Bearer regression-key"}


# ------------------------------------------------------------ S03a: _auth

def test_empty_allowlist_fails_closed(client, monkeypatch):
    # probe s03a_empty_allowlist: _auth(None) returned "anonymous-dev"
    monkeypatch.setenv("EARTH1_API_KEYS", "")
    monkeypatch.delenv("EARTH1_DEV_OPEN", raising=False)
    r = client.get("/v1/world/events")
    assert r.status_code == 503
    assert "no API keys configured" in r.json()["detail"]
    # a garbage bearer must not sneak past the closed door either
    r = client.get("/v1/world/events",
                   headers={"Authorization": "Bearer whatever"})
    assert r.status_code == 503


def test_dev_open_explicitly_enables_anonymous(client, monkeypatch):
    monkeypatch.setenv("EARTH1_API_KEYS", "")
    monkeypatch.setenv("EARTH1_DEV_OPEN", "1")
    r = client.get("/v1/world/events")
    assert r.status_code == 200


def test_configured_keys_still_enforced(client, monkeypatch):
    monkeypatch.setenv("EARTH1_API_KEYS", "regression-key")
    monkeypatch.delenv("EARTH1_DEV_OPEN", raising=False)
    assert client.get("/v1/world/events").status_code == 401
    assert client.get("/v1/world/events",
                      headers={"Authorization": "Bearer wrong"}
                      ).status_code == 403
    assert client.get("/v1/world/events", headers=KEY).status_code == 200


# ------------------------------------------------------- M02c: freeze tag

def test_freeze_tag_reflects_mismatched_env(client, monkeypatch):
    # the original probe: all EARTH1_* unset (engine defaults, NOT
    # freeze-0.9) yet /v1/capabilities reported "freeze-0.9" anyway
    for k in list(os.environ):
        if k.startswith("EARTH1_"):
            monkeypatch.delenv(k)
    monkeypatch.setattr(v1, "_stamp_state", None)
    r = client.get("/v1/capabilities")
    assert r.status_code == 200
    tag = r.json()["freezeTag"]
    assert tag != "freeze-0.9"
    assert tag.startswith("unfrozen-dev:")


def test_freeze_tag_frozen_when_stamp_says_so(client, monkeypatch):
    monkeypatch.setattr(configstamp, "stamp",
                        lambda: {"is_freeze_09": True, "mismatch": None})
    assert v1._freeze_tag() == "freeze-0.9"
    monkeypatch.setenv("EARTH1_API_KEYS", "")
    monkeypatch.setenv("EARTH1_DEV_OPEN", "1")
    r = client.get("/v1/health")
    assert r.json()["freeze_tag"] == "freeze-0.9"
    assert r.json()["physics_stamp"] == "ok"


def test_freeze_tag_counts_mismatches(monkeypatch):
    monkeypatch.setattr(configstamp, "stamp",
                        lambda: {"is_freeze_09": False,
                                 "mismatch": {"A": "x", "B": "y"}})
    assert v1._freeze_tag() == "unfrozen-dev:2"


def test_stamp_failure_degrades_instead_of_crashing(monkeypatch):
    def boom():
        raise RuntimeError("stamp exploded")
    monkeypatch.setattr(configstamp, "stamp", boom)
    assert v1._freeze_tag() == "unfrozen-dev:stamp-error"


def test_first_world_load_marks_health_degraded(client, fake_world,
                                                monkeypatch):
    monkeypatch.setattr(configstamp, "stamp",
                        lambda: {"is_freeze_09": False,
                                 "mismatch": {"EARTH1_HARDSHIP_MODE":
                                              "(unset->default)"}})
    v1._world("20k")   # the startup-style check fires at first load
    assert v1._stamp_state is not None and not v1._stamp_state["frozen"]
    r = client.get("/v1/health")
    assert r.json()["physics_stamp"] == "degraded"
    assert r.json()["physics_stamp_mismatch"] == ["EARTH1_HARDSHIP_MODE"]
    assert r.json()["freeze_tag"] == "unfrozen-dev:1"


# ------------------------------------------------- S02: bounded async path

def test_job_cap_429_when_saturated(client, fake_world, fake_adapters,
                                    monkeypatch):
    monkeypatch.setenv("EARTH1_API_KEYS", "regression-key")
    monkeypatch.setenv("EARTH1_MAX_JOBS", "1")
    fake_adapters["block"] = True
    body = {"fidelity": "200k", "text": "probe"}
    r1 = client.post("/v1/ask", json=body, headers=KEY)
    assert r1.status_code == 200 and r1.json()["status"] == "queued"
    assert fake_adapters["started"].wait(timeout=10)
    # the single slot is held by the running job -> saturated
    r2 = client.post("/v1/ask", json=body, headers=KEY)
    assert r2.status_code == 429
    assert "job queue full" in r2.json()["detail"]
    # slot frees when the job finishes
    fake_adapters["block"] = False
    fake_adapters["release"].set()
    done = _wait_done(client, r1.json()["job_id"], KEY)
    assert done["status"] == "done"
    r3 = client.post("/v1/ask", json=body, headers=KEY)
    assert r3.status_code == 200
    _wait_done(client, r3.json()["job_id"], KEY)


def test_finished_jobs_ttl_evicted_on_access(client, monkeypatch):
    monkeypatch.setenv("EARTH1_API_KEYS", "regression-key")
    monkeypatch.setenv("EARTH1_JOB_TTL", "60")
    v1._jobs["stalejob00001"] = {"status": "done", "payload": {},
                                 "finished_at": time.time() - 3600}
    v1._jobs["freshjob00001"] = {"status": "done", "payload": {},
                                 "finished_at": time.time()}
    v1._jobs["runningjob001"] = {"status": "queued"}
    assert client.get("/v1/jobs/stalejob00001",
                      headers=KEY).status_code == 404
    assert client.get("/v1/jobs/freshjob00001",
                      headers=KEY).status_code == 200
    # unfinished jobs carry no finished_at and are never TTL-evicted
    assert client.get("/v1/jobs/runningjob001",
                      headers=KEY).status_code == 200


def test_ask_horizon_clamped_on_sync_path(client, fake_world,
                                          fake_adapters, monkeypatch):
    monkeypatch.setenv("EARTH1_API_KEYS", "regression-key")
    r = client.post("/v1/ask", json={"fidelity": "20k", "text": "probe",
                                     "horizon_days": 10_000}, headers=KEY)
    assert r.status_code == 200
    assert fake_adapters["calls"][-1]["horizon_days"] == 365
    r = client.post("/v1/ask", json={"fidelity": "20k", "text": "probe",
                                     "horizon_days": -5}, headers=KEY)
    assert r.status_code == 200
    assert fake_adapters["calls"][-1]["horizon_days"] == 1


def test_clamp_helper_bounds():
    assert v1._clamp_int(None, 8, 8, 16) == 8       # default passes
    assert v1._clamp_int(40, 8, 8, 16) == 16        # seeds cap
    assert v1._clamp_int(2, 8, 8, 16) == 8          # seeds floor
    assert v1._clamp_int("400", 60, 1, 365) == 365  # horizon cap
    assert v1._clamp_int(0, 30, 1, 365) == 1
    with pytest.raises(Exception) as ei:
        v1._clamp_int("not-a-number", 8, 1, 16)
    assert getattr(ei.value, "status_code", None) == 422
