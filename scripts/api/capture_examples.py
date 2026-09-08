#!/usr/bin/env python3
"""Capture golden request/response examples for the Earth-1 API.

Runs the real FastAPI app (earth1.api.main:app) IN-PROCESS with
fastapi.testclient.TestClient against a SYNTHETIC 2,000-agent c2plus
world built in a throwaway temp directory. No network servers are
started; no sealed paths are read; no repo file is written except the
output (docs/api_examples.json by default) — request-time overlay
writes (question log, uncalibrated-question ledger, model store, event
wire, prospective register) are all redirected to the temp root.

Physics: the freeze-0.9 flag set (scripts/env/freeze09.env) is exported
BEFORE the first earth1 import, so the v1 surface serves the honest
"freeze-0.9" tag (earth1/configstamp.py binds several flags at import).

Auth setup mirrors production-shaped v1 auth:
  * EARTH1_API_KEYS="demo-key-A,demo-key-B" — happy-path v1 calls send
    "Authorization: Bearer demo-key-A" (earth1/api/v1.py:_auth);
  * EARTH1_DEV_OPEN=1 stays exported (it only matters when the
    allowlist is empty — the 503-dev-closed example clears both);
  * the app-wide X-API-Key middleware (earth1/api/auth.py) is OFF by
    default (EARTH1_AUTH_REQUIRED unset) and is toggled on briefly for
    its two failure examples.

Output shape: {group: [{name, method, path, request, status, response,
note?}]}. Response arrays are truncated to <= 3 items with an explicit
"...truncated (N items total)" marker; object keys are never dropped.

usage: python3 scripts/api/capture_examples.py [--out PATH] [--keep-tmp]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

POP = 2_000          # smallest non-degenerate population (tests/conftest.py)
SEED = 42
WARM_DAYS = 12
MAX_ITEMS = 3        # array-truncation width in stored responses

AUTH_A = {"Authorization": "Bearer demo-key-A"}
AUTH_B = {"Authorization": "Bearer demo-key-B"}
DEMO_QID = "api:demo-protest-q1"


# ─────────────────────────────────────────────── env, BEFORE any earth1 import

def _freeze09_env() -> dict:
    """Parse scripts/env/freeze09.env the way configstamp does — the
    file is the single source of truth for the frozen flag set."""
    out = {}
    for line in open(os.path.join(ROOT, "scripts", "env", "freeze09.env")):
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            k, v = line[len("export "):].split("=", 1)
            out[k.strip()] = v.strip()
    if not out:
        raise SystemExit("freeze09.env parsed to nothing — refusing to "
                         "capture with unfrozen physics")
    return out


def setup_env(tmp: str) -> None:
    os.environ.update(_freeze09_env())
    os.environ.update({
        "EARTH1_ALIVE_HOME": os.path.join(tmp, "alive"),
        "EARTH1_QUESTION_LOG": os.path.join(tmp, "qlog.jsonl"),
        # both fidelities point at the same tiny synthetic snapshot —
        # the capture documents payload SHAPES, not 200k-scale numbers
        "EARTH1_FIDELITY_20K": os.path.join(tmp, "snapshots", "tiny_c2plus.pkl"),
        "EARTH1_FIDELITY_200K": os.path.join(tmp, "snapshots", "tiny_c2plus.pkl"),
        "EARTH1_MODELS_DIR": os.path.join(tmp, "models"),
        "EARTH1_EVENT_WIRE": "on",
        "EARTH1_EVENT_WIRE_PATH": os.path.join(tmp, "event_wire.jsonl"),
        "EARTH1_DEV_OPEN": "1",
        "EARTH1_API_KEYS": "demo-key-A,demo-key-B",
        "EARTH1_API_RPM": "100000",       # capture must not trip the limiter
        "EARTH1_RATE_LIMIT": "100000",    # (defaults: 30 RPM / 60 per min-IP)
    })
    # anything that could reach a DB, the network, or real data must be off
    for k in ("DATABASE_URL", "EARTH1_AUTH_REQUIRED", "EARTH1_PAUSED",
              "EARTH1_GROUND_LADDER", "EARTH1_AGE_SCALE_YEARS",
              "EARTH1_EPOCH"):
        os.environ.pop(k, None)


# ───────────────────────────────────────────────────── synthetic world + files

def build_world(tmp: str) -> None:
    import uuid
    import numpy as np
    from earth1 import eventwire, persistence
    from earth1.alive import birth_world, live_one_day
    from earth1.history import Recorder, open_history
    from earth1.memory import Memory

    home = os.path.join(tmp, "alive")
    os.makedirs(home, exist_ok=True)
    os.makedirs(os.path.join(tmp, "snapshots"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "models"), exist_ok=True)

    w = birth_world(POP, SEED, substrate="c2plus_v1")
    rng = np.random.default_rng(SEED)
    rec = Recorder(open_history(home))
    rec.record(w)
    sig = np.zeros(8)
    sig[0] = 1.0
    scope = np.zeros(w.civ.n, bool)
    scope[:300] = True
    w.chronicle.remember(Memory(id="m-demo", label="synthetic demo shock",
                                day=0.0, force_signature=sig, scope=scope))
    for d in range(WARM_DAYS):
        if d == 3:                       # a few deaths so mortality surfaces
            w.health.alive[:20] = False  # have rows (synthetic, like the
            w.health.cause_of_death[:20] = 2  # committed API tests)
        st = live_one_day(w, rng)
        rec.record(w, st)
        # flush emitted moments to the temp wire with the daemon's meta
        # shape (scripts/world_alive.py:332) so /v1/world/events has rows
        eventwire.drain({"day": float(w.day), "epoch": "synthetic-capture",
                         "source": "capture_examples"})
    rec.con.close()

    meta = persistence.save_world(w, os.path.join(home, "world.pkl"), rng=rng)
    ep = {"epoch": 9, "world_uuid": str(uuid.uuid4()), "seed": SEED,
          "physics_version": "synthetic-capture"}
    with open(os.path.join(home, "EPOCH.json"), "w") as f:
        json.dump(ep, f)
    with open(os.path.join(home, "state.json"), "w") as f:
        json.dump({"day": w.day, "sha256": meta["sha256"], "epoch": 9,
                   "world_uuid": ep["world_uuid"]}, f)
    # the v1 fidelity snapshot is the same tiny world
    persistence.save_world(w, os.environ["EARTH1_FIDELITY_20K"], rng=rng)


def build_fake_root(tmp: str) -> str:
    """A temp stand-in for the repo root, for everything v1 reads by
    path: prospective register (synthetic), data-role registry
    (synthetic), country centroids (copied — public geo data)."""
    fr = os.path.join(tmp, "fake_root")
    os.makedirs(os.path.join(fr, "ops", "alive"), exist_ok=True)
    os.makedirs(os.path.join(fr, "data", "geo"), exist_ok=True)

    def _line(body, prev):
        body = dict(body, prev_line_sha256=prev)
        body["line_sha256"] = hashlib.sha256(
            json.dumps(body, sort_keys=True).encode()).hexdigest()
        return body

    e1 = _line({"question_id": DEMO_QID,
                "question": "Will protests intensify nationwide this month?",
                "class": "protest", "p_model": 0.62, "abstain": False,
                "abstain_reason": None, "first_seen_price": 0.55,
                "p_market": 0.55, "market_ts": "2026-09-01T00:00:00Z",
                "tag": "synthetic-example"}, "GENESIS")
    e2 = _line({"question_id": "api:demo-resolved-q2",
                "question": "Did the synthetic referendum pass?",
                "class": "referendum", "p_model": 0.31, "abstain": False,
                "abstain_reason": None, "first_seen_price": 0.28,
                "p_market": 0.28, "market_ts": "2026-08-15T00:00:00Z",
                "resolution_date": "2026-09-01", "resolution": 0,
                "tag": "synthetic-example"}, e1["line_sha256"])
    with open(os.path.join(fr, "ops", "alive",
                           "PROSPECTIVE_REGISTER.jsonl"), "w") as f:
        for e in (e1, e2):
            f.write(json.dumps(e, sort_keys=True) + "\n")

    with open(os.path.join(fr, "data", "data_roles.json"), "w") as f:
        json.dump({"entries": {"synthetic_holdout_example": {
            "role": "HOLDOUT",
            "path": "data/holdout/synthetic_example.jsonl",
            "notes": "synthetic registry for the API example capture; the "
                     "real registry lives at data/data_roles.json"}}}, f)

    shutil.copyfile(
        os.path.join(ROOT, "data", "geo", "country_centroids.json"),
        os.path.join(fr, "data", "geo", "country_centroids.json"))
    return fr


def patch_modules(tmp: str, fake_root: str) -> None:
    from pathlib import Path
    from earth1.adapters import multiverse as mv
    from earth1.api import deps, v1

    deps._world = deps._identity = None
    deps._history = None
    deps.ALIVE_HOME = Path(os.path.join(tmp, "alive"))

    mv.classes()          # cache the registered classes from the real repo…
    mv._ROOT = fake_root  # …then send overlay/uncalibrated writes to temp

    v1._ROOT = fake_root  # register + centroids + data-roles reads from temp
    v1._worlds.clear()
    v1._jobs.clear()
    v1._cache.clear()
    v1._rate.clear()
    v1._stamp_state = None


# ──────────────────────────────────────────────────────────── capture plumbing

def _trunc(x):
    if isinstance(x, dict):
        return {k: _trunc(v) for k, v in x.items()}
    if isinstance(x, list):
        if len(x) > MAX_ITEMS:
            return ([_trunc(v) for v in x[:MAX_ITEMS]]
                    + [f"...truncated ({len(x)} items total)"])
        return [_trunc(v) for v in x]
    return x


class Capture:
    def __init__(self, client):
        self.client = client
        self.examples = {}
        self.warnings = []

    def call(self, group, name, method, path, body=None, params=None,
             headers=None, expect=None, note=None):
        r = self.client.request(method, path, json=body, params=params,
                                headers=headers)
        try:
            resp = r.json()
        except ValueError:
            resp = {"_non_json_body": r.text[:500]}
        req = {}
        if headers:
            req["headers"] = dict(headers)
        if params:
            req["query"] = dict(params)
        if body is not None:
            req["body"] = body
        entry = {"name": name, "method": method.upper(), "path": path,
                 "request": req or None, "status": r.status_code,
                 "response": _trunc(resp)}
        if note:
            entry["note"] = note
        self.examples.setdefault(group, []).append(entry)
        tag = "ok" if (expect is None or r.status_code == expect) else "WARN"
        if tag == "WARN":
            self.warnings.append(f"{name}: expected {expect}, "
                                 f"got {r.status_code}")
        print(f"  [{tag}] {method.upper():6s} {path} -> {r.status_code}"
              f"  ({group}/{name})")
        return r


# ───────────────────────────────────────────────────────────────── the capture

def run_capture(cap: Capture) -> None:
    c = cap.call

    # ── meta: the mounted spec vs docs/openapi.json ──────────────────
    r = cap.client.get("/openapi.json")
    mounted = r.json().get("paths", {})
    try:
        docs_spec = json.load(open(os.path.join(ROOT, "docs",
                                                "openapi.json")))
        docs_paths = docs_spec.get("paths", {})
        parse_err = None
    except Exception as e:  # noqa: BLE001 — recorded, not raised
        docs_paths, parse_err = {}, repr(e)
    entry = {"name": "openapi_validation", "method": "GET",
             "path": "/openapi.json", "request": None,
             "status": r.status_code,
             "response": {
                 "mounted_app_title": r.json().get("info", {}).get("title"),
                 "mounted_app_paths": len(mounted),
                 "docs_openapi_json_parses": parse_err is None,
                 "docs_openapi_json_parse_error": parse_err,
                 "docs_openapi_json_paths": len(docs_paths),
                 "path_count_matches": len(mounted) == len(docs_paths),
                 "only_in_mounted_app": sorted(set(mounted) - set(docs_paths)),
                 "only_in_docs_file": sorted(set(docs_paths) - set(mounted))},
             "note": "validation summary, not the raw spec — fetch "
                     "/openapi.json from the app for the full document"}
    cap.examples.setdefault("meta", []).append(entry)
    if len(mounted) != len(docs_paths):
        cap.warnings.append(
            f"docs/openapi.json has {len(docs_paths)} paths, mounted app "
            f"has {len(mounted)}")
    print(f"  [{'ok' if len(mounted) == len(docs_paths) else 'WARN'}] "
          f"openapi paths: app={len(mounted)} docs={len(docs_paths)}")

    # ── system ───────────────────────────────────────────────────────
    c("system", "health", "GET", "/health", expect=200,
      note="exempt from every middleware layer (auth, budget, rate "
           "limit, pause switch)")
    c("system", "physics", "GET", "/physics", expect=200)
    c("system", "epoch_current", "GET", "/epochs/current", expect=200)
    c("system", "snapshot_current", "GET", "/snapshots/current", expect=200)

    # ── world ────────────────────────────────────────────────────────
    c("world", "world_summary", "GET", "/world", expect=200)

    # ── geography ────────────────────────────────────────────────────
    r = c("geography", "countries_list", "GET", "/countries", expect=200)
    iso = max(r.json()["countries"], key=lambda x: x["population_alive"])["iso2"]
    r = c("geography", "country_detail", "GET", f"/countries/{iso}",
          expect=200)
    loc = r.json()["localities"][0]
    c("geography", "locality_detail", "GET", f"/localities/{loc}", expect=200)

    # ── earthlings ───────────────────────────────────────────────────
    r = c("earthlings", "earthlings_list", "GET", "/earthlings",
          params={"limit": 3, "offset": 100}, expect=200)
    pid = r.json()["earthlings"][0]["person_id"]
    c("earthlings", "earthling_detail", "GET", f"/earthlings/{pid}",
      expect=200)
    c("earthlings", "earthling_forces", "GET", f"/earthlings/{pid}/forces",
      expect=200)
    c("earthlings", "earthling_needs", "GET", f"/earthlings/{pid}/needs",
      expect=200)
    c("earthlings", "earthling_history", "GET", f"/earthlings/{pid}/history",
      expect=200)

    # ── memories / cascades ──────────────────────────────────────────
    c("memories_cascades", "memories_list", "GET", "/memories", expect=200)
    c("memories_cascades", "cascades_list", "GET", "/cascades", expect=200,
      note="active_residues is empty here: at the 2,000-agent capture "
           "size locality populations sit below the pop>=10 cascade "
           "gate (tests/conftest.py caveat), so cascades never fire")

    # ── branches lifecycle ───────────────────────────────────────────
    body = {"scenario": {"id": "demo-fear", "label": "synthetic fear dose",
                         "forces": {"fear": 0.2}, "persists_days": 5},
            "seed": 5}
    r = c("branches", "branch_create", "POST", "/branches", body=body,
          expect=200)
    bid = r.json()["id"]
    c("branches", "branch_advance", "POST", f"/branches/{bid}/advance",
      params={"days": 2}, expect=200)
    c("branches", "branch_compare", "GET", f"/branches/{bid}/compare",
      expect=200)
    c("branches", "branch_delete", "DELETE", f"/branches/{bid}", expect=200)

    # ── predictions (DB-backed; no DATABASE_URL here) ────────────────
    c("predictions", "predictions_status", "GET", "/predictions/status",
      expect=200)
    c("predictions", "predictions_list_no_db", "GET", "/predictions/list",
      expect=503,
      note="503 BY DESIGN without DATABASE_URL — every /predictions "
           "route except /status requires the database "
           "(earth1/api/routes/predictions.py:66)")

    # ── app-wide X-API-Key middleware (earth1/api/auth.py) ───────────
    os.environ["EARTH1_AUTH_REQUIRED"] = "1"
    try:
        c("app_auth_middleware", "missing_x_api_key", "GET", "/world",
          expect=401,
          note="EARTH1_AUTH_REQUIRED=1 turns the app-wide X-API-Key "
               "middleware on for every path except /health")
        c("app_auth_middleware", "x_api_key_without_db", "GET", "/world",
          headers={"X-API-Key": "demo"}, expect=503,
          note="the X-API-Key layer verifies keys against the database; "
               "with EARTH1_AUTH_REQUIRED=1 and no DATABASE_URL it "
               "fails closed")
    finally:
        os.environ.pop("EARTH1_AUTH_REQUIRED", None)

    # ── v1: the typed ship surface ───────────────────────────────────
    c("v1", "capabilities", "GET", "/v1/capabilities", expect=200,
      note="discovery handshake — no auth required on this route")
    c("v1", "health", "GET", "/v1/health", expect=200,
      note="no auth required on this route")
    c("v1", "world_state", "GET", "/v1/world/state",
      params={"fidelity": "20k"}, headers=AUTH_A, expect=200)
    c("v1", "world_hash", "GET", "/v1/world/hash",
      params={"fidelity": "20k"}, headers=AUTH_A, expect=200)
    c("v1", "world_history", "GET", "/v1/world/history",
      params={"fidelity": "20k"}, headers=AUTH_A, expect=200)
    c("v1", "world_events", "GET", "/v1/world/events",
      params={"n": 5}, headers=AUTH_A, expect=200)

    c("v1", "ask_opinion_door", "POST", "/v1/ask",
      body={"fidelity": "20k", "question_id": "api:demo-opinion-q1",
            "text": "Do people trust their national institutions?"},
      headers=AUTH_A, expect=200,
      note="attitude phrasing routes to the OPINION door: a direct "
           "force readout, no branch simulation; stance_share is null "
           "without the ground ladder (EARTH1_GROUND_LADDER unset)")
    c("v1", "ask_forecast_door_scored", "POST", "/v1/ask",
      body={"fidelity": "20k", "question_id": DEMO_QID,
            "text": "Will protests intensify nationwide this month?",
            "class": "protest", "outcomes": ["YES", "NO"],
            "horizon_days": 10},
      headers=AUTH_A, expect=200,
      note="'will …' routes to the FORECAST door: real branch runs vs "
           "null. horizon_days is clamped to 1..365 (default 45 on the "
           "20k sync path). p_model is a normalized branch-displacement "
           "ratio (semantics: branch_consistency), not a calibrated "
           "event probability. Captured against the tiny synthetic "
           "world, so the numbers are shape-only")
    c("v1", "ask_forecast_door_abstain", "POST", "/v1/ask",
      body={"fidelity": "20k", "question_id": "api:demo-protest-q1b",
            "text": "Will protests intensify nationwide this month?",
            "class": "protest", "outcomes": ["YES", "NO"], "country": "US",
            "horizon_days": 2},
      headers=AUTH_A, expect=200,
      note="ABSTAIN is a first-class outcome: when every branch delta "
           "sits below the class noise floor, p_model is null and "
           "abstain_reason says so — the surface never serves a number "
           "from an abstained line. country scopes both the dose and "
           "the readout to that ISO2")
    c("v1", "forecast_lookup", "GET", f"/v1/forecast/{DEMO_QID}",
      headers=AUTH_A, expect=200,
      note="served from a SYNTHETIC prospective register built for this "
           "capture; /v1/ask does NOT register a forecast — only "
           "registered ids resolve here, others 404")
    c("v1", "job_status_unknown", "GET", "/v1/jobs/deadbeef0000",
      headers=AUTH_A, expect=404,
      note="jobs exist only for fidelity=200k asks; they are "
           "process-local, TTL-evicted (EARTH1_JOB_TTL, default 3600s "
           "after finishing) and do not survive a restart")
    c("v1", "consequences", "POST", "/v1/consequences",
      body={"fidelity": "20k",
            "scenario": {"id": "demo-shock", "label": "synthetic fear shock",
                         "forces": {"fear": 0.15}, "persists_days": 5},
            "seeds": 8, "horizon_days": 1},
      headers=AUTH_A, expect=200,
      note="seeds clamp to 8..16 (default 8), horizon_days to 1..365 "
           "(default 60); horizon=1 keeps the capture cheap — real "
           "reports run longer horizons. top_country_movers is empty "
           "here because per-country rows need >=200 agents")

    c("v1", "model_create", "POST", "/v1/models",
      body={"model_id": "demo-model-1",
            "description": "synthetic example model",
            "context": {"loyalty": {"base": 0.6,
                                    "modulators": {"income": 0.2},
                                    "synthetic": True}},
            "population": {}},
      headers=AUTH_A, expect=200,
      note="owner is the sha256-derived principal of the bearer key, "
           "never the raw token; an empty population predicate selects "
           "every living agent")
    c("v1", "model_scenario", "POST", "/v1/models/demo-model-1/scenario",
      body={"fidelity": "20k", "id": "demo-price-cut",
            "label": "synthetic price cut", "forces": {"desire": 0.2},
            "seeds": 2, "horizon_days": 2},
      headers=AUTH_A, expect=200,
      note="seeds clamp to 1..16 (default 3), horizon_days to 1..365 "
           "(default 30). SEND seeds>=2: seeds=1 currently 500s — the "
           "per-outcome sem is np.std(ddof=1) over the seed deltas "
           "(earth1/models.py:224,242), NaN for a single seed, and NaN "
           "fails FastAPI's JSON serialization")
    c("v1", "population_frame", "POST",
      "/v1/models/demo-model-1/population-frame",
      body={"cohorts": [{"id": "c1", "name": "budget-conscious students"},
                        {"id": "c2",
                         "name": "affluent urban professionals"}],
            "tierSize": 200000},
      headers=AUTH_A, expect=200,
      note="deterministic registered lexicon over the census-weighted "
           "C2+ joint; no LLM in the runtime path")

    # ── v1 auth failures ─────────────────────────────────────────────
    c("v1_auth", "bearer_missing_401", "GET", "/v1/world/events",
      expect=401,
      note="keys configured (EARTH1_API_KEYS) + no Authorization header")
    c("v1_auth", "bearer_unknown_403", "GET", "/v1/world/events",
      headers={"Authorization": "Bearer wrong-key"}, expect=403)
    saved_keys = os.environ.pop("EARTH1_API_KEYS", None)
    saved_open = os.environ.pop("EARTH1_DEV_OPEN", None)
    os.environ["EARTH1_API_KEYS"] = ""
    try:
        c("v1_auth", "empty_allowlist_503_fail_closed", "GET",
          "/v1/world/events", expect=503,
          note="an EMPTY allowlist fails CLOSED (503) unless "
               "EARTH1_DEV_OPEN=1 explicitly enables anonymous dev "
               "access (earth1/api/v1.py:_auth, review S03a)")
    finally:
        if saved_keys is not None:
            os.environ["EARTH1_API_KEYS"] = saved_keys
        if saved_open is not None:
            os.environ["EARTH1_DEV_OPEN"] = saved_open
    c("v1_auth", "model_id_traversal_422", "POST", "/v1/models",
      body={"model_id": "../escape", "description": "bad id"},
      headers=AUTH_A, expect=422,
      note="model ids must match [A-Za-z0-9][A-Za-z0-9_-]{0,63} "
           "(earth1/api/v1.py:_check_model_id, review S01b)")
    c("v1_auth", "cross_tenant_403", "POST",
      "/v1/models/demo-model-1/scenario",
      body={"fidelity": "20k", "forces": {"desire": 0.1}},
      headers=AUTH_B, expect=403,
      note="demo-model-1 was created by demo-key-A; a different valid "
           "key gets 403 (earth1/api/v1.py:_check_owner, review S01a)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "docs",
                                                  "api_examples.json"))
    ap.add_argument("--keep-tmp", action="store_true",
                    help="keep the synthetic world/temp root for debugging")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="earth1_api_capture_")
    setup_env(tmp)

    t0 = time.time()
    print(f"[capture] temp root: {tmp}")
    print(f"[capture] building the synthetic {POP}-agent c2plus world "
          f"({WARM_DAYS} days)…")
    build_world(tmp)
    fake_root = build_fake_root(tmp)
    patch_modules(tmp, fake_root)
    print(f"[capture] world ready in {time.time()-t0:.1f}s")

    from fastapi.testclient import TestClient
    from earth1.api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        cap = Capture(client)
        run_capture(cap)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(cap.examples, f, indent=1, sort_keys=False)
        f.write("\n")
    n = sum(len(v) for v in cap.examples.values())
    print(f"\n[capture] wrote {n} examples in {len(cap.examples)} groups "
          f"to {args.out} ({time.time()-t0:.1f}s total)")
    for w in cap.warnings:
        print(f"[capture] WARNING: {w}")

    if args.keep_tmp:
        print(f"[capture] temp root kept: {tmp}")
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if cap.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
