#!/usr/bin/env python3
"""Chunked candidate review for Club Sanguine creator research.

Reads the harvest cache (exports/harvest/), applies hard filters, and lets a reviewer
(human or agent) accept/reject candidates in frozen chunks. Nothing here touches the
network or creators.csv; tools/import_pools.py does the import.

    python tools/review.py summary                 # filter counts + how many are ready to review
    python tools/review.py pending                 # channel IDs that only lack an About page
    python tools/review.py next 90 [--quiet]       # freeze the next 90 ready candidates as a new chunk
    python tools/review.py show K                  # print chunk K, one line per candidate
    python tools/review.py decide K "<decisions>"  # record decisions for chunk K (once per chunk)

Decision string: entries separated by "|". Each entry is either
    idx:R=<reason>                                   reject
    idx:g=<10-20>,p=<1-5>,i=<1-5>[,s=<style>][,e=<email>][,n=<note>]   accept
`n=` must come last and may contain commas; `s=` must not. Unlisted indexes are accepted
with default scores, so always list every index. See tools/REVIEW_RUBRIC.md.
"""
import csv
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "exports" / "harvest"
LOG = ROOT / "exports" / "review_log"
CHUNKS = LOG / "chunks"
sys.path.insert(0, str(ROOT / "scripts"))
import yt_harvest as yt  # noqa: E402

NONENG = re.compile(
    r"\b(español|espanol|deutsch|português|portugues|parte \d|folge|bölüm|juego|jogo|jugando|joguei|gameplay en|tập|"
    r"прохождение|часть|odcinek|aflevering|episodio|capitulo|capítulo|el juego|le jeu|zagrałem|oyun|oynuyorum|sub indo|"
    r"bahasa|ngakak|tiếng|chơi|polskie|cała gra|malayalam|hindi|tamil|telugu|pinoy|tagalog)\b", re.I)
CLIP = re.compile(r"\b(clips?|highlights?|compilation|reupload|best of)\b", re.I)
TIER_ORDER = {1: 0, 2: 1, 3: 2, "related": 3}


def latin(s):
    letters = [c for c in s if c.isalpha()]
    return sum(c.isascii() for c in letters) / max(1, len(letters))


def reviewed_ids():
    ids = set()
    for f in CHUNKS.glob("chunk_*.json"):
        ids |= {r["cid"] for r in json.loads(f.read_text(encoding="utf-8"))}
    return ids


def load_all():
    """Every cached candidate not already in creators.csv, with hard-filter reasons attached."""
    cands = json.loads((HARVEST / "candidates.json").read_text(encoding="utf-8"))
    existing = {r["youtube_channel_id"] for r in csv.DictReader(open(ROOT / "creators.csv", encoding="utf-8"))}
    rows = []
    for c in cands:
        cid = c["channel_id"]
        f = HARVEST / "channels" / f"{cid}.json"
        if cid in existing or not f.exists():
            continue
        ch = json.loads(f.read_text(encoding="utf-8"))
        games = c["games"]
        t1 = sum(1 for g in games if yt.GAME_TIERS[g] == 1)
        t2 = sum(1 for g in games if yt.GAME_TIERS[g] == 2)
        rel = sum(1 for g in games if yt.GAME_TIERS[g] == "related")
        subs, days = ch["subscribers"], ch["latest_upload_days"]
        titles = [v["title"] for v in ch["recent_videos"][:12]]
        text = " ".join(titles) + " " + ch["description"][:400]
        reasons = []
        if subs and (subs > 3_000_000 or (subs > 500_000 and t1 < 2)):
            reasons.append("size")
        if (days is None or days > 90) and t1 < 3:
            reasons.append("inactive")
        if latin(" ".join(titles)) < 0.85 or len(NONENG.findall(text)) >= 2:
            reasons.append("lang")
        if re.search(r"no[ -]?commentary|no talking|without commentary", text, re.I):
            reasons.append("nocomm")
        if CLIP.search(ch["name"]) or len(CLIP.findall(" ".join(titles))) >= 4 or \
                re.search(r"top videos|to sleep to|fan ?made|unofficial", ch["name"] + " " + " ".join(titles[:3]), re.I):
            reasons.append("clips")
        if not titles:
            reasons.append("novids")
        apath = HARVEST / "about" / f"{cid}.json"
        about = json.loads(apath.read_text(encoding="utf-8")) if apath.exists() else None
        if about is None:
            reasons.append("noabout")
        elif not (about["links"] or about["emails"] or ch["emails_in_description"] or about["email_gated"]):
            reasons.append("nocontact")
        twitch = re.search(r"twitch\.tv/([A-Za-z0-9_]{3,25})", ch["description"])
        rows.append(dict(
            cid=cid, name=ch["name"], handle=ch["handle_url"], subs=subs, subs_text=ch["subscribers_text"], days=days,
            t1=t1, t2=t2, rel=rel, games=games, titles=titles, desc=ch["description"].replace("\n", " ")[:160],
            emails=ch["emails_in_description"], reasons=reasons, queries=c["queries"],
            twitch=f"https://www.twitch.tv/{twitch.group(1).lower()}" if twitch else None,
            country=(about or {}).get("country"), links=[l["url"] for l in (about or {}).get("links", [])][:4],
            gated=(about or {}).get("email_gated")))
    return rows


def show(chunk):
    for i, r in enumerate(chunk):
        g = ",".join(re.sub(r"[^A-Za-z0-9]", "", x)[:9] for x in r["games"])
        t = " / ".join(x[:34] for x in r["titles"][:6])
        c = ",".join(x.split("/")[0].replace("www.", "") for x in r.get("links", []))
        print(f"{i}|{r['name'][:26]}|{r['subs']}|{r['days']}d|{g}|{r.get('country') or '?'}|"
              f"C:{c}{'+gated' if r.get('gated') else ''}|E:{','.join(r['emails'])}|{t}|D:{r['desc'][:60]}")


def parse_decisions(spec):
    dec = {}
    for part in filter(None, (p.strip() for p in spec.split("|"))):
        idx, rest = part.split(":", 1)
        d = {}
        if ",n=" in rest or rest.startswith("n="):
            rest, d["n"] = rest.split(",n=", 1) if ",n=" in rest else ("", rest[2:])
        if rest.startswith("R="):
            d["R"], rest = rest[2:], ""
        for kv in filter(None, rest.split(",")):
            a, b = kv.split("=", 1)
            d[a.strip()] = b.strip()
        dec[int(idx)] = d
    return dec


def decide(k, spec):
    pool_path, rej_path = LOG / f"pool_c{k}.json", LOG / f"rejected_c{k}.json"
    if pool_path.exists():
        sys.exit(f"chunk {k} already decided ({pool_path.name} exists); delete it first to redo")
    chunk = json.loads((CHUNKS / f"chunk_{k}.json").read_text(encoding="utf-8"))
    dec = parse_decisions(spec)
    accepted, rejected = [], []
    for i, r in enumerate(chunk):
        d = dec.get(i, {})
        if "R" in d:
            rejected.append({"cid": r["cid"], "name": r["name"], "reason": d["R"]})
            continue
        order = sorted(r["games"], key=lambda g: TIER_ORDER[yt.GAME_TIERS[g]])
        evidence = [r["games"][g][0] for g in order][:3]
        for g in order:
            for u in r["games"][g][1:]:
                if len(evidence) < 3 and u not in evidence:
                    evidence.append(u)
        genre = min(20, 12 + 3 * min(r["t1"], 2) + min(r["t2"], 2) + (1 if r["rel"] else 0))
        note = (f"Latest upload ~{r['days']}d before {date.today().isoformat()} (channel videos tab). "
                f"{r['subs_text'] or 'Subscriber count hidden'}. Seed/related evidence by video title: {', '.join(order)}.")
        if r["subs"] and r["subs"] > 500_000:
            note += " Size exception: above preferred range but 2+ Tier-1 comparables."
        if d.get("n"):
            note += " " + d["n"]
        accepted.append({
            "channel_id": r["cid"], "name": r["name"], "profile": r["handle"], "subs": r["subs"], "games": order,
            "evidence": evidence, "activity_days": r["days"], "query": r["queries"][0], "notes": note,
            "style": d.get("s", "Gameplay commentary / playthroughs"),
            "email": d.get("e") or (r["emails"][0] if r["emails"] else None), "contact": None, "social": None,
            "twitch": r["twitch"], "genre": int(d.get("g", genre)), "personality": int(d.get("p", 4)),
            "indie": int(d.get("i", 4))})
    pool_path.write_text(json.dumps(accepted, indent=1, ensure_ascii=False), encoding="utf-8")
    rej_path.write_text(json.dumps(rejected, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"chunk {k}: accepted {len(accepted)}, rejected {len(rejected)}")


def main():
    CHUNKS.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1]
    if mode == "summary":
        rows, done = load_all(), reviewed_ids()
        print("fetched", len(rows), "passing", sum(not r["reasons"] for r in rows),
              "ready-to-review", sum(not r["reasons"] and r["cid"] not in done for r in rows))
        print(Counter(x for r in rows for x in r["reasons"]))
    elif mode == "pending":
        print("\n".join(r["cid"] for r in load_all() if r["reasons"] == ["noabout"]))
    elif mode == "next":
        done = reviewed_ids()
        ok = [r for r in load_all() if not r["reasons"] and r["cid"] not in done]
        ok.sort(key=lambda r: (-r["t1"], -r["t2"], -len(r["games"])))
        chunk = ok[:int(sys.argv[2])]
        k = max([int(f.stem.split("_")[1]) for f in CHUNKS.glob("chunk_*.json")] + [0]) + 1
        (CHUNKS / f"chunk_{k}.json").write_text(json.dumps(chunk, ensure_ascii=False), encoding="utf-8")
        print(f"chunk {k}: {len(chunk)}")
        if "--quiet" not in sys.argv:
            show(chunk)
    elif mode == "show":
        show(json.loads((CHUNKS / f"chunk_{sys.argv[2]}.json").read_text(encoding="utf-8")))
    elif mode == "decide":
        decide(sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
