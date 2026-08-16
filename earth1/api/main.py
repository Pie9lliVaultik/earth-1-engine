"""Earth-1 API — FastAPI application."""
from __future__ import annotations
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from earth1.api.routes import ask, billing, forecast, lab, loop, observatory, predictions, receiver, world
from earth1.api.schemas import HealthSchema, CivStatsSchema
from earth1.api.deps import get_civ
from earth1.engine import civ_breakdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    civ = get_civ()
    dt = time.time() - t0
    print(f"[earth1] Civilization built: {civ.n:,} agents in {dt:.1f}s")

    from earth1.db import init_db, is_enabled
    if is_enabled():
        init_db()
        print("[earth1] Database connected and tables created")
    else:
        print("[earth1] No DATABASE_URL — running without persistence")

    yield


app = FastAPI(
    title="Earth-1 Engine API",
    description="Synthetic civilization of ~1M agents — force-field opinion dynamics at scale",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ask.router)
app.include_router(forecast.router)
app.include_router(lab.router)
app.include_router(observatory.router)
app.include_router(loop.router)
app.include_router(predictions.router)
app.include_router(receiver.router)
app.include_router(billing.router)
app.include_router(world.router)

from earth1.api.middleware import RateLimitMiddleware, PauseSwitchMiddleware
from earth1.api.auth import APIKeyMiddleware

# All control middlewares mount unconditionally and self-gate on env
# flags PER REQUEST (2026-08-16 audit). Starlette middleware is LIFO —
# the LAST added runs FIRST. Execution order (outermost -> innermost):
# Pause -> APIKey -> Budget -> RateLimit. Budget must run INSIDE APIKey
# because it reads request.state.api_key (re-audit finding: the old
# order ran Budget first, so the budget check silently skipped).
from earth1.api.metering import BudgetMiddleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(BudgetMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(PauseSwitchMiddleware)


@app.get("/health", response_model=HealthSchema)
def health():
    civ = get_civ()
    return {"status": "ok", "population": civ.n, "engine": "numpy-vectorized"}


@app.get("/civ", response_model=CivStatsSchema)
def civ_stats():
    civ = get_civ()
    from scipy import sparse
    nnz = civ.adj.nnz if sparse.issparse(civ.adj) else 0
    return {
        "population": civ.n,
        "seed": civ.seed,
        "countries": civ_breakdown(civ),
        "edges": nnz,
        "mean_degree": nnz / max(civ.n, 1),
    }


def run():
    import uvicorn
    uvicorn.run("earth1.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
