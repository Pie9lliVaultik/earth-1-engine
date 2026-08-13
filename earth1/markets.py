"""Live prediction-market adapters for the standing record (bible §20.2).

One interface, multiple sources. Each adapter degrades gracefully — an
unreachable source returns [] and the arming run proceeds with whatever
is live. Polymarket and Kalshi are region-blocked from some networks
(notably Italy); Manifold's API is open everywhere. The daily cron should
run where all sources resolve.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

_UA = {"User-Agent": "Earth1-Engine/1.0"}

# Belief-causal filter: the engine reads opinion-driven questions.
# Mechanical outcomes (asset prices, sports scores, weather) are outside
# the premise and are excluded before perception ever sees them.
_EXCLUDE_TOKENS = (
    "bitcoin", "btc", "ethereum", "eth ", "crypto", "$", "price of",
    "stock", "s&p", "nasdaq", "close above", "close below", "all-time high",
    "nba", "nfl", "mlb", "nhl", "premier league", "champions league",
    "super bowl", "world cup", "grand slam", "olympic", "match", "vs.",
    "temperature", "hurricane", "earthquake", "rainfall",
)
_INCLUDE_TOKENS = (
    "election", "president", "prime minister", "approval", "vote", "voters",
    "senate", "congress", "parliament", "coalition", "candidate", "nominee",
    "war", "ceasefire", "peace", "treaty", "sanctions", "invade",
    "policy", "law", "bill", "ban", "legal", "court", "ruling", "impeach",
    "protest", "referendum", "immigration", "tariff", "regulation",
    "resign", "cabinet", "government", "party", "primary", "poll",
)


@dataclass
class LiveMarket:
    id: str
    source: str          # "manifold" | "polymarket"
    question: str
    price: float         # market-implied P(yes) at fetch time, [0,1]
    close_time: Optional[str]  # ISO-8601 or None
    url: str
    volume: float


def is_belief_causal(question: str) -> bool:
    ql = question.lower()
    if any(t in ql for t in _EXCLUDE_TOKENS):
        return False
    return any(t in ql for t in _INCLUDE_TOKENS)


def _get_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_manifold(
    terms: Optional[List[str]] = None,
    limit_per_term: int = 40,
) -> List[LiveMarket]:
    """Open binary markets from Manifold (public API, no key)."""
    terms = terms or ["election", "president", "war", "government", "policy"]
    out: dict = {}
    for term in terms:
        qs = urllib.parse.urlencode({
            "term": term, "filter": "open", "contractType": "BINARY",
            "sort": "liquidity", "limit": limit_per_term,
        })
        try:
            rows = _get_json(f"https://api.manifold.markets/v0/search-markets?{qs}")
        except Exception:
            continue
        for m in rows:
            if m.get("outcomeType") != "BINARY" or m.get("isResolved"):
                continue
            q = m.get("question", "")
            if not is_belief_causal(q):
                continue
            close_ms = m.get("closeTime")
            close_iso = (
                datetime.fromtimestamp(close_ms / 1000, tz=timezone.utc).isoformat()
                if close_ms else None
            )
            out[m["id"]] = LiveMarket(
                id=m["id"], source="manifold", question=q,
                price=float(m.get("probability", 0.5)),
                close_time=close_iso,
                url=m.get("url", ""),
                volume=float(m.get("volume", 0.0)),
            )
    return list(out.values())


def fetch_polymarket(limit: int = 100) -> List[LiveMarket]:
    """Open markets from Polymarket's Gamma API (public, region-blocked
    on some networks — returns [] where unreachable)."""
    qs = urllib.parse.urlencode({
        "closed": "false", "active": "true", "limit": limit,
        "order": "liquidity", "ascending": "false",
    })
    try:
        rows = _get_json(f"https://gamma-api.polymarket.com/markets?{qs}")
    except Exception:
        return []
    out = []
    for m in rows:
        q = m.get("question", "")
        if not q or not is_belief_causal(q):
            continue
        try:
            prices = json.loads(m.get("outcomePrices", "[]"))
            price = float(prices[0]) if prices else 0.5
        except Exception:
            price = 0.5
        out.append(LiveMarket(
            id=str(m.get("id")), source="polymarket", question=q,
            price=price, close_time=m.get("endDate"),
            url=f"https://polymarket.com/market/{m.get('slug', '')}",
            volume=float(m.get("volumeNum", 0.0) or 0.0),
        ))
    return out


def fetch_open_markets(
    sources: tuple = ("polymarket", "manifold"),
    min_volume: float = 0.0,
) -> List[LiveMarket]:
    """All reachable sources, deduplicated by question text."""
    fetchers = {"polymarket": fetch_polymarket, "manifold": fetch_manifold}
    seen_questions = set()
    out: List[LiveMarket] = []
    for s in sources:
        for m in fetchers[s]():
            key = m.question.strip().lower()
            if key in seen_questions or m.volume < min_volume:
                continue
            seen_questions.add(key)
            out.append(m)
    return out


def horizon_days(m: LiveMarket, cap: int = 3650) -> int:
    if not m.close_time:
        return 90
    try:
        close = datetime.fromisoformat(m.close_time.replace("Z", "+00:00"))
        days = (close - datetime.now(timezone.utc)).days
        return max(1, min(days, cap))
    except Exception:
        return 90
