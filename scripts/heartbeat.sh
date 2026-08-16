#!/bin/zsh
# Earth-1 daily heartbeat — run by launchd every morning.
# The world ticks, reads today's news, arms and resolves the record.
set -u
REPO="/Users/pietronovelli/Documents/GitHub/earth-1-engine"
LOG="$REPO/data/living/heartbeat.log"

cd "$REPO" || exit 1
[ -f .env ] && export $(grep -v '^#' .env | xargs)

{
  echo "=== heartbeat $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  /usr/bin/python3 -u scripts/world_daily.py --read-news
  echo "=== done $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$? ==="
} >> "$LOG" 2>&1
