# Club Sanguine Creator Research

> **New agent or collaborator? Start with [HANDOVER.md](HANDOVER.md)** — current state, decisions already made, and how to continue.

This project supports creator/streamer research for the indie game **Club Sanguine**. It is designed to be handed off to a research agent ("Astra") that will find and evaluate relevant content creators, while keeping outreach as a strictly separate, human-gated phase.

## Workflow

**Phase 1 — Brief**
A human inserts the final Club Sanguine creator-research brief into [CLUB_SANGUINE_CREATOR_BRIEF.md](CLUB_SANGUINE_CREATOR_BRIEF.md). This file is a placeholder until then.

**Phase 2 — Research**
Astra reads the brief, [seed_games.txt](seed_games.txt), and [exclusions.txt](exclusions.txt), then researches creators in batches, logging each search in [search_history.csv](search_history.csv).

**Phase 3 — Recording**
Astra records creator evidence (channels, links, evidence URLs, contact info, etc.) into [creators.csv](creators.csv).

**Phase 4 — Processing**
Python scripts in [scripts/](scripts/) deduplicate creators, validate the data, and calculate deterministic fit scores/tiers.

**Phase 5 — Human review**
A human reviews S/A-tier and high-priority creators before any outreach happens.

## Press database

Alongside the creator DB, `press/` holds a database of journalists (`journalists.csv`) and outlets (`outlets.csv`) to pitch the press kit to before Steam Next Fest. It covers indie sites, major outlets, Next Fest roundup writers, podcasts and newsletters, and uses the same evidence standard as the creator DB.

- **Rules and batch format:** [press/PRESS_RESEARCH_GUIDE.md](press/PRESS_RESEARCH_GUIDE.md)
- **Scripts:** `scripts/press_db.py` (check / stats / dedupe / import), `scripts/score_press.py` (recalc) and `scripts/validate_press.py`
- **Latest report:** [press/exports/press_batch_002_report.md](press/exports/press_batch_002_report.md) (185 outlets, 284 journalists)

## Outreach Desk (dashboard)

```powershell
powershell -ExecutionPolicy Bypass -File .\start_all.ps1   # starts the server + terminal picker
python tools/outreach_app.py                               # dashboard only: http://127.0.0.1:8765
```

`start_all.ps1` is the quickest way in. It shows an ASCII-art menu, lists creators, journalists or outlets with quick filters, and opens a card per contact with every social and contact link. Press `M` to **message them**: email opens your mail app with the message filled in; a DM, Discord or form copies the message and opens the page. Press `L` to log it.

The Outreach Desk is a local React dashboard for working through creators and press without any SQL. You can:
- filter contacts
- hit **Message them** (best public route first), or any of the contact's social buttons
- build a daily list
- copy emails and pre-filled, editable messages, or open them in your mail app
- log each contact with one keypress
- track replies, keys sent, coverage and due follow-ups

Settings live in `outreach/config.json` and message templates in `outreach/templates/`. Every action is appended to `outreach/outreach_log.csv`.

The dashboard runs on 127.0.0.1 only and **never sends anything**.

## Important safety/workflow rule

**Research and outreach are separate phases.** This project must NOT automatically send emails, DMs, Discord messages, or social posts. Astra should only collect publicly available business/contact information during the research phase. Any outreach is a manual, human-driven step that happens after Phase 5.

## Scripts

- `scripts/creator_db.py` — load, normalize, dedupe, and upsert creator records. Run with `check`, `dedupe`, or `stats`.
- `scripts/score_creator.py` — recalculate deterministic `fit_score` and `tier` for every row in `creators.csv`.
- `scripts/validate_data.py` — read-only validation report (malformed URLs, duplicates, impossible scores, missing data, etc.).
- `scripts/yt_harvest.py` — read-only YouTube discovery helper. It runs `search`, `channel`, `channels`, `about` (public About links and country) and `twitch` (TwitchTracker summary), plus `aggregate`, and caches results in `exports/harvest/`. Each evidence video comes with its uploader's channel ID straight from YouTube's page data.
- `exports/import_batch.py` — `import <batch.json> "<label>"` upserts reviewed candidates and derives the objective score components by a fixed rubric. `enrich` fills `Unknown` channel IDs on existing rows. `enrich-contacts` fills contact, country and Twitch fields from cached About and TwitchTracker data.

- `tools/build_creator_links.py` — exports every creator's public About-page links (socials, Discord, sites) to `exports/creator_links.csv`, which the Outreach Desk uses.

Batch reports live in `exports/batch_00N_report.md`, `exports/batches_004-016_report.md` and `exports/batches_017-019_report.md`. Related games found during research are listed in `exports/discovered_games.md`; `seed_games.txt` stays unchanged.

See [requirements.txt](requirements.txt) for dependencies (standard library only, currently).
