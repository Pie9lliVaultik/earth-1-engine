#!/usr/bin/env python3
"""
aggregate_anes.py — ANES 2024 Time Series -> political/age cohort calibration seeds.

Committed to the repo 2026-07-14 per the covenant audit doc-vs-repo reconciliation
(was delivered out-of-band, never committed). Companion: docs/COVENANT_AUDIT.md §4.

Provenance: ANES 2024 Time Series Study, Full Release CSV (May 19, 2026 version),
anes_timeseries_2024_csv_20260519.csv, n=5,521. Codebook shipped in same zip.
Weights: V240107a (pre-election full sample) for V241* items; V240107b (post) for V242* items.
Cohorts: V241177 lib-con 7pt -> far_left..far_right (99 & negatives excluded);
age V241458x numeric (80=topcode, negatives excluded) -> 6 buckets.
Missing: ALL negative codes excluded from numerator and denominator; 99 excluded on 7pt scales.
Cell rule: unweighted n >= 60 else cohort column dropped; seed kept if >= 3 cohorts.
"""
import pandas as pd, numpy as np, csv, sys

CSV = "/home/claude/anes/anes_timeseries_2024_csv_20260519.csv"
OUT = "/home/claude/anes/anes_cohort_seeds_v1.csv"

# var: (question_text, yes_codes, valid_codes, rule_note)
IT = {
 "V241302": ("By law, should a woman always be able to obtain an abortion as a matter of personal choice?", {4},{1,2,3,4},"std abortion 4pt; yes=always personal choice; code5 other excluded"),
 "V241382": ("Should gay and lesbian couples be allowed to legally marry?", {1},{1,2,3},"3pt; yes=legally marry"),
 "V241379": ("Should gay and lesbian couples be legally permitted to adopt children?", {1},{1,2},"binary yes/no"),
 "V241306": ("Do you favor the death penalty for persons convicted of murder?", {1},{1,2},"favor/oppose"),
 "V241393": ("Do you favor building a wall on the US border with Mexico?", {1},{1,2,3},"favor of favor/oppose/neither"),
 "V241387": ("Do you favor ending birthright citizenship?", {1},{1,2,3},"favor of 3"),
 "V241407": ("In the Middle East conflict, do you side more with the Israelis?", {1},{1,2,3,4},"yes=Israelis of Israelis/Palestinians/both/neither"),
 "V241400x": ("Do you favor sending weapons to help Ukraine fight Russia?", {1,2,3},{1,2,3,4,5,6,7},"7pt summary; yes=favor 1-3"),
 "V241314": ("Do you think votes in the November 2024 general election will be counted very or completely accurately?", {4,5},{1,2,3,4,5},"yes=very+completely of 5"),
 "V241239": ("Should the government provide more services and increase spending?", {5,6,7},{1,2,3,4,5,6,7},"7pt; yes=5-7 more services; 99 excluded"),
 "V241242": ("Should defense spending be increased?", {5,6,7},{1,2,3,4,5,6,7},"7pt; yes=5-7 increase; 99 excluded"),
 "V241258": ("Are tougher regulations on business needed to protect the environment?", {1,2,3},{1,2,3,4,5,6,7},"7pt REVERSED; yes=1-3 tougher env regs; 99 excluded"),
 "V241252": ("Should the government see to it that every person has a job and a good standard of living?", {1,2,3},{1,2,3,4,5,6,7},"7pt; yes=1-3 govt guarantee; 99 excluded"),
 "V241248": ("On the 7-point abortion scale, do you place yourself on the pro-choice side?", {5,6,7},{1,2,3,4,5,6,7},"7pt abortion (1=never permit,7=always); yes=5-7; 99 excluded"),
 "V241360": ("Is the income gap between rich and poor larger today than 20 years ago?", {1},{1,2,3},"yes=larger"),
 "V241288": ("Do you approve of diversity, equity and inclusion (DEI) programs?", {1},{1,2,3},"favor of 3"),
 "V242362": ("Do you favor allowing transgender people to serve in the United States Armed Forces?", {1},{1,2,3},"POST; favor of 3"),
 "V242227": ("Should immigration levels be decreased?", {4,5},{1,2,3,4,5},"POST; yes=decreased a little/a lot"),
 "V242235": ("Are immigrants generally good for America?", {1,2,3},{1,2,3,4,5,6,7},"POST; yes=good side 1-3 of 7"),
 "V242321": ("Is climate change affecting severe weather events and temperature patterns a lot or a great deal?", {4,5},{1,2,3,4,5},"POST; yes=4-5"),
 "V242365": ("Is China a major threat to the United States?", {4,5},{1,2,3,4,5},"POST; yes=a lot/a great deal"),
 "V242366": ("Is Russia a major threat to the United States?", {4,5},{1,2,3,4,5},"POST; yes=a lot/a great deal"),
 "V242370": ("Is Israel a major threat to the United States?", {4,5},{1,2,3,4,5},"POST; yes=a lot/a great deal"),
 "V242344": ("Do you favor the United States making free trade agreements with other countries?", {1},{1,2,3},"POST; favor of 3"),
 "V242553": ("Is there a great deal or a lot of discrimination against gays and lesbians in the US?", {1,2},{1,2,3,4,5},"POST; yes=1-2 of 5"),
 "V242347": ("Has increasing diversity made the United States a better place to live?", {1},{1,2,3},"POST; yes=better of better/worse/no difference — VERIFY code order at runtime"),
}

POL = {1:"far_left",2:"left",3:"center_left",4:"centrist",5:"center_right",6:"right",7:"far_right"}
AGEB = [("18-24",18,24),("25-34",25,34),("35-44",35,44),("45-54",45,54),("55-64",55,64),("65+",65,200)]
COHORTS = list(POL.values()) + [a[0] for a in AGEB]
MIN_N = 60

def wmean(vals, wts, yes, valid):
    ok = vals.isin(valid)
    v, w = vals[ok], wts[ok]
    if len(v) < MIN_N: return None, len(v)
    return float(((v.isin(yes)).astype(float)*w).sum()/w.sum()), len(v)

def main():
    cols = ["V241177","V241458x","V240107a","V240107b"] + list(IT.keys())
    df = pd.read_csv(CSV, usecols=lambda c: c in cols, low_memory=False)
    print("rows:", len(df), "cols:", len(df.columns))
    for c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

    pol = df["V241177"].where(df["V241177"].between(1,7))
    age = df["V241458x"].where(df["V241458x"]>=18)
    masks = {name: pol==code for code,name in POL.items()}
    for name,lo,hi in AGEB: masks[name] = (age>=lo)&(age<=hi)

    wpre = df["V240107a"].where(df["V240107a"]>0)
    wpost = df["V240107b"].where(df["V240107b"]>0)
    pv = pol[wpre.notna() & pol.notna()]
    wv = wpre[wpre.notna() & pol.notna()]
    dist = {POL[k]: round(float(((pv==k)*wv).sum()/wv.sum()),4) for k in POL}
    print("V241177 weighted dist:", dist)

    rows, national = [], {}
    for var,(qt,yes,valid,rule) in IT.items():
        if var not in df.columns: print(f"!! {var} missing"); continue
        w = wpre if var.startswith("V241") else wpost
        m0 = df[var].notna() & w.notna()
        nat, natn = wmean(df.loc[m0,var], w[m0], yes, valid)
        national[var] = nat
        row = {"question_text":qt,"question_type":"anes_seed",
               "source":"ANES 2024 Time Series (n=5,521)",
               "notes":f"{rule}; var={var}; weight={'V240107a' if var.startswith('V241') else 'V240107b'}; national={None if nat is None else round(nat,4)} (n={natn})"}
        kept=0
        for c in COHORTS:
            m = m0 & masks[c].fillna(False)
            val,n = wmean(df.loc[m,var], w[m], yes, valid)
            if val is not None: row[f"target_{c}"]=round(val,4); kept+=1
        if kept>=3: rows.append(row)
        else: print(f"-- {var}: only {kept} cohorts, dropped")

    # SPOT-CHECK GATE (ANES-instrument bands from 2020 vintage + plausibility)
    checks = [
      ("lib-con: centrist(moderate) is modal cohort", dist, lambda d: max(d,key=d.get)=="centrist"),
      ("gay marriage V241382 in [0.58,0.75]", national.get("V241382"), lambda x: x and 0.58<=x<=0.75),
      ("death penalty V241306 in [0.52,0.70] (ANES reads high vs Gallup)", national.get("V241306"), lambda x: x and 0.52<=x<=0.70),
      ("abortion always-choice V241302 in [0.38,0.58]", national.get("V241302"), lambda x: x and 0.38<=x<=0.58),
      ("wall favor V241393 in [0.35,0.55]", national.get("V241393"), lambda x: x and 0.35<=x<=0.55),
    ]
    ab = [r for r in rows if "var=V241302" in r["notes"]]
    if ab:
        seq=[ab[0].get(f"target_{c}") for c in list(POL.values())]
        mono=all(a>=b-0.025 for a,b in zip(seq,seq[1:]) if a is not None and b is not None)
        checks.append(("abortion monotonic far_left>=..>=far_right (2.5pp tol)", seq, lambda _: mono))
    wall = [r for r in rows if "var=V241393" in r["notes"]]
    if wall:
        seq=[wall[0].get(f"target_{c}") for c in list(POL.values())]
        mono=all(a<=b+0.025 for a,b in zip(seq,seq[1:]) if a is not None and b is not None)
        checks.append(("wall monotonic INCREASING left->right (2.5pp tol)", seq, lambda _: mono))

    print("\n==== SPOT-CHECK GATE ====")
    fails=0
    for name,val,fn in checks:
        ok=fn(val); print(("PASS " if ok else "FAIL "),name,"->",val)
        fails+=(not ok)
    if fails: print(f"\nGATE FAILED ({fails}) — NOT writing CSV."); sys.exit(2)

    fields=["question_text","question_type","source"]+[f"target_{c}" for c in COHORTS]+["notes"]
    with open(OUT,"w",newline="") as f:
        wtr=csv.DictWriter(f,fieldnames=fields); wtr.writeheader()
        for r in rows: wtr.writerow({k:r.get(k,"") for k in fields})
    print(f"\nWROTE {OUT}: {len(rows)} seeds")

if __name__=="__main__": main()
