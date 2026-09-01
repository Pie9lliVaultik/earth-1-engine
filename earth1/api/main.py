"""Earth-1 API — FastAPI application over THE canonical living world.

Phase 0.5e. Every product route answers from the daemon's persisted
`alive.World` — the same civilization, by identity, that
`earth1-alive.service` evolves. No route may construct or resolve any
other world; if the canonical snapshot is unavailable the API returns
503 rather than fabricating an Earth.

Retired with the engine family (0.5g): the `lab`, `loop` and
`receiver` routers — old-substrate research surfaces, not products.
Their history lives in git; they are not mounted.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from earth1.api.deps import CanonicalWorldUnavailable, get_world
from earth1.api.routes import (ask, billing, forecast, observatory,
                               predictions, world)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    try:
        _, identity = get_world()
        print(f"[earth1] canonical world resolved in {time.time()-t0:.1f}s"
              f": day {identity['world_day']}, "
              f"{identity['alive']:,} alive, "
              f"snapshot {str(identity['snapshot_sha256'])[:12]}")
    except CanonicalWorldUnavailable as e:
        # the app still starts (health must be reachable) but every
        # world-backed route will 503 loudly — never a legacy fallback
        print(f"[earth1] CANONICAL WORLD UNAVAILABLE: {e}")

    from earth1.db import init_db, is_enabled
    if is_enabled():
        init_db()
        print("[earth1] Database connected and tables created")
    else:
        print("[earth1] No DATABASE_URL — running without persistence")

    yield


app = FastAPI(
    title="Earth-1 API",
    description="One living civilization. Every route answers from the "
                "same canonical alive.World the daemon evolves.",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CanonicalWorldUnavailable)
async def world_unavailable(_req, exc):
    return JSONResponse(
        status_code=503,
        content={"error": "canonical_world_unavailable",
                 "detail": str(exc),
                 "note": "there is no legacy fallback by design"})


app.include_router(ask.router)
app.include_router(forecast.router)
app.include_router(observatory.router)
app.include_router(predictions.router)
app.include_router(billing.router)
app.include_router(world.router)
from earth1.api.routes import civilization, branches   # API-COMPLETE-1
app.include_router(civilization.router)
app.include_router(branches.router)

# v1 — THE typed ship surface (BIBLE v4.2.2 refinement 9). Fail-open
# mount: the legacy surface keeps serving if v1 deps are absent.
try:
    from earth1.api.v1 import router as _v1_router
    app.include_router(_v1_router)
    print("[earth1] v1 ship surface mounted")
except Exception as _v1e:                                  # noqa: BLE001
    print(f"[earth1] v1 surface NOT mounted: {_v1e}")

from earth1.api.auth import APIKeyMiddleware
from earth1.api.metering import BudgetMiddleware
from earth1.api.middleware import PauseSwitchMiddleware, RateLimitMiddleware

# Starlette middleware is LIFO — the LAST added runs FIRST. Execution
# order (outermost -> innermost): Pause -> APIKey -> Budget -> RateLimit.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BudgetMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(PauseSwitchMiddleware)


@app.get("/health")
def health():
    try:
        _, identity = get_world()
        return {"status": "ok", "world": identity}
    except CanonicalWorldUnavailable as e:
        return JSONResponse(status_code=503,
                            content={"status": "world_unavailable",
                                     "detail": str(e)})


@app.get("/civ")
def civ_stats():
    w, identity = get_world()
    import numpy as np
    alive = w.health.alive
    per_country = np.bincount(w.civ.country[alive], minlength=194)
    top = np.argsort(per_country)[::-1][:20]
    from earth1.genesis import GENESIS_COUNTRY_CODES
    return {
        "identity": identity,
        "edges": int(w.civ.adj.nnz),
        "mean_degree": round(float(w.civ.adj.nnz) / max(w.civ.n, 1), 2),
        "top_countries": [{"iso2": GENESIS_COUNTRY_CODES[int(c)],
                           "alive": int(per_country[c])} for c in top],
    }


def run():
    import uvicorn
    uvicorn.run("earth1.api.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
