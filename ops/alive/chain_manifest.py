#!/usr/bin/env python3
"""Append a hash-chained integrity entry for the history record.

Founder ruling 2026-08-31: the cascade/history record is the Result-2
reconstruction asset; it must be tamper-evident, not only copied. Each
backup run appends one entry to data/alive/history_chain.jsonl:
{stamp, world_day, history_sha256, cascade_rows, _prev, _hash} where
_hash = sha256 over the canonical entry + _prev. The chain file rides
inside every far-end snapshot, so any later edit of an old snapshot's
history breaks the chain visible in every newer snapshot.
"""
import hashlib
import json
import os
import sqlite3
import sys
import time

ALIVE = sys.argv[1] if len(sys.argv) > 1 else "/opt/earth1/data/alive"
CHAIN = os.path.join(ALIVE, "history_chain.jsonl")
H = os.path.join(ALIVE, "history.sqlite")

h = hashlib.sha256()
with open(H, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 22), b""):
        h.update(chunk)
con = sqlite3.connect(f"file:{H}?mode=ro", uri=True)
day = con.execute("SELECT value FROM meta WHERE key='last_day'").fetchone()
rows = con.execute("SELECT COUNT(*) FROM cascades").fetchone()[0]
prev = "GENESIS"
if os.path.exists(CHAIN):
    for line in open(CHAIN):
        prev = json.loads(line)["_hash"]
entry = {"stamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "world_day": int(day[0]) if day else None,
         "history_sha256": h.hexdigest(), "cascade_rows": int(rows),
         "_prev": prev}
entry["_hash"] = hashlib.sha256(
    json.dumps(entry, sort_keys=True).encode()).hexdigest()
with open(CHAIN, "a") as f:
    f.write(json.dumps(entry, sort_keys=True) + "\n")
print("CHAINED", entry["world_day"], entry["cascade_rows"],
      entry["_hash"][:12])
