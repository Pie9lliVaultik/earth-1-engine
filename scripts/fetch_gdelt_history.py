#!/usr/bin/env python3
"""Fetch GDELT historical tone/volume timelines for the WVS countries.

One timelinetone + one timelinevol call per country over 2017-2022 (the
DOC 2.0 API's historical floor is Jan 2017), aggregated to monthly means
and cached to data/gdelt_history.json. Paced to respect GDELT's 1-req/5s
limit; resolves the API host via 1.1.1.1 because some residential DNS
resolvers SERVFAIL on it.

Usage: python3 scripts/fetch_gdelt_history.py
"""
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gdelt_history.json"

START = "20170101000000"
END = "20221231235959"
PACE_SECONDS = 8
MAX_RETRIES = 4

# ISO2 -> GDELT sourcecountry name, for the WVS paired-country set
GDELT_NAMES = {
    "US": "unitedstates", "DE": "germany", "AU": "australia",
    "JP": "japan", "KR": "southkorea", "BR": "brazil", "MX": "mexico",
    "AR": "argentina", "CL": "chile", "CO": "colombia", "PE": "peru",
    "IN": "india", "PK": "pakistan", "NG": "nigeria", "GH": "ghana",
    "ZW": "zimbabwe", "EG": "egypt", "JO": "jordan", "IQ": "iraq",
    "LB": "lebanon", "TN": "tunisia", "MA": "morocco", "TR": "turkey",
    "RU": "russia", "UA": "ukraine", "RO": "romania", "KZ": "kazakhstan",
    "KG": "kyrgyzstan", "PH": "philippines", "TH": "thailand",
    "MY": "malaysia", "SG": "singapore", "NZ": "newzealand",
    "NL": "netherlands", "CY": "cyprus", "EC": "ecuador",
}


def _resolve_ip() -> str:
    out = subprocess.run(
        ["dig", "+short", "@1.1.1.1", "api.gdeltproject.org"],
        capture_output=True, text=True).stdout.strip().splitlines()
    if not out:
        sys.exit("cannot resolve api.gdeltproject.org via 1.1.1.1")
    return out[0]


def _fetch(ip: str, name: str, mode: str) -> dict:
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?"
           f"query=sourcecountry:{name}&mode={mode}"
           f"&STARTDATETIME={START}&ENDDATETIME={END}"
           f"&format=json&TIMELINESMOOTH=0")
    for attempt in range(MAX_RETRIES):
        r = subprocess.run(
            ["curl", "-s", "--max-time", "60",
             "--resolve", f"api.gdeltproject.org:443:{ip}",
             "-A", "Earth1-Engine/1.0 research", url],
            capture_output=True, text=True)
        body = r.stdout
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            wait = 30 * (attempt + 1)
            print(f"    non-JSON ({body[:60]!r}...), retry in {wait}s")
            time.sleep(wait)
    return {}


def _monthly(data: dict) -> dict:
    """Aggregate a GDELT timeline to monthly means."""
    sums, counts = defaultdict(float), defaultdict(int)
    for tl in data.get("timeline", []):
        for pt in tl.get("data", []):
            # date like "20170101T120000Z"
            month = pt["date"][:6]
            sums[f"{month[:4]}-{month[4:6]}"] += float(pt["value"])
            counts[f"{month[:4]}-{month[4:6]}"] += 1
    return {m: round(sums[m] / counts[m], 4) for m in sorted(sums)}


def main():
    ip = _resolve_ip()
    print(f"api.gdeltproject.org -> {ip}")
    history = json.loads(OUT.read_text()) if OUT.exists() else {}

    for i, (iso2, name) in enumerate(sorted(GDELT_NAMES.items())):
        if iso2 in history and history[iso2].get("tone") and history[iso2].get("vol"):
            print(f"[{i+1}/{len(GDELT_NAMES)}] {iso2} cached, skip")
            continue
        print(f"[{i+1}/{len(GDELT_NAMES)}] {iso2} ({name})...")
        tone = _monthly(_fetch(ip, name, "timelinetone"))
        time.sleep(PACE_SECONDS)
        vol = _monthly(_fetch(ip, name, "timelinevol"))
        time.sleep(PACE_SECONDS)
        if tone and vol:
            history[iso2] = {"tone": tone, "vol": vol}
            OUT.write_text(json.dumps(history, indent=1))
            print(f"    {len(tone)} tone months, {len(vol)} vol months — saved")
        else:
            print(f"    FAILED (tone={len(tone)}, vol={len(vol)})")

    print(f"\nDone: {len(history)}/{len(GDELT_NAMES)} countries "
          f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
