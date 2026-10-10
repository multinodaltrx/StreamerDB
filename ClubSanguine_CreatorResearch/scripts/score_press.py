#!/usr/bin/env python3
"""
score_press.py — deterministic fit-score calculator for the press database.

Four components are derived from recorded fields by fixed rules; two are
researcher judgements that this script only clamps. Nothing is guessed.

    comparable_score  30  from the games list (comparable_coverage / games_covered):
                          Tier 1 seed 12 each, Tier 2 seed 8, Tier 3 seed 5,
                          other listed related game 4; capped at 30
    nextfest_score    20  nextfest_coverage: Yes 20 · Demo coverage 12 · else 0
    recency_score     15  latest relevant article vs last_verified:
                          <=183 days 15 · <=365 10 · <=730 5 · else / Unknown 0
    focus_score       15  researcher judgement (indie / horror / quirky-sim focus)
    reach_score       10  researcher judgement (realistic reach for an indie game)
    contact_score     10  public email 10 · submission form 8 · social profile 5 · else 0

Tiers match score_creator.py: S >=85, A >=70, B >=55, C >=40, else Long Tail.
public_contact_method is rewritten from the same contact rule.

Commands:
    python scripts/score_press.py recalc
"""

import argparse
import re
import sys
from datetime import date

from press_db import PROJECT_DIR, load, save, TABLES
from score_creator import tier_for_score, parse_component

SEED_PATH = PROJECT_DIR / "seed_games.txt"
TIER_POINTS = {1: 12, 2: 8, 3: 5}
RELATED_POINTS = 4


def norm_game(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def load_seed_tiers():
    tiers, current = {}, None
    for line in SEED_PATH.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^TIER (\d)", line.strip())
        if m:
            current = int(m.group(1))
        elif line.startswith("- ") and current:
            tiers[norm_game(line[2:])] = current
    return tiers


def known(v):
    v = (v or "").strip()
    return "" if v.lower() == "unknown" else v


def comparable_points(games, seed_tiers):
    total = 0
    seen = set()
    for g in known(games).split(";"):
        key = norm_game(g)
        if not key or key in seen:
            continue
        seen.add(key)
        tier = seed_tiers.get(key)
        total += TIER_POINTS[tier] if tier else RELATED_POINTS
    return min(total, 30)


def parse_partial_date(v):
    """YYYY-MM-DD, or YYYY-MM / YYYY read conservatively as the first day of that month / year."""
    v = known(v)[:10]
    if len(v) == 4:
        v += "-01-01"
    elif len(v) == 7:
        v += "-01"
    return date.fromisoformat(v)


def recency_points(last, verified):
    try:
        days = (parse_partial_date(verified) - parse_partial_date(last)).days
    except ValueError:
        return 0
    if days <= 183:
        return 15
    if days <= 365:
        return 10
    if days <= 730:
        return 5
    return 0


def contact(row):
    if known(row.get("public_email")):
        return 10, "Public email"
    if known(row.get("submission_url")):
        return 8, "Submission form"
    if known(row.get("social_url")):
        return 5, "Social profile"
    return 0, "Unknown"


def clamp(raw, cap):
    return max(0.0, min(float(cap), parse_component(raw)))


def score_row(row, table, seed_tiers):
    games = row.get("comparable_coverage") if table == "outlets" else row.get("games_covered")
    last = row.get("last_relevant_article_date") if table == "outlets" else row.get("last_article_date")
    nf = known(row.get("nextfest_coverage")).lower()
    c_points, method = contact(row)
    comps = {
        "comparable_score": comparable_points(games, seed_tiers),
        "nextfest_score": 20 if nf == "yes" else 12 if nf == "demo coverage" else 0,
        "recency_score": recency_points(last, row.get("last_verified")),
        "focus_score": clamp(row.get("focus_score"), 15),
        "reach_score": clamp(row.get("reach_score"), 10),
        "contact_score": c_points,
    }
    for k, v in comps.items():
        row[k] = f"{v:g}"
    total = round(sum(float(v) for v in comps.values()), 2)
    row["fit_score"] = f"{total:g}"
    row["tier"] = tier_for_score(total)
    row["public_contact_method"] = method
    return row


def cmd_recalc(_args):
    seed_tiers = load_seed_tiers()
    for table in TABLES:
        _h, rows = load(table)
        rows = [score_row(r, table, seed_tiers) for r in rows]
        save(table, rows)
        print(f"{table}: recalculated {len(rows)} row(s)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic press fit-score calculator.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("recalc")
    args = parser.parse_args(argv)
    return {"recalc": cmd_recalc}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
