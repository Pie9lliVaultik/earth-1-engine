"""PF-DECAY-1 known-answer battery (frozen registration:
ops/alive/PF_DECAY_1.md). Conformance KAs for the restored
decay_half_life contract. NO parameter tuning. Any required KA
failure => VOID (fix implementation only, never the contract).

Arms:
  UNIT     KA1/KA6/KA7/expiry/clip on the pure recovered-law function
  KA0      flag-off continuity: it6 ALL @8890 == recorded metrics
  KA2LEVEL planted residue, stripped paired worlds: exact relax
           recursion + envelope bound + revert (level semantics)
  KA2PLANT planted INTEGRATOR through the same instrument: must be
           DETECTED (discrimination gate, Standing Rule 2)
  KA6LOOP  h<=0 residue in-loop: permanent constant level
  KA3      cooldown semantics: clamped-hot locality fires at
           {d0, d0+14, d0+28} exactly (strict-<)
  KA4      locality independence: staggered second locality fires on
           its own schedule
  KA5      restart continuity: save/load mid-decay, identical
           trajectory + residue + cooldown state
"""
import copy
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

N = int(os.environ.get("EARTH1_PF_N", "200000"))
SEED = 8890          # continuity seed (KA0 + semantic KAs; nothing scored)
OUT = Path(os.environ.get("EARTH1_PF_OUT", str(ROOT / "data" / "pf_decay")))
FEAR = 0
TOL = 1e-12


# ── pure-law unit battery ───────────────────────────────────────────
def arm_unit():
    from earth1.alive import cascade_residue_levels
    A = np.zeros(8); A[FEAR] = 0.10; A[3] = -0.08
    checks = {}
    # KA1: analytic grid, incl. L(0)=A, L(h)=A/2, L(2h)=A/4
    res = [{"rule": "r", "loc": 7, "day": 100, "effects": A, "h": 45.0}]
    worst = 0.0
    for dt in [0, 1, 3, 22, 45, 90, 135, 149]:
        lv, _ = cascade_residue_levels(res, 100 + dt)
        exp = A * 2.0 ** (-dt / 45.0)
        worst = max(worst, float(np.abs(lv[0][1] - exp).max()))
    checks["ka1_max_abs_err"] = worst
    checks["ka1_pass"] = bool(worst < TOL)
    # expiry: active iff factor>=0.01 AND max|A|*factor>=0.01;
    # max|A|=0.10 => drops when factor<0.1 => dt > 45*log2(10)=149.5
    lv149, _ = cascade_residue_levels(res, 100 + 149)
    lv150, sv150 = cascade_residue_levels(res, 100 + 150)
    checks["expiry_active_at_149"] = bool(len(lv149) == 1)
    checks["expiry_gone_at_150"] = bool(len(lv150) == 0 and not sv150)
    checks["expiry_pass"] = (checks["expiry_active_at_149"]
                             and checks["expiry_gone_at_150"])
    # KA6: h<=0 => permanent factor 1.0 (never expires)
    lv, sv = cascade_residue_levels(
        [{"rule": "r", "loc": 1, "day": 0, "effects": A, "h": 0.0}],
        10 ** 6)
    checks["ka6_pass"] = bool(len(lv) == 1 and len(sv) == 1
                              and np.array_equal(lv[0][1], A))
    # KA7: signed symmetric
    lvp, _ = cascade_residue_levels(
        [{"rule": "r", "loc": 1, "day": 0, "effects": A, "h": 45.0}], 45)
    lvn, _ = cascade_residue_levels(
        [{"rule": "r", "loc": 1, "day": 0, "effects": -A, "h": 45.0}], 45)
    checks["ka7_pass"] = bool(
        np.abs(lvp[0][1] + lvn[0][1]).max() < TOL
        and abs(lvp[0][1][FEAR] - 0.05) < TOL)
    checks["arm"] = "UNIT"
    checks["pass"] = all(checks[k] for k in
                         ("ka1_pass", "expiry_pass", "ka6_pass",
                          "ka7_pass"))
    return checks


# ── KA0: flag-off continuity through the it6 engine ─────────────────
def arm_ka0():
    os.environ.pop("EARTH1_DECAY_RESIDUE", None)
    sys.path.insert(0, str(ROOT / "scripts"))
    import it6_dyadic as it6
    got = json.loads(json.dumps(it6.run_arm("ALL")))  # normalize keys
    rec = [x for x in json.load(open(ROOT / "data" / "it6_dyadic" /
                                     "arms.json"))
           if x.get("arm") == "ALL"][0]
    same_panels = got["panels"] == rec["panels"]
    same_tau = got["tau"] == rec["tau"]
    same_trans = got["transmission"] == rec["transmission"]
    return {"arm": "KA0", "same_panels": bool(same_panels),
            "same_tau": bool(same_tau),
            "same_transmission": bool(same_trans),
            "got_tau": got["tau"], "rec_tau": rec["tau"],
            "got_sat120": got["panels"]["120"]["sat_max"],
            "pass": bool(same_panels and same_tau and same_trans)}


# ── stripped world: the residue is the ONLY force writer ────────────
def _stripped(seed, rules_off=False):
    os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    os.environ["EARTH1_DECAY_RESIDUE"] = "1"
    import earth1.alive as am
    if rules_off:
        # KA2/KA6 test the residue APPLICATION in isolation; the
        # detector is exercised by KA3/KA4. Natural firings would
        # contaminate the paired-Δ instrument in both worlds.
        import earth1.thresholds as th
        th.TRANSITION_RULES = []
    import earth1.institutions as inst
    import earth1.health as health
    import earth1.life as lifemod
    import earth1.knowledge as kn
    import earth1.flourishing as flmod
    import earth1.plasticity as plast
    w = am.birth_world(N, seed)
    w.presence = None
    w.mobility = None
    w.feed = None
    w.climate = None
    am.propagate = lambda forces, alpha, adj, **kw: forces
    am.update_conviction = lambda forces, alpha, adj: alpha
    am._be_born = lambda *a, **k: {}
    inst.govern = lambda *a, **k: {}
    inst.apply_policy_and_war = lambda *a, **k: {}
    inst.class_tick = lambda *a, **k: {}
    health.health_tick = lambda *a, **k: {}
    lifemod.life_tick = lambda *a, **k: {}
    kn.knowledge_tick = lambda *a, **k: {}
    flmod.flourishing_tick = lambda *a, **k: {}
    plast.plasticity_tick = lambda *a, **k: {}
    return am, w


def _biggest_locality(w):
    civ = w.civ
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2
           + civ.urban.astype(np.int64))
    alive_idx = np.flatnonzero(w.health.alive)
    vals, counts = np.unique(loc[alive_idx], return_counts=True)
    big = int(vals[np.argmax(counts)])
    cohort = alive_idx[loc[alive_idx] == big]
    return loc, big, cohort


RELAX = 0.045
A_KA2 = 0.10
H_KA2 = 45.0


def _interior_channel(w, cohort, amp):
    """Pick the channel where cohort targets +amp stay strictly
    interior — the exactness instrument must not engage the [0,1]
    target clip (clipping is real contract behavior; KA2/KA6 isolate
    the unclipped law). Returns (channel, clip_frac)."""
    from earth1.life import life_force_target
    t = life_force_target(w.civ, w.life)[cohort]
    fracs = [(float(((t[:, c] + amp > 0.98)
                     | (t[:, c] + amp < 0.02)).mean()), c)
             for c in range(8)]
    f, c = min(fracs)
    return c, f


def _ka2_run(mode):
    """mode 'level': planted residue (production path).
    mode 'integrator': the planted WRONG law F += L(t) daily, residue
    path off — same instrument must detect the difference."""
    am, w = _stripped(SEED, rules_off=True)
    rng = np.random.default_rng(SEED)
    for _ in range(10):                      # settle a few days
        am.live_one_day(w, rng, relax=RELAX)
    wc = copy.deepcopy(w)
    rngc = np.random.default_rng()
    rngc.bit_generator.state = rng.bit_generator.state

    loc, big, cohort = _biggest_locality(w)
    ch, clip_frac = _interior_channel(w, cohort, A_KA2)
    d0 = int(w.day)
    eff = np.zeros(8); eff[ch] = A_KA2
    if mode == "level":
        w.chronicle.cascade_residues = [
            {"rule": "ka2", "loc": big, "day": d0, "effects": eff,
             "h": H_KA2}]
    series = []
    delta_prev = 0.0
    worst_rec = 0.0
    for d in range(1, 231):
        am.live_one_day(w, rng, relax=RELAX)
        am.live_one_day(wc, rngc, relax=RELAX)
        if mode == "integrator":
            dt = (w.day - 1) - d0     # same clock the level sees
            L = A_KA2 * 2.0 ** (-dt / H_KA2)
            if L >= 0.01:             # same expiry as the contract
                w.civ.forces[cohort, ch] = np.clip(
                    w.civ.forces[cohort, ch] + L, 0, 1)
        delta = float(w.civ.forces[cohort, ch].mean()
                      - wc.civ.forces[cohort, ch].mean())
        dt = (w.day - 1) - d0         # day at which target was read
        L = A_KA2 * 2.0 ** (-dt / H_KA2)
        L_active = L if (L >= 0.01) else 0.0
        # exact level recursion: D_t = (1-r) D_{t-1} + r L(t) — the
        # discriminating instrument, computed identically in BOTH
        # modes: the true level satisfies it to machine precision, an
        # integrator cannot.
        pred = (1 - RELAX) * delta_prev + RELAX * L_active
        worst_rec = max(worst_rec, abs(delta - pred))
        delta_prev = delta
        if d % 5 == 0 or d <= 3:
            series.append({"day": d, "delta": round(delta, 6),
                           "L": round(L_active, 6)})
    peak = max(abs(s["delta"]) for s in series)
    final = abs(series[-1]["delta"])
    return {"mode": mode, "series": series, "channel": int(ch),
            "channel_clip_frac": clip_frac,
            "peak_delta": round(peak, 6),
            "final_delta": round(final, 6),
            "recursion_max_err": worst_rec,
            "envelope_bound": A_KA2}


def arm_ka2level():
    r = _ka2_run("level")
    # hard gates: exact recursion; peak bounded by envelope; reverts
    ok = (r["recursion_max_err"] < 1e-9
          and r["peak_delta"] <= A_KA2 + 1e-6
          and r["final_delta"] < 1e-3)
    r.update({"arm": "KA2LEVEL", "pass": bool(ok)})
    return r


def arm_ka2plant():
    r = _ka2_run("integrator")
    # the instrument must DETECT the wrong law. Reversion is NOT a
    # discriminator (relax pulls even an accumulator back once input
    # stops); the level recursion and the envelope bound are: a true
    # level satisfies the recursion at ~1e-16 and never exceeds max L.
    detected = (r["peak_delta"] > A_KA2 * 2.0
                and r["recursion_max_err"] > 1e-3)
    r.update({"arm": "KA2PLANT", "detected": bool(detected),
              "pass": bool(detected)})
    return r


def arm_ka6loop():
    am, w = _stripped(SEED, rules_off=True)
    rng = np.random.default_rng(SEED)
    for _ in range(10):
        am.live_one_day(w, rng, relax=RELAX)
    wc = copy.deepcopy(w)
    rngc = np.random.default_rng()
    rngc.bit_generator.state = rng.bit_generator.state
    loc, big, cohort = _biggest_locality(w)
    ch, clip_frac = _interior_channel(w, cohort, A_KA2)
    eff = np.zeros(8); eff[ch] = A_KA2
    w.chronicle.cascade_residues = [
        {"rule": "ka6", "loc": big, "day": int(w.day), "effects": eff,
         "h": 0.0}]
    deltas = []
    for d in range(1, 121):
        am.live_one_day(w, rng, relax=RELAX)
        am.live_one_day(wc, rngc, relax=RELAX)
        deltas.append(float(w.civ.forces[cohort, ch].mean()
                            - wc.civ.forces[cohort, ch].mean()))
    # permanent level: displacement converges to A and STAYS
    tail = deltas[-30:]
    ok = (abs(np.mean(tail) - A_KA2) < 5e-3
          and np.std(tail) < 1e-3
          and len(w.chronicle.cascade_residues) == 1)  # never expires
    return {"arm": "KA6LOOP", "tail_mean": round(float(np.mean(tail)), 5),
            "tail_std": round(float(np.std(tail)), 6),
            "channel": int(ch), "channel_clip_frac": clip_frac,
            "still_active": len(w.chronicle.cascade_residues),
            "pass": bool(ok)}


def _clamp(civ, cohort):
    civ.forces[cohort, 2] = 0.20      # ECONOMICS < 0.3
    civ.forces[cohort, FEAR] = 0.60   # FEAR > 0.5


def arm_ka3():
    am, w = _stripped(SEED)
    from earth1.types import Force
    assert int(Force.ECONOMICS) == 2 and int(Force.FEAR) == 0
    rng = np.random.default_rng(SEED)
    loc, big, cohort = _biggest_locality(w)
    d0 = None
    fires = []
    for d in range(1, 33):
        _clamp(w.civ, cohort)
        am.live_one_day(w, rng, relax=RELAX)
        res = [r for r in getattr(w.chronicle, "cascade_residues", [])
               or [] if r["rule"] == "panic_cascade"
               and r["loc"] == big]
        days = sorted({r["day"] for r in res})
        # also read the cooldown map (residues may expire; map does not)
        lf = {k: v for k, v in
              (w.chronicle.cascade_last_fired or {}).items()
              if k[0] == "panic_cascade" and k[1] == big}
        fires = days
    d0 = fires[0] if fires else None
    expected = [d0, d0 + 14, d0 + 28] if d0 is not None else None
    ok = (d0 is not None and fires == expected)
    return {"arm": "KA3", "fire_days": fires, "expected": expected,
            "pass": bool(ok)}


def arm_ka4():
    am, w = _stripped(SEED)
    rng = np.random.default_rng(SEED)
    civ = w.civ
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2
           + civ.urban.astype(np.int64))
    alive_idx = np.flatnonzero(w.health.alive)
    vals, counts = np.unique(loc[alive_idx], return_counts=True)
    order = np.argsort(counts)[::-1]
    bigX, bigY = int(vals[order[0]]), int(vals[order[1]])
    cohX = alive_idx[loc[alive_idx] == bigX]
    cohY = alive_idx[loc[alive_idx] == bigY]
    for d in range(1, 13):
        _clamp(civ, cohX)
        if d >= 6:
            _clamp(civ, cohY)
        am.live_one_day(w, rng, relax=RELAX)
    res = getattr(w.chronicle, "cascade_residues", []) or []
    dX = sorted({r["day"] for r in res
                 if r["rule"] == "panic_cascade" and r["loc"] == bigX})
    dY = sorted({r["day"] for r in res
                 if r["rule"] == "panic_cascade" and r["loc"] == bigY})
    # Y must fire on its first hot day even though X is mid-cooldown
    ok = (len(dX) == 1 and len(dY) == 1 and dY[0] == dX[0] + 5)
    return {"arm": "KA4", "x_fire_days": dX, "y_fire_days": dY,
            "pass": bool(ok)}


def arm_ka5():
    """FULL world (the serializer's completeness policy is part of the
    contract): planted residue + any natural firings must all restart
    exactly through the canonical save/load."""
    from earth1.persistence import save_world, load_world
    os.environ["EARTH1_CASCADE_COOLDOWN"] = "1"
    os.environ["EARTH1_DECAY_RESIDUE"] = "1"
    import earth1.alive as am
    w = am.birth_world(N, SEED)
    rng = np.random.default_rng(SEED)
    loc, big, cohort = _biggest_locality(w)
    eff = np.zeros(8); eff[FEAR] = A_KA2
    for d in range(1, 6):
        am.live_one_day(w, rng, relax=RELAX)
    if getattr(w.chronicle, "cascade_residues", None) is None:
        w.chronicle.cascade_residues = []
    w.chronicle.cascade_residues.append(
        {"rule": "ka5", "loc": big, "day": int(w.day), "effects": eff,
         "h": H_KA2})
    w.chronicle.cascade_last_fired[("ka5", big)] = int(w.day)
    for d in range(1, 21):                      # mid-decay
        am.live_one_day(w, rng, relax=RELAX)
    path = OUT / "ka5_world.pkl"
    save_world(w, path, rng=rng)
    w2, rng_state, _info = load_world(path)
    rng2 = np.random.default_rng()
    rng2.bit_generator.state = rng_state
    res1 = w.chronicle.cascade_residues
    res2 = w2.chronicle.cascade_residues
    same_state = (len(res1) == len(res2)
                  and all(a["day"] == b["day"] and a["h"] == b["h"]
                          and a["loc"] == b["loc"]
                          and np.array_equal(a["effects"], b["effects"])
                          for a, b in zip(res1, res2))
                  and w.chronicle.cascade_last_fired
                  == w2.chronicle.cascade_last_fired
                  and w.day == w2.day)
    for d in range(1, 21):
        am.live_one_day(w, rng, relax=RELAX)
        am.live_one_day(w2, rng2, relax=RELAX)
    same_traj = bool(np.array_equal(w.civ.forces, w2.civ.forces))
    same_res = (len(w.chronicle.cascade_residues)
                == len(w2.chronicle.cascade_residues))
    return {"arm": "KA5", "same_state": bool(same_state),
            "same_trajectory_20d": same_traj,
            "same_residue_count": bool(same_res),
            "pass": bool(same_state and same_traj and same_res)}


ARMS = {"UNIT": arm_unit, "KA0": arm_ka0, "KA2LEVEL": arm_ka2level,
        "KA2PLANT": arm_ka2plant, "KA6LOOP": arm_ka6loop,
        "KA3": arm_ka3, "KA4": arm_ka4, "KA5": arm_ka5}


def _worker(name):
    try:
        r = ARMS[name]()
        r.setdefault("arm", name)
        return r
    except Exception as e:
        import traceback
        return {"arm": name, "pass": False, "error": str(e),
                "trace": traceback.format_exc()[-2000:]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = list(ARMS)
    sel = os.environ.get("EARTH1_PF_ARMS")
    if sel:
        names = [a for a in sel.split(",") if a in ARMS]
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(len(names), 8), maxtasksperchild=1) as pool:
        results = pool.map(_worker, names)
    verdict = ("ALL_KA_PASS" if all(r.get("pass") for r in results)
               else "VOID")
    out = {"verdict": verdict, "results": results}
    (OUT / "ka.json").write_text(json.dumps(out, indent=1))
    for r in results:
        print(r["arm"], "PASS" if r.get("pass") else
              "FAIL " + str(r.get("error", ""))[:200])
    print(verdict)


if __name__ == "__main__":
    main()
