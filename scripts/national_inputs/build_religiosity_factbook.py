"""B2-c1a: national religiosity from CIA World Factbook religion shares.

Founder order 2026-09-01: religiosity = 1 - (unaffiliated+none+atheist
share). Countries whose Factbook entry lists no explicit nonreligious
percentage: if the listed religious shares sum to >=90% the nonreligious
share is taken as the explicit 0 the entry implies; below that the
country stays ABSENT (no invented numbers). Every country carries its
verbatim Factbook text as the source note; entries citing Pew Research
are flagged PEW_DERIVED (excluded from Pew-estate religion-family
scoring per order 1b).

usage: build_religiosity_factbook.py <path-to-factbook.json-clone>
writes data/national_inputs/religiosity_factbook.json
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

NONRELIG = re.compile(
    r"\b(none|unaffiliated|atheist[s]?|agnostic[s]?|no religion|"
    r"non-?religious|irreligious|not religious|secular)\b[^,;(]*?"
    r"(\d+(?:\.\d+)?)\s*%", re.I)
ANYPCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
ALIASES = {
    "united states": "US", "korea, south": "KR", "south korea": "KR",
    "korea, north": "KP", "north korea": "KP", "burma": "MM",
    "myanmar": "MM", "czechia": "CZ", "czech republic": "CZ",
    "turkey (turkiye)": "TR", "turkiye": "TR", "turkey": "TR",
    "cote d'ivoire": "CI", "ivory coast": "CI", "cabo verde": "CV",
    "cape verde": "CV", "laos": "LA", "vietnam": "VN", "russia": "RU",
    "iran": "IR", "syria": "SY", "venezuela": "VE", "bolivia": "BO",
    "tanzania": "TZ", "congo, democratic republic of the": "CD",
    "democratic republic of the congo": "CD",
    "congo, republic of the": "CG", "republic of the congo": "CG",
    "moldova": "MD", "kyrgyzstan": "KG", "eswatini": "SZ",
    "swaziland": "SZ", "timor-leste": "TL", "east timor": "TL",
    "north macedonia": "MK", "macedonia": "MK", "brunei": "BN",
    "gambia, the": "GM", "gambia": "GM", "bahamas, the": "BS",
    "bahamas": "BS", "micronesia, federated states of": "FM",
    "micronesia": "FM", "united kingdom": "GB", "taiwan": "TW",
    "hong kong": "HK", "macau": "MO", "palestine": "PS",
    "west bank": "PS", "kosovo": "XK", "vatican city": "VA",
    "holy see (vatican city)": "VA", "saint kitts and nevis": "KN",
    "saint lucia": "LC", "saint vincent and the grenadines": "VC",
    "sao tome and principe": "ST", "solomon islands": "SB",
    "marshall islands": "MH", "central african republic": "CF",
    "united arab emirates": "AE", "south sudan": "SS",
    "drc": "CD", "congo (kinshasa)": "CD", "congo (brazzaville)": "CG",
    "dominican": "DO", "dominican republic": "DO",
}


def norm(s):
    import html
    import unicodedata
    s = html.unescape(s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^a-z, ()]", "", s.lower()).strip()
    return s[4:] if s.startswith("the ") else s


def main(fb):
    from earth1.genesis import GENESIS_COUNTRIES
    name2iso = {norm(c["name"]): c["iso2"] for c in GENESIS_COUNTRIES}
    for k, v in ALIASES.items():
        name2iso.setdefault(norm(k), v)
    fbsha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=fb,
                           capture_output=True, text=True).stdout.strip()
    out, misses = {}, []
    for region in sorted(os.listdir(fb)):
        rdir = os.path.join(fb, region)
        if not os.path.isdir(rdir) or region in (".git", "meta"):
            continue
        for f in sorted(os.listdir(rdir)):
            if not f.endswith(".json"):
                continue
            try:
                d = json.load(open(os.path.join(rdir, f)))
            except Exception:
                continue
            gov = d.get("Government", {}).get("Country name", {})
            short = gov.get("conventional short form", {}).get("text") or ""
            longf = gov.get("conventional long form", {}).get("text") or ""
            if short.strip().lower() in ("", "none"):
                short = longf
            iso = name2iso.get(norm(short)) or name2iso.get(norm(longf))
            if iso is None:
                continue
            rel = d.get("People and Society", {}).get("Religions", {})
            text = rel.get("text", "") if isinstance(rel, dict) else ""
            note = " ".join(v.get("text", "") for k, v in rel.items()
                            if isinstance(v, dict) and k != "text") \
                if isinstance(rel, dict) else ""
            full = (text + " " + note).strip()
            if not full or not ANYPCT.search(text):
                misses.append((iso, short, "no percentages"))
                continue
            nonrel = sum(float(m.group(2)) for m in NONRELIG.finditer(text))
            allpct = sum(float(x) for x in ANYPCT.findall(text))
            if nonrel == 0.0 and allpct < 90.0:
                misses.append((iso, short, f"no nonreligious category, "
                                        f"listed shares sum {allpct:.0f}%"))
                continue
            relig = max(0.0, min(1.0, 1.0 - min(nonrel, 100.0) / 100.0))
            out[iso] = {"marginal": round(relig, 4), "cells": {},
                        "nonreligious_pct": round(nonrel, 2),
                        "pew_derived": bool(re.search(r"pew", full, re.I)),
                        "source_note": full[:600]}
    payload = {
        "source": "CIA World Factbook via github.com/factbook/factbook.json"
                  f" (public domain), clone commit {fbsha}",
        "retrieved": time.strftime("%Y-%m-%d"),
        "rule": "religiosity = 1 - explicit nonreligious share; implicit 0 "
                "only when listed shares sum >=90%; else ABSENT",
        "n_countries": len(out),
        "absent": [{"iso2": i, "name": n, "why": w} for i, n, w in misses],
        "countries": out,
    }
    p = os.path.join(ROOT, "data", "national_inputs",
                     "religiosity_factbook.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    blob = json.dumps(payload, indent=1, sort_keys=True).encode()
    open(p, "wb").write(blob)
    print("BUILT", p)
    print("countries:", len(out), "| absent:", len(misses),
          "| pew_derived:", sum(1 for v in out.values() if v["pew_derived"]),
          "| sha256:", hashlib.sha256(blob).hexdigest()[:16])
    vals = sorted((v["marginal"], k) for k, v in out.items())
    print("least religious:", vals[:5])
    print("most religious:", vals[-5:])


if __name__ == "__main__":
    main(sys.argv[1])
