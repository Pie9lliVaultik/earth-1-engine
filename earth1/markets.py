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


# ── civilization-scope gate (rule v1-2026-08-16) ───────────────────────
#
# is_belief_causal is token include/exclude only; the backtest showed it
# admits personal-resolution ("Will I vote...") and market-meta ("Will
# anyone help me find an edge...") questions. The scope gate asks the
# real question: does this market resolve on CIVILIZATION-scale human
# behavior? Two tiers: free heuristics, then one cached Haiku call.
# Rule committed before further record accumulation; applied forward;
# existing rows retro-labeled, never deleted; scoreboards print scoped
# and unscoped side by side forever.

SCOPE_RULE_VERSION = "v1-2026-08-16"

_META_TOKENS = ("this market", "anyone help", "find me",
                "resolves yes if i", "@")
_PRONOUN_RE = None  # compiled lazily

_SCOPE_PROMPT = (
    "Classify what this prediction-market question resolves on. Reply "
    "with exactly one token: AGGREGATE (resolves on aggregate human "
    "behavior - elections, polls, adoption, macro indicators), "
    "INSTITUTION (resolves on a decision by a government, court, "
    "central bank, legislature, or major organization), NATURAL "
    "(resolves on a physical/natural event), INDIVIDUAL (resolves on "
    "one private person's action or circumstance), META (resolves on "
    "the market itself, its creator, or its traders). "
    "Question: {question}"
)

# NATURAL fails scope (divergence from the draft, deliberate): the
# behavioral-response claim covers human REACTION to events, not the
# physical events themselves — the engine has no geophysics.
_SCOPE_PASS = {"AGGREGATE", "INSTITUTION"}
_SCOPE_FAIL = {"NATURAL", "INDIVIDUAL", "META"}


def _protect_us_tokens(question: str) -> str:
    """Replace standalone US/U.S./USA (case-sensitive, the country)
    before lowercasing, so the pronoun regex can't hit them."""
    import re
    return re.sub(r"\b(U\.S\.A?\.?|US|USA)\b", "UNITEDSTATES", question)


def is_civilization_scope(
    market: dict,
    cache_path: str = "data/market_scope_cache.json",
) -> tuple:
    """(passed, reason) — does this market resolve on civilization-scale
    behavior? market: dict with at least 'question'; 'id',
    'uniqueBettorCount', 'volume' used when present."""
    import json as _json
    import os
    import re
    from pathlib import Path

    global _PRONOUN_RE
    if _PRONOUN_RE is None:
        _PRONOUN_RE = re.compile(
            r"\b(i|me|my|mine|we|our|us|you|your)\b")

    question = market.get("question", "")

    # Tier 1a: personal resolution
    protected = _protect_us_tokens(question).lower()
    if _PRONOUN_RE.search(protected):
        return False, "personal_resolution"

    # Tier 1b: market-meta
    ql = question.lower()
    if any(t in ql for t in _META_TOKENS):
        return False, "market_meta"

    # Tier 1c: thin market (fields present in Manifold market JSON)
    if ("uniqueBettorCount" in market
            and market.get("uniqueBettorCount", 0) < 15):
        return False, "thin_market"
    if ("volume" in market and market.get("volume", 0) < 100):
        return False, "thin_market"

    # Tier 2: LLM scope class, cached, degrades OPEN without a key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return True, "tier2_skipped"

    cache = {}
    cp = Path(cache_path)
    if cp.exists():
        cache = _json.loads(cp.read_text())
    mid = str(market.get("id", question[:64]))
    if mid in cache:
        cls = cache[mid]["class"]
    else:
        import anthropic
        from datetime import datetime, timezone
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=8,
            temperature=0,
            messages=[{"role": "user",
                       "content": _SCOPE_PROMPT.format(question=question)}],
        )
        cls = resp.content[0].text.strip().upper()
        if cls not in _SCOPE_PASS | _SCOPE_FAIL:
            cls = "AGGREGATE"          # malformed -> degrade open, cached
        cache[mid] = {"class": cls,
                      "model": "claude-haiku-4-5-20251001",
                      "ts": datetime.now(timezone.utc).isoformat()}
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(_json.dumps(cache, indent=1))

    if cls in _SCOPE_PASS:
        return True, f"scope_{cls.lower()}"
    return False, f"scope_{cls.lower()}"
