"""PATH D — live grounding. Direct translation of live_grounding.ts.

This is a TRANSLATION, not a reimplementation. Every constant, prompt,
regex and quality gate is carried over from the old engine's shipping
code (vivid-node-forge, _shared/live_grounding.ts). Supabase calls
become file reads; the Anthropic API call is the same API.

Two steps, as in the original:
  1. rephrase_survey_queries — one Sonnet call, no web search, turns a
     question (including prediction-market phrasing) into 3
     survey-organization-flavoured search queries
  2. search_via_sonnet — one Sonnet call WITH the web_search server
     tool (max 3 uses), returning structured published-polling
     findings, then filtered by the credibility regex

Result is persisted as a live seed with full provenance and
confidence='medium'. Medium-confidence seeds never grade the engine.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
LIVE_MODEL = os.environ.get("EARTH1_LIVE_MODEL", "claude-sonnet-4-5")
FRESHNESS_HOURS_DEFAULT = 168          # 7 days
CONDITION_NUMBER_MAX = 20_000
MAX_WEB_USES = 3
APPROX_COST_USD = 0.04

# verbatim from live_grounding.ts:124
CREDIBLE_ORG_RX = re.compile(
    r"\b(pew|gallup|ipsos|yougov|eurobarometer|afrobarometer|"
    r"latinobar[oó]metro|world values survey|wvs|edelman|kantar|statista|"
    r"morning consult|reuters institute|kaiser family|kff|ipsos mori|"
    r"nielsen|comres|survation|opinium|essex|university of|census bureau|"
    r"eurostat|oecd|un department|world bank|epic[- ]?mra|marist|surveyusa|"
    r"survey usa|emerson|siena|quinnipiac|monmouth|suffolk|change research|"
    r"data for progress|merdeka center|detroit news|bridge michigan|"
    r"public policy polling|ppp|glengariff|hit strategies|fiftyplusone|"
    r"fifty ?plus ?one|tavern research|mo scout)\b", re.I)

LIVE_DIR = Path(__file__).resolve().parents[1] / "data" / "seed_corpus" / "live"


def is_credible(source: str) -> bool:
    return bool(CREDIBLE_ORG_RX.search(str(source or "")))


def _call(body: dict, timeout: int = 300) -> dict:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    req = urllib.request.Request(
        ANTHROPIC_API, data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    return {}


def _text_of(resp: dict) -> str:
    """Claude-5 responses may lead with a thinking block."""
    for b in resp.get("content", []):
        if b.get("type") == "text":
            return b.get("text", "")
    return ""


def _json_of(text: str) -> dict:
    t = (text or "").strip().strip("`").lstrip("json").strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < 0:
        return {}
    try:
        return json.loads(t[a:b + 1])
    except json.JSONDecodeError:
        return {}


def rephrase_survey_queries(question_text: str) -> dict:
    """Step 1 — translation of rephraseSurveyQueries (prompt verbatim)."""
    prompt = f'''The user asked: "{question_text}"

If this is a prediction-market question (starts with "Will X..." or asks about
a future event/outcome), first rewrite it as an opinion-poll question a survey
organization would ask about the underlying attitudes. Examples:
  "Will El-Sayed win the Michigan primary?"
    -> "Do Michigan Democratic primary voters support Abdul El-Sayed for Senate?"
  "Will the California wealth tax pass in Nov 2026?"
    -> "Do California voters support a wealth tax on residents earning over $50M?"
  "Will Trump nominate X to the Fed?"
    -> Keep as-is (external-substrate, not an opinion question).

Then generate 3 search queries that would find published survey or polling
results for the rewritten opinion question. Include organization names as
search terms (Pew, Gallup, Ipsos, YouGov, Eurobarometer, EPIC-MRA, Marist,
Emerson, SurveyUSA, Quinnipiac, Monmouth, Suffolk, Change Research, Data for
Progress, Public Policy Polling, HIT Strategies, Glengariff, Merdeka Center).
If the question combines two topics, split into separate queries.

Return JSON only:
{{ "opinion_form": "the rewritten opinion question, or the original if no rewrite applies",
  "queries": ["query 1", "query 2", "query 3"] }}'''
    out = _json_of(_text_of(_call({
        "model": LIVE_MODEL, "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]})))
    return {"queries": out.get("queries", [])[:MAX_WEB_USES],
            "opinion_form": out.get("opinion_form", question_text),
            "cost_usd": 0.01}


def search_via_sonnet(question_text: str, queries: list) -> dict:
    """Step 2 — translation of searchViaSonnet (prompt verbatim)."""
    qs = queries or [question_text]
    query_list = "\n".join(f"  {i + 1}. {q}" for i, q in enumerate(qs))
    prompt = f'''Find published survey or polling results for this question:
"{question_text}"

Use web_search up to {MAX_WEB_USES} times, once per query below (one search per line, in order). These queries have been rephrased into survey-organization language:
{query_list}

Look for results from established research organizations: Pew, Gallup, Ipsos, YouGov, Eurobarometer, Afrobarometer, Latinobarómetro, government statistics agencies, or major university research centers.

For each result found across all searches, return JSON only (no prose before or after):
{{
  "results": [
    {{
      "source": "organization name",
      "url": "source url",
      "date": "YYYY-MM",
      "question_as_asked": "exact wording",
      "findings": [
        {{ "population": "ISO2 country code or 'global'", "yes_pct": 0.XX, "sample_size": N }}
      ]
    }}
  ]
}}

If no credible survey data exists, return {{ "results": [] }}.
Deduplicate results across queries by URL — do not list the same source twice.
Only include results from named organizations with published methodology. No blog posts, no social media, no opinion articles.'''
    resp = _call({
        "model": LIVE_MODEL, "max_tokens": 4000,
        "tools": [{"type": "web_search_20250305", "name": "web_search",
                   "max_uses": MAX_WEB_USES}],
        "messages": [{"role": "user", "content": prompt}]})
    out = _json_of(_text_of(resp))
    return {"results": out.get("results", []), "cost_usd": APPROX_COST_USD}


def _coerce_pct(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x > 1.0 and x <= 100.0:      # percentages come both ways
        x = x / 100.0
    return x if 0.0 <= x <= 1.0 else None


def live_ground(question_text: str, population: str | None = None,
                persist: bool = True):
    """The Path D entry point used by earth1.grounding.ground()."""
    from earth1.grounding import Grounding
    try:
        r = rephrase_survey_queries(question_text)
        search = search_via_sonnet(r["opinion_form"], r["queries"])
    except Exception as exc:                       # network/API failure
        return Grounding("forward-estimate", "low",
                         note=f"live search failed: {str(exc)[:120]}")

    seen_urls, credible = set(), []
    for res in search["results"]:
        url = (res.get("url") or "").strip()
        if url in seen_urls:                       # dedup by URL, as in TS
            continue
        seen_urls.add(url)
        if is_credible(res.get("source", "")):
            credible.append(res)
    if not credible:
        return Grounding("forward-estimate", "low",
                         note="no credible survey sources returned")

    targets: dict = {}
    for res in credible:
        for f in res.get("findings", []):
            pop = str(f.get("population", "")).upper()[:6]
            pct = _coerce_pct(f.get("yes_pct"))
            if pop and pct is not None:
                targets.setdefault(pop, []).append(pct)
    agg = {k: float(sum(v) / len(v)) for k, v in targets.items()}
    if not agg:
        return Grounding("forward-estimate", "low",
                         note="credible sources carried no usable findings")

    best = credible[0]
    nat = agg.get((population or "").upper()) or agg.get("GLOBAL") or \
        float(sum(agg.values()) / len(agg))
    g = Grounding(
        "live-grounded", "medium",
        seed_id=f"live:{abs(hash(question_text)) % 10**10}",
        matched_question=best.get("question_as_asked"),
        cohort_targets={}, national_target=nat,
        source=best.get("source"), source_url=best.get("url"),
        date=best.get("date"),
        note=f"{len(credible)} credible source(s); "
             f"populations: {','.join(sorted(agg))}; "
             f"cost ~${search['cost_usd'] + 0.01:.2f}")
    if persist:
        try:
            LIVE_DIR.mkdir(parents=True, exist_ok=True)
            rec = {"id": g.seed_id, "question_text": question_text,
                   "opinion_form": r["opinion_form"],
                   "source": g.source, "source_url": g.source_url,
                   "date": g.date, "population_targets": agg,
                   "national_target": nat, "confidence": "medium",
                   "calibration_source": "live-grounded",
                   "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                               time.gmtime()),
                   "freshness_hours": FRESHNESS_HOURS_DEFAULT,
                   "excluded_from_grading": True}
            (LIVE_DIR / f"{g.seed_id}.json").write_text(
                json.dumps(rec, indent=1))
        except OSError:
            pass
    return g


def is_stale(rec: dict) -> bool:
    """Freshness check — the old engine re-ran search after 7 days."""
    try:
        t = time.strptime(rec["fetched_at"], "%Y-%m-%dT%H:%M:%SZ")
    except (KeyError, ValueError):
        return True
    age_h = (time.time() - time.mktime(t)) / 3600.0
    return age_h > float(rec.get("freshness_hours", FRESHNESS_HOURS_DEFAULT))
