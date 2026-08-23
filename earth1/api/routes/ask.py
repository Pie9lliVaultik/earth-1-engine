"""/ask — the opinion readout of the living civilization. Phase 0.5e.

The structural path exists (0.4: living_features, accepted with the
permutation-inverted evidence), but per-question weight calibration on
the living stack is Benchmark A work (Phase 1). Until it lands, /ask
FAILS LOUDLY: it will not serve numbers from the retired engine, and it
will not pretend uncalibrated numbers are answers. No silent fallback —
a legacy world answering here would be a different universe wearing the
same URL.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from earth1.api.deps import get_world

router = APIRouter(prefix="/ask", tags=["ask"])

_PENDING = ("the living answer path requires per-question calibration "
            "(Benchmark A, Phase 1). The retired engine will not answer "
            "in its place. World identity attached so you know which "
            "civilization WILL answer.")


@router.get("")
@router.post("")
def ask_pending():
    _, identity = get_world()          # proves the world is resolvable
    raise HTTPException(503, {"error": "living_calibration_pending",
                              "detail": _PENDING,
                              "identity": identity})


@router.post("/segment")
@router.post("/freetext")
@router.post("/mind")
def ask_variants_pending():
    _, identity = get_world()
    raise HTTPException(503, {"error": "living_calibration_pending",
                              "detail": _PENDING,
                              "identity": identity})
