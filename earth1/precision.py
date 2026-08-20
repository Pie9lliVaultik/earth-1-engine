"""EARTH1_PRECISION — numerical execution modes for ensemble work.

Founder ruling (0.7): float32 may change REPRESENTATION, never model
semantics. Production and 0.8 stay float64; f64 is the reference
implementation permanently, and any optimized executor is judged
against it (ops/alive/PRECISION_EQUIVALENCE_PROTOCOL_0_7.md — the
pre-registered gate this mode must pass before it may run ensembles).

Modes:
    float64            no-op (the reference)
    float32            every float64 array in the world -> float32
    float16-control    the pre-registered DEGRADED control: state is
                       quantized through float16, then run in float32.
                       Exists so the equivalence gate can demonstrate
                       rejection (Standing Rule 2); never a production
                       or ensemble executor.

The walk is reflective and aliasing-preserving: sparse matrices are
converted in place (fab.adj IS civ.adj — both see the conversion), and
converted ndarrays are memoized by original id so shared arrays stay
shared.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

MODES = ("float64", "float32", "float16-control")


def apply_precision(w, mode: str | None):
    """Convert a loaded World's floating state to the given mode,
    in place. Returns w. float64/None is a no-op."""
    if mode in (None, "", "float64"):
        return w
    if mode == "float32":
        def conv(a):
            return a.astype(np.float32)
    elif mode == "float16-control":
        def conv(a):
            return a.astype(np.float16).astype(np.float32)
    else:
        raise ValueError(f"unknown EARTH1_PRECISION mode: {mode!r}")

    arr_memo: dict[int, np.ndarray] = {}
    seen: set[int] = set()

    def conv_arr(a: np.ndarray) -> np.ndarray:
        if a.dtype != np.float64:
            return a
        got = arr_memo.get(id(a))
        if got is None:
            got = conv(a)
            arr_memo[id(a)] = got
        return got

    def walk(obj):
        if obj is None or isinstance(obj, (str, bytes, int, float, bool,
                                           np.random.Generator)):
            return obj
        if isinstance(obj, np.ndarray):
            return conv_arr(obj)
        if sparse.issparse(obj):
            if id(obj) not in seen:
                seen.add(id(obj))
                obj.data = conv_arr(obj.data)
            return obj
        if isinstance(obj, list):
            if id(obj) not in seen:
                seen.add(id(obj))
                for i, v in enumerate(obj):
                    obj[i] = walk(v)
            return obj
        if isinstance(obj, tuple):
            return tuple(walk(v) for v in obj)
        if isinstance(obj, dict):
            if id(obj) not in seen:
                seen.add(id(obj))
                for k in obj:
                    obj[k] = walk(obj[k])
            return obj
        if hasattr(obj, "__dict__"):
            if id(obj) not in seen:
                seen.add(id(obj))
                for k, v in vars(obj).items():
                    nv = walk(v)
                    if nv is not v:
                        setattr(obj, k, nv)
            return obj
        return obj

    walk(w)
    # the loop re-coerces at each day boundary: many producers REASSIGN
    # f64 arrays mid-tick (mixed-precision temporaries are fine — the
    # heavy graph ops consume day-start state), and this mark is what
    # tells live_one_day to fold them back
    w._precision = mode
    return w


def recoerce(w) -> None:
    """Day-boundary fold-back for reduced-precision worlds. No-op for
    the f64 reference. Both float32 and float16-control run in f32
    after load (the f16 quantization is a LOAD-time degradation)."""
    mode = getattr(w, "_precision", None)
    if mode in (None, "float64"):
        return
    seen: set[int] = set()

    def walk(obj):
        if obj is None or isinstance(obj, (str, bytes, int, float, bool,
                                           np.random.Generator)):
            return obj
        if isinstance(obj, np.ndarray):
            return obj.astype(np.float32) if obj.dtype == np.float64 \
                else obj
        if sparse.issparse(obj):
            if id(obj) not in seen:
                seen.add(id(obj))
                if obj.data.dtype == np.float64:
                    obj.data = obj.data.astype(np.float32)
            return obj
        if id(obj) in seen:
            return obj
        seen.add(id(obj))
        if isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = walk(v)
        elif isinstance(obj, dict):
            for k in obj:
                obj[k] = walk(obj[k])
        elif hasattr(obj, "__dict__"):
            for k, v in vars(obj).items():
                nv = walk(v)
                if nv is not v:
                    setattr(obj, k, nv)
        return obj

    walk(w)


def float64_survivors(w, min_size: int = 1000) -> list:
    """Paths of float64 arrays still in the world — after
    apply_precision + a tick, any large entry here marks a producer
    that reassigns f64 instead of following dtype (an upcast leak)."""
    out = []
    seen: set[int] = set()

    def walk(obj, path):
        if obj is None or isinstance(obj, (str, bytes, int, float, bool,
                                           np.random.Generator)):
            return
        if isinstance(obj, np.ndarray):
            if obj.dtype == np.float64 and obj.size >= min_size:
                out.append(f"{path} {obj.shape}")
            return
        if sparse.issparse(obj):
            if obj.data.dtype == np.float64 and obj.data.size >= min_size:
                out.append(f"{path}.data {obj.data.shape}")
            return
        if id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, list):
            for i, v in enumerate(obj[:50]):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}[{k!r}]")
        elif hasattr(obj, "__dict__"):
            for k, v in vars(obj).items():
                walk(v, f"{path}.{k}")

    walk(w, "w")
    return out


def world_precision(w) -> str:
    """Report the precision of the world's central state — for
    manifests, so an f32 artifact can never masquerade as f64."""
    dt = w.civ.forces.dtype
    return {np.dtype(np.float64): "float64",
            np.dtype(np.float32): "float32"}.get(dt, str(dt))
