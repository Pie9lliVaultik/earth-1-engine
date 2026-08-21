#!/bin/bash
# EARTH-1 — LIVE CIVILIZATION OBSERVATORY (local, read-only).
# One command: births a demo-scale civilization through the canonical
# engine, starts the read-only API + dashboard, opens the browser.
# Never touches canonical production state.
set -e
cd "$(dirname "$0")/.."
PORT="${EARTH1_OBS_PORT:-8811}"
echo "EARTH-1 Observatory starting on http://127.0.0.1:${PORT}"
( sleep 6 && command -v open >/dev/null && open "http://127.0.0.1:${PORT}" ) &
exec python3 -m uvicorn scripts.observatory_server:app \
  --host 127.0.0.1 --port "${PORT}" --log-level warning
