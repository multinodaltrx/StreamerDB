#!/usr/bin/env python3
"""
validate_press.py — read-only data-quality report for the press database.

Checks: header schema, malformed URLs / emails / dates, rows without
evidence, unknown outlet types, journalist outlet_ids that do not resolve,
likely duplicates, and fit_score / tier that disagree with score_press.py.

    python scripts/validate_press.py
"""

import copy
import re
import sys

from press_db import TABLES, OUTLET_TYPES, load, identity_keys, names_compatible
from score_press import load_seed_tiers, score_row

URL_FIELDS = ["url", "submission_url", "social_url", "author_page_url", "nextfest_url",
              "evidence_url_1", "evidence_url_2", "evidence_url_3"]
DATE_FIELDS = ["last_relevant_article_date", "last_article_date", "date_discovered", "last_verified"]
EMAIL_RE = re.compile(r"^[^@\s;,]+@[^@\s;,]+\.[a-z]{2,}$", re.I)


def known(v):
    v = (v or "").strip()
    return "" if v.lower() == "unknown" else v


def main():
    issues = []
    seed_tiers = load_seed_tiers()
    _h, outlets = load("outlets")
    outlet_ids = {o["outlet_id"] for o in outlets}

    for table, (path, fields, id_field, _p) in TABLES.items():
        header, rows = load(table)
        if rows and header != fields:
            issues.append(f"{table}: header does not match schema")
        seen = {}
        for r in rows:
            rid = f"{table}/{r.get(id_field)} ({r.get('name')})"
            for f in URL_FIELDS:
                v = known(r.get(f))
                if v and not re.match(r"^https?://[^\s]+\.[^\s]+", v):
                    issues.append(f"{rid}: malformed URL in {f}: {v!r}")
            for e in known(r.get("public_email")).split(";"):
                e = e.strip()
                if e and not EMAIL_RE.match(e):
                    issues.append(f"{rid}: malformed email {e!r}")
            for f in DATE_FIELDS:
                v = known(r.get(f))
                if v and not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", v):
                    issues.append(f"{rid}: {f} not ISO date: {v!r}")
            if not known(r.get("evidence_url_1")):
                issues.append(f"{rid}: no evidence URL")
            if table == "outlets" and r.get("type") not in OUTLET_TYPES:
                issues.append(f"{rid}: unknown type {r.get('type')!r}")
            if table == "journalists":
                for oid in known(r.get("outlet_ids")).split(";"):
                    if oid.strip() and oid.strip() not in outlet_ids:
                        issues.append(f"{rid}: outlet_id {oid.strip()} not in outlets.csv")
            expected = score_row(copy.deepcopy(r), table, seed_tiers)
            if expected["fit_score"] != r.get("fit_score") or expected["tier"] != r.get("tier"):
                issues.append(f"{rid}: score/tier stale (run score_press.py recalc)")
            for key in dict.fromkeys(identity_keys(table, r)):
                other = seen.get(key)
                if key and other and (table == "outlets" or names_compatible(r.get("name"), other[1])):
                    issues.append(f"{rid}: likely duplicate of {other[0]} (key {key})")
                elif key and not other:
                    seen[key] = (rid, r.get("name"))

    for i in issues:
        print(f"  {i}")
    print(f"Total issues found: {len(issues)}")
    print("(This is a read-only report. No data was modified.)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
