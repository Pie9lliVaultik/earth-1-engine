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


def _feature_treatment(Xc_list, names):
    """TRAIN-side rank analysis (prereg §4): drop exact/near-collinear
    columns (|r| > 0.98, later-by-order dropped); report condition
    number. Returns (kept_indices, report)."""
    M = np.array(Xc_list)
    keep = list(range(M.shape[1])); dropped = []
    R = np.corrcoef(M, rowvar=False)
    for j in range(M.shape[1]):
        for i in range(j):
            if i in keep and j in keep and abs(R[i, j]) > 0.98:
                keep.remove(j); dropped.append({"col": names[j], "collinear_with": names[i], "r": float(R[i, j])}); break
    cond = float(np.linalg.cond(M[:, keep] - M[:, keep].mean(0)))
    return keep, {"dropped": dropped, "condition_number": cond, "kept": [names[k] for k in keep]}


def run_earth1():
    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.calibration import living_features, living_feature_names, _get_country_index
    from earth1.persistence import world_hash
    D = json.load(open(os.path.join(OUT, "confirm_targets_v2.json")))
    B = json.load(open(os.path.join(OUT, "baselines_confirm_v2.json")))
    dev = json.load(open(os.path.join(OUT, "targets_v1.json")))
    Z = np.load(os.path.join(OUTD, "joint_vectors_confirm_v2.npz"))
    out = {"worlds": {}, "national_sanity": {}, "cohort": {}, "joint": {}, "zeroshot": {}, "feature_report": None,
           "stamp": stamp({"physics_version": PHYSICS_VERSION, "ka_mean_preservation": ka_mean_preservation()})}
    for ws in WORLD_SEEDS:
        t0 = time.time(); w = birth_world(POP, ws); rng = np.random.default_rng(ws)
        for _ in range(DAYS): live_one_day(w, rng)
        X = living_features(w); civ = w.civ; alive = w.health.alive
        c2i, codes = _get_country_index(civ)
        years = 18.0 + civ.age * 72.0
        band = np.where(years < 30, 0, np.where(years < 50, 1, 2))
        cmask = {k: (civ.country == c2i[k]) & alive for k in codes if k in c2i}
        Xc = {k: X[m].mean(0) for k, m in cmask.items() if m.sum() >= 30}
        if out["feature_report"] is None:
            keep, rep = _feature_treatment([Xc[k] for k in sorted(Xc)], living_feature_names(True))
            out["feature_report"] = rep; out["kept_cols"] = keep
        keep = out["kept_cols"]
        Xk = X[:, keep]
        out["worlds"][str(ws)] = {"world_hash": world_hash(w), "world_day": int(w.day), "alive": int(alive.sum()), "seconds": round(time.time() - t0, 1)}

        def fit_item(c, targets, seed):
            """ridge on TRAIN countries (lambda by inner LOO), returns per-country fitted latent fn."""
            cs = sorted(k for k in targets if k in Xc); y = {k: targets[k]["yes"] for k in cs}
            fits = {}
            for test in folds_for(cs, seed):
                train = [k for k in cs if k not in set(test)]
                if len(train) < 8: continue
                Xt = np.array([np.asarray(Xc[k])[keep] for k in train])
                yt = logit(np.clip(np.array([y[k] for k in train]), 0.02, 0.98))
                lam, be = LAMBDAS[0], np.inf
                for L in LAMBDAS:
                    errs = []
                    for i in range(len(yt)):
                        kk = np.arange(len(yt)) != i
                        mu, sd = Xt[kk].mean(0), Xt[kk].std(0) + 1e-9
                        Zt = (Xt[kk] - mu) / sd; b0 = yt[kk].mean()
                        wv = np.linalg.solve(Zt.T @ Zt + L * np.eye(Zt.shape[1]), Zt.T @ (yt[kk] - b0))
                        errs.append((yt[i] - (b0 + ((Xt[i] - mu) / sd) @ wv)) ** 2)
                    if (e := float(np.mean(errs))) < be: lam, be = L, e
                mu, sd = Xt.mean(0), Xt.std(0) + 1e-9; Zt = (Xt - mu) / sd; b0 = yt.mean()
                wv = np.linalg.solve(Zt.T @ Zt + lam * np.eye(Zt.shape[1]), Zt.T @ (yt - b0))
                for k in test:
                    fits[k] = (mu, sd, b0, wv)
            return fits

        for c in list(D["targets"]):
            t = D["targets"][c]; coh = D["cohorts"][c]
            for seed in CV_SEEDS:
                anch = B["anchors"][c][str(seed)]
                fits = fit_item(c, t, seed)
                nat, cohv = {}, {}
                for k, f in fits.items():
                    if k not in anch or k not in cmask: continue
                    assert_anchor_oos({"country": k, **anch[k]})
                    mu, sd, b0, wv = f
                    m = cmask[k]
                    latent = ((Xk[m] - mu) / sd) @ wv
                    delta = center_latent(latent)
                    a = anch[k]["anchor"]
                    K, p_i = solve_K(a, delta)
                    nat[k] = {"anchor": a, "hybrid_mean": float(p_i.mean()), "K": float(K),
                              "raw_latent_spread": float(np.std(delta)), "abstain": bool(m.sum() < 30)}
                    if k in coh:
                        bnd = band[m]
                        for bi, bname in enumerate(BANDS):
                            if bname in coh[k] and (bnd == bi).sum() >= 30:
                                cohv[f"{k}|{bname}"] = {"e1_dev": float(p_i[bnd == bi].mean())}
                out["national_sanity"].setdefault(c, {}).setdefault(str(ws), {})[str(seed)] = nat
                out["cohort"].setdefault(c, {}).setdefault(str(ws), {})[str(seed)] = cohv
        # joints: per-item K against the MRP marginal (seed 42), agents' binary vectors
        JI = D["joint_items"]
        fitsJ = {c: fit_item(c, D["targets"][c], 42) for c in JI}
        for k in Xc:
            if f"{k}_x" not in Z.files or k not in B["joint"]: continue
            m = cmask[k]; ok = True; cols = []
            for j, c in enumerate(JI):
                if k not in fitsJ[c]: ok = False; break
                mu, sd, b0, wv = fitsJ[c][k]
                delta = center_latent(((Xk[m] - mu) / sd) @ wv)
                a = B["joint"][k]["mrp_marginals"][j]
                K, p_i = solve_K(a, delta)
                import zlib
                rr = np.random.default_rng(zlib.crc32(f"{k}|{c}".encode()))
                cols.append((rr.random(p_i.size) < p_i).astype(np.int8))
            if not ok: continue
            A = np.stack(cols, 1); Xr = Z[f"{k}_x"].astype(np.int8); wt = Z[f"{k}_w"]
            out["joint"].setdefault(k, {})[str(ws)] = {"e1_mrp_anchored_energy": S.energy_distance(A, Xr, None, wt, seed=1), "n_agents": int(A.shape[0])}
        # zero-shot: neighbour weights (dev fit at seed 42 on dev targets) + neighbour's OOS MRP anchor
        for c in D["zeroshot_items"]:
            zb = B["zeroshot"][c]; nb = zb["neighbour"]
            nb_t = {k: {"yes": v["yes"]} for k, v in dev["targets"][nb].items()}
            fits = fit_item(nb, nb_t, 42)
            # AMENDMENT (pre-result, 2026-08-26): the anchored country mean
            # equals the baseline by construction, so task (iv) is scored on
            # the zero-shot items' COHORT CELLS — structure under transfer.
            cells = {}
            coh = D["cohorts"].get(c, {})
            for k, a in zb["anchors"].items():
                if k not in fits or k not in cmask or k not in coh: continue
                assert_anchor_oos({"country": k, **a})
                mu, sd, b0, wv = fits[k]
                m = cmask[k]
                delta = center_latent(((Xk[m] - mu) / sd) @ wv)
                K, p_i = solve_K(a["anchor"], delta)
                bnd = band[m]
                for bi, bname in enumerate(BANDS):
                    if bname in coh[k] and (bnd == bi).sum() >= 30:
                        cells[f"{k}|{bname}"] = {"e1_transfer": float(p_i[bnd == bi].mean()), "anchor": a["anchor"]}
            out["zeroshot"].setdefault(c, {})[str(ws)] = {"neighbour": nb, "cells": cells}
        print(f"world {ws} done {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(os.path.join(OUT, "earth1_confirm_v2.json"), "w"), indent=1)
    print("EARTH1 V2 WRITTEN")


def run_score():
    """ONE-SHOT confirmation scoring. Leakage guard on every row;
    compression trace per published row; gates per prereg §3."""
    D = json.load(open(os.path.join(OUT, "confirm_targets_v2.json")))
    B = json.load(open(os.path.join(OUT, "baselines_confirm_v2.json")))
    E = json.load(open(os.path.join(OUT, "earth1_confirm_v2.json")))
    sb = {"stamp": stamp({"prereg": "BENCHMARK_A_PREREG_v2.md@509a1ce+8e8e121"}), "tasks": {}, "compression_trace_summary": {}}
    # (i) sanity: anchor inheritance
    errs = []
    for c, per_ws in E["national_sanity"].items():
        for ws, per_seed in per_ws.items():
            for seed, nat in per_seed.items():
                for k, r in nat.items():
                    assert_anchor_oos({"country": k, **B["anchors"][c][seed][k]})
                    errs.append(abs(r["hybrid_mean"] - r["anchor"]))
    sb["tasks"]["i_sanity"] = {"n_cells": len(errs), "max_abs_inheritance_error": float(max(errs)), "gate": bool(max(errs) <= 1e-8),
                               "note": "no incremental credit; the level is MRP's"}
    # (ii) cohorts
    arms = {"national_copy": [], "global_gradient": [], "cohort_mrp": [], "e1": []}
    grad = {a: [[], [], [], []] for a in arms}
    for c in D["targets"]:
        for seed in map(str, CV_SEEDS):
            bc = B["cohort"].get(c, {}).get(seed, {})
            for ws in E["cohort"].get(c, {}):
                ec = E["cohort"][c][ws].get(seed, {})
                for k, bands in bc.items():
                    for bname, b in bands.items():
                        cell = f"{k}|{bname}"
                        if cell not in ec or "cohort_mrp" not in b: continue
                        assert_anchor_oos({"country": k, **B["anchors"][c][seed][k]})
                        for a, pv in (("national_copy", b["national_copy"]), ("global_gradient", b["global_gradient"]),
                                      ("cohort_mrp", b["cohort_mrp"]), ("e1", ec[cell]["e1_dev"])):
                            arms[a].append(abs(pv - b["truth"]))
                            grad[a][0].append(pv); grad[a][1].append(b["truth"]); grad[a][2].append(b["national_copy"]); grad[a][3].append(b["truth_national"])
    cm = {a: float(np.mean(v)) * 100 for a, v in arms.items()}
    gd = {a: S.gradient_direction_pct(*g) for a, g in grad.items()}
    strongest = min(("national_copy", "global_gradient", "cohort_mrp"), key=lambda a: cm[a])
    rr = S.relative_reduction(cm["e1"], cm[strongest])
    ci = S.paired_bootstrap_diff_ci(np.array(arms[strongest]), np.array(arms["e1"]))
    sb["tasks"]["ii_cohorts"] = {"mae_pp": cm, "gradient_direction_pct": gd, "strongest_baseline": strongest,
        "relative_reduction": rr, "strongest_minus_e1_ci_pp": [x * 100 for x in ci], "n_cells": len(arms["e1"]),
        "gate": bool(rr >= 0.10 and gd["e1"] >= 75.0), "gate_rule": ">=10% rel reduction vs strongest AND >=75% gradient"}
    # (iii) joints (MRP-anchored marginals both arms)
    rows = []
    for k, b in B["joint"].items():
        if k in E["joint"]:
            e_ = float(np.mean([v["e1_mrp_anchored_energy"] for v in E["joint"][k].values()]))
            rows.append((k, b["independent_mrp_energy"], e_))
    ind = np.array([r[1] for r in rows]); e1 = np.array([r[2] for r in rows])
    ci3 = S.paired_bootstrap_diff_ci(ind, e1)
    sb["tasks"]["iii_joints"] = {"n_countries": len(rows), "median_energy": {"independent_mrp": float(np.median(ind)), "e1_mrp_anchored": float(np.median(e1))},
        "independent_minus_e1_ci": ci3, "per_country": rows,
        "gate": bool(np.median(e1) < np.median(ind) and ci3[1] > 0), "gate_rule": "lower energy, median, paired CI excluding 0"}
    # (iv) zero-shot cohort cells
    zarms = {"national_copy": [], "neighbour_offset": [], "e1_transfer": []}
    dev = json.load(open(os.path.join(OUT, "targets_v1.json")))
    for c in D["zeroshot_items"]:
        zb = B["zeroshot"][c]; nb = zb["neighbour"]; coh = D["cohorts"].get(c, {})
        nb_coh = dev["cohorts"].get(nb, {}); nb_t = dev["targets"].get(nb, {})
        offs = {b: float(np.mean([nb_coh[k][b]["yes"] - nb_t[k]["yes"] for k in nb_coh if b in nb_coh[k] and k in nb_t] or [0.0])) for b in BANDS}
        for ws in E["zeroshot"].get(c, {}):
            for cell, r in E["zeroshot"][c][ws]["cells"].items():
                k, bname = cell.split("|")
                truth = coh.get(k, {}).get(bname, {}).get("yes")
                if truth is None: continue
                assert_anchor_oos({"country": k, **zb["anchors"][k]})
                a = r["anchor"]
                zarms["national_copy"].append(abs(a - truth))
                zarms["neighbour_offset"].append(abs(float(np.clip(a + offs[bname], 0, 1)) - truth))
                zarms["e1_transfer"].append(abs(r["e1_transfer"] - truth))
    zm = {a: float(np.mean(v)) * 100 for a, v in zarms.items()}
    zstrong = min(("national_copy", "neighbour_offset"), key=lambda a: zm[a])
    ci4 = S.paired_bootstrap_diff_ci(np.array(zarms[zstrong]), np.array(zarms["e1_transfer"]))
    sb["tasks"]["iv_zeroshot_cohorts"] = {"mae_pp": zm, "strongest_baseline": zstrong, "n_cells": len(zarms["e1_transfer"]),
        "strongest_minus_e1_ci_pp": [x * 100 for x in ci4],
        "gate": bool(zm["e1_transfer"] < zm[zstrong] and ci4[1] > 0), "gate_rule": "beat strongest transfer baseline, paired CI excluding 0"}
    sb["tasks"]["v_cross_wave"] = {"status": "BLOCKED-ON-DATA", "gate": None}
    # compression trace summary: spread by stage (national cells)
    spreads = {"raw_latent_spread": [], "published_spread": []}
    for c, per_ws in E["national_sanity"].items():
        for ws, per_seed in per_ws.items():
            for seed, nat in per_seed.items():
                for k, r in nat.items():
                    spreads["raw_latent_spread"].append(r["raw_latent_spread"])
                    spreads["published_spread"].append(abs(2 * r["hybrid_mean"] - 1))
    sb["compression_trace_summary"] = {k: float(np.mean(v)) for k, v in spreads.items()}
    json.dump(sb, open(os.path.join(OUT, "scoreboard_confirm_v2.json"), "w"), indent=1)
    for k, v in sb["tasks"].items():
        print(k, "GATE", v.get("gate"), {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items() if a in ("mae_pp", "median_energy", "relative_reduction", "gradient_direction_pct", "max_abs_inheritance_error", "strongest_baseline")})


if __name__ == "__main__":
    {"confirm_targets": run_confirm_targets, "baselines": run_baselines, "earth1": run_earth1, "score": run_score}[sys.argv[1]]()
