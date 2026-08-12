"""API key authentication."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from earth1.db.models import Base, _uuid


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=_uuid)
    key_hash = Column(String(64), unique=True, nullable=False)
    owner = Column(String(120), nullable=False)
    tier = Column(String(20), default="free")
    rate_limit = Column(Integer, default=60)
    daily_cap = Column(Integer, default=1000)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(
    session,
    owner: str,
    tier: str = "free",
    rate_limit: int = 60,
    daily_cap: int = 1000,
) -> Tuple[str, Optional[APIKey]]:
    if session is None:
        return "", None

    raw_key = f"e1-{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)

    record = APIKey(
        key_hash=key_hash,
        owner=owner,
        tier=tier,
        rate_limit=rate_limit,
        daily_cap=daily_cap,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return raw_key, record


def authenticate(session, raw_key: str) -> Optional[APIKey]:
    if session is None:
        return None
    key_hash = _hash_key(raw_key)
    return session.query(APIKey).filter_by(key_hash=key_hash, active=True).first()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Check X-API-Key header. Only active when EARTH1_AUTH_REQUIRED is set."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        if not os.environ.get("EARTH1_AUTH_REQUIRED"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                {"error": "missing_api_key", "message": "X-API-Key header required"},
                status_code=401,
            )

        from earth1.db import get_session
        session = get_session()
        if session is None:
            return JSONResponse(
                {"error": "auth_unavailable", "message": "Auth requires database"},
                status_code=503,
            )

        record = authenticate(session, api_key)
        if record is None:
            return JSONResponse(
                {"error": "invalid_api_key", "message": "Invalid or inactive API key"},
                status_code=403,
            )

        request.state.api_key = record
        return await call_next(request)
