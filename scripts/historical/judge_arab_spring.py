"""Arab Spring judge fetch + one-pass scoring (post-freeze only).

Judge: real protest events (GDELT EventRootCode 14) by country,
2010-12-17..2011-03-16, from the archive months; regime outcomes
recorded with Wikipedia provenance fetches. Model vectors come from the
FROZEN pairs: per-country Δfear (unrest basis, declared) and the frozen
hungry_by_country geography. Scored once; basis stamped; no reruns.
"""
import hashlib
import io
import json
import os
import sys
import zipfile
from datetime import date

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
GD = "/opt/earth1-data/gdelt"
W0, W1 = date(2010, 12, 17), date(2011, 3, 16)
FIPS = json.load(open(os.path.join(ROOT, "data/geo/fips_to_iso2.json")))["map"]


def judge_counts():
    counts = {}
    shas = {}
    for m in ("201012", "201101", "201102", "201103"):
        zp = os.path.join(GD, f"gdelt_{m}.zip")
        shas[m] = hashlib.sha256(open(zp, "rb").read()).hexdigest()[:16]
        with zipfile.ZipFile(zp) as z:
            with z.open(z.namelist()[0]) as f:
                for raw in io.TextIOWrapper(f, errors="replace"):
                    cols = raw.rstrip("\n").split("\t")
                    if len(cols) < 55:
                        continue
                    try:
                        d = date(int(cols[1][:4]), int(cols[1][4:6]),
                                 int(cols[1][6:8]))
                    except ValueError:
                        continue
                    if not (W0 <= d <= W1):
                        continue
                    root = cols[28][:2] if len(cols) > 28 else ""
                    if root != "14":            # PROTEST root code
                        continue
                    iso2 = FIPS.get(cols[51][:2] if len(cols) > 51 else "")
                    if iso2:
                        counts[iso2] = counts.get(iso2, 0) + 1
    return counts, shas


def model_vectors():
    import pickle
    dfear, dhung = {}, {}
    from earth1.genesis import GENESIS_COUNTRY_CODES as GCC
    for s in range(51, 67):
        p = f"/opt/earth1-data/historical/arab_spring/pair_{s}.pkl"
        if not os.path.exists(p):
            continue
        pair = pickle.load(open(p, "rb"))
        use = max(pair["scn"]["snaps"])
        fa = pair["scn"]["snaps"][use]["fear_by_country"]
        fb = pair["null"]["snaps"][use]["fear_by_country"]
        ha = pair["scn"]["snaps"][use].get("hungry_by_country")
        hb = pair["null"]["snaps"][use].get("hungry_by_country")
        for ci, iso in enumerate(GCC):
            dfear.setdefault(iso, []).append(float(fa[ci] - fb[ci]))
            if ha is not None and hb is not None:
                dhung.setdefault(iso, []).append(float(ha[ci] - hb[ci]))
    return ({k: float(np.mean(v)) for k, v in dfear.items()},
            {k: float(np.mean(v)) for k, v in dhung.items()})


def main():
    from scipy.stats import spearmanr
    counts, shas = judge_counts()
    dfear, dhung = model_vectors()
    MENA = ["EG", "TN", "LY", "YE", "SY", "JO", "MA", "DZ", "IQ", "LB",
            "SA", "BH", "KW", "OM", "AE", "QA"]
    rows = {}
    for basis_name, vec in (("fear_by_country", dfear),
                            ("hungry_by_country", dhung)):
        ov_all = [k for k in counts if k in vec]
        ov_mena = [k for k in MENA if k in counts and k in vec]
        r_all, p_all = spearmanr([vec[k] for k in ov_all],
                                 [counts[k] for k in ov_all])
        r_m, p_m = (spearmanr([vec[k] for k in ov_mena],
                              [counts[k] for k in ov_mena])
                    if len(ov_mena) >= 5 else (float("nan"), float("nan")))
        rows[basis_name] = {
            "spearman_global": round(float(r_all), 3),
            "p_global": round(float(p_all), 4), "n_global": len(ov_all),
            "spearman_mena": round(float(r_m), 3),
            "p_mena": round(float(p_m), 4), "n_mena": len(ov_mena)}
    real_top = sorted(counts.items(), key=lambda kv: -kv[1])[:10]
    model_top_fear = sorted(dfear.items(), key=lambda kv: -kv[1])[:10]
    out = {"judge": {"window": f"{W0}..{W1}",
                     "source": "GDELT 1.0 EventRootCode=14 by country",
                     "archive_shas": shas,
                     "total_protest_events": sum(counts.values()),
                     "real_top10": real_top},
           "model_top10_fear_basis": model_top_fear,
           "scores": rows,
           "regime_note": ("regime outcomes (TN 2011-01-14, EG "
                           "2011-02-11, LY, YE) are public record; "
                           "model regime chain was PRIOR-flagged weak "
                           "(legitimacy response |t|<1.2) and is scored "
                           "qualitative-only in the battery row")}
    json.dump(out, open(os.path.join(
        ROOT, "ops/alive/historical/arab_spring_scored.json"), "w"),
        indent=1)
    print(json.dumps(out["scores"], indent=1))
    print("real top5:", real_top[:5])
    print("model top5 (fear):", model_top_fear[:5])


if __name__ == "__main__":
    main()
