"""Tests for Stripe billing — checkout, webhooks, tiers, and upgrade."""
import json
import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from earth1.db.models import Base
from earth1.api.billing import (
    TIERS, create_checkout_session, handle_webhook, upgrade_api_key,
)
from earth1.api.auth import APIKey, create_api_key


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestTiers:
    def test_three_tiers_exist(self):
        assert len(TIERS) == 3
        assert set(TIERS.keys()) == {"free", "pro", "enterprise"}

    def test_free_is_zero_cost(self):
        assert TIERS["free"]["price"] == 0

    def test_pro_caps(self):
        assert TIERS["pro"]["daily_cap"] == 10_000
        assert TIERS["pro"]["rate_limit"] == 300

    def test_enterprise_caps(self):
        assert TIERS["enterprise"]["daily_cap"] == 100_000
        assert TIERS["enterprise"]["rate_limit"] == 1000

    def test_tiers_ordered_by_price(self):
        prices = [TIERS[t]["price"] for t in ["free", "pro", "enterprise"]]
        assert prices == sorted(prices)


class TestCreateCheckout:
    def test_unknown_tier_raises(self):
        with pytest.raises(ValueError, match="Unknown tier"):
            create_checkout_session("platinum", "user@example.com")

    def test_free_tier_raises(self):
        with pytest.raises(ValueError, match="Free tier"):
            create_checkout_session("free", "user@example.com")

    def test_no_stripe_key_raises(self):
        mock_stripe = MagicMock()

        with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}, clear=False):
            with patch.dict("sys.modules", {"stripe": mock_stripe}):
                with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY"):
                    create_checkout_session("pro", "user@example.com")

    def test_successful_checkout(self):
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        import sys
        saved = sys.modules.get("stripe")
        sys.modules["stripe"] = mock_stripe

        try:
            with patch.dict("os.environ", {
                "STRIPE_SECRET_KEY": "sk_test_123",
                "STRIPE_PRICE_PRO": "price_pro_123",
            }):
                url = create_checkout_session("pro", "user@example.com")
        finally:
            if saved is None:
                sys.modules.pop("stripe", None)
            else:
                sys.modules["stripe"] = saved

        assert url == "https://checkout.stripe.com/session_123"
        mock_stripe.checkout.Session.create.assert_called_once()
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["customer_email"] == "user@example.com"
        assert call_kwargs["mode"] == "subscription"
        assert call_kwargs["metadata"]["tier"] == "pro"


class TestWebhook:
    def test_checkout_completed_event(self):
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "user@example.com",
                    "metadata": {"tier": "pro"},
                }
            }
        }
        payload = json.dumps(event).encode()

        mock_stripe = MagicMock()
        import sys
        saved = sys.modules.get("stripe")
        sys.modules["stripe"] = mock_stripe

        try:
            with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123", "STRIPE_WEBHOOK_SECRET": ""}):
                result = handle_webhook(payload, "")
        finally:
            if saved is None:
                sys.modules.pop("stripe", None)
            else:
                sys.modules["stripe"] = saved

        assert result["action"] == "upgrade"
        assert result["customer_email"] == "user@example.com"
        assert result["tier"] == "pro"

    def test_subscription_deleted_event(self):
        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_123",
                    "status": "canceled",
                }
            }
        }
        payload = json.dumps(event).encode()

        mock_stripe = MagicMock()
        import sys
        saved = sys.modules.get("stripe")
        sys.modules["stripe"] = mock_stripe

        try:
            with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123", "STRIPE_WEBHOOK_SECRET": ""}):
                result = handle_webhook(payload, "")
        finally:
            if saved is None:
                sys.modules.pop("stripe", None)
            else:
                sys.modules["stripe"] = saved

        assert result["action"] == "subscription_change"
        assert result["status"] == "canceled"

    def test_ignored_event(self):
        event = {"type": "invoice.paid", "data": {"object": {}}}
        payload = json.dumps(event).encode()

        mock_stripe = MagicMock()
        import sys
        saved = sys.modules.get("stripe")
        sys.modules["stripe"] = mock_stripe

        try:
            with patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123", "STRIPE_WEBHOOK_SECRET": ""}):
                result = handle_webhook(payload, "")
        finally:
            if saved is None:
                sys.modules.pop("stripe", None)
            else:
                sys.modules["stripe"] = saved

        assert result["action"] == "ignored"


class TestUpgradeApiKey:
    def test_upgrade_changes_tier(self, db_session):
        raw_key, record = create_api_key(db_session, "user@example.com", tier="free")
        assert record.tier == "free"
        assert record.daily_cap == 1000

        success = upgrade_api_key(db_session, record.id, "pro")
        assert success is True

        db_session.refresh(record)
        assert record.tier == "pro"
        assert record.daily_cap == 10_000
        assert record.rate_limit == 300

    def test_upgrade_to_enterprise(self, db_session):
        raw_key, record = create_api_key(db_session, "corp@example.com", tier="free")
        upgrade_api_key(db_session, record.id, "enterprise")
        db_session.refresh(record)
        assert record.tier == "enterprise"
        assert record.daily_cap == 100_000

    def test_upgrade_nonexistent_key(self, db_session):
        result = upgrade_api_key(db_session, "nonexistent-id", "pro")
        assert result is False

    def test_upgrade_invalid_tier(self, db_session):
        raw_key, record = create_api_key(db_session, "user@example.com")
        result = upgrade_api_key(db_session, record.id, "platinum")
        assert result is False

    def test_none_session(self):
        result = upgrade_api_key(None, "some-id", "pro")
        assert result is False


class TestBillingRoutes:
    def test_tiers_endpoint(self):
        from starlette.testclient import TestClient
        from earth1.api.main import app
        client = TestClient(app)
        resp = client.get("/billing/tiers")
        assert resp.status_code == 200
        data = resp.json()
        assert "free" in data
        assert "pro" in data
        assert "enterprise" in data
        assert data["pro"]["price"] == 99

    def test_checkout_invalid_tier(self):
        from starlette.testclient import TestClient
        from earth1.api.main import app
        client = TestClient(app)
        resp = client.post("/billing/checkout", json={
            "tier": "platinum",
            "customer_email": "user@example.com",
        })
        assert resp.status_code == 400
