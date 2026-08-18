"""THE SIGNAL BUS — the engine's sensory system, OBSERVE-ONLY.

Translated from the old engine's collect-signals + world-pulse, which
pulled four signal families into one bus and — critically — gated them:

    "nothing here moves a prediction until the two-week correlation
     review says it earns the right to."

Earth-1's news_perception.py skipped both halves: no sensory layer
feeding it, and no observation period before an LLM-authored force
event was allowed to move the world. This module restores the sensor
AND the gate.

Families (all free, no key required except where noted):
  gdelt_tone   GDELT DOC 2.0 timelinetone — global news tone per topic,
               ~15-minute freshness
  gdelt_volume GDELT DOC 2.0 timelinevol — attention volume per topic
  rss          headline stream from established outlets, domain- and
               region-classified, deduplicated, 24h expiry
  macro        World Bank indicators (inflation, unemployment)

THE EARNED-RIGHT GATE: a signal family may only influence a prediction
after `data/signal_earned_rights.json` records a passing correlation
review for it. Until then every reading is stored with
`influences_prediction: false`. The gate is checked in code, not by
convention — `may_influence()` is the only way through.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
BUS = DATA / "signal_bus"
RIGHTS = DATA / "signal_earned_rights.json"
OBSERVATION_DAYS = 14          # the old engine's two-week review

GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
WB_API = "https://api.worldbank.org/v2/country/{cc}/indicator/{ind}"

RSS_FEEDS = {
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "reuters_wire": "https://www.reutersagency.com/feed/?best-topics=all&post_type=best",
    "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "ap": "https://rsshub.app/apnews/topics/apf-topnews",
    "guardian": "https://www.theguardian.com/world/rss",
}
DOMAIN_RX = [
    ("politics", re.compile(r"\b(election|parliament|senate|president|vote|"
                            r"minister|coalition|referendum)\b", re.I)),
    ("finance", re.compile(r"\b(inflation|market|stocks|economy|tariff|"
                           r"central bank|rates|recession)\b", re.I)),
    ("conflict", re.compile(r"\b(strike|attack|war|troops|ceasefire|"
                            r"missile|invasion)\b", re.I)),
    ("climate", re.compile(r"\b(climate|emission|wildfire|flood|drought|"
                           r"heatwave)\b", re.I)),
    ("health", re.compile(r"\b(outbreak|virus|vaccine|hospital|pandemic)\b",
                          re.I)),
    ("ai", re.compile(r"\b(artificial intelligence|\bAI\b|chatbot|model "
                      r"release|openai|anthropic)\b", re.I)),
]


@dataclass
class Reading:
    family: str
    key: str                       # topic / country / feed
    value: float | None
    unit: str
    observed_at: str
    source: str
    influences_prediction: bool = False   # flipped ONLY by the gate
    detail: dict = field(default_factory=dict)


def _get(url: str, timeout: int = 45) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "earth1/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def gdelt_tone(topic: str, timespan: str = "7d") -> Reading | None:
    """Mean news tone for a topic — GDELT DOC 2.0, free, no key."""
    q = urllib.parse.urlencode({"query": topic, "mode": "timelinetone",
                                "timespan": timespan, "format": "json"})
    try:
        payload = json.loads(_get(f"{GDELT_DOC}?{q}"))
        series = payload.get("timeline", [{}])[0].get("data", [])
        vals = [float(p["value"]) for p in series if p.get("value") is not None]
        if not vals:
            return None
        return Reading("gdelt_tone", topic, sum(vals) / len(vals),
                       "avg_tone", _now(), "GDELT DOC 2.0",
                       detail={"n_points": len(vals), "timespan": timespan,
                               "last": vals[-1]})
    except Exception as exc:
        return Reading("gdelt_tone", topic, None, "avg_tone", _now(),
                       "GDELT DOC 2.0", detail={"error": str(exc)[:120]})


def gdelt_volume(topic: str, timespan: str = "7d") -> Reading | None:
    q = urllib.parse.urlencode({"query": topic, "mode": "timelinevol",
                                "timespan": timespan, "format": "json"})
    try:
        payload = json.loads(_get(f"{GDELT_DOC}?{q}"))
        series = payload.get("timeline", [{}])[0].get("data", [])
        vals = [float(p["value"]) for p in series if p.get("value") is not None]
        if not vals:
            return None
        return Reading("gdelt_volume", topic, sum(vals) / len(vals),
                       "pct_coverage", _now(), "GDELT DOC 2.0",
                       detail={"n_points": len(vals), "last": vals[-1]})
    except Exception as exc:
        return Reading("gdelt_volume", topic, None, "pct_coverage", _now(),
                       "GDELT DOC 2.0", detail={"error": str(exc)[:120]})


def _classify(title: str) -> str:
    """Regex tier — fast, free, and deliberately the FALLBACK."""
    for name, rx in DOMAIN_RX:
        if rx.search(title or ""):
            return name
    return "general"


def classify_runtime(titles: list, allow_live: bool = True) -> list:
    """RUNTIME classification — resolved live, like grounding.

    The regex list under-hits (most headlines fell to 'general' on the
    first sweep) and hardcoding a bigger list just moves the ceiling.
    One batched Sonnet call labels the whole sweep with domain AND
    region, and the regex tier remains the offline fallback so the bus
    never depends on the network to keep observing.
    """
    if not titles:
        return []
    if not allow_live or not os.environ.get("ANTHROPIC_API_KEY"):
        return [{"domain": _classify(t), "region": None,
                 "by": "regex"} for t in titles]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    prompt = (
        "Classify each headline by DOMAIN and REGION.\n"
        "domain: politics | finance | conflict | climate | health | ai | "
        "society | sport | general\n"
        "region: ISO2 country code the headline is ABOUT, or GLOBAL, or "
        "NONE\n\n"
        f"{numbered}\n\n"
        'Return JSON only: {"items":[{"n":1,"domain":"...","region":"..."}]}')
    try:
        from earth1.live_search import _call, _json_of, _text_of, LIVE_MODEL
        out = _json_of(_text_of(_call({
            "model": LIVE_MODEL, "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}]})))
        by_n = {int(i["n"]): i for i in out.get("items", []) if "n" in i}
        res = []
        for i, t in enumerate(titles, start=1):
            it = by_n.get(i)
            res.append({"domain": (it or {}).get("domain") or _classify(t),
                        "region": (it or {}).get("region"),
                        "by": "llm" if it else "regex"})
        return res
    except Exception:
        return [{"domain": _classify(t), "region": None, "by": "regex"}
                for t in titles]


def rss_pulse(limit_per_feed: int = 25, allow_live: bool = True) -> list:
    """Headline stream, domain-classified at RUNTIME and deduplicated."""
    out, seen = [], set()
    for name, url in RSS_FEEDS.items():
        try:
            xml = _get(url, timeout=30)
        except Exception:
            continue
        titles = re.findall(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
                            xml, re.S)[1:limit_per_feed + 1]
        for t in titles:
            t = re.sub(r"\s+", " ", t).strip()
            k = t.lower()[:80]
            if not t or k in seen:
                continue
            seen.add(k)
            out.append(Reading("rss", "general", None, "headline", _now(),
                               name, detail={"title": t[:300]}))
    labels = classify_runtime([r.detail["title"] for r in out],
                              allow_live=allow_live)
    for r, lab in zip(out, labels):
        r.key = lab["domain"]
        r.detail["region"] = lab["region"]
        r.detail["classified_by"] = lab["by"]
    return out


def worldbank(cc: str, indicator: str = "FP.CPI.TOTL.ZG") -> Reading | None:
    """Macro pressure — World Bank indicator, free, no key."""
    url = WB_API.format(cc=cc, ind=indicator) + "?format=json&per_page=5"
    try:
        payload = json.loads(_get(url))
        rows = payload[1] if len(payload) > 1 else []
        for r in rows:
            if r.get("value") is not None:
                return Reading("macro", f"{cc}:{indicator}",
                               float(r["value"]), "pct", _now(),
                               "World Bank", detail={"year": r.get("date")})
    except Exception as exc:
        return Reading("macro", f"{cc}:{indicator}", None, "pct", _now(),
                       "World Bank", detail={"error": str(exc)[:120]})
    return None


# ── the earned-right gate ──

def _rights() -> dict:
    if RIGHTS.exists():
        return json.loads(RIGHTS.read_text())
    return {"_note": ("A signal family may influence predictions ONLY "
                      "after a passing correlation review over at least "
                      f"{OBSERVATION_DAYS} days. Until then it is "
                      "observed and stored, never applied."),
            "families": {}}


def may_influence(family: str) -> bool:
    """The ONLY way a signal is allowed to move a prediction."""
    fam = _rights().get("families", {}).get(family)
    if not fam or not fam.get("earned"):
        return False
    return bool(fam.get("review_passed") and
                fam.get("observation_days", 0) >= OBSERVATION_DAYS)


def record(readings: list) -> dict:
    """Persist a batch, stamping each with its gate status."""
    BUS.mkdir(parents=True, exist_ok=True)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    path = BUS / f"{day}.jsonl"
    n_ok = 0
    with path.open("a") as f:
        for r in readings:
            if r is None:
                continue
            r.influences_prediction = may_influence(r.family)
            f.write(json.dumps(asdict(r)) + "\n")
            n_ok += 1
    fams = sorted({r.family for r in readings if r is not None})
    return {"written": n_ok, "file": str(path), "families": fams,
            "influencing": [f for f in fams if may_influence(f)]}


def collect(topics: list | None = None, countries: list | None = None) -> dict:
    """One sweep of the bus. Observe-only unless a family earned rights."""
    topics = topics or ["inflation", "immigration", "climate change",
                        "artificial intelligence", "election"]
    countries = countries or ["US", "DE", "BR", "IN"]
    readings = []
    for t in topics:
        readings.append(gdelt_tone(t))
        readings.append(gdelt_volume(t))
    readings.extend(rss_pulse())
    for cc in countries:
        readings.append(worldbank(cc))
    return record([r for r in readings if r is not None])


# ── the correlation review that lets a family EARN rights ──

def correlation_review(family: str, outcome_series: dict,
                       min_days: int = OBSERVATION_DAYS,
                       min_abs_r: float = 0.30) -> dict:
    """Run the review the gate depends on — from accumulated bus data.

    `outcome_series` maps YYYY-MM-DD -> the observed quantity the signal
    is supposed to predict (an opinion reading, a resolved market, a
    survey share). The review pairs each day's signal value with the
    NEXT observed outcome, correlates them, and writes the verdict into
    data/signal_earned_rights.json.

    A family earns influence ONLY with (a) at least `min_days` of
    observation and (b) |r| >= min_abs_r. Anything else is recorded as
    a failed review — which is a result, not a bug.
    """
    import numpy as _np
    days, vals = [], []
    for p in sorted(BUS.glob("*.jsonl")):
        day = p.stem
        xs = []
        for line in p.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("family") == family and r.get("value") is not None:
                xs.append(float(r["value"]))
        if xs:
            days.append(day)
            vals.append(float(_np.mean(xs)))

    paired_x, paired_y = [], []
    for d, v in zip(days, vals):
        later = [k for k in sorted(outcome_series) if k > d]
        if later:
            paired_x.append(v)
            paired_y.append(float(outcome_series[later[0]]))
    n_days = len(days)
    r = (float(_np.corrcoef(paired_x, paired_y)[0, 1])
         if len(paired_x) >= 3 else None)
    earned = bool(r is not None and abs(r) >= min_abs_r
                  and n_days >= min_days)
    rights = _rights()
    rights.setdefault("families", {})[family] = {
        "earned": earned, "review_passed": bool(r is not None and
                                                abs(r) >= min_abs_r),
        "observation_days": n_days, "pairs": len(paired_x),
        "correlation": r, "min_abs_r": min_abs_r,
        "reviewed_at": _now(),
        "verdict": ("EARNED" if earned else
                    "insufficient observation" if n_days < min_days else
                    "failed correlation review"),
    }
    RIGHTS.write_text(json.dumps(rights, indent=1))
    return rights["families"][family]
