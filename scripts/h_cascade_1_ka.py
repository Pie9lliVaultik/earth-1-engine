"""H-CASCADE-1 semantic KA battery (frozen: ops/alive/H_CASCADE_1.md §5).

Planting harness: stripped world (dynamics stubbed as in pf_decay_ka),
the biggest locality's cohort is clamped HOT (FEAR=COLLECTIVE=1.0) or
COLD (FEAR=0.0) at the start of every day, so the predicate trajectory
of that locality is exactly controlled. Firings are read from the
chronicle residues of the scoped rules in that locality.
"""
import copy, json, os, sys
from pathlib import Path
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
N = int(os.environ.get("EARTH1_PF_N", "20000"))
SEED = 8890
OUT = Path(os.environ.get("EARTH1_HC1_OUT", str(ROOT / "data" / "h_cascade_1")))
RULES = ("identity_collapse", "collective_surge")
RELAX = 0.045
from pf_decay_ka import _stripped, _biggest_locality   # noqa: E402


def _hot(civ, cohort):
    civ.forces[cohort, 0] = 1.0; civ.forces[cohort, 3] = 1.0


def _cold(civ, cohort):
    civ.forces[cohort, 0] = 0.0


def _fires(w, loc):
    out = {}
    for r in RULES:
        out[r] = sorted(x["day"] for x in (getattr(w.chronicle, "cascade_residues", None) or [])
                        if x["rule"] == r and x["loc"] == loc)
    return out


def _lastfired(w, loc):
    return {r: (w.chronicle.cascade_last_fired or {}).get((r, loc)) for r in RULES}


_SEEN = {}   # id(world) -> {rule: set(fire days)}, cumulative (residues expire)


def _run(w, am, rng, cohort, schedule, loc=None):
    """schedule: list of 'H'/'C' per day. Records every firing day of the
    scoped rules in `loc` as it happens (residues expire; the record
    must not)."""
    rec = _SEEN.setdefault(id(w), {r: set() for r in RULES})
    for s in schedule:
        (_hot if s == "H" else _cold)(w.civ, cohort)
        am.live_one_day(w, rng, relax=RELAX)
        if loc is not None:
            for r, days in _fires(w, loc).items():
                rec[r].update(days)


def _seen(w):
    return {r: sorted(v) for r, v in _SEEN.get(id(w), {r: set() for r in RULES}).items()}


def _fresh_cold(seed=SEED):
    """World with episode state established (one cold step) so the
    initialization rule (KA4) is not what the other KAs measure."""
    am, w = _stripped(seed)
    rng = np.random.default_rng(seed)
    _, big, cohort = _biggest_locality(w)
    _run(w, am, rng, cohort, "C")
    return am, w, rng, big, cohort


def arm_ka1():
    am, w, rng, big, cohort = _fresh_cold()
    _run(w, am, rng, cohort, "H" * 340, loc=big)      # >10 cooldowns of 30d
    f = _seen(w)
    ok = all(len(f[r]) == 1 for r in RULES)
    # cooldown map: last_fired may predate residue expiry; fires read from
    # last_fired must also show a single entry day
    return {"arm": "KA1", "fires": f, "last_fired": _lastfired(w, big), "pass": bool(ok)}


def arm_ka2():
    am, w, rng, big, cohort = _fresh_cold()
    _run(w, am, rng, cohort, "H" * 5 + "C" * 40 + "H" * 5)
    f = _fires(w, big)
    ok = all(len(f[r]) == 2 and f[r][1] - f[r][0] == 45 for r in RULES)
    return {"arm": "KA2", "fires": f, "pass": bool(ok)}


def arm_ka2b():
    """Recurrence BLOCKED by the retained cooldown: cold→hot→cold→hot
    with the re-entry inside the cooldown → 1 firing (episode opens, no
    event)."""
    am, w, rng, big, cohort = _fresh_cold()
    _run(w, am, rng, cohort, "H" * 3 + "C" * 5 + "H" * 3)
    f = _fires(w, big)
    ok = all(len(f[r]) == 1 for r in RULES)
    return {"arm": "KA2b", "fires": f, "pass": bool(ok)}


def arm_ka3():
    am, w, rng, big, cohort = _fresh_cold()
    _run(w, am, rng, cohort, "H" * 95)       # 3 cooldowns of 30 (and >4 of 20)
    f = _fires(w, big)
    ok = all(len(f[r]) == 1 for r in RULES)
    return {"arm": "KA3", "fires": f, "pass": bool(ok)}


def arm_ka4():
    am, w = _stripped(SEED)
    rng = np.random.default_rng(SEED)
    _, big, cohort = _biggest_locality(w)
    assert getattr(w.chronicle, "cascade_episode_active", None) is None
    _run(w, am, rng, cohort, "H" * 40)       # already hot at init, stays hot
    f = _fires(w, big)
    ep = w.chronicle.cascade_episode_active
    ok = all(len(f[r]) == 0 and (r, big) in ep for r in RULES)
    # then a genuine exit/re-entry must still be detected
    _run(w, am, rng, cohort, "C" * 3 + "H" * 3)
    f2 = _fires(w, big)
    ok = ok and all(len(f2[r]) == 1 for r in RULES)
    return {"arm": "KA4", "fires_while_init_hot": f, "fires_after_reentry": f2, "pass": bool(ok)}


def arm_ka5():
    from earth1.persistence import save_world, load_world
    # FULL world: the serializer's completeness policy is part of the
    # contract (a stripped world is refused at load).
    import earth1.alive as am
    w = am.birth_world(N, SEED); rng = np.random.default_rng(SEED)
    _, big, cohort = _biggest_locality(w)
    _run(w, am, rng, cohort, "C" + "H" * 10)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "ka5_world.pkl"
    save_world(w, p, rng=rng)
    twin = copy.deepcopy(w); rng_t = copy.deepcopy(rng)
    w2, rs, _ = load_world(p)
    from earth1.persistence import rng_from_state
    rng2 = rng_from_state(rs)
    _, big2, cohort2 = _biggest_locality(w2)
    before = _fires(w2, big2)
    _run(w2, am, rng2, cohort2, "H" * 100)
    _run(twin, am, rng_t, cohort, "H" * 100)
    f2, ft = _fires(w2, big2), _fires(twin, big)
    same_res = len(w2.chronicle.cascade_residues) == len(twin.chronicle.cascade_residues) and all(
        a["rule"] == b["rule"] and a["loc"] == b["loc"] and a["day"] == b["day"]
        and np.array_equal(a["effects"], b["effects"])
        for a, b in zip(w2.chronicle.cascade_residues, twin.chronicle.cascade_residues))
    # residues expire (h=30, A=0.10 -> ~100d), so the duplicate check
    # reads the never-expiring cooldown map: one entry day, unchanged.
    lf_before, lf2, lft = _lastfired(w, big), _lastfired(w2, big2), _lastfired(twin, big)
    ok = (big2 == big and lf2 == lf_before and lf2 == lft and f2 == ft and same_res
          and w2.chronicle.cascade_episode_active == twin.chronicle.cascade_episode_active)
    return {"arm": "KA5", "fires_before_save": before, "last_fired_before": lf_before,
            "last_fired_restored": lf2, "last_fired_twin": lft,
            "residues_restored_vs_twin_identical": bool(same_res), "pass": bool(ok)}


def arm_ka6():
    am, w, rng, big, cohort = _fresh_cold()
    _run(w, am, rng, cohort, "H" * 10)
    clone = copy.deepcopy(w); rng_c = copy.deepcopy(rng)
    same_state = clone.chronicle.cascade_episode_active == w.chronicle.cascade_episode_active
    before = _fires(clone, big)
    _run(clone, am, rng_c, cohort, "H" * 60)
    f = _fires(clone, big)
    ok = same_state and f == before
    return {"arm": "KA6", "state_equal": bool(same_state), "fires_before": before,
            "fires_clone_after_60_hot": f, "pass": bool(ok)}


def arm_ka7():
    """Non-scoped rule (panic_cascade: ECON<0.3 ∧ FEAR>0.5) keeps
    cooldown-repeat firing: clamped-hot locality fires at d0, d0+14,
    d0+28 (the PF-DECAY KA3 contract, verbatim)."""
    am, w = _stripped(SEED)
    rng = np.random.default_rng(SEED)
    _, big, cohort = _biggest_locality(w)
    for d in range(1, 33):
        w.civ.forces[cohort, 0] = 1.0; w.civ.forces[cohort, 2] = 0.0
        am.live_one_day(w, rng, relax=RELAX)
    days = sorted({r["day"] for r in (w.chronicle.cascade_residues or [])
                   if r["rule"] == "panic_cascade" and r["loc"] == big})
    ok = len(days) == 3 and days[1] - days[0] == 14 and days[2] - days[1] == 14
    return {"arm": "KA7", "panic_fire_days": days, "pass": bool(ok)}


def arm_ka8():
    """Stored forces bit-identical between H-CASCADE-1 and the incumbent
    cooldown-only semantics (scope emptied) on the FULL canonical loop."""
    import earth1.alive as am
    from earth1.persistence import world_hash
    hashes = {}
    for tag, scope in (("h_cascade_1", am.EPISODE_ENTRY_RULES), ("incumbent", frozenset())):
        am.EPISODE_ENTRY_RULES = scope
        w = am.birth_world(N, SEED); rng = np.random.default_rng(SEED)
        tr = []
        for d in range(30):
            am.live_one_day(w, rng)
            tr.append((world_hash(w), int(np.asarray(w.civ.forces).view(np.uint8).sum())))
        hashes[tag] = {"world_hash_d30": tr[-1][0], "forces_bytes_sum_per_day": [t[1] for t in tr],
                       "world_hash_per_day": [t[0] for t in tr],
                       "fires_scoped": sum(1 for r in (w.chronicle.cascade_residues or []) if r["rule"] in RULES)}
    ok = hashes["h_cascade_1"]["world_hash_per_day"] == hashes["incumbent"]["world_hash_per_day"]
    return {"arm": "KA8", "hash_identical_30d": bool(ok),
            "fires_scoped_h1": hashes["h_cascade_1"]["fires_scoped"],
            "fires_scoped_incumbent": hashes["incumbent"]["fires_scoped"],
            "detector_differs": hashes["h_cascade_1"]["fires_scoped"] != hashes["incumbent"]["fires_scoped"],
            "pass": bool(ok)}


ARMS = {"KA1": arm_ka1, "KA2": arm_ka2, "KA2b": arm_ka2b, "KA3": arm_ka3, "KA4": arm_ka4,
        "KA5": arm_ka5, "KA6": arm_ka6, "KA7": arm_ka7, "KA8": arm_ka8}

if __name__ == "__main__":
    import multiprocessing as mp
    names = sys.argv[1:] or list(ARMS)
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for n in names:          # separate processes: each arm monkeypatches
        q = mp.get_context("spawn").Pool(1)
        r = q.apply(ARMS[n]); q.close()
        results.append(r); print(n, "PASS" if r["pass"] else "FAIL", json.dumps({k: v for k, v in r.items() if k not in ("arm", "pass")})[:400], flush=True)
    json.dump(results, open(OUT / "ka_results.json", "w"), indent=1)
    print("ALL PASS" if all(r["pass"] for r in results) else "SOME FAIL")
