#!/usr/bin/env python3
"""
aggregate_gss.py — GSS 2022+2024 pooled -> political/age cohort calibration seeds.

Provenance: GSS 1972-2024 Cross-Sectional Cumulative (Release 3, March 2026), gss7224_r3.dta.
Weight: WTSSNRPS (post-stratification, non-response adjusted, 2021+). Missing: NaN / negative
codes excluded from numerator AND denominator. Cohorts: POLVIEWS 1..7 -> far_left..far_right
(native 7-to-7); AGE -> 6 buckets. Cell rule: unweighted n >= 60 else cohort column dropped.
Rules per scale family match docs/gss_extraction_shortlist.md.
"""
import pandas as pd, numpy as np, csv, sys

DTA = "/home/claude/gss/gss7224_r3.dta"
OUT = "/home/claude/gss/gss_cohort_seeds_v1.csv"

# item -> (question_text, yes_codes, valid_codes, rule_note)
IT = {
 # 1. abortion (1=yes 2=no)
 "abany":   ("Should it be possible for a pregnant woman to obtain a legal abortion if she wants it for any reason?", {1},{1,2},"binary"),
 "abdefect":("Should legal abortion be possible if there is a strong chance of a serious defect in the baby?", {1},{1,2},"binary"),
 "abnomore":("Should legal abortion be possible if a married woman wants no more children?", {1},{1,2},"binary"),
 "abhlth":  ("Should legal abortion be possible if the woman's own health is seriously endangered?", {1},{1,2},"binary"),
 "abpoor":  ("Should legal abortion be possible if the family has a very low income and cannot afford more children?", {1},{1,2},"binary"),
 "abrape":  ("Should legal abortion be possible if the pregnancy resulted from rape?", {1},{1,2},"binary"),
 "absingle":("Should legal abortion be possible if the woman is not married and does not want to marry the man?", {1},{1,2},"binary"),
 # 2. confidence (1=great deal 2=only some 3=hardly any)
 "confinan":("Do you have a great deal of confidence in banks and financial institutions?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conbus":  ("Do you have a great deal of confidence in major companies?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conclerg":("Do you have a great deal of confidence in organized religion?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "coneduc": ("Do you have a great deal of confidence in education?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "confed":  ("Do you have a great deal of confidence in the executive branch of the federal government?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conlabor":("Do you have a great deal of confidence in organized labor?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conpress":("Do you have a great deal of confidence in the press?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conmedic":("Do you have a great deal of confidence in medicine?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "contv":   ("Do you have a great deal of confidence in television?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conjudge":("Do you have a great deal of confidence in the U.S. Supreme Court?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "consci":  ("Do you have a great deal of confidence in the scientific community?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conlegis":("Do you have a great deal of confidence in Congress?", {1},{1,2,3},"rule=1of3_greatdeal"),
 "conarmy": ("Do you have a great deal of confidence in the military?", {1},{1,2,3},"rule=1of3_greatdeal"),
 # 3. misanthropy
 "trust":  ("Generally speaking, would you say that most people can be trusted?", {1},{1,2,3},"yes=can_trust of 3"),
 "fair":   ("Do you think most people would try to be fair rather than take advantage of you?", {2},{1,2,3},"yes=fair of 3"),
 "helpful":("Would you say that most of the time people try to be helpful?", {1},{1,2,3},"yes=helpful of 3"),
 # 4. crime/guns
 "cappun": ("Do you favor the death penalty for persons convicted of murder?", {1},{1,2},"binary favor"),
 "gunlaw": ("Would you favor a law requiring a person to obtain a police permit before buying a gun?", {1},{1,2},"binary favor"),
 "owngun": ("Do you have a gun in your home?", {1},{1,2},"binary; refused excluded"),
 "courts": ("Do courts in this area deal with criminals not harshly enough?", {2},{1,2,3},"yes=not_harsh_enough of 3"),
 "grass":  ("Should the use of marijuana be made legal?", {1},{1,2},"binary"),
 "polhitok":("Are there any situations you can imagine in which you would approve of a policeman striking an adult male citizen?", {1},{1,2},"binary"),
 # 5. religion
 "god":    ("Do you believe in God (knowing God exists or believing with some doubts)?", {5,6},{1,2,3,4,5,6},"rule=top2of6"),
 "postlife":("Do you believe there is a life after death?", {1},{1,2},"binary"),
 "pray":   ("Do you pray at least once a day?", {1,2},{1,2,3,4,5,6},"rule=daily+ of 6"),
 "attend": ("Do you attend religious services nearly every week or more often?", {6,7,8},{0,1,2,3,4,5,6,7,8},"rule=6-8of0-8"),
 "reliten":("Would you call yourself a strong follower of your religion?", {1},{1,2,3,4},"yes=strong of 4"),
 "prayer": ("Do you approve of the Supreme Court ruling that no state or local government may require the reading of the Lord's Prayer or Bible verses in public schools?", {1},{1,2},"binary approve"),
 "bible":  ("Is the Bible the actual word of God, to be taken literally, word for word?", {1},{1,2,3},"rule=1of3; code 4 excluded"),
 # 6. gender/family
 "fefam":   ("Is it much better for everyone involved if the man is the achiever outside the home and the woman takes care of the home and family?", {1,2},{1,2,3,4},"agree+strongly of 4"),
 "fechld":  ("Can a working mother establish just as warm and secure a relationship with her children as a mother who does not work?", {1,2},{1,2,3,4},"agree+strongly of 4"),
 "fepresch":("Is a preschool child likely to suffer if his or her mother works?", {1,2},{1,2,3,4},"agree+strongly of 4"),
 "fepol":   ("Are most men better suited emotionally for politics than are most women?", {1},{1,2},"binary agree"),
 "marsame": ("Should homosexual couples have the right to marry one another?", {1,2},{1,2,3,4,5},"agree+strongly of 5"),
 # 7. sexual morality (yes = not wrong at all)
 "premarsx":("Is sex before marriage not wrong at all?", {4},{1,2,3,4},"rule=4of4"),
 "xmarsex": ("Is extramarital sex not wrong at all?", {4},{1,2,3,4},"rule=4of4"),
 "homosex": ("Are sexual relations between two adults of the same sex not wrong at all?", {4},{1,2,3,4},"rule=4of4"),
 "teensex": ("Is sex between 14-16 year olds not wrong at all?", {4},{1,2,3,4},"rule=4of4"),
 "pornlaw": ("Should there be laws against the distribution of pornography whatever the age?", {1},{1,2,3},"yes=illegal_to_all of 3"),
 # 8. free speech (spk/lib 1/2; col 4/5)
 "spkath": ("Should a person who is against all churches and religion be allowed to make a speech in your community?", {1},{1,2},"binary allowed"),
 "colath": ("Should a person who is against all churches and religion be allowed to teach in a college or university?", {4},{4,5},"allowed=4of4/5"),
 "libath": ("If a person who is against churches and religion wrote a book, should it NOT be removed from your public library?", {2},{1,2},"yes=not_remove"),
 "spkrac": ("Should a person who believes that Black people are genetically inferior be allowed to make a speech in your community?", {1},{1,2},"binary allowed"),
 "colrac": ("Should a person who believes that Black people are genetically inferior be allowed to teach in a college or university?", {4},{4,5},"allowed=4of4/5"),
 "librac": ("If a person who believes Black people are genetically inferior wrote a book, should it NOT be removed from your public library?", {2},{1,2},"yes=not_remove"),
 "spkcom": ("Should an admitted Communist be allowed to make a speech in your community?", {1},{1,2},"binary allowed"),
 "colcom": ("Should an admitted Communist be allowed to teach in a college or university?", {4},{4,5},"allowed=4of4/5"),
 "libcom": ("If an admitted Communist wrote a book, should it NOT be removed from your public library?", {2},{1,2},"yes=not_remove"),
 "spkmil": ("Should a person who advocates doing away with elections and letting the military run the country be allowed to make a speech in your community?", {1},{1,2},"binary allowed"),
 "colmil": ("Should a person who advocates military rule be allowed to teach in a college or university?", {4},{4,5},"allowed=4of4/5"),
 "libmil": ("If a person advocating military rule wrote a book, should it NOT be removed from your public library?", {2},{1,2},"yes=not_remove"),
 "spkhomo":("Should a man who admits that he is a homosexual be allowed to make a speech in your community?", {1},{1,2},"binary allowed"),
 "colhomo":("Should a man who admits he is a homosexual be allowed to teach in a college or university?", {4},{4,5},"allowed=4of4/5"),
 "libhomo":("If a man who admits he is homosexual wrote a book, should it NOT be removed from your public library?", {2},{1,2},"yes=not_remove"),
 # 9. spending (1=too little)
 "natenvir":("Are we spending too little money on improving and protecting the environment?", {1},{1,2,3},"yes=too_little of 3"),
 "nateduc": ("Are we spending too little money on improving the nation's education system?", {1},{1,2,3},"yes=too_little of 3"),
 "natrace": ("Are we spending too little money on improving the conditions of Black Americans?", {1},{1,2,3},"yes=too_little of 3"),
 "natdrug": ("Are we spending too little money on dealing with drug addiction?", {1},{1,2,3},"yes=too_little of 3"),
 "natcrime":("Are we spending too little money on halting the rising crime rate?", {1},{1,2,3},"yes=too_little of 3"),
 "natarms": ("Are we spending too little money on the military, armaments and defense?", {1},{1,2,3},"yes=too_little of 3"),
 "nataid":  ("Are we spending too little money on foreign aid?", {1},{1,2,3},"yes=too_little of 3"),
 "natfare": ("Are we spending too little money on welfare?", {1},{1,2,3},"yes=too_little of 3"),
 "natheal": ("Are we spending too little money on improving and protecting the nation's health?", {1},{1,2,3},"yes=too_little of 3"),
 "natspac": ("Are we spending too little money on the space exploration program?", {1},{1,2,3},"yes=too_little of 3"),
 # gov role scales
 "eqwlth":  ("Should the government reduce income differences between the rich and the poor?", {1,2,3},{1,2,3,4,5,6,7},"rule=1-3of7"),
 "helppoor":("Should the government do everything possible to improve the standard of living of all poor Americans?", {1,2},{1,2,3,4,5},"rule=1-2of5"),
 "helpsick":("Is it the responsibility of the government in Washington to help people pay for doctor and hospital bills?", {1,2},{1,2,3,4,5},"rule=1-2of5"),
 "helpnot": ("Should the government do more to solve our country's problems?", {1,2},{1,2,3,4,5},"rule=1-2of5 (do-more side)"),
 "affrmact":("Do you favor preferential hiring and promotion of Black Americans?", {1,2},{1,2,3,4},"favor+strongly of 4"),
 "wrkwayup":("Do you agree that Black Americans should work their way up without any special favors?", {1,2},{1,2,3,4,5},"agree+strongly of 5"),
 # 10. wellbeing/class
 "happy":  ("Taking all things together, would you say you are very happy?", {1},{1,2,3},"yes=very of 3"),
 "health": ("Would you say your own health is excellent?", {1},{1,2,3,4},"yes=excellent of 4"),
 "satfin": ("Are you satisfied with your present financial situation?", {1},{1,2,3},"yes=satisfied of 3"),
 "class":  ("Do you consider yourself middle or upper class?", {3,4},{1,2,3,4},"rule=top2of4"),
 "getahead":("Do people get ahead mainly by their own hard work?", {1},{1,2,3},"yes=hard_work of 3"),
 "letdie1":("When a person has an incurable disease, should doctors be allowed by law to end the patient's life if the patient and family request it?", {1},{1,2},"binary"),
 "suicide1":("Does a person with an incurable disease have the right to end their own life?", {1},{1,2},"binary"),
 "divlaw": ("Should divorce in this country be easier to obtain?", {1},{1,2,3},"yes=easier of 3"),
}

POL = {1:"far_left",2:"left",3:"center_left",4:"centrist",5:"center_right",6:"right",7:"far_right"}
AGEB = [("18-24",18,24),("25-34",25,34),("35-44",35,44),("45-54",45,54),("55-64",55,64),("65+",65,200)]
COHORTS = list(POL.values()) + [a[0] for a in AGEB]
MIN_N = 60

def wmean(sub, yes_codes, valid_codes):
    v = sub[sub["val"].isin(valid_codes)]
    if len(v) < MIN_N: return None, len(v)
    w = v["wt"]
    y = v["val"].isin(yes_codes).astype(float)
    return float((y*w).sum()/w.sum()), len(v)

def main():
    cols = ["year","age","polviews","wtssnrps"] + list(IT.keys())
    print("reading columns:", len(cols))
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)
    df = df[df["year"].isin([2022,2024])].copy()
    print("pooled 2022+2024 rows:", len(df), "| by year:", df["year"].value_counts().to_dict())
    df["wt"] = pd.to_numeric(df["wtssnrps"], errors="coerce")
    df = df[df["wt"].notna() & (df["wt"]>0)]
    print("rows with valid weight:", len(df))
    df["polviews"] = pd.to_numeric(df["polviews"], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    # cohort masks
    masks = {}
    for code,name in POL.items(): masks[name] = df["polviews"]==code
    for name,lo,hi in AGEB: masks[name] = (df["age"]>=lo)&(df["age"]<=hi)

    # POLVIEWS distribution check
    pv = df[df["polviews"].between(1,7)]
    dist = {POL[k]: round(float(((pv["polviews"]==k)*pv["wt"]).sum()/pv["wt"].sum()),4) for k in POL}
    print("POLVIEWS weighted dist:", dist)

    rows, national = [], {}
    for var,(qt,yes,valid,rule) in IT.items():
        if var not in df.columns:
            print(f"  !! {var} missing from file"); continue
        sub_all = pd.DataFrame({"val": pd.to_numeric(df[var], errors="coerce"), "wt": df["wt"]}).dropna()
        nat, nat_n = wmean(sub_all, yes, valid)
        national[var] = (nat, nat_n)
        row = {"question_text": qt, "question_type":"gss_seed", "source":"GSS 2022-2024 pooled",
               "notes": f"{rule}; var={var}; weight=WTSSNRPS; national={nat if nat is None else round(nat,4)} (n={nat_n})"}
        kept = 0
        for c in COHORTS:
            sub = pd.DataFrame({"val": pd.to_numeric(df.loc[masks[c], var], errors="coerce"),
                                "wt": df.loc[masks[c], "wt"]}).dropna()
            val, n = wmean(sub, yes, valid)
            if val is not None:
                row[f"target_{c}"] = round(val,4); kept += 1
        if kept >= 3:
            rows.append(row)
        else:
            print(f"  -- {var}: only {kept} cohorts >= n{MIN_N}, seed dropped")

    # ---- SPOT-CHECK GATE ----
    def nat(v): return national.get(v,(None,0))[0]
    checks = [
        ("CAPPUN favor in [0.56,0.66] (GSS instrument; GSS2022 pub ~0.60; Gallup reads lower)", nat("cappun"), lambda x: x and 0.56<=x<=0.66),
        ("GRASS legal in [0.64,0.74]", nat("grass"), lambda x: x and 0.64<=x<=0.74),
        ("TRUST in [0.22,0.30] (GSS 2022 historic low ~0.26)", nat("trust"), lambda x: x and 0.22<=x<=0.30),
        ("GOD top2of6 in [0.62,0.80]", nat("god"), lambda x: x and 0.62<=x<=0.80),
        ("centrist largest cohort", dist, lambda d: max(d,key=d.get)=="centrist"),
    ]
    ab = [r for r in rows if "var=abany" in r["notes"]]
    if ab:
        seq = [ab[0].get(f"target_{c}") for c in ["far_left","left","center_left","centrist","center_right","right","far_right"]]
        mono = all(a >= b - 0.025 for a,b in zip(seq,seq[1:]) if a is not None and b is not None)  # 2.5pt tail-noise tolerance
        checks.append(("ABANY monotonic (2.5pt tolerance) far_left>=...>=far_right", seq, lambda _ : mono))
    print("\n==== SPOT-CHECK GATE ====")
    fails = 0
    for name, val, fn in checks:
        ok = fn(val)
        print(("PASS " if ok else "FAIL "), name, "->", val)
        if not ok: fails += 1
    if fails:
        print(f"\nGATE FAILED ({fails}) — NOT writing CSV."); sys.exit(2)

    # ---- write CSV ----
    cohort_cols = [f"target_{c}" for c in COHORTS]
    fields = ["question_text","question_type","source"]+cohort_cols+["notes"]
    with open(OUT,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
    print(f"\nWROTE {OUT}: {len(rows)} seeds x {len(cohort_cols)} cohort columns")

if __name__=="__main__":
    main()
