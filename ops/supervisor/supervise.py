#!/usr/bin/env python3
"""Earth-1 job supervisor — the machines watch themselves.

Runs every 5 minutes via systemd timer, laptop-independent. For each
job in jobs.json (same directory):

  done_check passes          -> done, hands off
  process matches pgrep      -> running, note heartbeat
  neither                    -> INCIDENT: journal the log tail and
                                relaunch (bounded retries)

Optional "requires": a shell command that must pass before a launch is
attempted (e.g. merge jobs waiting on inputs) — not passing is not an
incident, just "waiting".

State:   state.json    (retry counts — survives reboots)
Journal: journal.jsonl (append-only incident/relaunch record)
Status:  status.json   (one-glance snapshot for humans and agents)
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))


def sh(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-lc", cmd], capture_output=True,
                          text=True, timeout=120)


def jlog(rec: dict) -> None:
    rec["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(os.path.join(BASE, "journal.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def main() -> None:
    jobs = json.load(open(os.path.join(BASE, "jobs.json")))
    state_f = os.path.join(BASE, "state.json")
    state = json.load(open(state_f)) if os.path.exists(state_f) else {}
    status = {}

    for job in jobs:
        name = job["name"]
        st = state.setdefault(name, {"retries": 0})
        try:
            if sh(job["done_check"]).returncode == 0:
                status[name] = "done"
                continue
            if sh(f"pgrep -f \"{job['pgrep']}\" >/dev/null").returncode == 0:
                status[name] = "running"
                continue
            req = job.get("requires")
            if req and sh(req).returncode != 0:
                status[name] = "waiting"
                continue
            tail = sh(f"tail -12 {job.get('log', '/dev/null')} "
                      f"2>/dev/null").stdout[-1500:]
            if st["retries"] >= job.get("max_retries", 3):
                status[name] = "FAILED_GAVE_UP"
                if st.get("gave_up_logged") is None:
                    st["gave_up_logged"] = True
                    jlog({"job": name, "event": "gave_up", "tail": tail})
                continue
            st["retries"] += 1
            jlog({"job": name, "event": "relaunch",
                  "retry": st["retries"], "tail": tail})
            sh(job["launch"])
            status[name] = f"relaunched({st['retries']})"
        except Exception as e:  # a broken job spec must not kill the loop
            status[name] = f"supervisor_error: {e}"
            jlog({"job": name, "event": "supervisor_error", "error": str(e)})

    json.dump(state, open(state_f, "w"), indent=1)
    json.dump(
        {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "jobs": status},
        open(os.path.join(BASE, "status.json"), "w"), indent=1)
    print(json.dumps(status))


if __name__ == "__main__":
    main()
