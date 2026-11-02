# HANDOVER — Club Sanguine creator and press research

**Read this before doing anything.** Last updated 2026-10-10 by the previous agent. The repository files are the source of truth. If anything here disagrees with the data, trust the data: run the status commands in section 3 first.

## 1. What this project is

We are building evidence-backed databases for **Club Sanguine**, an indie "Papers, Please meets supernatural nightclub bouncer" game. The owner is Omar (omar.t@xeleration.net). There are two databases:

- **Creators:** YouTube/Twitch creators whose audiences would enjoy the game, in `creators.csv`.
- **Press:** journalists and outlets to pitch the press kit to before **Steam Next Fest, February 2027**, in `press/`. Coverage should help creators find the game on their own.

The owner works through both from the **Outreach Desk**, a local dashboard (see section 7).

Read these, in order:

1. `CLUB_SANGUINE_CREATOR_BRIEF.md` — the game, target audience, size and activity preferences, evidence and contact rules, and the scoring weights.
2. `ASTRA_INSTRUCTIONS.md` — the research-agent rules: batch workflow and end-of-batch report fields.
3. `seed_games.txt` and `exclusions.txt`.
4. `tools/REVIEW_RUBRIC.md` — how candidates are judged in practice.
5. `exports/batches_004-016_report.md` — the latest creator run report.
6. `press/PRESS_RESEARCH_GUIDE.md` and `press/exports/press_batch_001_report.md` — the press DB rules and its first batch.

**MODE: RESEARCH (agents) + MANUAL OUTREACH (owner only).**
- Agents and tools never email, DM, post, submit forms, message Discord, or request Steam keys. The owner sends every message personally.
- The Outreach Desk only prepares messages and records what the owner did, in `outreach/outreach_log.csv`. Agents never write to that log on the owner's behalf.
- Never change `outreach_status` in `creators.csv`; outreach state lives only in the log.
- Collect only publicly published contact routes.
- Never bypass YouTube's sign-in/captcha email gate, and never guess emails.
- Unverifiable data is written as `Unknown`. Never fabricate metrics, URLs, contacts, countries or game coverage.

## 2. Current state (2026-10-10)

`creators.csv` has **1,798 creators** (C0001–C1798, Batches 001–019). `validate_data.py` reports 0 issues, every row has evidence, and every tier matches the scorer.

| Metric | Value |
|---|---|
| Tiers | S 7 · A 200 · B 1,160 · C 431 · high priority 15 |
| Contact routes | 990 YouTube-gated business email · 220 public email · 197 Discord / website · 313 social profile only · 78 Unknown |
| Socials | `exports/creator_links.csv` has 5,041 About-page links (Twitch, X, Bluesky, Instagram, TikTok, Discord, sites) for 1,592 creators |
| Twitch | 998 rows have a Twitch URL; only 77 have TwitchTracker average viewers (see known issues) |
| Searches logged | 650 rows in `search_history.csv` |

**Press DB** (`press/`, Press Batches 001–002, 2026-10-10). `validate_press.py` reports 0 issues.

| Metric | Value |
|---|---|
| Outlets | 185: 85 indie sites, 39 major outlets, 28 podcasts, 21 newsletters, 11 YouTube press, 1 curator. Tiers S 12 · A 16 · B 44 · C 72 · LT 41 |
| Journalists | 284. Tiers S 4 · A 10 · B 39 · C 107 · LT 124. 100 have Next Fest roundups on record |
| Contact routes | Outlets: 82 public email · 39 submission form · 30 social only. Journalists: 68 personal email; others reach through their outlet's email, form or social, which the Desk shows on their card |
| Searches logged | 394 rows in `press/search_history.csv` |

**Where things stand:**
- **Last batch:** Batch 019 (2 rows; 017 and 018 hold the other 198). The next import should start at **Batch 020**.
- **Review queue:** `exports/review_log/` holds chunk 0 (798 reconstructed rejections) and chunks 1–5 (412 reviewed: 202 accepted, 210 rejected). Nothing is waiting; a new cycle needs new searches (section 5).
- **Harvest cache:** rebuilt on this machine. It holds 1,721 channel pages and About pages for every creator in the DB plus all reviewed candidates. It's gitignored, so it's local only.
- **Outreach:** the Outreach Desk and `start_all.ps1` are built and tested, and the log is empty. The owner still needs to fill in `outreach/config.json` (`steam_url`, `press_kit_url`, `trailer_url`, `nextfest_start`).
- **Environment:** set up on 2026-10-10 with Python 3.12 (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`, which may not be on PATH in old shells) and Node 24 LTS (only needed to rebuild the dashboard UI).

### Decisions the owner already made (don't re-ask)

- **Press DB (2026-10-10):** a separate DB of journalists and outlets covering indie sites and blogs, major outlets, Next Fest roundup writers, and podcasts and newsletters. The target is **Next Fest, February 2027**.
- **Outreach tool:** a local web dashboard built with React, not a CLI or spreadsheet. The owner asked for something "more professional than an HTML page".
- **Creator DB to 3,000:** the next step, but **only after the owner explicitly approves it.**

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
python scripts/press_db.py check        # press schema + row counts
python scripts/press_db.py stats        # press types / tiers / contact routes
python scripts/validate_press.py        # read-only press report (expect 0 issues)
```

## 4. Layout

| Path | What |
|---|---|
| `creators.csv` | The database (40 columns, schema in `scripts/creator_db.py:FIELDNAMES`) |
| `search_history.csv` | Every search: query, filter, results, new and qualified counts |
| `scripts/creator_db.py` | `check` / `stats` / `dedupe` / `upsert`. Dedupe keys, in order: channel ID → Twitch username → profile URL → name. `Unknown` is never used as a key; merges only fill `Unknown` or empty fields. |
| `press/outlets.csv`, `press/journalists.csv` | Press DB (schemas in `scripts/press_db.py`: `OUTLET_FIELDS` / `JOURNALIST_FIELDS`) |
| `press/search_history.csv` | Every press search |
| `press/PRESS_RESEARCH_GUIDE.md` | Rules, evidence standard, JSON batch format and judgement-score rubric for press research |
| `press/exports/research/*.json` | Exactly what each press research segment produced (re-importable) |
| `scripts/press_db.py` | `check` / `stats` / `dedupe` / `import <batch.json> "<label>"` |
| `scripts/score_press.py` | `recalc`: 4 components derived from fields plus 2 judgement scores, tiers as for creators |
| `scripts/validate_press.py` | Read-only press validator |
| `start_all.ps1` | One-click launcher: starts the server if needed, then a terminal picker (ASCII art, lists, contact cards, a "message them" key, logging) |
| `tools/outreach_app.py` | The Outreach Desk server: 127.0.0.1 only, standard library, serves `dashboard/dist` plus the JSON API (`/api/data`, `/api/find`, `/api/contact`, `/api/stats`, `/api/log`, `/api/reveal`) |
| `tools/build_creator_links.py` | Exports every creator's About-page links to `exports/creator_links.csv`. `--missing` lists creators without a cached About page |
| `tools/run_plan.sh` | Runs a search plan file through `yt_harvest.py search` |
| `dashboard/` | React + TypeScript + Mantine UI source. `dist/` is committed, so Node is only needed to change the UI |
| `outreach/outreach_log.csv` | Append-only log of every action the owner records. A contact's status is its latest row |
| `outreach/revealed_contacts.csv` | Gated YouTube emails the owner revealed by hand and saved in the dashboard |
| `outreach/config.json` | Steam / press-kit / trailer URLs, Next Fest dates, signature, daily target, follow-up days |
| `outreach/templates/*.txt` | Message templates. `Subject:` on the first line; `{name}`, `{game}`, `{evidence_url}`, `{steam_url}`, `{press_kit_url}` and any other config key as placeholders |
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
| `exports/*_report.md` | Batch reports (001, 002, 003, combined 004–016, combined 017–019) |
| `exports/creator_links.csv` | Every public About-page link per creator (`creator_id,title,url`); rebuilt by `tools/build_creator_links.py` |
| `exports/discovered_games.md` | Related games used for expansion (the seed list is never edited) |
| `exports/harvest/` | **Local only (gitignored).** Rebuilt on 2026-10-10 with plans 7–9: 1,721 channel pages and 2,402 About pages, including every creator in the DB. The older cache from runs 1–2 is not on this machine. If it's missing, rebuild it with the commands below; everything is cached by ID. |

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

1. **Search.** Write a query plan of `query|sp|pages|force` lines, with **LF line endings**, in `exports/review_log/plans/planN.txt`, and run `bash tools/run_plan.sh <plan>`. Plans 7–9 are there as examples. Use query families that worked: `"<game>" gameplay / let's play / part 1 / stream`, plus newest and this-year filters.
   - **New seeds:** count recurring titles in accepted creators' recent uploads and pick the inspection / impostor / anomaly / odd-job ones. Add them to `GAMES` as `"related"` (this is how Animaly Bar, Shift at Midnight, Who's at the Door and others were found). Record them in `exports/discovered_games.md`, never in `seed_games.txt`.
2. **Fetch.** Run `bash tools/pipeline.sh <tag>`. It takes about 3 seconds per channel per worker. Run it in the background.
3. **Review.** Run `python tools/review.py next 90 --quiet`, then show and decide each chunk using `tools/REVIEW_RUBRIC.md`.
   - Previously this was done by parallel subagents, one per chunk, each told to read the rubric, `show K`, and `decide K` once.
   - That costs about 70K tokens per 90-line chunk, and acceptance runs about 40–65%.
   - Spot-check flagged or uncertain lines, especially "second channel of X", VOD channels, and creators with non-English descriptions.
4. **Import.** Back up `creators.csv` first, then run `python tools/import_pools.py 20 6 7` (Batch 020 onward, review_log chunks 6 and up; chunks 1–5 are already imported). Then run `python tools/build_creator_links.py` so the new creators' socials reach the Desk.
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

## 7. Press DB and Outreach Desk

**Start everything:** `powershell -ExecutionPolicy Bypass -File .\start_all.ps1`, or right-click → Run with PowerShell. It finds Python, builds `dashboard/dist` if it's missing, starts the server hidden if it isn't already running, and opens the terminal picker:
- **Menu:** `D` dashboard · `C` creators · `J` journalists · `O` outlets · `T` today · `F` follow-ups due · `A` everyone · `Q` quit (offers to stop the server).
- **Lists** take a quick filter (search, tiers, email-ready, include contacted), then show a 15-row paged table.
- **Contact card keys:**
  - `M` **message them**: opens the best route. For email it opens your mail app with the message pre-filled. For a DM, Discord or form, it copies the message and opens the page. For a gated YouTube email, it opens the About page and lets you save the email you reveal.
  - `1–n` open any social or link · `E1–3` open evidence
  - `V`/`C`/`A`/`T` view message, copy message, copy email, switch template
  - `L` log contacted · `K` skip · `R` replied · `I` interested · `Y` key sent · `G` covered · `D` declined · `U` undo · `O` note
  - `N`/`P` next/prev · `B` back
- **Best-route order:** public email → outlet email (for journalists) → gated YouTube About → Discord → submission or contact form → social DM → website.

**Run the dashboard only:** `python tools/outreach_app.py`. It opens http://127.0.0.1:8765. Restart it after any change to `tools/outreach_app.py`.

What it does:
- **Reach panel:** each contact's drawer has a big **Message them** button using the same best-route logic as above, then icon buttons for every public social and contact link.
- **Tabs:** Creators · Journalists · Outlets · Today · Follow-ups · Pipeline.
- **Filters:** tier, status, contact route, games, subscribers, activity, outlet type and Next Fest writers.
- **Build today's list** queues the top N not-yet-contacted contacts from the current filter.
- **Work through** opens a drawer with links, evidence, a copyable or editable filled message, and an "Open in mail app" button.
- **Shortcuts:** `m` logs a contact and moves to the next one; `j`/`k` next/prev; `c` copy message; `e` copy email; `s` skip.
- **Follow-ups** appear automatically `follow_up_days` after a contact if there's no reply.
- **Deep links:** `#C0002` opens a contact directly.
- **UI changes:** `cd dashboard && npm install && npm run build`. Use `npm run dev` for hot reload; it proxies `/api` to the Python server.

**Adding press records:** follow `press/PRESS_RESEARCH_GUIDE.md` and write a JSON batch. Then run:
1. `python scripts/press_db.py import <file> "Press Batch NNN (<segment>)"`
2. `python scripts/score_press.py recalc`
3. `python scripts/validate_press.py`

Log the queries in `press/search_history.csv` and write a report in `press/exports/`.

**Press dedupe gotchas (learned in Batch 001):**
- **Shared hosting:** many outlets live on YouTube, Substack, Apple Podcasts, Spotify and similar platforms. Those are keyed on the full URL, not the domain (`SHARED_HOSTS`).
- **Co-hosts:** co-hosts share show pages and social accounts, so a journalist URL match only counts when the first and last names agree (`names_compatible`).
- **List fields** (`outlets`, `games_covered`, `comparable_coverage`) are unioned on merge.
- **Partial dates** (`YYYY-MM` / `YYYY`) are scored as the first of the month or year.

**Timeline to Next Fest (February 2027):**

| When | What |
|---|---|
| Oct–Nov 2026 | Fill in `outreach/config.json`. Review top press and creator targets in the dashboard. Open the evidence of Batch 002 records marked "seen via listing" (see `press/exports/press_batch_002_report.md`) |
| Early Jan 2027 | Re-verify the top ~50 press targets (still at the outlet, recent bylines) |
| Mid-Jan 2027 | Press pitches go out, about 3–4 weeks before the fest |
| 1–2 weeks before the fest | Creator outreach (`1_creator_email` / `2_creator_dm`) |
| During the fest | `4_nextfest_reminder` to press and creators, then `5_follow_up` from the Follow-ups tab |

## 8. Suggested next steps (ask the owner which)

1. **Expand the creator DB to about 3,000.** Waiting on owner approval. The harvest cache is rebuilt, so this is new discovery cycles from Batch 020 (section 5). Plans 7–9 yielded about 0.5 accepted creators per search, so about 1,200 more needs roughly 2,400 searches across new seed games.
2. **Press Batch 003:** Irish and NZ outlets, horror-film sites with a games section, and re-checking the writers who may have moved (Alice Bell, Katharine Castle, Alex McHugh). RPS, Eurogamer, Polygon, IGN, VG247, The Guardian, The Verge and Wired block automated reading. Their bylines came from OpenCritic, Wikipedia and Bluesky.
3. Help the owner review S/A and high-priority creators and press in the dashboard.
4. Retry Twitch metrics once TwitchTracker stops rate-limiting:
   ```bash
   python scripts/yt_harvest.py twitch <users>    # delete the 429-cached files in exports/harvest/twitch/ first
   python exports/import_batch.py enrich-contacts
   ```
   Or, with Twitch API keys from the owner, add proper follower and viewer counts plus Twitch-only discovery.
5. Before outreach, deduplicate remaining second channels by hand, and refresh activity and subscriber data for the shortlist.

## 9. Update 2026-11-02: press kit, IGN-style outlets, Gmail profile

- **Press kit** lives in `press_kit/` (`Club_Sanguine_Press_Kit.pdf`, factsheet, verified-outlets list, IGN handoff, copy, tracker). There is no public link yet, so `press_kit_url` is empty. Templates use `{press_kit_note}` ("PDF attached"). Gmail compose links can't attach files: the Desk's **Show press kit PDF to attach** button selects the PDF in Explorer so the owner can drag it in. When a public Drive link exists, set `press_kit_url` and edit `press_kit_note`.
- **Press Batch 003** (`press/exports/research/b003_press_kit_outlets.json`): IGN got its editorial contact form; Alpha Beta Gamer and Wishlist or Not were added; Indie Games Plus (O0016) was merged. IGN's `trailers@`/`indies@`/`videowire@` addresses are community-reported and **unverified**, so they are in notes only. New rows have no comparable-game evidence yet (tiers Long Tail).
- **Template `6_trailer_submission`**: non-exclusive trailer submission for IGN-style desks. Never claim exclusivity.
- **Gmail:** compose links open in the Chrome profile signed in as `config.gmail_account` (found from Chrome's Local State, here "Profile 2"; fallback `gmail_chrome_profile`). The dashboard does this through `/api/open_mail`, so **restart `tools/outreach_app.py` after pulling**. `start_all.ps1` does the same via `Open-Mail`.

- **Trailer MP4** (`trailer_file` in config, 143 MB, in Downloads): too big for Gmail (25 MB) and GitHub (100 MB), so it is NOT in the repo. Emails still link `trailer_url` (YouTube) until the owner supplies a public link to this file. The Desk has a **Show trailer MP4** button.
- **IGN Middle East** (the 'IGN Arabia' edition, run by T-Break) was added as O0188 via Press Batch 003b; its only editorial route is editor@tbreak.com ('Review' in subject for demos). me.ign.com was not readable.
