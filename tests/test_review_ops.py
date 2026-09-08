"""Regression tests for external-review findings (APPARATUS CYCLE 1):

  S03b  /billing/usage disclosed every key's usage to any caller
  S03d  subscription cancellation never downgraded the paid tier
  auth  APIKeyMiddleware leaked a DB session on every request
  S04   run_backup.sh omitted history.sqlite; model-store scope unstated
  M09   packaging: flat-layout discovery, dead benchmark entry point,
        unconditional torch import at collection time

Reproduces the review's probes (scratchpad review_verify/) with
synthetic keys and an in-memory DB — no network servers, no sealed
paths, no credential files.
"""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

pytest.importorskip("sqlalchemy")
pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from earth1.db.models import Base
from earth1.api.auth import APIKey, APIKeyMiddleware, create_api_key
from earth1.api.billing import TIERS, apply_subscription_change, handle_webhook
from earth1.api.metering import log_usage


# ── shared in-memory DB, safe across TestClient threads ─────────────

@pytest.fixture
def db_factory(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    # is_enabled() keys off the env var; the actual engine is overridden.
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    yield factory
    engine.dispose()


@pytest.fixture
def billing_client(db_factory):
    from earth1.api.deps import get_db
    from earth1.api.routes import billing as billing_routes

    app = FastAPI()
    app.include_router(billing_routes.router)

    def _override_db():
        s = db_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


# ── S03b: /billing/usage requires auth and self-scopes ──────────────

class TestUsageScoping:
    def _seed_two_keys(self, db_factory):
        s = db_factory()
        raw_a, rec_a = create_api_key(s, "alice@example.com", tier="pro")
        raw_b, rec_b = create_api_key(s, "bob@example.com", tier="free")
        for _ in range(3):
            log_usage(s, rec_a.id, "/ask")
        for _ in range(5):
            log_usage(s, rec_b.id, "/ask")
        ids = (rec_a.id, rec_b.id)
        s.close()
        return raw_a, raw_b, ids

    def test_anonymous_caller_refused(self, billing_client, db_factory):
        # the original probe: a keyless GET dumped every key's usage
        self._seed_two_keys(db_factory)
        resp = billing_client.get("/billing/usage")
        assert resp.status_code == 401

    def test_invalid_key_refused(self, billing_client, db_factory):
        self._seed_two_keys(db_factory)
        resp = billing_client.get(
            "/billing/usage", headers={"X-API-Key": "e1-not-a-real-key"})
        assert resp.status_code == 403

    def test_caller_sees_only_own_usage(self, billing_client, db_factory):
        raw_a, raw_b, (id_a, id_b) = self._seed_two_keys(db_factory)

        resp = billing_client.get(
            "/billing/usage", headers={"X-API-Key": raw_a})
        assert resp.status_code == 200
        body = resp.json()
        # single object, not the old all-keys list
        assert isinstance(body, dict)
        assert body["api_key_id"] == id_a
        assert body["owner"] == "alice@example.com"
        assert body["daily_usage"]["requests"] == 3
        # nothing of key B leaks into A's response
        assert id_b not in resp.text
        assert "bob@example.com" not in resp.text

        resp_b = billing_client.get(
            "/billing/usage", headers={"X-API-Key": raw_b})
        assert resp_b.json()["api_key_id"] == id_b
        assert resp_b.json()["daily_usage"]["requests"] == 5


# ── S03d: cancellation downgrades to free, idempotently ─────────────

class TestSubscriptionDowngrade:
    def _canceled(self, email="payer@example.com", status="canceled"):
        return {"action": "subscription_change", "status": status,
                "subscription_id": "sub_1", "customer_email": email}

    def test_cancel_downgrades_and_is_idempotent(self, db_factory):
        s = db_factory()
        _, rec = create_api_key(s, "payer@example.com", tier="pro",
                                rate_limit=300, daily_cap=10_000)
        assert apply_subscription_change(s, self._canceled()) is True
        s.refresh(rec)
        assert rec.tier == "free"
        assert rec.daily_cap == TIERS["free"]["daily_cap"]
        assert rec.rate_limit == TIERS["free"]["rate_limit"]

        # second delivery of the same event: no error, same end state
        assert apply_subscription_change(s, self._canceled()) is True
        s.refresh(rec)
        assert rec.tier == "free"
        assert rec.daily_cap == TIERS["free"]["daily_cap"]
        s.close()

    def test_unpaid_downgrades_too(self, db_factory):
        s = db_factory()
        _, rec = create_api_key(s, "payer@example.com", tier="enterprise")
        assert apply_subscription_change(
            s, self._canceled(status="unpaid")) is True
        s.refresh(rec)
        assert rec.tier == "free"
        s.close()

    def test_active_status_is_not_a_downgrade(self, db_factory):
        s = db_factory()
        _, rec = create_api_key(s, "payer@example.com", tier="pro",
                                rate_limit=300, daily_cap=10_000)
        assert apply_subscription_change(
            s, self._canceled(status="active")) is False
        s.refresh(rec)
        assert rec.tier == "pro"
        s.close()

    def test_unknown_email_and_wrong_action_are_noops(self, db_factory):
        s = db_factory()
        assert apply_subscription_change(
            s, self._canceled(email="nobody@example.com")) is False
        assert apply_subscription_change(
            s, {"action": "upgrade", "status": "canceled"}) is False
        assert apply_subscription_change(s, self._canceled(email="")) is False
        assert apply_subscription_change(None, self._canceled()) is False
        s.close()

    def test_handle_webhook_carries_owner_email(self):
        event = {"type": "customer.subscription.deleted",
                 "data": {"object": {"id": "sub_9", "status": "canceled",
                                     "customer_email": "payer@example.com"}}}
        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = event
        with patch.dict(sys.modules, {"stripe": mock_stripe}):
            with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test",
                                         "STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                result = handle_webhook(b"{}", "sig")
        assert result["action"] == "subscription_change"
        assert result["status"] == "canceled"
        assert result["customer_email"] == "payer@example.com"

    def test_webhook_route_applies_downgrade(self, billing_client, db_factory):
        s = db_factory()
        _, rec = create_api_key(s, "payer@example.com", tier="pro")
        rec_id = rec.id
        s.close()

        event = {"type": "customer.subscription.deleted",
                 "data": {"object": {"id": "sub_9", "status": "canceled",
                                     "customer_email": "payer@example.com"}}}
        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = event
        with patch.dict(sys.modules, {"stripe": mock_stripe}):
            with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test",
                                         "STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                resp = billing_client.post(
                    "/billing/webhook", content=b"{}",
                    headers={"Stripe-Signature": "sig"})
        assert resp.status_code == 200

        s = db_factory()
        row = s.query(APIKey).filter_by(id=rec_id).one()
        assert row.tier == "free"
        s.close()


# ── auth middleware: DB session closed on every path ────────────────

class _FakeQuery:
    def __init__(self, record):
        self._record = record

    def filter_by(self, **_kw):
        return self

    def first(self):
        return self._record


class _FakeSession:
    def __init__(self, record):
        self._record = record
        self.closed = False

    def query(self, *_a, **_k):
        return _FakeQuery(self._record)

    def close(self):
        self.closed = True


class TestAuthSessionLifecycle:
    def _client(self):
        app = FastAPI()

        @app.get("/ping")
        def ping():
            return {"ok": True}

        app.add_middleware(APIKeyMiddleware)
        return TestClient(app)

    def _record(self):
        return APIKey(id="k1", key_hash="h" * 64, owner="o@example.com",
                      tier="free", rate_limit=60, daily_cap=1000, active=True)

    def test_session_closed_on_valid_and_invalid_key(self, monkeypatch):
        monkeypatch.setenv("EARTH1_AUTH_REQUIRED", "1")
        sessions = []

        def fake_get_session(record):
            def _make():
                s = _FakeSession(record)
                sessions.append(s)
                return s
            return _make

        client = self._client()

        monkeypatch.setattr("earth1.db.get_session",
                            fake_get_session(self._record()))
        assert client.get(
            "/ping", headers={"X-API-Key": "e1-good"}).status_code == 200

        monkeypatch.setattr("earth1.db.get_session", fake_get_session(None))
        assert client.get(
            "/ping", headers={"X-API-Key": "e1-bad"}).status_code == 403

        assert len(sessions) == 2
        assert all(s.closed for s in sessions), \
            "APIKeyMiddleware left a DB session open (review auth-lifecycle)"


# ── S04: backup covers history.sqlite; model-store scope stated ─────

class TestBackupScript:
    SCRIPT = ROOT / "ops" / "alive" / "run_backup.sh"

    def test_bash_syntax_ok(self):
        proc = subprocess.run(["bash", "-n", str(self.SCRIPT)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr

    def test_history_sqlite_staged(self):
        text = self.SCRIPT.read_text()
        assert "history.sqlite" in text, "review S04: history.sqlite still omitted"
        assert ".backup" in text, "review S04: no sqlite3 online .backup path"
        assert "history.sqlite-wal" in text and "history.sqlite-shm" in text, \
            "review S04: plain-copy fallback must include -wal/-shm sidecars"

    def test_model_store_scope_stated_in_header(self):
        header = "\n".join(
            line for line in self.SCRIPT.read_text().splitlines()
            if line.startswith("#"))
        assert "EARTH1_MODELS_DIR" in header
        assert "EXCLUDED" in header


# ── M09: packaging and torch-free collection ────────────────────────

class TestPackaging:
    def test_benchmark_entry_target_importable(self):
        env = dict(os.environ, EARTH1_LEGACY_COMPARISON="1")
        proc = subprocess.run(
            [sys.executable, "-c",
             "from earth1.legacy_benchmark import run_cli; "
             "assert callable(run_cli)"],
            cwd=str(ROOT), env=env, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr

    def test_pyproject_discovery_and_entry_point(self):
        text = (ROOT / "pyproject.toml").read_text()
        assert "[tool.setuptools.packages.find]" in text
        assert 'include = ["earth1*"]' in text
        assert 'earth1-benchmark = "earth1.legacy_benchmark:run_cli"' in text
        assert 'earth1.benchmark:run_cli' not in text, \
            "review M09: entry point still targets the nonexistent earth1.benchmark"

    def test_collection_clean_without_torch(self, tmp_path):
        # a stub torch that raises ImportError shadows any installed one,
        # so this passes/fails identically with or without the gpu extra
        (tmp_path / "torch.py").write_text(
            "raise ImportError('stubbed out: review M09 collection probe')\n")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "-p", "no:cacheprovider", "tests/test_torch.py"],
            cwd=str(ROOT), env=env, capture_output=True, text=True)
        out = proc.stdout + proc.stderr
        # 0 = collected fine; 5 = nothing collected (whole module skipped).
        # A pre-fix tree exits 2 with an "ERRORS" section and a traceback.
        # (pytest >= 8.2 additionally WARNS that the stub was found-but-
        # raising — a stub artifact, not a collection error; real absence
        # raises ModuleNotFoundError and stays silent.)
        assert proc.returncode in (0, 5), out
        assert "Traceback" not in out, out
        assert "ERROR" not in out, out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
