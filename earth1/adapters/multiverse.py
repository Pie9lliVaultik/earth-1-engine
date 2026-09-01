"""THE MULTIVERSE ADAPTER — the single typed question path (BIBLE
v4.2.2 refinement 9; founder orders 2026-09-01).

Every binary and multi-outcome question routes through here. Universal
rules, asserted in code:
  * branches are REAL Earth-1 branches paired against null_branch() —
    there is no logit-shift path in this module;
  * abstain when every scenario-vs-control force delta is below the
    class noise floor: p_model is None then (type-level Abstain);
  * p_model is the ONLY scored field. This module has no market-price
    parameter; blending is a product-layer concern stored elsewhere as
    p_blended and never read by any scorer;
  * class-specific logic is confined to the outcome injector templates
    in data/question_classes.json (one XI.A.2 report per class).

Readout (registered):
  binary:       P(YES) = d_no / (d_yes + d_no)
  k outcomes:   P(i) = softmax(-d_i / T_class)  (T FITTED per class on
                FIT-half DEV events; default 1.0 until first fits)
  d_i = euclidean distance between the null world's and world_i's
  census-weighted scoped 8-force mean at horizon end.
  Conviction Index = ||mean agent force delta|| / mean ||agent force
  delta|| over the scoped population (response coherence, in [0,1]).
"""
import copy
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CLASSES = None


def classes() -> dict:
    global _CLASSES
    if _CLASSES is None:
        _CLASSES = json.load(open(os.path.join(
            _ROOT, "data", "question_classes.json")))["classes"]
    return _CLASSES


@dataclass
class Verdict:
    question_id: str
    question_class: str
    p_model: Optional[float]          # None == Abstain (type-level)
    abstain: bool
    abstain_reason: Optional[str]
    outcomes: list
    p_by_outcome: Optional[dict]
    distances: dict
    noise_floor: float
    temperature: float
    force_signature: dict             # per-outcome 8-force delta vs null
    conviction_index: Optional[float]
    branch_hashes: dict
    ledger_cutoff_day: float
    pop: int
    horizon_days: int
    seed: int


def _scoped(w, country_iso2):
    from earth1.genesis import GENESIS_COUNTRY_CODES, census_weights
    alive = w.health.alive
    cw = census_weights(w.civ)
    if country_iso2:
        ci = GENESIS_COUNTRY_CODES.index(country_iso2)
        m = alive & (w.civ.country == ci)
    else:
        m = alive
    return m, cw


def _force_mean(w, m, cw):
    f = w.civ.forces[m]
    wt = cw[m][:, None]
    return (f * wt).sum(0) / max(float(cw[m].sum()), 1e-9)


def _build_scenario(cls_name, outcome_key, spec):
    from earth1.branch import Scenario
    tpl = classes()[cls_name]
    forces = tpl["injector"]["forces"].get(outcome_key)
    if forces is None:
        return None
    countries = ([spec["country"]] if tpl["injector"]["scope"] == "country"
                 and spec.get("country") else None)
    return Scenario(
        id=f"{cls_name}:{spec['question_id']}:{outcome_key}",
        label=f"{cls_name} outcome {outcome_key} as accomplished fact",
        forces=dict(forces), countries=countries,
        firm_damage=float(tpl["injector"].get("firm_damage", 0.0)),
        trade_shock=float(tpl["injector"].get("trade_shock", 0.0)),
        persists_days=float(tpl["injector"].get("persists_days", 60.0)))


def answer(spec: dict, base_world, seed: int, horizon_days: int = 60,
           **kwargs) -> Verdict:
    """spec: {question_id, class, outcomes: [..], country: ISO2|None}.
    base_world: a warmed World (never mutated — branches are deepcopies).
    Accepts NO market information by contract."""
    assert not kwargs, f"multiverse.answer takes no extra args: {kwargs}"
    from earth1.alive import live_one_day
    from earth1.branch import apply, null_branch
    from earth1.persistence import world_hash
    from earth1.types import FORCE_KEYS
    cls_name = spec["class"]
    tpl = classes().get(cls_name)
    if tpl is None:
        return _abstain(spec, f"unregistered class {cls_name}", seed,
                        horizon_days, base_world)
    outcomes = spec["outcomes"]
    keys = (["YES", "NO"] if len(outcomes) == 2 else
            [f"O{i}" for i in range(len(outcomes))])
    if any(tpl["injector"]["forces"].get(k) is None for k in keys):
        return _abstain(spec, f"class template lacks {len(outcomes)}-"
                        "outcome form", seed, horizon_days, base_world)

    ends, hashes, per_agent = {}, {}, {}
    for key in ["NULL"] + keys:
        w = copy.deepcopy(base_world)
        rng = np.random.default_rng(977 * 31 + seed)   # CRN across branches
        sc = (null_branch() if key == "NULL"
              else _build_scenario(cls_name, key, spec))
        apply(w, sc, rng)
        for _ in range(horizon_days):
            live_one_day(w, rng)
        m, cw = _scoped(w, spec.get("country"))
        ends[key] = _force_mean(w, m, cw)
        per_agent[key] = w.civ.forces[m].copy()
        hashes[key] = world_hash(w)[:16]

    dists = {k: float(np.linalg.norm(ends["NULL"] - ends[k])) for k in keys}
    floor = float(tpl.get("noise_floor", 0.0))
    temp = float(tpl.get("temperature", 1.0))
    sig = {k: {fk.name.lower(): round(float(ends[k][i] - ends["NULL"][i]), 5)
               for i, fk in enumerate(FORCE_KEYS)} for k in keys}
    n = min(len(per_agent["NULL"]), min(len(per_agent[k]) for k in keys))
    deltas = per_agent[keys[0]][:n] - per_agent["NULL"][:n]
    denom = float(np.linalg.norm(deltas, axis=1).mean())
    conviction = (float(np.linalg.norm(deltas.mean(0))) / denom
                  if denom > 1e-12 else None)

    common = dict(question_id=spec["question_id"], question_class=cls_name,
                  outcomes=outcomes, distances=dists, noise_floor=floor,
                  temperature=temp, force_signature=sig,
                  conviction_index=conviction, branch_hashes=hashes,
                  ledger_cutoff_day=float(base_world.day),
                  pop=int(base_world.civ.n), horizon_days=horizon_days,
                  seed=seed)
    if max(dists.values()) < floor:
        return Verdict(p_model=None, abstain=True,
                       abstain_reason=f"all branch deltas below class "
                       f"noise floor {floor:.4g} (branch = control)",
                       p_by_outcome=None, **common)
    if len(keys) == 2:
        p_yes = dists["NO"] / max(dists["YES"] + dists["NO"], 1e-12)
        pbo = {outcomes[0]: p_yes, outcomes[1]: 1.0 - p_yes}
        p_model = p_yes
    else:
        z = np.array([-dists[k] / max(temp, 1e-9) for k in keys])
        z -= z.max()
        p = np.exp(z) / np.exp(z).sum()
        pbo = {outcomes[i]: float(p[i]) for i in range(len(keys))}
        p_model = float(p.max())
    return Verdict(p_model=float(p_model), abstain=False,
                   abstain_reason=None, p_by_outcome=pbo, **common)


def _abstain(spec, reason, seed, horizon_days, base_world):
    return Verdict(question_id=spec["question_id"],
                   question_class=spec.get("class", "?"), p_model=None,
                   abstain=True, abstain_reason=reason,
                   outcomes=spec.get("outcomes", []), p_by_outcome=None,
                   distances={}, noise_floor=0.0, temperature=1.0,
                   force_signature={}, conviction_index=None,
                   branch_hashes={},
                   ledger_cutoff_day=float(getattr(base_world, "day", -1)),
                   pop=int(getattr(base_world.civ, "n", 0)
                           if base_world is not None else 0),
                   horizon_days=horizon_days, seed=seed)


def measure_noise_floor(base_world, seed: int, horizon_days: int = 60,
                        country=None, n_pairs: int = 3) -> float:
    """Twin-null calibration: distance between two null branches with
    DIFFERENT rng streams = pure chaos noise at this pop/horizon. The
    class floor is 2x the mean twin-null distance."""
    import copy as _c
    from earth1.alive import live_one_day
    from earth1.branch import apply, null_branch
    ds = []
    for p in range(n_pairs):
        es = []
        for j in (0, 1):
            w = _c.deepcopy(base_world)
            rng = np.random.default_rng(7000 + seed + p * 10 + j)
            apply(w, null_branch(), rng)
            for _ in range(horizon_days):
                live_one_day(w, rng)
            m, cw = _scoped(w, country)
            es.append(_force_mean(w, m, cw))
        ds.append(float(np.linalg.norm(es[0] - es[1])))
    return 2.0 * float(np.mean(ds))
