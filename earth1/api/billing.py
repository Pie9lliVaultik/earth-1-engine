"""Stripe billing — checkout sessions, webhooks, and tier management."""
from __future__ import annotations

import os
from typing import Dict, Optional


TIERS: Dict[str, Dict] = {
    "free": {"price": 0, "daily_cap": 100, "rate_limit": 30, "stripe_price_id": None},
    "pro": {"price": 99, "daily_cap": 10_000, "rate_limit": 300, "stripe_price_id": None},
    "enterprise": {"price": 499, "daily_cap": 100_000, "rate_limit": 1000, "stripe_price_id": None},
}


def _get_stripe():
    try:
        import stripe
    except ImportError:
        raise RuntimeError("stripe package not installed. Install with: pip install 'earth1-engine[billing]'")
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        raise RuntimeError("STRIPE_SECRET_KEY not set")
    return stripe


def _get_price_id(tier: str) -> str:
    price_id = TIERS[tier].get("stripe_price_id")
    if not price_id:
        env_key = f"STRIPE_PRICE_{tier.upper()}"
        price_id = os.environ.get(env_key, "")
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for tier '{tier}'. Set STRIPE_PRICE_{tier.upper()} env var.")
    return price_id


def create_checkout_session(
    tier: str,
    customer_email: str,
    success_url: str = "https://earth1.dev/billing/success",
    cancel_url: str = "https://earth1.dev/billing/cancel",
) -> str:
    if tier not in TIERS:
        raise ValueError(f"Unknown tier: {tier}. Valid: {list(TIERS.keys())}")
    if tier == "free":
        raise ValueError("Free tier does not require checkout")

    stripe = _get_stripe()
    price_id = _get_price_id(tier)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tier": tier},
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    stripe = _get_stripe()
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "") if isinstance(event, dict) else event["type"]

    if event_type == "checkout.session.completed":
        session_data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event["data"]["object"]
        return {
            "action": "upgrade",
            "customer_email": session_data.get("customer_email", ""),
            "tier": session_data.get("metadata", {}).get("tier", "pro"),
        }
    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        sub_data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event["data"]["object"]
        status = sub_data.get("status", "")
        return {
            "action": "subscription_change",
            "status": status,
            "subscription_id": sub_data.get("id", ""),
        }

    return {"action": "ignored", "event_type": event_type}


def upgrade_api_key(session, api_key_id: str, tier: str) -> bool:
    if session is None or tier not in TIERS:
        return False

    from earth1.api.auth import APIKey
    key = session.query(APIKey).filter_by(id=api_key_id).first()
    if not key:
        return False

    key.tier = tier
    key.rate_limit = TIERS[tier]["rate_limit"]
    key.daily_cap = TIERS[tier]["daily_cap"]
    session.commit()
    return True
