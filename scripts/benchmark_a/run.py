"""Benchmark A Phase 2 — ONE runner, frozen protocol (BENCHMARK_A_PREREG_v1.md).
Stage 'baselines' runs every baseline through the frozen scorer and writes
data/benchmark_a/baselines_v1.json BEFORE any Earth-1 readout exists.
Stage 'earth1' builds Epoch-3-physics lab worlds and computes the Earth-1
arms on the identical folds. Stage 'score' produces the scoreboard.
"""
import hashlib, json, os, subprocess, sys, time
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
from earth1.benchmark_a import scoring as S
from earth1.rng import logit, sigmoid
OUT = os.path.join(ROOT, "data", "benchmark_a"); os.makedirs(OUT, exist_ok=True)
DATA = json.load(open(os.path.join(OUT, "targets_v1.json")))
JOINTS_NPZ = os.environ.get("BA_JOINTS", "/opt/earth1-data/benchmark_a/joint_vectors_v1.npz")
FOLDS, CV_SEEDS, POP, DAYS = 5, (42, 7, 13), 200_000, 60
WORLD_SEEDS = (42, 20260901, 20260902)
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0)
BANDS = ("18-29", "30-49", "50+")
GOQA = [c for c, it in DATA["items"].items() if it["set"] == "goqa"]
NEWQ = [c for c, it in DATA["items"].items() if it["set"] == "new"]
JOINT_ITEMS = DATA["manifest"]["joint_items"]


def stamp(extra=None):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return {"commit": sha, "scoring_sha256": S.sha256_of_file(os.path.join(ROOT, "earth1/benchmark_a/scoring.py")),
            "targets_sha256": S.sha256_of_file(os.path.join(OUT, "targets_v1.json")), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **(extra or {})}


def folds_for(codes, seed):
    order = np.random.default_rng(seed).permutation(len(codes))
    return [[codes[i] for i in order[f::FOLDS]] for f in range(FOLDS)]


def ridge_fit(Xt, yt, lam):
    mu, sd = Xt.mean(0), Xt.std(0) + 1e-9; Zt = (Xt - mu) / sd; b0 = yt.mean()
    w = np.linalg.solve(Zt.T @ Zt + lam * np.eye(Zt.shape[1]), Zt.T @ (yt - b0))
    return mu, sd, b0, w


def ridge_select(Xt, yt):
    """inner leave-one-country-out on TRAIN only (prereg §2)."""
    best, be = LAMBDAS[0], np.inf
    for lam in LAMBDAS:
        errs = []
        for i in range(len(yt)):
            k = np.arange(len(yt)) != i
            mu, sd, b0, w = ridge_fit(Xt[k], yt[k], lam)
            errs.append((yt[i] - (b0 + ((Xt[i] - mu) / sd) @ w)) ** 2)
        e = float(np.mean(errs))
        if e < be: best, be = lam, e
    return best


# ── baselines ─────────────────────────────────────────────────────
def run_baselines():
    from earth1.alive import birth_world
    from mrp_baseline import build_context, fit_mrsp, LAMBDAS as ML, TAUS
    from earth1.calibration import _get_country_index
    w = birth_world(POP, 42); civ = w.civ
    c2i, codes = _get_country_index(civ)
    ctx, cells, usable = build_context(civ, codes)
    res = {"protocol": {"folds": FOLDS, "cv_seeds": CV_SEEDS}, "national": {}, "cohort": {}, "joint": {}, "newq": {}, "stamp": stamp()}
    mrp_pred = {}      # (item, seed) -> {country: pred}
    for c in GOQA + NEWQ:
        t = DATA["targets"][c]; cs = sorted(k for k in t if k in ctx and k in cells)
        y = {k: t[k]["yes"] for k in cs}
        for seed in CV_SEEDS:
            preds_m, preds_n = {}, {}
            for test in folds_for(cs, seed):
                train = [k for k in cs if k not in set(test)]
                g = float(np.mean([y[k] for k in train])); bl = logit(np.array([g]))[0]
                Xtr = np.array([ctx[k] for k in train]); ytr = np.array([logit(np.array([y[k]]))[0] - bl for k in train])
                mu, sd = Xtr.mean(0), Xtr.std(0); sd = np.where(sd > 1e-9, sd, 1.0); Xs = (Xtr - mu) / sd
                best, be = (ML[0], TAUS[0]), np.inf
                for lam in ML:
                    for tau in TAUS:
                        errs = []
                        for i in range(len(train)):
                            k = np.arange(len(train)) != i
                            b = fit_mrsp(Xs[k], ytr[k], lam, tau); errs.append((ytr[i] - (b[0] + Xs[i] @ b[1:])) ** 2)
                        e = float(np.mean(errs))
                        if e < be: best, be = (lam, tau), e
                beta = fit_mrsp(Xs, ytr, *best)
                for k in test:
                    x = (ctx[k] - mu) / sd; lin = beta[0] + x @ beta[1:]
                    preds_m[k] = float(np.sum(cells[k] * sigmoid(np.full(len(cells[k]), bl + lin)))); preds_n[k] = g
            mrp_pred[(c, seed)] = preds_m
            res["national"].setdefault(c, {})[str(seed)] = {"mrp": preds_m, "naive": preds_n, "truth": y}
    # cohort baselines: national-copy and global-gradient (train-fold mean offset per item/band)
    for c in GOQA:
        coh = DATA["cohorts"][c]
        for seed in CV_SEEDS:
            cs = sorted(k for k in DATA["targets"][c] if k in ctx and k in cells)
            out = {}
            for test in folds_for(cs, seed):
                train = [k for k in cs if k not in set(test)]
                off = {b: float(np.mean([coh[k][b]["yes"] - DATA["targets"][c][k]["yes"] for k in train if k in coh and b in coh[k]] or [0.0])) for b in BANDS}
                for k in test:
                    if k not in coh: continue
                    m = mrp_pred[(c, seed)][k]
                    for b, v in coh[k].items():
                        out[f"{k}|{b}"] = {"truth": v["yes"], "national_copy": m, "global_gradient": float(np.clip(m + off[b], 0, 1)), "mrp_national": m, "truth_national": DATA["targets"][c][k]["yes"]}
            res["cohort"].setdefault(c, {})[str(seed)] = out
    # joint baseline: independent-marginal synthetic population vs respondents
    Z = np.load(JOINTS_NPZ); rng = np.random.default_rng(0)
    for iso in sorted(k[:-2] for k in Z.files if k.endswith("_x")):
        X = Z[f"{iso}_x"].astype(np.int8); wt = Z[f"{iso}_w"]
        if X.shape[0] < 100: continue
        p = (wt[:, None] * X).sum(0) / wt.sum()
        synth = (rng.random((X.shape[0], X.shape[1])) < p[None, :]).astype(np.int8)
        res["joint"][iso] = {"n": int(X.shape[0]), "marginals": [float(v) for v in p], "independent_marginal_energy": S.energy_distance(synth, X, None, wt, seed=1)}
    # new-question semantic-neighbour baseline: hashed TF-IDF cosine over question text
    from earth1.embedder import embed
    texts = {c: DATA["items"][c]["text"] for c in GOQA + NEWQ}
    E = embed([texts[c] for c in GOQA + NEWQ]); E = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
    idx = {c: i for i, c in enumerate(GOQA + NEWQ)}
    for c in NEWQ:
        sims = [(float(E[idx[c]] @ E[idx[g]]), g) for g in GOQA]; sim, nb = max(sims)
        t = DATA["targets"][c]; tn = DATA["targets"][nb]
        res["newq"][c] = {"neighbour": nb, "cosine": sim, "semantic_neighbour_pred": {k: tn[k]["yes"] for k in t if k in tn}, "truth": {k: t[k]["yes"] for k in t}}
    json.dump(res, open(os.path.join(OUT, "baselines_v1.json"), "w"), indent=1)
    print("BASELINES WRITTEN", os.path.join(OUT, "baselines_v1.json"))


# ── Earth-1 arms ──────────────────────────────────────────────────
def run_earth1():
    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.calibration import living_features, _get_country_index
    from earth1.persistence import world_hash
    from earth1.genesis import GENESIS_COUNTRY_CODES
    base = json.load(open(os.path.join(OUT, "baselines_v1.json")))
    Z = np.load(JOINTS_NPZ)
    out = {"worlds": {}, "national": {}, "cohort": {}, "joint": {}, "newq": {}, "stamp": stamp({"physics_version": PHYSICS_VERSION})}
    for ws in WORLD_SEEDS:
        t0 = time.time(); w = birth_world(POP, ws); rng = np.random.default_rng(ws)
        for _ in range(DAYS): live_one_day(w, rng)
        X = living_features(w); civ = w.civ; alive = w.health.alive
        c2i, codes = _get_country_index(civ)
        years = 18.0 + civ.age * 72.0
        band = np.where(years < 30, 0, np.where(years < 50, 1, 2))
        out["worlds"][str(ws)] = {"world_hash": world_hash(w), "world_day": int(w.day), "alive": int(alive.sum()), "seconds": round(time.time() - t0, 1)}
        cmask = {k: (civ.country == c2i[k]) & alive for k in codes if k in c2i}
        Xc = {k: X[m].mean(0) for k, m in cmask.items() if m.sum() >= 30}
        fitted = {}   # (item, seed, country) -> (mu,sd,b0,w,bl)
        for c in GOQA:
            t = DATA["targets"][c]; cs = sorted(k for k in t if k in Xc); y = {k: t[k]["yes"] for k in cs}
            for seed in CV_SEEDS:
                pn, ph = {}, {}
                mrp = base["national"][c][str(seed)]["mrp"]
                for test in folds_for(cs, seed):
                    train = [k for k in cs if k not in set(test)]
                    Xt = np.array([Xc[k] for k in train]); yt = logit(np.clip(np.array([y[k] for k in train]), 0.02, 0.98))
                    lam = ridge_select(Xt, yt); mu, sd, b0, wv = ridge_fit(Xt, yt, lam)
                    for k in test:
                        z = (X[cmask[k]] - mu) / sd; s_i = sigmoid(b0 + z @ wv)
                        pn[k] = float(s_i.mean())
                        if k in mrp:   # hybrid: MRP national level + Earth-1 within-country structure
                            zc = z - z.mean(0); ph[k] = float(sigmoid(logit(np.array([np.clip(mrp[k], 0.02, 0.98)]))[0] + zc @ wv).mean())
                        fitted[(c, seed, k)] = (mu, sd, b0, wv)
                out["national"].setdefault(c, {}).setdefault(str(ws), {})[str(seed)] = {"e1_national": pn, "e1_hybrid": ph}
        # cohorts
        for c in GOQA:
            coh = DATA["cohorts"][c]
            for seed in CV_SEEDS:
                cells = {}
                for (cc, sd_, k), (mu, sd, b0, wv) in fitted.items():
                    if cc != c or sd_ != seed or k not in coh: continue
                    m = cmask[k]; z = (X[m] - mu) / sd; s_i = sigmoid(b0 + z @ wv); bnd = band[m]
                    mrp = base["national"][c][str(seed)]["mrp"].get(k)
                    zc = z - z.mean(0); s_h = sigmoid(logit(np.array([np.clip(mrp, 0.02, 0.98)]))[0] + zc @ wv) if mrp is not None else None
                    for bi, bname in enumerate(BANDS):
                        if bname in coh[k] and (bnd == bi).sum() >= 30:
                            cells[f"{k}|{bname}"] = {"e1": float(s_i[bnd == bi].mean()), "e1_hybrid": (float(s_h[bnd == bi].mean()) if s_h is not None else None), "e1_national": float(s_i.mean())}
                out["cohort"].setdefault(c, {}).setdefault(str(ws), {})[str(seed)] = cells
        # joints (seed 42 folds: each country held out once)
        for k in Xc:
            if f"{k}_x" not in Z.files or all((c, 42, k) not in fitted for c in JOINT_ITEMS): continue
            m = cmask[k]; Xr = Z[f"{k}_x"].astype(np.int8); wt = Z[f"{k}_w"]
            if Xr.shape[0] < 100: continue
            cols, cols_m = [], []
            p = (wt[:, None] * Xr).sum(0) / wt.sum()
            for j, c in enumerate(JOINT_ITEMS):
                if (c, 42, k) not in fitted: cols = None; break
                mu, sd, b0, wv = fitted[(c, 42, k)]; s_i = sigmoid(b0 + ((X[m] - mu) / sd) @ wv)
                cols.append((s_i >= 0.5).astype(np.int8))
                # marginal-matched threshold; q clipped (harness repair
                # 2026-08-24: one country produced q epsilon-outside [0,1])
                q = float(np.clip(1.0 - p[j], 0.0, 1.0))
                if not np.isfinite(q): cols = None; break
                thr = np.quantile(s_i, q); cols_m.append((s_i >= thr).astype(np.int8))
            if cols is None: continue
            A = np.stack(cols, 1); Am = np.stack(cols_m, 1)
            out["joint"].setdefault(k, {})[str(ws)] = {"e1_energy": S.energy_distance(A, Xr, None, wt, seed=1), "e1_marginal_matched_energy": S.energy_distance(Am, Xr, None, wt, seed=1), "n_agents": int(A.shape[0])}
        # new questions: weights transferred from the semantic neighbour (never fitted on the new item's targets)
        for c in NEWQ:
            nb = base["newq"][c]["neighbour"]; t = DATA["targets"][c]; pred = {}
            for k in t:
                if (nb, 42, k) in fitted and k in cmask:
                    mu, sd, b0, wv = fitted[(nb, 42, k)]; pred[k] = float(sigmoid(b0 + ((X[cmask[k]] - mu) / sd) @ wv).mean())
            out["newq"].setdefault(c, {})[str(ws)] = {"neighbour": nb, "e1_transfer_pred": pred}
        print(f"world {ws} done in {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(os.path.join(OUT, "earth1_v1.json"), "w"), indent=1)
    print("EARTH1 WRITTEN")


# ── scoring ───────────────────────────────────────────────────────
def run_score():
    base = json.load(open(os.path.join(OUT, "baselines_v1.json"))); e1 = json.load(open(os.path.join(OUT, "earth1_v1.json")))
    sb = {"stamp": stamp(), "tasks": {}}
    # (i) national: per-item MAE averaged over seeds; Earth-1 averaged over worlds
    per_item = {"mrp": [], "naive": [], "e1_national": [], "e1_hybrid": []}
    for c in GOQA:
        for arm in ("mrp", "naive"):
            per_item[arm].append(np.mean([S.mae_pp([base["national"][c][s][arm][k] for k in base["national"][c][s]["truth"] if k in base["national"][c][s][arm]],
                                                    [base["national"][c][s]["truth"][k] for k in base["national"][c][s]["truth"] if k in base["national"][c][s][arm]]) for s in map(str, CV_SEEDS)]))
        for arm in ("e1_national", "e1_hybrid"):
            vals = []
            for ws in e1["national"][c]:
                for s in map(str, CV_SEEDS):
                    pr = e1["national"][c][ws][s][arm]; tr = base["national"][c][s]["truth"]; ks = [k for k in pr if k in tr]
                    if ks: vals.append(S.mae_pp([pr[k] for k in ks], [tr[k] for k in ks]))
            per_item[arm].append(float(np.mean(vals)))
    mae = {a: float(np.mean(v)) for a, v in per_item.items()}
    d_hyb = S.paired_bootstrap_diff_ci(per_item["mrp"], per_item["e1_hybrid"])
    sb["tasks"]["i_country_means"] = {"mae_pp": mae, "per_item": per_item, "excess_e1_over_mrp_pp": mae["e1_national"] - mae["mrp"],
        "hybrid_gain_over_mrp_pp_ci": d_hyb, "gate": bool(mae["e1_national"] - mae["mrp"] <= 0.5 or (d_hyb[1] > 0)),
        "gate_rule": "E1 national non-inferior to MRP (<=0.5pp excess) OR hybrid gain CI excludes 0"}
    # (ii) cohorts
    arms = {"national_copy": [], "global_gradient": [], "e1": [], "e1_hybrid": []}; grad = {"national_copy": [[], [], [], []], "global_gradient": [[], [], [], []], "e1": [[], [], [], []], "e1_hybrid": [[], [], [], []]}
    for c in GOQA:
        for s in map(str, CV_SEEDS):
            bc = base["cohort"][c][s]
            for ws in e1["cohort"][c]:
                ec = e1["cohort"][c][ws][s]
                for cell, b in bc.items():
                    if cell not in ec or ec[cell]["e1_hybrid"] is None: continue
                    arms["national_copy"].append(abs(b["national_copy"] - b["truth"])); arms["global_gradient"].append(abs(b["global_gradient"] - b["truth"]))
                    arms["e1"].append(abs(ec[cell]["e1"] - b["truth"])); arms["e1_hybrid"].append(abs(ec[cell]["e1_hybrid"] - b["truth"]))
                    for a, pv, pr in (("national_copy", b["national_copy"], b["mrp_national"]), ("global_gradient", b["global_gradient"], b["mrp_national"]), ("e1", ec[cell]["e1"], ec[cell]["e1_national"]), ("e1_hybrid", ec[cell]["e1_hybrid"], b["mrp_national"])):
                        grad[a][0].append(pv); grad[a][1].append(b["truth"]); grad[a][2].append(pr); grad[a][3].append(b["truth_national"])
    cm = {a: float(np.mean(v)) * 100 for a, v in arms.items()}
    gd = {a: S.gradient_direction_pct(*g) for a, g in grad.items()}
    strongest = min(("national_copy", "global_gradient"), key=lambda a: cm[a]); best_e1 = min(("e1", "e1_hybrid"), key=lambda a: cm[a])
    rr = S.relative_reduction(cm[best_e1], cm[strongest])
    sb["tasks"]["ii_cohort_cells"] = {"mae_pp": cm, "gradient_direction_pct": gd, "strongest_baseline": strongest, "best_e1_arm": best_e1, "relative_reduction": rr,
        "n_cells": len(arms["e1"]), "gate": bool(rr >= 0.10 and gd[best_e1] >= 75.0), "gate_rule": ">=10% relative MAE reduction vs strongest baseline AND >=75% gradient direction"}
    # (iii) joints
    rows = []
    for k, b in base["joint"].items():
        if k in e1["joint"]:
            e_raw = np.mean([v["e1_energy"] for v in e1["joint"][k].values()]); e_mm = np.mean([v["e1_marginal_matched_energy"] for v in e1["joint"][k].values()])
            rows.append((k, b["independent_marginal_energy"], e_raw, e_mm))
    ind = np.array([r[1] for r in rows]); raw = np.array([r[2] for r in rows]); mm = np.array([r[3] for r in rows])
    ci_raw = S.paired_bootstrap_diff_ci(ind, raw); ci_mm = S.paired_bootstrap_diff_ci(ind, mm)
    sb["tasks"]["iii_joint_distributions"] = {"n_countries": len(rows), "median_energy": {"independent_marginal": float(np.median(ind)), "e1_raw": float(np.median(raw)), "e1_marginal_matched": float(np.median(mm))},
        "independent_minus_e1_raw_ci": ci_raw, "independent_minus_e1_marginal_matched_ci": ci_mm, "per_country": rows,
        "gate": bool(np.median(raw) < np.median(ind) and ci_raw[1] > 0), "gate_secondary_marginal_matched": bool(np.median(mm) < np.median(ind) and ci_mm[1] > 0),
        "gate_rule": "E1 energy distance lower than independent-marginal population, median over countries, paired CI excluding 0"}
    # (iv) new questions
    nq = {}
    sn, et = [], []
    for c in NEWQ:
        b = base["newq"][c]; tr = b["truth"]; ks = [k for k in b["semantic_neighbour_pred"] if k in tr]
        m_sn = S.mae_pp([b["semantic_neighbour_pred"][k] for k in ks], [tr[k] for k in ks])
        m_e1 = float(np.mean([S.mae_pp([v["e1_transfer_pred"][k] for k in ks if k in v["e1_transfer_pred"]], [tr[k] for k in ks if k in v["e1_transfer_pred"]]) for v in e1["newq"][c].values()]))
        nq[c] = {"neighbour": b["neighbour"], "semantic_neighbour_mae_pp": m_sn, "e1_transfer_mae_pp": m_e1, "n_countries": len(ks)}; sn.append(m_sn); et.append(m_e1)
    ci = S.paired_bootstrap_diff_ci(sn, et)
    sb["tasks"]["iv_heldout_questions"] = {"per_question": nq, "mae_pp": {"semantic_neighbour": float(np.mean(sn)), "e1_transfer": float(np.mean(et)), "llm": "NOT RUN (awaiting authorization)"},
        "semantic_minus_e1_ci": ci, "gate": bool(np.mean(et) < np.mean(sn) and ci[1] > 0), "gate_rule": "beat the semantic-neighbour/LLM baseline, paired CI excluding 0"}
    sb["tasks"]["v_cross_wave"] = {"status": "BLOCKED-ON-DATA (WVS/EVS Trend file not in estate)", "gate": None}
    json.dump(sb, open(os.path.join(OUT, "scoreboard_v1.json"), "w"), indent=1)
    for k, v in sb["tasks"].items(): print(k, "GATE", v.get("gate"), {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items() if a in ("mae_pp", "median_energy", "relative_reduction", "gradient_direction_pct", "excess_e1_over_mrp_pp", "hybrid_gain_over_mrp_pp_ci")})


if __name__ == "__main__":
    {"baselines": run_baselines, "earth1": run_earth1, "score": run_score}[sys.argv[1]]()
