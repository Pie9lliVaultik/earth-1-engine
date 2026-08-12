"""Rate limiting and pause switch middleware."""
from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter per IP. Configurable via EARTH1_RATE_LIMIT env var."""

    def __init__(self, app, rate_limit: int = 0):
        super().__init__(app)
        self.rate_limit = rate_limit or int(os.environ.get("EARTH1_RATE_LIMIT", "60"))
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (time.monotonic(), float(self.rate_limit))
        )

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        last_time, tokens = self.buckets[client_ip]
        elapsed = now - last_time
        tokens = min(self.rate_limit, tokens + elapsed * (self.rate_limit / 60.0))

        if tokens < 1.0:
            return JSONResponse(
                {"error": "rate_limit_exceeded", "retry_after_seconds": 60},
                status_code=429,
            )

        self.buckets[client_ip] = (now, tokens - 1.0)
        return await call_next(request)


class PauseSwitchMiddleware(BaseHTTPMiddleware):
    """Returns 503 when EARTH1_PAUSED=true. Health endpoint exempt."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        if os.environ.get("EARTH1_PAUSED", "").lower() in ("true", "1", "yes"):
            return JSONResponse(
                {"error": "service_paused", "message": "Engine is temporarily paused"},
                status_code=503,
            )

        return await call_next(request)
