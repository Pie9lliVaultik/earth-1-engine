"""B2-c2a: geopolitical alignment from UNGA ideal points (founder order
2026-09-01 item 2). Source: Bailey-Strezhnev-Voeten ideal point
estimates, Harvard Dataverse doi:10.7910/DVN/LEJUQZ, file
IdealpointsJuly2025.tab (fetched on prime, sha256 94417a94...).

Three national inputs, latest available year per country:
  geopol_ideal  ideal point (idealpointall), min-max normalized to [0,1]
  geopol_us     |ideal - ideal_US|  normalized by the observed max
  geopol_cn     |ideal - ideal_CN|  normalized by the observed max
Provenance: external:unga-idealpoints (no shared respondents/instrument
with any judged estate). Absent countries stay absent.

usage: build_geopol_unga.py <path-to-IdealpointsJuly2025.tab>
writes data/national_inputs/geopol_unga.json
"""
import csv
import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def main(path):
    from earth1.benchmark_questions import ISO3_TO_ISO2
    from earth1.genesis import GENESIS_COUNTRIES, GENESIS_COUNTRY_CODES
    sys.path.insert(0, os.path.join(ROOT, "scripts", "national_inputs"))
    from build_religiosity_factbook import ALIASES, norm
    genesis = set(GENESIS_COUNTRY_CODES)
    name2iso = {norm(c["name"]): c["iso2"] for c in GENESIS_COUNTRIES}
    for k, v in ALIASES.items():
        name2iso.setdefault(norm(k), v)
    latest = {}
    with open(path) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            iso2 = (ISO3_TO_ISO2.get(row["iso3c"])
                    or name2iso.get(norm(row.get("countryname", ""))))
            if iso2 not in genesis:
                continue
            try:
                yr = int(float(row["year"]))
                ip = float(row["idealpointall"])
            except (ValueError, KeyError):
                continue
            if iso2 not in latest or yr > latest[iso2][0]:
                latest[iso2] = (yr, ip)
    if "US" not in latest or "CN" not in latest:
        raise SystemExit("US/CN anchor missing from source")
    us, cn = latest["US"][1], latest["CN"][1]
    ips = [v[1] for v in latest.values()]
    lo, hi = min(ips), max(ips)
    dmax_us = max(abs(v[1] - us) for v in latest.values())
    dmax_cn = max(abs(v[1] - cn) for v in latest.values())
    vars_out = {"geopol_ideal": {}, "geopol_us": {}, "geopol_cn": {}}
    for iso2, (yr, ip) in latest.items():
        note = f"idealpointall={ip:.3f} year={yr}"
        vars_out["geopol_ideal"][iso2] = {
            "marginal": round((ip - lo) / (hi - lo), 4), "cells": {},
            "source_note": note}
        vars_out["geopol_us"][iso2] = {
            "marginal": round(abs(ip - us) / dmax_us, 4), "cells": {},
            "source_note": note}
        vars_out["geopol_cn"][iso2] = {
            "marginal": round(abs(ip - cn) / dmax_cn, 4), "cells": {},
            "source_note": note}
    payload = {
        "source": "UNGA ideal points (Bailey-Strezhnev-Voeten), Harvard "
                  "Dataverse doi:10.7910/DVN/LEJUQZ, IdealpointsJuly2025.tab",
        "provenance": "external:unga-idealpoints",
        "raw_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "retrieved": time.strftime("%Y-%m-%d"),
        "normalization": {"ideal_minmax": [lo, hi], "us_anchor": us,
                          "cn_anchor": cn, "dmax_us": dmax_us,
                          "dmax_cn": dmax_cn},
        "n_countries": len(latest),
        "vars": vars_out,
    }
    p = os.path.join(ROOT, "data", "national_inputs", "geopol_unga.json")
    blob = json.dumps(payload, indent=1, sort_keys=True).encode()
    open(p, "wb").write(blob)
    print("BUILT", p, "| countries:", len(latest),
          "| sha256:", hashlib.sha256(blob).hexdigest()[:16])
    for c in ("US", "CN", "RU", "IL", "IR", "DE", "IN", "BR"):
        if c in latest:
            v = vars_out["geopol_us"][c]["marginal"]
            print(f"  {c}: ideal={latest[c][1]:+.2f} dist_us={v}")


if __name__ == "__main__":
    main(sys.argv[1])
