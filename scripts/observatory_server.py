"""EARTH-1 — LIVE CIVILIZATION OBSERVATORY (local, read-only).

Investor-facing local dashboard over the REAL engine. Governing rules:
no second simulator, no mocked outputs, no physics added or tuned.
The world served here is a LOCAL DEMO CIVILIZATION born through the
canonical birth_world()/live_one_day() engine at demo scale — the
canonical 4M production world lives on the production box and is
never touched (read-only rule). Everything shown is computed by the
engine or explicitly marked NOT YET COMPUTABLE.
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from earth1.alive import birth_world, live_one_day   # noqa: E402
from earth1.branch import Scenario, apply as apply_scenario  # noqa: E402
from earth1.types import Force                        # noqa: E402
from earth1.genesis import GENESIS_COUNTRIES          # noqa: E402

N = int(os.environ.get("EARTH1_OBS_N", "25000"))
SEED = int(os.environ.get("EARTH1_OBS_SEED", "1142"))
TICK_SECONDS = float(os.environ.get("EARTH1_OBS_TICK", "2.0"))
BRANCH_DAYS = int(os.environ.get("EARTH1_OBS_HORIZON", "30"))
BRANCH_PAIRS = int(os.environ.get("EARTH1_OBS_PAIRS", "2"))

app = FastAPI(title="Earth-1 Observatory (local)")

MODEL_COMMIT = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
    capture_output=True, text=True).stdout.strip() or "unknown"

LOCK = threading.Lock()
PULSE: deque = deque(maxlen=400)
STATE = {"born_at": None, "ticks": 0, "paused_for_branch": False}
BRANCHES: dict = {}          # event_id -> {"status", "result", ...}

print(f"[observatory] birthing demo civilization N={N} seed={SEED} "
      f"(canonical engine, local demo scale) ...", flush=True)
W = birth_world(N, SEED)
RNG = np.random.default_rng(SEED)
STATE["born_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
_prev = {}


def _snapshot_prev():
    a = W.health.alive
    return {
        "employed": W.life.employed.copy(),
        "alive": a.copy(),
        "firm_sick": (W.life.firm_health < 0.4).copy(),
        "deprived": (W.life.deprivation > 0.5).copy(),
        "forces": W.civ.forces[a].mean(axis=0).copy(),
        "memories": len(W.chronicle.events),
        "wealth_poor": (W.life.wealth < 5.0).copy(),
    }


def _pulse_tick():
    """One real engine day; every line below is a measured diff of
    actual state, never an animation."""
    global _prev
    with LOCK:
        st = live_one_day(W, RNG)
        cur = _snapshot_prev()
        day = int(W.day)
    ts = time.strftime("%H:%M:%S")
    ev = []
    if _prev:
        emp = int((cur["employed"] != _prev["employed"]).sum())
        if emp:
            ev.append(f"{emp} employment transitions")
        fs = int((cur["firm_sick"] != _prev["firm_sick"]).sum())
        if fs:
            ev.append(f"{fs} firms changed health state")
        dp = int((cur["deprived"] != _prev["deprived"]).sum())
        if dp:
            ev.append(f"{dp} households crossed the deprivation line")
        wp = int((cur["wealth_poor"] != _prev["wealth_poor"]).sum())
        if wp:
            ev.append(f"{wp} wealth-reserve transitions (<5 days)")
        deaths = int((_prev["alive"] & ~cur["alive"]).sum())
        births = int(st.get("births", 0))
        if deaths:
            ev.append(f"{deaths} deaths")
        if births:
            ev.append(f"{births} births")
        dm = cur["memories"] - _prev["memories"]
        if dm:
            ev.append(f"{dm:+d} standing memories")
        spread = st.get("memory_spread", 0)
        if spread:
            ev.append(f"{spread} memory spread events")
        casc = st.get("cascades_fired", 0)
        if casc:
            ev.append(f"{casc} threshold cascades fired")
        df = cur["forces"] - _prev["forces"]
        k = int(np.abs(df).argmax())
        if abs(df[k]) > 1e-5:
            ev.append(f"{Force(k).name} field {df[k]:+.4f}")
    for line in ev:
        PULSE.append({"t": ts, "day": day, "line": line})
    if not ev:
        PULSE.append({"t": ts, "day": day, "line": "a quiet day"})
    _prev = cur
    STATE["ticks"] += 1


def _pulse_loop():
    global _prev
    _prev = _snapshot_prev()
    while True:
        if not STATE["paused_for_branch"]:
            try:
                _pulse_tick()
            except Exception as e:               # surfaced, not hidden
                PULSE.append({"t": time.strftime("%H:%M:%S"),
                              "day": int(W.day),
                              "line": f"ENGINE ERROR: {e}"})
        time.sleep(TICK_SECONDS)


# ── news ingestion (editorial layer, separate from simulation) ──────
NEWS_CACHE = {"at": 0.0, "items": [], "error": None}
CATS = [
    ("conflict", ["war", "strike", "attack", "missile", "troops",
                  "ceasefire", "invasion", "military"]),
    ("geopolitics", ["sanction", "summit", "treaty", "nato", "un ",
                     "diplomat", "border"]),
    ("energy", ["oil", "gas", "opec", "pipeline", "energy", "barrel"]),
    ("economics", ["economy", "inflation", "recession", "gdp", "trade",
                   "tariff", "unemployment", "market"]),
    ("central-bank", ["fed ", "ecb", "rate cut", "rate hike",
                      "central bank"]),
    ("technology", ["ai ", "artificial intelligence", "chip", "launch",
                    "tech"]),
    ("corporate", ["bankrupt", "layoff", "merger", "acquisition",
                   "shares", "stock"]),
    ("climate", ["hurricane", "flood", "wildfire", "earthquake",
                 "drought", "heat wave", "storm", "typhoon"]),
    ("health", ["outbreak", "virus", "pandemic", "vaccine", "disease"]),
    ("politics", ["election", "vote", "parliament", "president",
                  "coup", "protest"]),
]
# editorial force-signature adapter per category: how this CLASS of
# event presses the 8 forces if branched (WorldEvent candidate). This
# is the ingestion adapter, not a simulation output.
CAT_ADAPTER = {
    "conflict":   {"forces": {"fear": 0.35, "collective": 0.15},
                   "firm_damage": 0.10, "trade_shock": 0.02,
                   "status": "READY TO BRANCH"},
    "climate":    {"forces": {"fear": 0.25}, "firm_damage": 0.12,
                   "status": "READY TO BRANCH"},
    "economics":  {"forces": {"economics": -0.20, "fear": 0.15},
                   "firm_damage": 0.08, "trade_shock": 0.03,
                   "status": "READY TO BRANCH"},
    "corporate":  {"forces": {"economics": -0.10}, "firm_damage": 0.15,
                   "status": "PARTIAL MODEL COVERAGE",
                   "missing": "sector-level firm exposure adapter"},
    "health":     {"forces": {"fear": 0.30}, "firm_damage": 0.05,
                   "status": "PARTIAL MODEL COVERAGE",
                   "missing": "epidemiological transmission adapter"},
    "geopolitics": {"forces": {"fear": 0.15, "identity": 0.10},
                    "trade_shock": 0.02,
                    "status": "PARTIAL MODEL COVERAGE",
                    "missing": "alliance/deterrence adapter"},
    "energy":     {"status": "INSUFFICIENT CAUSAL ADAPTER",
                   "missing": "energy/shipping chokepoint network, "
                              "commodity prices, pass-through"},
    "central-bank": {"status": "INSUFFICIENT CAUSAL ADAPTER",
                     "missing": "monetary/credit transmission"},
    "technology": {"status": "INSUFFICIENT CAUSAL ADAPTER",
                   "missing": "innovation-diffusion adapter"},
    "politics":   {"status": "PARTIAL MODEL COVERAGE",
                   "forces": {"identity": 0.15, "collective": 0.10},
                   "missing": "institutional/electoral adapter "
                              "(opinion readout exists; policy "
                              "consequence pass does not)"},
}
_COUNTRY_PAT = {c["iso2"]: re.compile(
    r"\b" + re.escape(c["name"]) + r"\b", re.I)
    for c in GENESIS_COUNTRIES}


def _fetch_news():
    url = ("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
    req = urllib.request.Request(url, headers={"User-Agent": "earth1"})
    xml = urllib.request.urlopen(req, timeout=8).read()
    root = ET.fromstring(xml)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = it.find("{*}source")
        items.append({
            "headline": title,
            "source": (src.text if src is not None else
                       (it.findtext("source") or "")),
            "published": it.findtext("pubDate") or "",
            "link": it.findtext("link") or ""})
    return items


def _rank_and_structure(raw):
    out = []
    for it in raw:
        tl = " " + it["headline"].lower() + " "
        cat, score = None, 0
        for c, kws in CATS:
            s = sum(2 if k in tl else 0 for k in kws)
            if s > score:
                cat, score = c, s
        if not cat:
            continue
        countries = [iso for iso, pat in _COUNTRY_PAT.items()
                     if pat.search(it["headline"])]
        ad = CAT_ADAPTER.get(cat, {})
        status = ad.get("status", "INSUFFICIENT CAUSAL ADAPTER")
        if status == "READY TO BRANCH" and not countries:
            status = "PARTIAL MODEL COVERAGE"
            ad = dict(ad)
            ad["missing"] = "geographic scope not resolved from headline"
        out.append({**it, "category": cat, "relevance": score,
                    "countries": countries,
                    "world_event": {
                        "forces": ad.get("forces"),
                        "firm_damage": ad.get("firm_damage", 0.0),
                        "trade_shock": ad.get("trade_shock", 0.0),
                        "persists_days": 30.0,
                        "adapter": "editorial category adapter "
                                   "(ingestion layer — NOT a "
                                   "simulation output)"},
                    "status": status,
                    "missing": ad.get("missing"),
                    "event_id": f"news{abs(hash(it['headline'])) % 10**8}"})
    out.sort(key=lambda x: -x["relevance"])
    # category diversity: at most 2 per category in the top 10
    seen, top = {}, []
    for it in out:
        if seen.get(it["category"], 0) >= 2:
            continue
        seen[it["category"]] = seen.get(it["category"], 0) + 1
        top.append(it)
        if len(top) == 10:
            break
    return top


def _news():
    now = time.time()
    if now - NEWS_CACHE["at"] > 600:
        try:
            NEWS_CACHE["items"] = _rank_and_structure(_fetch_news())
            NEWS_CACHE["error"] = None
        except Exception as e:
            NEWS_CACHE["error"] = (f"news ingestion unavailable: {e} "
                                   "(no canned headlines are shown)")
        NEWS_CACHE["at"] = now
    return NEWS_CACHE


# ── branching (the product): paired control/scenario, common dice ───
def _run_branch(event):
    eid = event["event_id"]
    B = BRANCHES[eid]
    try:
        we = event["world_event"]
        sc = Scenario(
            id=eid, label=event["headline"][:80],
            forces=we.get("forces") or {},
            countries=event["countries"] or None,
            firm_damage=we.get("firm_damage", 0.0),
            trade_shock=we.get("trade_shock", 0.0),
            persists_days=we.get("persists_days", 30.0))
        STATE["paused_for_branch"] = True
        with LOCK:
            base = copy.deepcopy(W)
            base_day = int(W.day)
        STATE["paused_for_branch"] = False

        iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
        if sc.countries:
            hit = np.isin(base.civ.country,
                          [iso[c] for c in sc.countries if c in iso])
        else:
            hit = np.ones(base.civ.n, dtype=bool)
        # earthlings selected BEFORE outcomes are inspected:
        # deterministic first-k employed members of the affected scope
        cand = np.flatnonzero(hit & base.health.alive
                              & base.life.employed)
        folk = [int(x) for x in cand[:3]]

        pairs = []
        for p in range(BRANCH_PAIRS):
            seed_p = SEED * 1000 + p
            rc = np.random.default_rng(seed_p)
            rs = np.random.default_rng(seed_p)   # common dice
            wc = copy.deepcopy(base)
            ws = copy.deepcopy(base)
            apply_scenario(ws, sc, rs)
            days = {"c": [], "s": []}
            for d in range(1, BRANCH_DAYS + 1):
                live_one_day(wc, rc)
                live_one_day(ws, rs)
                for tag, w_ in (("c", wc), ("s", ws)):
                    a = w_.health.alive & hit
                    lf = a & w_.life.in_lf
                    days[tag].append({
                        "day": d,
                        "employment": float(
                            w_.life.employed[lf].mean()) if lf.any()
                        else None,
                        "deprivation": float(
                            w_.life.deprivation[a].mean()),
                        "fear": float(
                            w_.civ.forces[a, Force.FEAR].mean()),
                        "firm_health": float(w_.life.firm_health[
                            np.isin(w_.life.firm_country,
                                    np.unique(base.civ.country[hit]))
                        ].mean()),
                        "alive": int(a.sum()),
                        "earthlings": [{
                            "id": i,
                            "employed": bool(w_.life.employed[i]),
                            "wealth_days": round(float(
                                w_.life.wealth[i]), 1),
                            "deprivation": round(float(
                                w_.life.deprivation[i]), 3),
                            "fear": round(float(
                                w_.civ.forces[i, Force.FEAR]), 3),
                        } for i in folk],
                    })
                B["progress"] = (p * BRANCH_DAYS + d) / (
                    BRANCH_PAIRS * BRANCH_DAYS)
            pairs.append(days)

        def diff(metric, day_idx):
            ds = [p_["s"][day_idx][metric] for p_ in pairs
                  if p_["s"][day_idx][metric] is not None]
            dc = [p_["c"][day_idx][metric] for p_ in pairs
                  if p_["c"][day_idx][metric] is not None]
            if not ds or not dc:
                return None
            d_ = [a - b for a, b in zip(ds, dc)]
            return {"mean": float(np.mean(d_)),
                    "spread": [float(min(d_)), float(max(d_))],
                    "pairs": len(d_)}

        last = BRANCH_DAYS - 1
        outcomes = {
            "employment_pp": diff("employment", last),
            "deprivation": diff("deprivation", last),
            "fear": diff("fear", last),
            "firm_health": diff("firm_health", last),
            "mortality": diff("alive", last),
        }
        B.update({
            "status": "done",
            "result": {
                "scenario": {"label": sc.label,
                             "countries": sc.countries,
                             "forces": sc.forces,
                             "firm_damage": sc.firm_damage,
                             "trade_shock": sc.trade_shock},
                "horizon_days": BRANCH_DAYS,
                "pairs": BRANCH_PAIRS,
                "base_day": base_day,
                "cohort_n": int(hit.sum()),
                "model_commit": MODEL_COMMIT,
                "physics": "Phase 0.8 candidate era — INCUMBENT "
                           "canonical physics (experimental flags "
                           "OFF); demo-scale world",
                "outcomes_day_final": outcomes,
                "series": pairs[0],       # first pair, full timeline
                "earthlings": folk,
                "not_yet_computable": [
                    {"metric": "Oil price",
                     "missing": "energy/shipping chokepoint adapter"},
                    {"metric": "Inflation",
                     "missing": "calibrated price pass-through"},
                    {"metric": "Migration",
                     "missing": "event-conditional migration adapter"},
                    {"metric": "Opinion readout",
                     "missing": "observer pass not run in this "
                                "branch (available in engine, not "
                                "wired into demo horizon)"},
                ],
                "causal_path_label": "MODEL ARCHITECTURE (executable "
                                     "pathway; per-write causal "
                                     "receipts NOT YET INSTRUMENTED)",
                "causal_path": ["scenario event", "chronicle memory + "
                                "firm damage + cost of living",
                                "firm health", "hiring / separation",
                                "employment", "household income & "
                                "wealth", "deprivation",
                                "force state (fear, economics)",
                                "conviction / opinion"],
            }})
    except Exception as e:
        import traceback
        B.update({"status": "error", "error": str(e),
                  "trace": traceback.format_exc()[-1500:]})
    finally:
        STATE["paused_for_branch"] = False


# ── routes ──────────────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse(ROOT / "dashboard" / "observatory.html")


@app.get("/api/identity")
def identity():
    with LOCK:
        a = W.health.alive
        f = W.civ.forces[a].mean(axis=0)
        return {
            "name": "EARTH-1 — LIVE CIVILIZATION",
            "mode": f"LOCAL DEMO CIVILIZATION (N={N:,}) — born through "
                    "the canonical engine at demo scale. The canonical "
                    "4M production world runs on the production box "
                    "and is READ-ONLY / not local.",
            "world_day": int(W.day),
            "population": int(W.civ.n),
            "alive": int(a.sum()),
            "countries": len(GENESIS_COUNTRIES),
            "model_commit": MODEL_COMMIT,
            "physics": "incumbent canonical physics; Phase 0.8 "
                       "candidate physics is experimental and "
                       "flag-gated OFF here",
            "seed": SEED,
            "born_at": STATE["born_at"],
            "ticks": STATE["ticks"],
            "memories_standing": len(W.chronicle.events),
            "forces": {Force(k).name: round(float(f[k]), 4)
                       for k in range(8)},
            "employment": round(float(
                W.life.employed[a & W.life.in_lf].mean()), 4),
            "deprivation": round(float(W.life.deprivation[a].mean()), 4),
        }


@app.get("/api/pulse")
def pulse():
    return {"pulse": list(PULSE)[-60:],
            "paused_for_branch": STATE["paused_for_branch"]}


@app.get("/api/news")
def news():
    n = _news()
    return {"items": n["items"], "error": n["error"],
            "ingested_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(NEWS_CACHE["at"])),
            "layer": "editorial relevance + category adapter — "
                     "separate from simulation"}


@app.post("/api/branch/{event_id}")
def start_branch(event_id: str):
    items = {i["event_id"]: i for i in NEWS_CACHE["items"]}
    ev = items.get(event_id)
    if ev is None:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    if ev["status"] == "INSUFFICIENT CAUSAL ADAPTER":
        return JSONResponse({"error": "insufficient causal adapter",
                             "missing": ev.get("missing")},
                            status_code=409)
    if event_id in BRANCHES and BRANCHES[event_id]["status"] in (
            "running", "done"):
        return BRANCHES[event_id]
    BRANCHES[event_id] = {"status": "running", "progress": 0.0}
    threading.Thread(target=_run_branch, args=(ev,), daemon=True).start()
    return BRANCHES[event_id]


@app.get("/api/branch/{event_id}")
def branch_status(event_id: str):
    b = BRANCHES.get(event_id)
    if b is None:
        return {"status": "not_started"}
    return b


threading.Thread(target=_pulse_loop, daemon=True).start()
