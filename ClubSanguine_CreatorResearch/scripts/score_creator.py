#!/usr/bin/env python3
"""
score_creator.py — deterministic fit-score calculator for creators.csv.

This script does NOT use an LLM and makes no judgment calls of its own.
It assumes a research agent (Astra) has already supplied the component
score columns for each creator, and simply clamps, sums, and maps those
to a fit_score (0-100) and a tier label.

Component weights (max points):
    direct_comparable_score   30   Direct comparable coverage
    genre_fit_score           20   Genre fit
    activity_score            15   Recent activity
    size_score                10   Audience-size suitability
    multi_game_score          10   Multiple comparable games covered
    contact_score              5   Contactability
    personality_fit_score      5   Personality / streamer suitability
    indie_affinity_score       5   Indie-game affinity
    ------------------------------
    fit_score                100   Sum of the above (clamped)

Tier mapping:
    85-100 = S
    70-84  = A
    55-69  = B
    40-54  = C
    < 40   = Long Tail

Commands:
    python scripts/score_creator.py recalc
        Recalculate fit_score and tier for every row in creators.csv
        and write the results back to the file.

    python scripts/score_creator.py score --json '{"direct_comparable_score": 25, ...}'
        Compute (without writing anything) the fit_score/tier for a
        single set of component scores. Useful for testing.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CSV_PATH = PROJECT_DIR / "creators.csv"

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


def tier_for_score(score):
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return LONG_TAIL


def parse_component(raw):
    if raw is None or str(raw).strip() == "":
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def compute_fit_score(components):
    """components: dict of field -> raw value. Returns (fit_score, tier, warnings)."""
    total = 0.0
    warnings = []
    for field, max_points in COMPONENT_WEIGHTS.items():
        value = parse_component(components.get(field))
        if value < 0:
            warnings.append(f"{field}={value} below 0, clamped to 0")
            value = 0
        if value > max_points:
            warnings.append(f"{field}={value} exceeds max {max_points}, clamped")
            value = max_points
        total += value
    total = round(total, 2)
    return total, tier_for_score(total), warnings


def cmd_recalc(_args):
    if not CSV_PATH.exists():
        print(f"FAIL: {CSV_PATH} not found")
        return 1

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = [dict(r) for r in reader]

    changed = 0
    for row in rows:
        fit_score, tier, warnings = compute_fit_score(row)
        old_fit = (row.get("fit_score") or "").strip()
        old_tier = (row.get("tier") or "").strip()
        row["fit_score"] = str(fit_score)
        row["tier"] = tier
        if warnings:
            name = row.get("creator_name", "(unnamed)")
            for w in warnings:
                print(f"  WARN [{name}]: {w}")
        if old_fit != row["fit_score"] or old_tier != row["tier"]:
            changed += 1

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Recalculated {len(rows)} row(s); {changed} row(s) changed.")
    return 0


def cmd_score(args):
    if args.json_file:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    elif args.json:
        data = json.loads(args.json)
    else:
        print("score requires --json or --json-file")
        return 1

    fit_score, tier, warnings = compute_fit_score(data)
    for w in warnings:
        print(f"WARN: {w}")
    print(json.dumps({"fit_score": fit_score, "tier": tier}, indent=2))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Deterministic creator fit-score calculator.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("recalc", help="Recalculate fit_score/tier for every row in creators.csv.")

    p_score = sub.add_parser("score", help="Compute fit_score/tier for a single set of component scores.")
    p_score.add_argument("--json", help="JSON object string with component score fields.")
    p_score.add_argument("--json-file", help="Path to a JSON file with component score fields.")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "recalc": cmd_recalc,
        "score": cmd_score,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
