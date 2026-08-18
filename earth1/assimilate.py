"""ASSIMILATE — the time machine. A hundred worlds, and reality as a filter.

You cannot invert a dissipative chaotic system, so you never rewind.
Instead you run an ENSEMBLE forward, and every time reality left a
fingerprint you kill the worlds that do not match it and multiply the
ones that do. What survives is not THE past. It is the set of pasts
consistent with everything we actually recorded, and the width of that
set is the honest measure of how much we do not know about our own
history.

This is a particle filter — the same method weather services use to
"travel to the past" every six hours — applied to a civilisation.

    propagate   run every particle to the next observation date
    score       how well does each world match what was recorded
    resample    kill the poor matches, clone the good ones, jitter
    repeat

THE OBSERVATION COLLAPSES THE ENSEMBLE, and this is not a metaphor for
quantum mechanics — it is the same mathematics. Before a survey is
published, a hundred synthetic histories are live. The survey arrives
and kills eighty. The world's past becomes MORE DEFINITE because someone
measured it, and stays spread where nobody looked.

THE CONTROL THAT DECIDES WHETHER ANY OF THIS WORKS. A filter that does
not beat an unfiltered ensemble is not assimilating, it is resampling
noise. So every run carries a twin that receives no observations at all,
and the claim is only ever the DIFFERENCE between them. Three diagnostics
are reported and any of them can fail:

  RMSE FALLING      does the filtered ensemble track the observation
                    better over time than the unfiltered one
  ESS NOT COLLAPSED effective sample size. If one particle takes all the
                    weight the ensemble has degenerated into a single
                    history and the uncertainty estimate is fiction
  SPREAD SHRINKING  does measuring actually narrow the set of surviving
                    pasts, which is the whole claim
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "data" / "history"

# how much observational error to assume. Too tight and the filter kills
# everything on the first observation; too loose and it never learns.
DEFAULT_SIGMA = 0.03          # 3 percentage points on unemployment
JITTER = 0.01                 # roughening after resampling


@dataclass
class Observation:
    """Something reality recorded, in a form a world can be scored on."""
    date: str
    kind: str                       # "unemployment", "wvs", "conflict", ...
    by_country: dict = field(default_factory=dict)   # iso2 -> value
    sigma: float = DEFAULT_SIGMA
    source: str = ""


def fetch_unemployment(start: int = 2015, end: int = 2025) -> list:
    """World Bank SL.UEM.TOTL.ZS, annual, every country.

    One observable, chosen deliberately as the first: it is annual, it
    covers 190+ countries, it is directly computable from the world's own
    state, and it is exactly the quantity the life layer produces. If the
    filter cannot converge on this, adding attitudes will not save it.
    """
    import urllib.request
    url = ("https://api.worldbank.org/v2/country/all/indicator/"
           f"SL.UEM.TOTL.ZS?date={start}:{end}&format=json&per_page=20000")
    with urllib.request.urlopen(url, timeout=120) as r:
        payload = json.loads(r.read().decode())
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    by_year: dict = {}
    for row in rows:
        v, y = row.get("value"), row.get("date")
        cc = (row.get("country", {}) or {}).get("id") or ""
        iso2 = (row.get("countryiso3code") or "")[:2]
        if v is None or not y:
            continue
        # World Bank returns iso3; map through our own table below
        by_year.setdefault(int(y), {})[row["countryiso3code"]] = float(v) / 100.0
    obs = []
    for y in sorted(by_year):
        obs.append(Observation(date=f"{y}-12-31", kind="unemployment",
                               by_country=by_year[y], sigma=DEFAULT_SIGMA,
                               source="World Bank SL.UEM.TOTL.ZS"))
    OBS.mkdir(parents=True, exist_ok=True)
    (OBS / "unemployment.json").write_text(json.dumps(
        [{"date": o.date, "kind": o.kind, "by_country": o.by_country,
          "source": o.source} for o in obs], indent=1))
    return obs


def load_observations(kind: str = "unemployment") -> list:
    p = OBS / f"{kind}.json"
    if not p.exists():
        return []
    return [Observation(date=d["date"], kind=d["kind"],
                        by_country=d["by_country"],
                        source=d.get("source", ""))
            for d in json.loads(p.read_text())]


def measure(w, kind: str = "unemployment") -> dict:
    """What this world would report, in the same units as the observation."""
    from earth1.genesis import GENESIS_COUNTRIES
    if kind != "unemployment":
        raise ValueError(f"no measurement defined for {kind}")
    civ, life, alive = w.civ, w.life, w.health.alive
    out = {}
    for i, c in enumerate(GENESIS_COUNTRIES):
        m = (civ.country == i) & alive & life.in_lf
        if m.sum() < 20:                  # too few to report honestly
            continue
        out[c.get("iso3", c["iso2"])] = float((~life.employed[m]).mean())
    return out


def log_likelihood_per_country(sim: dict, obs: Observation) -> dict:
    """Per-country log-likelihood — the input to a LOCALIZED filter.

    A global particle filter in a state space this large degenerates on
    the first observation: one world wins everything and the ensemble
    becomes a single history wearing a confidence interval. This is the
    known failure mode, and the standard fix in geophysical assimilation
    is LOCALIZATION — stop treating the world as one indivisible
    hypothesis and resample region by region.

    It is valid here for a measured reason: only 5.3% of Earth-1's social
    edges cross a border, so a country is nearly a separate dynamical
    system. Taking Nigeria from the world that got Nigeria right and
    Sweden from the world that got Sweden right converts ONE
    million-dimensional problem into 194 low-dimensional ones, and the
    per-country ESS stays healthy where a global ESS would collapse.

    THE COST, STATED: splicing populations between worlds severs the
    international edges that ran between them — diaspora ties and media
    reach. At 5.3% of edges the damage is bounded but it is real, and it
    is why localized resampling is an OPTION rather than the default.
    Global resampling keeps every world internally coherent and degrades
    by degeneracy; local resampling keeps the ensemble diverse and
    degrades by cutting ties. Both failure modes are reported.
    """
    out = {}
    for k, v in obs.by_country.items():
        if k in sim:
            d = (sim[k] - v) / obs.sigma
            out[k] = float(-0.5 * d * d)
    return out


def log_likelihood(sim: dict, obs: Observation) -> float:
    """Gaussian log-likelihood over the countries both sides can speak to."""
    keys = [k for k in obs.by_country if k in sim]
    if not keys:
        return 0.0
    d = np.array([sim[k] - obs.by_country[k] for k in keys])
    return float(-0.5 * np.sum((d / obs.sigma) ** 2) / len(keys))


def _systematic_resample(weights: np.ndarray, rng) -> np.ndarray:
    """Low-variance resampling. Fewer duplicates than multinomial."""
    n = weights.size
    positions = (rng.random() + np.arange(n)) / n
    cumsum = np.cumsum(weights)
    return np.searchsorted(cumsum, positions).clip(0, n - 1)


def _ess(weights: np.ndarray) -> float:
    return float(1.0 / np.sum(weights ** 2))


def _weights_from(ll: np.ndarray, temper: float = 1.0) -> np.ndarray:
    """Softmax with TEMPERING.

    temper < 1 flattens the likelihood, which stops the first observation
    from annihilating the ensemble before it has had a chance to learn
    anything. It is the difference between a filter that updates and a
    filter that commits suicide on contact with data.
    """
    z = ll * temper
    w = np.exp(z - z.max())
    return w / max(w.sum(), 1e-300)


def _localized_resample(particles, per_country_ll: list, rng,
                        temper: float = 1.0) -> tuple:
    """Resample COUNTRY BY COUNTRY, then reassemble worlds.

    Each country's population is taken from whichever particle modelled
    that country best. Returns the new particle list and the per-country
    ESS distribution, so localization can be shown to have actually
    preserved diversity rather than merely claimed to.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    n_p = len(particles)
    codes = [c.get("iso3", c["iso2"]) for c in GENESIS_COUNTRIES]

    # start every new world as a clone of a globally-decent particle, then
    # overwrite each country from its own winner
    base_ll = np.array([sum(d.values()) for d in per_country_ll])
    base_idx = _systematic_resample(_weights_from(base_ll, temper), rng)
    new = [copy.deepcopy(particles[j][0]) for j in base_idx]

    ess_per_country = []
    for ci, code in enumerate(codes):
        ll = np.array([d.get(code, 0.0) for d in per_country_ll])
        if not np.any(ll):
            continue
        w = _weights_from(ll, temper)
        ess_per_country.append(_ess(w))
        pick = _systematic_resample(w, rng)
        for slot in range(n_p):
            src = particles[int(pick[slot])][0]
            dst = new[slot]
            m_src = src.civ.country == ci
            m_dst = dst.civ.country == ci
            k = int(min(m_src.sum(), m_dst.sum()))
            if k == 0:
                continue
            si = np.flatnonzero(m_src)[:k]
            di = np.flatnonzero(m_dst)[:k]
            # move the whole person: forces, traits, material life, body
            dst.civ.forces[di] = src.civ.forces[si]
            dst.civ.alpha[di] = src.civ.alpha[si]
            for attr in ("openness", "doubt", "desire_intensity", "age"):
                getattr(dst.civ, attr)[di] = getattr(src.civ, attr)[si]
            for attr in ("employed", "in_lf", "wage", "wealth", "spells",
                         "deprivation", "mental", "addiction",
                         "relationship", "social_need"):
                a_s = getattr(src.life, attr, None)
                a_d = getattr(dst.life, attr, None)
                if a_s is not None and a_d is not None:
                    a_d[di] = a_s[si]
            dst.health.alive[di] = src.health.alive[si]
            dst.health.condition[di] = src.health.condition[si]
    out = [(w2, np.random.default_rng(int(rng.integers(1 << 30))))
           for w2 in new]
    return out, ess_per_country


def run(n_particles: int = 24, days_between: int = 365,
        n_steps: int = 5, pop: int = 20_000, seed: int = 42,
        kind: str = "unemployment", localize: bool = True,
        temper: float = 0.35, ess_floor: float = 0.5, log=print) -> dict:
    """Assimilate. Filtered ensemble AND an unfiltered twin.

    The unfiltered twin is not decoration. Without it there is no way to
    tell assimilation from resampling noise, and "the ensemble tracks
    reality" would be unfalsifiable.
    """
    from earth1.alive import birth_world, live_one_day

    obs_all = load_observations(kind)
    if not obs_all:
        return {"error": f"no observations for {kind}. run fetch first."}
    obs_all = obs_all[:n_steps]

    rng = np.random.default_rng(seed)
    log(f"  {n_particles} worlds x {pop:,} agents, {len(obs_all)} observations")

    def fresh(i):
        w = birth_world(pop, seed + i * 101)
        return w, np.random.default_rng(seed * 31 + i)

    filt = [fresh(i) for i in range(n_particles)]
    free = [fresh(i) for i in range(n_particles)]   # the control twin

    history = []
    for step, o in enumerate(obs_all):
        for pool in (filt, free):
            for w, r in pool:
                for _ in range(days_between):
                    live_one_day(w, r)

        sim_f = [measure(w, kind) for w, _ in filt]
        sim_u = [measure(w, kind) for w, _ in free]

        def rmse(sims):
            errs = []
            for s in sims:
                keys = [k for k in o.by_country if k in s]
                if keys:
                    errs.append(np.sqrt(np.mean(
                        [(s[k] - o.by_country[k]) ** 2 for k in keys])))
            return float(np.mean(errs)) if errs else None

        # the ensemble MEAN is the estimate, not any single particle
        def mean_rmse(sims):
            keys = set(o.by_country)
            for s in sims:
                keys &= set(s)
            keys = sorted(keys)
            if not keys:
                return None
            m = {k: float(np.mean([s[k] for s in sims])) for k in keys}
            return float(np.sqrt(np.mean(
                [(m[k] - o.by_country[k]) ** 2 for k in keys])))

        per_country = [log_likelihood_per_country(s, o) for s in sim_f]
        ll = np.array([sum(d.values()) for d in per_country])
        wts = _weights_from(ll, temper)
        ess = _ess(wts)

        row = {"step": step, "observation_date": o.date,
               "filtered_rmse": mean_rmse(sim_f),
               "unfiltered_rmse": mean_rmse(sim_u),
               "filtered_spread": float(np.std(
                   [np.mean(list(s.values())) for s in sim_f])),
               "unfiltered_spread": float(np.std(
                   [np.mean(list(s.values())) for s in sim_u])),
               "ess": round(ess, 2),
               "ess_fraction": round(ess / n_particles, 3)}
        history.append(row)
        log(f"    {o.date}  filtered RMSE {row['filtered_rmse']:.4f}"
            f"  unfiltered {row['unfiltered_rmse']:.4f}"
            f"  ESS {ess:.1f}/{n_particles}")

        # ── THE OBSERVATION COLLAPSES THE ENSEMBLE ───────────────────
        # ADAPTIVE: only resample when the ensemble has actually
        # degenerated. Resampling every step throws away diversity for
        # nothing and is the second most common way to wreck a filter.
        if ess >= ess_floor * n_particles:
            row["resampled"] = False
            log(f"      ESS healthy — carried forward without resampling")
        elif localize:
            filt, ess_pc = _localized_resample(filt, per_country, rng, temper)
            row["resampled"] = "localized"
            row["median_country_ess"] = (round(float(np.median(ess_pc)), 2)
                                         if ess_pc else None)
            log(f"      localized resample — median per-country ESS "
                f"{row['median_country_ess']}/{n_particles}")
        else:
            idx = _systematic_resample(wts, rng)
            new = []
            for j in idx:
                w2 = copy.deepcopy(filt[j][0])
                # roughening: without jitter, resampling collapses to clones
                w2.civ.forces = np.clip(
                    w2.civ.forces
                    + rng.normal(0, JITTER, w2.civ.forces.shape), 0.0, 1.0)
                new.append((w2, np.random.default_rng(
                    int(rng.integers(1 << 30)))))
            filt = new
            row["resampled"] = "global"

        # roughening always, so clones diverge again
        for w2, _ in filt:
            w2.civ.forces = np.clip(
                w2.civ.forces + rng.normal(0, JITTER * 0.5,
                                           w2.civ.forces.shape), 0.0, 1.0)

    f_last = history[-1]["filtered_rmse"]
    u_last = history[-1]["unfiltered_rmse"]
    f_first = history[0]["filtered_rmse"]
    beats = (f_last is not None and u_last is not None and f_last < u_last)
    improved = (f_last is not None and f_first is not None
                and f_last < f_first)
    narrowed = (history[-1]["filtered_spread"]
                < history[-1]["unfiltered_spread"])
    degenerate = history[-1]["ess_fraction"] < 0.1

    verdict = ("FILTER WORKS" if (beats and not degenerate) else
               "DEGENERATE — one particle took all the weight, the "
               "uncertainty estimate is fiction" if degenerate else
               "NO BETTER THAN UNFILTERED — this is resampling noise, "
               "not assimilation")
    return {"particles": n_particles, "pop": pop, "kind": kind,
            "localized": localize, "temper": temper, "ess_floor": ess_floor,
            "history": history,
            "beats_unfiltered": bool(beats),
            "rmse_improved_over_time": bool(improved),
            "measuring_narrowed_the_past": bool(narrowed),
            "degenerate": bool(degenerate),
            "verdict": verdict}
