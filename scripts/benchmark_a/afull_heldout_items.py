"""A-FULL-1 task (iv) — held-out-items harness.

Protocol (campaign A-FULL-1, measurement only):
  Within the WVS confirmation estate (confirm_targets_v2.json, 98 items),
  fit the readout on a random 70% of items (numpy default_rng seed
  20260831; the split item lists are recorded in the output), score the
  untouched 30%. Two arms, scored on the SAME (item, country) pairs:

    e1        — Earth-1 readout transfer: each held-out item is mapped to
                its nearest FIT item by the similarity representation
                below; that neighbour's per-item ridge readout (the exact
                run_v2 fit_item recipe: country-holdout folds, inner-LOO
                lambda, logit targets clipped to [0.02, 0.98]) is fitted
                on the neighbour's OWN targets over candidate-world
                country-mean living features, and its per-country
                out-of-fold fit predicts the held-out item's national
                share for that country. UNANCHORED by design: an
                MRP-anchored country mean equals the anchor by
                construction (zero credit), so the national-level readout
                must stand on its own here.
    neighbour — semantic-neighbour baseline: predict the neighbour item's
                observed per-country national share ("copy the
                neighbour's distribution").

  Similarity representation (S3 recommendation; purely local, no external
  model, no network, no LLM): hashed TF-IDF (earth1.corpus._Vectorizer,
  4096 dims, crc32 hashing) with the frozen IDF from
  data/corpus/goqa_seed.json, guarded by the stem-family collision
  cascade (earth1.stem_family): candidates are ranked by
  dampening_factor(cosine, classify_pair(...)), which caps stem
  collisions ("confidence in the press" vs "... in the army") at 0.30
  while non-collision matches cap at 0.60 — so a verbatim-stem collision
  can be out-ranked by a genuinely same-object match. Ties break on raw
  cosine, then item id. If every guarded score is 0 (all cosines <= 0.50)
  the raw-cosine argmax is used and flagged as a fallback.

  Metric: MAE in percentage points (earth1.benchmark_a.scoring.mae_pp)
  on the held-out 30%, pooled over (item, country) pairs and per item,
  plus a paired bootstrap CI over per-item MAE differences
  (neighbour - e1; positive lower bound = e1 better).

Both arms only ever read FIT-item targets during fitting/selection; the
held-out items' targets are touched exclusively in the scoring section.
The selftest proves both properties on synthetic data (including a
tamper test: perturbing held-out targets must not change any prediction,
and a negative control proving the neighbour check fails for a random
picker).

Usage (on prime, inside /opt/earth1, candidate flag env exported first):
  export EARTH1_AFULL_OUT=/opt/earth1-data/afull1
  .venv/bin/python scripts/benchmark_a/afull_heldout_items.py
Local selftest (no world, no data files needed):
  python3 scripts/benchmark_a/afull_heldout_items.py --selftest

Writes $EARTH1_AFULL_OUT/heldout_items.json. Never writes into
data/benchmark_a or /opt/earth1-data/benchmark_a (guarded).
"""
import argparse
import json
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_v2  # frozen A-v2 harness: folds_for, LAMBDAS, _feature_treatment, stamp
from earth1.benchmark_a import scoring as S
from earth1.corpus import _Vectorizer
from earth1.rng import logit, sigmoid
from earth1.stem_family import classify_pair, dampening_factor

SPLIT_SEED = 20260831
SPLIT_FRAC = 0.70
CV_SEED = 42          # matches the run_v2 zeroshot precedent (dev fit at seed 42)
FROZEN_DIRS = (
    os.path.abspath(os.path.join(ROOT, "data", "benchmark_a")),
    "/opt/earth1-data/benchmark_a",
    "/opt/earth1-data/av2_c2plus",
)

_QRE = re.compile(r"^Q(\d+)$")


def _qkey(item_id):
    m = _QRE.match(item_id)
    return (0, int(m.group(1)), item_id) if m else (1, 0, item_id)


# ── split ──────────────────────────────────────────────────────────────
def split_items(ids, seed=SPLIT_SEED, frac=SPLIT_FRAC):
    """Deterministic 70/30 item split. Input order never matters: the
    permutation runs over the canonically sorted id list."""
    ids = sorted(set(ids), key=_qkey)
    order = np.random.default_rng(seed).permutation(len(ids))
    n_fit = int(round(frac * len(ids)))
    fit = sorted((ids[i] for i in order[:n_fit]), key=_qkey)
    held = sorted((ids[i] for i in order[n_fit:]), key=_qkey)
    return fit, held


# ── semantic neighbour (similarity-guarded) ────────────────────────────
def select_neighbour(held_text, fit_ids, fit_texts, vec, fit_vecs):
    """Nearest calibrated item under guarded hashed-TF-IDF similarity."""
    qv = vec.embed(held_text)
    rows = []
    for fid in fit_ids:
        sim = float(fit_vecs[fid] @ qv)
        cls = classify_pair(held_text, fit_texts[fid])
        rows.append((fid, sim, cls, float(dampening_factor(sim, cls))))
    best = sorted(rows, key=lambda r: (-r[3], -r[1], _qkey(r[0])))[0]
    fallback = False
    if best[3] <= 0.0:  # nothing clears the similarity floor: raw cosine
        best = sorted(rows, key=lambda r: (-r[1], _qkey(r[0])))[0]
        fallback = True
    return {"neighbour": best[0], "cosine": round(best[1], 6),
            "stem_class": best[2], "guarded_score": round(best[3], 6),
            "fallback": fallback}


def neighbour_map(held_ids, held_texts, fit_ids, fit_texts, vec):
    fit_vecs = {i: vec.embed(fit_texts[i]) for i in fit_ids}
    return {h: select_neighbour(held_texts[h], fit_ids, fit_texts, vec, fit_vecs)
            for h in held_ids}


# ── readout fit: verbatim port of run_v2.run_earth1's fit_item closure ─
def fit_item_ridge(Xc, keep, targets, seed):
    """Ridge on TRAIN countries (lambda by inner LOO); returns per-country
    out-of-fold (mu, sd, b0, wv). Identical recipe to run_v2 fit_item;
    Xc/keep passed in instead of closed over."""
    cs = sorted(k for k in targets if k in Xc)
    y = {k: targets[k]["yes"] for k in cs}
    fits = {}
    for test in run_v2.folds_for(cs, seed):
        train = [k for k in cs if k not in set(test)]
        if len(train) < 8:
            continue
        Xt = np.array([np.asarray(Xc[k])[keep] for k in train])
        yt = logit(np.clip(np.array([y[k] for k in train]), 0.02, 0.98))
        lam, be = run_v2.LAMBDAS[0], np.inf
        for L in run_v2.LAMBDAS:
            errs = []
            for i in range(len(yt)):
                kk = np.arange(len(yt)) != i
                mu, sd = Xt[kk].mean(0), Xt[kk].std(0) + 1e-9
                Zt = (Xt[kk] - mu) / sd
                b0 = yt[kk].mean()
                wv = np.linalg.solve(Zt.T @ Zt + L * np.eye(Zt.shape[1]), Zt.T @ (yt[kk] - b0))
                errs.append((yt[i] - (b0 + ((Xt[i] - mu) / sd) @ wv)) ** 2)
            if (e := float(np.mean(errs))) < be:
                lam, be = L, e
        mu, sd = Xt.mean(0), Xt.std(0) + 1e-9
        Zt = (Xt - mu) / sd
        b0 = yt.mean()
        wv = np.linalg.solve(Zt.T @ Zt + lam * np.eye(Zt.shape[1]), Zt.T @ (yt - b0))
        for k in test:
            fits[k] = (mu, sd, b0, wv)
    return fits


def _predict(fits, Xc, keep):
    out = {}
    for k, (mu, sd, b0, wv) in fits.items():
        lin = b0 + ((np.asarray(Xc[k])[keep] - mu) / sd) @ wv
        out[k] = float(sigmoid(np.array([lin]))[0])
    return out


# ── harness core (pure over its inputs; selftest runs it synthetically) ─
def run_harness_core(texts, targets, Xc_by_world, keep, vec,
                     split_seed=SPLIT_SEED, frac=SPLIT_FRAC, cv_seed=CV_SEED,
                     split_override=None):
    """texts: {item: text}; targets: {item: {iso2: {'yes': float, ...}}};
    Xc_by_world: {world_seed: {iso2: feature_vector}}; keep: kept column
    indices; vec: fitted _Vectorizer. Returns the result dict."""
    ids = sorted(texts, key=_qkey)
    if split_override is None:
        fit_items, held_items = split_items(ids, split_seed, frac)
    else:
        fit_items = sorted(split_override[0], key=_qkey)
        held_items = sorted(split_override[1], key=_qkey)
    fset, hset = set(fit_items), set(held_items)
    if fset & hset:
        raise AssertionError(f"split leak: fit and held-out overlap: {sorted(fset & hset)}")
    if fset | hset != set(ids):
        raise AssertionError("split must cover every item exactly once")

    # ── FITTING/SELECTION PHASE: only fit-item targets exist here ──────
    fit_targets = {i: {k: {"yes": float(v["yes"])} for k, v in targets[i].items()}
                   for i in fit_items}
    nb = neighbour_map(held_items, {h: texts[h] for h in held_items},
                       fit_items, {i: texts[i] for i in fit_items}, vec)
    preds_e1 = {}
    for ws, Xc in Xc_by_world.items():
        cache = {}
        preds_e1[ws] = {}
        for h in held_items:
            n = nb[h]["neighbour"]
            if n not in cache:
                cache[n] = fit_item_ridge(Xc, keep, fit_targets[n], cv_seed)
            preds_e1[ws][h] = _predict(cache[n], Xc, keep)

    # ── SCORING PHASE: the only place held-out targets are read ────────
    ws_keys = list(Xc_by_world)
    per_item, pairs, all_rows = {}, {}, []
    for h in held_items:
        n = nb[h]["neighbour"]
        ks = set(targets[h])
        for ws in ws_keys:
            ks &= set(preds_e1[ws][h])
        ks = sorted(ks)
        rows = {}
        for k in ks:
            e1w = {str(ws): round(preds_e1[ws][h][k], 6) for ws in ws_keys}
            e1m = float(np.mean([preds_e1[ws][h][k] for ws in ws_keys]))
            base = float(fit_targets[n][k]["yes"])
            t = float(targets[h][k]["yes"])
            rows[k] = {"truth": t, "neighbour_copy": base,
                       "e1": e1w, "e1_mean": round(e1m, 6)}
            all_rows.append((h, k, t, base, {str(ws): preds_e1[ws][h][k] for ws in ws_keys}, e1m))
        pairs[h] = rows
        if ks:
            t = [rows[k]["truth"] for k in ks]
            per_item[h] = {"neighbour": n, "n_pairs": len(ks), "mae_pp": {
                "e1": S.mae_pp([float(np.mean([preds_e1[ws][h][k] for ws in ws_keys])) for k in ks], t),
                "e1_by_world": {str(ws): S.mae_pp([preds_e1[ws][h][k] for k in ks], t) for ws in ws_keys},
                "neighbour_copy": S.mae_pp([rows[k]["neighbour_copy"] for k in ks], t)}}
        else:
            per_item[h] = {"neighbour": n, "n_pairs": 0, "mae_pp": None}

    scored = [h for h in held_items if per_item[h]["n_pairs"] > 0]
    e1_item = np.array([per_item[h]["mae_pp"]["e1"] for h in scored])
    nb_item = np.array([per_item[h]["mae_pp"]["neighbour_copy"] for h in scored])
    ci = S.paired_bootstrap_diff_ci(nb_item, e1_item)
    truth_all = [r[2] for r in all_rows]
    headline = {
        "n_items_scored": len(scored),
        "n_items_unscored": len(held_items) - len(scored),
        "n_pairs": len(all_rows),
        "e1_mae_pp": S.mae_pp([r[5] for r in all_rows], truth_all),
        "neighbour_mae_pp": S.mae_pp([r[3] for r in all_rows], truth_all),
        "e1_mae_pp_by_world": {str(ws): S.mae_pp([r[4][str(ws)] for r in all_rows], truth_all)
                               for ws in ws_keys},
        "per_item_mean_mae_pp": {"e1": float(e1_item.mean()) if len(scored) else None,
                                 "neighbour_copy": float(nb_item.mean()) if len(scored) else None},
        "neighbour_minus_e1_per_item_ci_pp": [ci[0], ci[1], ci[2]],
        "e1_beats_neighbour": bool(len(all_rows) and
                                   S.mae_pp([r[5] for r in all_rows], truth_all)
                                   < S.mae_pp([r[3] for r in all_rows], truth_all)),
        "ci_excludes_zero": bool(len(scored) and ci[1] > 0),
    }
    return {"split": {"seed": split_seed, "frac": frac,
                      "override_used": split_override is not None,
                      "n_items": len(ids), "n_fit": len(fit_items),
                      "n_heldout": len(held_items),
                      "fit_items": fit_items, "heldout_items": held_items},
            "cv_seed": cv_seed, "neighbours": nb, "per_item": per_item,
            "pairs": pairs, "headline": headline}


# ── real run ───────────────────────────────────────────────────────────
def run_real(args):
    outdir = os.environ.get("EARTH1_AFULL_OUT")
    if not outdir:
        sys.exit("EARTH1_AFULL_OUT must be set (a fresh dir; frozen artifact dirs are refused)")
    outdir = os.path.abspath(outdir)
    if outdir in FROZEN_DIRS:
        sys.exit(f"refusing to write into frozen artifact dir {outdir}")
    os.makedirs(outdir, exist_ok=True)

    conf_path = os.path.join(ROOT, "data", "benchmark_a", "confirm_targets_v2.json")
    D = json.load(open(conf_path))
    texts = {c: D["items"][c]["text"] for c in D["targets"]}
    targets = D["targets"]

    corpus_path = os.path.join(ROOT, "data", "corpus", "goqa_seed.json")
    seed_corpus = json.load(open(corpus_path))
    vec = _Vectorizer(idf=seed_corpus["idf"])

    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.calibration import living_features, living_feature_names, _get_country_index
    from earth1.persistence import world_hash

    substrate = os.environ.get("EARTH1_SUBSTRATE") or None
    world_seeds = tuple(int(s) for s in args.world_seeds.split(","))
    Xc_by_world, worlds_meta = {}, {}
    keep, feature_report = None, None
    for ws in world_seeds:
        t0 = time.time()
        w = birth_world(args.pop, ws, substrate=substrate)
        rng = np.random.default_rng(ws)
        for _ in range(args.days):
            live_one_day(w, rng)
        X = living_features(w)
        civ, alive = w.civ, w.health.alive
        c2i, codes = _get_country_index(civ)
        cmask = {k: (civ.country == c2i[k]) & alive for k in codes if k in c2i}
        Xc = {k: X[m].mean(0) for k, m in cmask.items() if m.sum() >= 30}
        if keep is None:
            keep, feature_report = run_v2._feature_treatment(
                [Xc[k] for k in sorted(Xc)], living_feature_names(True))
        Xc_by_world[ws] = Xc
        worlds_meta[str(ws)] = {"world_hash": world_hash(w), "world_day": int(w.day),
                                "alive": int(alive.sum()),
                                "seconds": round(time.time() - t0, 1)}
        print(f"world {ws} done {time.time() - t0:.0f}s", flush=True)

    res = run_harness_core(texts, targets, Xc_by_world, keep, vec,
                           split_seed=args.split_seed, frac=SPLIT_FRAC,
                           cv_seed=args.cv_seed)
    deviation = (args.pop != run_v2.POP or args.days != run_v2.DAYS
                 or world_seeds != run_v2.WORLD_SEEDS
                 or args.cv_seed != CV_SEED or args.split_seed != SPLIT_SEED)
    out = {
        "task": "A-FULL-1 (iv) held-out items: 70/30 item split within WVS confirmation estate",
        "stamp": run_v2.stamp({"physics_version": PHYSICS_VERSION, "substrate": substrate,
                               "confirm_targets_sha256": S.sha256_of_file(conf_path),
                               "corpus_idf_sha256": S.sha256_of_file(corpus_path)}),
        "flags_env": {k: os.environ[k] for k in sorted(os.environ) if k.startswith("EARTH1_")},
        "protocol": {
            "split_seed": args.split_seed, "split_frac": SPLIT_FRAC, "cv_seed": args.cv_seed,
            "pop": args.pop, "days": args.days, "world_seeds": list(world_seeds),
            "protocol_deviation": bool(deviation),
            "truth_source": "confirm_targets_v2.json targets[item][iso2].yes (national weighted shares)",
            "similarity": {"representation": "hashed TF-IDF (earth1.corpus._Vectorizer, 4096 dims, crc32)",
                           "idf": "frozen data/corpus/goqa_seed.json idf",
                           "stem_guard": "earth1.stem_family dampening cascade (collision cap 0.30)",
                           "selection": "argmax dampening_factor(cosine, classify_pair); tie -> raw cosine -> item id; raw-cosine fallback if all guarded scores are 0"},
            "e1_arm": "neighbour-transferred run_v2 fit_item ridge (fitted on the neighbour's targets, country-holdout OOS), applied to candidate-world country-mean living features; UNANCHORED at national level",
            "baseline_arm": "copy the neighbour item's observed per-country national share"},
        "feature_report": feature_report, "kept_cols": keep,
        "worlds": worlds_meta,
        **res,
    }
    path = os.path.join(outdir, "heldout_items.json")
    json.dump(out, open(path, "w"), indent=1)
    h = out["headline"]
    print("HELDOUT ITEMS WRITTEN", path)
    print(f"items scored {h['n_items_scored']}/{len(res['split']['heldout_items'])}, "
          f"pairs {h['n_pairs']}; e1 {h['e1_mae_pp']:.3f}pp vs neighbour {h['neighbour_mae_pp']:.3f}pp; "
          f"per-item CI (nb-e1) {h['neighbour_minus_e1_per_item_ci_pp']}")


# ── selftest ───────────────────────────────────────────────────────────
def _synthetic_world(n_countries=12, dim=6, seed=0):
    rng = np.random.default_rng(seed)
    codes = [f"C{i:02d}" for i in range(n_countries)]
    F = rng.normal(0, 1, (n_countries, dim))
    return codes, {k: F[i] for i, k in enumerate(codes)}


def _synthetic_targets(items, codes, Xc, seed=7):
    rng = np.random.default_rng(seed)
    targets = {}
    for it in items:
        wv = rng.normal(0, 0.8, len(next(iter(Xc.values()))))
        b = rng.normal(0, 0.4)
        targets[it] = {k: {"yes": float(np.clip(sigmoid(np.array([b + Xc[k] @ wv]))[0], 0.05, 0.95))}
                       for k in codes}
    return targets


_FIT_TEXTS = {
    "F1": "Is abortion ever justifiable?",
    "F2": "How important is religion in your life?",
    "F3": "Do most people try to take advantage of you?",
    "F4": "Should the government reduce income inequality between rich and poor?",
    "F5": "Is climate change a very serious problem for the world?",
    "F6": "Would you be willing to fight for your country in a war?",
}
_HELD_TEXTS = {
    "H1": "Do you think abortion can ever be justifiable?",
    "H2": "How important would you say religion is in your life?",
    "H3": "Is climate change a serious problem facing the world?",
}
_EXPECTED_NB = {"H1": "F1", "H2": "F2", "H3": "F5"}


def _test_split():
    ids = [f"Q{i}" for i in range(1, 99)]
    fit, held = split_items(ids)
    assert len(fit) == 69 and len(held) == 29, (len(fit), len(held))
    assert not set(fit) & set(held), "fit and held-out overlap"
    assert set(fit) | set(held) == set(ids), "split does not cover all items"
    fit2, held2 = split_items(list(reversed(ids)))
    assert fit == fit2 and held == held2, "split depends on input order"
    fit3, held3 = split_items(ids)
    assert fit == fit3 and held == held3, "split not deterministic"
    print("PASS split: 69/29, disjoint, covering, order-invariant, deterministic")


def _test_split_guard():
    vec = _Vectorizer()
    codes, Xc = _synthetic_world()
    items = list(_FIT_TEXTS) + list(_HELD_TEXTS)
    texts = {**_FIT_TEXTS, **_HELD_TEXTS}
    targets = _synthetic_targets(items, codes, Xc)
    bad = (list(_FIT_TEXTS), ["F1"] + list(_HELD_TEXTS))  # F1 on both sides
    try:
        run_harness_core(texts, targets, {0: Xc}, list(range(6)), vec,
                         split_override=bad)
    except AssertionError as e:
        assert "split leak" in str(e)
        print("PASS split guard: overlapping split is refused (fails closed)")
        return
    raise AssertionError("core accepted an overlapping fit/held-out split")


def _test_neighbour_similarity():
    vec = _Vectorizer()  # empty idf: every token idf=1; same code path as real
    nbmap = neighbour_map(list(_HELD_TEXTS), _HELD_TEXTS,
                          list(_FIT_TEXTS), _FIT_TEXTS, vec)
    got = {h: nbmap[h]["neighbour"] for h in _HELD_TEXTS}
    assert got == _EXPECTED_NB, f"similarity selection wrong: {got} != {_EXPECTED_NB}"
    # negative control: the SAME check must fail for a random picker
    rng = np.random.default_rng(123)
    random_pick = {h: str(rng.choice(sorted(_FIT_TEXTS))) for h in sorted(_HELD_TEXTS)}
    assert random_pick != _EXPECTED_NB, (
        "negative control degenerate: random picker matched the expected map; "
        "the similarity test would not catch a random-choice bug")
    print(f"PASS neighbour similarity: paraphrases map to their sources {got}; "
          f"random picker {random_pick} fails the same check")


def _test_stem_guard():
    vec = _Vectorizer()
    held = "Please tell me how much confidence you have in the press."
    fits = {"A": "Much confidence in the press?",
            "B": "Please tell me how much confidence you have in the armed forces."}
    fit_vecs = {i: vec.embed(t) for i, t in fits.items()}
    qv = vec.embed(held)
    raw = {i: float(fit_vecs[i] @ qv) for i in fits}
    # premise: the verbatim-stem collision wins on raw cosine
    assert raw["B"] > raw["A"] > 0.5, f"selftest premise broken: raw sims {raw}"
    assert classify_pair(held, fits["B"]) == "stem_collision"
    assert classify_pair(held, fits["A"]) == "same_stem_same_object"
    pick = select_neighbour(held, sorted(fits), fits, vec, fit_vecs)
    assert pick["neighbour"] == "A" and not pick["fallback"], (
        f"stem guard failed to demote the collision: picked {pick}")
    raw_pick = max(sorted(fits), key=lambda i: raw[i])
    assert raw_pick == "B", "premise broken: guard was not needed"
    print(f"PASS stem guard: raw cosine prefers collision B ({raw['B']:.3f} > {raw['A']:.3f}) "
          f"but guarded selection picks same-object A (score {pick['guarded_score']:.3f})")


def _test_core_end_to_end():
    vec = _Vectorizer()
    codes, Xc1 = _synthetic_world(seed=0)
    rng = np.random.default_rng(1)
    Xc2 = {k: v + rng.normal(0, 0.01, v.shape) for k, v in Xc1.items()}
    items = list(_FIT_TEXTS) + list(_HELD_TEXTS)
    texts = {**_FIT_TEXTS, **_HELD_TEXTS}
    targets = _synthetic_targets(items, codes, Xc1)
    keep = list(range(6))
    split = (list(_FIT_TEXTS), list(_HELD_TEXTS))
    res = run_harness_core(texts, targets, {11: Xc1, 22: Xc2}, keep, vec,
                           split_override=split)
    # 1. split honored: scored set == held-out set, no fit item scored
    scored = set(res["per_item"])
    assert scored == set(_HELD_TEXTS), f"scored {scored} != held-out {set(_HELD_TEXTS)}"
    assert not scored & set(_FIT_TEXTS), "a FIT item appears in the scored set"
    assert set(res["split"]["fit_items"]) == set(_FIT_TEXTS)
    assert set(res["split"]["heldout_items"]) == set(_HELD_TEXTS)
    # 2. neighbours chosen by similarity
    got = {h: res["neighbours"][h]["neighbour"] for h in _HELD_TEXTS}
    assert got == _EXPECTED_NB, f"core neighbour map wrong: {got}"
    # 3. predictions well-formed and scored on common pairs
    for h, rows in res["pairs"].items():
        assert rows, f"no pairs for {h}"
        for k, r in rows.items():
            assert k in targets[h] and k in Xc1
            assert 0.0 <= r["e1_mean"] <= 1.0 and 0.0 <= r["neighbour_copy"] <= 1.0
    # 4. MAE recomputation matches the frozen scorer
    h = "H1"
    ks = sorted(res["pairs"][h])
    manual = float(np.mean([abs(res["pairs"][h][k]["neighbour_copy"]
                                - res["pairs"][h][k]["truth"]) for k in ks])) * 100
    assert abs(manual - res["per_item"][h]["mae_pp"]["neighbour_copy"]) < 1e-9
    # 5. tamper test: perturbing HELD-OUT targets must not move any
    #    prediction (proves neither arm reads held-out truth before scoring)
    tampered = {i: {k: dict(v) for k, v in targets[i].items()} for i in targets}
    trng = np.random.default_rng(99)
    for hh in _HELD_TEXTS:
        for k in tampered[hh]:
            tampered[hh][k] = {"yes": float(np.clip(
                tampered[hh][k]["yes"] + trng.uniform(0.1, 0.3) * trng.choice([-1, 1]),
                0.01, 0.99))}
    res_t = run_harness_core(texts, tampered, {11: Xc1, 22: Xc2}, keep, vec,
                             split_override=split)
    moved = False
    for hh in _HELD_TEXTS:
        assert res_t["neighbours"][hh]["neighbour"] == res["neighbours"][hh]["neighbour"]
        for k in res["pairs"][hh]:
            a, b = res["pairs"][hh][k], res_t["pairs"][hh][k]
            assert a["e1"] == b["e1"] and a["e1_mean"] == b["e1_mean"], (
                f"e1 prediction for {hh}/{k} changed when held-out truth was tampered")
            assert a["neighbour_copy"] == b["neighbour_copy"], (
                f"baseline for {hh}/{k} changed when held-out truth was tampered")
            moved = moved or a["truth"] != b["truth"]
    assert moved, "tamper test degenerate: no truth value actually changed"
    assert res_t["headline"]["e1_mae_pp"] != res["headline"]["e1_mae_pp"], (
        "tamper test degenerate: scores did not react to changed truth")
    # 6. determinism
    res2 = run_harness_core(texts, targets, {11: Xc1, 22: Xc2}, keep, vec,
                            split_override=split)
    assert json.dumps(res2["headline"], sort_keys=True) == json.dumps(res["headline"], sort_keys=True)
    print(f"PASS core end-to-end: scored={sorted(scored)}, pairs/item="
          f"{[res['per_item'][x]['n_pairs'] for x in sorted(scored)]}, "
          f"predictions invariant under held-out-truth tampering, deterministic")


def selftest():
    _test_split()
    _test_split_guard()
    _test_neighbour_similarity()
    _test_stem_guard()
    _test_core_end_to_end()
    print("SELFTEST OK (5/5)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true", help="run synthetic selftests and exit")
    ap.add_argument("--pop", type=int, default=run_v2.POP)
    ap.add_argument("--days", type=int, default=run_v2.DAYS)
    ap.add_argument("--world-seeds", default=",".join(str(s) for s in run_v2.WORLD_SEEDS))
    ap.add_argument("--cv-seed", type=int, default=CV_SEED)
    ap.add_argument("--split-seed", type=int, default=SPLIT_SEED)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    run_real(args)


if __name__ == "__main__":
    main()
