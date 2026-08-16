#!/usr/bin/env python3
"""Phase 5.7 step 1: fetch GDELT theme-salience timelines.

For each WVS question with a plausible GKG theme, fetch the monthly
share of a country's coverage matching that theme (timelinevol with a
theme: filter), 2017-2022. This feeds the ENGINE-FREE correlation check
that gates whether a theme replay gets built at all (5.6 lesson: tone
was checked only after the build — never again).

Each candidate theme is probed once (Brazil) before the full sweep;
invalid/empty themes are dropped. Paced for GDELT's 1-req/5s limit.
"""
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gdelt_themes.json"

import os

START = "20170101000000"
END = "20221231235959"
PACE = int(os.environ.get("GDELT_PACE", "25"))
TIMEOUT = "180"

# question_id -> candidate GKG theme codes (first valid one wins)
QUESTION_THEMES = {
    "t_homosexuality": ["LGBT"],
    "t_religion": ["RELIGION"],
    "t_democracy": ["DEMOCRACY"],
    "t_army_rule": ["MILITARY"],
    "t_men_leaders": ["WOMENS_RIGHTS", "GENDER_EQUALITY", "DISCRIMINATION_WOMEN"],
    "t_environment": ["ENV_CLIMATECHANGE", "ENV_GREEN"],
    "t_trust": ["CORRUPTION"],
    "t_abortion": ["ABORTION"],
    "t_death_penalty": ["DEATH_PENALTY", "TAX_DEATHPENALTY"],
    "t_life_sat": ["ECON_INFLATION", "UNEMPLOYMENT"],
}

# countries we score (fetched tone history ∩ WVS) — reuse tone coverage
GDELT_NAMES = {
    "US": "unitedstates", "DE": "germany", "AU": "australia",
    "JP": "japan", "KR": "southkorea", "BR": "brazil", "MX": "mexico",
    "AR": "argentina", "CL": "chile", "CO": "colombia", "IN": "india",
    "PK": "pakistan", "NG": "nigeria", "TR": "turkey", "RO": "romania",
    "PH": "philippines", "TH": "thailand", "MY": "malaysia",
    "NL": "netherlands", "EC": "ecuador",
}


def _resolve_ip() -> str:
    out = subprocess.run(
        ["dig", "+short", "@1.1.1.1", "api.gdeltproject.org"],
        capture_output=True, text=True).stdout.strip().splitlines()
    if not out:
        sys.exit("cannot resolve api.gdeltproject.org")
    return out[0]


def _fetch(ip: str, query: str, retries: int = 4) -> dict:
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?"
           f"query={query}&mode=timelinevol"
           f"&STARTDATETIME={START}&ENDDATETIME={END}"
           f"&format=json&TIMELINESMOOTH=0")
    for attempt in range(retries):
        r = subprocess.run(
            ["curl", "-s", "--max-time", TIMEOUT,
             "--resolve", f"api.gdeltproject.org:443:{ip}",
             "-A", "Earth1-Engine/1.0 research", url],
            capture_output=True, text=True)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(30 * (attempt + 1))
    return {}


def _monthly(data: dict) -> dict:
    sums, counts = defaultdict(float), defaultdict(int)
    for tl in data.get("timeline", []):
        for pt in tl.get("data", []):
            m = f"{pt['date'][:4]}-{pt['date'][4:6]}"
            sums[m] += float(pt["value"])
            counts[m] += 1
    return {m: round(sums[m] / counts[m], 5) for m in sorted(sums)}


def main():
    ip = _resolve_ip()
    print(f"api -> {ip}")
    store = json.loads(OUT.read_text()) if OUT.exists() else {}

    # 1. probe candidate themes on Brazil, keep the first valid per question
    valid: dict = store.get("_theme_map", {})
    for qid, candidates in QUESTION_THEMES.items():
        if qid in valid:
            continue
        for theme in candidates:
            probe = _monthly(_fetch(ip, f"theme:{theme}%20sourcecountry:brazil"))
            time.sleep(PACE)
            if len(probe) >= 60:
                valid[qid] = theme
                print(f"probe {qid}: theme {theme} VALID ({len(probe)} months)")
                break
            print(f"probe {qid}: theme {theme} empty, next candidate")
        store["_theme_map"] = valid
        OUT.write_text(json.dumps(store, indent=1))

    # 2. full sweep: valid themes x countries
    for qid, theme in valid.items():
        block = store.setdefault(qid, {})
        for iso2, name in sorted(GDELT_NAMES.items()):
            if iso2 in block:
                continue
            series = _monthly(_fetch(
                ip, f"theme:{theme}%20sourcecountry:{name}"))
            time.sleep(PACE)
            if series:
                block[iso2] = series
                OUT.write_text(json.dumps(store, indent=1))
        print(f"{qid} ({theme}): {len(block)}/{len(GDELT_NAMES)} countries")

    print("Done.")


if __name__ == "__main__":
    main()
