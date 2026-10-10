# Press research guide (journalists and outlets)

This is for any agent or person adding to `press/outlets.csv` and `press/journalists.csv`. Read `CLUB_SANGUINE_CREATOR_BRIEF.md` sections 1–9 first, because the game and its comparable games are the same as for creators.

**Goal:** before **Steam Next Fest in February 2027**, find journalists and outlets whose published work shows they cover games like Club Sanguine. Coverage makes the game easier to find, so creators come across it on their own.

## Mode: research only

- Never email, DM, post, submit forms or request anything.
- Record **published** contact routes only:
  - an outlet's tips@ / press@ / submissions@ address
  - a "submit your game" page
  - an email a journalist publishes on their author page, personal site or social bio
  - their public social profile
- **Never guess emails.** No firstname.lastname@ patterns, and no email-finder tools.
- Don't use paywalled or login databases such as Muck Rack, Cision or LinkedIn search.
- Anything you can't verify is `Unknown`. Never invent URLs, dates, games or contacts.

## What counts as evidence

Evidence is a **direct URL to a published piece** by that journalist or outlet that covers a comparable game, a Next Fest roundup or a demo roundup. Every row needs `evidence_url_1`. Prefer 2–3 evidence URLs.

Comparable games:
- Tier 1: Papers, Please · That's Not My Neighbor · Not Tonight · Contraband Police · Quarantine Zone
- Tier 2: The Mortuary Assistant · Killer Frequency · Buckshot Roulette · I'm on Observation Duty · Death and Taxes
- Tier 3: Inscryption · World of Horror · Fears to Fathom · Scarlet Hollow · Cult of the Lamb
- Related (see `exports/discovered_games.md`): No, I'm Not a Human · Shift at Midnight · Animaly Bar · The Exit 8 · Beholder · Return of the Obra Dinn · Strange Horticulture · Scrutinized · Security 51 · Who's at the Door · Kiosk · and others

Write game names **exactly** as above, separated by `; `. The scorer matches seed names after stripping punctuation.

## Search approach

Use comparable games as fingerprints, then expand to the outlet's other writers:
- `"That's Not My Neighbor" review` · `"Quarantine Zone" preview` · `games like Papers, Please` · `"No, I'm Not a Human" review` · `"Mortuary Assistant" review`
- `Steam Next Fest best demos` (2024 / 2025 / 2026, all editions) · `Next Fest horror demos` · `indie horror demos you should play`
- `site:<outlet>` searches to find an outlet's writers on those games

On an outlet you find, look for its **contact / about / submit / tips** page and record what it says, such as "accepts indie submissions via form" or "no unsolicited keys".

## Batch JSON format

Write `press/exports/research/<segment>.json` containing `{"outlets": [...], "journalists": [...]}`. Use the field names from `scripts/press_db.py` (`OUTLET_FIELDS` / `JOURNALIST_FIELDS`). Leave out `*_id`, `outlet_ids`, every `*_score` except the two judgement scores, `fit_score`, `tier` and `public_contact_method`; the scripts derive those.

**Outlet:**
- `name`
- `type`, which must be one of: `Indie site/blog`, `Major outlet`, `Newsletter`, `Podcast`, `YouTube press`, `Roundup/curator`
- `url`, `submission_url`, `public_email`, `social_url`
- `press_policy_notes`, `audience_note`
- `comparable_coverage`
- `evidence_url_1..3`
- `nextfest_coverage` (`Yes` / `Demo coverage` / `No` / `Unknown`), `nextfest_url`
- `last_relevant_article_date` (YYYY-MM-DD or YYYY-MM)
- `region_language`
- `focus_score` (0–15), `reach_score` (0–10)
- `notes`, `source_query`

**Journalist:**
- `name`
- `outlets`: outlet names exactly as in the outlets list, `; `-separated. Include every outlet you list for a journalist as an outlet record too.
- `role` (`Staff` / `Freelance` / `Editor` / `Owner` / `Host`), `beat`
- `author_page_url`, `public_email`, `social_url`, `contact_preference`
- `games_covered`
- `evidence_url_1..3`
- `nextfest_coverage`, `nextfest_url`
- `last_article_date`
- `region_language`
- `focus_score`, `reach_score`
- `notes`, `source_query`

## Judgement scores

`focus_score` (0–15):

| Score | Who |
|---|---|
| 13–15 | Mostly indie / horror / weird sims; repeatedly covers inspection, deduction or anomaly games |
| 9–12 | Regular indie coverage alongside other beats |
| 5–8 | General games coverage with occasional indie |
| 0–4 | Mostly AAA, hardware or news |

`reach_score` (0–10):
- **10:** a realistic, high-impact target. That means a mid-sized indie-focused outlet, or a writer at a major outlet who regularly covers small indies.
- **6–8:** a niche but engaged audience.
- **3–5:** very small, or a major outlet that rarely covers small indies.
- **0–2:** tiny or inactive.

## English only

For this campaign, record only English-language outlets and writers.
