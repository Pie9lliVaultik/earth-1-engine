"""Experience receipts — the immutable ledger of the Experience Loop.

MISSION v2 (founder ruling 2026-08-27): every forecast is an immutable
experience candidate; every learning transition M_t + E_t -> M_{t+1}
must be replayable. Records are hash-chained JSONL: each record stores
the sha256 of the previous record, so history cannot be silently
edited; replaying the ledger from M0 must reproduce every model hash.
"""
from __future__ import annotations

import hashlib
import json
import os

REQUIRED = (
    "experience_id", "forecast_emitted_at", "forecast_world_hash",
    "model_version", "inference_version", "observation_cutoff",
    "predicted_distribution", "uncertainty", "resolution_rule",
    "resolution", "resolution_source", "score",
    "prior_posterior", "eligible_update_evidence", "posterior",
    "update_diff", "next_model_hash",
)


def _canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


class Ledger:
    """Append-only, hash-chained experience ledger."""

    def __init__(self, path: str):
        self.path = path
        self.prev_hash = "GENESIS"
        self.n = 0
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    rec = json.loads(line)
                    self.prev_hash = rec["_hash"]
                    self.n += 1

    def append(self, record: dict) -> str:
        missing = [k for k in REQUIRED if k not in record]
        if missing:
            raise ValueError(f"experience record missing {missing}")
        body = dict(record)
        body["_prev"] = self.prev_hash
        body["_seq"] = self.n
        h = hashlib.sha256(_canon(body)).hexdigest()
        body["_hash"] = h
        with open(self.path, "a") as f:
            f.write(json.dumps(body, sort_keys=True) + "\n")
        self.prev_hash = h
        self.n += 1
        return h

    def verify(self) -> int:
        """Walk the chain; raise on any break. Returns record count."""
        prev = "GENESIS"
        n = 0
        with open(self.path) as f:
            for line in f:
                rec = json.loads(line)
                h = rec.pop("_hash")
                if rec["_prev"] != prev:
                    raise ValueError(f"chain break at seq {rec['_seq']}")
                if hashlib.sha256(_canon(rec)).hexdigest() != h:
                    raise ValueError(f"tamper at seq {rec['_seq']}")
                prev = h
                n += 1
        return n


def model_hash(u: "np.ndarray", w: "np.ndarray") -> str:  # noqa: F821
    """Deterministic hash of a particle-cloud model state."""
    import numpy as np
    return hashlib.sha256(
        np.round(np.asarray(u, dtype=np.float64), 10).tobytes()
        + np.round(np.asarray(w, dtype=np.float64), 12).tobytes()
    ).hexdigest()
