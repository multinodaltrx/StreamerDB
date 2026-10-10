#!/usr/bin/env python3
"""
press_db.py — manage the press database (press/outlets.csv, press/journalists.csv).

No external dependencies. No network access. No LLM calls.

Commands:
    python scripts/press_db.py check
        Load both press CSVs and report header problems / row counts.

    python scripts/press_db.py stats
        Summary counts (type, tier, contact method) for outlets and journalists.

    python scripts/press_db.py dedupe
        Merge likely-duplicate rows in both files (existing data preserved).

    python scripts/press_db.py import <batch.json> "<label>"
        Upsert a reviewed research batch. The JSON is an object:
            {"outlets": [ {...}, ... ], "journalists": [ {...}, ... ]}
        Journalists name their outlets in "outlets" (semicolon-separated);
        names are resolved to outlet_ids after the outlets are upserted.
        Run scripts/score_press.py recalc afterwards.

Dedupe keys (strongest first):
    outlets      normalized site domain -> normalized name
    journalists  normalized author-page URL -> normalized social URL
                 -> normalized name + first outlet

As in creator_db.py: merges only fill empty / Unknown fields, Unknown is
never used as a key, and rows are never silently dropped.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from creator_db import normalize_generic_url, normalize_name

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PRESS_DIR = PROJECT_DIR / "press"
OUTLETS_PATH = PRESS_DIR / "outlets.csv"
JOURNALISTS_PATH = PRESS_DIR / "journalists.csv"

SCORE_FIELDS = [
    "comparable_score",   # 30  coverage of seed / related games
    "nextfest_score",     # 20  Next Fest / demo-roundup history
    "recency_score",      # 15  latest relevant article
    "focus_score",        # 15  indie / horror / quirky-sim focus (researcher judgement)
    "reach_score",        # 10  realistic reach for an indie game (researcher judgement)
    "contact_score",      # 10  public contact route
    "fit_score",
    "tier",
]

OUTLET_FIELDS = [
    "outlet_id",
    "name",
    "type",
    "url",
    "submission_url",
    "public_email",
    "social_url",
    "public_contact_method",
    "press_policy_notes",
    "audience_note",
    "comparable_coverage",
    "evidence_url_1",
    "evidence_url_2",
    "evidence_url_3",
    "nextfest_coverage",
    "nextfest_url",
    "last_relevant_article_date",
    "region_language",
] + SCORE_FIELDS + [
    "notes",
    "date_discovered",
    "last_verified",
    "source_query",
]

JOURNALIST_FIELDS = [
    "journalist_id",
    "name",
    "outlets",
    "outlet_ids",
    "role",
    "beat",
    "author_page_url",
    "public_email",
    "social_url",
    "public_contact_method",
    "contact_preference",
    "games_covered",
    "evidence_url_1",
    "evidence_url_2",
    "evidence_url_3",
    "nextfest_coverage",
    "nextfest_url",
    "last_article_date",
    "region_language",
] + SCORE_FIELDS + [
    "notes",
    "date_discovered",
    "last_verified",
    "source_query",
]

OUTLET_TYPES = [
    "Indie site/blog",
    "Major outlet",
    "Newsletter",
    "Podcast",
    "YouTube press",
    "Roundup/curator",
]

TABLES = {
    "outlets": (OUTLETS_PATH, OUTLET_FIELDS, "outlet_id", "O"),
    "journalists": (JOURNALISTS_PATH, JOURNALIST_FIELDS, "journalist_id", "J"),
}


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load(table):
    path, fields, _id, _p = TABLES[table]
    if not path.exists():
        return list(fields), []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], [dict(r) for r in reader]


def save(table, rows):
    path, fields, _id, _p = TABLES[table]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def _known(v):
    v = (v or "").strip()
    return "" if v.lower() == "unknown" else v


def domain_of(url):
    url = _known(url)
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = parsed.netloc.lower()
    return host[4:] if host.startswith("www.") else host


# Platforms that host many unrelated outlets: key on the full URL, not the domain.
SHARED_HOSTS = {
    "youtube.com", "m.youtube.com", "substack.com", "podcasts.apple.com", "open.spotify.com",
    "x.com", "twitter.com", "bsky.app", "linktr.ee", "medium.com", "patreon.com", "buttondown.com",
    "buttondown.email", "beehiiv.com", "podbean.com", "buzzsprout.com", "anchor.fm", "creators.spotify.com",
    "soundcloud.com", "store.steampowered.com", "steamcommunity.com", "twitch.tv", "pod.link", "podcasters.spotify.com",
    "rss.com", "audioboom.com", "libsyn.com", "simplecast.com", "transistor.fm", "ko-fi.com", "carrd.co", "tumblr.com",
}

# List-valued fields: merging unions them instead of keeping only the first value.
LIST_FIELDS = {"outlets", "games_covered", "comparable_coverage"}


def site_key(url):
    host = domain_of(url)
    if host in SHARED_HOSTS:
        return normalize_generic_url(_known(url))
    return host


def identity_keys(table, row):
    if table == "outlets":
        return [site_key(row.get("url")), normalize_name(_known(row.get("name")))]
    first_outlet = normalize_name(_known(row.get("outlets")).split(";")[0])
    name = normalize_name(_known(row.get("name")))
    return [
        normalize_generic_url(_known(row.get("author_page_url"))),
        normalize_generic_url(_known(row.get("social_url"))),
        f"{name}|{first_outlet}" if name else "",
    ]


def names_compatible(a, b):
    """Co-hosts often share a show page / social account, so a URL match only
    counts for journalists whose names also agree (same first and last token)."""
    ta, tb = normalize_name(_known(a)).split(), normalize_name(_known(b)).split()
    if not ta or not tb:
        return True
    return ta[0] == tb[0] and ta[-1] == tb[-1]


def find_match(table, rows, keys, name=""):
    for level, value in enumerate(keys):
        if not value:
            continue
        for i, row in enumerate(rows):
            if identity_keys(table, row)[level] != value:
                continue
            if table == "journalists" and not names_compatible(name, row.get("name")):
                continue
            return i
    return None


def merge(existing, incoming, fields):
    merged = dict(existing)
    for k in fields:
        old = (existing.get(k) or "").strip()
        new = (incoming.get(k) or "").strip()
        if k == "notes" and _known(old) and _known(new):
            if new not in old:  # keep every batch's notes (e.g. "Other socials: ...") with provenance
                merged[k] = f"{old} | {new}"
        elif k in LIST_FIELDS and _known(old) and _known(new):
            items = [x.strip() for x in f"{old};{new}".split(";") if x.strip()]
            merged[k] = "; ".join(dict.fromkeys(items))
        elif (not old or old.lower() == "unknown") and new and new.lower() != "unknown":
            merged[k] = new
    return merged


def next_id(rows, id_field, prefix):
    n = 0
    for r in rows:
        m = re.match(rf"^{prefix}(\d+)$", (r.get(id_field) or "").strip())
        if m:
            n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1:04d}"


def clean(value):
    if value is None:
        return ""
    if isinstance(value, list):
        value = "; ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def upsert(table, rows, data, label):
    _path, fields, id_field, prefix = TABLES[table]
    cand = {k: clean(data.get(k)) for k in fields}
    for k in fields:
        if k not in SCORE_FIELDS and not cand[k]:
            cand[k] = "Unknown"
    today = date.today().isoformat()
    cand["date_discovered"] = cand["date_discovered"] if _known(cand["date_discovered"]) else today
    cand["last_verified"] = cand["last_verified"] if _known(cand["last_verified"]) else today
    if label:
        note = _known(cand["notes"])
        cand["notes"] = f"{label}. {note}".strip() if note else f"{label}."
    idx = find_match(table, rows, identity_keys(table, cand), cand.get("name"))
    if idx is None:
        cand[id_field] = next_id(rows, id_field, prefix)
        rows.append(cand)
        return "inserted", cand
    rows[idx] = merge(rows[idx], cand, fields)
    return "merged", rows[idx]


def resolve_outlet_ids(journalists, outlets):
    by_name = {normalize_name(o["name"]): o["outlet_id"] for o in outlets}
    by_domain = {site_key(o["url"]): o["outlet_id"] for o in outlets if site_key(o["url"])}
    unresolved = set()
    for j in journalists:
        ids = []
        for name in _known(j.get("outlets")).split(";"):
            name = name.strip()
            if not name:
                continue
            oid = by_name.get(normalize_name(name)) or by_domain.get(site_key(name))
            if oid:
                ids.append(oid)
            else:
                unresolved.add(name)
        j["outlet_ids"] = "; ".join(dict.fromkeys(ids)) or "Unknown"
    return unresolved


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(_args):
    ok = True
    for table, (path, fields, id_field, _p) in TABLES.items():
        if not path.exists():
            print(f"{table}: {path.name} missing")
            ok = False
            continue
        header, rows = load(table)
        if header != fields:
            ok = False
            print(f"{table}: FAIL header mismatch; missing={[c for c in fields if c not in header]} "
                  f"extra={[c for c in header if c not in fields]}")
        else:
            print(f"{table}: header OK, {len(rows)} rows")
        ids = Counter(r.get(id_field) for r in rows)
        dup = [k for k, v in ids.items() if v > 1]
        if dup:
            ok = False
            print(f"{table}: FAIL duplicate ids {dup}")
    print("check: PASS" if ok else "check: FAIL")
    return 0 if ok else 1


def cmd_stats(_args):
    for table in TABLES:
        _h, rows = load(table)
        print(f"\n== {table}: {len(rows)} ==")
        group_fields = [("Type", "type")] if table == "outlets" else [("Role", "role")]
        group_fields += [("Tier", "tier"), ("Contact", "public_contact_method"),
                         ("Next Fest coverage", "nextfest_coverage")]
        for label, field in group_fields:
            counts = Counter((r.get(field) or "(blank)").strip() for r in rows)
            print(f"  {label}: " + " · ".join(f"{k} {v}" for k, v in counts.most_common()))
    return 0


def cmd_dedupe(_args):
    for table, (_path, fields, _id, _p) in TABLES.items():
        _h, rows = load(table)
        out = []
        merged = 0
        for row in rows:
            idx = find_match(table, out, identity_keys(table, row), row.get("name"))
            if idx is None:
                out.append(row)
            else:
                out[idx] = merge(out[idx], row, fields)
                merged += 1
        save(table, out)
        print(f"{table}: {len(rows)} -> {len(out)} rows ({merged} merged)")
    return 0


def cmd_import(args):
    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    _h, outlets = load("outlets")
    _h, journalists = load("journalists")
    report = Counter()
    for item in data.get("outlets", []):
        status, row = upsert("outlets", outlets, item, args.label)
        report[f"outlets {status}"] += 1
        if status == "merged":
            print(f"  merged outlet into {row['outlet_id']} ({row['name']})")
    for item in data.get("journalists", []):
        status, row = upsert("journalists", journalists, item, args.label)
        report[f"journalists {status}"] += 1
        if status == "merged":
            print(f"  merged journalist into {row['journalist_id']} ({row['name']})")
    unresolved = resolve_outlet_ids(journalists, outlets)
    save("outlets", outlets)
    save("journalists", journalists)
    for k, v in sorted(report.items()):
        print(f"{k}: {v}")
    if unresolved:
        print(f"WARN outlet names not found in outlets.csv: {sorted(unresolved)}")
    print("Now run: python scripts/score_press.py recalc")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manage the Club Sanguine press database.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("stats")
    sub.add_parser("dedupe")
    p_imp = sub.add_parser("import")
    p_imp.add_argument("json_file")
    p_imp.add_argument("label", nargs="?", default="")
    args = parser.parse_args(argv)
    return {"check": cmd_check, "stats": cmd_stats, "dedupe": cmd_dedupe,
            "import": cmd_import}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
