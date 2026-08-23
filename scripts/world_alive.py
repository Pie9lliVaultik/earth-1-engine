"""EARTH-1, ALIVE — the process that never stops.

No timer. No cron. A world that ticks continuously, reads the news as
it arrives, and journals every heartbeat so it can be replayed and so
it survives a restart without losing who anyone is.

  every tick        one world-day: matter, influence, conviction,
                    cascade, feedback (earth1/chaos.world_step)
  every NEWS_EVERY  the world reads what actually happened on Earth
                    today and it lands on people's lives — firm
                    failures, job losses, crime pressure
  every SAVE_EVERY  the whole population is written to disk
  always            one JSON line per tick to the journal

Stopping it is safe: SIGTERM saves and exits at the end of the current
day, so nobody is left half-lived.

Env:
  ALIVE_POP        population if the world has to be born  (200000)
  ALIVE_PERIOD     wall seconds per world-day              (60)
  ALIVE_NEWS       ticks between news reads                (60)
  ALIVE_SAVE       ticks between full saves                (30)
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1 import persistence, provenance
from earth1.alive import birth_world, live_one_day
from earth1.chaos import entropy
from earth1.memory import event_from_news

HOME = ROOT / "data" / "alive"
JOURNAL = HOME / "journal.jsonl"
POP = int(os.environ.get("ALIVE_POP", "200000"))
PERIOD = float(os.environ.get("ALIVE_PERIOD", "60"))
NEWS_EVERY = int(os.environ.get("ALIVE_NEWS", "60"))
SAVE_EVERY = int(os.environ.get("ALIVE_SAVE", "30"))
# 0.2: the ONE canonical configuration — no local copy to drift
from earth1.alive import CANONICAL_DAY as STEP

_stop = False


def _sigterm(*_):
    global _stop
    _stop = True
    print("  stop requested — finishing the day, then saving", flush=True)


WORLD_PKL = HOME / "world.pkl"
LEGACY_ADJ = HOME / "adj.npz"          # the pre-schema graph location


def save_world(w, rng=None):
    """Persist everything, through the one canonical serializer.

    This used to carry its own field list, which is how presence and
    mobility came to be dropped on every restart. `persistence` walks a
    declared policy instead, so new world state cannot be forgotten
    here (tests/test_persistence_roundtrip.py).
    """
    HOME.mkdir(parents=True, exist_ok=True)
    meta = persistence.save_world(w, WORLD_PKL, rng=rng)
    (HOME / "state.json").write_text(json.dumps(
        {"day": w.day, "pop": int(w.civ.n), "seed": int(w.civ.seed),
         "alive": int(w.health.alive.sum()),
         "schema_version": meta["schema_version"],
         "sha256": meta["sha256"],
         "rng_persisted": meta["rng_persisted"],
         "saved_at": meta["saved_at"]}))
    return meta


def load_world():
    """Bring the world back, or refuse to pretend. Returns (world, rng).

    A pre-schema snapshot cannot carry presence, mobility or the random
    stream, so resuming from one silently changes the physics. That is a
    deliberate migration, not an incidental load: set
    EARTH1_MIGRATE_V0=1 once, at a controlled checkpoint.
    """
    if not WORLD_PKL.exists():
        print(f"  birthing a world: {POP:,} earthlings", flush=True)
        return birth_world(POP, 42), None, {"schema_version": None,
                                            "lost": [], "born": True}

    migrate = os.environ.get("EARTH1_MIGRATE_V0") == "1"
    # graph priority: the v1 graph (world.adj.npz) is canonical whenever
    # it exists; the legacy adj.npz is only for pre-migration snapshots.
    # The old order preferred legacy whenever present, which silently
    # masked a truncated v1 graph in production on 2026-08-19.
    v1_adj = WORLD_PKL.with_suffix(".adj.npz")
    adj = None if v1_adj.exists() else (LEGACY_ADJ if LEGACY_ADJ.exists()
                                        else None)
    w, rng_state, info = persistence.load_world(
        WORLD_PKL, allow_v0_migration=migrate, adj_path=adj)

    if info["schema_version"] == 0:
        print(f"  MIGRATED a v0 snapshot. It could not carry: "
              f"{', '.join(info['lost']) or 'nothing'}", flush=True)
        print("  those subsystems were rebuilt at birth values — this "
              "world is NOT bit-continuous with the one that saved it.",
              flush=True)
    print(f"  woke up: day {w.day}, {int(w.health.alive.sum()):,} alive"
          f"  (schema v{info['schema_version']}, "
          f"checksum {info.get('checksum')})", flush=True)
    return w, rng_state, info


def journal_continuity_break(w, info):
    """Mark an epoch boundary in the journal, permanently.

    A v0 migration rebuilds presence and mobility at birth values
    because the old format never wrote them. That is an ENGINEERING
    discontinuity in the trajectory, not something that happened to the
    civilization — and nothing downstream may ever read across it as
    though the world evolved through it.

    It is journaled rather than merely printed so that any later
    analysis can find the instant and refuse to span it. No causal
    benchmark may use this boundary as evidence.
    """
    rec = {"event": "continuity_break",
           "reason": "legacy_v0_missing_presence_mobility",
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "world_day": int(w.day),
           "population": int(w.civ.n),
           "alive": int(w.health.alive.sum()),
           "fields_not_carried": list(info.get("lost", [])),
           "from_schema": 0,
           "to_schema": persistence.SCHEMA_VERSION,
           "epoch": 1,
           "bit_continuous": False,
           "note": ("engineering discontinuity, not a world event — "
                    "do not use as evidence in any causal benchmark, "
                    "and do not treat any trajectory as continuous "
                    "across this instant")}
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"  EPOCH BOUNDARY journaled at day {w.day}: "
          f"{rec['reason']}", flush=True)
    return rec


def read_the_news(civ, life, world=None):
    """LAYER 4 — what actually happened on Earth lands on these lives.

    Real-world stress does not reach an agent as an opinion. It reaches
    them as a firm that failed and a job that vanished. So the news is
    coupled to the LIFE layer, not to the force layer: it changes the
    conditions people live under, and their opinions move because their
    circumstances moved.

    This is deliberately not gated by the earned-right rule. That gate
    exists to stop an unvalidated signal being used to PREDICT. This is
    not a prediction — it is the world's economy being pushed by the
    world's news, and every tick where it fired is marked in the journal
    so nothing downstream can quietly inherit it as validated.
    """
    try:
        from earth1 import signal_bus
        info = signal_bus.collect()
        # read back what this sweep just wrote and average the two
        # families that describe the mood and loudness of the day
        tones, vols = [], []
        with open(info["file"]) as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                fam = str(r.get("family", ""))
                val = r.get("value")
                if val is None:
                    continue
                if "tone" in fam:
                    tones.append(float(val))
                elif "volume" in fam:
                    vols.append(float(val))
    except Exception as exc:
        return {"news": "unavailable", "detail": str(exc)[:80]}

    tone = float(np.mean(tones)) if tones else 0.0
    vol = float(np.mean(vols)) if vols else 0.0
    # negative tone weakens firms; high volume means a loud, agitating
    # news day. Both are bounded so no single reading can wreck a world.
    stress = float(np.clip(-tone / 10.0 + vol / 200.0, -0.5, 0.5))
    if abs(stress) > 1e-6:
        life.firm_health = np.clip(life.firm_health - 0.02 * stress, 0.0, 1.0)
    # THE NEWS BECOMES A THING THAT HAPPENED. Until now the chronicle
    # ran its decay loop over an empty list forever, because nothing
    # ever called remember(). A headline is an event in this world with
    # a place, a day and people it happened to — and it fades.
    if world is not None and world.chronicle is not None:
        from earth1.memory import event_from_news
        scope = np.ones(civ.n, dtype=bool)
        if world.knowledge is not None:
            scope = world.knowledge.connected.copy()   # you have to hear it
        world.chronicle.remember(event_from_news(
            f"world news, tone {tone:.2f}", tone, float(world.day), scope))

    return {"news": "read", "tone": round(tone, 3), "volume": round(vol, 1),
            "stress": round(stress, 4), "readings": len(tones) + len(vols),
            # marked on every tick where real-world news touched these
            # lives, so nothing downstream inherits it as validated
            "news_influenced_life": bool(abs(stress) > 1e-6)}


def _snapshot_version():
    """Schema version of the snapshot on disk, or None if unversioned.

    Everything written before 0.0c is unversioned, and says so rather
    than defaulting to a number nobody stamped.
    """
    try:
        with open(HOME / "state.json") as f:
            return json.load(f).get("schema_version")
    except (OSError, ValueError):
        return None


def main():
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)

    # ── 0.0e provenance gate: prove what code this is, before the world
    # takes a step. Strict on the single writer; EARTH1_STRICT_PROVENANCE=0
    # for laptop iteration only.
    strict = os.environ.get("EARTH1_STRICT_PROVENANCE", "1") == "1"
    prov = provenance.record(
        ROOT,
        config={**STEP, "ALIVE_POP": POP, "ALIVE_PERIOD": PERIOD,
                "ALIVE_NEWS": NEWS_EVERY, "ALIVE_SAVE": SAVE_EVERY},
        snapshot_version=_snapshot_version(),
    )
    provenance.enforce(prov, strict=strict)

    w, rng_state, load_info = load_world()
    civ, life = w.civ, w.life
    # continue the saved stream where it stopped. Only a world with no
    # stream to continue — a fresh birth, or a migrated v0 snapshot —
    # falls back to the clock, and that fallback is journaled below.
    rng = persistence.rng_from_state(
        rng_state, fallback_seed=int(time.time()) % (2 ** 31))
    HOME.mkdir(parents=True, exist_ok=True)

    # the world is identified only once it exists, so population and day
    # are filled in here and the record is journaled as the first line
    # of this process's life
    prov.update(population=int(civ.n), world_day=int(w.day),
                rng_continued=rng_state is not None,
                snapshot_schema=load_info.get("schema_version") if load_info
                else None,
                event="startup",
                at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(prov) + "\n")
    print(f"  commit {str(prov['code_commit'])[:12]}"
          f"  dirty={prov['dirty_worktree']}"
          f"  schema={prov['schema_version']}"
          f"  snapshot={prov['snapshot_version']}"
          f"  pop {int(civ.n):,}  day {w.day}", flush=True)
    # an epoch boundary is recorded BEFORE the world takes a step, so
    # the journal can never show a tick that appears to cross it
    if load_info and load_info.get("schema_version") == 0:
        journal_continuity_break(w, load_info)

    print(f"  alive. one world-day every {PERIOD:.0f}s\n", flush=True)

    while not _stop:
        t0 = time.time()
        st = live_one_day(w, rng, **STEP)
        day = w.day

        line = {"day": day,
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "unemployment": round(st["unemployment"], 5),
                "deprived": round(st["deprived"], 5),
                "cascades": st.get("cascades_fired", 0),
                "firms_failed": st.get("firms_failed", 0),
                "entropy": round(entropy(civ.forces), 5),
                "fear": round(float(civ.forces[:, 0].mean()), 5)}
        for k in ("mental_ill", "addicted", "isolated", "crime_victims",
                  "bereaved", "new_children", "alive", "deaths", "ill",
                  # 0.1d mortality contract: the journal must carry the
                  # full accounting so closure is provable from the
                  # journal alone, not just from in-memory st
                  "births", "disease_deaths", "weather_deaths",
                  "starved_or_parched", "road_deaths_today",
                  "rehomed_migrants", "rehomed_workers",
                  "ties_strengthened", "ties_weakened",
                  "ties_pruned", "ties_rewired",
                  "in_treatment", "countries_at_war", "war_deaths",
                  "conscripted", "mean_welfare", "mean_legitimacy",
                  "homeless", "crimes_today", "criminal_share",
                  "wealth_gini", "status_gini", "migrated_today",
                  "mean_knowledge", "discoveries_today", "works_today",
                  "living_works", "scientists", "remembered",
                  "people_under_memory"):
            if k in st:
                line[k] = round(st[k], 5) if isinstance(st[k], float) else st[k]
        if day % NEWS_EVERY == 0:
            line.update(read_the_news(civ, life, world=w))
        with open(JOURNAL, "a") as f:
            f.write(json.dumps(line) + "\n")
        if day % SAVE_EVERY == 0:
            save_world(w, rng)

        if day % 10 == 0 or day < 3:
            print(f"  day {day:6d}  alive {line.get('alive', 0):7,d}"
                  f"  unemp {line['unemployment']:5.1%}"
                  f"  homeless {line.get('homeless', 0):5.2%}"
                  f"  wars {line.get('countries_at_war', 0):3d}"
                  f"  gini {line.get('wealth_gini', 0):.3f}"
                  f"  know {line.get('mean_knowledge', 0):.3f}"
                  f"  entropy {line['entropy']:.4f}", flush=True)

        rest = PERIOD - (time.time() - t0)
        while rest > 0 and not _stop:
            time.sleep(min(rest, 1.0))
            rest -= 1.0

    save_world(w, rng)
    print(f"  saved at day {w.day}. the world is paused, not lost.",
          flush=True)


if __name__ == "__main__":
    main()
