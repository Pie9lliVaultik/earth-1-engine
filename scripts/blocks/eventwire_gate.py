"""Event-wire bitwise gate: flag on vs off, same seed, 20k x 30d ->
identical world hash (the wire observes; it must never touch)."""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def run(flag):
    os.environ["EARTH1_EVENT_WIRE"] = flag
    os.environ["EARTH1_EVENT_WIRE_PATH"] = "/tmp/wire_gate_test.jsonl"
    import importlib
    from earth1 import eventwire
    importlib.reload(eventwire)
    from earth1 import persistence
    from earth1.alive import birth_world, live_one_day
    w = birth_world(20000, 31337, substrate="c2plus_v1")
    rng = np.random.default_rng(31337)
    for _ in range(30):
        live_one_day(w, rng)
        eventwire.drain({"day": float(w.day), "epoch": "gate"})
    return persistence.world_hash(w)


if os.path.exists("/tmp/wire_gate_test.jsonl"):
    os.remove("/tmp/wire_gate_test.jsonl")
h_on = run("on")
n_ev = sum(1 for _ in open("/tmp/wire_gate_test.jsonl")) \
    if os.path.exists("/tmp/wire_gate_test.jsonl") else 0
h_off = run("off")
print("on ", h_on[:16], "| events published:", n_ev)
print("off", h_off[:16])
print("GATE", "PASS" if h_on == h_off else "FAIL")
