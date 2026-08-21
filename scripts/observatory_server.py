"""EARTH-1 — LIVE CIVILIZATION OBSERVATORY (local, read-only).

Investor-facing local dashboard over the REAL engine. Governing rules:
no second simulator, no mocked outputs, no physics added or tuned.
The world served here is a LOCAL DEMO CIVILIZATION born through the
canonical birth_world()/live_one_day() engine at demo scale — the
canonical 4M production world lives on the production box and is
never touched (read-only rule). Every number in the outcome table is
computed by the engine; the narration layer explains computed
results and covers non-computed channels QUALITATIVELY, always
labeled as analyst context, never as simulation output.
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

# repo convention: keys live in .env (see llm_gateway.py provider
# auto-detection); load without overriding an exported environment
_envf = ROOT / ".env"
if _envf.exists():
    for _line in _envf.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from earth1.alive import birth_world, live_one_day   # noqa: E402
from earth1.branch import Scenario, apply as apply_scenario  # noqa: E402
from earth1.types import Force                        # noqa: E402
from earth1.genesis import GENESIS_COUNTRIES          # noqa: E402
from earth1.life import OCCUPATIONS                   # noqa: E402

N = int(os.environ.get("EARTH1_OBS_N", "25000"))
SEED = int(os.environ.get("EARTH1_OBS_SEED", "1142"))
TICK_SECONDS = float(os.environ.get("EARTH1_OBS_TICK", "2.0"))
BRANCH_DAYS = int(os.environ.get("EARTH1_OBS_HORIZON", "30"))
BRANCH_PAIRS = int(os.environ.get("EARTH1_OBS_PAIRS", "4"))
PRECOMPUTE = int(os.environ.get("EARTH1_OBS_PRECOMPUTE", "3"))

app = FastAPI(title="Earth-1 Observatory (local)")

MODEL_COMMIT = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
    capture_output=True, text=True).stdout.strip() or "unknown"

LOCK = threading.Lock()
BRANCH_GATE = threading.Semaphore(1)     # one branch computation at a time
PULSE: deque = deque(maxlen=400)
HISTORY: deque = deque(maxlen=5000)      # daily aggregates of the world
CUSTOM_EVENTS: list = []                 # user-composed hypotheticals
STATE = {"born_at": None, "ticks": 0, "paused_for_branch": False,
         "births_total": 0, "deaths_total": 0, "news_ingested": 0}
BRANCHES: dict = {}          # branch_key -> {"status", "result", ...}
BASES: dict = {}             # event_id -> frozen base world for
                             # counterfactual component removal

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
            ev.append(f"{emp} people changed employment")
        fs = int((cur["firm_sick"] != _prev["firm_sick"]).sum())
        if fs:
            ev.append(f"{fs} firms changed health state")
        dp = int((cur["deprived"] != _prev["deprived"]).sum())
        if dp:
            ev.append(f"{dp} households crossed the deprivation line")
        wp = int((cur["wealth_poor"] != _prev["wealth_poor"]).sum())
        if wp:
            ev.append(f"{wp} families' reserves crossed 5 days")
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
            ev.append(f"{spread} memories spread between people")
        casc = st.get("cascades_fired", 0)
        if casc:
            ev.append(f"{casc} local threshold cascades")
        df = cur["forces"] - _prev["forces"]
        k = int(np.abs(df).argmax())
        if abs(df[k]) > 1e-5:
            ev.append(f"{Force(k).name} field moved {df[k]:+.4f}")
    for line in ev:
        PULSE.append({"t": ts, "day": day, "line": line})
    if not ev:
        PULSE.append({"t": ts, "day": day, "line": "a quiet day"})
    if _prev:
        STATE["deaths_total"] += int((_prev["alive"]
                                      & ~cur["alive"]).sum())
        STATE["births_total"] += int(st.get("births", 0))
    with LOCK:
        a = W.health.alive
        lf = a & W.life.in_lf
        HISTORY.append({
            "day": day,
            "alive": int(a.sum()),
            "employment": round(float(W.life.employed[lf].mean()), 4),
            "deprivation": round(float(
                W.life.deprivation[a].mean()), 4),
            "wealth": round(float(W.life.wealth[a].mean()), 2),
            "memories": len(W.chronicle.events),
            "forces": [round(float(x), 4) for x in
                       W.civ.forces[a].mean(axis=0)],
        })
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
# Every category has an ingestion adapter (editorial mapping from
# headline class to the engine's Scenario inputs), so EVERY event
# branches through the real engine. Channels the engine does not
# compute are named in estimated_channels and covered by the LLM
# estimation layer, each row tagged ESTIMATED in the UI.
_EST_ECON = ["consumer inflation (pp)", "government approval (pp)",
             "recession probability within 12m (%)"]
CAT_ADAPTER = {
    "conflict":   {"forces": {"fear": 0.35, "collective": 0.15},
                   "firm_damage": 0.10, "trade_shock": 0.02,
                   "status": "FULL BRANCH",
                   "estimated_channels": ["oil price (%)",
                                          "migration pressure (%)"]
                   + _EST_ECON},
    "climate":    {"forces": {"fear": 0.25}, "firm_damage": 0.12,
                   "status": "FULL BRANCH",
                   "estimated_channels": ["reconstruction cost",
                                          "migration pressure (%)"]
                   + _EST_ECON},
    "economics":  {"forces": {"economics": -0.20, "fear": 0.15},
                   "firm_damage": 0.08, "trade_shock": 0.03,
                   "status": "FULL BRANCH",
                   "estimated_channels": _EST_ECON},
    "corporate":  {"forces": {"economics": -0.10}, "firm_damage": 0.15,
                   "status": "HYBRID BRANCH",
                   "estimated_channels": ["sector contagion"]
                   + _EST_ECON},
    "health":     {"forces": {"fear": 0.30}, "firm_damage": 0.05,
                   "status": "HYBRID BRANCH",
                   "estimated_channels": ["case load direction"]
                   + _EST_ECON},
    "geopolitics": {"forces": {"fear": 0.15, "identity": 0.10},
                    "trade_shock": 0.02,
                    "status": "HYBRID BRANCH",
                    "estimated_channels": ["escalation likelihood (%)"]
                    + _EST_ECON},
    "energy":     {"forces": {"fear": 0.15, "economics": -0.15},
                   "firm_damage": 0.06, "trade_shock": 0.04,
                   "status": "HYBRID BRANCH",
                   "estimated_channels": ["oil price (%)",
                                          "shipping/freight cost (%)"]
                   + _EST_ECON},
    "central-bank": {"forces": {"economics": -0.10},
                     "trade_shock": 0.01,
                     "status": "HYBRID BRANCH",
                     "estimated_channels": ["policy rate path",
                                            "credit conditions"]
                     + _EST_ECON},
    "technology": {"forces": {"desire": 0.10, "economics": 0.05},
                   "status": "HYBRID BRANCH",
                   "estimated_channels": ["sector valuation",
                                          "productivity direction"]
                   + _EST_ECON},
    "politics":   {"forces": {"identity": 0.15, "collective": 0.10},
                   "status": "HYBRID BRANCH",
                   "estimated_channels": ["policy direction"]
                   + _EST_ECON,
                   "readout": "approval"},
    # custom-event categories (composer): both carry an OPINION
    # READOUT — the engine's own observer.ask, run identically on
    # scenario and control cohorts at the end of the branch
    "product-launch": {"forces": {"desire": 0.25, "culture": 0.10,
                                  "economics": 0.05},
                       "status": "FULL BRANCH",
                       "estimated_channels": [
                           "unit sales direction", "price positioning",
                           "competitor response"],
                       "readout": "adoption"},
    "political-campaign": {"forces": {"identity": 0.20,
                                      "collective": 0.10},
                           "status": "FULL BRANCH",
                           "estimated_channels": [
                               "turnout direction", "media reach"],
                           "readout": "approval"},
}
# readout question weight vectors (the instrument, disclosed in the
# result): stance = forces . w / sum|w|, adopters/supporters = >0.5
READOUTS = {
    "adoption": {"label": "WOULD THEY BUY IT?",
                 "weights": [0.0, 0.45, 0.25, 0.10, 0.0, 0.20,
                             0.0, 0.0]},
    "approval": {"label": "DO THEY SUPPORT IT?",
                 "weights": [-0.15, 0.0, 0.25, 0.35, 0.25, 0.0,
                             0.0, 0.0]},
}
# Qualitative analyst context per category for channels Earth-1 does
# not compute. NO magnitudes — direction/mechanism language only,
# always labeled as analyst context in the UI.
CAT_CONTEXT = {
    "energy": "Events of this class propagate through shipping "
              "routes, energy prices and import-dependent industry. "
              "Earth-1 does not yet compute these channels; the "
              "psychological and firm-level channels shown are the "
              "modeled subset.",
    "conflict": "Beyond the modeled fear, firm-damage and "
                "cost-of-living channels, conflicts of this class "
                "also move energy markets, migration flows and "
                "alliance politics — channels Earth-1 marks as not "
                "yet computable rather than guessing.",
    "climate": "Physical destruction and displacement beyond the "
               "modeled firm-damage channel — reconstruction "
               "spending, insurance, migration — are not yet "
               "computed.",
    "economics": "Price-level and monetary-policy responses are not "
                 "yet computed; the modeled channels are firm "
                 "health, employment, household reserves and the "
                 "psychological field.",
    "health": "Disease transmission itself is not modeled; the "
              "computed channels are the fear field and economic "
              "disruption of the announcement.",
    "politics": "Policy consequences of electoral outcomes are not "
                "yet computed; the modeled channels are identity/"
                "collective field response.",
    "corporate": "Sector contagion and supply-chain exposure are "
                 "not yet computed beyond the firm-health channel.",
    "geopolitics": "Deterrence dynamics and alliance shifts are not "
                   "yet computed.",
    "technology": "Innovation diffusion and productivity effects "
                  "are not yet computed.",
    "central-bank": "Monetary transmission is not yet computed.",
}
_COUNTRY_PAT = {c["iso2"]: re.compile(
    r"\b" + re.escape(c["name"]) + r"\b", re.I)
    for c in GENESIS_COUNTRIES}
_CNAME = {c["iso2"]: c["name"] for c in GENESIS_COUNTRIES}


def _fetch_news():
    url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
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
        status = ad.get("status", "HYBRID BRANCH")
        if status == "FULL BRANCH" and not countries:
            status = "HYBRID BRANCH"
            ad = dict(ad)
            ad["missing"] = "geographic scope not resolved from headline"
        out.append({**it, "category": cat, "relevance": score,
                    "countries": countries,
                    "country_names": [_CNAME[c] for c in countries],
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
                    "estimated_channels": ad.get("estimated_channels",
                                                 []),
                    "context": CAT_CONTEXT.get(cat),
                    "event_id": f"news{abs(hash(it['headline'])) % 10**8}"})
    out.sort(key=lambda x: -x["relevance"])
    seen, top = {}, []
    for it in out:
        if seen.get(it["category"], 0) >= 2:
            continue
        seen[it["category"]] = seen.get(it["category"], 0) + 1
        top.append(it)
        if len(top) == 10:
            break
    return top


def _ingest_into_world(items):
    """Top headlines enter the LIVING world's memory through the
    canonical chronicle path — the same mechanism scenarios use.
    Small salience: today's news is ambient, not a shock."""
    from earth1.memory import Memory
    iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
    ingested = 0
    with LOCK:
        have = {m.id for m in W.chronicle.events}
        for it in items[:3]:
            mid = f"news:{it['event_id']}"
            if mid in have or not it["world_event"].get("forces"):
                continue
            sig = np.zeros(8)
            for k, v in it["world_event"]["forces"].items():
                f = getattr(Force, k.upper(), None)
                if f is not None:
                    sig[f] = v * 0.15          # ambient, not a shock
            if it["countries"]:
                scope = np.isin(W.civ.country,
                                [iso[c] for c in it["countries"]])
            else:
                scope = np.ones(W.civ.n, dtype=bool)
            W.chronicle.remember(Memory(
                id=mid, label=it["headline"][:70], day=float(W.day),
                force_signature=sig, scope=scope, salience=0.4,
                half_life=10.0, origin="news"))
            ingested += 1
    if ingested:
        STATE["news_ingested"] += ingested
        PULSE.append({"t": time.strftime("%H:%M:%S"),
                      "day": int(W.day),
                      "line": f"{ingested} real-world headlines "
                              f"entered the world's memory"})


def _news():
    now = time.time()
    if now - NEWS_CACHE["at"] > 600:
        try:
            NEWS_CACHE["items"] = _rank_and_structure(_fetch_news())
            NEWS_CACHE["error"] = None
            _ingest_into_world(NEWS_CACHE["items"])
        except Exception as e:
            NEWS_CACHE["error"] = (f"news ingestion unavailable: {e} "
                                   "(no canned headlines are shown)")
        NEWS_CACHE["at"] = now
    return NEWS_CACHE


def _all_events():
    return CUSTOM_EVENTS + NEWS_CACHE["items"]


# ── narration (explains computed output; adds no numbers) ───────────
def _narrate(result, event):
    """Plain-English summary built ONLY from the computed outcomes.
    Every number quoted comes from the result dict."""
    o = result["outcomes"]["d30"]
    parts = []
    emp = o.get("employment_pp")
    if emp and emp["mean"] is not None:
        d = emp["mean"] * 100
        parts.append(
            f"employment in the affected population ends "
            f"{abs(d):.1f} points {'lower' if d < 0 else 'higher'} "
            f"than in the futures where it never happened "
            f"(range across {emp['pairs']} paired futures: "
            f"{emp['spread'][0]*100:+.1f} to {emp['spread'][1]*100:+.1f})")
    fear = o.get("fear")
    if fear:
        d = fear["mean"]
        parts.append(f"the fear field moves {d:+.3f}")
    dep = o.get("deprivation")
    if dep:
        parts.append(f"household deprivation moves {dep['mean']:+.3f}")
    fh = o.get("firm_health")
    if fh:
        parts.append(f"firm health moves {fh['mean']:+.3f}")
    computed = (
        f"Across {result['pairs']} matched pairs of futures — same "
        f"civilization, same dice, the only difference being whether "
        f"“{event['headline'][:70]}” happens — by day "
        f"{result['horizon_days']}: " + "; ".join(parts) +
        f". The spread between futures is the honest width of the "
        f"forecast: this world is measurably chaotic.")
    return computed


# ── LLM estimation layer (clearly labeled; never mixed with
#    simulated rows). Receives ONLY the computed outputs + headline;
#    estimates the named non-simulated channels with intervals. ──────
EST_MODEL = os.environ.get("EARTH1_OBS_EST_MODEL", "claude-sonnet-5")


def _estimate(event, result):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"available": False,
                "reason": "estimation layer offline — export "
                          "ANTHROPIC_API_KEY before launch"}
    o = result["outcomes"]["d30"]
    computed = {k: (round(v["mean"], 4) if v else None)
                for k, v in o.items()}
    channels = event.get("estimated_channels", [])
    prompt = (
        "You are the ESTIMATION LAYER of Earth-1, a civilization "
        "simulator. The engine computed these 30-day treatment-"
        "control differences for the event below; estimate ONLY the "
        "listed non-simulated channels. Rules: stay directionally "
        "consistent with the computed outputs; be conservative; "
        "give a central value and a wide interval; one short basis "
        "phrase each (outside-view/analog reasoning). These will be "
        "displayed to users tagged as ESTIMATED, next to rows tagged "
        "SIMULATED. Return STRICT JSON only: "
        '[{"metric": str, "value": str, "interval": str, '
        '"basis": str}]\n\n'
        f"EVENT: {event['headline']}\n"
        f"CLASS: {event['category']}; scope: "
        f"{event.get('country_names') or 'global'}\n"
        f"COMPUTED (30d, scenario minus control): "
        f"{json.dumps(computed)}\n"
        f"ESTIMATE THESE CHANNELS: {json.dumps(channels)}")
    body = json.dumps({"model": EST_MODEL, "max_tokens": 800,
                       "messages": [{"role": "user",
                                     "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        resp = json.loads(urllib.request.urlopen(
            req, timeout=45).read())
        txt = resp["content"][0]["text"]
        rows = json.loads(txt[txt.index("["):txt.rindex("]") + 1])
        return {"available": True, "model": EST_MODEL, "rows": rows,
                "label": "ESTIMATED by LLM from computed outputs + "
                         "outside-view reasoning — NOT simulated"}
    except Exception as e:
        return {"available": False,
                "reason": f"estimation call failed: {e}"}


# ── go-to-market message test: each MESSAGE is its own scenario ─────
# (a frame presses different forces; which message lands is a
# COMPUTED multi-arm branch against shared controls, not copywriting)
MESSAGES = {
    "product-launch": {
        "status":     {"label": "STATUS — “for the few who know”",
                       "forces": {"identity": 0.10, "desire": 0.25,
                                  "culture": 0.15}},
        "protection": {"label": "PROTECTION — “never lose what "
                                "you love”",
                       "forces": {"fear": 0.10, "desire": 0.20,
                                  "economics": 0.05}},
        "value":      {"label": "VALUE — “insured in minutes, "
                                "priced fairly”",
                       "forces": {"economics": 0.20, "desire": 0.15}},
    },
    "political-campaign": {
        "unity":     {"label": "UNITY — “what we can do together”",
                      "forces": {"collective": 0.20, "identity": 0.10}},
        "security":  {"label": "SECURITY — “keep what we have safe”",
                      "forces": {"fear": 0.10, "identity": 0.15,
                                 "economics": 0.05}},
        "prosperity": {"label": "PROSPERITY — “more in your pocket”",
                       "forces": {"economics": 0.20,
                                  "collective": 0.10}},
    },
}
GTM_PAIRS = 2
DEFAULT_PRICE = 120.0     # annual, ESTIMATED default; composer can set


def _run_gtm(event, key):
    """Multi-arm message test: per seed, ONE control + one world per
    message frame (common dice). Adoption readout per frame; personas
    pulled from the winning world with per-person stance
    decomposition (the readout formula's own receipt); revenue =
    SIMULATED adoption x real scoped adult population x ESTIMATED
    price — each factor labeled."""
    eid = event["event_id"]
    B = BRANCHES[key]
    try:
      with BRANCH_GATE:
        cat = event["category"]
        msgs = MESSAGES.get(cat)
        ro_key = CAT_ADAPTER[cat]["readout"]
        wgt = np.array(READOUTS[ro_key]["weights"])
        den = max(np.abs(wgt).sum(), 1e-9)
        if eid in BASES:
            base = BASES[eid]
        else:
            STATE["paused_for_branch"] = True
            with LOCK:
                base = copy.deepcopy(W)
            STATE["paused_for_branch"] = False
            BASES[eid] = base
        iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
        ccs = [c for c in (event["countries"] or []) if c in iso]
        if ccs:
            hit = np.isin(base.civ.country, [iso[c] for c in ccs])
        else:
            hit = np.ones(base.civ.n, dtype=bool)
        yrs = base.civ.age * 100.0
        cohorts = {
            "low income": base.civ.income == 0,
            "middle income": base.civ.income == 1,
            "high income": base.civ.income == 2,
            "under 30": yrs < 30, "30 to 55": (yrs >= 30) & (yrs < 55),
            "over 55": yrs >= 55,
            "urban": base.civ.urban, "rural": ~base.civ.urban}

        total = GTM_PAIRS * (1 + len(msgs)) * BRANCH_DAYS
        done_days = 0
        per_msg = {m: [] for m in msgs}
        last_worlds = {}
        for p in range(GTM_PAIRS):
            seed_p = SEED * 2000 + p
            wc = copy.deepcopy(base)
            rc = np.random.default_rng(seed_p)
            for d in range(BRANCH_DAYS):
                live_one_day(wc, rc)
                done_days += 1
                B["progress"] = done_days / total
            for m, spec in msgs.items():
                wsm = copy.deepcopy(base)
                rs = np.random.default_rng(seed_p)   # common dice
                sc = Scenario(id=f"{key}:{m}",
                              label=spec["label"][:70],
                              forces=spec["forces"],
                              countries=ccs or None,
                              firm_damage=0.0, trade_shock=0.0,
                              persists_days=30.0)
                apply_scenario(wsm, sc, rs)
                for d in range(BRANCH_DAYS):
                    live_one_day(wsm, rs)
                    done_days += 1
                    B["progress"] = done_days / total
                mro = hit & wc.health.alive & wsm.health.alive
                st_s = np.clip(wsm.civ.forces[mro] @ wgt / den, 0, 1)
                st_c = np.clip(wc.civ.forces[mro] @ wgt / den, 0, 1)
                thr = float(np.quantile(st_c, 0.75))
                by = {}
                for label, cmask in cohorts.items():
                    cm = cmask & mro
                    if cm.sum() >= 10:
                        s2 = np.clip(wsm.civ.forces[cm] @ wgt / den,
                                     0, 1)
                        by[label] = float((s2 > thr).mean())
                per_msg[m].append({
                    "rate": float((st_s > thr).mean()),
                    "anchor_rate": float((st_c > thr).mean()),
                    "by": by, "n": int(mro.sum())})
                if p == GTM_PAIRS - 1:
                    last_worlds[m] = (wsm, mro, st_s, thr)
        # aggregate
        ranking = []
        for m, spec in msgs.items():
            rs_ = per_msg[m]
            rate = float(np.mean([r["rate"] for r in rs_]))
            anchor = float(np.mean([r["anchor_rate"] for r in rs_]))
            spread = [float(min(r["rate"] for r in rs_)),
                      float(max(r["rate"] for r in rs_))]
            byavg = {}
            for label in rs_[0]["by"]:
                byavg[label] = float(np.mean(
                    [r["by"].get(label, np.nan) for r in rs_]))
            best_seg = max(byavg, key=byavg.get) if byavg else None
            ranking.append({"message": m, "label": spec["label"],
                            "forces": spec["forces"],
                            "rate": rate, "push_pp": (rate - anchor)
                            * 100, "spread": spread,
                            "by_segment": byavg,
                            "best_segment": best_seg})
        ranking.sort(key=lambda x: -x["rate"])
        win = ranking[0]["message"]

        # personas from the WINNING message's last world — real
        # earthlings, with the stance formula's own decomposition
        wsm, mro, st_s, thr = last_worlds[win]
        idxs = np.flatnonzero(mro)
        order = np.argsort(-st_s)
        personas = []
        used_cohort = set()
        adult = yrs >= 18

        def _bio(i, stance, adopter):
            occ = OCCUPATIONS[int(base.life.occupation[i])]
            contrib = {Force(k).name: round(float(
                wsm.civ.forces[i, k] * wgt[k] / den), 3)
                for k in range(8) if wgt[k]}
            return {"id": int(i), "age": int(round(yrs[i])),
                    "country": _CNAME[GENESIS_COUNTRIES[
                        int(base.civ.country[i])]["iso2"]],
                    "occupation": (occ[0] if isinstance(occ, tuple)
                                   else str(occ)).replace("_", " "),
                    "income": ["low", "middle", "high"][
                        int(base.civ.income[i])],
                    "urban": bool(base.civ.urban[i]),
                    "employed": bool(base.life.employed[i]),
                    "wealth_days": round(float(base.life.wealth[i]),
                                         1),
                    "stance": round(float(stance), 3),
                    "adopter": bool(adopter),
                    "stance_drivers": contrib}
        for oi in order:
            i = idxs[oi]
            if not adult[i]:
                continue
            ck = ("high" if base.civ.income[i] == 2 else
                  "urban" if base.civ.urban[i] else "other")
            if ck in used_cohort:
                continue
            used_cohort.add(ck)
            personas.append(_bio(i, st_s[oi], st_s[oi] > thr))
            if len(personas) == 3:
                break
        for oi in order[::-1]:
            i = idxs[oi]
            if adult[i]:
                personas.append(_bio(i, st_s[oi], st_s[oi] > thr))
                break

        # revenue scenarios: SIMULATED rate x real adult population
        # of scope x ESTIMATED price
        price = float(event.get("price") or DEFAULT_PRICE)
        world_pop = 8.3e9
        if ccs:
            adult_pop = sum(GENESIS_COUNTRIES[iso[c]]["pop"]
                            * (1 - GENESIS_COUNTRIES[iso[c]]["u18"])
                            for c in ccs) * world_pop
        else:
            adult_pop = world_pop * 0.72
        revenue = []
        for r_ in ranking:
            lo, hi = r_["spread"]
            revenue.append({
                "message": r_["message"],
                "adopters_mid": int(r_["rate"] * adult_pop),
                "adopters_range": [int(lo * adult_pop),
                                   int(hi * adult_pop)],
                "revenue_mid_usd": r_["rate"] * adult_pop * price,
                "revenue_range_usd": [lo * adult_pop * price,
                                      hi * adult_pop * price]})
        result = {
            "kind": "gtm", "event": event["headline"],
            "category": cat, "pairs": GTM_PAIRS,
            "horizon_days": BRANCH_DAYS,
            "scope": event.get("country_names") or ["global"],
            "adult_population_scope": int(adult_pop),
            "price_assumed_usd": price,
            "ranking": ranking, "winner": win,
            "personas": personas,
            "revenue": revenue,
            "labels": {
                "adoption": "SIMULATED (top-quartile propensity "
                            "anchor, disclosed)",
                "population_scaling": "MECHANICAL (real adult "
                                      "population of scope)",
                "price": "ESTIMATED (composer default — set your "
                         "own)",
                "personas": "REAL simulated people from the winning "
                            "message's world; stance_drivers is the "
                            "readout formula's own decomposition"},
            "model_commit": MODEL_COMMIT}
        # analyst GTM plan from computed results only
        keyk = os.environ.get("ANTHROPIC_API_KEY")
        if keyk:
            try:
                pr = ("You are the analyst layer of Earth-1. Using "
                      "ONLY these computed message-test results, "
                      "write a go-to-market recommendation: lead "
                      "message, target segments in order, channel "
                      "suggestions, one risk. Do not invent numbers "
                      "not present. Max 130 words.\n"
                      + json.dumps({"ranking": ranking,
                                    "revenue": revenue}, default=str))
                body = json.dumps({"model": EST_MODEL,
                                   "max_tokens": 400,
                                   "messages": [{"role": "user",
                                                 "content": pr}]}
                                  ).encode()
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=body,
                    headers={"x-api-key": keyk,
                             "anthropic-version": "2023-06-01",
                             "content-type": "application/json"})
                resp = json.loads(urllib.request.urlopen(
                    req, timeout=45).read())
                result["gtm_plan"] = resp["content"][0]["text"]
                result["gtm_plan_label"] = ("ANALYST LAYER — written "
                                            "from the computed "
                                            "results above")
            except Exception:
                pass
        B.update({"status": "done", "result": result})
    except Exception as e:
        import traceback
        B.update({"status": "error", "error": str(e),
                  "trace": traceback.format_exc()[-1500:]})
    finally:
        STATE["paused_for_branch"] = False


# ── branching (the product): paired control/scenario, common dice ───
def _lens_mask(base, lens):
    """Resolve 'US' or 'US-NE' to a population mask. Only geography
    Earth-1 actually represents; returns (mask, description)."""
    from earth1.regions import get_regions
    iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
    part = lens.strip().upper()
    cc = part.split("-")[0]
    if cc not in iso:
        return None, f"unknown country {cc}"
    m = base.civ.country == iso[cc]
    desc = _CNAME[cc]
    if "-" in part:
        codes = [r.code for r in get_regions(cc)]
        if part in codes:
            m = m & (base.civ.region == codes.index(part))
            desc = f"{part} ({_CNAME[cc]})"
        else:
            desc = (f"{_CNAME[cc]} — region {part} not modeled; "
                    f"nearest modeled geography is country level "
                    f"(regions: {', '.join(codes)})")
    return m, desc


def _run_branch(event, branch_key=None, remove=None, lens=None):
    """remove='material' zeroes firm_damage/trade_shock (memory-only
    scenario); remove='informational' zeroes the force signature
    (material-only). A removal reuses the SAME frozen base world and
    the SAME dice as the full branch, so scenario-minus-component is
    a computed attribution, never an algebraic guess."""
    eid = event["event_id"]
    key = branch_key or eid
    B = BRANCHES[key]
    try:
      with BRANCH_GATE:
        we = dict(event["world_event"])
        if remove == "material":
            we["firm_damage"] = 0.0
            we["trade_shock"] = 0.0
        if remove == "informational":
            we["forces"] = {}
        sc = Scenario(
            id=key, label=event["headline"][:80],
            forces=we.get("forces") or {},
            countries=event["countries"] or None,
            firm_damage=we.get("firm_damage", 0.0),
            trade_shock=we.get("trade_shock", 0.0),
            persists_days=we.get("persists_days", 30.0))
        if eid in BASES:
            base = BASES[eid]
            base_day = int(base.day)
        else:
            STATE["paused_for_branch"] = True
            with LOCK:
                base = copy.deepcopy(W)
                base_day = int(W.day)
            STATE["paused_for_branch"] = False
            BASES[eid] = base

        iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
        if sc.countries:
            hit = np.isin(base.civ.country,
                          [iso[c] for c in sc.countries if c in iso])
        else:
            hit = np.ones(base.civ.n, dtype=bool)
        scope0 = hit & base.health.alive
        lmask, ldesc = (None, None)
        if lens:
            lmask, ldesc = _lens_mask(base, lens)

        # WHO cohorts, defined on the BASE world (pre-outcome)
        yrs = base.civ.age * 100.0
        cohorts = {
            "low income": scope0 & (base.civ.income == 0),
            "middle income": scope0 & (base.civ.income == 1),
            "high income": scope0 & (base.civ.income == 2),
            "under 30": scope0 & (yrs < 30),
            "30 to 55": scope0 & (yrs >= 30) & (yrs < 55),
            "over 55": scope0 & (yrs >= 55),
            "urban": scope0 & base.civ.urban,
            "rural": scope0 & ~base.civ.urban,
        }

        # earthlings selected BEFORE outcomes: one employed member of
        # three different cohorts, deterministic order
        folk = []
        adult = yrs >= 18
        for key in ("low income", "middle income", "urban"):
            cand = np.flatnonzero(cohorts[key] & base.life.employed
                                  & adult)
            for c in cand:
                if int(c) not in folk:
                    folk.append(int(c))
                    break
        folk = folk[:3]
        bios = []
        for i in folk:
            occ = OCCUPATIONS[int(base.life.occupation[i])]
            bios.append({
                "id": i, "age": int(round(yrs[i])),
                "country": _CNAME.get(
                    GENESIS_COUNTRIES[int(base.civ.country[i])]["iso2"],
                    "?"),
                "occupation": (occ[0] if isinstance(occ, tuple)
                               else str(occ)).replace("_", " "),
                "urban": bool(base.civ.urban[i]),
                "income": ["low", "middle", "high"][
                    int(base.civ.income[i])],
            })

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
                        "wealth": float(w_.life.wealth[a].mean()),
                        "fear": float(
                            w_.civ.forces[a, Force.FEAR].mean()),
                        "firm_health": float(w_.life.firm_health[
                            np.isin(w_.life.firm_country,
                                    np.unique(base.civ.country[hit]))
                        ].mean()),
                        "alive": int(a.sum()),
                        **({} if lmask is None else (lambda la, llf: {
                            "l_employment": float(
                                w_.life.employed[llf].mean())
                            if llf.any() else None,
                            "l_deprivation": float(
                                w_.life.deprivation[la].mean()),
                            "l_wealth": float(
                                w_.life.wealth[la].mean()),
                            "l_fear": float(
                                w_.civ.forces[la, Force.FEAR].mean()),
                            "l_alive": int(la.sum()),
                        })(w_.health.alive & lmask,
                           w_.health.alive & lmask & w_.life.in_lf)),
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
            # opinion readout (product adoption / approval): the
            # observer's stance construction (observer.py) with the
            # disclosed question weights, run IDENTICALLY on both
            # worlds' cohorts at the end of the pair
            ro_key = CAT_ADAPTER.get(event["category"], {}).get(
                "readout")
            ro_p = None
            if ro_key:
                wgt = np.array(READOUTS[ro_key]["weights"])
                den = max(np.abs(wgt).sum(), 1e-9)
                mro = hit & wc.health.alive & ws.health.alive
                st_s = np.clip(ws.civ.forces[mro] @ wgt / den, 0, 1)
                st_c = np.clip(wc.civ.forces[mro] @ wgt / den, 0, 1)
                # the propensity scale is unanchored in absolute
                # terms; "adopter/supporter" is anchored at the
                # CONTROL world's top quartile (disclosed instrument
                # — control rate is ~25% by construction, the
                # scenario rate shows the event's own push across a
                # fixed bar)
                thr = float(np.quantile(st_c, 0.75))
                ro_p = {"scenario_rate": float((st_s > thr).mean()),
                        "control_rate": float((st_c > thr).mean()),
                        "stance_shift": float(st_s.mean()
                                              - st_c.mean()),
                        "anchor": thr,
                        "n": int(mro.sum()), "by": {}}
                for label, cmask in cohorts.items():
                    cm = (cmask & hit & wc.health.alive
                          & ws.health.alive)
                    if cm.sum() >= 10:
                        s2 = np.clip(ws.civ.forces[cm] @ wgt / den,
                                     0, 1)
                        c2 = np.clip(wc.civ.forces[cm] @ wgt / den,
                                     0, 1)
                        ro_p["by"][label] = {
                            "scenario": float((s2 > thr).mean()),
                            "delta": float((s2 > thr).mean()
                                           - (c2 > thr).mean()),
                            "n": int(cm.sum())}
            # full 8-force human response at final day, this pair
            mboth = hit & wc.health.alive & ws.health.alive
            fdiff = (ws.civ.forces[mboth].mean(axis=0)
                     - wc.civ.forces[mboth].mean(axis=0))
            # WHO decomposition at final day, this pair
            who_p = {}
            for label, mask in cohorts.items():
                m = mask & wc.health.alive & ws.health.alive
                lfm = m & wc.life.in_lf & ws.life.in_lf
                if lfm.sum() >= 10:
                    who_p[label] = {
                        "employment_pp": float(
                            ws.life.employed[lfm].mean()
                            - wc.life.employed[lfm].mean()),
                        "fear": float(
                            ws.civ.forces[m, Force.FEAR].mean()
                            - wc.civ.forces[m, Force.FEAR].mean()),
                        "n": int(lfm.sum())}
            pairs.append({"days": days, "who": who_p, "readout": ro_p,
                          "forces_final": [float(x) for x in fdiff]})

        def diff(metric, day_idx):
            ds = [p_["days"]["s"][day_idx][metric] for p_ in pairs
                  if p_["days"]["s"][day_idx][metric] is not None]
            dc = [p_["days"]["c"][day_idx][metric] for p_ in pairs
                  if p_["days"]["c"][day_idx][metric] is not None]
            if not ds or not dc:
                return None
            d_ = [a - b for a, b in zip(ds, dc)]
            return {"mean": float(np.mean(d_)),
                    "spread": [float(min(d_)), float(max(d_))],
                    "pairs": len(d_)}

        def outcome_block(day_idx):
            return {
                "employment_pp": diff("employment", day_idx),
                "reserves_days": diff("wealth", day_idx),
                "deprivation": diff("deprivation", day_idx),
                "fear": diff("fear", day_idx),
                "firm_health": diff("firm_health", day_idx),
                "mortality": diff("alive", day_idx),
            }

        # fan series: every pair, both arms, three metrics (compact)
        fan = {}
        for metric in ("employment", "fear", "deprivation"):
            fan[metric] = {
                "c": [[p_["days"]["c"][d][metric] for d in
                       range(BRANCH_DAYS)] for p_ in pairs],
                "s": [[p_["days"]["s"][d][metric] for d in
                       range(BRANCH_DAYS)] for p_ in pairs]}

        # WHO aggregated over pairs
        who = {}
        for label in cohorts:
            vals = [p_["who"].get(label) for p_ in pairs
                    if p_["who"].get(label)]
            if vals:
                who[label] = {
                    "employment_pp": float(np.mean(
                        [v["employment_pp"] for v in vals])),
                    "fear": float(np.mean([v["fear"] for v in vals])),
                    "n": vals[0]["n"]}

        result = {
            "scenario": {"label": sc.label,
                         "countries": sc.countries,
                         "country_names": event.get("country_names"),
                         "forces": sc.forces,
                         "firm_damage": sc.firm_damage,
                         "trade_shock": sc.trade_shock},
            "horizon_days": BRANCH_DAYS,
            "pairs": BRANCH_PAIRS,
            "base_day": base_day,
            "cohort_n": int(scope0.sum()),
            "model_commit": MODEL_COMMIT,
            "physics": "incumbent canonical physics (Phase 0.8 "
                       "candidate flags OFF); demo-scale world",
            "outcomes": {"d7": outcome_block(6),
                         "d30": outcome_block(BRANCH_DAYS - 1)},
            "fan": fan,
            "who": who,
            "series": pairs[0]["days"],
            "earthlings": bios,
            "estimated_channels": event.get("estimated_channels", []),
            "removed_component": remove,
            "analyst_context": event.get("context"),
            "causal_path_label": "MODEL ARCHITECTURE (executable "
                                 "pathway; per-write causal receipts "
                                 "NOT YET INSTRUMENTED)",
            "causal_path": ["scenario event", "memory + firm damage "
                            "+ cost of living", "firm health",
                            "hiring / separation", "employment",
                            "household income & wealth",
                            "deprivation", "force state",
                            "conviction / opinion"],
        }
        # lens outcomes
        if lmask is not None:
            result["lens"] = {"query": lens, "resolved": ldesc,
                              "cohort_n": int((lmask
                                               & base.health.alive
                                               ).sum())}
            result["outcomes_lens"] = {
                "d7": {"employment_pp": diff("l_employment", 6),
                       "reserves_days": diff("l_wealth", 6),
                       "deprivation": diff("l_deprivation", 6),
                       "fear": diff("l_fear", 6),
                       "mortality": diff("l_alive", 6)},
                "d30": {"employment_pp": diff("l_employment",
                                              BRANCH_DAYS - 1),
                        "reserves_days": diff("l_wealth",
                                              BRANCH_DAYS - 1),
                        "deprivation": diff("l_deprivation",
                                            BRANCH_DAYS - 1),
                        "fear": diff("l_fear", BRANCH_DAYS - 1),
                        "mortality": diff("l_alive",
                                          BRANCH_DAYS - 1)}}
        # opinion readout aggregated over pairs
        ros = [p_["readout"] for p_ in pairs if p_.get("readout")]
        if ros:
            ro_key = CAT_ADAPTER[event["category"]]["readout"]
            by = {}
            for label in ros[0]["by"]:
                vals = [r_["by"][label] for r_ in ros
                        if label in r_["by"]]
                by[label] = {
                    "scenario": float(np.mean(
                        [v["scenario"] for v in vals])),
                    "delta_pp": float(np.mean(
                        [v["delta"] for v in vals])) * 100,
                    "n": vals[0]["n"]}
            sr = float(np.mean([r_["scenario_rate"] for r_ in ros]))
            cr = float(np.mean([r_["control_rate"] for r_ in ros]))
            result["readout"] = {
                "type": ro_key,
                "label": READOUTS[ro_key]["label"],
                "weights": {Force(k).name: w for k, w in
                            enumerate(READOUTS[ro_key]["weights"])
                            if w},
                "scenario_rate": sr, "control_rate": cr,
                "delta_pp": (sr - cr) * 100,
                "asked_n": ros[0]["n"],
                "buyers_in_cohort": int(round(sr * ros[0]["n"])),
                "by_cohort": by,
                "method": "observer stance construction "
                          "(observer.py) with the disclosed question "
                          "weights, computed identically on scenario "
                          "and control worlds"}
        result["human_response"] = {
            Force(k).name: float(np.mean(
                [p_["forces_final"][k] for p_ in pairs]))
            for k in range(8)}
        result["summary_computed"] = _narrate(result, event)
        if remove is None:
            result["estimated"] = _estimate(event, result)
        B.update({"status": "done", "result": result})
    except Exception as e:
        import traceback
        B.update({"status": "error", "error": str(e),
                  "trace": traceback.format_exc()[-1500:]})
    finally:
        STATE["paused_for_branch"] = False


def _precompute_loop():
    """Branch the first READY events in the background so cards feel
    immediate. Startup is never blocked."""
    time.sleep(20)
    try:
        _news()
        ready = [i for i in NEWS_CACHE["items"]
                 if i["status"] == "READY TO BRANCH"][:PRECOMPUTE]
        for ev in ready:
            if ev["event_id"] not in BRANCHES:
                BRANCHES[ev["event_id"]] = {"status": "running",
                                            "progress": 0.0}
                _run_branch(ev)
    except Exception as e:
        print(f"[observatory] precompute: {e}", flush=True)


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


@app.get("/api/history")
def history():
    return {"history": list(HISTORY),
            "births_total": STATE["births_total"],
            "deaths_total": STATE["deaths_total"],
            "news_ingested": STATE["news_ingested"],
            "force_names": [Force(k).name for k in range(8)]}


@app.post("/api/custom")
async def custom_event(payload: dict):
    """Compose a hypothetical event: product launch, campaign, or any
    adapter category. Branches through the identical machinery."""
    cat = payload.get("category", "product-launch")
    if cat not in CAT_ADAPTER:
        return JSONResponse({"error": f"unknown category {cat}",
                             "known": list(CAT_ADAPTER)},
                            status_code=400)
    headline = (payload.get("headline") or "").strip()
    if not headline:
        return JSONResponse({"error": "headline required"},
                            status_code=400)
    raw = payload.get("countries") or []
    if isinstance(raw, str):
        raw = [x.strip().upper() for x in raw.split(",") if x.strip()]
    countries = [c for c in raw if c in _CNAME]
    ad = CAT_ADAPTER[cat]
    item = {"headline": headline, "source": "COMPOSED HYPOTHETICAL",
            "published": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                       time.gmtime()),
            "link": "", "category": cat, "relevance": 99,
            "countries": countries,
            "country_names": [_CNAME[c] for c in countries],
            "world_event": {
                "forces": ad.get("forces"),
                "firm_damage": ad.get("firm_damage", 0.0),
                "trade_shock": ad.get("trade_shock", 0.0),
                "persists_days": 30.0,
                "adapter": f"{cat} adapter (composed hypothetical — "
                           "NOT observed news)"},
            "status": ad.get("status", "HYBRID BRANCH"),
            "missing": None, "custom": True,
            "price": payload.get("price"),
            "estimated_channels": ad.get("estimated_channels", []),
            "context": CAT_CONTEXT.get(cat),
            "event_id": f"custom{abs(hash(headline)) % 10**8}"}
    CUSTOM_EVENTS.insert(0, item)
    return item


@app.get("/api/news")
def news():
    n = _news()
    items = []
    for i in _all_events():
        b = BRANCHES.get(i["event_id"])
        badge = None
        if b and b.get("status") == "done":
            o = b["result"]["outcomes"]["d30"]
            best = None
            if o.get("employment_pp"):
                best = f"{o['employment_pp']['mean']*100:+.1f} pp " \
                       f"employment @ d30"
            elif o.get("fear"):
                best = f"{o['fear']['mean']:+.3f} fear @ d30"
            badge = {"status": "done",
                     "futures": 2 * b["result"]["pairs"],
                     "headline_outcome": best}
        elif b:
            badge = {"status": b.get("status"),
                     "progress": b.get("progress", 0)}
        items.append({**i, "branch": badge})
    return {"items": items, "error": n["error"],
            "ingested_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(NEWS_CACHE["at"])),
            "layer": "editorial relevance + category adapter — "
                     "separate from simulation"}


@app.post("/api/branch/{event_id}")
def start_branch(event_id: str, lens: str = None):
    items = {i["event_id"]: i for i in _all_events()}
    ev = items.get(event_id)
    if ev is None:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    key = event_id + (f":lens-{lens.strip().upper()}" if lens else "")
    if key in BRANCHES and BRANCHES[key]["status"] in (
            "running", "done"):
        return BRANCHES[key]
    BRANCHES[key] = {"status": "running", "progress": 0.0}
    threading.Thread(target=_run_branch,
                     args=(ev, key, None, lens),
                     daemon=True).start()
    return BRANCHES[key]


@app.get("/api/branch/{event_id}")
def branch_status(event_id: str):
    b = BRANCHES.get(event_id)
    if b is None:
        return {"status": "not_started"}
    return b


@app.post("/api/branch/{event_id}/gtm")
def start_gtm(event_id: str):
    """Go-to-market message test: multi-arm computed branch."""
    items = {i["event_id"]: i for i in _all_events()}
    ev = items.get(event_id)
    if ev is None:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    if ev["category"] not in MESSAGES:
        return JSONResponse({"error": "message test available for "
                             "product-launch and political-campaign"},
                            status_code=400)
    key = f"{event_id}:gtm"
    if key in BRANCHES and BRANCHES[key]["status"] in ("running",
                                                       "done"):
        return BRANCHES[key]
    BRANCHES[key] = {"status": "running", "progress": 0.0}
    threading.Thread(target=_run_gtm, args=(ev, key),
                     daemon=True).start()
    return BRANCHES[key]


@app.post("/api/branch/{event_id}/remove/{component}")
def remove_component(event_id: str, component: str):
    """Counterfactual removal: re-branch from the SAME frozen base
    with one causal component removed. Computed attribution."""
    if component not in ("material", "informational"):
        return JSONResponse({"error": "component must be material or "
                             "informational"}, status_code=400)
    if BRANCHES.get(event_id, {}).get("status") != "done":
        return JSONResponse({"error": "run the full branch first"},
                            status_code=409)
    items = {i["event_id"]: i for i in _all_events()}
    ev = items.get(event_id)
    if ev is None:
        return JSONResponse({"error": "unknown event"}, status_code=404)
    key = f"{event_id}:no-{component}"
    if key in BRANCHES and BRANCHES[key]["status"] in ("running",
                                                       "done"):
        return BRANCHES[key]
    BRANCHES[key] = {"status": "running", "progress": 0.0}
    threading.Thread(target=_run_branch, args=(ev, key, component),
                     daemon=True).start()
    return BRANCHES[key]


threading.Thread(target=_pulse_loop, daemon=True).start()
threading.Thread(target=_precompute_loop, daemon=True).start()
