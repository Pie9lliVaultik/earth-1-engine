"""Fetch living-baseline anchors from official open APIs.

Founder ruling 2026-08-27: benchmark against REAL data, never against
constants typed from memory. Every anchor here is fetched from the
World Bank open indicator API, stored raw with its source URL, series
id, vintage and fetch date, and hashed into the data-role registry.
No value in this file is authored by hand.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.worldbank.org/v2/country/WLD/indicator/{}?format=json&per_page=5&date=2019:2024"
INDICATORS = {
    "poverty_300_2021ppp": "SI.POV.DDAY",
    "poverty_420_2021ppp": "SI.POV.LMIC",
    "poverty_830_2021ppp": "SI.POV.UMIC",
    "crude_death_rate_per_1000": "SP.DYN.CDRT.IN",
    "crude_birth_rate_per_1000": "SP.DYN.CBRT.IN",
    "life_expectancy_years": "SP.DYN.LE00.IN",
    "unemployment_pct_lf": "SL.UEM.TOTL.ZS",
    "pop_share_0_14_pct": "SP.POP.0014.TO.ZS",
    "pop_share_65plus_pct": "SP.POP.65UP.TO.ZS",
}


def main():
    out = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "source": "World Bank open indicator API (api.worldbank.org/v2)",
           "aggregate": "WLD (World)", "anchors": {}}
    for name, ind in INDICATORS.items():
        url = API.format(ind)
        raw = subprocess.run(["curl", "-s", "--max-time", "30", url],
                             capture_output=True, text=True).stdout
        d = json.loads(raw)
        obs = [r for r in (d[1] or []) if r.get("value") is not None]
        if not obs:
            print("NO DATA", name, ind); continue
        latest = max(obs, key=lambda r: int(r["date"]))
        out["anchors"][name] = {
            "value": float(latest["value"]), "year": int(latest["date"]),
            "series_id": ind, "series_name": latest["indicator"]["value"],
            "url": url,
            "history": {r["date"]: float(r["value"]) for r in obs},
        }
        print(f"{name:32s} {latest['value']:>10.3f}  ({latest['date']})")
    # BLOCKED: age-specific death distribution needs UN WPP / WHO life
    # tables; WHO GHO API was unreachable 2026-08-27. Never invented.
    out["blocked_on_data"] = {
        "adult_death_share_by_age_band":
            "requires UN WPP or WHO life tables; WHO GHO API unreachable "
            "2026-08-27. Mortality AGE STRUCTURE is unscored until "
            "fetched — a correct crude rate can hide a wrong age curve.",
        "global_median_daily_consumption":
            "requires World Bank PIP percentile API; not yet fetched.",
    }
    p = os.path.join(ROOT, "data", "anchors_worldbank.json")
    json.dump(out, open(p, "w"), indent=1, sort_keys=True)
    print("\nWROTE", p, "sha256",
          hashlib.sha256(open(p, "rb").read()).hexdigest()[:16])


if __name__ == "__main__":
    main()
