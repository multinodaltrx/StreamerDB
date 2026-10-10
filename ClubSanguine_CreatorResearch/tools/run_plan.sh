#!/usr/bin/env bash
# Run a search plan (lines: query|sp|pages|force) through yt_harvest.py search.
# Usage: bash tools/run_plan.sh exports/review_log/plans/planN.txt
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
tr -d '\r' < "$1" | while IFS='|' read -r q sp pages force; do
  [ -z "$q" ] && continue
  echo ">> $q [$sp x$pages]"
  python scripts/yt_harvest.py search "$q" --sp "$sp" --pages "$pages" ${force:+--force} 2>&1 | tail -1
done
echo PLAN_DONE
