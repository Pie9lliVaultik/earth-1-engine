"""CUSTOM EARTH-1 MODELS — persistent, user-owned population layers
(founder architecture, 2026-09-02).

Three layers, kept physically separate:
  EARTH-1 CORE     the civilization — engine-owned, never mutated here
  MODEL CONTEXT    per-agent dynamic attributes in an OVERLAY store
                   (person_id-aligned arrays beside the world, never in
                   it); every attribute carries provenance and a
                   synthetic flag
  SCENARIO STATE   temporary; dosed through the Memory channel onto the
                   model population mask; never persisted into the model
                   unless the owner promotes it

Sacred lines (inherited from the campaign, asserted here):
  * context sources pass the same provenance discipline as national
    inputs — a judged estate can never feed a model attribute;
  * synthetic grounding is flagged per attribute in every payload;
  * model outcomes are tier-stamped UNCALIBRATED until the model's own
    resolved outcomes exist;
  * the overlay never enters world state: Block-0 determinism holds.
"""
import hashlib
import json
import os
import time

import numpy as np

MODELS_DIR = os.environ.get("EARTH1_MODELS_DIR", "/opt/earth1-data/models")


def _mdir(model_id):
    d = os.path.join(MODELS_DIR, model_id)
    os.makedirs(d, exist_ok=True)
    return d


def _chain_append(model_id, record):
    p = os.path.join(_mdir(model_id), "history.jsonl")
    prev = "GENESIS"
    if os.path.exists(p):
        for line in open(p):
            prev = json.loads(line)["_hash"]
    rec = {**record, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                         time.gmtime()), "_prev": prev}
    rec["_hash"] = hashlib.sha256(
        json.dumps(rec, sort_keys=True).encode()).hexdigest()
    with open(p, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec["_hash"]


def create_model(model_id: str, owner: str, description: str = "") -> dict:
    meta = {"model_id": model_id, "owner": owner,
            "description": description, "version": 1,
            "context_attrs": {}, "population_def": None,
            "calibration_tier": "UNCALIBRATED",
            "resolved_outcomes": 0}
    json.dump(meta, open(os.path.join(_mdir(model_id), "model.json"), "w"),
              indent=1)
    _chain_append(model_id, {"kind": "created", "owner": owner})
    return meta


def load_model(model_id: str) -> dict:
    return json.load(open(os.path.join(_mdir(model_id), "model.json")))


def _save(meta):
    meta["version"] += 1
    json.dump(meta, open(os.path.join(
        _mdir(meta["model_id"]), "model.json"), "w"), indent=1)


def select_population(world, predicate: dict, overlay: dict = None):
    """Predicate over core + context attributes -> boolean mask.
    predicate: {countries: [ISO2], age: [lo,hi], min_income_pctile: p,
                context: {attr: [lo,hi]}}"""
    from earth1.genesis import GENESIS_COUNTRY_CODES
    civ = world.civ
    m = world.health.alive.copy()
    if predicate.get("countries"):
        idx = [GENESIS_COUNTRY_CODES.index(c)
               for c in predicate["countries"]
               if c in GENESIS_COUNTRY_CODES]
        m &= np.isin(civ.country, idx)
    if predicate.get("age"):
        # predicate speaks YEARS; civ.age is normalized (1.0 ~ a full
        # lifespan, ~87.6yr). Conversion is explicit, never guessed by
        # callers.
        lo, hi = predicate["age"]
        scale = float(os.environ.get("EARTH1_AGE_SCALE_YEARS", "87.6"))
        m &= (civ.age >= lo / scale) & (civ.age <= hi / scale)
    if predicate.get("min_income_pctile") is not None and m.any():
        thr = np.percentile(world.life.wage[m],
                            predicate["min_income_pctile"])
        m &= world.life.wage >= thr
    for attr, (lo, hi) in (predicate.get("context") or {}).items():
        if overlay and attr in overlay:
            m &= (overlay[attr] >= lo) & (overlay[attr] <= hi)
    return m


def attach_context(model_id: str, world, attrs: dict) -> dict:
    """attrs: {name: {"base": float, "modulators": {core_attr: weight},
                      "source": str, "synthetic": bool}}.
    v1 grounding: attribute = clip(base + sum(w * standardized core
    attr) + seeded noise, 0, 1). Deterministic per (model, attr) —
    reruns reproduce the same overlay. Everything is flagged."""
    meta = load_model(model_id)
    d = _mdir(model_id)
    path = os.path.join(d, "context.npz")
    overlay = dict(np.load(path)) if os.path.exists(path) else {}
    civ, life = world.civ, world.life
    core = {"age": civ.age, "income": life.wage,
            "openness": civ.openness, "desire": civ.desire_intensity,
            "urban": civ.urban.astype(float),
            "education": civ.education.astype(float)}
    for name, spec in attrs.items():
        rng = np.random.default_rng(int(hashlib.sha256(
            f"{model_id}:{name}".encode()).hexdigest()[:8], 16))
        v = np.full(civ.n, float(spec.get("base", 0.5)))
        for cname, w in (spec.get("modulators") or {}).items():
            x = core.get(cname)
            if x is None:
                continue
            sd = x.std()
            if sd > 1e-9:
                v = v + w * (x - x.mean()) / sd
        v = np.clip(v + rng.normal(0, 0.05, civ.n), 0.0, 1.0)
        overlay[name] = v
        meta["context_attrs"][name] = {
            "source": spec.get("source", "synthetic_grounding_v1"),
            "synthetic": bool(spec.get("synthetic", True)),
            "provenance": spec.get("provenance", "model-owner supplied "
                                   "spec; DERIVED from core attributes; "
                                   "no external data"),
            "base": spec.get("base", 0.5)}
    np.savez_compressed(path, **overlay)
    _save(meta)
    _chain_append(model_id, {"kind": "context_attached",
                             "attrs": sorted(attrs),
                             "overlay_sha": hashlib.sha256(
                                 open(path, "rb").read()).hexdigest()[:16]})
    return meta


def load_overlay(model_id: str) -> dict:
    path = os.path.join(_mdir(model_id), "context.npz")
    return dict(np.load(path)) if os.path.exists(path) else {}


def run_scenario(model_id: str, world, scenario: dict, seeds=(1, 2, 3),
                 horizon_days: int = 30) -> dict:
    """Scenario dosed onto the MODEL population via the Memory channel;
    outcomes = scoped population deltas vs CRN-paired null, with the
    who/where/why anatomy. The world argument is deepcopied per branch;
    the caller's world is never touched."""
    import copy
    from earth1.alive import live_one_day
    from earth1.branch import apply, null_branch
    from earth1.memory import Memory
    from earth1.types import FORCE_KEYS, Force
    from earth1.genesis import GENESIS_COUNTRY_CODES
    meta = load_model(model_id)
    overlay = load_overlay(model_id)
    mask = select_population(world, scenario.get("population",
                                                 meta.get("population_def")
                                                 or {}), overlay)
    n_sel = int(mask.sum())
    if n_sel < 50:
        return {"model_id": model_id, "abstain": True,
                "abstain_reason": f"selected population too small "
                f"({n_sel} agents) for a stable readout",
                "population": n_sel}
    sig = np.zeros(len(Force))
    for fname, val in (scenario.get("forces") or {}).items():
        f = getattr(Force, fname.upper(), None)
        if f is not None:
            sig[f] = val
    deltas_by_seed = []
    seg_deltas = {}
    for s in seeds:
        ends = {}
        for arm in ("scn", "null"):
            w = copy.deepcopy(world)
            rng = np.random.default_rng(977 * 71 + s)
            apply(w, null_branch(), rng)
            if arm == "scn" and np.any(sig):
                w.chronicle.remember(Memory(
                    id=f"model:{model_id}:{scenario.get('id', 'scn')}",
                    label=scenario.get("label", "model scenario"),
                    day=float(w.day), force_signature=sig,
                    scope=mask.copy(), origin="model_scenario",
                    half_life=float(scenario.get("persists_days", 30))))
            for _ in range(horizon_days):
                live_one_day(w, rng)
            a = w.health.alive & mask
            ends[arm] = {
                "forces": w.civ.forces[a].mean(0),
                "employed": float(w.life.employed[a].mean()),
                "deprivation": float(w.life.deprivation[a].mean()),
                "wealth": float(np.median(w.life.wealth[a]))}
        deltas_by_seed.append({
            "forces": ends["scn"]["forces"] - ends["null"]["forces"],
            "employed": ends["scn"]["employed"] - ends["null"]["employed"],
            "deprivation": (ends["scn"]["deprivation"]
                            - ends["null"]["deprivation"]),
            "wealth": ends["scn"]["wealth"] - ends["null"]["wealth"]})
    fmat = np.stack([d["forces"] for d in deltas_by_seed])
    force_anatomy = {fk.name.lower(): {
        "delta": round(float(fmat[:, i].mean()), 5),
        "sem": round(float(fmat[:, i].std(ddof=1)
                           / max(len(seeds) - 1, 1) ** 0.5), 5)}
        for i, fk in enumerate(FORCE_KEYS)}
    who = {}
    civ = world.civ
    for ci in np.unique(civ.country[mask]):
        cm = mask & (civ.country == ci)
        if cm.sum() >= 30:
            who[GENESIS_COUNTRY_CODES[ci]] = int(cm.sum())
    out = {"model_id": model_id, "model_version": meta["version"],
           "calibration_tier": meta["calibration_tier"],
           "population": n_sel,
           "population_by_country": who,
           "force_anatomy": force_anatomy,
           "outcomes": {k: {
               "delta": round(float(np.mean([d[k] for d in
                                             deltas_by_seed])), 5),
               "sem": round(float(np.std([d[k] for d in deltas_by_seed],
                                         ddof=1)
                                  / max(len(seeds) - 1, 1) ** 0.5), 5)}
               for k in ("employed", "deprivation", "wealth")},
           "data_foundation": {a: meta["context_attrs"][a]
                               for a in meta["context_attrs"]},
           "epistemics": "outcomes are scoped-population deltas vs a "
                         "CRN-paired null; tier is the model's own "
                         "calibration state, earned from resolved "
                         "outcomes only"}
    _chain_append(model_id, {"kind": "scenario_run",
                             "scenario": scenario.get("id"),
                             "population": n_sel,
                             "outcome_sha": hashlib.sha256(json.dumps(
                                 out, sort_keys=True, default=str
                             ).encode()).hexdigest()[:16]})
    return out
