"""TIMELINE — one cold start, then a decade of lived history.

Pietro's design, and it is better than reconstructing a year from
tables: you cold-start ONCE at the earliest date the data supports, then
feed the world real history day by day and snapshot it as it goes. Every
later state is arrived at by LIVING rather than by assembly.

    2015 cold start  ->  real news, real macro, real conflicts, daily
                     ->  monthly snapshots
                     ->  restore any month and branch from it

What that buys, and no reconstruction can: PATH DEPENDENCE. A world
cold-started in February 2020 from census tables does not know the UK
just went through a referendum. A world that lived through it does, and
its response to a pandemic is conditioned on what it already carries —
the scars in specific agents, the ties that broke, the convictions that
hardened in the places where they actually hardened.

WHY 2015. GDELT 1.0 events reach back to 1979, but GDELT 2.0 — the
version with tone, themes and the Global Knowledge Graph — begins in
FEBRUARY 2015. World Bank annual series reach back to 1960 and WVS
Wave 6 closes in 2014. So February 2015 is simultaneously the first
month of good news data and a clean starting line before Brexit, Trump,
COVID and Ukraine.

WHAT THIS DOES NOT CLAIM. The world will not reproduce real history.
Chaos forbids it: at the measured FSLE of +0.13/day, any initialisation
error is beyond recovery within months, and the timeline will diverge
from the real one no matter how good the input. What it produces is a
population that has lived through events OF THE SAME SHAPE AT THE SAME
TIMES. That is what makes its structure organically path-dependent, and
it is a real and useful property — but "our 2020 matches the real 2020"
is a claim this design cannot support and must never make.

THE TIMELINE IS DISPOSABLE ON PURPOSE. A decade of replay costs roughly
twenty minutes at 200K agents, which means it is regenerated whenever
the physics changes rather than preserved as a precious artifact. Given
how many construction errors have been found and fixed, that is the
only safe posture: a cheap timeline is re-derived, an expensive one gets
defended past its expiry.
"""
from __future__ import annotations

import json
import os
import pickle
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "data" / "timeline"
SIGNALS = ROOT / "data" / "history"

START = date(2015, 2, 1)          # GDELT 2.0 begins
SNAPSHOT_EVERY_DAYS = 30

# The SQL that produces the daily driver table. Run server-side so we
# download megabytes instead of terabytes — the raw GKG is tens of TB and
# we need only a daily aggregate per country.
GDELT_BIGQUERY_SQL = """
-- Daily tone and volume by country from GDELT 2.0 events.
-- Aggregate in BigQuery, export the result: ~3,650 days x 194 countries.
SELECT
  PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING)) AS day,
  ActionGeo_CountryCode AS iso2,
  COUNT(*)                       AS volume,
  AVG(AvgTone)                   AS tone,
  AVG(GoldsteinScale)            AS goldstein,
  SUM(CASE WHEN CAST(EventRootCode AS INT64) BETWEEN 18 AND 20
           THEN 1 ELSE 0 END)    AS violent_events,
  SUM(CASE WHEN CAST(EventRootCode AS INT64) BETWEEN 14 AND 15
           THEN 1 ELSE 0 END)    AS protest_events
FROM `gdelt-bq.gdeltv2.events`
WHERE SQLDATE >= 20150201
  AND ActionGeo_CountryCode IS NOT NULL
GROUP BY day, iso2
ORDER BY day, iso2
"""


@dataclass
class DailySignals:
    """Real-world drivers, one row per (day, country).

    Missing data is explicit rather than imputed: a country-day with no
    coverage returns None and the world simply receives no news that
    day, which is closer to the truth than a fabricated zero.
    """
    days: list = field(default_factory=list)          # date objects
    iso2: list = field(default_factory=list)
    tone: dict = field(default_factory=dict)          # (day, iso2) -> float
    volume: dict = field(default_factory=dict)
    violent: dict = field(default_factory=dict)
    protest: dict = field(default_factory=dict)
    macro: dict = field(default_factory=dict)         # (year, iso2) -> dict

    @property
    def available(self) -> bool:
        return bool(self.tone)

    def for_day(self, d: date) -> dict:
        """Everything real that happened on this day, by country."""
        return {"tone": {c: self.tone.get((d, c)) for c in self.iso2
                         if (d, c) in self.tone},
                "volume": {c: self.volume.get((d, c)) for c in self.iso2
                           if (d, c) in self.volume},
                "violent": {c: self.violent.get((d, c)) for c in self.iso2
                            if (d, c) in self.violent},
                "protest": {c: self.protest.get((d, c)) for c in self.iso2
                            if (d, c) in self.protest}}


def load_signals(path: Path | None = None) -> DailySignals:
    """Load the daily driver table if it has been fetched.

    Returns an EMPTY signal set when the file is absent, and the replay
    then runs on endogenous dynamics alone. That is a legitimate mode —
    it is the control for the whole exercise, since it shows what the
    world does over a decade with no real history at all — but it must
    never be mistaken for the historical run.
    """
    p = path or (SIGNALS / "gdelt_daily.csv")
    s = DailySignals()
    if not p.exists():
        return s
    import csv
    seen_days, seen_iso = set(), set()
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                d = date.fromisoformat(row["day"])
            except (ValueError, KeyError):
                continue
            cc = (row.get("iso2") or "").strip().upper()
            if not cc:
                continue
            seen_days.add(d)
            seen_iso.add(cc)
            for key, col, cast in (("tone", "tone", float),
                                   ("volume", "volume", float),
                                   ("violent", "violent_events", float),
                                   ("protest", "protest_events", float)):
                v = row.get(col)
                if v not in (None, ""):
                    try:
                        getattr(s, key)[(d, cc)] = cast(v)
                    except ValueError:
                        pass
    s.days = sorted(seen_days)
    s.iso2 = sorted(seen_iso)
    mp = SIGNALS / "worldbank_annual.json"
    if mp.exists():
        s.macro = {tuple(k.split("|")): v
                   for k, v in json.loads(mp.read_text()).items()}
    return s


def cold_start(pop: int, seed: int = 42, year: int = 2015):
    """The ONE reconstruction from tables. Everything after this is lived.

    Honest about what it is: genesis uses contemporary country
    distributions, so a 2015 cold start is contemporary structure with a
    2015 label. That error matters much less here than it would in a
    reconstruct-the-year design, because the point of this world is not
    to BE 2015 — it is to be a plausible living population that then
    experiences a decade of real events in the right order. Path
    dependence comes from the decade, not from the starting line.
    """
    from earth1.alive import birth_world
    w = birth_world(pop, seed)
    w.day = 0
    return w


def _apply_real_day(w, sig: dict, rng) -> dict:
    """One day of real history lands on the world.

    Real stress reaches an agent as a firm that failed and a job that
    vanished, never as an opinion handed down — same rule as the live
    loop. Volume and tone move the economy; violence and protest events
    press the force channels of the countries where they happened.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    from earth1.memory import event_from_news
    from earth1.types import Force

    iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
    touched = 0
    tones = sig.get("tone", {})
    vols = sig.get("volume", {})
    viol = sig.get("violent", {})
    prot = sig.get("protest", {})
    if not tones and not vols:
        return {"real_countries": 0}

    # normalise volume within the day so a busy news day is loud
    # everywhere rather than an artefact of one country's coverage
    vals = np.array([v for v in vols.values() if v is not None], dtype=float)
    vmed = float(np.median(vals)) if vals.size else 1.0

    for cc, i in iso.items():
        t = tones.get(cc)
        v = vols.get(cc)
        if t is None and v is None:
            continue
        mask = w.civ.country == i
        if not mask.any():
            continue
        touched += 1
        # negative tone weakens the firms of that country
        if t is not None:
            firm_hit = w.life.firm_country == i
            if firm_hit.any():
                w.life.firm_health[firm_hit] = np.clip(
                    w.life.firm_health[firm_hit] + 0.004 * (t / 10.0),
                    0.0, 1.0)
        # violence and protest press the channels they actually press
        nv = (viol.get(cc) or 0.0) / max(vmed, 1.0)
        npr = (prot.get(cc) or 0.0) / max(vmed, 1.0)
        if nv > 0:
            w.civ.forces[mask, Force.FEAR] = np.clip(
                w.civ.forces[mask, Force.FEAR] + 0.02 * min(nv, 3.0), 0, 1)
        if npr > 0:
            w.civ.forces[mask, Force.COLLECTIVE] = np.clip(
                w.civ.forces[mask, Force.COLLECTIVE]
                + 0.02 * min(npr, 3.0), 0, 1)
            w.civ.forces[mask, Force.IDENTITY] = np.clip(
                w.civ.forces[mask, Force.IDENTITY]
                + 0.015 * min(npr, 3.0), 0, 1)

    # the day becomes a thing that happened, and fades
    worst = min((t for t in tones.values() if t is not None), default=0.0)
    if worst < -4.0 and w.chronicle is not None:
        scope = w.knowledge.connected.copy() if w.knowledge is not None \
            else np.ones(w.civ.n, dtype=bool)
        w.chronicle.remember(event_from_news(
            f"a bad day in the world (tone {worst:.1f})", worst,
            float(w.day), scope))
    return {"real_countries": touched}


def build(pop: int = 200_000, seed: int = 42, start: date = START,
          end: date | None = None, every: int = SNAPSHOT_EVERY_DAYS,
          signals: DailySignals | None = None, log=print) -> dict:
    """Cold start once, live through real history, snapshot as you go."""
    from earth1.alive import live_one_day

    end = end or date.today()
    sig = signals if signals is not None else load_signals()
    HOME.mkdir(parents=True, exist_ok=True)
    w = cold_start(pop, seed, start.year)
    rng = np.random.default_rng(seed ^ 0x71E5)

    mode = "HISTORICAL" if sig.available else "ENDOGENOUS ONLY (no signal file)"
    total = (end - start).days
    log(f"  timeline: {mode}")
    log(f"  {pop:,} earthlings, {start} -> {end} ({total:,} days), "
        f"snapshot every {every}")

    index, d = [], start
    fed = 0
    while d < end:
        st = live_one_day(w, rng)
        if sig.available:
            r = _apply_real_day(w, sig.for_day(d), rng)
            fed += 1 if r["real_countries"] else 0
        if (d - start).days % every == 0:
            path = HOME / f"{d.isoformat()}.pkl"
            _save(w, path, rng=rng)
            index.append({"date": d.isoformat(), "day": w.day,
                          "file": path.name,
                          "population": int(w.health.alive.sum()),
                          "unemployment": round(st.get("unemployment", 0), 5),
                          "at_war": st.get("countries_at_war", 0)})
            if len(index) % 12 == 1:
                log(f"    {d.isoformat()}  pop {int(w.health.alive.sum()):,}"
                    f"  unemp {st.get('unemployment', 0):.1%}"
                    f"  wars {st.get('countries_at_war', 0)}")
        d += timedelta(days=1)

    meta = {"mode": mode, "pop": pop, "seed": seed,
            "start": start.isoformat(), "end": end.isoformat(),
            "snapshot_every_days": every,
            "days_with_real_news": fed,
            "snapshots": index,
            "caveat": ("the world does not reproduce real history — chaos "
                       "forbids it. It has lived through events of the same "
                       "shape at the same times, which is what makes its "
                       "structure path-dependent.")}
    (HOME / "index.json").write_text(json.dumps(meta, indent=1))
    log(f"  {len(index)} snapshots, {fed:,} days carried real news")
    return meta


def _save(w, path: Path, rng=None) -> None:
    """Snapshot through the one canonical serializer.

    This carried its own field list until 0.0c, and it omitted
    `presence` and `mobility`. Because those are None-defaulted
    optionals that `live_one_day` gates on (alive.py:150,160), a
    restored snapshot ran permanently without contagion, crowds, riots,
    road deaths or flight cultural mixing — a different physics, not a
    missing value. Every backtest branched from such a world was
    incomparable to one branched from the live daemon.
    """
    from earth1 import persistence
    persistence.save_world(w, path, rng=rng)


def restore(when: str, *, with_rng: bool = False,
            allow_v0_migration: bool = False):
    """Bring back the world as it was — organically — on that date.

    Returns the world, or `(world, rng)` when `with_rng` is set. A world
    restored without its stream continues on different dice than the one
    that saved it, which makes it a similar counterfactual rather than
    the same one — so paired branch work should always ask for it.
    """
    from earth1 import persistence
    p = HOME / f"{when}.pkl"
    if not p.exists():
        avail = sorted(x.stem for x in HOME.glob("*.pkl"))
        raise FileNotFoundError(
            f"no snapshot for {when}. have: {avail[:3]}...{avail[-3:]}"
            if avail else f"no snapshots at all in {HOME}")
    w, rng_state, _ = persistence.load_world(
        p, allow_v0_migration=allow_v0_migration)
    if with_rng:
        return w, persistence.rng_from_state(rng_state)
    return w


def available() -> list:
    idx = HOME / "index.json"
    if not idx.exists():
        return []
    return [s["date"] for s in json.loads(idx.read_text())["snapshots"]]
