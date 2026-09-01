"""THE EVENT WIRE — individual moments, published with provenance.

Observation-only: tick code appends to the sink at the exact points
where the event masks already exist; nothing here draws randomness or
writes world state, so flag-off (and flag-on) runs are bitwise
identical to an uninstrumented world — the D3-style hash gate proves
it. The daemon drains the sink once per tick into an append-only,
hash-chained JSONL; the API serves the tail read-only.

Kinds (v1): job_lost, job_found, partnership, firm_failed, firm_opened,
protest_onset, birth, death, eviction, migration.
"""
import hashlib
import json
import os
import threading

_SINK: list = []
_LOCK = threading.Lock()
_ENABLED = os.environ.get("EARTH1_EVENT_WIRE", "off") == "on"
WIRE_PATH = os.environ.get("EARTH1_EVENT_WIRE_PATH",
                           "/opt/earth1-data/event_wire.jsonl")
_MAX_IDS = 12          # a moment names a few people, never a census


def enabled() -> bool:
    return _ENABLED


def emit(kind: str, day: float, agent_ids=None, country: int = -1,
         loc: int = -1, detail: str = ""):
    """Called from tick code. Free when the wire is off."""
    if not _ENABLED:
        return
    ids = (list(map(int, agent_ids[:_MAX_IDS]))
           if agent_ids is not None else [])
    _SINK.append({"kind": kind, "day": float(day), "agents": ids,
                  "country": int(country), "loc": int(loc),
                  "detail": detail})


def drain(world_meta: dict) -> int:
    """Daemon-side: flush the sink to the chained wire. Returns count."""
    global _SINK
    if not _ENABLED or not _SINK:
        _SINK = []
        return 0
    with _LOCK:
        batch, _SINK = _SINK, []
        prev = "GENESIS"
        if os.path.exists(WIRE_PATH):
            with open(WIRE_PATH, "rb") as f:
                try:
                    f.seek(-4096, 2)
                except OSError:
                    f.seek(0)
                tail = f.read().decode(errors="replace").strip().split("\n")
                if tail and tail[-1]:
                    prev = json.loads(tail[-1])["_hash"]
        with open(WIRE_PATH, "a") as f:
            for ev in batch:
                rec = {**ev, **world_meta, "_prev": prev}
                rec["_hash"] = hashlib.sha256(
                    json.dumps(rec, sort_keys=True).encode()).hexdigest()
                f.write(json.dumps(rec, sort_keys=True) + "\n")
                prev = rec["_hash"]
        return len(batch)


def tail(n: int = 200, since_day: float = None) -> list:
    if not os.path.exists(WIRE_PATH):
        return []
    out = []
    with open(WIRE_PATH) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since_day is not None and rec.get("day", -1) <= since_day:
                continue
            out.append(rec)
    return out[-n:]
