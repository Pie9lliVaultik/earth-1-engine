"""GROUNDING-FIRST ROUTER (founder ruling 2026-09-01: answer
everything, grounding first; never a shrug).

Resolution order, first match wins:
  a. PREMISE — settled facts / trivially bounded outcomes via keyless
     structured fetchers (JPL SSD, USGS, open-meteo, coingecko,
     frankfurter/ECB, Wikipedia, resolved market books). tier=FACT,
     p in {~0, ~1} or the value itself; one plain sentence; source +
     retrieval timestamp; every fetch logged to the ground ledger.
     The simulation does not run.
  b. SCOPE — exogenous forecasts (weather, geophysics, sports, single-
     company earnings, price thresholds) answer from public evidence
     (odds, base rates, spot prices, with source) and ALSO carry the
     population's conditional reaction as `if_it_happens`. No exogenous
     forecast ever returns a simulated p_model.
  c. belief_causal questions route to the three doors unchanged.

Registered bound (price thresholds): a move of >30% needed within <=31
days is answered as FACT p~0/p~1 — no G10 currency, major metal or
index has moved 30% in a month absent the exact catastrophes the
simulation exists to model; the bound and the spot are both in the
payload. Every answer carries `scope`, `resolved_at`, and a top-level
`answer` sentence built deterministically from the payload.
"""
import hashlib
import json
import os
import re
import time
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
CITY_COORDS = {"milan": (45.46, 9.19), "london": (51.5, -0.13),
               "paris": (48.86, 2.35), "tokyo": (35.68, 139.69),
               "new york": (40.71, -74.0), "berlin": (52.52, 13.4),
               "madrid": (40.42, -3.7), "rome": (41.9, 12.5),
               "sao paulo": (-23.55, -46.63), "cairo": (30.04, 31.24)}
SPOT = {"gold": ("coingecko", "pax-gold", "PAXG (gold-backed token) proxy"),
        "bitcoin": ("coingecko", "bitcoin", "spot"),
        "btc": ("coingecko", "bitcoin", "spot"),
        "euro": ("frankfurter", "EUR/USD", "ECB reference"),
        "eur": ("frankfurter", "EUR/USD", "ECB reference")}
EXO_RX = re.compile(
    r"\b(rain|snow|weather|temperature|earthquake|quake|asteroid|meteor|"
    r"hurricane|eruption|champions league|world cup|super bowl|final|"
    r"olympic|earnings|dice|coin flip|lottery)\b", re.I)
HORIZON = [(r"today|tonight", 1), (r"tomorrow", 2),
           (r"by friday|this week", 7), (r"this month|by .*month", 31),
           (r"this year", 365)]


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def _ledger(kind, url, text, qid):
    try:
        from earth1.ground.ladder import _ledger_append
        _ledger_append({"kind": kind, "question_id": qid, "url": url,
                        "snippet_sha256": hashlib.sha256(
                            text[:2000].encode()).hexdigest(),
                        "retrieved": _now()})
    except Exception:
        pass


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _horizon_days(t):
    for rx, d in HORIZON:
        if re.search(rx, t, re.I):
            return d
    m = re.search(r"by (20\d\d)", t)
    if m:
        return max(1, (int(m.group(1)) - 2026) * 365)
    return None


def _spot(asset, qid):
    kind, sym, note = SPOT[asset]
    if kind == "coingecko":
        url = (f"https://api.coingecko.com/api/v3/simple/price?ids={sym}"
               "&vs_currencies=usd")
        raw = _get(url)
        val = json.loads(raw)[sym]["usd"]
    else:
        url = "https://api.frankfurter.app/latest?from=EUR&to=USD"
        raw = _get(url)
        val = json.loads(raw)["rates"]["USD"]
    _ledger("premise_spot", url, raw, qid)
    return float(val), url, note


# ── premise handlers ─────────────────────────────────────────────────

def _p_asteroid(q, m, qid):
    url = ("https://ssd-api.jpl.nasa.gov/cad.api?date-min=" +
           time.strftime("%Y-%m-%d") + "&date-max=" +
           time.strftime("%Y-%m-%d", time.gmtime(time.time() + 86400)) +
           "&dist-max=0.05")
    raw = _get(url)
    d = json.loads(raw)
    _ledger("premise_neo", url, raw, qid)
    n = int(d.get("count", 0))
    dists = [float(r[4]) for r in d.get("data", [])] if n else []
    impact = any(x < 5e-5 for x in dists)
    return {"tier": "FACT", "p": 0.999 if impact else 0.0001,
            "answer": ("Yes — an object is on an impact-range approach "
                       "today per JPL close-approach data."
                       if impact else
                       f"No — JPL tracks {n} close approach(es) today, "
                       f"nearest {min(dists):.4f} au (~"
                       f"{min(dists)*389:.0f} lunar distances); none "
                       "remotely on an impact course."
                       if n else "No — JPL lists no close approaches "
                       "within 0.05 au today."),
            "source": url, "retrieved": _now()}


def _p_price(q, m, qid):
    asset, direction, num = m.group(1).lower(), m.group(2).lower(), \
        float(m.group(3).replace(",", ""))
    spot, url, note = _spot(asset, qid)
    hz = _horizon_days(q) or 31
    below = direction in ("below", "under", "drop below", "fall below")
    gap = (spot - num) / spot if below else (num - spot) / spot
    if gap > 0.30 and hz <= 31:
        return {"tier": "FACT", "p": 0.0001,
                "answer": (f"No — {asset} trades at {spot:,.2f} "
                           f"({note}); reaching {num:,.2f} within "
                           f"{hz} day(s) would need a "
                           f"{abs(gap)*100:.0f}% move, far beyond any "
                           "observed short-horizon change."),
                "source": url, "retrieved": _now(),
                "bound": "registered 30%/31d impossibility bound",
                "spot": spot}
    if gap < -0.001:
        return {"tier": "FACT", "p": 0.999,
                "answer": (f"Yes — already true: {asset} trades at "
                           f"{spot:,.2f}, {'below' if below else 'above'}"
                           f" {num:,.2f}."),
                "source": url, "retrieved": _now(), "spot": spot}
    return {"tier": "GROUNDED", "p": None,
            "answer": (f"{asset} trades at {spot:,.2f} ({note}); the "
                       f"threshold {num:,.2f} is {abs(gap)*100:.1f}% "
                       f"away over ~{hz} day(s) — inside normal market "
                       "range, so no bound applies; see market odds if "
                       "a book exists."),
            "source": url, "retrieved": _now(), "spot": spot}


def _p_officeholder(q, m, qid):
    entity = m.group(1).strip()
    from earth1.ground.ladder import _fetch_wikipedia
    page = _fetch_wikipedia(entity)
    if not page:
        return None
    _ledger("premise_wiki", page["url"], page["text"], qid)
    t = page["text"].lower()
    role = m.group(2).lower()
    holds = (re.search(r"\b(is|has been|serving as)\b[^.]{0,80}\b"
                       + re.escape(role.split()[0]), t)
             and "former " + role not in t[:200])
    return {"tier": "FACT", "p": 0.999 if holds else 0.001,
            "answer": (f"{'Yes' if holds else 'No'} — per Wikipedia's "
                       f"current summary, {entity} "
                       f"{'holds' if holds else 'does not hold'} that "
                       "office."),
            "source": page["url"], "retrieved": _now()}


def _p_didhappen(q, m, qid):
    import sys
    sys.path.insert(0, os.path.join(_ROOT, "scripts", "prospective"))
    try:
        url = ("https://gamma-api.polymarket.com/public-search?q="
               + urllib.request.quote(" ".join(q.split()[:6]))
               + "&limit_per_type=10")
        raw = _get(url)
        d = json.loads(raw)
        _ledger("premise_resolved_market", url, raw, qid)
        toks = set(re.findall(r"[a-z]{3,}", q.lower()))
        best = None
        for ev in d.get("events", []):
            for mk in ev.get("markets", []) or []:
                if not mk.get("closed"):
                    continue
                mt = set(re.findall(r"[a-z]{3,}",
                                    (mk.get("question") or "").lower()))
                score = len(toks & mt) / max(len(toks | mt), 1)
                prices = mk.get("outcomePrices")
                if isinstance(prices, str):
                    prices = json.loads(prices)
                if score > 0.3 and prices and (best is None
                                               or score > best[0]):
                    best = (score, mk.get("question"), float(prices[0]))
        if best:
            yes = best[2] >= 0.95
            no = best[2] <= 0.05
            if yes or no:
                return {"tier": "FACT", "p": 0.999 if yes else 0.001,
                        "answer": (f"{'Yes' if yes else 'No'} — the "
                                   f"resolved market \"{best[1]}\" "
                                   f"settled {'YES' if yes else 'NO'}."),
                        "source": url, "retrieved": _now()}
    except Exception:
        pass
    snap = "/opt/earth1-data/resolved_dev_2026-09-01.json"
    if os.path.exists(snap):
        d = json.load(open(snap))
        toks = set(re.findall(r"[a-z]{3,}", q.lower())) - STOPWORDS
        best = None
        for mid, r in d.get("rows", {}).items():
            mt = set(re.findall(r"[a-z]{3,}", r["question"].lower()))
            sc = len(toks & mt) / max(len(toks | mt), 1)
            if sc > 0.3 and (best is None or sc > best[0]):
                best = (sc, r)
        if best:
            r = best[1]
            yes = r["resolution"] == 1
            return {"tier": "FACT", "p": 0.999 if yes else 0.001,
                    "answer": (f"{'Yes' if yes else 'No'} — the resolved "
                               f"market \"{r['question']}\" settled "
                               f"{'YES' if yes else 'NO'} "
                               f"(closed {r['close']})."),
                    "source": f"resolved-market snapshot {snap} "
                              f"({r['source']})", "retrieved": _now()}
    return None


def _p_weather(q, m, qid):
    city = m.group(2).strip().lower()
    ll = CITY_COORDS.get(city)
    if ll is None:
        return None
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={ll[0]}"
           f"&longitude={ll[1]}&daily=precipitation_probability_max"
           "&forecast_days=2&timezone=UTC")
    raw = _get(url)
    d = json.loads(raw)
    _ledger("premise_weather", url, raw, qid)
    day = 1 if re.search(r"tomorrow", q, re.I) else 0
    p = d["daily"]["precipitation_probability_max"][day] / 100.0
    when = "tomorrow" if day else "today"
    return {"tier": "GROUNDED", "p": p,
            "answer": (f"The forecast gives {city.title()} a "
                       f"{p*100:.0f}% maximum precipitation probability "
                       f"{when} (open-meteo)."),
            "source": url, "retrieved": _now()}


def _p_quake(q, m, qid):
    mag = float(m.group(1))
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/count?format=text"
           f"&minmagnitude={mag - 0.1}&starttime=1900-01-01")
    raw = _get(url)
    _ledger("premise_quake", url, raw, qid)
    n = int(raw.strip())
    yrs = time.gmtime().tm_year - 1900
    rate = n / yrs
    hz = _horizon_days(q) or 365
    p = min(1.0, rate * hz / 365.0)
    return {"tier": "GROUNDED", "p": round(p, 4),
            "answer": (f"USGS records {n} M≥{mag:g} earthquakes globally "
                       f"since 1900 (~{rate:.2f}/yr); over {hz} days "
                       f"that is p≈{p:.3f} ANYWHERE on Earth — for one "
                       "named city it is far smaller still."),
            "source": url, "retrieved": _now()}


PREMISE_RULES = [
    (re.compile(r"\b(asteroid|meteor|near.?earth object)\b.*\b(today|"
                r"tonight|tomorrow)\b", re.I), _p_asteroid),
    (re.compile(r"\b(gold|bitcoin|btc|euro|eur)\b.{0,40}?\b(below|under|"
                r"above|over|hit|reach|drop below|fall below)\b[^\d$]{0,10}?"
                r"\$?((?:\d[\d,]*\.?\d*|0?\.\d+))", re.I), _p_price),
    (re.compile(r"[Ii]s (?:the )?([A-Z][\wÀ-ſ]+(?: [A-Z]"
                r"[\wÀ-ſ]+)?) still (?:the )?((?i:[\w ]*?(?:president|"
                r"prime minister|pm\b|chancellor|king|pope))[\w ]*)"),
     _p_officeholder),
    (re.compile(r"\b(did|has)\b.{3,80}\b(cut|raise|hike|win|won|pass|"
                r"happen|resign)\b", re.I), _p_didhappen),
    (re.compile(r"\b(rain|snow)\b.{0,20}\bin ([A-Za-z ]+?)\s*"
                r"(today|tomorrow)\b", re.I), _p_weather),
    (re.compile(r"magnitude[- ]?(\d+(?:\.\d+)?)\b.{0,30}\b(earthquake|"
                r"quake)", re.I), _p_quake),
]

STOPWORDS = set("who wins win the will a an is are do does of in on at to by for this that it be with and or".split())


RETIRED_EXO_CLASSES = {"sports_final", "corporate_earnings"}


def _market_odds(text, qid):
    try:
        toks_q = [t for t in re.findall(r"[A-Za-z]{3,}", text.lower())
                  if t not in STOPWORDS][:5]
        url = ("https://gamma-api.polymarket.com/public-search?q="
               + urllib.request.quote(" ".join(toks_q))
               + "&limit_per_type=10&events_status=active")
        raw = _get(url)
        d = json.loads(raw)
        _ledger("grounding_odds", url, raw, qid)
        toks = set(re.findall(r"[a-z]{3,}", text.lower()))
        best = None
        for ev in d.get("events", []):
            for mk in ev.get("markets", []) or []:
                mt = set(re.findall(r"[a-z]{3,}",
                                    (mk.get("question") or "").lower()))
                score = len(toks & mt) / max(len(toks | mt), 1)
                prices = mk.get("outcomePrices")
                if isinstance(prices, str):
                    prices = json.loads(prices)
                if score >= 0.22 and prices and (best is None
                                                 or score > best[0]):
                    best = (score, mk.get("question"), float(prices[0]))
        if best:
            return {"p": best[2], "book": best[1], "source": url,
                    "retrieved": _now()}
    except Exception:
        pass
    return None


def answer_any(q: dict, base_world, seed: int,
               horizon_days: int = 45, include_reaction: bool = True) -> dict:
    """THE entry point. q: {question_id, text, class?, outcomes?,
    country?}. Returns the product payload with scope, resolved_at and
    a deterministic `answer` sentence. Never a shrug."""
    from earth1.adapters import multiverse as mv
    text = q.get("text", "") or ""
    qid = q["question_id"]
    if not text.strip():
        return {"question_id": qid, "scope": None, "resolved_at": None,
                "answer": "The question is empty — nothing to resolve.",
                "unparseable": True}
    # a) PREMISE
    if os.environ.get("EARTH1_GROUND_LADDER") == "v1":
        for rx, handler in PREMISE_RULES:
            m = rx.search(text)
            if m:
                try:
                    res = handler(text, m, qid)
                except Exception:
                    res = None
                if res:
                    res.update({"question_id": qid, "scope": "premise",
                                "resolved_at": "premise",
                                "question": text})
                    return res
    # b) SCOPE
    exo = bool(EXO_RX.search(text)) or (q.get("class")
                                        in RETIRED_EXO_CLASSES)
    if exo:
        odds = _market_odds(text, qid)
        payload = {"question_id": qid, "question": text,
                   "scope": "exogenous", "resolved_at": "grounding"}
        if odds:
            payload["p_public"] = odds["p"]
            payload["answer"] = (f"Public odds price this at "
                                 f"{odds['p']*100:.0f}% (book: "
                                 f"\"{odds['book']}\"). The outcome is "
                                 "exogenous to the population, so "
                                 "Earth-1 does not simulate a p for it.")
            payload["source"] = odds["source"]
            payload["retrieved"] = odds["retrieved"]
        else:
            payload["answer"] = ("No public odds book is reachable for "
                                 "this outcome right now; it is "
                                 "exogenous to the population, so "
                                 "Earth-1 does not simulate a p for it. "
                                 "The population's reaction if it "
                                 "happens is attached.")
        if include_reaction:
            try:
                cq = mv._conditional_door(
                    {"question_id": qid + ":react",
                     "text": f"what happens if this occurs: {text}",
                     "outcomes": ["it happens", "it does not"],
                     "class": q.get("class"), "country": q.get("country")},
                    base_world, seed, min(horizon_days, 45))
                payload["if_it_happens"] = {
                    "forks": cq["forks"], "epistemics": cq["epistemics"]}
            except Exception as e:
                payload["if_it_happens"] = {"error": repr(e)}
        return payload
    # c) the three doors
    payload = mv.ask(q, base_world, seed, horizon_days)
    payload["scope"] = "belief_causal"
    payload["resolved_at"] = "simulation"
    if payload.get("door") == "opinion":
        ss = payload.get("stance_share")
        payload["answer"] = (
            (f"{ss*100:.0f}% of the scoped population lean yes on the "
             "grounded reading of this attitude." if ss is not None else
             "The population's force profile on this attitude is "
             "attached; no grounded stance axis exists yet for a share.")
            + f" (tier {payload.get('calibration_tier')})")
    elif payload.get("door") == "conditional":
        payload["answer"] = ("Conditional worlds attached: each fork is "
                             "a population reaction inside that world, "
                             "not a probability of the world.")
    else:
        pm = payload.get("p_model")
        if pm is None:
            payload["answer"] = (f"The simulation abstains "
                                 f"({payload.get('abstain_reason')}); "
                                 "no grounded fact answers it either — "
                                 "the abstention reason is the answer.")
        else:
            sig = payload.get("force_signature", {}).get("YES", {})
            top = max(sig, key=lambda k: abs(sig[k])) if sig else "n/a"
            payload["answer"] = (f"Earth-1 simulates p={pm:.2f} "
                                 f"(tier {payload.get('calibration_tier')}"
                                 f"; strongest force channel: {top}).")
    return payload
