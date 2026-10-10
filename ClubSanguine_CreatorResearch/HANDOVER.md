# HANDOVER — Club Sanguine creator research

**Read this before doing anything.** Last updated 2026-10-10 by the previous agent. The repository files are the source of truth. If anything here disagrees with the data, trust the data: run the status commands in section 3 first.

## 1. What this project is

We are building an evidence-backed database of YouTube/Twitch creators whose audiences would enjoy **Club Sanguine**, an indie "Papers, Please meets supernatural nightclub bouncer" game. The owner is Omar (omar.t@xeleration.net).

Read these, in order:

1. `CLUB_SANGUINE_CREATOR_BRIEF.md` — the game, target audience, size and activity preferences, evidence and contact rules, and the scoring weights.
2. `ASTRA_INSTRUCTIONS.md` — the research-agent rules: batch workflow and end-of-batch report fields.
3. `seed_games.txt` and `exclusions.txt`.
4. `tools/REVIEW_RUBRIC.md` — how candidates are judged in practice.
5. `exports/batches_004-016_report.md` — the latest run report.

**MODE: RESEARCH ONLY.**
- Never email, DM, post, submit forms, message Discord, or request Steam keys.
- Never change `outreach_status`.
- Collect only publicly published contact routes.
- Never bypass YouTube's sign-in/captcha email gate, and never guess emails.
- Unverifiable data is written as `Unknown`. Never fabricate metrics, URLs, contacts, countries or game coverage.

## 2. Current state (2026-10-10)

`creators.csv` has **1,598 creators** (C0001–C1598, Batches 001–016). `validate_data.py` reports 0 issues, every row has evidence, and every tier matches the scorer.

| Metric | Value |
|---|---|
| Tiers | S 6 · A 185 · B 1,024 · C 383 · high priority 14 |
| Contact routes | 893 YouTube-gated business email · 193 public email · 170 Discord / website · 266 social profile only · 76 Unknown |
| Twitch | 883 rows have a Twitch URL; only 42 have TwitchTracker average viewers (see known issues) |
| Searches logged | 506 rows in `search_history.csv` |

**Where things stand:**
- **Last batch:** Batch 016 (98 rows). The next import should start at **Batch 017**.
- **Review queue:** chunk 0 in `exports/review_log/` is a reconstructed list of 798 already-rejected channels; it keeps them from being re-reviewed. **164 new candidates** from search plan 6 are ready to review. Start with `python tools/review.py next 82 --quiet`, which creates chunk 1.
- **Outreach:** not started. The owner still needs to review S/A and high-priority creators.

### Decisions the owner already made (don't re-ask)

- **Scale:** the owner wanted as many creators as possible. Targets went 300 → 600 → 1,500, and all were reached. Don't start new discovery runs without being asked.
- **Contact rule:** accept new creators only if they show **at least one public contact route**. That means:
  - an email in the channel description
  - YouTube's "View email address" gate (`email_gated`)
  - About-page links: Discord, website, link-in-bio or socials

  Patreon, merch and Steam links alone don't count.
- **Twitch:** covered via Twitch links on creators' YouTube About pages, plus TwitchTracker metrics. Twitch-only discovery needs official Twitch API keys from the owner. **None have been provided.**
- **Size:** the preferred range is 1K–500K YouTube subscribers.
  - Creators over 500K are allowed only with 2+ Tier-1 games, recorded as a "size exception" in notes.
  - Creators over 3M are always rejected, and so are second channels of 3M+ creators.
- **Language:** English-language content. A creator's country doesn't matter.
- **Git:** the repo is **private** at `https://github.com/multinodaltrx/StreamerDB.git` (branch `master`). The owner chose to keep creator data in it.
  - `.gitignore` excludes `exports/harvest/` (the scrape cache), `.claude/`, and caches and secrets.
  - Commit or push only when asked.
  - If the repo ever becomes public, the contact data must come out of git history.

## 3. Status commands (run first)

Run from `ClubSanguine_CreatorResearch/`. On Windows, always set `PYTHONIOENCODING=utf-8`.

```bash
export PYTHONIOENCODING=utf-8
python scripts/creator_db.py check      # schema + row count
python scripts/creator_db.py stats      # tiers / status / platform / high-priority
python scripts/validate_data.py         # read-only data-quality report (expect 0 issues)
python tools/review.py summary          # cached candidates, filter reasons, ready-to-review count
```

## 4. Layout

| Path | What |
|---|---|
| `creators.csv` | The database (40 columns, schema in `scripts/creator_db.py:FIELDNAMES`) |
| `search_history.csv` | Every search: query, filter, results, new and qualified counts |
| `scripts/creator_db.py` | `check` / `stats` / `dedupe` / `upsert`. Dedupe keys, in order: channel ID → Twitch username → profile URL → name. `Unknown` is never used as a key; merges only fill `Unknown` or empty fields. |
| `scripts/score_creator.py` | `recalc`: deterministic fit_score (sum of 8 components) and tier (S ≥85, A ≥70, B ≥55, C ≥40) |
| `scripts/validate_data.py` | Read-only validator |
| `scripts/yt_harvest.py` | Read-only YouTube/TwitchTracker fetcher with cache (see below). `GAMES` is the title-matching list (seed tiers 1–3 plus "related" games). |
| `exports/import_batch.py` | `import <json> "Batch NNN"` (builds rows; objective score components come from a fixed rubric) · `enrich` · `enrich-contacts` |
| `tools/review.py` | Hard filters plus chunked review (`summary` / `pending` / `next` / `show` / `decide`) |
| `tools/import_pools.py` | Reviewed chunks → 100-row batches → import → dedupe → recalc → validate |
| `tools/pipeline.sh` | After new searches: aggregate → fetch channel pages → fetch About pages (3 workers each) |
| `tools/REVIEW_RUBRIC.md` | Reviewer rubric with examples |
| `exports/review_log/` | Frozen chunks, `pool_cK.json` (accepted) and `rejected_cK.json` |
| `exports/batch_NNN_candidates*.json` | Exactly what was imported per batch |
| `exports/*_report.md` | Batch reports (001, 002, 003, and combined 004–016) |
| `exports/discovered_games.md` | Related games used for expansion (the seed list is never edited) |
| `exports/harvest/` | **Local only (gitignored).** Cache of 470 searches, 5,525 channel pages, 3,335 About pages and 878 Twitch lookups. If it's missing, rebuild it with the commands below; everything is cached by ID. |

### `yt_harvest.py` commands

```bash
python scripts/yt_harvest.py search "\"Papers, Please\" gameplay" --sp EgIQAQ%3D%3D --pages 5   # [--force]
python scripts/yt_harvest.py channels UC... UC...     # channel page: subs, handle, recent uploads + ages, description
python scripts/yt_harvest.py about UC... UC...        # About panel: country, public links, email_gated flag
python scripts/yt_harvest.py twitch user1 user2       # TwitchTracker summary panel
python scripts/yt_harvest.py aggregate                # -> exports/harvest/candidates.json (channels with title-matched games)
```

Useful `--sp` values:

| Value | Meaning |
|---|---|
| `EgIQAQ%3D%3D` | Videos, by relevance |
| `EgQIBRAB` | Videos uploaded this year |
| `EgQIBBAB` | Videos uploaded this month |
| `CAISAhAB` | Videos, newest first |

## 5. How to continue (one discovery cycle)

1. **Search.** Write a query plan of `query|sp|pages|force` lines, with **LF line endings**, and loop it through `yt_harvest.py search`. Use query families that worked: `"<game>" gameplay / let's play / part 1 / stream`, plus newest and this-year filters.
   - **New seeds:** count recurring titles in accepted creators' recent uploads and pick the inspection / impostor / anomaly / odd-job ones. Add them to `GAMES` as `"related"` (this is how Animaly Bar, Shift at Midnight, Who's at the Door and others were found). Record them in `exports/discovered_games.md`, never in `seed_games.txt`.
2. **Fetch.** Run `bash tools/pipeline.sh <tag>`. It takes about 3 seconds per channel per worker. Run it in the background.
3. **Review.** Run `python tools/review.py next 90 --quiet`, then show and decide each chunk using `tools/REVIEW_RUBRIC.md`.
   - Previously this was done by parallel subagents, one per chunk, each told to read the rubric, `show K`, and `decide K` once.
   - That costs about 70K tokens per 90-line chunk, and acceptance runs about 40–65%.
   - Spot-check flagged or uncertain lines, especially "second channel of X", VOD channels, and creators with non-English descriptions.
4. **Import.** Back up `creators.csv` first, then run `python tools/import_pools.py 17 1 2` (Batch 017 onward, review_log chunks 1–2).
   - Afterwards, check any "merged into existing" rows. So far every merge has been a main/VOD pair sharing a Twitch username, which is correct.
5. **Log.** Append one `search_history.csv` row per query, then write a batch report with the ASTRA end-of-batch fields. The previous reports' generator logic is reproduced in their structure.
6. **Stop and report** to the owner after each discovery cycle.

## 6. Known issues and gotchas (all learned the hard way)

**Windows and scripting**
- **CRLF:** text files written by Python on Windows get `\r\n`. A stray `\r` broke URLs and filenames twice. Always `.strip()` IDs, and write plan files with `newline="\n"`. `yt_harvest.py` now strips its arguments.
- **Regex escaping:** when generating regex source code through shell heredocs or f-strings, `\b` turned into a backspace character (`\x08`) and silently broke matching. Build it with `chr(92) + "b"` in a script file, then test `match_games()` on sample titles.
- **Encoding:** always set `PYTHONIOENCODING=utf-8`, or non-Latin titles crash prints. Never pass HTML through argv; write it to a file.

**Title matching**
- **Ambiguous game names:** "Not Tonight" (songs), "Death and Taxes" (an MTG deck), "Subliminal", "Kiosk", "Night Plane" and others are in `AMBIGUOUS` and need gaming-context words in the title.
- **Comparison titles:** "Papers, Please but…", "Europe's Papers Please" and "Papers-Please-inspired" are *not* coverage; `match_games()` skips them.

**External data sources**
- **TwitchTracker** rate-limits hard (HTTP 429). 805 of 878 lookups failed, and a slow retry an hour later was still blocked. The period behind its "Average viewers" figure isn't labelled in the static HTML, so treat it as approximate. Twitch follower counts aren't available this way.
- **YouTube business emails** sit behind sign-in. `email_gated=True` means one exists; a human must reveal it manually. Do not automate this.
- **WebFetch can't read YouTube or Twitch,** because they're JavaScript-only. Use `yt_harvest.py`, which parses the `ytInitialData` JSON and the innertube continuations.

**Review process**
- **`decide` once per chunk.** It now refuses to overwrite `pool_cK.json`.
- **Same-creator channels:** dedupe catches shared Twitch usernames, and `import_pools.py` skips shared business emails. Unlinked "X VODS" or second channels can still slip through.
- **`last_active_date`** is derived from YouTube's relative "N days ago" label at fetch time.
- **The previous scratchpad was wiped,** which is why tools now live in `tools/` and logs in `exports/review_log/`. Keep all state inside the repo.

## 7. Suggested next steps (ask the owner which)

1. Help the owner review S/A and high-priority creators. For example, produce a shortlist sorted by fit_score with contact routes.
2. Review the 164 ready plan-6 candidates (chunks 1–2), then import them as Batch 017+.
3. Retry Twitch metrics once TwitchTracker stops rate-limiting:
   ```bash
   python scripts/yt_harvest.py twitch <users>    # delete the 429-cached files in exports/harvest/twitch/ first
   python exports/import_batch.py enrich-contacts
   ```
   Or, with Twitch API keys from the owner, add proper follower and viewer counts plus Twitch-only discovery.
4. Before outreach, deduplicate remaining second channels by hand, and refresh activity and subscriber data for the shortlist.
