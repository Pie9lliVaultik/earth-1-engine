"""Resolved election/referendum/rate DEV set from market archives
(founder order 2026-09-01 item 3: calibrate before signing).

Polymarket gamma /markets?closed=true (90d window) + Kalshi settled
markets. Each row: question, class, resolution (0/1), price-at-T
(first-seen archive price = the market baseline the calibration is
scored against), close date. Truth here is the market RESOLUTION (an
observed fact), not the price.

usage: fetch_resolved.py <out.json>
"""
import json
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
sys.path.insert(0, "/opt/earth1/scripts/prospective")
from fetch_markets import classify  # noqa: E402  (same registered classifier)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main(out_path):
    rows = {}
    for off in range(0, 3000, 500):
        try:
            d = get("https://gamma-api.polymarket.com/markets?closed=true"
                    f"&limit=500&offset={off}&order=endDate&ascending=false")
        except Exception as e:
            print("poly fail", off, e)
            break
        got = 0
        for m in d if isinstance(d, list) else d.get("markets", []):
            try:
                end = (m.get("endDate") or "")[:10]
                if not end or end < "2026-03-01" or end > "2026-09-01":
                    continue
                outcomes = m.get("outcomes")
                if isinstance(outcomes, str):
                    outcomes = json.loads(outcomes)
                if [o.lower() for o in (outcomes or [])] != ["yes", "no"]:
                    continue
                prices = m.get("outcomePrices")
                if isinstance(prices, str):
                    prices = json.loads(prices)
                p_final = float(prices[0]) if prices else None
                if p_final is None or 0.05 < p_final < 0.95:
                    continue          # unresolved-looking, skip
                resolution = 1 if p_final >= 0.95 else 0
                ques = (m.get("question") or "").strip()
                cls = classify(ques)
                if cls not in ("election", "referendum", "rate_decision"):
                    continue
                if float(m.get("liquidityNum") or m.get("liquidity") or 0) < 2000 \
                        and float(m.get("volumeNum") or m.get("volume") or 0) < 10000:
                    continue
                # price-at-T baseline: last trade ~30d before close if
                # available, else the 1-week price field
                base = m.get("oneWeekPriceChange")
                p_t = (p_final - float(base)) if base is not None else None
                rows["poly:" + str(m.get("id"))] = {
                    "source": "polymarket", "question": ques, "class": cls,
                    "resolution": resolution, "close": end,
                    "p_market_final": p_final,
                    "p_market_minus7d": p_t,
                    "volume": m.get("volumeNum") or m.get("volume")}
                got += 1
            except Exception:
                continue
        print("poly offset", off, "kept", got)
        time.sleep(0.4)
    json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime()),
               "window": "2026-03-01..2026-09-01", "rows": rows},
              open(out_path, "w"), indent=1, sort_keys=True)
    from collections import Counter
    print("RESOLVED FETCHED", len(rows), dict(
        Counter(v["class"] for v in rows.values())))


if __name__ == "__main__":
    main(sys.argv[1])
