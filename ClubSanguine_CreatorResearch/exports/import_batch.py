"""Import reviewed batch candidates into creators.csv (upsert; never deletes or downgrades data).

Usage:
    python exports/import_batch.py import exports/batch_002_candidates.json BATCH_LABEL
    python exports/import_batch.py enrich      # fill Unknown channel IDs / activity on existing rows

Each candidate in the JSON is a reviewed record:
    channel_id, name, profile, subs, games[], evidence[], activity_days, query, notes,
    style, email, contact, social, twitch, genre, personality, indie
Objective components (direct comparable, activity, size, multi-game, contact) are
derived here by a fixed rubric; genre/personality/indie are the reviewer's judgement.
Final fit_score/tier arithmetic stays with scripts/score_creator.py.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import creator_db as db  # noqa: E402
import yt_harvest as yt  # noqa: E402

TODAY = date.today().isoformat()
TIER_ORDER = {1: 0, 2: 1, 3: 2, "related": 3}


SOCIAL_HOSTS = ("x.com", "twitter.com", "bsky.app", "instagram.com", "tiktok.com", "facebook.com", "threads.net", "threads.com")
SKIP_HOSTS = ("patreon.com", "ko-fi.com", "throne.com", "streamelements.com", "streamlabs.com", "amazon.", "amzn.",
              "steamcommunity.com", "store.steampowered.com", "youtube.com", "youtu.be", "paypal.", "merch", "spotify.com",
              "soundcloud.com", "teespring", "fourthwall", "gofundme", "tipeeestream", "cash.app", "venmo")
CONTACT_HOSTS = ("discord.gg", "discord.com", "linktr.ee", "beacons.ai", "carrd.co", "linkin.bio", "solo.to", "bio.link")


def contact_fields(channel_id, desc_emails=()):
    """Public contact routes from the cached YouTube About panel. Never invents anything."""
    path = ROOT / "exports" / "harvest" / "about" / f"{channel_id}.json"
    about = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    links = [l["url"].strip() for l in about.get("links", [])]
    emails = list(desc_emails) + [e for e in about.get("emails", []) if e not in desc_emails]
    twitch = next((l for l in links if "twitch.tv/" in l.lower()), None)
    social = next((l for l in links if any(h in l.lower() for h in SOCIAL_HOSTS)), None)
    page = next((l for l in links if any(h in l.lower() for h in CONTACT_HOSTS)), None) or next(
        (l for l in links if "twitch.tv/" not in l.lower() and not any(h in l.lower() for h in SOCIAL_HOSTS + SKIP_HOSTS)), None)
    fields = {}
    if emails:
        fields["business_email"] = emails[0]
        method, score = "Public business email", 5
    elif about.get("email_gated"):
        method, score = "YouTube About business email (sign-in required to view)", 3
    elif page:
        method, score = "Public community/contact page", 2
    elif social or twitch:
        method, score = "Public social profile", 1
    else:
        method, score = "Unknown", 0
    full = lambda u: u if u.startswith("http") else "https://" + u
    if twitch:
        fields["twitch_channel_url"] = full(twitch)
    if social:
        fields["other_social_url"] = full(social)
    if page:
        fields["contact_page"] = full(page)
    if about.get("country"):
        fields["country"] = about["country"]
    fields["public_contact_method"] = method
    return fields, score, bool(about)


def twitch_metrics(username):
    path = ROOT / "exports" / "harvest" / "twitch" / f"{username}.json"
    if not path.exists():
        return {}
    t = json.loads(path.read_text(encoding="utf-8"))
    return {"twitch_avg_viewers": t["avg_viewers"]} if t.get("avg_viewers") else {}


def tier_counts(games):
    tiers = [yt.GAME_TIERS.get(g, "related") for g in games]
    return {t: tiers.count(t) for t in (1, 2, 3, "related")}


def rubric(c):
    t = tier_counts(c["games"])
    if t[1] >= 3:
        direct = 30
    elif t[1] == 2:
        direct = 24
    elif t[1] == 1:
        direct = 18
    elif t[2] >= 2:
        direct = 14
    elif t[2] == 1:
        direct = 10
    elif t["related"]:
        direct = 10
    elif t[3] >= 2:
        direct = 8
    else:
        direct = 5

    days = c.get("activity_days")
    activity = 0 if days is None else 15 if days <= 30 else 12 if days <= 90 else 6 if days <= 180 else 2

    subs = c.get("subs")
    if subs is None:
        size = 5
    elif subs < 1_000:
        size = 4
    elif subs <= 500_000:
        size = 10
    elif subs <= 1_000_000:
        size = 5
    else:
        size = 3

    n_games = len(c["games"])
    multi = {0: 0, 1: 0, 2: 4, 3: 6, 4: 8}.get(n_games, 10)
    contact = max(5 if c.get("email") else 0, contact_fields(c["channel_id"], [c["email"]] if c.get("email") else [])[1])

    scores = {
        "direct_comparable_score": direct,
        "genre_fit_score": c["genre"],
        "activity_score": activity,
        "size_score": size,
        "multi_game_score": multi,
        "contact_score": contact,
        "personality_fit_score": c.get("personality", 4),
        "indie_affinity_score": c.get("indie", 4),
    }
    high = (t[1] >= 2 and days is not None and days <= 90 and subs is not None
            and 1_000 <= subs <= 500_000 and contact >= 2 and scores["indie_affinity_score"] >= 4)
    return scores, t, high


def build_row(c, label):
    scores, t, high = rubric(c)
    games = sorted(c["games"], key=lambda g: TIER_ORDER[yt.GAME_TIERS.get(g, "related")])
    days = c.get("activity_days")
    row = {k: "Unknown" for k in db.FIELDNAMES}
    row.update(
        creator_name=c["name"],
        primary_platform="YouTube",
        youtube_channel_url=c.get("profile") or f"https://www.youtube.com/channel/{c['channel_id']}",
        youtube_channel_id=c["channel_id"],
        youtube_subscribers=str(c["subs"]) if c.get("subs") is not None else "Unknown",
        twitch_channel_url=c.get("twitch") or "Unknown",
        other_social_url=c.get("social") or "Unknown",
        language="English",
        last_active_date=(date.today() - timedelta(days=days)).isoformat() if days is not None else "Unknown",
        relevant_games="; ".join(games),
        direct_comparable_count=str(t[1]),
        content_style=c.get("style") or "Gameplay commentary / playthroughs",
        business_email=c.get("email") or "Unknown",
        contact_page=c.get("contact") or "Unknown",
        public_contact_method=("Public business email" if c.get("email") else
                               "Public community/contact page" if c.get("contact") else
                               "Public social profile" if c.get("social") else "Unknown"),
        high_priority="Yes" if high else "No",
        status="candidate",
        outreach_status="",
        notes=f"{label}. {c.get('notes', '')}".strip(),
        date_discovered=TODAY,
        last_verified=TODAY,
        source_query=c.get("query", "Unknown"),
        fit_score="",
        tier="",
    )
    for i, url in enumerate(c["evidence"][:3], 1):
        row[f"evidence_url_{i}"] = url
    row.update({k: str(v) for k, v in scores.items()})
    fields, _, _ = contact_fields(c["channel_id"], [c["email"]] if c.get("email") else [])
    row.update({k: v for k, v in fields.items() if v})
    row = db.apply_normalized_fields(row)
    if row.get("twitch_username") not in ("", "Unknown"):
        row.update(twitch_metrics(row["twitch_username"]))
    return row


def cmd_import(path, label):
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    header, rows = db.load_rows()
    assert header == db.FIELDNAMES, "creators.csv header drifted from schema"
    added = merged = 0
    for c in items:
        row = build_row(c, label)
        idx = db.find_match_index(rows, db.identity_keys(row))
        if idx is None:
            row["creator_id"] = db.next_creator_id(rows)
            rows.append(row)
            added += 1
        else:
            rows[idx] = db.merge_rows(rows[idx], row)
            merged += 1
    db.save_rows(rows)
    print(f"{label}: {added} added, {merged} merged into existing; total rows {len(rows)}")


def cmd_enrich():
    header, rows = db.load_rows()
    filled = 0
    for row in rows:
        url = row.get("youtube_channel_url", "")
        if row.get("youtube_channel_id", "Unknown") not in ("", "Unknown") or "/@" not in url:
            continue
        handle = "@" + url.split("/@", 1)[1].strip("/")
        try:
            ch, _ = yt.do_channel(handle)
        except Exception as exc:
            print(f"FAIL {row['creator_id']} {handle}: {exc}")
            continue
        update = {"youtube_channel_id": ch["channel_id"]}
        if ch.get("subscribers"):
            update["youtube_subscribers"] = str(ch["subscribers"])
        if ch.get("latest_upload_date"):
            update["last_active_date"] = ch["latest_upload_date"]
        before = dict(row)
        row.update(db.merge_rows(row, update))
        if row != before:
            filled += 1
            print(f"{row['creator_id']} {row['creator_name']}: id={ch['channel_id']} latest={ch.get('latest_upload_days')}d")
    db.save_rows(rows)
    print(f"Enriched {filled} row(s).")


def days_since(iso):
    try:
        return (date.today() - date.fromisoformat(iso)).days
    except ValueError:
        return None


def cmd_enrich_contacts():
    """Fill Unknown contact/Twitch/country fields from cached About + TwitchTracker data; upgrade contact score only."""
    header, rows = db.load_rows()
    stats = {"rows": len(rows), "upgraded": 0, "no_about": 0}
    for row in rows:
        desc = [row["business_email"]] if row.get("business_email") not in ("", "Unknown") else []
        fields, score, had_about = contact_fields(row["youtube_channel_id"], desc)
        stats["no_about"] += not had_about
        method = fields.pop("public_contact_method")
        merged = db.merge_rows(row, fields)
        merged = db.apply_normalized_fields(merged)
        if merged.get("twitch_username") not in ("", "Unknown"):
            merged = db.merge_rows(merged, twitch_metrics(merged["twitch_username"]))
        old = int(float(row.get("contact_score") or 0))
        if score > old:
            merged["contact_score"] = str(score)
            merged["public_contact_method"] = method
            stats["upgraded"] += 1
        try:
            subs = int(merged["youtube_subscribers"])
        except ValueError:
            subs = None
        days = days_since(merged.get("last_active_date", ""))
        hp = (int(merged.get("direct_comparable_count") or 0) >= 2 and days is not None and days <= 90 and subs
              and 1_000 <= subs <= 500_000 and int(merged["contact_score"]) >= 2 and int(merged["indie_affinity_score"]) >= 4)
        merged["high_priority"] = "Yes" if hp else "No"
        row.clear()
        row.update(merged)
    db.save_rows(rows)
    print(stats)


if __name__ == "__main__":
    if sys.argv[1] == "import":
        cmd_import(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "enrich":
        cmd_enrich()
    elif sys.argv[1] == "enrich-contacts":
        cmd_enrich_contacts()
