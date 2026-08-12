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

    return result


@router.get("/usage")
def usage(db=Depends(get_db)):
    if not is_enabled():
        raise HTTPException(503, "Database not configured")

    from earth1.api.metering import get_daily_usage
    from earth1.api.auth import APIKey

    if db is None:
        raise HTTPException(503, "Database not available")

    keys = db.query(APIKey).filter_by(active=True).all()
    results = []
    for key in keys:
        daily = get_daily_usage(db, key.id)
        results.append({
            "api_key_id": key.id,
            "owner": key.owner,
            "tier": key.tier,
            "daily_cap": key.daily_cap,
            "daily_usage": daily,
        })
    return results
