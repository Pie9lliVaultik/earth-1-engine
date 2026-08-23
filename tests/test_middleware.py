"""Tests for rate limiting, API keys, pause switch, metering, and budget."""
import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from earth1.db.models import Base
from earth1.api.auth import APIKey, create_api_key, authenticate, _hash_key
from earth1.api.metering import UsageLog, log_usage, get_daily_usage, check_budget

# Ensure all models are registered with Base before create_all
_ = APIKey.__table__
_ = UsageLog.__table__


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestAPIKey:
    def test_create_key(self, db_session):
        raw_key, record = create_api_key(db_session, "test-user")
        assert raw_key.startswith("e1-")
        assert record is not None
        assert record.owner == "test-user"
        assert record.tier == "free"
        assert record.active is True

    def test_authenticate_valid(self, db_session):
        raw_key, _ = create_api_key(db_session, "test-user")
        record = authenticate(db_session, raw_key)
        assert record is not None
        assert record.owner == "test-user"

    def test_authenticate_invalid(self, db_session):
        create_api_key(db_session, "test-user")
        assert authenticate(db_session, "wrong-key") is None

    def test_authenticate_inactive(self, db_session):
        raw_key, record = create_api_key(db_session, "test-user")
        record.active = False
        db_session.commit()
        assert authenticate(db_session, raw_key) is None

    def test_hash_deterministic(self):
        h1 = _hash_key("test-key")
        h2 = _hash_key("test-key")
        assert h1 == h2
        assert len(h1) == 64

    def test_tier_custom(self, db_session):
        _, record = create_api_key(db_session, "pro-user", tier="pro", rate_limit=300, daily_cap=10000)
        assert record.tier == "pro"
        assert record.rate_limit == 300
        assert record.daily_cap == 10000

    def test_none_session(self):
        raw, record = create_api_key(None, "test")
        assert raw == ""
        assert record is None
        assert authenticate(None, "x") is None


class TestRateLimiter:
    def test_rate_limiter_allows_normal_traffic(self):
        from fastapi.testclient import TestClient
        from earth1.api.main import app
        client = TestClient(app)
        for _ in range(5):
            r = client.get("/health")
            # rate-limit test: requests must be ALLOWED (not 429).
            # 503 = canonical world absent in this environment, which
            # is the world resolver's business, not the limiter's.
            assert r.status_code in (200, 503)

    def test_pause_switch_health_exempt(self):
        from earth1.api.middleware import PauseSwitchMiddleware
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        async def health(request):
            return PlainTextResponse("ok")
        async def ask(request):
            return PlainTextResponse("data")

        test_app = Starlette(routes=[
            Route("/health", health),
            Route("/ask", ask),
        ])
        test_app.add_middleware(PauseSwitchMiddleware)

        from starlette.testclient import TestClient
        with patch.dict(os.environ, {"EARTH1_PAUSED": "true"}):
            client = TestClient(test_app)
            assert client.get("/health").status_code == 200
            assert client.get("/ask").status_code == 503


class TestUsageMetering:
    def test_log_usage(self, db_session):
        entry = log_usage(db_session, "key-1", "/ask", tokens=100, compute_ms=50)
        assert entry is not None
        assert entry.tokens_used == 100
        assert entry.compute_ms == 50

    def test_get_daily_usage(self, db_session):
        log_usage(db_session, "key-1", "/ask", tokens=100)
        log_usage(db_session, "key-1", "/ask", tokens=200)
        log_usage(db_session, "key-2", "/ask", tokens=50)

        usage = get_daily_usage(db_session, "key-1")
        assert usage["requests"] == 2
        assert usage["tokens"] == 300

    def test_check_budget_within_cap(self, db_session):
        log_usage(db_session, "key-1", "/ask")
        assert check_budget(db_session, "key-1", daily_cap=100) is True

    def test_check_budget_exceeded(self, db_session):
        for _ in range(10):
            log_usage(db_session, "key-1", "/ask")
        assert check_budget(db_session, "key-1", daily_cap=5) is False

    def test_none_session(self):
        assert log_usage(None, "x", "/ask") is None
        usage = get_daily_usage(None, "x")
        assert usage["requests"] == 0
        assert check_budget(None, "x", 100) is False
