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

## Important safety/workflow rule

**Research and outreach are separate phases.** This project must NOT automatically send emails, DMs, Discord messages, or social posts. Astra should only collect publicly available business/contact information during the research phase. Any outreach is a manual, human-driven step that happens after Phase 5.

## Scripts

- `scripts/creator_db.py` — load, normalize, dedupe, and upsert creator records. Run with `check`, `dedupe`, or `stats`.
- `scripts/score_creator.py` — recalculate deterministic `fit_score` and `tier` for every row in `creators.csv`.
- `scripts/validate_data.py` — read-only validation report (malformed URLs, duplicates, impossible scores, missing data, etc.).
- `scripts/yt_harvest.py` — read-only YouTube discovery helper. It runs `search`, `channel`, `channels`, `about` (public About links and country) and `twitch` (TwitchTracker summary), plus `aggregate`, and caches results in `exports/harvest/`. Each evidence video comes with its uploader's channel ID straight from YouTube's page data.
- `exports/import_batch.py` — `import <batch.json> "<label>"` upserts reviewed candidates and derives the objective score components by a fixed rubric. `enrich` fills `Unknown` channel IDs on existing rows. `enrich-contacts` fills contact, country and Twitch fields from cached About and TwitchTracker data.

Batch reports live in `exports/batch_00N_report.md`. Related games found during research are listed in `exports/discovered_games.md`; `seed_games.txt` stays unchanged.

See [requirements.txt](requirements.txt) for dependencies (standard library only, currently).
