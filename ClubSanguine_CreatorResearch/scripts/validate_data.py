#!/usr/bin/env python3
"""
validate_data.py — read-only data quality report for creators.csv.

This script never modifies creators.csv. It only reads the file and
prints a human-readable report. Run it any time after Astra has added
or updated creator records.

Usage:
    python scripts/validate_data.py

Checks performed:
    - Malformed URLs (youtube/twitch/other social/contact/evidence links)
    - Malformed business_email values
    - Duplicate creators (same youtube_channel_id, twitch_username,
      profile URL, or normalized name)
    - Impossible scores (component scores out of range, fit_score not
      in 0-100, tier inconsistent with fit_score)
    - Missing creator names
    - High-priority creators with no evidence URLs
    - Creators marked "qualified" with zero relevant_games
    - Suspiciously incomplete rows (very few fields populated)
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CSV_PATH = PROJECT_DIR / "creators.csv"

URL_FIELDS = [
    "youtube_channel_url",
    "twitch_channel_url",
    "other_social_url",
    "contact_page",
    "evidence_url_1",
    "evidence_url_2",
    "evidence_url_3",
]

COMPONENT_WEIGHTS = {
    "direct_comparable_score": 30,
    "genre_fit_score": 20,
    "activity_score": 15,
    "size_score": 10,
    "multi_game_score": 10,
    "contact_score": 5,
    "personality_fit_score": 5,
    "indie_affinity_score": 5,
}

TIER_THRESHOLDS = [
    (85, "S"),
    (70, "A"),
    (55, "B"),
    (40, "C"),
]
LONG_TAIL = "Long Tail"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CORE_FIELDS_FOR_COMPLETENESS = [
    "creator_name",
    "primary_platform",
    "youtube_channel_url",
    "twitch_channel_url",
    "relevant_games",
    "evidence_url_1",
    "content_style",
    "last_active_date",
]


def tier_for_score(score):
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return LONG_TAIL


def is_truthy(value):
    return (value or "").strip().lower() in ("yes", "y", "true", "1")


def is_malformed_url(raw):
    """Return True if raw is non-empty but does not look like a valid URL."""
    raw = (raw or "").strip()
    if not raw:
        return False
    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlparse(candidate)
    if not parsed.netloc or "." not in parsed.netloc:
        return True
    if " " in raw:
        return True
    return False


def normalize_youtube_url(raw):
    raw = (raw or "").strip()
    if not raw:
        return ""
    candidate = raw if "://" in raw else "https://" + raw
    parsed = urlparse(candidate)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip('/')
    if not path.startswith('/channel/'):
        path = path.lower()
    return f"https://{host}{path}"


def normalize_twitch_username(raw):
    raw = (raw or "").strip()
    if not raw:
        return ""
    if "twitch.tv" in raw.lower():
        candidate = raw if "://" in raw else "https://" + raw
        path = urlparse(candidate).path.strip("/")
        username = path.split("/")[0] if path else ""
    else:
        username = raw.lstrip("@")
    return username.lower()


def normalize_name(raw):
    name = (raw or "").strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name.strip()


def identity_keys(row):
    yt_id = (row.get("youtube_channel_id") or "").strip()
    twitch_user = normalize_twitch_username(row.get("twitch_username") or row.get("twitch_channel_url") or "")
    profile_url = normalize_youtube_url(row.get("youtube_channel_url", ""))
    if not profile_url and row.get("twitch_channel_url"):
        profile_url = normalize_twitch_username(row.get("twitch_channel_url"))
    name_norm = normalize_name(row.get("creator_name", ""))
    return {
        "youtube_channel_id": yt_id,
        "twitch_username": twitch_user,
        "profile_url": profile_url,
        "name_norm": name_norm,
    }


def load_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Unknown is the brief's required missing-data marker, not a URL,
        # email address, shared identity, or evidence of completeness.
        return [{k: ("" if (v or "").strip().lower() == "unknown" else v)
                 for k, v in row.items()} for row in reader]


def check_malformed_urls(rows):
    issues = []
    for i, row in enumerate(rows):
        rid = row.get("creator_id") or f"row {i}"
        for field in URL_FIELDS:
            if is_malformed_url(row.get(field)):
                issues.append(f"[{rid}] {field}: malformed URL -> {row.get(field)!r}")
        email = (row.get("business_email") or "").strip()
        if email and not EMAIL_RE.match(email):
            issues.append(f"[{rid}] business_email: malformed -> {email!r}")
    return issues


def check_duplicates(rows):
    issues = []
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        keys = identity_keys(row)
        for level, value in keys.items():
            if value:
                groups[(level, value)].append(row.get("creator_id") or f"row {i}")
    seen_groups = set()
    for (level, value), ids in groups.items():
        unique_ids = sorted(set(ids))
        if len(unique_ids) > 1:
            key = (level, tuple(unique_ids))
            if key in seen_groups:
                continue
            seen_groups.add(key)
            issues.append(f"Possible duplicate ({level}={value!r}): {', '.join(unique_ids)}")
    return issues


def check_impossible_scores(rows):
    issues = []
    for i, row in enumerate(rows):
        rid = row.get("creator_id") or f"row {i}"
        total = 0.0
        any_component = False
        for field, max_points in COMPONENT_WEIGHTS.items():
            raw = (row.get(field) or "").strip()
            if not raw:
                continue
            any_component = True
            try:
                value = float(raw)
            except ValueError:
                issues.append(f"[{rid}] {field}: not numeric -> {raw!r}")
                continue
            if value < 0 or value > max_points:
                issues.append(f"[{rid}] {field}={value} out of range [0, {max_points}]")
            total += value

        fit_raw = (row.get("fit_score") or "").strip()
        if fit_raw:
            try:
                fit_value = float(fit_raw)
                if fit_value < 0 or fit_value > 100:
                    issues.append(f"[{rid}] fit_score={fit_value} out of range [0, 100]")
                else:
                    expected_tier = tier_for_score(fit_value)
                    actual_tier = (row.get("tier") or "").strip()
                    if actual_tier and actual_tier != expected_tier:
                        issues.append(
                            f"[{rid}] tier={actual_tier!r} inconsistent with fit_score={fit_value} "
                            f"(expected {expected_tier!r})"
                        )
            except ValueError:
                issues.append(f"[{rid}] fit_score: not numeric -> {fit_raw!r}")
        elif any_component:
            issues.append(f"[{rid}] has component scores but no fit_score (run score_creator.py recalc)")
    return issues


def check_missing_names(rows):
    issues = []
    for i, row in enumerate(rows):
        if not (row.get("creator_name") or "").strip():
            rid = row.get("creator_id") or f"row {i}"
            issues.append(f"[{rid}] missing creator_name")
    return issues


def check_high_priority_without_evidence(rows):
    issues = []
    for i, row in enumerate(rows):
        if is_truthy(row.get("high_priority")):
            evidence = [row.get("evidence_url_1"), row.get("evidence_url_2"), row.get("evidence_url_3")]
            if not any((e or "").strip() for e in evidence):
                rid = row.get("creator_id") or f"row {i}"
                issues.append(f"[{rid}] marked high_priority but has no evidence URLs")
    return issues


def check_qualified_zero_games(rows):
    issues = []
    for i, row in enumerate(rows):
        status = (row.get("status") or "").strip().lower()
        outreach = (row.get("outreach_status") or "").strip().lower()
        if "qualified" in status or "qualified" in outreach:
            games = (row.get("relevant_games") or "").strip()
            count = (row.get("direct_comparable_count") or "").strip()
            if not games or games == "0" or count == "0":
                rid = row.get("creator_id") or f"row {i}"
                issues.append(f"[{rid}] marked qualified but has no relevant_games")
    return issues


def check_incomplete_rows(rows, min_populated=3):
    issues = []
    for i, row in enumerate(rows):
        if not (row.get("creator_name") or "").strip():
            continue  # already reported by check_missing_names
        populated = sum(1 for f in CORE_FIELDS_FOR_COMPLETENESS if (row.get(f) or "").strip())
        if populated < min_populated:
            rid = row.get("creator_id") or f"row {i}"
            issues.append(
                f"[{rid}] suspiciously incomplete: only {populated}/{len(CORE_FIELDS_FOR_COMPLETENESS)} "
                f"core fields populated"
            )
    return issues


def print_section(title, issues):
    print(f"\n== {title} ({len(issues)}) ==")
    if not issues:
        print("  none")
        return
    for issue in issues:
        print(f"  - {issue}")


def main():
    if not CSV_PATH.exists():
        print(f"FAIL: {CSV_PATH} not found")
        return 1

    rows = load_rows()
    print(f"Loaded {len(rows)} creator row(s) from {CSV_PATH.name}")

    sections = [
        ("Malformed URLs / emails", check_malformed_urls(rows)),
        ("Duplicate creators", check_duplicates(rows)),
        ("Impossible scores", check_impossible_scores(rows)),
        ("Missing creator names", check_missing_names(rows)),
        ("High-priority creators without evidence URLs", check_high_priority_without_evidence(rows)),
        ("Qualified creators with zero relevant games", check_qualified_zero_games(rows)),
        ("Suspiciously incomplete rows", check_incomplete_rows(rows)),
    ]

    total_issues = 0
    for title, issues in sections:
        print_section(title, issues)
        total_issues += len(issues)

    print(f"\nTotal issues found: {total_issues}")
    print("(This is a read-only report. No data was modified.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
