"""PERSISTENCE — one save path for the living world, driven by the schema.

Phase 0.0c. No physics.

Two hand-maintained field lists used to decide what survived a restart:
`scripts/world_alive.py`'s save dict and `timeline._save`'s. Both were
incomplete, and incompleteness here is not a missing number — it is a
different world. On 2026-08-18 commit d3d2a0c fixed the climate and
flourishing fields that a restart had been silently wiping in
production, and *in the same commit* introduced `presence` and
`mobility` unpersisted. A hand-written list will keep losing new state
as the world grows, because nobody remembers to edit it.

So this module never names a field. It walks `dataclasses.fields(World)`
and saves what it finds. Add a field to the world and it is persisted;
`tests/test_persistence_roundtrip.py::test_every_world_field_is_saved`
fails loudly if that ever stops being true.

Two defects this closes, beyond the missing fields themselves:

  * `timeline.restore` dropped `presence`/`mobility`, which are
    None-defaulted optionals gated at `alive.py:150,160` — so a restored
    world ran *without* contagion, crowds, riots, road deaths or flight
    cultural mixing, permanently and silently. Different physics, not a
    state gap.
  * `world_alive.load_world` called `birth_world()` first and restored
    over the top, so `presence.locality` was rebuilt from a *fresh*
    genesis population and was stale against the world that came back.
    Loading no longer births anything.

Backward compatibility is mandatory, not polite: the world box holds a
live 4M-agent population in the pre-schema format. `load_world` reads
v0 files and reports what they could not carry, rather than orphaning
110 days of history.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pickle
import time
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from earth1.provenance import SCHEMA_VERSION

# Fields whose absence changes which code paths run, rather than merely
# losing values. `live_one_day` gates on these being non-None
# (alive.py:150,160), so a restore that drops them silently disables
# contagion, shared attention and mobility.
PHYSICS_GATING_FIELDS = ("presence", "mobility")

# ── the persistence policy ──────────────────────────────────────────
#
# Every field of World must be declared here, in exactly one set. This
# is deliberately NOT auto-discovered: a serializer that silently
# absorbs whatever it finds cannot tell you that you forgot to think
# about a new field. Adding a field to World and running the suite
# fails at `test_persistence_policy_is_complete` until you decide, in
# writing, whether it is state or scratch.
#
# That is the permanent cure for the d3d2a0c defect class, where the
# commit that fixed climate/flourishing persistence introduced
# presence/mobility unpersisted in the same patch.

PERSISTENT_FIELDS = frozenset({
    "civ", "life", "fabric", "health", "knowledge", "gov", "klass",
    "chronicle", "feed", "climate", "flourishing", "presence",
    "mobility", "day",
})

# name -> why it is safe to rebuild rather than carry. Nothing qualifies
# today; `susceptibility` is the shape of a future entry (recomputed
# fresh every tick at alive.py:142 and never read across a boundary).
TRANSIENT_FIELDS: Dict[str, str] = {}


def world_fields() -> Tuple[str, ...]:
    """Every field of the World dataclass, as the code defines it now."""
    from earth1.alive import World
    return tuple(f.name for f in dataclass_fields(World))


def policy_gaps() -> Dict[str, Tuple[str, ...]]:
    """Fields the policy has not accounted for, in both directions.

    `undeclared` — on World, in neither set: someone added state and the
    persistence system was never taught about it.
    `stale` — declared here but no longer on World: the policy is
    describing a world that does not exist.
    """
    actual = set(world_fields())
    declared = set(PERSISTENT_FIELDS) | set(TRANSIENT_FIELDS)
    return {"undeclared": tuple(sorted(actual - declared)),
            "stale": tuple(sorted(declared - actual))}


def _assert_policy_current() -> None:
    gaps = policy_gaps()
    if gaps["undeclared"]:
        raise ValueError(
            f"World fields not declared in the persistence policy: "
            f"{', '.join(gaps['undeclared'])}. Add each to "
            f"PERSISTENT_FIELDS or TRANSIENT_FIELDS (with a reason) in "
            f"earth1/persistence.py — refusing to guess whether new "
            f"state should survive a restart.")
    if gaps["stale"]:
        raise ValueError(
            f"persistence policy names fields World no longer has: "
            f"{', '.join(gaps['stale'])}")


def _sha256_stream(path: Path, chunk: int = 1 << 20) -> str:
    """Digest a file without loading it — the live world is ~18 GB."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


# ── state hashing ───────────────────────────────────────────────────

def _feed(h: "hashlib._Hash", obj: Any, depth: int = 0) -> None:
    """Fold any world object into a hash, deterministically.

    Ordering is explicit everywhere (sorted keys, sorted dataclass
    fields) so the digest depends on state and never on dict insertion
    order or memory layout.
    """
    if depth > 12:                                   # cycles / absurd nesting
        h.update(b"<deep>")
        return
    if obj is None:
        h.update(b"<none>")
    elif isinstance(obj, np.ndarray):
        h.update(str(obj.dtype).encode())
        h.update(str(obj.shape).encode())
        h.update(np.ascontiguousarray(obj).tobytes())
    elif hasattr(obj, "tocsr") and hasattr(obj, "indptr"):   # scipy sparse
        m = obj.tocsr()
        m.sort_indices()
        for part in (m.indptr, m.indices, m.data):
            _feed(h, np.ascontiguousarray(part), depth + 1)
        h.update(str(m.shape).encode())
    elif isinstance(obj, (bool, int, float, np.integer, np.floating)):
        # bool before int on purpose: True and 1 must not collide
        h.update(f"{type(obj).__name__}:{obj!r}".encode())
    elif isinstance(obj, (str, bytes)):
        h.update(obj if isinstance(obj, bytes) else obj.encode())
    elif isinstance(obj, dict):
        for k in sorted(obj, key=repr):
            _feed(h, k, depth + 1)
            _feed(h, obj[k], depth + 1)
    elif isinstance(obj, (list, tuple)):
        h.update(f"<seq:{len(obj)}>".encode())
        for v in obj:
            _feed(h, v, depth + 1)
    elif hasattr(obj, "__dataclass_fields__"):
        h.update(type(obj).__name__.encode())
        for name in sorted(obj.__dataclass_fields__):
            h.update(name.encode())
            _feed(h, getattr(obj, name, None), depth + 1)
    else:
        h.update(repr(obj).encode())


def world_hash(w) -> str:
    """A digest of the entire world — every component, not just civ.

    The existing `living.pop_hash_full` covers `civ` and the graph only,
    which is why a world could lose its weather, its hunger and its
    crowds and still hash as unchanged.
    """
    h = hashlib.sha256()
    for name in world_fields():
        h.update(name.encode())
        _feed(h, getattr(w, name, None))
    return h.hexdigest()


# ── save ────────────────────────────────────────────────────────────

def _detach_adj(w):
    """Shallow copies of civ/fabric with `adj` removed.

    `alive.py:64` aliases `civ.adj = fabric.adj`, so the graph would
    otherwise be pickled twice. scipy's compressed npz is far smaller
    than pickle for an 18 GB world, so the graph travels as npz and the
    copies keep the originals untouched — the live daemon is mid-day
    when this runs.
    """
    civ = copy.copy(w.civ)
    civ.adj = None
    fab = None
    if w.fabric is not None:
        fab = copy.copy(w.fabric)
        fab.adj = None
    return civ, fab


def save_world(w, path, rng: Optional[np.random.Generator] = None,
               extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Write the complete world. Returns the sidecar metadata written.

    `path` is the pickle; the graph goes beside it as `<path>.adj.npz`.
    Passing `rng` persists the generator state, without which a restored
    world continues on a different stream than the one that saved it.
    """
    from scipy import sparse

    _assert_policy_current()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # the graph is written atomically too. sparse.save_npz truncates its
    # destination in place, which left a 210 MB world.adj.npz inside a
    # verified production backup on 2026-08-19 — the manifest faithfully
    # recorded the truncation and the restore rehearsal caught it at
    # load. tmp name must end in .npz or save_npz appends the suffix.
    adj_tmp = path.with_suffix(".adj.tmp.npz")
    sparse.save_npz(adj_tmp, w.civ.adj.tocsr())
    adj_tmp.replace(path.with_suffix(".adj.npz"))

    civ, fab = _detach_adj(w)
    payload = {name: getattr(w, name) for name in PERSISTENT_FIELDS}
    payload["civ"] = civ
    if fab is not None and "fabric" in payload:
        payload["fabric"] = fab

    blob = {
        "schema_version": SCHEMA_VERSION,
        "fields": payload,
        "field_names": sorted(PERSISTENT_FIELDS),
        "rng_state": (None if rng is None
                      else rng.bit_generator.state),
        "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n": int(w.civ.n),
        "seed": int(w.civ.seed),
        "day": int(w.day),
    }
    if extra:
        blob["extra"] = dict(extra)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(blob, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)                       # atomic: never a torn world

    # checksum written AFTER the world, and last of all — its presence
    # is itself the signal that the save completed. A snapshot with no
    # sidecar is a snapshot that was interrupted.
    digest = _sha256_stream(path)
    path.with_suffix(path.suffix + ".sha256").write_text(digest + "\n")

    return {"schema_version": SCHEMA_VERSION, "day": blob["day"],
            "n": blob["n"], "seed": blob["seed"],
            "saved_at": blob["saved_at"], "sha256": digest,
            "rng_persisted": rng is not None}


# ── load ────────────────────────────────────────────────────────────

def _restore_v0(d: Dict[str, Any], adj) -> Tuple[Any, list]:
    """Read a pre-schema snapshot. Returns (world, list of losses).

    Two v0 dialects existed: `timeline._save` pickled `civ` whole, while
    `world_alive.save_world` pickled a dict of 25 named civ arrays and
    relied on `birth_world` to supply the rest. Both are read here; only
    the second can lose the five optional Civilization fields.
    """
    from earth1.alive import World

    lost = []
    civ = d["civ"]
    if isinstance(civ, dict):
        # the world_alive dialect: named arrays over a fresh genesis
        from earth1.genesis import genesis
        base = genesis(int(d["n"]), int(d["seed"]))
        for k, v in civ.items():
            setattr(base, k, v)
        for opt in ("religiosity", "marital", "employed", "ideology",
                    "social_class"):
            if opt not in civ:
                lost.append(f"civ.{opt}")
        civ = base

    kw = {"civ": civ, "day": d.get("day", 0)}
    for name in world_fields():
        if name in ("civ", "day"):
            continue
        if d.get(name) is not None:
            kw[name] = d[name]
        else:
            lost.append(name)

    w = World(**kw)
    civ.adj = adj
    if w.fabric is not None and getattr(w.fabric, "adj", None) is None:
        w.fabric.adj = adj

    # REBUILD the physics-gating subsystems the v0 format never wrote.
    # Leaving them None does not merely lose values — live_one_day gates
    # contagion, shared attention and mobility on them being non-None
    # (alive.py:150,160), so a None-migrated world runs REDUCED PHYSICS,
    # silently, forever. The first production migration (2026-08-19,
    # day 284) shipped exactly that defect: this function printed
    # "rebuilt at birth values" while rebuilding nothing, and the
    # restore rehearsal on prime caught it 20 world-days later. The
    # boundary record already declares these fields discontinuous;
    # rebuilding at birth values is the documented migration semantic.
    if w.presence is None:
        from earth1.contagion import birth_presence
        w.presence = birth_presence(w.civ, seed=int(d.get("seed", 0)))
    if w.mobility is None:
        from earth1.mobility import birth_mobility
        w.mobility = birth_mobility(w.civ, w.life,
                                    seed=int(d.get("seed", 0)))
    return w, lost


class SnapshotError(RuntimeError):
    """A snapshot could not be loaded as the world it claims to be."""


def load_world(path, *, allow_v0_migration: bool = False,
               verify_checksum: bool = True,
               adj_path=None
               ) -> Tuple[Any, Optional[dict], Dict[str, Any]]:
    """Read a world, failing closed. Returns (world, rng_state, info).

    Every failure mode raises rather than substituting a default. A
    missing stateful module is not a world with a gap — it is a
    different universe, and it must never be handed back as if it were
    the one that was saved.

    `allow_v0_migration` opts in to reading a pre-schema snapshot. It is
    off by default precisely because those files silently lack
    presence/mobility/RNG; migrating one is a deliberate, once-only act
    at a controlled checkpoint, never an incidental load.
    """
    from scipy import sparse

    path = Path(path)
    if not path.exists():
        raise SnapshotError(f"no snapshot at {path}")

    sidecar = path.with_suffix(path.suffix + ".sha256")
    checksum_state = "absent"
    if sidecar.exists():
        want = sidecar.read_text().strip()
        got = _sha256_stream(path)
        if want != got:
            raise SnapshotError(
                f"snapshot checksum mismatch at {path}: expected "
                f"{want[:16]}, got {got[:16]} — the file is corrupt or "
                f"was written by an interrupted save")
        checksum_state = "verified"
    elif verify_checksum:
        checksum_state = "missing"      # v0 files have none; v1 always do

    try:
        with open(path, "rb") as f:
            d = pickle.load(f)
    except (pickle.UnpicklingError, EOFError, AttributeError) as e:
        raise SnapshotError(f"snapshot at {path} is unreadable: {e}") from e

    # the daemon's pre-schema layout kept the graph at a fixed sibling
    # path rather than beside the pickle; `adj_path` lets a caller point
    # at it without a second serializer existing
    ap = Path(adj_path) if adj_path else path.with_suffix(".adj.npz")
    if not ap.exists():
        raise SnapshotError(f"snapshot at {path} has no graph ({ap})")
    adj = sparse.load_npz(ap)

    version = d.get("schema_version")

    if version is None:
        if not allow_v0_migration:
            raise SnapshotError(
                f"{path} is a pre-schema (v0) snapshot. It cannot carry "
                f"{', '.join(PHYSICS_GATING_FIELDS)} or the RNG stream, so "
                f"loading it would resume a world with different physics "
                f"than the one that was saved. Pass "
                f"allow_v0_migration=True to migrate it deliberately.")
        w, lost = _restore_v0(d, adj)
        return w, None, {"schema_version": 0, "lost": lost,
                         "migrated_from": 0, "checksum": checksum_state}

    if version > SCHEMA_VERSION:
        raise SnapshotError(
            f"snapshot schema v{version} is newer than this code "
            f"(v{SCHEMA_VERSION}) — refusing to guess at fields it does "
            f"not know about")

    _assert_policy_current()
    fld = d.get("fields") or {}
    missing = sorted(set(PERSISTENT_FIELDS) - set(fld))
    if missing:
        raise SnapshotError(
            f"snapshot at {path} is missing persistent state: "
            f"{', '.join(missing)}. Refusing to substitute defaults — a "
            f"world with regenerated {missing[0]} is not the world that "
            f"was saved.")
    # present-as-None is as bad as absent for the gating fields:
    # live_one_day switches whole subsystems off on None (alive.py:150,
    # 160), so such a snapshot resumes with different physics. The first
    # production migration wrote exactly this kind of v1 snapshot; it
    # must never load as if whole.
    none_gating = sorted(f for f in PHYSICS_GATING_FIELDS
                         if fld.get(f) is None)
    if none_gating:
        raise SnapshotError(
            f"snapshot at {path} carries {', '.join(none_gating)} as "
            f"None — a world saved without these subsystems runs reduced "
            f"physics on resume. This snapshot is defective; restore "
            f"from a complete one, or re-migrate from the v0 origin.")

    from earth1.alive import World
    w = World(**{k: v for k, v in fld.items() if k in PERSISTENT_FIELDS})
    w.civ.adj = adj
    if w.fabric is not None:
        w.fabric.adj = adj
    return w, d.get("rng_state"), {"schema_version": version, "lost": [],
                                   "saved_at": d.get("saved_at"),
                                   "checksum": checksum_state}


def rng_from_state(state: Optional[dict],
                   fallback_seed: Optional[int] = None
                   ) -> np.random.Generator:
    """Rebuild the exact generator a snapshot was saved with.

    Without this a restored world advances on a different random stream,
    so save->restore->step and step-without-saving diverge even at the
    same seed.
    """
    if state is None:
        return np.random.default_rng(fallback_seed)
    rng = np.random.default_rng()
    rng.bit_generator.state = state
    return rng
