"""Benchmark A v2 — frozen protocol (BENCHMARK_A_PREREG_v2.md, 509a1ce).
Stages: confirm_targets (builds the untouched confirmation set AFTER the
freeze) -> baselines (incl. OOS MRP anchors; before Earth-1) -> earth1
(anchored mean-preserving hybrid) -> score (ONCE; leakage guard on every
row; compression trace)."""
import hashlib, json, os, re, subprocess, sys, time
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
from earth1.benchmark_a import scoring as S
from earth1.benchmark_a.mean_preserving import solve_K, center_latent, ka_mean_preservation
from earth1.benchmark_a.leakage import assert_anchor_oos
from earth1.rng import logit, sigmoid
OUT = os.path.join(ROOT, "data", "benchmark_a"); os.makedirs(OUT, exist_ok=True)
OUTD = "/opt/earth1-data/benchmark_a"
FOLDS, CV_SEEDS, POP, DAYS = 5, (42, 7, 13), 200_000, 60
WORLD_SEEDS = (42, 20260901, 20260902)
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0)
BANDS = ("18-29", "30-49", "50+")
CONSUMED = {"Q10", "Q23", "Q51", "Q68", "Q86", "Q138", "Q169", "Q196"}


def stamp(extra=None):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return {"commit": sha, "scoring_sha256": S.sha256_of_file(os.path.join(ROOT, "earth1/benchmark_a/scoring.py")),
            "mean_preserving_sha256": S.sha256_of_file(os.path.join(ROOT, "earth1/benchmark_a/mean_preserving.py")),
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **(extra or {})}


def folds_for(codes, seed):
    order = np.random.default_rng(seed).permutation(len(codes))
    return [[codes[i] for i in order[f::FOLDS]] for f in range(FOLDS)]


def run_confirm_targets():
    import duckdb
    from earth1.benchmark_questions import ISO3_TO_ISO2
    from earth1.genesis import GENESIS_COUNTRY_CODES
    ns = {}; exec(open(os.path.join(ROOT, 'imported_vnf/scripts/wvs7_labels.py')).read(), ns)
    L = ns.get('LABELS') or ns.get('labels')
    goqa = {q['id'] for q in json.load(open(os.path.join(ROOT, 'data/benchmark/goqa_ground_truth.json')))}
    cand = sorted([k for k in L if re.fullmatch(r"Q\d+", k) and k not in goqa and k not in CONSUMED], key=lambda k: int(k[1:]))
    con = duckdb.connect(os.path.join(OUTD, "wvs7.duckdb"), read_only=True)
    genesis = set(GENESIS_COUNTRY_CODES)
    items, targets, cohorts = {}, {}, {}
    for c in cand:
        try:
            mn, mx = con.execute(f"SELECT min({c}), max({c}) FROM wvs WHERE {c} >= 0").fetchone()
        except Exception:
            continue
        if mx is None: continue
        mx = int(mx)
        if mx <= 2: rule, e = "=1", f"CASE WHEN {c}=1 THEN 1 ELSE 0 END"
        elif mx <= 5: rule, e = "top2", f"CASE WHEN {c} IN (1,2) THEN 1 ELSE 0 END"
        elif mx == 10: rule, e = ">=6", f"CASE WHEN {c}>=6 THEN 1 ELSE 0 END"
        else: continue
        rows = con.execute(f"SELECT B_COUNTRY_ALPHA, SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) FROM wvs WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 GROUP BY 1").fetchall()
        t = {ISO3_TO_ISO2.get(r[0]): {"yes": round(float(r[1]), 6), "n": int(r[2])} for r in rows if ISO3_TO_ISO2.get(r[0]) in genesis and r[2] >= 100}
        if len(t) < 40: continue
        rows = con.execute(f"""SELECT B_COUNTRY_ALPHA, CASE WHEN Q262<30 THEN '18-29' WHEN Q262<50 THEN '30-49' ELSE '50+' END,
            SUM(W_WEIGHT*({e}))/SUM(W_WEIGHT), count(*) FROM wvs WHERE {c} IS NOT NULL AND {c}>=0 AND W_WEIGHT>0 AND Q262>=18 GROUP BY 1,2""").fetchall()
        cc = {}
        for iso3, band, share, n in rows:
            iso2 = ISO3_TO_ISO2.get(iso3)
            if iso2 in t and n >= 50: cc.setdefault(iso2, {})[band] = {"yes": round(float(share), 6), "n": int(n)}
        items[c] = {"text": L[c], "rule": rule, "scale_max": mx}
        targets[c] = t; cohorts[c] = cc
    conf = sorted(items, key=lambda k: int(k[1:]))
    joint_items = sorted(conf, key=lambda c: (-len(targets[c]), int(c[1:])))[:8]
    stride = max(1, len(conf) // 8)
    zeroshot = [conf[i] for i in range(0, len(conf), stride)][:8]
    ex = ", ".join(f"CASE WHEN {c} IS NULL OR {c}<0 THEN -1 WHEN " + {"=1": f"{c}=1", "top2": f"{c} IN (1,2)", ">=6": f"{c}>=6"}[items[c]["rule"]] + f" THEN 1 ELSE 0 END AS {c}_b" for c in joint_items)
    rows = con.execute(f"SELECT B_COUNTRY_ALPHA, W_WEIGHT, {ex} FROM wvs WHERE W_WEIGHT>0").fetchall()
    by = {}
    for r in rows:
        iso2 = ISO3_TO_ISO2.get(r[0])
        if iso2 in genesis and all(v >= 0 for v in r[2:]): by.setdefault(iso2, []).append(r[1:])
    npz = {}
    for iso2, rr in by.items():
        a = np.array(rr, float)
        if a.shape[0] >= 100: npz[f"{iso2}_w"] = a[:, 0]; npz[f"{iso2}_x"] = a[:, 1:].astype(np.int8)
    np.savez_compressed(os.path.join(OUTD, "joint_vectors_confirm_v2.npz"), **npz)
    out = {"items": items, "targets": targets, "cohorts": cohorts, "joint_items": joint_items, "zeroshot_items": zeroshot,
           "n_items": len(conf), "stamp": stamp()}
    p = os.path.join(OUT, "confirm_targets_v2.json"); json.dump(out, open(p, "w"), indent=1, sort_keys=True)
    print("CONFIRM TARGETS", len(conf), "items; joints", joint_items, "; zeroshot", zeroshot, "; sha", S.sha256_of_file(p)[:16])


def run_baselines():
    from earth1.alive import birth_world
    from mrp_baseline import build_context, fit_mrsp, LAMBDAS as ML, TAUS
    from earth1.calibration import _get_country_index
    D = json.load(open(os.path.join(OUT, "confirm_targets_v2.json")))
    w = birth_world(POP, 42); civ = w.civ
    c2i, codes = _get_country_index(civ); ctx, cells, usable = build_context(civ, codes)
    res = {"anchors": {}, "cohort": {}, "joint": {}, "zeroshot": {}, "stamp": stamp()}

    def mrp_fold(train, y, test, band_rows=None):
        g = float(np.mean([y[k] for k in train])); bl = logit(np.array([g]))[0]
        if band_rows is None:
            X = np.array([ctx[k] for k in train]); yv = np.array([logit(np.array([y[k]]))[0] - bl for k in train])
        else:
            X = np.array([r[0] for r in band_rows]); yv = np.array([r[1] - bl for r in band_rows])
        mu, sd = X.mean(0), X.std(0); sd = np.where(sd > 1e-9, sd, 1.0); Xs = (X - mu) / sd
        best, be = (ML[0], TAUS[0]), np.inf
        for lam in ML:
            for tau in TAUS:
                errs = []
                for i in range(len(yv)):
                    k = np.arange(len(yv)) != i
                    b = fit_mrsp(Xs[k], yv[k], lam, tau); errs.append((yv[i] - (b[0] + Xs[i] @ b[1:])) ** 2)
                if (e := float(np.mean(errs))) < be: best, be = (lam, tau), e
        beta = fit_mrsp(Xs, yv, *best)
        return bl, mu, sd, beta

    for c, t in D["targets"].items():
        cs = sorted(k for k in t if k in ctx and k in cells); y = {k: t[k]["yes"] for k in cs}
        coh = D["cohorts"][c]
        for seed in CV_SEEDS:
            anch, coh_out = {}, {}
            for test in folds_for(cs, seed):
                train = [k for k in cs if k not in set(test)]
                if len(train) < 8: continue
                bl, mu, sd, beta = mrp_fold(train, y, test)
                off = {b: float(np.mean([coh[k][b]["yes"] - y[k] for k in train if k in coh and b in coh[k]] or [0.0])) for b in BANDS}
                # cohort-MRP (registered): band dummies + band x context
                def brow(k, bi):
                    d = np.zeros(3); d[bi] = 1
                    return np.concatenate([ctx[k], d, np.kron(d, ctx[k])])
                br = [(brow(k, bi), logit(np.array([coh[k][b]["yes"]]))[0])
                      for k in train for bi, b in enumerate(BANDS)
                      if k in coh and b in coh[k]]
                blc, muc, sdc, betac = mrp_fold(train, y, test, band_rows=br) if len(br) >= 24 else (None,) * 4
                for k in test:
                    x = (ctx[k] - mu) / sd; lin = beta[0] + x @ beta[1:]
                    a = float(np.sum(cells[k] * sigmoid(np.full(len(cells[k]), bl + lin))))
                    anch[k] = {"anchor": a, "anchor_train_countries": train, "anchor_model": "mrp"}
                    if k in coh:
                        co = {}
                        for bi, b in enumerate(BANDS):
                            if b not in coh[k]: continue
                            row = {"truth": coh[k][b]["yes"], "national_copy": a, "global_gradient": float(np.clip(a + off[b], 0, 1)), "truth_national": y[k]}
                            if blc is not None:
                                xc = (brow(k, bi) - muc) / sdc
                                row["cohort_mrp"] = float(sigmoid(blc + betac[0] + xc @ betac[1:]))
                            co[b] = row
                        coh_out[k] = co
            res["anchors"].setdefault(c, {})[str(seed)] = anch
            res["cohort"].setdefault(c, {})[str(seed)] = coh_out
    # joints: independence with OOS MRP marginals (seed 42 folds)
    Z = np.load(os.path.join(OUTD, "joint_vectors_confirm_v2.npz")); rng = np.random.default_rng(0)
    JI = D["joint_items"]
    for iso in sorted(k[:-2] for k in Z.files if k.endswith("_x")):
        X = Z[f"{iso}_x"].astype(np.int8); wt = Z[f"{iso}_w"]
        anch = [res["anchors"].get(c, {}).get("42", {}).get(iso, {}).get("anchor") for c in JI]
        if any(a is None for a in anch): continue
        p = np.array(anch)
        synth = (rng.random((X.shape[0], len(JI))) < p[None, :]).astype(np.int8)
        res["joint"][iso] = {"n": int(X.shape[0]), "mrp_marginals": [float(v) for v in p],
                             "anchor_train_countries": res["anchors"][JI[0]]["42"][iso]["anchor_train_countries"],
                             "independent_mrp_energy": S.energy_distance(synth, X, None, wt, seed=1)}
    # zero-shot: semantic neighbour (dev items) + neighbour's OOS MRP anchor
    from earth1.embedder import embed
    dev = json.load(open(os.path.join(OUT, "targets_v1.json")))
    devq = [c for c, it in dev["items"].items() if it["set"] == "goqa"]
    texts = [dev["items"][c]["text"] for c in devq] + [D["items"][c]["text"] for c in D["zeroshot_items"]]
    E = embed(texts); E = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
    base_v1 = json.load(open(os.path.join(OUT, "baselines_v1.json")))
    for zi, c in enumerate(D["zeroshot_items"]):
        sims = [(float(E[len(devq) + zi] @ E[i]), devq[i]) for i in range(len(devq))]
        sim, nb = max(sims)
        a = base_v1["national"].get(nb, {}).get("42", {})
        cs_nb = sorted(a.get("truth", {}))                 # the neighbour's country list (v1 protocol)
        fold_of = {}
        for fold in folds_for(cs_nb, 42):
            for k in fold: fold_of[k] = set(fold)
        anch = {}
        for k in D["targets"][c]:
            if k in a.get("mrp", {}) and k in fold_of:
                train = [x for x in cs_nb if x not in fold_of[k]]
                anch[k] = {"anchor": a["mrp"][k], "anchor_train_countries": train, "anchor_model": f"mrp-transfer:{nb}"}
        res["zeroshot"][c] = {"neighbour": nb, "cosine": sim, "anchors": anch, "truth": {k: D["targets"][c][k]["yes"] for k in D["targets"][c]}}
    p = os.path.join(OUT, "baselines_confirm_v2.json"); json.dump(p and res, open(p, "w"), indent=1)
    print("BASELINES V2 WRITTEN")


if __name__ == "__main__":
    {"confirm_targets": run_confirm_targets, "baselines": run_baselines}[sys.argv[1]]()
