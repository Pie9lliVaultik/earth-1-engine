"""Prospective-register market fetch (founder order 2026-09-01 item 1).

Ports VNF's keyless endpoints: Polymarket gamma public-search + Kalshi
elections API, browser UA. Pulls open binary in-class questions
resolving before 2026-11-15, applies VNF's disqualifiers (liquidity
floor $5k / Kalshi volume 10k, dead/past markets dropped), classifies
by keyword, writes a raw snapshot with first-seen prices.

usage: fetch_markets.py <out.json>
"""
import json
import re
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
DEADLINE = "2026-11-15"
CLASS_KW = {
    "election": ["election", "governor", "senate race", "presidential",
                 "midterm", "wins the", "elected"],
    "referendum": ["referendum", "ballot measure", "proposition"],
    "rate_decision": ["fed ", "federal reserve", "interest rate", "ecb",
                      "rate cut", "rate hike", "fomc"],
    "protest": ["protest", "unrest", "strike", "demonstration"],
    "conflict": ["ceasefire", "war ", "invasion", "military strike",
                 "attack on"],
    "market_cascade": ["bank run", "default on", "recession declared",
                       "circuit breaker", "bitcoin above", "s&p"],
    "policy": ["signs a bill", "legislation", "policy", "ban on",
               "tariff"],
}
QUERIES = ["election", "referendum", "interest rate", "fed", "ceasefire",
           "protest", "recession", "tariff"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def classify(text):
    t = " " + text.lower() + " "
    for cls, kws in CLASS_KW.items():
        if any(k in t for k in kws):
            return cls
    return None


def poly():
    out = {}
    for q in QUERIES:
        try:
            d = get("https://gamma-api.polymarket.com/public-search?q="
                    + urllib.request.quote(q)
                    + "&limit_per_type=20&events_status=active")
        except Exception as e:
            print("poly fail", q, e)
            continue
        for ev in d.get("events", []):
            for m in ev.get("markets", []) or []:
                try:
                    end = (m.get("endDate") or ev.get("endDate") or "")[:10]
                    if not end or end >= DEADLINE or end <= "2026-09-01":
                        continue
                    prices = m.get("outcomePrices")
                    if isinstance(prices, str):
                        prices = json.loads(prices)
                    outcomes = m.get("outcomes")
                    if isinstance(outcomes, str):
                        outcomes = json.loads(outcomes)
                    if not prices or len(prices) != 2 or \
                            [o.lower() for o in (outcomes or [])] != ["yes", "no"]:
                        continue
                    liq = float(m.get("liquidityNum") or m.get("liquidity")
                                or 0)
                    if liq < 5000:
                        continue
                    ques = m.get("question") or ev.get("title") or ""
                    cls = classify(ques + " " + (ev.get("title") or ""))
                    if cls is None:
                        continue
                    mid = "poly:" + str(m.get("id") or m.get("slug"))
                    out[mid] = {"source": "polymarket", "id": mid,
                                "question": ques.strip(), "class": cls,
                                "p_yes": float(prices[0]),
                                "resolution_date": end, "liquidity": liq}
                except Exception:
                    continue
        time.sleep(0.4)
    return out


def kalshi():
    out = {}
    for q in QUERIES:
        try:
            d = get("https://api.elections.kalshi.com/v1/search/series?query="
                    + urllib.request.quote(q))
        except Exception as e:
            print("kalshi fail", q, e)
            continue
        for row in d.get("current_page", [])[:12]:
            et = row.get("event_ticker")
            if not et or int(row.get("recent_volume") or 0) < 10000:
                continue
            try:
                md = get("https://api.elections.kalshi.com/trade-api/v2/"
                         "markets?event_ticker=" + urllib.request.quote(et)
                         + "&limit=200")
            except Exception:
                continue
            for m in md.get("markets", []):
                try:
                    if m.get("status") != "active":
                        continue
                    end = (m.get("close_time") or "")[:10]
                    if not end or end >= DEADLINE or end <= "2026-09-01":
                        continue
                    yb, ya = m.get("yes_bid"), m.get("yes_ask")
                    if not yb or not ya:
                        continue
                    p = (yb + ya) / 200.0
                    ques = (row.get("event_title", "") + " — "
                            + (m.get("yes_sub_title") or m.get("subtitle")
                               or m.get("ticker", ""))).strip(" —")
                    cls = classify(ques)
                    if cls is None:
                        continue
                    mid = "kalshi:" + m.get("ticker", et)
                    out[mid] = {"source": "kalshi", "id": mid,
                                "question": ques, "class": cls,
                                "p_yes": p, "resolution_date": end,
                                "volume": row.get("recent_volume")}
                except Exception:
                    continue
        time.sleep(0.4)
    return out


def main(out_path):
    snap = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "deadline": DEADLINE, "ua": "browser (VNF port)",
            "markets": {}}
    snap["markets"].update(poly())
    snap["markets"].update(kalshi())
    json.dump(snap, open(out_path, "w"), indent=1, sort_keys=True)
    from collections import Counter
    c = Counter(v["class"] for v in snap["markets"].values())
    print("FETCHED", len(snap["markets"]), "markets ->", out_path,
          "| by class:", dict(c))


if __name__ == "__main__":
    main(sys.argv[1])
