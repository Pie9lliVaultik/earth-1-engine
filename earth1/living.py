"""The living world — Phase 5 bifurcation and persistence (bible §21.2, §34).

Two copies of the manifold with opposite dynamics, by design:

  FROZEN calibration copy — genesis(pop, seed), reproducible bit-for-bit,
  identified by its pop-hash. Every benchmark and gate number runs here.
  It is never ticked.

  LIVING copy — born from the same genesis, then persisted to disk. It
  ticks daily, absorbs signal, evolves, and survives across sessions.
  An earthling is a frozen core plus an evolving shell; this is the shell.

Census-drift guard (§34): an agent ticked a thousand times may no longer
represent its demographic cell, which makes its census weight wrong.
Drift is measured per country against the frozen anchors; cells beyond
tolerance are re-anchored — the excess mean shift is subtracted, the
within-cell variance (the lived history) is kept.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy import sparse

from earth1.types import Civilization, Question, NUM_FORCES
from earth1.genesis import genesis
from earth1.event_log import EventLog, WorldEvent
from earth1.tick import WorldState, world_tick, _make_mutable

FORMAT_VERSION = 1

# traits guarded against census drift — the demographically-anchored ones
_DRIFT_TRAITS = (
    "openness", "empathy", "risk_appetite", "doubt", "desire_intensity",
    "conscientiousness", "agreeableness", "extraversion", "neuroticism",
)


def pop_hash(civ: Civilization) -> str:
    return hashlib.sha256(civ.forces.tobytes()).hexdigest()


def _civ_arrays(civ: Civilization) -> Dict[str, np.ndarray]:
    out = {}
    for name in civ.__dataclass_fields__:
        v = getattr(civ, name)
        if isinstance(v, np.ndarray):
            out[name] = v
    return out


class LivingWorld:
    """A persisted, ticking civilization. Load it tomorrow and it is the
    same world one day older — not a fresh population."""

    def __init__(self, state: WorldState, path: Path, meta: dict):
        self.state = state
        self.path = Path(path)
        self.meta = meta

    # ── birth ──

    @classmethod
    def create(
        cls,
        path: str | Path,
        pop: int = 200_000,
        seed: int = 42,
        min_per_country: int = 100,
        questions: Optional[List[Question]] = None,
    ) -> "LivingWorld":
        """Bifurcate: genesis the frozen copy, record its anchors, and
        persist the living copy beside them."""
        civ = genesis(pop, seed, min_per_country)
        anchor_hash = pop_hash(civ)

        # frozen per-country anchors for the drift guard
        anchors: Dict[str, Dict[str, float]] = {}
        for c in np.unique(civ.country):
            mask = civ.country == c
            anchors[str(int(c))] = {
                t: float(getattr(civ, t)[mask].mean()) for t in _DRIFT_TRAITS
            }

        state = WorldState(
            civ=_make_mutable(civ),
            event_log=EventLog(),
            t=0.0,
            tick_count=0,
            question_history=[],
            coupling_matrix={},
            last_fired={},
            rng=np.random.default_rng(seed),
        )
        meta = {
            "format_version": FORMAT_VERSION,
            "pop": pop, "seed": seed, "min_per_country": min_per_country,
            "frozen_pop_hash": anchor_hash,
            "anchors": anchors,
            "ticks": 0,
        }
        world = cls(state, Path(path), meta)
        world.save()
        return world

    # ── persistence ──

    def save(self) -> None:
        p = self.path
        p.mkdir(parents=True, exist_ok=True)

        arrays = _civ_arrays(self.state.civ)
        np.savez_compressed(p / "civ.npz", **arrays)
        sparse.save_npz(p / "adj.npz", self.state.civ.adj.tocsr())

        self.meta["ticks"] = self.state.tick_count
        self.meta["t"] = self.state.t
        self.meta["n"] = int(self.state.civ.n)
        self.meta["civ_seed"] = int(self.state.civ.seed)
        self.meta["living_pop_hash"] = pop_hash(self.state.civ)
        self.meta["last_fired"] = self.state.last_fired
        self.meta["rng_state"] = json.loads(
            json.dumps(self.state.rng.bit_generator.state))
        self.meta["events"] = [
            {"id": e.id, "timestamp": e.timestamp,
             "region_pattern": e.region_pattern,
             "demographic_filter": e.demographic_filter,
             "force_deltas": {str(k): v for k, v in e.force_deltas.items()},
             "decay_half_life": e.decay_half_life, "source": e.source}
            for e in self.state.event_log.events()
        ]
        with open(p / "world.json", "w") as f:
            json.dump(self.meta, f)

    @classmethod
    def load(cls, path: str | Path) -> "LivingWorld":
        p = Path(path)
        with open(p / "world.json") as f:
            meta = json.load(f)
        if meta.get("format_version") != FORMAT_VERSION:
            raise ValueError(f"unknown living-world format: {meta.get('format_version')}")

        arrays = dict(np.load(p / "civ.npz"))
        adj = sparse.load_npz(p / "adj.npz")
        civ = Civilization(n=meta["n"], seed=meta["civ_seed"], adj=adj, **arrays)

        log = EventLog()
        for e in meta.get("events", []):
            log.append(WorldEvent(
                id=e["id"], timestamp=e["timestamp"],
                region_pattern=e["region_pattern"],
                demographic_filter=e["demographic_filter"],
                force_deltas={(int(k) if k.lstrip("-").isdigit() else k): v
                              for k, v in e["force_deltas"].items()},
                decay_half_life=e["decay_half_life"], source=e["source"],
            ))

        rng = np.random.default_rng()
        rng.bit_generator.state = meta["rng_state"]

        state = WorldState(
            civ=civ, event_log=log,
            t=meta["t"], tick_count=meta["ticks"],
            question_history=[], coupling_matrix={},
            last_fired=meta.get("last_fired", {}),
            rng=rng,
        )
        return cls(state, p, meta)

    # ── time ──

    def tick(
        self,
        questions: List[Question],
        days: int = 1,
        save: bool = True,
        **tick_kwargs,
    ) -> None:
        """Advance the world. Deterministic given the persisted rng state."""
        for _ in range(days):
            world_tick(self.state, questions=questions, dt=1.0, **tick_kwargs)
        if save:
            self.save()

    # ── §34 census-drift guard ──

    def drift_report(self) -> Dict[str, Dict[str, float]]:
        """Per-country drift of guarded trait means from frozen anchors."""
        civ = self.state.civ
        out: Dict[str, Dict[str, float]] = {}
        for c_str, anchor in self.meta["anchors"].items():
            mask = civ.country == int(c_str)
            if not mask.any():
                continue
            drifts = {t: float(getattr(civ, t)[mask].mean()) - anchor[t]
                      for t in _DRIFT_TRAITS}
            worst = max(drifts.values(), key=abs)
            out[c_str] = {**drifts, "max_abs": abs(worst)}
        return out

    def re_anchor(self, tolerance: float = 0.05) -> int:
        """Pull drifted cells back toward their frozen anchors.

        Only the mean excess beyond tolerance is removed — agents keep
        their within-cell variation (their lived history); the cell as a
        whole stops misrepresenting its demographic weight.
        """
        civ = self.state.civ
        fixed = 0
        for c_str, anchor in self.meta["anchors"].items():
            mask = civ.country == int(c_str)
            if not mask.any():
                continue
            for t in _DRIFT_TRAITS:
                arr = getattr(civ, t)
                drift = float(arr[mask].mean()) - anchor[t]
                if abs(drift) > tolerance:
                    excess = drift - np.sign(drift) * tolerance
                    arr[mask] = np.clip(arr[mask] - excess, 0, 1)
                    fixed += 1
        return fixed
