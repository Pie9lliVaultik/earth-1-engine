"""SBI synthetic-twin theta surface (THREE_TRACK_PREREG_v1 A1).

Six calibratable parameters, injected process-locally by the harness:
kwargs for the two live_one_day parameters, module-constant override for
the four hoisted constants (commit 'Hoist 4 theta loci': trajectory-hash
proven behavior-identical at canonical values). Canonical physics files
are never edited by this harness.
"""
import numpy as np

THETA = [
    # name, canonical, low, high, log?
    ("relax",                   0.045, 0.015, 0.135, False),
    ("critical_fraction",       0.12,  0.06,  0.24,  False),
    ("conviction_gain_dyadic",  0.003, 0.001, 0.009, True),
    ("memory_press",            0.02,  0.005, 0.08,  True),
    ("hardship_mortality_gain", 1.0,   0.33,  3.0,   True),
    ("informal_floor_scale",    1.0,   0.5,   1.3,   False),
]
NAMES = [t[0] for t in THETA]
CANONICAL = {t[0]: t[1] for t in THETA}


def prior_ppf(name: str, q: float) -> float:
    _, _, lo, hi, log = next(t for t in THETA if t[0] == name)
    if log:
        return float(np.exp(np.log(lo) + q * (np.log(hi) - np.log(lo))))
    return float(lo + q * (hi - lo))


def sample_prior(rng: np.random.Generator, n: int) -> list:
    out = []
    for _ in range(n):
        out.append({name: prior_ppf(name, float(rng.random()))
                    for name in NAMES})
    return out


def apply_theta(theta: dict) -> dict:
    """Patch the four module constants (process-local) and return the
    kwargs for live_one_day. Call once per process, before any tick."""
    import earth1.health as health
    import earth1.influence as influence
    import earth1.life as life
    import earth1.memory as memory
    influence.CONVICTION_GAIN_DYADIC = float(theta["conviction_gain_dyadic"])
    memory.PRESS = float(theta["memory_press"])
    health.HARDSHIP_GAIN = float(theta["hardship_mortality_gain"])
    life.INFORMAL_SCALE = float(theta["informal_floor_scale"])
    return {"relax": float(theta["relax"]),
            "critical_fraction": float(theta["critical_fraction"])}


CUM_KEYS = ("deaths", "births", "disease_deaths", "rehomed_migrants",
            "rehomed_workers", "cascades_fired", "firms_failed")


PROBE_DAY = 10   # amendment A4.1: registered observation probe


def _inject_probe(w):
    """One registered memory so memory_press is observable (A4.1).
    theta-independent, deterministic, identical across configs/seeds."""
    from earth1.memory import Memory
    w.chronicle.events.append(Memory(
        id="obs_probe", label="obs_probe", day=float(w.day),
        force_signature=np.full(8, 0.06),
        scope=w.health.alive.copy(), salience=0.8, half_life=180.0))


def run_days(w, rng, days: int, kw: dict) -> list:
    """Run and observe. Returns the list of daily observables dicts."""
    from earth1.alive import live_one_day
    from earth1.observables import collect
    cum = {k: 0 for k in CUM_KEYS}
    daily = []
    for d in range(days):
        if d == PROBE_DAY:
            _inject_probe(w)
        st = live_one_day(w, rng, **kw)
        for k in CUM_KEYS:
            cum[k] += int(st.get(k, 0) or 0)
        daily.append(collect(w, cum))
    return daily


def summarize(daily: list) -> dict:
    """Frozen candidate summary vector (prereg A3) from a 90-day run."""
    d90, n = daily[-1], len(daily)
    t = np.arange(n)
    s = {}

    def series(key):
        return np.array([0.0 if day[key] is None else float(day[key])
                         for day in daily])

    for key in ("employment_rate", "destitute_share", "wealth_mean"):
        x = series(key)
        s[f"{key}_end"] = float(x[-1])
        s[f"{key}_m61_90"] = float(x[60:].mean())
        sl = np.polyfit(t[30:], x[30:], 1)[0]
        s[f"{key}_slope"] = float(sl)
    s["deprivation_mean_end"] = float(d90["deprivation"]["mean"])
    for key in ("cum_deaths", "cum_disease_deaths", "mental_mean",
                "addiction_mean", "evicted_share", "arrears_mean",
                "policy_net_mean", "firm_health_mean", "cum_firms_failed",
                "knowledge_stock_mean", "memories_remembered",
                "cum_cascades"):
        v = d90[key]
        s[key] = 0.0 if v is None else float(v)
    for j in range(8):
        s[f"force_mean_{j}"] = float(d90["force_mean"][j])
        s[f"force_sd_{j}"] = float(d90["force_sd"][j])
        s[f"pole_share_{j}"] = float(d90["pole_share"][j])
    return s
