"""COLLECTIVE-GEO-1 known-answer battery (frozen:
ops/alive/COLLECTIVE_GEO_1.md). Any required failure => VOID."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = Path(os.environ.get("EARTH1_PF_OUT",
                          str(ROOT / "data" / "geo1")))
N = int(os.environ.get("EARTH1_GEO1_N", "20000"))
REF = dict(ds=0.0, pol=0.3998, sn=0.2855, bel=0.6416)


def build():
    os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
    from earth1.alive import birth_world
    return birth_world(N, 424243)


def _set_reference(w, i):
    """Force agent set i into the exact reference state."""
    life, fl = w.life, w.flourishing
    life.deprivation[:] = 0.0            # => ds = 0 = REF_DS everywhere
    life.political[i] = REF["pol"]
    life.social_need[i] = REF["sn"]
    life.addiction[i] = 0.0
    fl.belonging[i] = REF["bel"]


def target_col(w):
    import earth1.field_lab as flab
    import earth1.life as lifemod
    flab.FLOUR_REF[0] = w.flourishing
    t = flab.flourishing_level_map(lifemod.life_force_target)(
        w.civ, w.life)
    return t[:, 3]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    w = build()
    i = np.arange(w.civ.n)
    _set_reference(w, i)
    B = w.life.force_baseline[:, 3]
    T = target_col(w)
    interior = (B > 0.02) & (B < 0.98)
    err = float(np.abs(T[interior] - B[interior]).max())
    res["KA1_neutral_T_equals_B"] = {"max_err": err,
                                     "pass": err < 1e-12}

    # KA2/KA3: per-modifier monotonicity + exact slopes at reference
    slopes = {"political": ("political", 0.25),
              "social_need": ("social_need", -0.20),
              "belonging": ("belonging", 0.20)}
    ka3 = {}
    delta = 0.05
    for name, (attr, slope) in slopes.items():
        w2 = build()
        _set_reference(w2, np.arange(w2.civ.n))
        T0 = target_col(w2)
        if attr == "belonging":
            w2.flourishing.belonging[:] += delta
        else:
            getattr(w2.life, attr)[:] = getattr(
                w2.life, attr) + delta
        T1 = target_col(w2)
        d = T1 - T0
        m = (T0 > 0.05) & (T0 < 0.90) & (T1 > 0.05) & (T1 < 0.90)
        worst = float(np.abs(d[m] - slope * delta).max())
        ka3[name] = {"expected": slope * delta,
                     "got_mean": round(float(d[m].mean()), 6),
                     "max_err": worst,
                     "mono_ok": bool(np.sign(d[m].mean())
                                     == np.sign(slope)),
                     "pass": worst < 1e-12}
    # ds slope: raise dep uniformly so ds = dep*shared moves
    w2 = build()
    _set_reference(w2, np.arange(w2.civ.n))
    T0 = target_col(w2)
    w2.life.deprivation[:] = 0.3         # uniform => shared = 0.3
    T1 = target_col(w2)
    dsv = 0.3 * 0.3
    d = T1 - T0
    m = (T0 > 0.05) & (T0 < 0.85) & (T1 > 0.05) & (T1 < 0.85)
    # dep also moves ECONOMICS/FEAR targets; COLLECTIVE row isolated
    worst = float(np.abs(d[m] - 0.40 * dsv).max())
    ka3["ds"] = {"expected": 0.40 * dsv, "max_err": worst,
                 "pass": worst < 1e-9}
    res["KA2_KA3_slopes"] = ka3

    # KA4: other agents' state does not move my constants
    w3 = build()
    _set_reference(w3, np.arange(w3.civ.n))
    keep = 7
    T0 = target_col(w3)[keep]
    w3.life.political[:] = 0.9
    w3.life.political[keep] = REF["pol"]
    w3.flourishing.belonging[:] = 0.9
    w3.flourishing.belonging[keep] = REF["bel"]
    T1 = target_col(w3)[keep]
    res["KA4_no_dynamic_centering"] = {
        "delta": float(abs(T1 - T0)), "pass": abs(T1 - T0) < 1e-12}

    # KA5: seven other force rows bit-identical flag on/off
    w4 = build()
    on = target_all(w4, True)
    off = target_all(w4, False)
    other = [k for k in range(8) if k != 3]
    same = all(np.array_equal(on[:, k], off[:, k]) for k in other)
    res["KA5_other_forces_untouched"] = {"pass": bool(same)}

    ok = (res["KA1_neutral_T_equals_B"]["pass"]
          and all(v["pass"] for v in ka3.values())
          and res["KA4_no_dynamic_centering"]["pass"]
          and res["KA5_other_forces_untouched"]["pass"])
    res["verdict"] = "ALL_KA_PASS" if ok else "VOID"
    (OUT / "geo1_ka.json").write_text(json.dumps(res, indent=1,
                                               default=bool))
    print(json.dumps(res, indent=1, default=bool))


def target_all(w, flag):
    import earth1.field_lab as flab
    import earth1.life as lifemod
    os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1" if flag else "0"
    flab.FLOUR_REF[0] = w.flourishing
    t = flab.flourishing_level_map(lifemod.life_force_target)(
        w.civ, w.life)
    os.environ["EARTH1_COLLECTIVE_CENTERED"] = "1"
    return t


if __name__ == "__main__":
    main()
