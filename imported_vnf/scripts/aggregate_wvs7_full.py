"""
aggregate_wvs7_full.py — re-aggregate the raw WVS Wave 7 microdata into
country-level measured anchors, well beyond the published GlobalOpinionQA
subset.

SOURCE      WVS_Cross-National_Wave_7_csv_v6_0.csv (v6.0, 2024; ~97k
            respondents, 66 countries; Inglehart et al.)
WEIGHT      W_WEIGHT (official per-country design weight)
COUNTRY     B_COUNTRY_ALPHA (ISO3) -> ISO2
MISSING     all negative codes (-1..-5) dropped from numerator and denominator
MIN CELL    n_valid >= 400 per country, else the country is omitted (no
            imputation); a variable needs >= 20 usable countries to ship

BINARIZATION is derived from the observed value range, never guessed:
    max 2    -> yes = (v == 1)         mentioned / first option
    max 3..5 -> yes = (v in (1, 2))    top-two of an ordered scale (1 = most)
    max 10   -> yes = (v in 6..10)     upper half of a 10-point scale

LABELS come from scripts/wvs7_labels.py, whose block offsets were verified by
correlating every raw column against the already-ingested published WVS items
(see that file's docstring). Unpinned or polarity-ambiguous blocks are skipped.

Outputs /tmp/w7/wvs7_micro_rows.json — one row per variable:
    {code, question_text, rule, targets: {ISO2: share}, n_countries}
Load it into benchmark_calibrations as measured_only reference anchors with
source_instrument = 'wvs7_microdata'.

Run: python scripts/aggregate_wvs7_full.py /path/to/WVS7.csv
"""

import json
import os
import re
import sys

import duckdb

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/wvs7.csv"
OUT_DIR = "/tmp/w7"
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wvs7_labels import LABELS  # noqa: E402

ISO3_TO_ISO2 = {
    "AND": "AD", "ARG": "AR", "ARM": "AM", "AUS": "AU", "BGD": "BD", "BOL": "BO",
    "BRA": "BR", "CAN": "CA", "CHL": "CL", "CHN": "CN", "COL": "CO", "CYP": "CY",
    "CZE": "CZ", "DEU": "DE", "ECU": "EC", "EGY": "EG", "ETH": "ET", "GBR": "GB",
    "GRC": "GR", "GTM": "GT", "HKG": "HK", "IDN": "ID", "IND": "IN", "IRN": "IR",
    "IRQ": "IQ", "JOR": "JO", "JPN": "JP", "KAZ": "KZ", "KEN": "KE", "KGZ": "KG",
    "KOR": "KR", "LBN": "LB", "LBY": "LY", "MAC": "MO", "MAR": "MA", "MDV": "MV",
    "MEX": "MX", "MMR": "MM", "MNG": "MN", "MYS": "MY", "NGA": "NG", "NIC": "NI",
    "NLD": "NL", "NZL": "NZ", "PAK": "PK", "PER": "PE", "PHL": "PH", "PRI": "PR",
    "ROU": "RO", "RUS": "RU", "SGP": "SG", "SRB": "RS", "SVK": "SK", "THA": "TH",
    "TJK": "TJ", "TUN": "TN", "TUR": "TR", "TWN": "TW", "UKR": "UA", "URY": "UY",
    "USA": "US", "UZB": "UZ", "VEN": "VE", "VNM": "VN", "ZWE": "ZW",
}

MIN_CELL_N = 400
MIN_COUNTRIES = 20

con = duckdb.connect(os.path.join(OUT_DIR, "wvs.duckdb"))
tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
if "wvs" not in tables:
    con.execute(f"""
      CREATE TABLE wvs AS SELECT * FROM read_csv('{CSV_PATH}',
        header=true, strict_mode=false, ignore_errors=true,
        max_line_size=10000000, null_padding=true)
    """)
con.execute("CREATE OR REPLACE TABLE iso_map(iso3 TEXT, iso2 TEXT)")
con.executemany("INSERT INTO iso_map VALUES (?, ?)", list(ISO3_TO_ISO2.items()))

cols = {r[0] for r in con.execute("DESCRIBE wvs").fetchall()}
qcols = sorted((c for c in cols if re.fullmatch(r"Q\d+", c)), key=lambda c: int(c[1:]))


def rule_for(mx: int):
    if mx <= 2:
        return "binary_first_option", "CASE WHEN {c} = 1 THEN 1.0 ELSE 0.0 END"
    if mx <= 5:
        return f"top2of{mx}", "CASE WHEN {c} IN (1,2) THEN 1.0 ELSE 0.0 END"
    if mx == 10:
        return "6to10of10", "CASE WHEN {c} BETWEEN 6 AND 10 THEN 1.0 ELSE 0.0 END"
    return None, None


rows = []
skipped = []
for c in qcols:
    if c not in LABELS:
        continue
    mn, mx, n = con.execute(
        f"SELECT min({c}), max({c}), count(*) FROM wvs WHERE {c} IS NOT NULL AND {c} >= 0"
    ).fetchone()
    if not mx or n < 5000:
        skipped.append((c, f"sparse n={n}"))
        continue
    rule, tmpl = rule_for(int(mx))
    if not rule:
        skipped.append((c, f"unmapped scale max={mx}"))
        continue
    expr = tmpl.format(c=c)
    per_country = con.execute(f"""
      SELECT im.iso2, SUM(W_WEIGHT * {expr}) / SUM(W_WEIGHT) AS pct, count(*) AS n
      FROM wvs JOIN iso_map im ON im.iso3 = wvs.B_COUNTRY_ALPHA
      WHERE {c} IS NOT NULL AND {c} >= 0 AND W_WEIGHT IS NOT NULL AND W_WEIGHT > 0
      GROUP BY 1
    """).fetchall()
    targets = {r[0]: round(float(r[1]), 6) for r in per_country if r[2] >= MIN_CELL_N}
    if len(targets) < MIN_COUNTRIES:
        skipped.append((c, f"only {len(targets)} countries"))
        continue
    rows.append({
        "code": c,
        "question_text": LABELS[c],
        "rule": rule,
        "scale_max": int(mx),
        "targets": targets,
        "n_countries": len(targets),
    })

# ---------------------------------------------------------------- spot checks
by_code = {r["code"]: r for r in rows}


def share(code, iso):
    return by_code.get(code, {}).get("targets", {}).get(iso)


checks = [
    ("US trust (Q57) in 0.30-0.45", 0.30 <= (share("Q57", "US") or -1) <= 0.45),
    ("God important (Q164): NG > US > DE > JP",
     (share("Q164", "NG") or -1) > (share("Q164", "US") or -1)
     > (share("Q164", "DE") or -1) > (share("Q164", "JP") or -1)),
    ("Homosexuality justifiable (Q182): NL > US > ID",
     (share("Q182", "NL") or -1) > (share("Q182", "US") or -1) > (share("Q182", "ID") or 9)),

    ("Confidence police (Q69) DE > NG", (share("Q69", "DE") or -1) > (share("Q69", "NG") or 9)),
]

print(f"variables shipped : {len(rows)}")
print(f"variables skipped : {len(skipped)}")
print(f"median countries  : {sorted(r['n_countries'] for r in rows)[len(rows) // 2]}")
print("\nSPOT CHECKS")
ok = True
for name, passed in checks:
    print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    ok = ok and passed
if not ok:
    print("\nspot check failed — not writing output")
    sys.exit(2)

out = os.path.join(OUT_DIR, "wvs7_micro_rows.json")
json.dump(rows, open(out, "w"))
print(f"\nwrote {out}")
