#!/bin/bash
# Archive downloads for battery events 3-12 (ranges = warm windows).
set -u
cd /opt/earth1-data/gdelt
dl_range() {  # dl_range END_DATE DAYS
  local END=$1 DAYS=$2
  for i in $(seq 0 $DAYS); do
    D=$(date -d "$END -$i days" +%Y%m%d)
    [ -f gdelt_$D.zip ] || curl -sL --max-time 180 -A "Mozilla/5.0" \
      "https://data.gdeltproject.org/events/$D.export.CSV.zip" -o gdelt_$D.zip
  done
}
for M in 200806 200807 200808 200809; do
  [ -f gdelt_$M.zip ] || curl -sL --max-time 300 -A "Mozilla/5.0" \
    "https://data.gdeltproject.org/events/$M.zip" -o gdelt_$M.zip &
done
dl_range 2020-02-28 91 &
dl_range 2022-09-22 91 &
dl_range 2022-03-31 91 &
dl_range 2019-10-17 91 &
dl_range 2025-06-12 91 &
dl_range 2021-01-05 91 &
wait
echo ARCHIVES_DONE $(ls gdelt_*.zip | wc -l) files
