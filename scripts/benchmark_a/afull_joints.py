"""A-FULL-1 task iii — 2D attitude-pair joints (measurement only; new harness).

Protocol
--------
Estate: WVS confirm joint vectors (joint_vectors_confirm_v2.npz — per-country
respondent-level binary vectors over the 8 confirm joint items, with survey
weights).  Countries are "held out" in the A-v2 sense: every Earth-1 marginal
anchor is an OOS MRP anchor (leakage guard re-asserted on every scored row).

1. REGISTRATION (written to the output json BEFORE any Earth-1 scoring):
   all C(8,2)=28 item pairs are ranked by |survey covariance| — the
   equal-country mean of the within-country weighted covariance of the two
   binarized items — and the top 20 are registered.
2. MODEL ARM: per world seed (42, 20260901, 20260902) the candidate world is
   replayed (birth_world + 60 live days, substrate/flags from the environment
   — identical to scripts/benchmark_a/run_v2.py stage "earth1"), per-agent
   probabilities p_i are rebuilt with the frozen recipe (per-item ridge at cv
   seed 42, center_latent, solve_K against the OOS MRP marginal), and agent
   binary vectors are drawn with the frozen deterministic RNG
   (zlib.crc32(f"{iso}|{item}")).  If a candidate earth1_confirm_v2.json is
   supplied its kept_cols are reused and each replayed world hash must match.
3. METRIC: the joint of a binary item pair is a categorical distribution on
   {0,1}^2, so "2D Wasserstein" is computed as the EXACT discretized
   1-Wasserstein with L1 (Hamming) ground metric on the 4 cells.  The four
   cells with L1 costs form a 4-cycle graph whose graph metric equals L1, so
   W1 = min-cost flow on the cycle = min_t sum_i |t - c_i| (closed form via
   the median of the breakpoints; verified in --selftest against exhaustive
   Kantorovich-dual enumeration, which is exact here by LP duality + total
   unimodularity of the cycle incidence constraints).
4. BASELINE: independent-marginal synthetic population with IDENTICAL
   marginals to Earth-1's own — the second item's column of Earth-1's agent
   matrix is permuted within country (N_SHUFFLES deterministic permutations,
   W1 averaged).  A permutation preserves both marginals exactly, so any
   advantage of the model arm is joint structure, never level.
5. AGGREGATION/GATE: per (pair, country, world-seed) W1 -> mean over world
   seeds -> median over countries per pair.  Pair win = median_e1 <
   median_baseline.  WIN gate = wins / n_registered > 0.60 (strict).

Data availability: if the survey respondent-level npz (or the OOS-anchor
baselines artifact) is absent the script writes a NOT_RUN artifact with the
reason and exits 0 — joints are never faked from marginals.

Inputs (env):
  EARTH1_AFULL_OUT        REQUIRED output dir (refuses frozen artifact dirs);
                          writes $EARTH1_AFULL_OUT/joints.json
  EARTH1_AV2_OUT          candidate A-v2 artifact dir; default source of
                          confirm_targets_v2.json / baselines_confirm_v2.json
                          / earth1_confirm_v2.json
  EARTH1_AFULL_CONFIRM    override path to confirm_targets_v2.json
  EARTH1_AFULL_BASELINES  override path to baselines_confirm_v2.json
  EARTH1_AFULL_E1         override path to earth1_confirm_v2.json (optional;
                          supplies kept_cols + world-hash verification)
  EARTH1_AFULL_NPZ        override path to joint_vectors_confirm_v2.npz
                          (default /opt/earth1-data/benchmark_a/...)
  EARTH1_SUBSTRATE + physics flag env — read by the engine at import, exactly
                          as in the run_v2 candidate chain.

Usage:
  .venv/bin/python scripts/benchmark_a/afull_joints.py            # real run
  python3 scripts/benchmark_a/afull_joints.py --selftest          # local test

Read-only with respect to every existing artifact; writes ONLY joints.json.
"""
import json
import os
import sys
import time
import zlib

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)  # `earth1` package, exactly as run_v2.py does

N_REGISTERED = 20
N_SHUFFLES = 8
WIN_THRESHOLD = 0.60          # strict: win_fraction must EXCEED this
JOINT_CV_SEED = 42            # frozen: run_v2 joint task fits at cv seed 42

# The 4 cells of {0,1}^2 in 4-CYCLE order (adjacent cells differ in one
# coordinate): (0,0) -> (0,1) -> (1,1) -> (1,0) -> (0,0).  The cycle graph
# metric equals the L1 ground metric on these points.
CYCLE_CELLS = ((0, 0), (0, 1), (1, 1), (1, 0))
# bincount index (a<<1)|b gives standard order 00,01,10,11 -> cycle order:
_STD_TO_CYCLE = np.array([0, 1, 3, 2])


# ────────────────────────────────────────────────────────────────────
# Pure metric / baseline / registration functions (selftested)
# ────────────────────────────────────────────────────────────────────
def joint_dist(a, b, w=None):
    """4-cell joint distribution (cycle order) of two binary columns."""
    a = np.asarray(a); b = np.asarray(b)
    idx = (a.astype(np.int64) << 1) | b.astype(np.int64)
    cnt = np.bincount(idx, weights=w, minlength=4).astype(float)
    tot = cnt.sum()
    if tot <= 0:
        raise ValueError("empty joint")
    return (cnt / tot)[_STD_TO_CYCLE]


def w1_pair(p, q):
    """EXACT 1-Wasserstein between two distributions on {0,1}^2 with L1
    ground metric.  p, q are length-4 arrays in CYCLE order summing to 1.

    Min-cost flow on the 4-cycle: with edge flows f_i (v_i -> v_{i+1}) and
    imbalances b = p - q, conservation gives f_i = t + b_1 + ... + b_i for a
    single free circulation t; cost(t) = sum_i |t - c_i| with breakpoints
    c = [0, -b1, -(b1+b2), -(b1+b2+b3)], minimized at the median."""
    b = np.asarray(p, float) - np.asarray(q, float)
    c = np.array([0.0, -b[1], -(b[1] + b[2]), -(b[1] + b[2] + b[3])])
    t = float(np.median(c))
    return float(np.abs(t - c).sum())


def weighted_cov(a, b, w=None):
    """Weighted covariance of two binary columns."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    w = np.ones_like(a) if w is None else np.asarray(w, float)
    w = w / w.sum()
    return float(w @ ((a - w @ a) * (b - w @ b)))


def register_pairs(survey, items, top_k=N_REGISTERED):
    """Rank all item pairs by |equal-country mean of within-country weighted
    covariance| over the survey data; return the top_k registered records.

    survey: {iso2: (X int matrix [n, len(items)], w weights [n])}.
    Deterministic; depends on survey data only (never on the model)."""
    n_items = len(items)
    recs = []
    for i in range(n_items):
        for j in range(i + 1, n_items):
            covs = [weighted_cov(X[:, i], X[:, j], w) for X, w in survey.values()]
            m = float(np.mean(covs))
            recs.append({"pair": [items[i], items[j]], "i": i, "j": j,
                         "mean_within_country_weighted_cov": round(m, 6),
                         "abs_cov": round(abs(m), 6),
                         "n_countries": len(covs)})
    recs.sort(key=lambda r: (-r["abs_cov"], r["i"], r["j"]))
    return recs[:top_k], len(recs)


def shuffled_baseline_w1(a_col, b_col, survey_dist, seed_key, n_shuffles=N_SHUFFLES):
    """Baseline arm: permute the second column within the country (marginals
    identical to the model's own by construction), W1 to the survey joint,
    averaged over n_shuffles deterministic permutations."""
    b_col = np.asarray(b_col)
    vals = []
    for r in range(n_shuffles):
        rr = np.random.default_rng(zlib.crc32(f"afull-shuffle|{seed_key}|{r}".encode()))
        perm = rr.permutation(b_col.size)
        vals.append(w1_pair(joint_dist(a_col, b_col[perm]), survey_dist))
    return float(np.mean(vals))


def decide_gate(per_pair):
    """per_pair: list of (median_e1, median_baseline). WIN iff the fraction
    of pairs with median_e1 < median_baseline strictly exceeds 0.60."""
    wins = sum(1 for e, b in per_pair if e < b)
    frac = wins / len(per_pair) if per_pair else 0.0
    return wins, frac, bool(frac > WIN_THRESHOLD)


# ────────────────────────────────────────────────────────────────────
# Selftest (pure numpy; must FAIL a broken implementation)
# ────────────────────────────────────────────────────────────────────
def _w1_reference_dual(p, q):
    """Independent exact reference: exhaustive Kantorovich dual.
    max f.(p-q) over potentials f with f0=0, |f_u - f_v| <= d(u, v);
    with an integral graph metric an integral optimal potential in [-2, 2]
    exists (min-cost-flow duality / total unimodularity)."""
    D = np.zeros((4, 4))
    for u in range(4):
        for v in range(4):
            D[u, v] = abs(CYCLE_CELLS[u][0] - CYCLE_CELLS[v][0]) + \
                      abs(CYCLE_CELLS[u][1] - CYCLE_CELLS[v][1])
    diff = np.asarray(p, float) - np.asarray(q, float)
    best = 0.0
    rng5 = range(-2, 3)
    for f1 in rng5:
        for f2 in rng5:
            for f3 in rng5:
                f = np.array([0.0, f1, f2, f3])
                if all(abs(f[u] - f[v]) <= D[u, v] for u in range(4) for v in range(u + 1, 4)):
                    best = max(best, float(f @ diff))
    return best


def selftest():
    failures = []

    def check(name, fn):
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failures.append(name)
            print(f"  FAIL  {name}: {e}")

    # 1. W1 exactness on hand-computable cases
    def t_hand_cases():
        e = lambda k: np.eye(4)[k]
        assert abs(w1_pair(e(0), e(0))) < 1e-12, "W1(P,P) != 0"
        # point mass (0,0) vs (1,1): cells 0 and 2 in cycle order, dist 2
        assert abs(w1_pair(e(0), e(2)) - 2.0) < 1e-12, "opposite corners != 2"
        assert abs(w1_pair(e(0), e(1)) - 1.0) < 1e-12, "adjacent != 1"
        # diagonal vs anti-diagonal: every unit moves distance 1
        P = np.array([.5, 0., .5, 0.]); Q = np.array([0., .5, 0., .5])
        assert abs(w1_pair(P, Q) - 1.0) < 1e-12, "diag vs anti-diag != 1"
        # perfectly correlated vs independent at p=q=0.5: W1 = 0.5
        P = np.array([.5, 0., .5, 0.]); Q = np.full(4, .25)
        assert abs(w1_pair(P, Q) - 0.5) < 1e-12, "corr vs indep != 0.5"

    # 2. W1 exactness vs independent exhaustive-dual reference (random)
    def t_dual_reference():
        rng = np.random.default_rng(123)
        worst = 0.0
        for _ in range(400):
            p = rng.dirichlet(np.full(4, rng.uniform(0.2, 3.0)))
            q = rng.dirichlet(np.full(4, rng.uniform(0.2, 3.0)))
            worst = max(worst, abs(w1_pair(p, q) - _w1_reference_dual(p, q)))
            assert abs(w1_pair(p, q) - w1_pair(q, p)) < 1e-12, "asymmetric"
        assert worst < 1e-9, f"primal/dual mismatch {worst}"

    # 2b. optional scipy LP cross-check (skipped silently if unavailable)
    def t_scipy_lp():
        try:
            from scipy.optimize import linprog
        except Exception:
            return
        D = np.array([[abs(a[0] - b[0]) + abs(a[1] - b[1])
                       for b in CYCLE_CELLS] for a in CYCLE_CELLS], float)
        rng = np.random.default_rng(9)
        for _ in range(50):
            p = rng.dirichlet(np.ones(4)); q = rng.dirichlet(np.ones(4))
            A_eq = np.zeros((8, 16)); b_eq = np.concatenate([p, q])
            for u in range(4):
                for v in range(4):
                    A_eq[u, 4 * u + v] = 1; A_eq[4 + v, 4 * u + v] = 1
            r = linprog(D.ravel(), A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
            assert r.success and abs(r.fun - w1_pair(p, q)) < 1e-8, \
                f"LP {r.fun} vs {w1_pair(p, q)}"

    # 3. THE TRAP for broken implementations: a synthetic model with the
    # correct correlation must beat its own shuffled (independent-marginal)
    # version by a clear margin.  A metric that only sees marginals ties
    # here (the shuffle preserves marginals EXACTLY), so a broken w1_pair /
    # joint_dist / shuffle fails this check.
    def t_correlated_beats_shuffled():
        rng = np.random.default_rng(7)
        n = 6000
        def draw():
            z = rng.random(n) < 0.5
            return ((z ^ (rng.random(n) < 0.15)).astype(np.int8),
                    (z ^ (rng.random(n) < 0.15)).astype(np.int8))
        si, sj = draw()                       # "survey"
        mi, mj = draw()                       # "model": same joint law
        sd_ = joint_dist(si, sj)
        w_model = w1_pair(joint_dist(mi, mj), sd_)
        w_base = shuffled_baseline_w1(mi, mj, sd_, "selftest|X|Qa|Qb")
        assert w_base - w_model >= 0.10, \
            f"correlated model must beat shuffled baseline (model {w_model:.4f} vs baseline {w_base:.4f})"
        # and the gate must call this a win
        wins, frac, gate = decide_gate([(w_model, w_base)])
        assert wins == 1 and gate, "gate failed to register a clear win"

    # 4. the shuffle preserves both marginals exactly
    def t_shuffle_preserves_marginals():
        rng = np.random.default_rng(11)
        a = (rng.random(500) < 0.3).astype(np.int8)
        b = (rng.random(500) < 0.7).astype(np.int8)
        rr = np.random.default_rng(zlib.crc32(b"afull-shuffle|k|0"))
        bs = b[rr.permutation(b.size)]
        assert bs.sum() == b.sum() and sorted(bs) == sorted(b), "marginal broken"
        d = joint_dist(a, bs)
        # cycle order (00,01,11,10): P(a=1) = cells 2+3, P(b=1) = cells 1+2
        assert abs((d[2] + d[3]) - a.mean()) < 1e-12, "a-marginal broken"
        assert abs((d[1] + d[2]) - b.mean()) < 1e-12, "b-marginal broken"

    # 5. weighted joint == row duplication
    def t_weighted_joint():
        a = np.array([0, 1, 1]); b = np.array([1, 1, 0])
        w = np.array([1.0, 2.0, 1.0])
        dup = joint_dist(np.array([0, 1, 1, 1]), np.array([1, 1, 1, 0]))
        assert np.allclose(joint_dist(a, b, w), dup), "weights != duplication"

    # 6. registration: designed covariances rank correctly, top-k honoured
    def t_registration():
        rng = np.random.default_rng(3)
        n = 5000
        z = (rng.random(n) < 0.5)
        X = np.stack([
            (z ^ (rng.random(n) < 0.05)).astype(np.int8),     # A: ~z
            (z ^ (rng.random(n) < 0.05)).astype(np.int8),     # B: ~z  -> (A,B) big cov
            (rng.random(n) < 0.5).astype(np.int8),            # C: independent
            (~z ^ (rng.random(n) < 0.25)).astype(np.int8),    # D: anti-corr, weaker
        ], axis=1)
        survey = {"AA": (X, np.ones(n)), "BB": (X.copy(), np.ones(n))}
        top, n_total = register_pairs(survey, ["A", "B", "C", "D"], top_k=2)
        assert n_total == 6, "C(4,2) != 6"
        assert len(top) == 2, "top_k not honoured"
        assert top[0]["pair"] == ["A", "B"], f"strongest pair wrong: {top[0]}"
        assert {tuple(t["pair"]) for t in top} == {("A", "B"), ("A", "D")} or \
               {tuple(t["pair"]) for t in top} == {("A", "B"), ("B", "D")}, \
            f"second pair implausible: {top}"
        assert abs(top[0]["mean_within_country_weighted_cov"]) > \
               abs(top[1]["mean_within_country_weighted_cov"]), "not sorted by |cov|"

    # 7. gate arithmetic: strict > 0.60
    def t_gate():
        w = (0.1, 0.2); l = (0.2, 0.1)
        wins, frac, gate = decide_gate([w] * 12 + [l] * 8)   # 12/20 = 0.60
        assert wins == 12 and not gate, "12/20 must NOT pass a strict >0.60 gate"
        wins, frac, gate = decide_gate([w] * 13 + [l] * 7)   # 13/20 = 0.65
        assert wins == 13 and gate, "13/20 must pass"

    print("afull_joints selftest:")
    for name, fn in [("hand-computable W1 cases", t_hand_cases),
                     ("W1 primal == exhaustive Kantorovich dual", t_dual_reference),
                     ("W1 == scipy LP (optional)", t_scipy_lp),
                     ("correlated model beats shuffled baseline", t_correlated_beats_shuffled),
                     ("shuffle preserves marginals exactly", t_shuffle_preserves_marginals),
                     ("weighted joint == row duplication", t_weighted_joint),
                     ("pair registration ranking", t_registration),
                     ("gate strict >0.60", t_gate)]:
        check(name, fn)
    if failures:
        print(f"SELFTEST FAIL ({len(failures)}): {failures}")
        return 1
    print("SELFTEST PASS (8/8)")
    return 0


# ────────────────────────────────────────────────────────────────────
# Real run (prime, .venv python, candidate flags in env)
# ────────────────────────────────────────────────────────────────────
FROZEN_DIRS = (os.path.join(ROOT, "data", "benchmark_a"),
               "/opt/earth1-data/benchmark_a",
               "/opt/earth1-data/av2_c2plus")


def _die(msg):
    print(f"afull_joints: FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def _write(path, doc):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def _not_run(out_path, reason):
    _write(out_path, {"protocol": "A-FULL-1 task iii (2D attitude-pair joints)",
                      "status": "NOT_RUN", "reason": reason,
                      "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    print(f"NOT_RUN: {reason}\nwrote {out_path}")
    sys.exit(0)


def main():
    outdir = os.environ.get("EARTH1_AFULL_OUT")
    if not outdir:
        _die("EARTH1_AFULL_OUT is required (candidate output dir)")
    outdir = os.path.abspath(outdir)
    if os.path.realpath(outdir) in {os.path.realpath(p) for p in FROZEN_DIRS}:
        _die(f"refusing to write into frozen artifact dir {outdir}")
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "joints.json")

    av2 = os.environ.get("EARTH1_AV2_OUT")
    confirm_p = os.environ.get("EARTH1_AFULL_CONFIRM") or (
        os.path.join(av2, "confirm_targets_v2.json") if av2
        else os.path.join(ROOT, "data", "benchmark_a", "confirm_targets_v2.json"))
    base_p = os.environ.get("EARTH1_AFULL_BASELINES") or (
        os.path.join(av2, "baselines_confirm_v2.json") if av2 else None)
    e1_p = os.environ.get("EARTH1_AFULL_E1") or (
        os.path.join(av2, "earth1_confirm_v2.json") if av2 else None)
    npz_p = os.environ.get("EARTH1_AFULL_NPZ",
                           "/opt/earth1-data/benchmark_a/joint_vectors_confirm_v2.npz")

    # ── data availability (NOT_RUN, never faked from marginals) ──────
    if not os.path.exists(npz_p):
        _not_run(out_path, f"respondent-level survey joint vectors not found: {npz_p}")
    if not base_p or not os.path.exists(base_p):
        _not_run(out_path, "baselines_confirm_v2.json (OOS MRP joint marginals) not found; "
                           "set EARTH1_AV2_OUT or EARTH1_AFULL_BASELINES")
    if not os.path.exists(confirm_p):
        _not_run(out_path, f"confirm_targets_v2.json not found: {confirm_p}")

    from earth1.benchmark_a import scoring as S  # sha256_of_file, bootstrap
    D = json.load(open(confirm_p))
    B = json.load(open(base_p))
    Z = np.load(npz_p)
    JI = D["joint_items"]
    if "joint" not in B or not B["joint"]:
        _not_run(out_path, "baselines artifact carries no joint anchors")

    survey_all = {}
    for key in sorted(Z.files):
        if key.endswith("_x"):
            iso = key[:-2]
            X = Z[f"{iso}_x"].astype(np.int8)
            if X.shape[1] != len(JI):
                _not_run(out_path, f"npz item-dimension {X.shape[1]} != joint_items {len(JI)}")
            survey_all[iso] = (X, Z[f"{iso}_w"].astype(float))
    if not survey_all:
        _not_run(out_path, "npz holds no per-country respondent vectors")

    # ── 1. REGISTRATION — written to disk BEFORE any Earth-1 scoring ─
    pairs, n_total = register_pairs(survey_all, JI, top_k=N_REGISTERED)
    doc = {
        "protocol": "A-FULL-1 task iii (2D attitude-pair joints)",
        "status": "REGISTERED",
        "registered": {
            "rule": ("top-{} of all C({},2)={} item pairs by |survey covariance| = "
                     "|equal-country mean of within-country weighted covariance| "
                     "(survey data only; ties broken by item index)").format(
                         N_REGISTERED, len(JI), n_total),
            "joint_items": JI,
            "n_pairs_total": n_total,
            "n_registered": len(pairs),
            "pairs": pairs,
            "n_survey_countries": len(survey_all),
            "survey_npz": npz_p,
            "survey_npz_sha256": S.sha256_of_file(npz_p),
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "metric": {
            "name": "discrete_wasserstein_l1_binary_pair",
            "note": ("exact 1-Wasserstein on the 4-cell joint of a binarized item pair, "
                     "L1 (Hamming) ground metric; survey joint is survey-weight weighted, "
                     "Earth-1 joint is unweighted over alive agents (the synthetic "
                     "population IS the model's claim); range [0, 2]")},
        "baseline": {
            "name": "within_country_column_shuffle",
            "n_shuffles": N_SHUFFLES,
            "note": ("second item's column of Earth-1's OWN agent matrix permuted within "
                     "country (identical marginals by construction), deterministic seeds, "
                     "W1 averaged over shuffles")},
        "gate_rule": ("per pair: mean over world seeds then median over countries; "
                      "win iff median_e1 < median_baseline; "
                      "WIN iff wins/n_registered > {} (strict)").format(WIN_THRESHOLD),
        "config": {
            "pop": None, "days": None, "world_seeds": None,  # filled from run_v2 below
            "joint_cv_seed": JOINT_CV_SEED,
            "substrate": os.environ.get("EARTH1_SUBSTRATE"),
            "flags": {k: v for k, v in sorted(os.environ.items())
                      if k.startswith("EARTH1_")},
            "confirm_targets": confirm_p,
            "confirm_targets_sha256": S.sha256_of_file(confirm_p),
            "baselines": base_p,
            "baselines_sha256": S.sha256_of_file(base_p),
            "e1_artifact": e1_p if e1_p and os.path.exists(e1_p) else None,
        },
    }
    _write(out_path, doc)
    print(f"REGISTERED {len(pairs)}/{n_total} pairs -> {out_path}", flush=True)

    # ── 2. Earth-1 replay (frozen recipe from run_v2.run_earth1) ─────
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import run_v2  # frozen constants + folds_for + _feature_treatment
    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.calibration import living_features, living_feature_names, _get_country_index
    from earth1.persistence import world_hash
    from earth1.benchmark_a.mean_preserving import solve_K, center_latent
    from earth1.benchmark_a.leakage import assert_anchor_oos
    from earth1.rng import logit

    POP, DAYS = run_v2.POP, run_v2.DAYS
    WORLD_SEEDS, LAMBDAS, FOLDS = run_v2.WORLD_SEEDS, run_v2.LAMBDAS, run_v2.FOLDS
    folds_for = run_v2.folds_for
    SUBSTRATE = os.environ.get("EARTH1_SUBSTRATE") or None
    doc["config"].update({"pop": POP, "days": DAYS, "world_seeds": list(WORLD_SEEDS),
                          "physics_version": PHYSICS_VERSION})

    E1 = None
    if e1_p and os.path.exists(e1_p):
        E1 = json.load(open(e1_p))

    def fit_item(Xc, keep, targets, seed):
        """VERBATIM numerics of run_v2.run_earth1.fit_item (frozen)."""
        cs = sorted(k for k in targets if k in Xc)
        y = {k: targets[k]["yes"] for k in cs}
        fits = {}
        for test in folds_for(cs, seed):
            train = [k for k in cs if k not in set(test)]
            if len(train) < 8:
                continue
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
                if (e := float(np.mean(errs))) < be:
                    lam, be = L, e
            mu, sd = Xt.mean(0), Xt.std(0) + 1e-9; Zt = (Xt - mu) / sd; b0 = yt.mean()
            wv = np.linalg.solve(Zt.T @ Zt + lam * np.eye(Zt.shape[1]), Zt.T @ (yt - b0))
            for k in test:
                fits[k] = (mu, sd, b0, wv)
        return fits

    # accumulators: rows[pair_key][iso] = {"e1": [per ws], "baseline": [per ws]}
    rows = {f'{r["pair"][0]}|{r["pair"][1]}': {} for r in pairs}
    keep = E1.get("kept_cols") if E1 else None
    doc["worlds"] = {}

    for ws in WORLD_SEEDS:
        t0 = time.time()
        w = birth_world(POP, ws, substrate=SUBSTRATE)
        rng = np.random.default_rng(ws)
        for _ in range(DAYS):
            live_one_day(w, rng)
        wh = world_hash(w)
        winfo = {"world_hash": wh, "world_day": int(w.day),
                 "alive": int(w.health.alive.sum()),
                 "seconds": round(time.time() - t0, 1)}
        if E1 is not None:
            ref = E1.get("worlds", {}).get(str(ws), {}).get("world_hash")
            winfo["matches_e1_artifact"] = bool(ref == wh)
            if ref is not None and ref != wh:
                doc["status"] = "ERROR"
                doc["error"] = (f"world {ws} replay hash {wh} != candidate artifact hash {ref}: "
                                "flag environment or physics differs from the recorded "
                                "candidate run; refusing to score a different physics")
                doc["worlds"][str(ws)] = winfo
                _write(out_path, doc)
                _die(doc["error"])
        doc["worlds"][str(ws)] = winfo

        X = living_features(w); civ = w.civ; alive = w.health.alive
        c2i, codes = _get_country_index(civ)
        cmask = {k: (civ.country == c2i[k]) & alive for k in codes if k in c2i}
        Xc = {k: X[m].mean(0) for k, m in cmask.items() if m.sum() >= 30}
        if keep is None:  # same construction as run_v2 (first world defines it)
            keep, rep = run_v2._feature_treatment([Xc[k] for k in sorted(Xc)],
                                                  living_feature_names(True))
            doc["feature_report"] = rep
        Xk = X[:, keep]

        fitsJ = {c: fit_item(Xc, keep, D["targets"][c], JOINT_CV_SEED) for c in JI}
        n_scored = 0
        for k in sorted(Xc):
            if f"{k}_x" not in Z.files or k not in B["joint"]:
                continue
            m = cmask[k]
            ok, cols = True, []
            for j, c in enumerate(JI):
                if k not in fitsJ[c]:
                    ok = False
                    break
                # leakage guard: this country's anchor was fit without it
                assert_anchor_oos({"country": k, **B["anchors"][c][str(JOINT_CV_SEED)][k]})
                mu, sd, b0, wv = fitsJ[c][k]
                delta = center_latent(((Xk[m] - mu) / sd) @ wv)
                a = B["joint"][k]["mrp_marginals"][j]
                K, p_i = solve_K(a, delta)
                rr = np.random.default_rng(zlib.crc32(f"{k}|{c}".encode()))
                cols.append((rr.random(p_i.size) < p_i).astype(np.int8))
            if not ok:
                continue
            A = np.stack(cols, 1)
            Xr, wt = survey_all[k]
            for r in pairs:
                i, j = r["i"], r["j"]
                pk = f'{r["pair"][0]}|{r["pair"][1]}'
                sd_ = joint_dist(Xr[:, i], Xr[:, j], wt)
                e1 = w1_pair(joint_dist(A[:, i], A[:, j]), sd_)
                base = shuffled_baseline_w1(
                    A[:, i], A[:, j], sd_,
                    seed_key=f"{ws}|{k}|{r['pair'][0]}|{r['pair'][1]}")
                cell = rows[pk].setdefault(k, {"e1": [], "baseline": [],
                                               "n_survey": int(Xr.shape[0]),
                                               "n_agents": int(A.shape[0])})
                cell["e1"].append(e1); cell["baseline"].append(base)
            n_scored += 1
        print(f"world {ws} done {time.time() - t0:.0f}s ({n_scored} countries)", flush=True)

    # ── 3. aggregate + gate ──────────────────────────────────────────
    if not any(rows.values()):
        doc["status"] = "ERROR"
        doc["error"] = ("zero countries scored (no country had fits for all 8 joint "
                        "items plus survey vectors and OOS anchors)")
        _write(out_path, doc)
        _die(doc["error"])
    per_pair_out, medians = {}, []
    for r in pairs:
        pk = f'{r["pair"][0]}|{r["pair"][1]}'
        cc = rows[pk]
        per_country = {iso: {"e1_w1": round(float(np.mean(v["e1"])), 6),
                             "baseline_w1": round(float(np.mean(v["baseline"])), 6),
                             "n_survey": v["n_survey"], "n_agents": v["n_agents"]}
                       for iso, v in sorted(cc.items())}
        med_e1 = float(np.median([v["e1_w1"] for v in per_country.values()]))
        med_b = float(np.median([v["baseline_w1"] for v in per_country.values()]))
        medians.append((med_e1, med_b))
        per_pair_out[pk] = {"median_e1_w1": round(med_e1, 6),
                            "median_baseline_w1": round(med_b, 6),
                            "win": bool(med_e1 < med_b),
                            "n_countries": len(per_country),
                            "abs_survey_cov": r["abs_cov"],
                            "per_country": per_country}
    wins, frac, gate = decide_gate(medians)
    ci = S.paired_bootstrap_diff_ci(np.array([b for _, b in medians]),
                                    np.array([e for e, _ in medians]))
    doc["status"] = "SCORED"
    doc["results"] = {
        "per_pair": per_pair_out,
        "wins": wins,
        "n_pairs": len(medians),
        "win_fraction": round(frac, 4),
        "gate": gate,
        "median_over_pairs": {
            "e1_w1": round(float(np.median([e for e, _ in medians])), 6),
            "baseline_w1": round(float(np.median([b for _, b in medians])), 6)},
        "baseline_minus_e1_median_ci": [round(x, 6) for x in ci],
        "note": "CI over registered pairs (paired bootstrap on per-pair medians); reference only, gate is the win fraction",
    }
    doc["scored_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _write(out_path, doc)
    print(f"SCORED: wins {wins}/{len(medians)} (fraction {frac:.2f}) GATE {gate}\nwrote {out_path}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
