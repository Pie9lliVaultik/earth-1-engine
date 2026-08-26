"""C2+ population-synthesis bake-off (THREE_TRACK_PREREG_v1 Track B).

Leave-country-out on WVS-7 microdata. Methods receive ONLY the held-out
country's five 1-way margins (+ TRAIN-country microdata); scored on the
held-out country's withheld two-way and three-way joints.

Stages: extract | genesis_map | run
Axes: sex(2) x age(6) x edu(3) x income(3) x urban(2) -> 216 cells.
M1 note: genesis has NO sex attribute -> sex = CANNOT_EXPRESS, scored
as independence on that axis per prereg B4 (a finding, not a repair).
"""
import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from earth1.dataroles import path_for  # noqa: E402

OUT = "/opt/earth1-data/c2plus"
SHAPE = (2, 6, 3, 3, 2)
AXES = ("sex", "age", "edu", "income", "urban")
MIN_ROWS = 800
NBOOT = 200
A3 = {  # alpha-3 -> alpha-2 for WVS-7 countries; extract fails loudly on gaps
 "AND":"AD","ARG":"AR","ARM":"AM","AUS":"AU","BGD":"BD","BOL":"BO","BRA":"BR",
 "CAN":"CA","CHL":"CL","CHN":"CN","COL":"CO","CYP":"CY","CZE":"CZ","DEU":"DE",
 "ECU":"EC","EGY":"EG","ETH":"ET","GBR":"GB","GRC":"GR","GTM":"GT","HKG":"HK",
 "IDN":"ID","IND":"IN","IRN":"IR","IRQ":"IQ","JOR":"JO","JPN":"JP","KAZ":"KZ",
 "KEN":"KE","KGZ":"KG","KOR":"KR","LBN":"LB","LBY":"LY","LKA":"LK","MAC":"MO",
 "MAR":"MA","MDV":"MV","MEX":"MX","MMR":"MM","MNG":"MN","MYS":"MY","NGA":"NG",
 "NIC":"NI","NLD":"NL","NZL":"NZ","PAK":"PK","PER":"PE","PHL":"PH","PRI":"PR",
 "ROU":"RO","RUS":"RU","SGP":"SG","SRB":"RS","SVK":"SK","THA":"TH","TJK":"TJ",
 "TUN":"TN","TUR":"TR","TWN":"TW","UKR":"UA","URY":"UY","USA":"US","VEN":"VE",
 "VNM":"VN","ZWE":"ZW"}


def _cells(sex, age, edu, inc, urb, wt):
    t = np.zeros(SHAPE)
    np.add.at(t, (sex, age, edu, inc, urb), wt)
    return t / t.sum()


def stage_extract():
    import duckdb
    os.makedirs(OUT, exist_ok=True)
    db = path_for("wvs7_microdata", "training")
    con = duckdb.connect(db, read_only=True)
    rows = con.execute(
        "select B_COUNTRY_ALPHA, Q260, X003R, Q275R, Q288R, H_URBRURAL, "
        "W_WEIGHT*S018 as wt from wvs "
        "where Q260 in (1,2) and X003R between 1 and 6 "
        "and Q275R in (1,2,3) and Q288R in (1,2,3) "
        "and H_URBRURAL in (1,2) and wt > 0").fetchall()
    total = con.execute("select count(*) from wvs").fetchone()[0]
    by_c = {}
    for a3, sex, age, edu, inc, urb, wt in rows:
        by_c.setdefault(a3, []).append(
            (int(sex) - 1, int(age) - 1, int(edu) - 1, int(inc) - 1,
             int(urb) - 1, float(wt)))
    unmapped = sorted(set(by_c) - set(A3))
    if unmapped:
        sys.exit(f"unmapped alpha-3 codes {unmapped}: extend A3")
    out = {}
    for a3, r in by_c.items():
        if len(r) < MIN_ROWS:
            continue
        arr = np.array(r)
        out[a3] = {"n": len(r), "iso2": A3[a3],
                   "rows": arr.tolist()}
    json.dump({"countries": {k: {"n": v["n"], "iso2": v["iso2"]}
                             for k, v in out.items()},
               "dropped_rows": total - len(rows), "total_rows": total},
              open(os.path.join(OUT, "extract_meta.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(OUT, "rows.npz"),
                        **{k: np.array(v["rows"]) for k, v in out.items()})
    print("EXTRACTED", len(out), "countries;",
          f"{total-len(rows)}/{total} rows dropped on missing codes")


def stage_genesis_map():
    """Incumbent genesis (M1): 200k world, mapped to the 4 expressible
    axes; sex is CANNOT_EXPRESS (independence with the supplied margin)."""
    from earth1.genesis import GENESIS_COUNTRY_CODES, genesis
    civ = genesis(200_000, 42)
    iso = {c: i for i, c in enumerate(GENESIS_COUNTRY_CODES)}
    years = 18.0 + np.asarray(civ.age) * 72.0
    band = np.digitize(years, [25, 35, 45, 55, 65])   # 0..5, ~X003R
    tabs = {}
    for a3, a2 in A3.items():
        if a2 not in iso:
            continue
        m = np.asarray(civ.country) == iso[a2]
        if m.sum() < 200:
            continue
        t = np.zeros((6, 3, 3, 2))
        np.add.at(t, (band[m], np.asarray(civ.education)[m],
                      np.asarray(civ.income)[m],
                      np.asarray(civ.urban)[m].astype(int)), 1.0)
        tabs[a3] = (t / t.sum()).tolist()
    json.dump(tabs, open(os.path.join(OUT, "genesis_4way.json"), "w"))
    print("GENESIS MAPPED", len(tabs), "countries (sex CANNOT_EXPRESS)")


def margins_of(t):
    return [t.sum(axis=tuple(j for j in range(5) if j != i))
            for i in range(5)]


def ipf(seed, margins, tol=1e-9, iters=2000):
    t = seed.copy() + 1e-12
    t /= t.sum()
    for _ in range(iters):
        for i, m in enumerate(margins):
            cur = t.sum(axis=tuple(j for j in range(5) if j != i))
            f = np.where(cur > 0, m / np.maximum(cur, 1e-300), 0.0)
            t *= np.expand_dims(f, [j for j in range(5) if j != i])
        errs = [np.abs(t.sum(axis=tuple(j for j in range(5) if j != i)) - m).max()
                for i, m in enumerate(margins)]
        if max(errs) < tol:
            break
    return t / t.sum(), max(errs)


def verify_margins(t, margins, label):
    for i, m in enumerate(margins):
        err = np.abs(t.sum(axis=tuple(j for j in range(5) if j != i)) - m).max()
        assert err <= 1e-6, f"{label}: margin {AXES[i]} err {err:.2e} > 1e-6"


def chained(pooled, margins):
    """M4: conditionals (Dirichlet 0.5 smoothing) chained in the frozen
    order sex -> age|sex -> edu|age,sex -> income|edu,age,sex ->
    urban|income,edu,age, then IPF to the supplied margins."""
    def cond(joint, given_axes, target_axis):
        keep = sorted(set(given_axes) | {target_axis})
        marg = pooled.sum(axis=tuple(j for j in range(5) if j not in keep))
        # reorder to (given..., target)
        order = [keep.index(a) for a in given_axes] + [keep.index(target_axis)]
        m = np.transpose(marg, order) + 0.5 / marg.size
        return m / m.sum(axis=-1, keepdims=True)
    p_sex = pooled.sum(axis=(1, 2, 3, 4))
    p_age = cond(pooled, [0], 1)               # age|sex
    p_edu = cond(pooled, [1, 0], 2)            # edu|age,sex
    p_inc = cond(pooled, [2, 1, 0], 3)         # income|edu,age,sex
    p_urb = cond(pooled, [3, 2, 1], 4)         # urban|income,edu,age
    t = np.zeros(SHAPE)
    for s, a, e, i, u in itertools.product(*map(range, SHAPE)):
        t[s, a, e, i, u] = (p_sex[s] * p_age[s, a] * p_edu[a, s, e]
                            * p_inc[e, a, s, i] * p_urb[i, e, a, u])
    t /= t.sum()
    out, _ = ipf(t, margins)
    return out


def mae_kway(truth, model, k):
    tot, cnt = 0.0, 0
    for axes in itertools.combinations(range(5), k):
        drop = tuple(j for j in range(5) if j not in axes)
        tt, mm = truth.sum(axis=drop), model.sum(axis=drop)
        tot += np.abs(tt - mm).sum() * 100.0
        cnt += tt.size
    return tot / cnt


def stage_run():
    rows = np.load(os.path.join(OUT, "rows.npz"))
    gen = json.load(open(os.path.join(OUT, "genesis_4way.json")))
    countries = sorted(rows.files)
    tables = {c: _cells(*(rows[c][:, i].astype(int) for i in range(5)),
                        rows[c][:, 5]) for c in countries}
    rng = np.random.default_rng(20260826)
    results = {}
    for held in countries:
        truth = tables[held]
        margins = margins_of(truth)                      # the ONLY thing supplied
        train = [c for c in countries if c != held]
        eq_pool = np.mean([tables[c] for c in train], axis=0)     # equal-country
        resp_pool = np.zeros(SHAPE)                               # respondent-pooled
        for c in train:
            r = rows[c]
            np.add.at(resp_pool, tuple(r[:, i].astype(int) for i in range(5)),
                      r[:, 5])
        resp_pool /= resp_pool.sum()

        m = {}
        m["M0_independence"] = np.einsum("a,b,c,d,e->abcde", *margins)
        if held in gen:
            g4 = np.array(gen[held])                     # age,edu,inc,urb
            m["M1_genesis"] = np.einsum("a,bcde->abcde", margins[0],
                                        g4 / g4.sum())
        m["M2_ipf_eqpool"], _ = ipf(eq_pool, margins)
        m["M3_greg_resppool"], _ = ipf(resp_pool, margins)
        m["M4_conditional"] = chained(eq_pool, margins)
        # broken-method KA (Standing Rule 2): shuffled M2 must lose to M0
        flat = m["M2_ipf_eqpool"].ravel().copy()
        rng_ka = np.random.default_rng(4242)
        rng_ka.shuffle(flat)
        m["KA_broken"] = flat.reshape(SHAPE)

        for name, t in m.items():
            if name in ("M0_independence", "KA_broken"):
                continue
            if name == "M1_genesis":
                # only the sex margin is supplied-by-construction; the
                # other four are genesis's own -> verify sex only
                np.testing.assert_allclose(t.sum(axis=(1, 2, 3, 4)),
                                           margins[0], atol=1e-6)
            else:
                verify_margins(t, margins, f"{held}:{name}")

        r = rows[held]
        n = len(r)
        res = {name: {"mae2": mae_kway(truth, t, 2),
                      "mae3": mae_kway(truth, t, 3)} for name, t in m.items()}
        boots = {name: {"mae2": [], "mae3": []} for name in m}
        for _ in range(NBOOT):
            idx = rng.integers(0, n, n)
            bt = _cells(*(r[idx, i].astype(int) for i in range(5)), r[idx, 5])
            for name, t in m.items():
                boots[name]["mae2"].append(mae_kway(bt, t, 2))
                boots[name]["mae3"].append(mae_kway(bt, t, 3))
        for name in m:
            for k in ("mae2", "mae3"):
                lo, hi = np.percentile(boots[name][k], [2.5, 97.5])
                res[name][f"{k}_ci"] = [round(float(lo), 4),
                                        round(float(hi), 4)]
        results[held] = {"n": n, **{name: {k: (round(v, 4)
                          if isinstance(v, float) else v)
                          for k, v in d.items()} for name, d in res.items()}}
        print("scored", held, "n=", n, flush=True)
    json.dump(results, open(os.path.join(OUT, "bakeoff_results.json"), "w"),
              indent=1)
    print("RUN COMPLETE", len(results), "countries")


if __name__ == "__main__":
    {"extract": stage_extract, "genesis_map": stage_genesis_map,
     "run": stage_run}[sys.argv[1]]()
