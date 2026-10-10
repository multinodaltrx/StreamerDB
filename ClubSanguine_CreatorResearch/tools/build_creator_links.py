#!/usr/bin/env python3
"""Export every public link creators list on their YouTube About panel.

    python tools/build_creator_links.py          # writes exports/creator_links.csv
    python tools/build_creator_links.py --missing   # print channel IDs with no cached About page

Reads the About cache (exports/harvest/about/, fetched by `yt_harvest.py about`). The
output is committed, so the Outreach Desk can show all socials even without the cache.
Only links the creator published themselves are included; nothing is inferred.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABOUT = ROOT / "exports" / "harvest" / "about"
OUT = ROOT / "exports" / "creator_links.csv"
SKIP = ("teespring.", "creator-spring.", "spreadshirt.", "store.", "shop.", "merch", "amazon.", "amzn.", "bandcamp.")

rows = list(csv.DictReader(open(ROOT / "creators.csv", encoding="utf-8")))
if "--missing" in sys.argv:
    for r in rows:
        cid = r["youtube_channel_id"].strip()
        if cid and cid != "Unknown" and not (ABOUT / f"{cid}.json").exists():
            print(cid)
    sys.exit(0)

old = {}
if OUT.exists():  # keep links for creators whose About page is no longer cached
    for r in csv.DictReader(open(OUT, encoding="utf-8")):
        old.setdefault(r["creator_id"], []).append(r)
out, n_cached = [], 0
for r in rows:
    f = ABOUT / f"{r['youtube_channel_id'].strip()}.json"
    if not f.exists():
        out += old.get(r["creator_id"], [])
        continue
    n_cached += 1
    seen = set()
    about = json.loads(f.read_text(encoding="utf-8"))
    for link in about.get("links", []):
        url = link["url"].strip()
        if not url or any(s in url.lower() for s in SKIP):
            continue
        url = url if "://" in url else "https://" + url
        if url.lower() in seen:
            continue
        seen.add(url.lower())
        out.append({"creator_id": r["creator_id"], "title": link.get("title", "").strip() or "Link", "url": url})
    for e in about.get("emails", []):
        out.append({"creator_id": r["creator_id"], "title": "Email (description)", "url": "mailto:" + e})
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["creator_id", "title", "url"])
    w.writeheader()
    w.writerows(out)
print(f"{len(out)} links for {len({x['creator_id'] for x in out})} creators ({n_cached} About pages cached) -> {OUT}")
