#!/usr/bin/env python3
"""
outreach_app.py — local outreach dashboard for creators and press.

    python tools/outreach_app.py            # opens http://127.0.0.1:8765
    python tools/outreach_app.py --no-browser --port 8800

Standard library only. Binds to 127.0.0.1 so contact data never leaves this
machine. Serves the React UI from dashboard/dist (committed, so Node is only
needed to change the UI: cd dashboard && npm install && npm run build) plus a
small JSON API (/api/data, /api/log, /api/reveal). It NEVER sends anything: it lets the owner filter contacts, copy
emails / links / filled-in message templates, and records what the owner did.

Reads (never writes):  creators.csv, press/outlets.csv, press/journalists.csv,
                       outreach/config.json, outreach/templates/*.txt,
                       exports/discord_invites.csv, exports/evidence_titles.csv
                       (both from tools/check_outreach_links.py)
Appends to:            outreach/outreach_log.csv       (one row per button press)
                       outreach/revealed_contacts.csv  (emails the owner revealed
                                                        by hand from YouTube's gate)

A contact's status is the latest non-"note" action in the log; "undo" rows
cancel the action before them, so history is never rewritten.
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from score_press import load_seed_tiers, norm_game  # noqa: E402

OUTREACH_DIR = PROJECT_DIR / "outreach"
LOG_PATH = OUTREACH_DIR / "outreach_log.csv"
REVEALED_PATH = OUTREACH_DIR / "revealed_contacts.csv"
CONFIG_PATH = OUTREACH_DIR / "config.json"
TEMPLATE_DIR = OUTREACH_DIR / "templates"
DIST_DIR = PROJECT_DIR / "dashboard" / "dist"   # built React app (cd dashboard && npm run build)
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
        ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".woff2": "font/woff2"}

LOG_FIELDS = ["timestamp", "contact_id", "kind", "name", "action", "channel", "template", "note", "follow_up_on"]
REVEALED_FIELDS = ["contact_id", "email", "revealed_on"]
ACTIONS = {"queued", "contacted", "followed_up", "replied", "interested", "key_sent",
           "covered", "declined", "skip", "note", "undo"}
FOLLOW_UP_ACTIONS = {"contacted", "followed_up"}


def known(v):
    v = (v or "").strip()
    return "" if v.lower() == "unknown" else v


def read_csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def append_csv(path, fields, row):
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def split_games(s):
    return [g.strip() for g in known(s).split(";") if g.strip()]


def lead_game(games, seed_tiers):
    """The most relevant game to mention in a message: lowest seed tier first."""
    if not games:
        return ""
    return min(games, key=lambda g: seed_tiers.get(norm_game(g), 9))


def to_int(v):
    try:
        return int(float(known(v)))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

PLATFORMS = [  # (domain fragment, label) - first match wins
    ("discord.gg", "Discord"), ("discord.com", "Discord"), ("discordapp.com", "Discord"),
    ("bsky.app", "Bluesky"), ("x.com", "X"), ("twitter.com", "X"), ("instagram.com", "Instagram"),
    ("tiktok.com", "TikTok"), ("threads.net", "Threads"), ("twitch.tv", "Twitch"), ("kick.com", "Kick"),
    ("youtube.com", "YouTube"), ("facebook.com", "Facebook"), ("linkedin.com", "LinkedIn"),
    ("linktr.ee", "Linktree"), ("mastodon", "Mastodon"), ("reddit.com", "Reddit"), ("patreon.com", "Patreon"),
    ("ko-fi.com", "Ko-fi"), ("carrd.co", "Carrd"), ("substack.com", "Substack"),
]
DM_PLATFORMS = ("Discord", "X", "Bluesky", "Instagram", "TikTok", "Threads", "Mastodon", "LinkedIn", "Facebook")


def platform_of(url, fallback="Website"):
    u = url.lower()
    if u.startswith("mailto:"):
        return "Email"
    host = u.split("://", 1)[-1].split("/", 1)[0]
    for frag, label in PLATFORMS:
        if frag in host:
            return label
    return fallback


def norm_url(u):
    return u.lower().split("://", 1)[-1].removeprefix("www.").rstrip("/")


def add_link(links, label, url):
    """Append [label, url] unless the same URL is already listed."""
    url = (url or "").strip()
    if not url or url.lower() == "unknown":
        return
    if not url.startswith(("http", "mailto:")):
        url = "https://" + url
    if any(norm_url(u) == norm_url(url) for _, u in links):
        return
    links.append([label, url])


def reach_routes(c):
    """Every way to message this contact, one per channel, best first: email (own, then outlet),
    the YouTube About page (reveals a gated business email), Discord, submission form, a social DM.
    A plain website is only offered when there is nothing else, and is marked as a dead end."""
    links, out = c["links"], []
    mails = ([c["email"]] if c["email"] else []) + [u[7:] for _, u in links if u.startswith("mailto:")]
    if mails:
        out.append({"how": "email", "label": f"Email {mails[0]}", "url": "mailto:" + mails[0]})
    about = next((u for l, u in links if l == "About (email)"), "")
    if not mails and c["route"] == "Gated email" and about:
        out.append({"how": "gated", "label": "Reveal business email (YouTube About)", "url": about})
    discord = next((u for _, u in links if platform_of(u) == "Discord"), "")
    if discord:
        out.append({"how": "discord", "label": "Join / DM on Discord", "url": discord})
    form = next((u for l, u in links if l.lower().endswith("submit") or l == "Contact page"), "")
    if form:
        out.append({"how": "form", "label": "Contact / submission form", "url": form})
    dm = next(((want, u) for want in DM_PLATFORMS if want != "Discord"
               for _, u in links if platform_of(u) == want), None)
    if dm:
        out.append({"how": "dm", "label": f"DM on {dm[0]}", "url": dm[1]})
    if not out:
        web = next(((l, u) for l, u in links if l not in ("YouTube", "About (email)", "Next Fest piece")
                    and not l.startswith("Evidence")), None)
        if web:
            out.append({"how": "web", "label": f"Open {web[0]} (no direct contact)", "url": web[1]})
    return out or [{"how": "none", "label": "No public route", "url": ""}]


def other_socials(notes):
    """URLs a researcher listed as 'Other socials: <url>, <url>' in notes."""
    m = re.search(r"Other socials:\s*([^|]+)", notes or "")
    return re.findall(r"https?://[^\s,;|]+", m.group(1)) if m else []

INVITE_RE = re.compile(r"(?:discord\.gg|discord(?:app)?\.com/invite)/([\w-]+)", re.I)
VIDEO_RE = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/live/)([\w-]{11})")


def dead_invites():
    """Discord invite codes Discord reports as expired (tools/check_outreach_links.py discord)."""
    return {r["code"].lower() for r in read_csv(PROJECT_DIR / "exports" / "discord_invites.csv")
            if r.get("status") == "expired"}


def is_dead_invite(url, dead):
    m = INVITE_RE.search(url or "")
    return bool(m and m.group(1).lower() in dead)


def clean_title(t):
    """Video title safe to quote in a message: no emoji, hashtags or runs of spaces."""
    t = re.sub(r"#\w+", "", t or "")
    t = t.replace("{", "(").replace("}", ")")  # braces would look like unfilled placeholders
    t = "".join(ch for ch in t if ord(ch) < 0x2190 or 0x3000 <= ord(ch) < 0xD800 or 0xF900 <= ord(ch) < 0xFE00)
    return re.sub(r"\s{2,}", " ", t).strip(" -|")


def evidence_titles():
    return {r["video_id"]: clean_title(r["title"]) for r in read_csv(PROJECT_DIR / "exports" / "evidence_titles.csv")
            if r.get("status") == "ok" and r.get("title")}


def pick_evidence_title(evidence, game, titles):
    """Title of an evidence video to name in a message, preferring one that mentions the lead game."""
    found = [titles[m.group(1)] for e in evidence if (m := VIDEO_RE.search(e)) and titles.get(m.group(1))]
    key = norm_game(game) if game else ""
    return next((t for t in found if key and key in norm_game(t)), found[0] if found else "")


def creator_route(r, revealed):
    if r["creator_id"] in revealed or known(r.get("business_email")):
        return "Email"
    m = r.get("public_contact_method", "")
    if m.startswith("YouTube About"):
        return "Gated email"
    if "community/contact" in m:
        return "Discord / site"
    if "social" in m:
        return "Social only"
    return "Unknown"


def load_contacts():
    seed_tiers = load_seed_tiers()
    revealed = {r["contact_id"]: r["email"] for r in read_csv(REVEALED_PATH) if known(r.get("email"))}
    dead, titles = dead_invites(), evidence_titles()
    about_links = {}
    for r in read_csv(PROJECT_DIR / "exports" / "creator_links.csv"):
        about_links.setdefault(r["creator_id"], []).append((r["title"], r["url"]))
    contacts = []

    for r in read_csv(PROJECT_DIR / "creators.csv"):
        games = split_games(r.get("relevant_games"))
        yt = known(r.get("youtube_channel_url"))
        contact_page = known(r.get("contact_page"))
        links = []
        if yt:
            links.append(["YouTube", yt])
            links.append(["About (email)", yt.rstrip("/") + "/about"])
        if known(r.get("twitch_channel_url")):
            links.append(["Twitch", known(r["twitch_channel_url"])])
        if contact_page and not is_dead_invite(contact_page, dead):
            links.append(["Discord" if "discord" in contact_page.lower() else "Contact page", contact_page])
        if known(r.get("other_social_url")) and not is_dead_invite(r["other_social_url"], dead):
            add_link(links, platform_of(known(r["other_social_url"]), "Social"), known(r["other_social_url"]))
        for title, url in about_links.get(r["creator_id"], []):  # every link on their YouTube About panel
            if is_dead_invite(url, dead):
                continue
            add_link(links, title if url.startswith("mailto:") else platform_of(url, title or "Website"), url)
        evidence = [e for e in (known(r.get(f"evidence_url_{i}")) for i in (1, 2, 3)) if e]
        game = lead_game(games, seed_tiers)
        contacts.append({
            "id": r["creator_id"],
            "kind": "creator",
            "name": r["creator_name"],
            "tier": r.get("tier", ""),
            "score": float(known(r.get("fit_score")) or 0),
            "hp": r.get("high_priority") == "Yes",
            "subs": to_int(r.get("youtube_subscribers")),
            "twitch": bool(known(r.get("twitch_channel_url"))),
            "games": games,
            "game": game,
            "evidence": evidence,
            "evidence_title": pick_evidence_title(evidence, game, titles),
            "links": links,
            "email": revealed.get(r["creator_id"]) or known(r.get("business_email")),
            "email_revealed": r["creator_id"] in revealed,
            "route": creator_route(r, revealed),
            "last_active": known(r.get("last_active_date")),
            "country": known(r.get("country")),
            "style": known(r.get("content_style")),
            "type": "",
            "outlet": "",
            "notes": known(r.get("notes")),
            "policy": "",
        })

    outlets = read_csv(PROJECT_DIR / "press" / "outlets.csv")
    outlet_names = {o["outlet_id"]: o["name"] for o in outlets}
    outlet_types = {o["outlet_id"]: o["type"] for o in outlets}
    outlet_by_id = {o["outlet_id"]: o for o in outlets}
    for kind, rows, id_field in (("outlet", outlets, "outlet_id"),
                                 ("journalist", read_csv(PROJECT_DIR / "press" / "journalists.csv"),
                                  "journalist_id")):
        for r in rows:
            games = split_games(r.get("comparable_coverage") if kind == "outlet" else r.get("games_covered"))
            links = []
            for label, field in (("Site", "url"), ("Author page", "author_page_url"),
                                 ("Submit", "submission_url"), ("Social", "social_url"),
                                 ("Next Fest piece", "nextfest_url")):
                if known(r.get(field)) and not is_dead_invite(r[field], dead):
                    add_link(links, platform_of(known(r[field]), label) if field == "social_url" else label,
                             known(r[field]))
            for url in other_socials(r.get("notes")):
                if not is_dead_invite(url, dead):
                    add_link(links, platform_of(url, "Social"), url)
            evidence = [known(r.get(f"evidence_url_{i}")) for i in (1, 2, 3)]
            oids = [o.strip() for o in known(r.get("outlet_ids")).split(";") if o.strip()]
            route = known(r.get("public_contact_method")) or "Unknown"
            if kind == "journalist":
                # Journalists without a personal route can still be pitched through their outlet.
                for oid in oids:
                    o = outlet_by_id.get(oid, {})
                    for e in known(o.get("public_email")).split(";"):
                        if e.strip():
                            add_link(links, f"{o['name']} email", "mailto:" + e.strip())
                    if known(o.get("submission_url")):
                        add_link(links, f"{o['name']} submit", known(o["submission_url"]))
                    if known(o.get("social_url")):
                        add_link(links, f"{o['name']} {platform_of(known(o['social_url']), 'social')}", known(o["social_url"]))
                if route in ("Unknown", "Social profile") and any(l[1].startswith("mailto:") for l in links):
                    route = "Via outlet email"
            outlet = (", ".join(outlet_names.get(o, o) for o in oids) or known(r.get("outlets"))
                      if kind == "journalist" else r["name"])
            notes = " | ".join(x for x in (known(r.get("press_policy_notes")), known(r.get("contact_preference")),
                                           known(r.get("beat")), known(r.get("notes"))) if x)
            contacts.append({
                "id": r[id_field],
                "kind": kind,
                "name": r["name"],
                "tier": r.get("tier", ""),
                "score": float(known(r.get("fit_score")) or 0),
                "hp": False,
                "subs": None,
                "twitch": False,
                "games": games,
                "game": lead_game(games, seed_tiers),
                "evidence": [e for e in evidence if e],
                "evidence_title": "",
                "links": links,
                "email": known(r.get("public_email")),
                "email_revealed": False,
                "route": route,
                "last_active": known(r.get("last_relevant_article_date") or r.get("last_article_date")),
                "country": known(r.get("region_language")),
                "style": known(r.get("role")) if kind == "journalist" else "",
                "type": r.get("type", "") if kind == "outlet" else
                        "; ".join(dict.fromkeys(outlet_types.get(o, "") for o in oids if outlet_types.get(o))),
                "outlet": outlet,
                "nextfest": known(r.get("nextfest_coverage")),
                "notes": notes,
                "policy": " | ".join(x for x in (known(r.get("press_policy_notes")),
                                                 known(r.get("contact_preference"))) if x),
            })
    for c in contacts:
        c["reach"] = reach_routes(c)
        c["message"] = c["reach"][0]
    return contacts


def compute_status(log_rows):
    """contact_id -> {status, since, follow_up_on, history:[...]}"""
    out = {}
    for row in log_rows:
        cid = row["contact_id"]
        s = out.setdefault(cid, {"stack": [], "history": []})
        s["history"].append({k: row.get(k, "") for k in ("timestamp", "action", "channel", "template", "note")})
        action = row.get("action")
        if action == "note":
            continue
        if action == "undo":
            if s["stack"]:
                s["stack"].pop()
            continue
        s["stack"].append(row)
    result = {}
    for cid, s in out.items():
        last = s["stack"][-1] if s["stack"] else None
        result[cid] = {
            "status": last["action"] if last else "",
            "since": last["timestamp"][:10] if last else "",
            "follow_up_on": last.get("follow_up_on", "") if last else "",
            "channel": last.get("channel", "") if last else "",
            "history": s["history"][-12:],
        }
    return result


def load_templates():
    templates = []
    for p in sorted(TEMPLATE_DIR.glob("*.txt")):
        text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        subject = ""
        if text.startswith("Subject:"):
            first, _, text = text.partition("\n")
            subject = first[len("Subject:"):].strip()
        templates.append({"id": p.stem, "subject": subject, "body": text.strip("\n")})
    return templates


def build_payload():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    log_rows = read_csv(LOG_PATH)
    return {
        "contacts": load_contacts(),
        "status": compute_status(log_rows),
        "config": config,
        "templates": load_templates(),
        "today": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Gmail in the right Chrome profile
# ---------------------------------------------------------------------------

def chrome_exe():
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if base and (Path(base) / "Google/Chrome/Application/chrome.exe").is_file():
            return str(Path(base) / "Google/Chrome/Application/chrome.exe")
    return None


def chrome_profile_for(email, fallback=""):
    """Chrome profile directory signed in as `email` (from Chrome's Local State), else `fallback`."""
    try:
        state = json.loads((Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/User Data/Local State").read_text(encoding="utf-8"))
        for folder, info in state["profile"]["info_cache"].items():
            if (info.get("user_name") or "").lower() == (email or "").lower():
                return folder
    except (KeyError, OSError, ValueError):
        pass
    return fallback


def default_sender(c, config):
    """Major outlets, Arabic-language press and IGN go out from config.press_major_account; everyone else
    from config.gmail_account. Mirrors dashboard/src/lib.ts defaultSender."""
    major = (config.get("press_major_account") or "").strip()
    if major and c["kind"] != "creator" and (
            re.search(r"major outlet", c.get("type", ""), re.I) or re.search(r"arab", c.get("country", ""), re.I)
            or re.search(r"\bIGN\b", f"{c['name']} {c.get('outlet', '')}")):
        return major
    return (config.get("gmail_account") or "").strip()


def open_mail(url, config):
    """Open a Gmail compose URL in the Chrome profile logged in as its authuser (else config.gmail_account)."""
    exe = chrome_exe()
    account = (parse_qs(urlparse(url).query).get("authuser") or [config.get("gmail_account", "")])[0]
    # Only the configured default account falls back to the fixed profile; another account must be found by sign-in.
    fallback = config.get("gmail_chrome_profile", "") if account.lower() == config.get("gmail_account", "").lower() else ""
    profile = chrome_profile_for(account, fallback)
    if exe and profile:
        subprocess.Popen([exe, f"--profile-directory={profile}", url])
        return {"ok": True, "profile": profile}
    webbrowser.open(url)
    return {"ok": True, "profile": None}


# ---------------------------------------------------------------------------
# Small query API (used by start_all.ps1's terminal picker; Windows PowerShell 5.1
# can't parse the full /api/data payload, so the server filters and fills templates)
# ---------------------------------------------------------------------------

def greeting_name(c):
    if c["kind"] == "journalist":
        return c["name"].split()[0] if c["name"].split() else c["name"]
    if c["kind"] == "outlet":
        return f"{c['name']} team"
    return c["name"]


def seen_line(c):
    """One verified, specific thing about a creator's channel. Never claims the owner watched it."""
    if c.get("evidence_title"):
        return f'I noticed your video "{c["evidence_title"]}"'
    if c["game"]:
        return f"I noticed you've played {c['game']} on your channel"
    return "I came across your channel while looking for people who play deduction games"


def coverage_line(c):
    """' I saw you've covered <game>...' for press, or nothing when no coverage is on record."""
    if not c["game"]:
        return ""
    who = "you've written about" if c["kind"] == "journalist" else "you've covered"
    return f" I saw {who} {c['game']}, which is why I thought of you."


def default_template(c, how, status=""):
    """Template that fits who they are, how the owner is reaching them, and where things stand.
    Mirrors dashboard/src/lib.ts defaultTemplateId."""
    if status in ("contacted", "followed_up"):
        return "5_follow_up"
    if c["kind"] != "creator":
        return "7_send_press_kit" if status in ("replied", "interested") else "3_press_pitch"
    if status in ("replied", "interested"):
        return "8_dm_steam_link" if how in ("discord", "dm", "form") else "1_creator_email"
    return "1_creator_email" if how in ("email", "gated") else "2_creator_dm"


def fill_template(text, c, config):
    """Same placeholders as the React UI (dashboard/src/lib.ts fillTemplate)."""
    values = {**{k: str(v) for k, v in config.items()}, "name": greeting_name(c), "full_name": c["name"],
              "game": c["game"] or "indie horror", "games": ", ".join(c["games"]),
              "evidence_url": (c["evidence"] or [""])[0], "outlet": c["outlet"],
              "seen_line": seen_line(c), "coverage_line": coverage_line(c)}

    def sub(m):
        v = values.get(m.group(1))
        return v if v or (v == "" and m.group(1).endswith("_line")) else m.group(0)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"\{(\w+)\}", sub, text))


def lite(c, st):
    s = st.get(c["id"], {})
    return {"id": c["id"], "kind": c["kind"], "name": c["name"], "tier": c["tier"], "score": c["score"],
            "hp": c["hp"], "subs": c["subs"], "games": c["games"], "outlet": c["outlet"], "type": c["type"],
            "country": c["country"], "last_active": c["last_active"], "email": c["email"],
            "how": c["message"]["how"], "status": s.get("status", ""), "since": s.get("since", ""),
            "follow_up_on": s.get("follow_up_on", ""), "channels": [r["how"] for r in c["reach"]]}


def api_find(q):
    """GET /api/find?kind=creator|journalist|outlet|any&q=&tier=S,A&status=new|any|today|due|<action>&email=1&via=discord&limit=200

    via: only contacts reachable on that channel (email, gated, discord, form, dm)."""
    today = date.today().isoformat()
    kind, text = q.get("kind", "any"), q.get("q", "").lower()
    tiers = [t for t in q.get("tier", "").split(",") if t]
    want, need_email, via = q.get("status", "new"), q.get("email") == "1", q.get("via", "")
    status = compute_status(read_csv(LOG_PATH))
    out = []
    for c in load_contacts():
        s = status.get(c["id"], {})
        cur = s.get("status", "")
        if kind != "any" and c["kind"] != kind:
            continue
        if tiers and c["tier"] not in tiers:
            continue
        if need_email and c["message"]["how"] != "email":
            continue
        if via and via not in (r["how"] for r in c["reach"]):
            continue
        if text and text not in f"{c['name']} {' '.join(c['games'])} {c['outlet']} {c['email']}".lower():
            continue
        if want == "new" and cur:
            continue
        if want == "today" and not any(h["timestamp"].startswith(today) for h in s.get("history", [])):
            continue
        if want == "due" and not (cur in FOLLOW_UP_ACTIONS and s.get("follow_up_on") and s["follow_up_on"] <= today):
            continue
        if want not in ("new", "any", "today", "due") and cur != want:
            continue
        out.append(lite(c, status))
    out.sort(key=lambda r: (r["status"] != "queued" if want == "today" else 0, -r["score"]))
    return out[: int(q.get("limit", 300))]


def api_contact(q):
    """GET /api/contact?id=C0002&template=<id> -> full contact, status history and the filled message."""
    contacts = {c["id"]: c for c in load_contacts()}
    c = contacts.get(q.get("id", ""))
    if not c:
        return None
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    templates = {t["id"]: t for t in load_templates()}
    st = compute_status(read_csv(LOG_PATH)).get(c["id"], {"status": "", "since": "", "follow_up_on": "", "history": []})
    via = next((r for r in c["reach"] if r["how"] == q.get("via")), c["reach"][0])
    c = {**c, "message": via}
    default = default_template(c, via["how"], st.get("status", ""))
    t = templates.get(q.get("template") or default) or next(iter(templates.values()), {"id": "", "subject": "", "body": ""})
    subject, body = fill_template(t["subject"], c, config), fill_template(t["body"], c, config)
    sender, base = default_sender(c, config), (config.get("gmail_account") or "").strip()
    if base and sender and sender != base:
        body = body.replace(base, sender)
    return {**c, "state": st, "template": t["id"], "templates": list(templates), "subject": subject, "body": body,
            "sender": sender,
            "unfilled": sorted(set(re.findall(r"\{\w+\}", subject + body)))}


def api_stats():
    today = date.today().isoformat()
    contacts = load_contacts()
    status = compute_status(read_csv(LOG_PATH))
    by = {}
    for c in contacts:
        cur = status.get(c["id"], {}).get("status", "") or "new"
        by.setdefault(c["kind"], {}).setdefault(cur, 0)
        by[c["kind"]][cur] += 1
    # current (post-undo) status only, so an undone "contacted" no longer counts
    messaged = sum(1 for s in status.values() if s["status"] in FOLLOW_UP_ACTIONS and s["since"] == today)
    due = sum(1 for s in status.values()
              if s["status"] in FOLLOW_UP_ACTIONS and s["follow_up_on"] and s["follow_up_on"] <= today)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    return {"by_kind": by, "messaged_today": messaged, "daily_target": config.get("daily_target", 30),
            "follow_ups_due": due, "totals": {k: sum(v.values()) for k, v in by.items()}}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "OutreachApp/1"

    def log_message(self, fmt, *args):  # quiet console
        pass

    def _host_ok(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, '{"error":"forbidden host"}')
        path, _, qs = self.path.partition("?")
        q = {k: v[-1] for k, v in parse_qs(qs).items()}
        if path == "/api/data":
            return self._send(200, json.dumps(build_payload()))
        if path == "/api/find":
            return self._send(200, json.dumps(api_find(q)))
        if path == "/api/contact":
            c = api_contact(q)
            return self._send(200 if c else 404, json.dumps(c or {"error": "no such contact"}))
        if path == "/api/stats":
            return self._send(200, json.dumps(api_stats()))
        if path.startswith("/api/"):
            return self._send(404, '{"error":"not found"}')
        return self._static(path)

    def _static(self, path):
        if not (DIST_DIR / "index.html").exists():
            return self._send(503, "Dashboard not built. Run: cd dashboard && npm install && npm run build",
                              "text/plain; charset=utf-8")
        target = (DIST_DIR / path.lstrip("/")).resolve()
        if path == "/" or not target.is_file() or DIST_DIR.resolve() not in target.parents:
            target = DIST_DIR / "index.html"
        return self._send(200, target.read_bytes(), MIME.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        if not self._host_ok() or not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._send(403, '{"error":"forbidden"}')
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, '{"error":"bad json"}')

        if self.path == "/api/log":
            entries = body.get("entries") or [body]
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
            for e in entries:
                action = e.get("action", "")
                if action not in ACTIONS or not e.get("contact_id"):
                    return self._send(400, json.dumps({"error": f"bad entry {e}"}))
                follow = e.get("follow_up_on", "")
                if not follow and action in FOLLOW_UP_ACTIONS:
                    days = int(config.get("follow_up_days", 7))
                    follow = (date.today() + timedelta(days=days)).isoformat()
                append_csv(LOG_PATH, LOG_FIELDS, {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "contact_id": e["contact_id"],
                    "kind": e.get("kind", ""),
                    "name": e.get("name", ""),
                    "action": action,
                    "channel": e.get("channel", ""),
                    "template": e.get("template", ""),
                    "note": (e.get("note") or "").replace("\n", " "),
                    "follow_up_on": follow,
                })
            return self._send(200, json.dumps({"ok": True, "status": compute_status(read_csv(LOG_PATH))}))

        if self.path == "/api/reveal":
            email = (body.get("email") or "").strip()
            if "@" not in email or not body.get("contact_id"):
                return self._send(400, '{"error":"need contact_id and email"}')
            append_csv(REVEALED_PATH, REVEALED_FIELDS, {
                "contact_id": body["contact_id"], "email": email, "revealed_on": date.today().isoformat()})
            return self._send(200, '{"ok":true}')

        if self.path == "/api/open_mail":
            url = body.get("url") or ""
            if not url.startswith("https://mail.google.com/mail/"):
                return self._send(400, '{"error":"only Gmail compose links"}')
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
            return self._send(200, json.dumps(open_mail(url, config)))

        if self.path == "/api/open_url":
            url = body.get("url") or ""
            if not re.match(r"https://(www\.)?youtube\.com/", url):
                return self._send(400, '{"error":"only YouTube links"}')
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
            return self._send(200, json.dumps(open_mail(url.replace("://youtube.com", "://www.youtube.com", 1), config)))

        if self.path in ("/api/show_press_kit", "/api/show_trailer"):
            key = "trailer_file" if self.path.endswith("trailer") else "press_kit_file"
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
            f = (PROJECT_DIR / config.get(key, "")).resolve()
            if not config.get(key) or not f.is_file():
                return self._send(404, json.dumps({"error": f"{key} not found"}))
            subprocess.Popen(["explorer", f"/select,{f}"])
            return self._send(200, '{"ok":true}')

        return self._send(404, '{"error":"not found"}')


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local outreach dashboard (never sends anything).")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    port = args.port or int(config.get("port", 8765))
    httpd = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Outreach dashboard running at {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
