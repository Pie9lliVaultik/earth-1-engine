#!/usr/bin/env python3
"""Fetch World Bank WDI development trajectories — the tide data.

Three slow variables that drive secular value drift (Inglehart):
  GDP per capita PPP, tertiary education enrollment, urban share.
1990-2024, all countries, cached once in data/wdi_tide.json.
Free API, no key, no rate-limit drama.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "wdi_tide.json"

INDICATORS = {
    "gdp_pcap_ppp": "NY.GDP.PCAP.PP.KD",
    "tertiary_enroll": "SE.TER.ENRR",
    "urban_share": "SP.URB.TOTL.IN.ZS",
}


def fetch_indicator(code: str) -> dict:
    """All countries, 1990-2024, paged."""
    series: dict = {}
    page, pages = 1, 1
    while page <= pages:
        url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
               f"?date=1990:2024&format=json&per_page=2000&page={page}")
        r = subprocess.run(["curl", "-s", "--max-time", "60", url],
                           capture_output=True, text=True)
        try:
            meta, rows = json.loads(r.stdout)
        except (json.JSONDecodeError, ValueError):
            time.sleep(5)
            continue
        pages = meta.get("pages", 1)
        for row in rows or []:
            iso2 = (row.get("country") or {}).get("id", "")
            year = row.get("date", "")
            val = row.get("value")
            if len(iso2) == 2 and val is not None:
                series.setdefault(iso2, {})[year] = round(float(val), 3)
        page += 1
        time.sleep(1)
    return series


def main():
    out = {}
    for name, code in INDICATORS.items():
        print(f"fetching {name} ({code})...")
        out[name] = fetch_indicator(code)
        n_countries = len(out[name])
        n_points = sum(len(v) for v in out[name].values())
        print(f"  {n_countries} countries, {n_points} datapoints")
    OUT.write_text(json.dumps(out, indent=1))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
