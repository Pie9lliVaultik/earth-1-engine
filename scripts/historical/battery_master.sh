#!/bin/bash
# Battery master: wait for archives -> six 20k events in parallel ->
# two 200k flagships (GFC, COVID). Fidelity per the founder ruling.
set -u
cd /opt/earth1
LOG=/opt/earth1-data/battery_master.log
echo "MASTER START $(date -u +%FT%TZ)" >> "$LOG"
until grep -q ARCHIVES_DONE /opt/earth1-data/archives_dl.log 2>/dev/null; do sleep 60; done
echo "archives ready $(date -u +%FT%TZ)" >> "$LOG"
for EV in truss_2022 sri_lanka_2022 chile_2019 iran_war_2025 jan6_2021; do
  bash scripts/historical/hist_pipeline.sh $EV &
done
wait
echo "20k wave complete $(date -u +%FT%TZ)" >> "$LOG"
for EV in gfc_2008 covid_2020; do
  bash scripts/historical/hist_pipeline.sh $EV &
done
wait
echo "MASTER COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
