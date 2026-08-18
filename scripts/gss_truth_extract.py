"""THE RULER — real verified opinion time series from GSS microdata.

Instruction (2026-08-18): stop testing dynamics against authored
truth. This builds the replacement from data already on the machine:
the General Social Survey 1972-2024 (Release 3), real respondent
microdata, a DIFFERENT survey organisation from WVS/GOQA, never used
in any Earth-1 calibration.

What it produces:
  data/gss_truth.json
    per (variable, year): weighted national share + n
    per (variable, year, age bucket, education): weighted share + n
so every temporal, cohort and distributional claim can be graded
against measured reality with 50 years of movement to predict.

Variables chosen for coverage across decades and for having genuine
movement (abortion, confidence, tolerance, trust, gender roles).
Weight: WTSSNRPS where present, else WTSSALL / WTSSPS.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import zipfile

import numpy as np
import pandas as pd

RAW_ZIP = "/opt/earth1/rawdata/GSS_stata.zip"
WORK = "/tmp/gss"

# variable -> (positive-response codes, human label)
VARS = {
    "abany": ([1], "Abortion legal for any reason"),
    "abdefect": ([1], "Abortion legal if serious defect"),
    "cappun": ([1], "Favour death penalty for murder"),
    "grass": ([1], "Marijuana should be legal"),
    "homosex": ([4], "Homosexual relations not wrong at all"),
    "fechld": ([1, 2], "Working mother can have warm relationship"),
    "fepresch": ([3, 4], "Preschool child does NOT suffer if mother works"),
    "trust": ([1], "Most people can be trusted"),
    "confinan": ([1], "Great confidence in banks"),
    "conmedic": ([1], "Great confidence in medicine"),
    "conpress": ([1], "Great confidence in press"),
    "conlegis": ([1], "Great confidence in Congress"),
    "polviews": ([1, 2, 3], "Liberal self-placement"),
    "natenvir": ([1], "Too little spending on environment"),
    "racopen": ([2], "Support open-housing law"),
}
AGE_BINS = [(18, 29, "18_29"), (30, 44, "30_44"),
            (45, 59, "45_59"), (60, 200, "60_plus")]


def edu_bucket(v):
    if pd.isna(v):
        return None
    return 0 if v < 12 else (1 if v < 16 else 2)


def main() -> None:
    os.makedirs(WORK, exist_ok=True)
    if not glob.glob(f"{WORK}/*.dta"):
        with zipfile.ZipFile(RAW_ZIP) as z:
            for n in z.namelist():
                if n.lower().endswith(".dta"):
                    z.extract(n, WORK)
    dta = sorted(glob.glob(f"{WORK}/**/*.dta", recursive=True),
                 key=os.path.getsize)[-1]
    print(f"reading {os.path.basename(dta)}", flush=True)
    cols = ["year", "age", "educ", "wtssnrps", "wtssall", "wtssps"] + \
        list(VARS)
    df = pd.read_stata(dta, columns=None, convert_categoricals=False,
                       chunksize=None)
    have = [c for c in cols if c in df.columns]
    df = df[have]
    wcol = next((c for c in ("wtssnrps", "wtssall", "wtssps")
                 if c in df.columns), None)
    df["_w"] = df[wcol].fillna(1.0) if wcol else 1.0
    print(f"  {len(df):,} respondents, weight column: {wcol}", flush=True)

    out = {}
    for var, (pos, label) in VARS.items():
        if var not in df.columns:
            continue
        sub = df[df[var].notna() & (df[var] > 0)].copy()
        if len(sub) < 500:
            continue
        sub["_y"] = sub[var].isin(pos).astype(float)
        national, cells = {}, {}
        for yr, g in sub.groupby("year"):
            if g["_w"].sum() < 200:
                continue
            national[str(int(yr))] = {
                "share": round(float(np.average(g["_y"], weights=g["_w"])), 5),
                "n": int(len(g))}
            if "age" in g.columns and "educ" in g.columns:
                for lo, hi, tag in AGE_BINS:
                    for eb in (0, 1, 2):
                        cm = g[(g["age"] >= lo) & (g["age"] <= hi)
                               & (g["educ"].map(edu_bucket) == eb)]
                        if len(cm) >= 40:
                            cells[f"{int(yr)}|{tag}|{eb}"] = {
                                "share": round(float(np.average(
                                    cm["_y"], weights=cm["_w"])), 5),
                                "n": int(len(cm))}
        if len(national) >= 10:
            years = sorted(int(y) for y in national)
            shares = [national[str(y)]["share"] for y in years]
            out[var] = {"label": label, "national": national,
                        "cells": cells,
                        "span": [years[0], years[-1]],
                        "total_movement": round(shares[-1] - shares[0], 4)}
            print(f"  {var:10s} {years[0]}-{years[-1]}  "
                  f"{len(national):3d} years, {len(cells):4d} cells | "
                  f"{shares[0]:.3f} -> {shares[-1]:.3f} "
                  f"({shares[-1]-shares[0]:+.3f})", flush=True)
    json.dump(out, open("data/gss_truth.json", "w"), indent=1)
    print(f"GSS-TRUTH: {len(out)} variables, "
          f"{sum(len(v['national']) for v in out.values())} country-years, "
          f"{sum(len(v['cells']) for v in out.values())} cohort cells",
          flush=True)


if __name__ == "__main__":
    main()
