#!/usr/bin/env python3
"""
yt_harvest.py — evidence-linked YouTube discovery helper (standard library only).

Reads public YouTube search/channel pages and caches what they show. It never
logs in, never posts, and never contacts anyone. Every video it records comes
with the uploader's channel ID straight from YouTube's own page data, so
evidence is never inferred.

Commands:
    python scripts/yt_harvest.py search "\"Papers, Please\" gameplay" [--sp FILTER] [--pages N]
    python scripts/yt_harvest.py channel UCxxxxxxxx [--force]
    python scripts/yt_harvest.py channels UC1 UC2 ...          # fetch many (cached)
    python scripts/yt_harvest.py aggregate                       # -> exports/harvest/candidates.json

Useful --sp filters: EgIQAQ%3D%3D (videos), CAISAhAB (videos, newest first),
EgQIBRAB (videos, this year), EgQIBBAB (videos, this month).
"""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
HARVEST_DIR = PROJECT_DIR / "exports" / "harvest"
QUERY_DIR = HARVEST_DIR / "queries"
CHANNEL_DIR = HARVEST_DIR / "channels"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
DELAY_SECONDS = 1.2

# (canonical name, tier, title patterns). Order matters: more specific first.
GAMES = [
    ("Not Tonight 2", "related", [r"not tonight 2"]),
    ("Papers, Please", 1, [r"papers please"]),
    ("That's Not My Neighbor", 1, [r"thats not my neighbou?r", r"tnmn"]),
    ("Not Tonight", 1, [r"not tonight"]),
    ("Contraband Police", 1, [r"contraband police"]),
    ("Quarantine Zone", 1, [r"quarantine zone"]),
    ("The Mortuary Assistant", 2, [r"mortuary assistant"]),
    ("Killer Frequency", 2, [r"killer frequency"]),
    ("Buckshot Roulette", 2, [r"buckshot roulette"]),
    ("I'm on Observation Duty", 2, [r"observation duty"]),
    ("Death and Taxes", 2, [r"death and taxes"]),
    ("Inscryption", 3, [r"inscryption"]),
    ("World of Horror", 3, [r"world of horror"]),
    ("Fears to Fathom", 3, [r"fears to fathom"]),
    ("Scarlet Hollow", 3, [r"scarlet hollow"]),
    ("Cult of the Lamb", 3, [r"cult of the lamb"]),
    # Related titles discovered during research (see exports/discovered_games.md).
    ("No, I'm Not a Human", "related", [r"no im not a human"]),
    ("Security 51", "related", [r"security 51"]),
    ("Airport Contraband", "related", [r"airport contraband"]),
    ("Alternate Watch", "related", [r"alternate watch"]),
    ("Jeremy, No!", "related", [r"jeremy no"]),
    ("The Exit 8", "related", [r"exit 8"]),
    ("Beholder", "related", [r"\bbeholder\b"]),
    ("Return of the Obra Dinn", "related", [r"obra dinn"]),
    ("Strange Horticulture", "related", [r"strange horticulture"]),
    ("Welcome to the Game", "related", [r"welcome to the game"]),
    ("Do Not Feed the Monkeys", "related", [r"do not feed the monkeys"]),
    ("Night Security", "related", [r"night security"]),
    ("Shift at Midnight", "related", [r"shift at midnight"]),
    ("Scrutinized", "related", [r"\bscrutinized\b"]),
    ("Diapers Please", "related", [r"diapers please"]),
    ("Animaly Bar", "related", [r"animaly bar"]),
    ("Japan Stigmatized Property", "related", [r"stigmatized property"]),
    ("Can I Come In", "related", [r"\bcan i come in\b"]),
    ("Photomaly", "related", [r"\bphotomaly\b"]),
    ("Kiosk", "related", [r"\bkiosk\b"]),
    ("Roadhouse Simulator", "related", [r"\broadhouse simulator\b"]),
    ("Endacopia", "related", [r"\bendacopia\b"]),
    ("Gas Station Case", "related", [r"\bgas station case\b"]),
    ("The Floor Above", "related", [r"\bthe floor above\b"]),
    ("Perceptum", "related", [r"\bperceptum\b"]),
    ("Roadside Research", "related", [r"\broadside research\b"]),
    ("The Skin Stapler", "related", [r"\bskin stapler\b"]),
    ("Take Care of the Dog", "related", [r"\btake care of the dog\b"]),
    ("Loan Shark", "related", [r"\bloan shark\b"]),
    ("Hariti", "related", [r"\bhariti\b"]),
    ("Subliminal", "related", [r"\bsubliminal\b"]),
    ("Creature Kitchen", "related", [r"\bcreature kitchen\b"]),
    ("Servant of the Lake", "related", [r"\bservant of the lake\b"]),
    ("Dread Neighbor", "related", [r"\bdread neighbou?r\b"]),
    ("Who's at the Door", "related", [r"\bwhos at the door\b"]),
    ("Not My Dad", "related", [r"\bnot my dad\b"]),
    ("Human Shaped", "related", [r"\bhuman shaped\b"]),
    ("The Pale Mimic", "related", [r"\bpale mimic\b"]),
    ("The Unfamiliars", "related", [r"\bthe unfamiliars\b"]),
    ("Obey the Voice", "related", [r"\bobey the voice\b"]),
    ("Final Witness", "related", [r"\bfinal witness\b"]),
    ("The Cabin Factory", "related", [r"\bcabin factory\b"]),
    ("Project Threshold", "related", [r"\bproject threshold\b"]),
    ("Uncanny Tales: The Watcher", "related", [r"\buncanny tales\b"]),
    ("The Stalked", "related", [r"\bthe stalked\b"]),
    ("Rehaunted", "related", [r"\brehaunted\b"]),
    ("The Delivery Guy", "related", [r"\bthe delivery guy\b"]),
    ("Late Pizza Delivery", "related", [r"\blate pizza delivery\b"]),
    ("Night Plane", "related", [r"\bnight plane\b"]),
    ("Exorcist Candy", "related", [r"\bexorcist candy\b"]),
    ("Get Upstairs", "related", [r"\bget upstairs\b"]),
    ("The Plant Shop", "related", [r"\bthe plant shop\b"]),
    ("Choicer Voicer", "related", [r"\bchoicer voicer\b"]),
]


def norm_title(text):
    text = (text or "").lower().replace("’", "'").replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


# Names that are also common phrases / song titles need gaming context elsewhere in the title.
AMBIGUOUS = {"Not My Dad", "Human Shaped", "Get Upstairs", "The Delivery Guy", "Night Plane", "Final Witness", "Obey the Voice", "The Plant Shop", "The Stalked", "Kiosk", "Loan Shark", "Subliminal", "Can I Come In", "The Floor Above", "Not Tonight", "Not Tonight 2", "Death and Taxes", "Beholder", "Night Security", "Welcome to the Game"}
GAMING_CONTEXT = re.compile(
    r"\b(gameplay|lets? plays?|part|pt|ep|episode|playthrough|walkthrough|streams?|vods?|full game|game|bouncer|"
    r"pc|steam|review|ending|playing|plays|played|play|100|switch|ps[45]|xbox|indie|demo|dlc|day \d+|info|live)\b")


def match_games(title):
    t = norm_title(title)
    found = []
    for name, tier, patterns in GAMES:
        hit = next((p for p in patterns if re.search(p, t)), None)
        if not hit:
            continue
        if name == "Not Tonight" and "Not Tonight 2" in found:
            continue
        if name in AMBIGUOUS and not GAMING_CONTEXT.search(re.sub(hit, " ", t)):
            continue
        # "Papers, Please but X" / "Europe's Papers Please" describe other games, not coverage.
        if name == "Papers, Please" and re.search(
                rf"(like|europes|made|inspired) {hit}|{hit} (but|meets|inspired|style|like)|{hit}inspired", t):
            continue
        if name == "Not Tonight 2" and re.search(r"not tonight\s*[(#]\s*2", title, re.I):
            name = "Not Tonight"
        found.append(name)
    return found


GAME_TIERS = {name: tier for name, tier, _ in GAMES}


# ---------------------------------------------------------------------------
# HTTP + page parsing
# ---------------------------------------------------------------------------

_last_request = [0.0]


def _throttle():
    wait = DELAY_SECONDS - (time.time() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    _last_request[0] = time.time()


def http_get(url):
    _throttle()
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_post_json(url, payload):
    _throttle()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={**HEADERS, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    return json.loads(m.group(1)) if m else {}


def walk(obj, key):
    """Yield every value stored under `key` anywhere in a nested structure."""
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k == key:
                    yield v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(reversed(cur))


def runs_text(node):
    if not node:
        return ""
    if "simpleText" in node:
        return node["simpleText"]
    return "".join(r.get("text", "") for r in node.get("runs", []))


def parse_video_renderers(data):
    videos = []
    for v in walk(data, "videoRenderer"):
        owner = (v.get("ownerText") or v.get("longBylineText") or {}).get("runs", [{}])[0]
        browse = owner.get("navigationEndpoint", {}).get("browseEndpoint", {})
        videos.append({
            "video_id": v.get("videoId"),
            "title": runs_text(v.get("title")),
            "channel_name": owner.get("text", ""),
            "channel_id": browse.get("browseId", ""),
            "channel_url": browse.get("canonicalBaseUrl", ""),
            "published": runs_text(v.get("publishedTimeText")),
            "length": runs_text(v.get("lengthText")),
        })
    return videos


def continuation_tokens(data):
    return [c.get("token") for c in walk(data, "continuationCommand") if c.get("token")]


def age_to_days(text):
    """Convert '13h ago' / '3 days ago' / 'Streamed 2 weeks ago' to days (approx)."""
    t = (text or "").lower()
    m = re.search(r"(\d+)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?|mo|[smhdwy])\b", t)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if unit.startswith("mo"):
        return n * 30
    return {"s": 0, "m": 0, "h": 0, "d": n, "w": n * 7, "y": n * 365}[unit[0]]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def query_cache_path(query, sp):
    digest = hashlib.sha1(f"{query}|{sp}".encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")[:50]
    return QUERY_DIR / f"{slug}__{digest}.json"


def do_search(query, sp="EgIQAQ%3D%3D", pages=3, force=False):
    query, sp = query.strip(), (sp or "").strip()
    QUERY_DIR.mkdir(parents=True, exist_ok=True)
    path = query_cache_path(query, sp)
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8")), True

    url = "https://www.youtube.com/results?hl=en&gl=US&search_query=" + urllib.parse.quote_plus(query)
    if sp:
        url += "&sp=" + sp
    html = http_get(url)
    data = initial_data(html)
    videos = parse_video_renderers(data)

    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    ver = re.search(r'"INNERTUBE_CONTEXT_CLIENT_VERSION":"([^"]+)"', html)
    tokens = continuation_tokens(data)
    for _ in range(max(0, pages - 1)):
        if not (key and ver and tokens):
            break
        payload = {
            "context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1), "hl": "en", "gl": "US"}},
            "continuation": tokens[-1],
        }
        try:
            more = http_post_json(f"https://www.youtube.com/youtubei/v1/search?key={key.group(1)}", payload)
        except Exception as exc:  # network hiccup: keep what we have
            print(f"  continuation failed: {exc}", file=sys.stderr)
            break
        videos.extend(parse_video_renderers(more))
        tokens = continuation_tokens(more)

    seen, unique = set(), []
    for v in videos:
        if v["video_id"] and v["video_id"] not in seen:
            seen.add(v["video_id"])
            v["games"] = match_games(v["title"])
            unique.append(v)

    result = {"query": query, "sp": sp, "fetched": date.today().isoformat(), "videos": unique}
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result, False


def parse_subscribers(text):
    m = re.search(r"([\d.,]+)\s*([KMB]?)\s*subscribers?", text or "", re.I)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[m.group(2).upper()]
    return int(round(n * mult))


def do_channel(channel_id, force=False):
    CHANNEL_DIR.mkdir(parents=True, exist_ok=True)
    path = CHANNEL_DIR / f"{channel_id}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8")), True

    target = f"https://www.youtube.com/channel/{channel_id}/videos" if channel_id.startswith("UC") \
        else f"https://www.youtube.com/{channel_id.lstrip('/')}/videos"
    html = http_get(target + "?hl=en&gl=US")
    data = initial_data(html)
    meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
    header_texts = [c for c in walk(data.get("header", {}), "content") if isinstance(c, str)]

    subs_text = next((t for t in header_texts if "subscriber" in t.lower()), "")
    handle = next((t for t in header_texts if t.startswith("@")), "")
    links = [t.strip() for t in header_texts if re.search(r"[a-z0-9-]+\.[a-z]{2,}", t, re.I) and " " not in t.strip()]
    description = meta.get("description", "")
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", description)))

    recent = []
    for lk in walk(data, "lockupViewModel"):
        if lk.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO":
            continue
        md = lk.get("metadata", {}).get("lockupMetadataViewModel", {})
        title = md.get("title", {}).get("content", "")
        labels = [p.get("accessibilityLabel") or p.get("text", {}).get("content", "")
                  for parts in walk(md.get("metadata", {}), "metadataParts") for p in parts]
        age = next((l for l in labels if l and "ago" in l), "")
        recent.append({"video_id": lk.get("contentId"), "title": title, "age": age, "games": match_games(title)})
    for v in parse_video_renderers(data):  # older page layout fallback
        recent.append({"video_id": v["video_id"], "title": v["title"], "age": v["published"], "games": match_games(v["title"])})

    ages = [age_to_days(v["age"]) for v in recent if age_to_days(v["age"]) is not None]
    latest_days = min(ages) if ages else None
    result = {
        "channel_id": meta.get("externalId") or channel_id,
        "name": meta.get("title", ""),
        "handle": handle,
        "handle_url": f"https://www.youtube.com/{handle}" if handle else (meta.get("vanityChannelUrl") or "").replace("http://", "https://"),
        "subscribers": parse_subscribers(subs_text),
        "subscribers_text": subs_text,
        "description": description,
        "emails_in_description": emails,
        "header_links": links,
        "recent_videos": recent[:30],
        "latest_upload_days": latest_days,
        "latest_upload_date": (date.today() - timedelta(days=latest_days)).isoformat() if latest_days is not None else None,
        "fetched": date.today().isoformat(),
    }
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result, False


ABOUT_DIR = HARVEST_DIR / "about"
TWITCH_DIR = HARVEST_DIR / "twitch"


def do_about(channel_id, force=False):
    """Public About panel: country and creator-listed links. Business emails stay captcha-gated and are not touched."""
    ABOUT_DIR.mkdir(parents=True, exist_ok=True)
    path = ABOUT_DIR / f"{channel_id}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8")), True
    html = http_get(f"https://www.youtube.com/channel/{channel_id}/about?hl=en&gl=US")
    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    ver = re.search(r'"INNERTUBE_CONTEXT_CLIENT_VERSION":"([^"]+)"', html)
    result = {"channel_id": channel_id, "country": None, "links": [], "description": "", "email_gated": False,
              "fetched": date.today().isoformat()}
    about = next(walk(initial_data(html), "aboutChannelViewModel"), None)
    tokens = re.findall(r'"continuationCommand":\{"token":"([^"]+)"', html)
    while about is None and tokens and key and ver:
        payload = {"context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1), "hl": "en", "gl": "US"}},
                   "continuation": tokens.pop(0)}
        about = next(walk(http_post_json(f"https://www.youtube.com/youtubei/v1/browse?key={key.group(1)}", payload),
                          "aboutChannelViewModel"), None)
    if about:
        result["country"] = about.get("country")
        result["description"] = about.get("description", "")
        result["email_gated"] = "signInForBusinessEmail" in about
        for link in walk(about, "channelExternalLinkViewModel"):
            url = link.get("link", {}).get("content", "")
            if url:
                result["links"].append({"title": link.get("title", {}).get("content", ""), "url": url})
    result["emails"] = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", result["description"])))
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result, False


def do_twitch(username, force=False):
    """TwitchTracker public summary panel (period label is not in the static page)."""
    TWITCH_DIR.mkdir(parents=True, exist_ok=True)
    username = username.lower()
    path = TWITCH_DIR / f"{username}.json"
    if path.exists() and not force:
        return json.loads(path.read_text(encoding="utf-8")), True
    result = {"username": username, "found": False, "hours_streamed": None, "avg_viewers": None,
              "peak_viewers": None, "fetched": date.today().isoformat()}
    try:
        html = http_get(f"https://twitchtracker.com/{urllib.parse.quote(username)}")
        panel = html[html.find('id="performance-panel"'):][:3000]
        pairs = dict((label.strip(), value.replace(",", "")) for value, label in
                     re.findall(r'g-x-s-value[^>]*>([\d,]+)</div>\s*<div class="g-x-s-label[^"]*">([^<]+)<', panel))
        result.update(found=bool(pairs), hours_streamed=pairs.get("Hours streamed"),
                      avg_viewers=pairs.get("Average viewers"), peak_viewers=pairs.get("Peak viewers"))
    except urllib.error.HTTPError as exc:
        result["error"] = exc.code
    path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result, False


def do_aggregate():
    channels = {}
    for qfile in sorted(QUERY_DIR.glob("*.json")):
        q = json.loads(qfile.read_text(encoding="utf-8"))
        for v in q["videos"]:
            v["games"] = match_games(v["title"])
            if not v["games"] or not v["channel_id"]:
                continue
            c = channels.setdefault(v["channel_id"], {
                "channel_id": v["channel_id"], "name": v["channel_name"],
                "channel_url": v.get("channel_url", ""), "games": {}, "queries": [],
            })
            for g in v["games"]:
                urls = c["games"].setdefault(g, [])
                url = f"https://www.youtube.com/watch?v={v['video_id']}"
                if url not in urls:
                    urls.append(url)
            if q["query"] not in c["queries"]:
                c["queries"].append(q["query"])

    # Fold in any comparable games seen in cached channel uploads.
    for cid, c in channels.items():
        cpath = CHANNEL_DIR / f"{cid}.json"
        if cpath.exists():
            ch = json.loads(cpath.read_text(encoding="utf-8"))
            for v in ch.get("recent_videos", []):
                for g in match_games(v["title"]):
                    urls = c["games"].setdefault(g, [])
                    url = f"https://www.youtube.com/watch?v={v['video_id']}"
                    if url not in urls:
                        urls.append(url)

    for c in channels.values():
        tiers = [GAME_TIERS[g] for g in c["games"]]
        c["tier1"] = sum(1 for t in tiers if t == 1)
        c["tier2"] = sum(1 for t in tiers if t == 2)
        c["tier3"] = sum(1 for t in tiers if t == 3)
        c["related"] = sum(1 for t in tiers if t == "related")

    ordered = sorted(channels.values(), key=lambda c: (-c["tier1"], -c["tier2"], -len(c["games"])))
    out = HARVEST_DIR / "candidates.json"
    out.write_text(json.dumps(ordered, indent=1, ensure_ascii=False), encoding="utf-8")
    return ordered


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evidence-linked YouTube discovery helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--sp", default="EgIQAQ%3D%3D")
    p.add_argument("--pages", type=int, default=3)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("channel")
    p.add_argument("channel_id")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("channels")
    p.add_argument("channel_ids", nargs="+")
    sub.add_parser("aggregate")
    p = sub.add_parser("about")
    p.add_argument("channel_ids", nargs="+")
    p = sub.add_parser("twitch")
    p.add_argument("usernames", nargs="+")
    args = parser.parse_args(argv)
    for attr in ("channel_ids", "usernames"):
        if hasattr(args, attr):
            setattr(args, attr, [x.strip() for x in getattr(args, attr) if x.strip()])
    if hasattr(args, "channel_id"):
        args.channel_id = args.channel_id.strip()

    if args.command == "search":
        res, cached = do_search(args.query, args.sp, args.pages, args.force)
        hits = [v for v in res["videos"] if v["games"]]
        print(f"{'(cached) ' if cached else ''}{args.query!r}: {len(res['videos'])} videos, {len(hits)} game-matched, "
              f"{len({v['channel_id'] for v in hits})} channels")
    elif args.command == "channel":
        res, _ = do_channel(args.channel_id, args.force)
        print(json.dumps({k: res[k] for k in ("channel_id", "name", "handle_url", "subscribers", "latest_upload_days")}))
    elif args.command == "channels":
        for cid in args.channel_ids:
            try:
                res, cached = do_channel(cid)
                print(f"{'(cached) ' if cached else ''}{cid} {res['name']} subs={res['subscribers']} latest={res['latest_upload_days']}d")
            except Exception as exc:
                print(f"FAIL {cid}: {exc}")
    elif args.command == "about":
        for cid in args.channel_ids:
            try:
                res, cached = do_about(cid)
                print(f"{'(cached) ' if cached else ''}{cid} country={res['country']} links={len(res['links'])} emails={len(res['emails'])}")
            except Exception as exc:
                print(f"FAIL {cid}: {exc}")
    elif args.command == "twitch":
        for u in args.usernames:
            try:
                res, cached = do_twitch(u)
                print(f"{'(cached) ' if cached else ''}{u} found={res['found']} avg={res['avg_viewers']} hours={res['hours_streamed']}")
            except Exception as exc:
                print(f"FAIL {u}: {exc}")
    elif args.command == "aggregate":
        ordered = do_aggregate()
        print(f"{len(ordered)} channels with game-matched evidence -> {HARVEST_DIR / 'candidates.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
