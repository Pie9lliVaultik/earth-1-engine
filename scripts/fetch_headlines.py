#!/usr/bin/env python3
"""Fetch real historical headlines for the temporal replay (G5 run #8).

GDELT DOC artlist per country per quarter, 2017-2022: the top articles
of each window become NewsItems for perception. Paced for the rate
limit, checkpointed per window, resumable. 1.1.1.1 DNS workaround.
"""
import json, subprocess, sys, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "headlines_2017_2022.json"
PACE = int(os.environ.get("GDELT_PACE", "22"))
PER_WINDOW = 3

COUNTRIES = {
    "US": "unitedstates", "DE": "germany", "AU": "australia",
    "JP": "japan", "KR": "southkorea", "BR": "brazil", "MX": "mexico",
    "AR": "argentina", "CL": "chile", "CO": "colombia", "IN": "india",
    "PK": "pakistan", "NG": "nigeria", "TR": "turkey", "RO": "romania",
    "PH": "philippines", "TH": "thailand", "MY": "malaysia",
    "NL": "netherlands", "EC": "ecuador",
}
QUARTERS = [(y, q) for y in range(2017, 2023) for q in (1, 2, 3, 4)]


def _resolve_ip():
    out = subprocess.run(["dig", "+short", "@1.1.1.1", "api.gdeltproject.org"],
                         capture_output=True, text=True).stdout.strip().splitlines()
    if not out:
        sys.exit("DNS fail")
    return out[0]


def _fetch(ip, name, y, q, retries=4):
    m0 = (q - 1) * 3 + 1
    m1 = m0 + 2
    start = f"{y}{m0:02d}01000000"
    end = f"{y}{m1:02d}28235959"
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?"
           f"query=sourcecountry:{name}&mode=artlist&maxrecords=25"
           f"&sort=hybridrel&STARTDATETIME={start}&ENDDATETIME={end}"
           f"&format=json")
    for attempt in range(retries):
        r = subprocess.run(["curl", "-s", "--max-time", "180",
                            "--resolve", f"api.gdeltproject.org:443:{ip}",
                            "-A", "Earth1-Engine/1.0 research", url],
                           capture_output=True, text=True)
        try:
            arts = json.loads(r.stdout).get("articles", [])
            seen, out = set(), []
            for a in arts:
                t = (a.get("title") or "").strip()
                if len(t) > 25 and t[:40] not in seen:
                    seen.add(t[:40])
                    out.append({"title": t, "date": a.get("seendate", "")[:8]})
                if len(out) >= PER_WINDOW:
                    break
            return out
        except json.JSONDecodeError:
            time.sleep(30 * (attempt + 1))
    return None


def main():
    ip = _resolve_ip()
    print(f"api -> {ip}")
    store = json.loads(OUT.read_text()) if OUT.exists() else {}
    total = len(COUNTRIES) * len(QUARTERS)
    done = sum(1 for k in store if store[k] is not None)
    print(f"resuming: {done}/{total} windows cached")
    for cc, name in sorted(COUNTRIES.items()):
        for (y, q) in QUARTERS:
            key = f"{cc}|{y}Q{q}"
            if store.get(key):
                continue
            arts = _fetch(ip, name, y, q)
            time.sleep(PACE)
            if arts:
                store[key] = arts
                OUT.write_text(json.dumps(store, indent=1))
        n = sum(1 for k in store if k.startswith(cc) and store[k])
        print(f"{cc}: {n}/{len(QUARTERS)} quarters")
    print("Done.")


if __name__ == "__main__":
    main()
