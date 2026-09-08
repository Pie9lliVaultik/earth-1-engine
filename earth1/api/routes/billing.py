"""Billing routes — Stripe checkout, webhooks, usage, and tiers."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from earth1.api.deps import get_db
from earth1.api.billing import TIERS, create_checkout_session, handle_webhook, upgrade_api_key
from earth1.db import is_enabled

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tier: str
    customer_email: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.get("/tiers")
def list_tiers():
    return {
        name: {"price": t["price"], "daily_cap": t["daily_cap"], "rate_limit": t["rate_limit"]}
        for name, t in TIERS.items()
    }


@router.post("/checkout")
def checkout(req: CheckoutRequest):
    try:
        kwargs = {"tier": req.tier, "customer_email": req.customer_email}
        if req.success_url:
            kwargs["success_url"] = req.success_url
        if req.cancel_url:
            kwargs["cancel_url"] = req.cancel_url
        url = create_checkout_session(**kwargs)
        return {"checkout_url": url}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@router.post("/webhook")
async def webhook(request: Request, db=Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        result = handle_webhook(payload, sig)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")

    if result.get("action") == "upgrade" and is_enabled():
        email = result.get("customer_email", "")
        tier = result.get("tier", "pro")
        if db and email:
            from earth1.api.auth import APIKey
            key = db.query(APIKey).filter_by(owner=email, active=True).first()
            if key:
                upgrade_api_key(db, key.id, tier)
    elif result.get("action") == "subscription_change" and is_enabled():
        # review S03d: canceled/unpaid subscriptions never downgraded —
        # the paid tier survived cancellation forever.
        from earth1.api.billing import apply_subscription_change
        apply_subscription_change(db, result)

    return result


@router.get("/usage")
def usage(request: Request, db=Depends(get_db)):
    if not is_enabled():
        raise HTTPException(503, "Database not configured")

    from earth1.api.metering import get_daily_usage
    from earth1.api.auth import authenticate

    if db is None:
        raise HTTPException(503, "Database not available")

    # review S03b: this route returned EVERY key's usage (id, owner, tier,
    # caps) to any anonymous caller. Resolve the caller the way the
    # authenticated paths do — the middleware-attached key when
    # EARTH1_AUTH_REQUIRED is on, else the X-API-Key header verified
    # against the key store — and answer for that key alone.
    record = getattr(request.state, "api_key", None)
    if record is None:
        raw_key = request.headers.get("X-API-Key", "")
        if not raw_key:
            raise HTTPException(401, "X-API-Key header required")
        record = authenticate(db, raw_key)
        if record is None:
            raise HTTPException(403, "Invalid or inactive API key")

    return {
        "api_key_id": record.id,
        "owner": record.owner,
        "tier": record.tier,
        "daily_cap": record.daily_cap,
        "daily_usage": get_daily_usage(db, record.id),
    }
