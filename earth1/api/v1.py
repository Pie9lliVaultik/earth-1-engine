"""EARTH-1 API v1 — THE typed ship surface (founder ruling 2026-09-01).

One adapter, six endpoints. Read-only by construction:
  * no code path in this module opens any file whose data-role is
    HOLDOUT or PROSPECTIVE-outcome; the register is read only to
    DISPLAY registered forecasts (p_model + first-seen market price);
  * branch runs happen on deepcopies of dedicated fidelity snapshots
    (EARTH1_FIDELITY_20K / _200K pickles) — the canonical living world
    and production epochs are untouched by any request;
  * the only write is the append-only, hash-chained question log.
No response carries a number from an ABSTAIN line; p_blended does not
exist anywhere on this surface (p_market is display-only).
"""
from __future__ import annotations
from typing import Optional

import copy
import hashlib
import json
import os
import subprocess
import threading
import time
import uuid

from fastapi import APIRouter, Header, HTTPException

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
router = APIRouter(prefix="/v1", tags=["v1"])

FREEZE_TAG = "freeze-0.9"
EPOCH = os.environ.get("EARTH1_EPOCH", "3-lab")
QLOG = os.environ.get("EARTH1_QUESTION_LOG",
                      "/opt/earth1-data/api_question_log.jsonl")
_FIDELITY = {"20k": os.environ.get("EARTH1_FIDELITY_20K",
                                   "/opt/earth1-data/sign_b/base.pkl"),
             "200k": os.environ.get("EARTH1_FIDELITY_200K",
                                    "/opt/earth1-data/five/base200k.pkl")}
_worlds: dict = {}
_jobs: dict = {}
_cache: dict = {}
_rate: dict = {}
_qlock = threading.Lock()


def _tree_hash():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True,
                              cwd=_ROOT).stdout.strip()
    except Exception:
        return "unknown"


_TREE = _tree_hash()


def _forbid_sealed(path: str):
    """dataroles guard: raise on any HOLDOUT/PROSPECTIVE-role file."""
    try:
        roles = json.load(open(os.path.join(_ROOT, "data",
                                            "data_roles.json")))
    except Exception:
        return
    base = os.path.basename(path)
    for name, meta in (roles.items() if isinstance(roles, dict) else []):
        role = (meta.get("role") if isinstance(meta, dict) else None)
        if base in name and role in ("HOLDOUT", "PROSPECTIVE"):
            raise HTTPException(403, f"sealed role {role}: {base}")


def _auth(authorization: str | None):
    keys = [k for k in os.environ.get("EARTH1_API_KEYS", "").split(",") if k]
    if not keys:
        return "anonymous-dev"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "bearer token required")
    tok = authorization[7:]
    if tok not in keys:
        raise HTTPException(403, "unknown key")
    now = time.time()
    win = _rate.setdefault(tok, [])
    win[:] = [t for t in win if now - t < 60]
    if len(win) >= int(os.environ.get("EARTH1_API_RPM", "30")):
        raise HTTPException(429, "rate limit")
    win.append(now)
    return tok


def _qlog(kind, body, key):
    rec = {"kind": kind, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime()),
           "key": hashlib.sha256(key.encode()).hexdigest()[:12],
           "tree_hash": _TREE,
           "body_sha256": hashlib.sha256(
               json.dumps(body, sort_keys=True, default=str).encode()
           ).hexdigest()}
    with _qlock:
        prev = "GENESIS"
        if os.path.exists(QLOG):
            for line in open(QLOG):
                prev = json.loads(line)["_hash"]
        rec["_prev"] = prev
        rec["_hash"] = hashlib.sha256(
            json.dumps(rec, sort_keys=True).encode()).hexdigest()
        with open(QLOG, "a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")


def _world(fidelity):
    if fidelity not in _FIDELITY:
        raise HTTPException(400, f"fidelity must be one of "
                            f"{sorted(_FIDELITY)}")
    if fidelity not in _worlds:
        from earth1 import persistence
        p = _FIDELITY[fidelity]
        _forbid_sealed(p)
        if not os.path.exists(p):
            raise HTTPException(503, f"fidelity snapshot missing: {p}")
        w, _, _ = persistence.load_world(p)
        _worlds[fidelity] = w
    return _worlds[fidelity]


def _envelope(fidelity, extra=None):
    w = _worlds.get(fidelity)
    return {"epoch": EPOCH, "freeze_tag": FREEZE_TAG, "tree_hash": _TREE,
            "fidelity": fidelity,
            "ledger_cutoff_day": (float(w.day) if w is not None else None),
            **(extra or {})}


def _centroids():
    return json.load(open(os.path.join(
        _ROOT, "data/geo/country_centroids.json")))["centroids"]


@router.post("/ask")
def ask(body: dict, authorization: Optional[str] = Header(None)):
    key = _auth(authorization)
    _qlog("ask", body, key)
    fidelity = body.get("fidelity", "20k")
    q = {"question_id": body.get("question_id") or f"api:{uuid.uuid4().hex[:10]}",
         "text": body.get("text", ""), "class": body.get("class"),
         "outcomes": body.get("outcomes"), "country": body.get("country"),
         "p_market": body.get("p_market")}
    if fidelity == "200k":
        jid = uuid.uuid4().hex[:12]
        _jobs[jid] = {"status": "queued"}

        def run():
            try:
                from earth1.adapters import router as rt
                w = copy.deepcopy(_world("200k"))
                _jobs[jid] = {"status": "done",
                              "payload": rt.answer_any(q, w, seed=int(hashlib.sha256(
                                  q["question_id"].encode()
                              ).hexdigest()[:8], 16) % 99991,
                              horizon_days=60)}
            except Exception as e:
                _jobs[jid] = {"status": "error", "error": repr(e)}
        threading.Thread(target=run, daemon=True).start()
        return _envelope(fidelity, {"job_id": jid, "status": "queued"})
    from earth1.adapters import router as rt
    w = copy.deepcopy(_world(fidelity))
    payload = rt.answer_any(q, w, seed=int(hashlib.sha256(
        q["question_id"].encode()).hexdigest()[:8], 16) % 99991,
                            horizon_days=45)
    return _envelope(fidelity, {"result": payload})


@router.post("/consequences")
def consequences(body: dict, authorization: Optional[str] = Header(None)):
    key = _auth(authorization)
    _qlog("consequences", body, key)
    fidelity = body.get("fidelity", "20k")
    n_seeds = max(8, min(32, int(body.get("seeds", 8))))
    seeds = list(range(11, 11 + n_seeds))
    horizon = int(body.get("horizon_days", 60))
    from earth1.branch import Scenario
    sc = body.get("scenario", {})
    scenario = Scenario(id=sc.get("id", f"api:{uuid.uuid4().hex[:8]}"),
                        label=sc.get("label", "api scenario"),
                        forces=sc.get("forces", {}),
                        countries=sc.get("countries"),
                        firm_damage=float(sc.get("firm_damage", 0.0)),
                        trade_shock=float(sc.get("trade_shock", 0.0)),
                        persists_days=float(sc.get("persists_days", 60)))
    w0 = _world(fidelity)
    ck = hashlib.sha256(json.dumps(
        [sc, float(w0.day), fidelity, seeds, horizon],
        sort_keys=True, default=str).encode()).hexdigest()[:24]
    if ck in _cache:
        return _envelope(fidelity, {"cached": True, "report": _cache[ck]})
    from earth1.adapters.consequences import consequence_report
    spec = {"question_id": scenario.id, "class": body.get("class"),
            "scenario": scenario}
    rep = consequence_report(spec, copy.deepcopy(w0), seeds,
                             horizon=horizon)
    cents = _centroids()
    for row in rep["order1"]["top_country_movers"]:
        row["centroid"] = cents.get(row["country"])
        row["adm1"] = None            # engine has no adm1 geography yet
    _cache[ck] = rep
    return _envelope(fidelity, {"cached": False, "cache_key": ck,
                                "report": rep})


@router.get("/forecast/{qid}")
def forecast(qid: str, authorization: Optional[str] = Header(None)):
    key = _auth(authorization)
    _qlog("forecast_lookup", {"qid": qid}, key)
    reg = os.path.join(_ROOT, "ops/alive/PROSPECTIVE_REGISTER.jsonl")
    latest = None
    for line in open(reg):
        e = json.loads(line)
        if e.get("question_id") == qid:
            latest = e
    if latest is None:
        raise HTTPException(404, "unregistered forecast id")
    return _envelope("20k", {"forecast": {
        "question": latest["question"], "class": latest["class"],
        "p_model": latest["p_model"], "abstain": latest["abstain"],
        "abstain_reason": latest.get("abstain_reason"),
        "market_first_seen_display_only": latest.get("first_seen_price",
                                                     latest.get("p_market")),
        "resolution_date": latest.get("resolution_date"),
        "resolution": latest.get("resolution"),
        "status": ("resolved" if latest.get("resolution") is not None
                   else "abstained" if latest["abstain"] else "open"),
        "tag": latest.get("tag"), "line_sha256": latest["line_sha256"]}})


@router.get("/world/state")
def world_state(fidelity: str = "20k",
                authorization: Optional[str] = Header(None)):
    import numpy as np
    key = _auth(authorization)
    _qlog("world_state", {"fidelity": fidelity}, key)
    from earth1.genesis import GENESIS_COUNTRY_CODES
    from earth1.types import FORCE_KEYS
    w = _world(fidelity)
    cents = _centroids()
    alive = w.health.alive
    out = []
    for ci, iso in enumerate(GENESIS_COUNTRY_CODES):
        m = alive & (w.civ.country == ci)
        if m.sum() < 30:
            continue
        f = w.civ.forces[m]
        mean = f.mean(0)
        denom = float(np.linalg.norm(f, axis=1).mean())
        out.append({"country": iso, "centroid": cents.get(iso),
                    "adm1": None,
                    "forces": {fk.name.lower(): round(float(mean[i]), 4)
                               for i, fk in enumerate(FORCE_KEYS)},
                    "conviction_index": (round(float(
                        np.linalg.norm(mean)) / denom, 4)
                        if denom > 1e-9 else None),
                    "agents": int(m.sum())})
    return _envelope(fidelity, {"countries": out,
                                "note_adm1": "engine has no adm1 geography "
                                "yet — registered limitation"})


@router.get("/world/history")
def world_history(fidelity: str = "20k",
                  authorization: Optional[str] = Header(None)):
    key = _auth(authorization)
    _qlog("world_history", {"fidelity": fidelity}, key)
    w = _world(fidelity)
    res = getattr(w.chronicle, "cascade_residues", None) or []
    return _envelope(fidelity, {
        "cascade_episodes_active": [
            {"rule": r["rule"], "day": float(r["day"]), "loc": int(r["loc"])}
            for r in res],
        "note": "date-range history requires the recorder store "
                "(hash-chained manifest, ops/alive backups) — v1 serves "
                "the live chronicle window only; PENDING_RECORDER_STORE"})


@router.get("/health")
def health():
    tiers = {}
    try:
        d = json.load(open(os.path.join(_ROOT, "data",
                                        "question_classes.json")))
        for cls, tpl in d["classes"].items():
            tiers[cls] = ("CALIBRATED" if tpl.get("temperature_fitted")
                          else "UNCALIBRATED")
    except Exception:
        pass
    lhead = "GENESIS"
    if os.path.exists(QLOG):
        for line in open(QLOG):
            lhead = json.loads(line)["_hash"]
    return _envelope("20k", {"calibration_table": tiers,
                             "question_log_head": lhead[:16],
                             "fidelities": {k: os.path.exists(v)
                                            for k, v in _FIDELITY.items()}})
