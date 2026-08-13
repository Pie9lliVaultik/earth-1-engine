"""Resolving the standing record (bible §20.2).

The other half of the arming loop: when a live market resolves, the
armed reading is scored against reality and the (signature, fragility,
price, resolution) tuple lands in the Force-Outcome Atlas.

Integrity first: a reading is only scored if its stored sha256 still
matches its content — a hash mismatch is tamper evidence and the row is
flagged, never scored. Cancelled/voided markets are marked and excluded.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import dataclass
from typing import Callable, List, Optional

from earth1.db import store
from earth1.db.models import Prediction, Run

_UA = {"User-Agent": "Earth1-Engine/1.0"}


@dataclass
class Resolution:
    resolved: bool
    actual: Optional[float] = None   # 1.0 / 0.0, or probability for MKT
    voided: bool = False
    detail: str = ""


def _get_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_manifold_resolution(market_id: str) -> Resolution:
    try:
        m = _get_json(f"https://api.manifold.markets/v0/market/{market_id}")
    except Exception as e:
        return Resolution(resolved=False, detail=f"fetch failed: {e}")
    if not m.get("isResolved"):
        return Resolution(resolved=False)
    res = m.get("resolution")
    if res == "YES":
        return Resolution(resolved=True, actual=1.0)
    if res == "NO":
        return Resolution(resolved=True, actual=0.0)
    if res == "MKT":
        p = m.get("resolutionProbability")
        if p is not None:
            return Resolution(resolved=True, actual=float(p))
        return Resolution(resolved=False, detail="MKT without probability")
    return Resolution(resolved=True, voided=True, detail=f"resolution={res}")


def fetch_polymarket_resolution(market_id: str) -> Resolution:
    try:
        m = _get_json(f"https://gamma-api.polymarket.com/markets/{market_id}")
    except Exception as e:
        return Resolution(resolved=False, detail=f"fetch failed: {e}")
    if isinstance(m, list):
        m = m[0] if m else {}
    status = str(m.get("umaResolutionStatus", "")).lower()
    if not m.get("closed"):
        return Resolution(resolved=False)
    try:
        prices = json.loads(m.get("outcomePrices", "[]"))
        p0 = float(prices[0]) if prices else None
    except Exception:
        p0 = None
    if status == "resolved" and p0 is not None:
        return Resolution(resolved=True, actual=round(p0))
    if p0 is not None and (p0 >= 0.99 or p0 <= 0.01):
        return Resolution(resolved=True, actual=round(p0))
    return Resolution(resolved=False, detail="closed but resolution unclear")


_FETCHERS = {
    "manifold": fetch_manifold_resolution,
    "polymarket": fetch_polymarket_resolution,
}


def verify_hash(pred: Prediction) -> bool:
    """A reading is scoreable only if its pre-commitment hash still holds."""
    content = f"{pred.question_text}|{pred.predicted_yes_pct}|{pred.horizon_days}"
    return hashlib.sha256(content.encode()).hexdigest() == pred.prediction_hash


@dataclass
class ResolveOutcome:
    prediction_id: str
    question: str
    status: str          # "resolved" | "voided" | "open" | "tampered"
    actual: Optional[float] = None
    engine_yes_pct: Optional[float] = None
    price_at_arming: Optional[float] = None
    fragility: Optional[float] = None


def resolve_armed(
    session,
    fetch: Optional[Callable[[str, str], Resolution]] = None,
) -> List[ResolveOutcome]:
    """Check every armed, open reading against its market. Score what
    resolved, void what was cancelled, flag what was tampered with."""
    preds = (session.query(Prediction)
             .filter_by(armed=True, status="open").all())

    out: List[ResolveOutcome] = []
    for pred in preds:
        run = session.query(Run).filter_by(id=pred.run_id).first()
        meta = (run.gateway_raw or {}) if run else {}
        market_id = meta.get("market_id")
        source = meta.get("market_source")
        price = meta.get("price_at_arming")
        if not market_id or source not in _FETCHERS:
            out.append(ResolveOutcome(pred.id, pred.question_text, "open"))
            continue

        if not verify_hash(pred):
            pred.status = "tampered"
            session.commit()
            out.append(ResolveOutcome(pred.id, pred.question_text, "tampered"))
            continue

        res = (fetch(source, market_id) if fetch
               else _FETCHERS[source](market_id))

        if res.voided:
            pred.status = "voided"
            session.commit()
            out.append(ResolveOutcome(pred.id, pred.question_text, "voided"))
        elif res.resolved and res.actual is not None:
            store.resolve_with_atlas(
                session, pred.id, actual_yes_pct=float(res.actual),
                source=source, source_url=meta.get("market_url", ""),
            )
            out.append(ResolveOutcome(
                pred.id, pred.question_text, "resolved",
                actual=float(res.actual),
                engine_yes_pct=pred.predicted_yes_pct,
                price_at_arming=price, fragility=pred.fragility,
            ))
        else:
            out.append(ResolveOutcome(pred.id, pred.question_text, "open"))
    return out


def atlas_report(session) -> dict:
    """The G4 scoreboard from accumulated Atlas tuples.

    Brier: mean (prediction - outcome)^2, engine vs the market price at
    arming — the gate asks the structurally-continuous reading to beat
    the price. Fragility split: among resolved readings, error above vs
    below median fragility — fragility should predict collapse.
    """
    from earth1.db.models import ForceOutcome

    rows = session.query(ForceOutcome).all()
    n = len(rows)
    if n == 0:
        return {"n_resolved": 0}

    engine_brier, market_brier = [], []
    frag_err = []
    for fo in rows:
        pred = session.query(Prediction).filter_by(id=fo.prediction_id).first()
        run = session.query(Run).filter_by(id=pred.run_id).first() if pred else None
        price = ((run.gateway_raw or {}).get("price_at_arming")
                 if run else None)
        outcome = fo.actual_yes_pct
        engine_brier.append((fo.predicted_yes_pct - outcome) ** 2)
        if price is not None:
            market_brier.append((float(price) - outcome) ** 2)
        frag_err.append((fo.fragility_at_prediction, fo.error))

    report = {
        "n_resolved": n,
        "engine_brier": sum(engine_brier) / len(engine_brier),
        "market_brier": (sum(market_brier) / len(market_brier)
                         if market_brier else None),
        "engine_beats_price": (
            sum(engine_brier) / len(engine_brier) <
            sum(market_brier) / len(market_brier)
            if market_brier else None),
    }

    if len(frag_err) >= 4:
        frags = sorted(f for f, _ in frag_err)
        median = frags[len(frags) // 2]
        hi = [e for f, e in frag_err if f >= median]
        lo = [e for f, e in frag_err if f < median]
        if hi and lo:
            report["fragility_split"] = {
                "median_fragility": median,
                "high_fragility_mean_error": sum(hi) / len(hi),
                "low_fragility_mean_error": sum(lo) / len(lo),
                "fragility_predicts_error": sum(hi) / len(hi) > sum(lo) / len(lo),
            }
    return report
