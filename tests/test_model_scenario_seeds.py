"""Regression: POST /v1/models/{id}/scenario with seeds=1.

The v1 clamp accepts seeds in [1,16] (model_scenario_ep), but
run_scenario computed every sem as np.std(..., ddof=1) over the
per-seed deltas — NaN for a single seed — and NaN fails FastAPI's
JSON serialization, so an accepted request always died with a
plain-text 500. Fixed at the source (earth1/models.py::run_scenario):
sem is served as null when fewer than two seeds ran; the deltas are
still real. Documented caveat #1 of docs/API_REFERENCE.md §7 closes
with this.

In-process TestClient only, mirroring tests/test_review_service.py —
no network servers, no snapshots, no sealed paths. The world is the
conftest tiny_world (2,000 agents, pinned substrate) injected straight
into the v1 world cache; the model store is confined to tmp_path.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from earth1.api import v1

KEY = {"Authorization": "Bearer regression-key"}


@pytest.fixture(autouse=True)
def _reset_v1_state(monkeypatch, tmp_path):
    """Fresh module state per test; question log + model store in tmp."""
    from earth1 import models as em
    monkeypatch.setattr(v1, "_stamp_state", None)
    monkeypatch.setattr(v1, "_worlds", {})
    monkeypatch.setattr(v1, "_jobs", {})
    monkeypatch.setattr(v1, "_rate", {})
    monkeypatch.setattr(v1, "_cache", {})
    monkeypatch.setattr(v1, "QLOG", str(tmp_path / "qlog.jsonl"))
    monkeypatch.setattr(em, "MODELS_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("EARTH1_API_KEYS", "regression-key")


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(v1.router)
    return TestClient(app, raise_server_exceptions=False)


def _run(client, tiny_world, n_seeds):
    v1._worlds["20k"] = tiny_world   # bypass snapshot loading entirely
    r = client.post("/v1/models", json={"model_id": "semreg"}, headers=KEY)
    assert r.status_code == 200
    r = client.post("/v1/models/semreg/scenario",
                    json={"id": "s1", "seeds": n_seeds, "horizon_days": 1,
                          "forces": {"fear": 0.2}}, headers=KEY)
    assert r.status_code == 200, r.text
    return r.json()["result"]


def _sem_lines(out):
    return list(out["force_anatomy"].values()) + list(out["outcomes"].values())


def test_single_seed_serves_null_sem_not_500(client, tiny_world):
    # the probe that used to die: seeds=1 is inside the documented
    # [1,16] clamp yet every sem came out NaN -> plain-text 500
    out = _run(client, tiny_world, 1)
    assert out["population"] >= 50   # not an abstain payload
    for line in _sem_lines(out):
        assert line["sem"] is None
        assert isinstance(line["delta"], float)


def test_two_seeds_still_serve_numeric_sem(client, tiny_world):
    # the control must be able to fail: the guard may not blanket-null
    out = _run(client, tiny_world, 2)
    for line in _sem_lines(out):
        assert isinstance(line["sem"], float)
        assert line["sem"] == line["sem"]   # not NaN
