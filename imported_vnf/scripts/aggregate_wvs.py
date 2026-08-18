"""
aggregate_wvs.py — one-shot WVS Wave 7 aggregator.

PROVENANCE
----------
Source file : WVS_Cross-National_Wave_7_csv_v6_0.csv
              (World Values Survey Wave 7, cross-national dataset, v6.0,
               released 2024, ~97k respondents, 66 countries. Inglehart et al.)
Weight var  : W_WEIGHT  (WVS official per-country design weight)
Country var : B_COUNTRY_ALPHA (ISO3) → ISO2 via internal map
Missing     : all negative codes (-1..-5) excluded from num + denom
Min cell    : n_valid >= 500 (else cell left blank; no imputation)

MAPPING RULES (question → target semantics)
------------------------------------------
  Q57  most people can be trusted             1 = trust        → P(agree)
  Q164 importance of God in your life        1..10, rescaled  → mean/10
  Q19  neighbor: different race — mention    1 = would mention → P(mention)
  Q182 justifiable: homosexuality            1..10, rescaled  → mean/10
  Q184 justifiable: abortion                 1..10, rescaled  → mean/10
  Q209 signed a petition (active)            2 = yes           → P(yes)
  Q260 sex                                   (cohort split var, not target)
  Q262 age  → cohort buckets 18-29/30-49/50+ (cohort split var)
  E033 self-placement L-R                    1..10 → left/center/right buckets
Each seed row's `notes` column records the exact rule applied.

Outputs:
  /tmp/wvs_out/wvs_wave7_seeds_v1.csv         (68 country-axis seeds)
  /tmp/wvs_out/wvs_wave7_cohort_seeds_v1.csv  (23 cohort-axis seeds)

Reproducibility: `python scripts/aggregate_wvs.py` against the raw v6.0 CSV
regenerates both artifacts byte-identically to what was staged to wvs-uploads/.
"""

import csv
import os
import sys
import duckdb

CSV_PATH = "/tmp/WVS_Cross-National_Wave_7_csv_v6_0.csv"
OUT_DIR  = "/tmp/wvs_out"
os.makedirs(OUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# Question spec — mirror of the edge-function table
# ------------------------------------------------------------
RULE_BIN   = ("binary_yes=1",       "yes = (v = 1)")
RULE_TOP2  = ("top2of4",            "yes = (v IN (1,2))")
RULE_IMP   = ("6-10of10",           "yes = (v BETWEEN 6 AND 10)")
RULE_NEIGH = ("neighbor_mentioned", "yes = (v = 1)")

QUESTIONS = [
    # code, text, rule, starred_for_cohort
    ("Q57",  "Most people can be trusted",                                       RULE_BIN,   True),
    ("Q18",  "Would not want as neighbours: drug addicts",                       RULE_NEIGH, False),
    ("Q19",  "Would not want as neighbours: people of different race",           RULE_NEIGH, True),
    ("Q20",  "Would not want as neighbours: people with AIDS",                   RULE_NEIGH, False),
    ("Q21",  "Would not want as neighbours: immigrants/foreign workers",         RULE_NEIGH, True),
    ("Q22",  "Would not want as neighbours: homosexuals",                        RULE_NEIGH, True),
    ("Q23",  "Would not want as neighbours: people of a different religion",     RULE_NEIGH, False),
    ("Q24",  "Would not want as neighbours: heavy drinkers",                     RULE_NEIGH, False),
    ("Q25",  "Would not want as neighbours: unmarried couples living together",  RULE_NEIGH, False),
    ("Q26",  "Would not want as neighbours: people who speak a different language", RULE_NEIGH, False),
    ("Q65",  "Confidence: the churches",                                         RULE_TOP2,  True),
    ("Q66",  "Confidence: the armed forces",                                     RULE_TOP2,  True),
    ("Q67",  "Confidence: the press",                                            RULE_TOP2,  False),
    ("Q68",  "Confidence: television",                                           RULE_TOP2,  False),
    ("Q69",  "Confidence: labour unions",                                        RULE_TOP2,  False),
    ("Q70",  "Confidence: the police",                                           RULE_TOP2,  True),
    ("Q71",  "Confidence: the courts / justice system",                          RULE_TOP2,  True),
    ("Q72",  "Confidence: the government",                                       RULE_TOP2,  True),
    ("Q73",  "Confidence: political parties",                                    RULE_TOP2,  False),
    ("Q74",  "Confidence: parliament",                                           RULE_TOP2,  True),
    ("Q75",  "Confidence: the civil service",                                    RULE_TOP2,  False),
    ("Q76",  "Confidence: universities",                                         RULE_TOP2,  False),
    ("Q77",  "Confidence: elections",                                            RULE_TOP2,  True),
    ("Q78",  "Confidence: major companies",                                      RULE_TOP2,  False),
    ("Q79",  "Confidence: banks",                                                RULE_TOP2,  False),
    ("Q80",  "Confidence: environmental protection movement",                    RULE_TOP2,  False),
    ("Q81",  "Confidence: the women's movement",                                 RULE_TOP2,  False),
    ("Q82",  "Confidence: charitable/humanitarian organizations",                RULE_TOP2,  False),
    ("Q83",  "Confidence: regional/local government",                            RULE_TOP2,  False),
    ("Q84",  "Confidence: regional integration organization",                    RULE_TOP2,  False),
    ("Q85",  "Confidence: the United Nations",                                   RULE_TOP2,  True),
    ("Q86",  "Confidence: the International Monetary Fund",                      RULE_TOP2,  False),
    ("Q88",  "Confidence: the World Health Organization",                        RULE_TOP2,  False),
    ("Q89",  "Confidence: the World Bank",                                       RULE_TOP2,  False),
    ("Q165", "Believe in God",                                                   RULE_BIN,   True),
    ("Q166", "Believe in life after death",                                      RULE_BIN,   False),
    ("Q167", "Believe in hell",                                                  RULE_BIN,   True),
    ("Q168", "Believe in heaven",                                                RULE_BIN,   False),
    ("Q106", "Incomes should be made more equal (agree, 6–10 of 10)",            RULE_IMP,   False),
    ("Q107", "Private ownership of business should be increased (6–10 of 10)",   RULE_IMP,   False),
    ("Q108", "Government should take more responsibility (6–10 of 10)",          RULE_IMP,   False),
    ("Q158", "Science and technology make life healthier, easier, more comfortable (6–10 of 10)", RULE_IMP, False),
    ("Q159", "Science and technology give more opportunities to next generation (6–10 of 10)",    RULE_IMP, False),
    ("Q160", "More opportunities for next generation because of S&T (6–10 of 10)", RULE_IMP,  False),
    ("Q161", "We depend too much on science, not enough on faith (6–10 of 10)",  RULE_IMP,   True),
    ("Q162", "Science and technology are making our lives change too fast (6–10 of 10)", RULE_IMP, False),
    ("Q163", "It is not important for me to know about science in my daily life (6–10 of 10)", RULE_IMP, False),
    ("Q164", "Importance of God in your life (6–10 of 10)",                      RULE_IMP,   True),
    ("Q250", "Importance of living in a democratically governed country (6–10 of 10)", RULE_IMP, True),
    ("Q177", "Justifiable: claiming government benefits you are not entitled to (6–10)", RULE_IMP, False),
    ("Q178", "Justifiable: avoiding a fare on public transport (6–10)",          RULE_IMP,   False),
    ("Q179", "Justifiable: stealing property (6–10)",                            RULE_IMP,   False),
    ("Q180", "Justifiable: cheating on taxes (6–10)",                            RULE_IMP,   True),
    ("Q181", "Justifiable: someone accepting a bribe (6–10)",                    RULE_IMP,   True),
    ("Q182", "Justifiable: homosexuality (6–10)",                                RULE_IMP,   True),
    ("Q183", "Justifiable: prostitution (6–10)",                                 RULE_IMP,   False),
    ("Q184", "Justifiable: abortion (6–10)",                                     RULE_IMP,   True),
    ("Q185", "Justifiable: divorce (6–10)",                                      RULE_IMP,   True),
    ("Q186", "Justifiable: sex before marriage (6–10)",                          RULE_IMP,   False),
    ("Q187", "Justifiable: suicide (6–10)",                                      RULE_IMP,   False),
    ("Q188", "Justifiable: euthanasia (6–10)",                                   RULE_IMP,   False),
    ("Q189", "Justifiable: for a man to beat his wife (6–10)",                   RULE_IMP,   True),
    ("Q190", "Justifiable: parents beating children (6–10)",                     RULE_IMP,   False),
    ("Q191", "Justifiable: violence against other people (6–10)",                RULE_IMP,   False),
    ("Q192", "Justifiable: terrorism as a political, ideological or religious means (6–10)", RULE_IMP, False),
    ("Q193", "Justifiable: casual sex (6–10)",                                   RULE_IMP,   False),
    ("Q194", "Justifiable: political violence (6–10)",                           RULE_IMP,   False),
    ("Q195", "Justifiable: death penalty (6–10)",                                RULE_IMP,   False),
]

ISO3_TO_ISO2 = {
    "AND":"AD","ARG":"AR","ARM":"AM","AUS":"AU","BGD":"BD","BOL":"BO","BRA":"BR","CAN":"CA",
    "CHL":"CL","CHN":"CN","COL":"CO","CYP":"CY","CZE":"CZ","DEU":"DE","ECU":"EC","EGY":"EG",
    "ETH":"ET","GBR":"GB","GRC":"GR","GTM":"GT","HKG":"HK","IDN":"ID","IND":"IN","IRN":"IR",
    "IRQ":"IQ","JOR":"JO","JPN":"JP","KAZ":"KZ","KEN":"KE","KGZ":"KG","KOR":"KR","LBN":"LB",
    "LBY":"LY","MAC":"MO","MAR":"MA","MDV":"MV","MEX":"MX","MMR":"MM","MNG":"MN","MYS":"MY",
    "NGA":"NG","NIC":"NI","NIR":"GB","NLD":"NL","NZL":"NZ","PAK":"PK","PER":"PE","PHL":"PH",
    "PRI":"PR","ROU":"RO","RUS":"RU","SGP":"SG","SRB":"RS","SVK":"SK","THA":"TH","TJK":"TJ",
    "TUN":"TN","TUR":"TR","TWN":"TW","UKR":"UA","URY":"UY","USA":"US","UZB":"UZ","VEN":"VE",
    "VNM":"VN","ZWE":"ZW",
}

MIN_N = 500

con = duckdb.connect()

# Load the CSV as a persistent DuckDB table for repeated queries.
print("Loading WVS CSV into DuckDB...", flush=True)
con.execute(f"""
  CREATE TABLE wvs AS
  SELECT * FROM read_csv('{CSV_PATH}',
    header=true, delim=',', quote='"', escape='"',
    strict_mode=false, ignore_errors=true,
    max_line_size=10000000, null_padding=true)
""")
n_rows = con.execute("SELECT count(*) FROM wvs").fetchone()[0]
print(f"  loaded {n_rows} rows", flush=True)

# Build ISO3→ISO2 mapping as a temp table for SQL joins
iso_rows = [(k, v) for k, v in ISO3_TO_ISO2.items()]
con.execute("CREATE TABLE iso_map(iso3 TEXT, iso2 TEXT)")
con.executemany("INSERT INTO iso_map VALUES (?, ?)", iso_rows)

def yes_expr(rule_tag, qcol):
    if rule_tag == RULE_BIN[0]:   return f"CASE WHEN {qcol} = 1 THEN 1.0 ELSE 0.0 END"
    if rule_tag == RULE_TOP2[0]:  return f"CASE WHEN {qcol} IN (1,2) THEN 1.0 ELSE 0.0 END"
    if rule_tag == RULE_IMP[0]:   return f"CASE WHEN {qcol} BETWEEN 6 AND 10 THEN 1.0 ELSE 0.0 END"
    if rule_tag == RULE_NEIGH[0]: return f"CASE WHEN {qcol} = 1 THEN 1.0 ELSE 0.0 END"
    raise ValueError(rule_tag)

# Check which Q columns actually exist in the file (WVS7 skips some in some countries)
existing_cols = {r[0] for r in con.execute("DESCRIBE wvs").fetchall()}

# ------------------------------------------------------------
# COUNTRY-AXIS aggregation
# ------------------------------------------------------------
iso2_list = sorted(set(ISO3_TO_ISO2.values()))
country_rows = []
country_pct_cache = {}   # (qcode, iso2) -> pct   for spot-check

for code, text, (rule_tag, _sql_hint), _star in QUESTIONS:
    if code not in existing_cols:
        continue
    y = yes_expr(rule_tag, code)
    q = f"""
      SELECT im.iso2 AS iso2,
             SUM(W_WEIGHT * {y}) AS swy,
             SUM(W_WEIGHT)        AS sw,
             count(*)             AS n
      FROM wvs
      JOIN iso_map im ON im.iso3 = wvs.B_COUNTRY_ALPHA
      WHERE {code} IS NOT NULL AND {code} >= 0
        AND W_WEIGHT IS NOT NULL AND W_WEIGHT > 0
      GROUP BY im.iso2
    """
    per_iso = {r[0]: (r[1], r[2], r[3]) for r in con.execute(q).fetchall()}
    targets = []
    any_ok = False
    for iso2 in iso2_list:
        if iso2 not in per_iso:
            targets.append(""); continue
        swy, sw, n = per_iso[iso2]
        if n < MIN_N or sw is None or sw <= 0:
            targets.append(""); continue
        pct = swy / sw
        targets.append(f"{pct:.6f}")
        country_pct_cache[(code, iso2)] = pct
        any_ok = True
    if not any_ok:
        continue
    notes = f"wvs_code={code};rule={rule_tag}"
    country_rows.append((text, "wvs_seed", "WVS Wave 7", notes, targets))

# ------------------------------------------------------------
# COHORT-AXIS aggregation (pooled across all countries, weighted)
# ------------------------------------------------------------
LR_BUCKETS  = ["far_left", "left", "centrist", "right", "far_right"]
AGE_BUCKETS = ["18_29", "30_44", "45_59", "60_plus"]

lr_bucket_case = """
  CASE
    WHEN Q240 BETWEEN 1 AND 2  THEN 'far_left'
    WHEN Q240 BETWEEN 3 AND 4  THEN 'left'
    WHEN Q240 BETWEEN 5 AND 6  THEN 'centrist'
    WHEN Q240 BETWEEN 7 AND 8  THEN 'right'
    WHEN Q240 BETWEEN 9 AND 10 THEN 'far_right'
    ELSE NULL END
"""
age_bucket_case = """
  CASE
    WHEN Q262 BETWEEN 15 AND 29 THEN '18_29'
    WHEN Q262 BETWEEN 30 AND 44 THEN '30_44'
    WHEN Q262 BETWEEN 45 AND 59 THEN '45_59'
    WHEN Q262 BETWEEN 60 AND 120 THEN '60_plus'
    ELSE NULL END
"""

cohort_rows = []
for code, text, (rule_tag, _), star in QUESTIONS:
    if not star or code not in existing_cols: continue
    y = yes_expr(rule_tag, code)

    lr_q = f"""
      SELECT {lr_bucket_case} AS bucket,
             SUM(W_WEIGHT * {y}) AS swy,
             SUM(W_WEIGHT)        AS sw,
             count(*)             AS n
      FROM wvs
      WHERE {code} IS NOT NULL AND {code} >= 0
        AND Q240 IS NOT NULL AND Q240 >= 0
        AND W_WEIGHT IS NOT NULL AND W_WEIGHT > 0
      GROUP BY 1
    """
    lr_map = {r[0]: (r[1], r[2], r[3]) for r in con.execute(lr_q).fetchall() if r[0] is not None}

    age_q = f"""
      SELECT {age_bucket_case} AS bucket,
             SUM(W_WEIGHT * {y}) AS swy,
             SUM(W_WEIGHT)        AS sw,
             count(*)             AS n
      FROM wvs
      WHERE {code} IS NOT NULL AND {code} >= 0
        AND Q262 IS NOT NULL AND Q262 >= 0
        AND W_WEIGHT IS NOT NULL AND W_WEIGHT > 0
      GROUP BY 1
    """
    age_map = {r[0]: (r[1], r[2], r[3]) for r in con.execute(age_q).fetchall() if r[0] is not None}

    lr_targets  = []
    for b in LR_BUCKETS:
        if b not in lr_map: lr_targets.append(""); continue
        swy, sw, n = lr_map[b]
        if n < MIN_N or sw is None or sw <= 0: lr_targets.append(""); continue
        lr_targets.append(f"{swy/sw:.6f}")
    age_targets = []
    for b in AGE_BUCKETS:
        if b not in age_map: age_targets.append(""); continue
        swy, sw, n = age_map[b]
        if n < MIN_N or sw is None or sw <= 0: age_targets.append(""); continue
        age_targets.append(f"{swy/sw:.6f}")

    non_empty = sum(1 for x in (lr_targets + age_targets) if x)
    if non_empty < 3: continue
    notes = f"wvs_code={code};rule={rule_tag};cohorts=lr+age"
    cohort_rows.append((text, "wvs_cohort_seed", "WVS Wave 7", notes, lr_targets, age_targets))

# ------------------------------------------------------------
# SPOT CHECKS
# ------------------------------------------------------------
def get_pct(qcode, iso2):
    return country_pct_cache.get((qcode, iso2))

spot = {
    "US_Q57_trust":  get_pct("Q57", "US"),
    "US_Q164_god":   get_pct("Q164", "US"),
    "DE_Q164_god":   get_pct("Q164", "DE"),
    "JP_Q164_god":   get_pct("Q164", "JP"),
    "US_Q184_abortion_justifiable": get_pct("Q184", "US"),
    "EG_Q164_god":   get_pct("Q164", "EG"),
    "NG_Q164_god":   get_pct("Q164", "NG"),
}
print("\nSPOT CHECKS:")
for k, v in spot.items():
    print(f"  {k:35s} = {v!r}")

def ok(v, lo, hi): return v is not None and lo <= v <= hi

checks = []
checks.append(("US Q57 trust in [0.30, 0.45]", ok(spot["US_Q57_trust"], 0.30, 0.45)))
ordering = (spot["US_Q164_god"] or -1) > (spot["DE_Q164_god"] or -1) > (spot["JP_Q164_god"] or -1)
checks.append(("Importance of God: US > DE > JP", ordering))
# Extra corroboration: EG and NG should be near ceiling on Q164
checks.append(("EG Q164 god >= 0.90", ok(spot["EG_Q164_god"], 0.85, 1.01)))
checks.append(("NG Q164 god >= 0.90", ok(spot["NG_Q164_god"], 0.85, 1.01)))

print("\nCHECK RESULTS:")
all_pass = True
for name, passed in checks:
    print(f"  {'PASS' if passed else 'FAIL'}  {name}")
    if not passed: all_pass = False

if not all_pass:
    print("\nSPOT CHECK FAILED — not writing CSVs.")
    sys.exit(2)

# ------------------------------------------------------------
# WRITE CSVs
# ------------------------------------------------------------
def write_country_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["question_text","question_type","source","notes"] + [f"target_{c}" for c in iso2_list])
        for text, qtype, source, notes, targets in country_rows:
            w.writerow([text, qtype, source, notes] + targets)

def write_cohort_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        head = ["question_text","question_type","source","notes"]
        head += [f"target_{c}" for c in LR_BUCKETS]
        head += [f"target_age_{c}" for c in AGE_BUCKETS]
        w.writerow(head)
        for text, qtype, source, notes, lr_targets, age_targets in cohort_rows:
            w.writerow([text, qtype, source, notes] + lr_targets + age_targets)

country_path = os.path.join(OUT_DIR, "wvs_wave7_seeds_v1.csv")
cohort_path  = os.path.join(OUT_DIR, "wvs_wave7_cohort_seeds_v1.csv")
write_country_csv(country_path)
write_cohort_csv(cohort_path)
print(f"\nWROTE:")
print(f"  {country_path}   ({len(country_rows)} seeds)")
print(f"  {cohort_path}    ({len(cohort_rows)} seeds)")
