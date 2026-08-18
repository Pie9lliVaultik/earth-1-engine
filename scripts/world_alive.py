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

from earth1.alive import birth_world, live_one_day
from earth1.chaos import entropy
from earth1.memory import event_from_news

HOME = ROOT / "data" / "alive"
JOURNAL = HOME / "journal.jsonl"
POP = int(os.environ.get("ALIVE_POP", "200000"))
PERIOD = float(os.environ.get("ALIVE_PERIOD", "60"))
NEWS_EVERY = int(os.environ.get("ALIVE_NEWS", "60"))
SAVE_EVERY = int(os.environ.get("ALIVE_SAVE", "30"))
STEP = dict(beta=2.0, residue=0.02, critical_fraction=0.12, relax=0.25)

_stop = False


def _sigterm(*_):
    global _stop
    _stop = True
    print("  stop requested — finishing the day, then saving", flush=True)


LIFE_ARRAYS = ("occupation", "firm", "employed", "in_lf", "wage", "wealth",
               "cost", "tenure", "deprivation", "spells", "firm_health",
               "firm_country", "force_baseline", "trait_baseline", "mental",
               "physical", "addiction", "relationship", "social_need",
               "political", "mental_setpoint", "relationship_setpoint",
               "last_event", "last_event_day", "n_events")
CIV_ARRAYS = ("country", "region", "age_bucket", "age", "education", "income",
              "urban", "openness", "empathy", "risk_appetite", "doubt",
              "desire_intensity", "economic_field", "culture_offset",
              "conscientiousness", "agreeableness", "extraversion",
              "neuroticism", "power_distance", "individualism",
              "uncertainty_avoidance", "long_term_orientation", "forces",
              "alpha", "means")


def save_world(w):
    """Persist everything: people, bodies, knowledge, states, memory."""
    import pickle
    HOME.mkdir(parents=True, exist_ok=True)
    from scipy import sparse
    sparse.save_npz(HOME / "adj.npz", w.civ.adj.tocsr())
    with open(HOME / "world.pkl", "wb") as f:
        pickle.dump({"civ": {k: getattr(w.civ, k) for k in CIV_ARRAYS},
                     "fabric": w.fabric, "feed": w.feed,
                     "life": w.life, "health": w.health,
                     "knowledge": w.knowledge, "gov": w.gov,
                     "klass": w.klass, "chronicle": w.chronicle,
                     # climate and flourishing were absent here, so every
                     # restart silently reset the weather and wiped
                     # everyone's hunger, thirst and hope. Restart=always
                     # means that was happening in production.
                     "climate": w.climate, "flourishing": w.flourishing,
                     "day": w.day, "n": w.civ.n, "seed": w.civ.seed}, f)
    (HOME / "state.json").write_text(json.dumps(
        {"day": w.day, "pop": int(w.civ.n), "seed": int(w.civ.seed),
         "alive": int(w.health.alive.sum()),
         "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))


def load_world():
    import pickle
    from scipy import sparse
    if not (HOME / "world.pkl").exists():
        print(f"  birthing a world: {POP:,} earthlings", flush=True)
        return birth_world(POP, 42)
    with open(HOME / "world.pkl", "rb") as f:
        d = pickle.load(f)
    w = birth_world(d["n"], d["seed"])
    for k, v in d["civ"].items():
        setattr(w.civ, k, v)
    w.civ.adj = sparse.load_npz(HOME / "adj.npz")
    # THE FABRIC MUST MATCH THE GRAPH IT DESCRIBES. birth_world builds a
    # fresh fabric from a fresh population; overwriting civ.adj from disk
    # afterwards left w.fabric.by_type describing a world that no longer
    # exists, so any per-channel analysis on a resumed world was wrong.
    if "fabric" in d and d["fabric"] is not None:
        w.fabric = d["fabric"]
    if "feed" in d and d["feed"] is not None:
        w.feed = d["feed"]
    w.life, w.health = d["life"], d["health"]
    w.knowledge, w.gov = d["knowledge"], d["gov"]
    w.klass, w.chronicle, w.day = d["klass"], d["chronicle"], d["day"]
    if d.get("climate") is not None:
        w.climate = d["climate"]
    if d.get("flourishing") is not None:
        w.flourishing = d["flourishing"]
    print(f"  woke up: day {w.day}, {int(w.health.alive.sum()):,} alive",
          flush=True)
    return w


def _unused_save(civ, life, fab, day):
    HOME.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(HOME / "civ.npz",
                        **{k: getattr(civ, k) for k in CIV_ARRAYS})
    np.savez_compressed(HOME / "life.npz",
                        **{k: getattr(life, k) for k in LIFE_ARRAYS
                           if getattr(life, k, None) is not None})
    from scipy import sparse
    sparse.save_npz(HOME / "adj.npz", civ.adj.tocsr())
    (HOME / "state.json").write_text(json.dumps(
        {"day": day, "pop": int(civ.n), "seed": int(civ.seed),
         "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))


def load_or_birth():
    st = HOME / "state.json"
    if st.exists():
        from scipy import sparse
        meta = json.loads(st.read_text())
        civ = genesis(meta["pop"], meta["seed"])
        cz = np.load(HOME / "civ.npz")
        for k in cz.files:
            setattr(civ, k, cz[k])
        civ.adj = sparse.load_npz(HOME / "adj.npz")
        life = birth_life(civ, seed=meta["seed"])
        lz = np.load(HOME / "life.npz")
        for k in lz.files:
            setattr(life, k, lz[k])
        print(f"  woke up: day {meta['day']}, {civ.n:,} earthlings",
              flush=True)
        return civ, life, None, int(meta["day"])
    print(f"  birthing a world: {POP:,} earthlings", flush=True)
    civ = genesis(POP, 42)
    life = birth_life(civ, seed=42)
    fab = build_fabric(civ, life, seed=42)
    civ.adj = fab.adj
    return civ, life, fab, 0


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


def main():
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)
    w = load_world()
    civ, life = w.civ, w.life
    rng = np.random.default_rng(int(time.time()) % (2 ** 31))
    HOME.mkdir(parents=True, exist_ok=True)
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
            save_world(w)

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

    save_world(w)
    print(f"  saved at day {w.day}. the world is paused, not lost.",
          flush=True)


if __name__ == "__main__":
    main()
