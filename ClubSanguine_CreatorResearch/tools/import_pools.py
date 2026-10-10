#!/usr/bin/env python3
"""Import reviewed chunk pools into creators.csv as 100-creator batches.

    python tools/import_pools.py <first_batch>[:<cap>] <chunk numbers...>
    e.g. python tools/import_pools.py 17 1 2 3       -> Batch 017, 018, ... from review_log chunks 1-3
         python tools/import_pools.py 17:40 4 5      -> top up Batch 017 with 40 rows first, then 018...

It skips:
- creators already in the CSV (by channel ID)
- second channels sharing a business email with an existing row
- names in DROP

It also fetches TwitchTracker summaries for linked Twitch channels.
For each batch it then runs: import -> creator_db dedupe -> score_creator recalc -> validate_data.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "exports" / "review_log"
sys.path.insert(0, str(ROOT / "scripts"))
import yt_harvest as yt  # noqa: E402

DROP = set()  # exact channel names to skip, e.g. second channels of creators rejected for size

spec, chunks = sys.argv[1], sys.argv[2:]
first, cap = (int(x) for x in spec.split(":")) if ":" in spec else (int(spec), 100)
rows = list(csv.DictReader(open(ROOT / "creators.csv", encoding="utf-8")))
seen = {r["youtube_channel_id"] for r in rows}
emails = {r["business_email"].lower() for r in rows if "@" in r["business_email"]}
pool = []
for k in chunks:
    for r in json.loads((LOG / f"pool_c{k}.json").read_text(encoding="utf-8")):
        e = (r.get("email") or "").lower()
        if r["channel_id"] in seen or r["name"].strip() in DROP or (e and e in emails):
            print("skip (already present / same creator / dropped):", r["name"])
            continue
        seen.add(r["channel_id"])
        if e:
            emails.add(e)
        pool.append(r)
print("new records", len(pool))

users = set()
for r in pool:
    a = ROOT / "exports" / "harvest" / "about" / f"{r['channel_id']}.json"
    if a.exists():
        for link in json.loads(a.read_text(encoding="utf-8"))["links"]:
            m = re.search(r"twitch\.tv/([A-Za-z0-9_]{3,25})", link["url"])
            if m:
                users.add(m.group(1).lower())
for u in sorted(users):
    try:
        yt.do_twitch(u)
    except Exception as exc:  # TwitchTracker rate-limits often; the row still imports
        print("twitch fail", u, exc)

parts = [pool[:cap]] + [pool[i:i + 100] for i in range(cap, len(pool), 100)]
n = first
for part in parts:
    if not part:
        continue
    label = f"Batch {n:03d}"
    out = ROOT / "exports" / f"batch_{n:03d}_candidates.json"
    suffix = 2
    while out.exists():
        out = ROOT / "exports" / f"batch_{n:03d}_candidates_part{suffix}.json"
        suffix += 1
    out.write_text(json.dumps(part, indent=1, ensure_ascii=False), encoding="utf-8")
    for cmd in (["exports/import_batch.py", "import", str(out), label], ["scripts/creator_db.py", "dedupe"],
                ["scripts/score_creator.py", "recalc"]):
        print(subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True, text=True).stdout.strip())
    v = subprocess.run([sys.executable, "scripts/validate_data.py"], cwd=ROOT, capture_output=True, text=True).stdout
    print(label, v.strip().splitlines()[-2])
    n += 1
