"""Usage metering and budget governor."""
from __future__ import annotations

import os
from datetime import datetime, date
from typing import Dict, Optional

from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Index, func
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from earth1.db.models import Base, _uuid


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    api_key_id = Column(String(36), nullable=True)
    endpoint = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tokens_used = Column(Integer, default=0)
    compute_ms = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_usage_key", "api_key_id"),
        Index("ix_usage_ts", "timestamp"),
    )


def log_usage(
    session,
    api_key_id: Optional[str],
    endpoint: str,
    tokens: int = 0,
    compute_ms: int = 0,
) -> Optional[UsageLog]:
    if session is None:
        return None

    entry = UsageLog(
        api_key_id=api_key_id,
        endpoint=endpoint,
        tokens_used=tokens,
        compute_ms=compute_ms,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_daily_usage(
    session,
    api_key_id: str,
    day: Optional[date] = None,
) -> Dict:
    if session is None:
        return {"requests": 0, "tokens": 0, "compute_ms": 0}

    if day is None:
        now = datetime.utcnow()
        day = now.date()

    start = datetime(day.year, day.month, day.day)
    end = datetime(day.year, day.month, day.day, 23, 59, 59)

    result = (
        session.query(
            func.count(UsageLog.id).label("requests"),
            func.coalesce(func.sum(UsageLog.tokens_used), 0).label("tokens"),
            func.coalesce(func.sum(UsageLog.compute_ms), 0).label("compute_ms"),
        )
        .filter(UsageLog.api_key_id == api_key_id)
        .filter(UsageLog.timestamp >= start)
        .filter(UsageLog.timestamp <= end)
        .first()
    )

    return {
        "requests": int(result.requests),
        "tokens": int(result.tokens),
        "compute_ms": int(result.compute_ms),
    }


def check_budget(session, api_key_id: str, daily_cap: int) -> bool:
    if session is None:
        return False
    usage = get_daily_usage(session, api_key_id)
    return usage["requests"] < daily_cap


class BudgetMiddleware(BaseHTTPMiddleware):
    """Checks daily usage against api_key.daily_cap. Fails closed."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        if not os.environ.get("EARTH1_AUTH_REQUIRED"):
            return await call_next(request)

        api_key = getattr(request.state, "api_key", None)
        if api_key is None:
            return await call_next(request)

        from earth1.db import get_session
        session = get_session()
        if session is None:
            return JSONResponse(
                {"error": "budget_unavailable"},
                status_code=503,
            )

        if not check_budget(session, api_key.id, api_key.daily_cap):
            return JSONResponse(
                {"error": "daily_cap_exceeded",
                 "message": f"Daily cap of {api_key.daily_cap} requests exceeded"},
                status_code=429,
            )

        return await call_next(request)
