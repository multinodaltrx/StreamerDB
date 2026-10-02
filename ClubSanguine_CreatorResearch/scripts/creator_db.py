#!/usr/bin/env python3
"""
creator_db.py — small CLI utility for managing creators.csv.

No external dependencies. No network access. No LLM calls.

Commands:
    python scripts/creator_db.py check
        Load creators.csv and report row count / header issues.

    python scripts/creator_db.py stats
        Print summary counts (by tier, status, platform, high_priority).

    python scripts/creator_db.py dedupe
        Scan creators.csv for likely duplicate creators, merge them
        (preserving existing non-empty data), and rewrite the file.

    python scripts/creator_db.py upsert --json '{"creator_name": "Example", ...}'
    python scripts/creator_db.py upsert --json-file new_creator.json
        Insert a new creator row, or merge into an existing matching
        row if one is found, then write creators.csv.

Dedupe key priority (strongest to weakest):
    1. youtube_channel_id
    2. twitch_username (normalized)
    3. canonical profile URL (normalized youtube_channel_url, then
       normalized twitch_channel_url, then other_social_url)
    4. normalized creator_name (weak fallback)

When merging two records for the same creator, existing non-empty
values are preserved; only empty fields are filled in from the new
data. This script never overwrites populated data with blank data,
and never silently drops rows.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CSV_PATH = PROJECT_DIR / "creators.csv"

FIELDNAMES = [
    "creator_id",
    "creator_name",
    "primary_platform",
    "youtube_channel_url",
    "youtube_channel_id",
    "youtube_subscribers",
    "twitch_channel_url",
    "twitch_username",
    "twitch_followers",
    "twitch_avg_viewers",
    "other_social_url",
    "language",
    "country",
    "last_active_date",
    "relevant_games",
    "direct_comparable_count",
    "evidence_url_1",
    "evidence_url_2",
    "evidence_url_3",
    "content_style",
    "business_email",
    "contact_page",
    "public_contact_method",
    "direct_comparable_score",
    "genre_fit_score",
    "activity_score",
    "size_score",
    "multi_game_score",
    "contact_score",
    "personality_fit_score",
    "indie_affinity_score",
    "fit_score",
    "tier",
    "high_priority",
    "status",
    "outreach_status",
    "notes",
    "date_discovered",
    "last_verified",
    "source_query",
]


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def normalize_youtube_url(raw):
    """Return a canonical, lowercase YouTube channel URL, or '' if empty."""
    if not raw:
        return ""
    raw = raw.strip()
    if not raw:
        return ""
    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlparse(candidate)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host in ("youtube.com", "m.youtube.com", "youtu.be"):
        path = parsed.path.rstrip("/")
        # Channel IDs are case-sensitive; handles are not.
        if not path.startswith('/channel/'):
            path = path.lower()
        return f"https://{host}{path}"
    # Not a recognized YouTube host; return a cleaned-up version as-is.
    return raw.rstrip("/").lower()


def normalize_twitch_username(raw):
    """Return a lowercase twitch username extracted from a URL or handle."""
    if not raw:
        return ""
    raw = raw.strip()
    if not raw:
        return ""
    if "twitch.tv" in raw.lower():
        candidate = raw if "://" in raw else "https://" + raw
        parsed = urlparse(candidate)
        path = parsed.path.strip("/")
        username = path.split("/")[0] if path else ""
    else:
        username = raw.lstrip("@")
    return username.lower()


def twitch_canonical_url(username):
    if not username:
        return ""
    return f"https://www.twitch.tv/{username}"


def normalize_generic_url(raw):
    if not raw:
        return ""
    raw = raw.strip()
    if not raw:
        return ""
    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlparse(candidate)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return f"https://{host}{path}".lower()


def normalize_name(raw):
    if not raw:
        return ""
    name = raw.strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name.strip()


# ---------------------------------------------------------------------------
# CSV I/O
# ---------------------------------------------------------------------------

def load_rows(path=CSV_PATH):
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = [dict(r) for r in reader]
    return header, rows


def save_rows(rows, path=CSV_PATH):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def blank_row():
    return {k: "" for k in FIELDNAMES}


# ---------------------------------------------------------------------------
# Identity / dedupe keys
# ---------------------------------------------------------------------------

def identity_keys(row):
    """Return the dedupe keys for a row, strongest first, as a dict."""
    row = {k: ("" if str(v).strip().lower() == "unknown" else v) for k, v in row.items()}
    yt_id = (row.get("youtube_channel_id") or "").strip()
    twitch_user = normalize_twitch_username(row.get("twitch_username") or row.get("twitch_channel_url") or "")

    profile_url = normalize_youtube_url(row.get("youtube_channel_url", ""))
    if not profile_url and row.get("twitch_channel_url"):
        profile_url = normalize_generic_url(row.get("twitch_channel_url"))
    if not profile_url and row.get("other_social_url"):
        profile_url = normalize_generic_url(row.get("other_social_url"))

    name_norm = normalize_name(row.get("creator_name", ""))

    return {
        "youtube_channel_id": yt_id,
        "twitch_username": twitch_user,
        "profile_url": profile_url,
        "name_norm": name_norm,
    }


def find_match_index(rows, candidate_keys):
    """Find the index of the first row matching candidate_keys, by priority."""
    priority = ["youtube_channel_id", "twitch_username", "profile_url", "name_norm"]
    for level in priority:
        value = candidate_keys.get(level)
        if not value:
            continue
        for i, row in enumerate(rows):
            existing_keys = identity_keys(row)
            if existing_keys.get(level) == value:
                return i
    return None


def merge_rows(existing, incoming):
    """Merge incoming into existing, preserving existing non-empty values."""
    merged = dict(existing)
    for key in FIELDNAMES:
        existing_val = (existing.get(key) or "").strip()
        incoming_val = (incoming.get(key) or "").strip()
        if (not existing_val or existing_val.lower() == "unknown") and incoming_val and incoming_val.lower() != "unknown":
            merged[key] = incoming_val
    return merged


def next_creator_id(rows):
    max_n = 0
    for row in rows:
        m = re.match(r"^[Cc](\d+)$", (row.get("creator_id") or "").strip())
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"C{max_n + 1:04d}"


def apply_normalized_fields(row):
    """Fill in canonical URL/username fields derived from raw input."""
    unknown_fields = [k for k, v in row.items() if str(v).strip().lower() == "unknown"]
    for k in unknown_fields:
        row[k] = ""
    if row.get("youtube_channel_url"):
        row["youtube_channel_url"] = normalize_youtube_url(row["youtube_channel_url"])
    if row.get("twitch_channel_url") or row.get("twitch_username"):
        username = normalize_twitch_username(row.get("twitch_username") or row.get("twitch_channel_url"))
        if username:
            row["twitch_username"] = username
            if not row.get("twitch_channel_url"):
                row["twitch_channel_url"] = twitch_canonical_url(username)
    for k in unknown_fields:
        if not row.get(k):
            row[k] = "Unknown"
    return row


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(_args):
    if not CSV_PATH.exists():
        print(f"FAIL: {CSV_PATH} not found")
        return 1
    header, rows = load_rows()
    ok = True
    if header != FIELDNAMES:
        ok = False
        missing = [c for c in FIELDNAMES if c not in header]
        extra = [c for c in header if c not in FIELDNAMES]
        print("FAIL: header does not match expected schema")
        if missing:
            print(f"  missing columns: {missing}")
        if extra:
            print(f"  unexpected columns: {extra}")
    else:
        print("Header OK: matches expected schema.")

    print(f"Row count: {len(rows)}")

    blank_names = [i for i, r in enumerate(rows) if not (r.get("creator_name") or "").strip()]
    if blank_names:
        ok = False
        print(f"FAIL: {len(blank_names)} row(s) missing creator_name (rows: {blank_names})")

    if ok:
        print("check: PASS")
        return 0
    print("check: FAIL")
    return 1


def cmd_stats(_args):
    _header, rows = load_rows()
    print(f"Total creators: {len(rows)}")
    if not rows:
        return 0

    for label, field in [
        ("Tier", "tier"),
        ("Status", "status"),
        ("Outreach status", "outreach_status"),
        ("Primary platform", "primary_platform"),
        ("High priority", "high_priority"),
    ]:
        counts = Counter((r.get(field) or "(blank)").strip() or "(blank)" for r in rows)
        print(f"\n{label}:")
        for value, count in counts.most_common():
            print(f"  {value}: {count}")

    return 0


def cmd_dedupe(_args):
    _header, rows = load_rows()
    if not rows:
        print("No rows to dedupe.")
        return 0

    merged_rows = []
    merge_count = 0
    for row in rows:
        row = apply_normalized_fields(dict(row))
        keys = identity_keys(row)
        idx = find_match_index(merged_rows, keys)
        if idx is None:
            merged_rows.append(row)
        else:
            merged_rows[idx] = merge_rows(merged_rows[idx], row)
            merge_count += 1

    save_rows(merged_rows)
    print(f"Dedupe complete. {len(rows)} rows -> {len(merged_rows)} rows ({merge_count} merged).")
    return 0


def cmd_upsert(args):
    if args.json_file:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    elif args.json:
        data = json.loads(args.json)
    else:
        print("upsert requires --json or --json-file")
        return 1

    if not isinstance(data, dict):
        print("upsert data must be a JSON object")
        return 1

    _header, rows = load_rows()

    candidate = blank_row()
    for k, v in data.items():
        if k in FIELDNAMES and v is not None:
            candidate[k] = str(v)
    candidate = apply_normalized_fields(candidate)

    keys = identity_keys(candidate)
    idx = find_match_index(rows, keys)

    if idx is None:
        if not candidate.get("creator_id"):
            candidate["creator_id"] = next_creator_id(rows)
        rows.append(candidate)
        print(f"Inserted new creator: {candidate['creator_id']} ({candidate.get('creator_name', '')})")
    else:
        rows[idx] = merge_rows(rows[idx], candidate)
        print(f"Merged into existing creator: {rows[idx]['creator_id']} ({rows[idx].get('creator_name', '')})")

    save_rows(rows)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Manage creators.csv for Club Sanguine creator research.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Validate creators.csv loads and matches the expected schema.")
    sub.add_parser("stats", help="Print summary counts from creators.csv.")
    sub.add_parser("dedupe", help="Merge likely-duplicate creator rows in creators.csv.")

    p_upsert = sub.add_parser("upsert", help="Insert or merge a single creator record.")
    p_upsert.add_argument("--json", help="JSON object string with creator fields.")
    p_upsert.add_argument("--json-file", help="Path to a JSON file with a creator object.")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "check": cmd_check,
        "stats": cmd_stats,
        "dedupe": cmd_dedupe,
        "upsert": cmd_upsert,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
