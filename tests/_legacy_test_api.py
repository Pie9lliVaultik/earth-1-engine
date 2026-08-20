"""RETIRED (0.5g): tests of the old-engine API surface (/ask numbers,
/lab, legacy /world). Not collected (no test_ prefix). Historical
comparator only - the living surface is proven by
tests/test_api_one_earth.py."""
"""API integration tests using FastAPI's test client."""
import sys
sys.path.insert(0, ".")
import os
os.environ["EARTH1_POP"] = "5000"

from fastapi.testclient import TestClient
from earth1.api.main import app
from earth1.api.deps import reset_civ

reset_civ()
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["population"] == 5000


def test_civ():
    r = client.get("/civ")
    assert r.status_code == 200
    data = r.json()
    assert data["population"] == 5000
    assert len(data["countries"]) >= 50


def test_ask():
    r = client.get("/ask?q=svb")
    assert r.status_code == 200
    data = r.json()
    assert data["question_id"] == "svb"
    assert data["yes_pct"] > 0.5
    assert data["dominant"] == "fear"
    assert len(data["final_distribution"]) == 20


def test_ask_abstain():
    r = client.get("/ask?q=rain")
    assert r.status_code == 200
    data = r.json()
    assert data["abstained"] is not None


def test_ask_unknown():
    r = client.get("/ask?q=nonexistent")
    assert r.status_code == 404


def test_segment():
    r = client.get("/ask/segment?q=ssm&split_by=country")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 50
    assert all("yes_pct" in c for c in data)


def test_multiverse():
    r = client.get("/forecast/multiverse?q=svb")
    assert r.status_code == 200
    data = r.json()
    assert "present" in data
    assert len(data["branches"]) == 2


def test_perishability():
    r = client.get("/forecast/perishability?q=svb")
    assert r.status_code == 200
    data = r.json()
    assert "half_life_days" in data
    assert len(data["months"]) > 0


def test_questions_list():
    r = client.get("/observatory/questions")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 28


def test_standing_readings():
    r = client.get("/observatory/standing-readings")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 27  # 27 belief-causal questions


def test_superposition():
    r = client.get("/lab/superposition?q=ssm")
    assert r.status_code == 200
    data = r.json()
    assert "born_yes_pct" in data


def test_order_effect():
    r = client.get("/lab/order-effect?q1=ssm&q2=ai_trust")
    assert r.status_code == 200
    data = r.json()
    assert "order_effect_q2" in data


def test_cube():
    r = client.get("/lab/cube?q=svb")
    assert r.status_code == 200
    data = r.json()
    assert data["n"] == 5000


def test_layer_scrub():
    r = client.get("/lab/layer-scrub?q=ssm")
    assert r.status_code == 200
    data = r.json()
    assert len(data["layers"]) == 9  # 0..8
    assert "core" in data["layers"][0]
    assert "crust" in data["layers"][0]
    assert "sharpening" in data


def test_layer_scrub_country():
    r = client.get("/lab/layer-scrub?q=ssm&country=BR")
    assert r.status_code == 200
    data = r.json()
    assert data["population"] > 0
    assert data["sharpening"]["verdict"] in [
        "flat_to_sharp_confirmed", "sharpened_no_separation", "partial", "no_sharpening"
    ]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
