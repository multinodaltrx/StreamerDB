#!/usr/bin/env bash
# Fetch stage after new searches:
#   aggregate -> fetch new channel pages (3 workers) -> fetch About pages for filter-passing candidates (3 workers)
# Usage: bash tools/pipeline.sh <tag>      (tag only names the log files)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
H=exports/harvest
TAG=${1:-run}
python scripts/yt_harvest.py aggregate
python - <<'EOF' > $H/tofetch_$TAG.txt
import json, os, csv
c = json.load(open('exports/harvest/candidates.json', encoding='utf-8'))
db = {r['youtube_channel_id'] for r in csv.DictReader(open('creators.csv', encoding='utf-8'))}
import glob  # also skip channels already reviewed (and rejected) in earlier chunks
for f in glob.glob('exports/review_log/chunks/chunk_*.json'):
    db |= {r['cid'] for r in json.load(open(f, encoding='utf-8'))}
print('\n'.join(x['channel_id'] for x in c if x['channel_id'] not in db
                and not os.path.exists(f"exports/harvest/channels/{x['channel_id']}.json")))
EOF
echo "channels to fetch: $(grep -c . $H/tofetch_$TAG.txt)"
for w in 0 1 2; do awk -v w=$w 'NF && NR%3==w' $H/tofetch_$TAG.txt | tr -d '\r' | xargs -r -n 25 python scripts/yt_harvest.py channels > $H/fetch_${TAG}_$w.log 2>&1 & done
wait
python scripts/yt_harvest.py aggregate
python tools/review.py pending | tr -d '\r' | while read -r id; do [ -f "$H/about/$id.json" ] || echo "$id"; done > $H/about_$TAG.txt
echo "about pages to fetch: $(grep -c . $H/about_$TAG.txt)"
for w in 0 1 2; do awk -v w=$w 'NF && NR%3==w' $H/about_$TAG.txt | xargs -r -n 25 python scripts/yt_harvest.py about > $H/aboutlog_${TAG}_$w.log 2>&1 & done
wait
python tools/review.py summary
echo PIPELINE_DONE
