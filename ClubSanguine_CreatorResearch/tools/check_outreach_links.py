"""Read-only checks that keep the Outreach Desk from sending the owner to dead ends.

    python tools/check_outreach_links.py discord   # is each Discord invite still valid?
    python tools/check_outreach_links.py titles    # title of every evidence video (still online?)
    python tools/check_outreach_links.py all

discord: asks Discord's public invite endpoint (no login) whether each invite in creators.csv,
exports/creator_links.csv and the press CSVs still resolves. Writes exports/discord_invites.csv
(code, status valid|expired|unknown, server name, members). The dashboard drops expired invites.

titles: looks up every evidence video's title, first from the YouTube cache in exports/harvest,
then YouTube's public oEmbed endpoint. Writes exports/evidence_titles.csv (video_id, title,
status ok|gone|unknown). Drafts quote this exact title instead of inventing familiarity.

Nothing here logs in, messages anyone or changes creators.csv. Results are cached; rerun to
retry `unknown` rows only (add --force to recheck everything).
"""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
INVITES_CSV = PROJECT / "exports" / "discord_invites.csv"
TITLES_CSV = PROJECT / "exports" / "evidence_titles.csv"
UA = {"User-Agent": "Mozilla/5.0 (ClubSanguine outreach link check)"}

INVITE_RE = re.compile(r"(?:discord\.gg|discord(?:app)?\.com/invite)/([\w-]+)", re.I)
VIDEO_RE = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/live/)([\w-]{11})")


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def get_json(url):
    """(status_code, parsed json or None). Retries politely on 429."""
    for _ in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    wait = float(json.loads(e.read().decode("utf-8")).get("retry_after", 5))
                except (ValueError, AttributeError):
                    wait = 5
                time.sleep(min(wait, 60) + 1)
                continue
            return e.code, None
        except (urllib.error.URLError, TimeoutError, ValueError):
            time.sleep(3)
    return 0, None


def all_text_cells():
    for path in (PROJECT / "creators.csv", PROJECT / "exports" / "creator_links.csv",
                 PROJECT / "press" / "outlets.csv", PROJECT / "press" / "journalists.csv"):
        for row in read_csv(path):
            yield from row.values()


def check_discord(force):
    cache = {r["code"]: r for r in read_csv(INVITES_CSV)}
    codes = sorted({m.group(1) for cell in all_text_cells() for m in INVITE_RE.finditer(cell or "")})
    todo = [c for c in codes if force or cache.get(c, {}).get("status") in (None, "", "unknown")]
    print(f"{len(codes)} invites, checking {len(todo)}")
    for i, code in enumerate(todo, 1):
        status, data = get_json(f"https://discord.com/api/v10/invites/{urllib.parse.quote(code)}?with_counts=true")
        row = {"code": code, "checked": date.today().isoformat(), "server": "", "members": ""}
        if status == 200 and data:
            row.update(status="valid", server=(data.get("guild") or {}).get("name", ""),
                       members=data.get("approximate_member_count", ""))
        elif status == 404:
            row["status"] = "expired"
        else:
            row["status"] = "unknown"
        cache[code] = row
        if i % 25 == 0 or i == len(todo):
            write_csv(INVITES_CSV, ["code", "status", "server", "members", "checked"], sorted(cache.values(), key=lambda r: r["code"]))
            print(f"  {i}/{len(todo)}")
        time.sleep(1.2)
    counts = {}
    for r in cache.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("discord:", counts)


def harvest_titles():
    titles = {}

    def walk(o):
        if isinstance(o, dict):
            vid, t = o.get("video_id"), o.get("title")
            if vid and isinstance(t, str) and t:
                titles.setdefault(vid, t)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for p in (PROJECT / "exports" / "harvest").rglob("*.json"):
        try:
            walk(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return titles


def check_titles(force):
    cache = {r["video_id"]: r for r in read_csv(TITLES_CSV)}
    ids = []
    for r in read_csv(PROJECT / "creators.csv"):
        for i in (1, 2, 3):
            m = VIDEO_RE.search(r.get(f"evidence_url_{i}") or "")
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
    known = harvest_titles()
    for vid in ids:
        if vid in known and (force or vid not in cache):
            cache[vid] = {"video_id": vid, "title": known[vid], "status": "ok", "source": "harvest"}
    todo = [v for v in ids if force and cache.get(v, {}).get("source") != "harvest"
            or cache.get(v, {}).get("status") in (None, "", "unknown")]
    print(f"{len(ids)} evidence videos, {len(ids) - len(todo)} known, looking up {len(todo)}")
    for i, vid in enumerate(todo, 1):
        url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
        status, data = get_json(url)
        if status == 200 and data:
            cache[vid] = {"video_id": vid, "title": data.get("title", ""), "status": "ok", "source": "oembed"}
        elif status in (400, 401, 403, 404):
            cache[vid] = {"video_id": vid, "title": "", "status": "gone", "source": "oembed"}
        else:
            cache[vid] = {"video_id": vid, "title": "", "status": "unknown", "source": "oembed"}
        if i % 50 == 0 or i == len(todo):
            write_csv(TITLES_CSV, ["video_id", "title", "status", "source"], sorted(cache.values(), key=lambda r: r["video_id"]))
            print(f"  {i}/{len(todo)}")
        time.sleep(0.35)
    write_csv(TITLES_CSV, ["video_id", "title", "status", "source"], sorted(cache.values(), key=lambda r: r["video_id"]))
    counts = {}
    for r in cache.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("titles:", counts)


def main(argv):
    what = argv[0] if argv else "all"
    force = "--force" in argv
    if what in ("titles", "all"):
        check_titles(force)
    if what in ("discord", "all"):
        check_discord(force)


if __name__ == "__main__":
    main(sys.argv[1:])
