# Batch 001 — report

Research only. No outreach happened; `outreach_status` is blank for every row. Report date: 2026-10-02.

This batch completes Discovery Batch 001: C0001–C0014 from the 2026-09-12 session plus 86 new creators (C0015–C0100). It holds the strongest candidates, because the review ran most-comparable-first.

## Summary

| Metric | Value |
|---|---|
| Records in batch | 100 |
| New creators discovered this run | 86 |
| Duplicates skipped / merged | 0 merged at import (see funnel for same-creator channels skipped) |
| Validation issues (`validate_data.py`) | 0 |
| S-tier | 3 |
| A-tier | 44 |
| B-tier | 51 |
| C-tier | 2 |
| High priority | 5 — C0021 Jezabelle Live, C0029 Neyreyan, C0035 RTGame Stream Archive, C0059 NIRDSTUFF, C0095 Synissta |
| Creators with a public business email | 16 |

## Top 10 candidates

| ID | Creator | Score | Tier | YouTube subs | Comparable games | Public contact |
|---|---|---|---|---|---|---|
| C0002 | [DieDevDie](https://youtube.com/@diedevdie) | 92 | S | 669,000 | That's Not My Neighbor; Contraband Police; Quarantine Zone | Public community/contact page |
| C0021 | [Jezabelle Live](https://youtube.com/@jezabellelive) | 90 | S | 35,800 | Quarantine Zone; That's Not My Neighbor; The Mortuary Assistant; Fears to Fathom | Public business email |
| C0024 | [Floydson](https://youtube.com/@floydsonyt) | 86 | S | 998,000 | Contraband Police; Papers, Please; Cult of the Lamb; Inscryption; Strange Horticulture | Public business email |
| C0059 | [NIRDSTUFF](https://youtube.com/@nirdstuff) | 84 | A | 17,000 | Quarantine Zone; Papers, Please; Security 51 | Public business email |
| C0035 | [RTGame Stream Archive](https://youtube.com/@rtgamestreamarchive) | 82 | A | 201,000 | Not Tonight; Papers, Please | Public business email |
| C0017 | [Gab Smolders](https://youtube.com/@gabsmolders) | 81 | A | 1,310,000 | Quarantine Zone; That's Not My Neighbor; I'm on Observation Duty; Buckshot Roulette; Killer Frequency; The Mortuary Assistant; Fears to Fathom; Scarlet Hollow; Alternate Watch | Unknown |
| C0029 | [Neyreyan](https://youtube.com/@neyreyan) | 81 | A | 9,800 | Contraband Police; Papers, Please; Security 51 | Public business email |
| C0062 | [Jozzoh](https://youtube.com/@jozzoh) | 81 | A | 37,000 | Quarantine Zone; The Mortuary Assistant; Fears to Fathom | Public business email |
| C0001 | [MetalCanyon](https://youtube.com/@metalcanyon) | 80 | A | 81,800 | Papers, Please; Contraband Police | Unknown |
| C0009 | [Insym](https://youtube.com/@insym) | 80 | A | 1,240,000 | Not Tonight; Quarantine Zone; Security 51 | Unknown |

## Search clusters

- **Strongest:** Papers, Please and That's Not My Neighbor (with "part 1" and "this year" variants).
- **Weakest:** Tier 3 expansion searches (Inscryption, World of Horror, Fears to Fathom, Scarlet Hollow, Cult of the Lamb) and the "Not Tonight" variants. Tier 3 results are mostly generic horror or variety channels and largely sit unreviewed in the backlog, and "Not Tonight" matches many music videos.

## Run-level discovery funnel (shared by Batches 001–003)

All three batches came from one discovery run on 2026-10-02. Candidates were reviewed in strength order (most Tier-1 comparables first) and then split into batches, so per-batch rejection counts can't be separated. These are run totals:

| Step | Count |
|---|---|
| YouTube searches run (15 seeds + 5 related titles, several query variants each) | 90 |
| Channels with a video whose title names a comparable game | 1,594 |
| Channel pages fetched (subscribers, latest uploads, description) | 1,545 |
| Removed by hard filters (no upload in ~90 days, over 500K subs without 2+ Tier-1 games or over 3M at any level, no-commentary label, non-English, clip channel) | about 665 (counted with the final matcher) |
| Reviewed manually | 565 |
| Accepted | 293 |
| Rejected on manual review | 272 (incl. 1 dropped after evidence re-check) |
| Duplicates skipped (same creator, second channel) | 2 (Insym VODS = C0009; Fir Plus = Fir Unlisted) |
| Merged into existing rows at import | 0 |
| Passed filters but not yet reviewed (backlog) | about 240 |

Main manual rejection reasons: off-genre focus such as AAA, Roblox, Fortnite, MMO, sports or card games (81); walkthrough / no-commentary format (37); false title matches, e.g. songs called "Not Tonight" or the Magic: The Gathering deck "Death and Taxes" (29); too small or sparse (21); non-English (18); fan, clip or reupload channels (17); very large creators (4).

**Verification:**
- Every evidence URL comes from YouTube's own page data, which names the uploading channel.
- An oEmbed spot-check of 32 random accepted creators matched the uploader in 32 of 32 cases.
- Titles that only use a seed game as a comparison ("Papers Please but…", "Europe's Papers Please") were removed as coverage, and the matcher in `scripts/yt_harvest.py` now ignores them.

## Recommendations for the next batch

1. **Review the backlog first.** About 240 channels already pass the hard filters and are cached in `exports/harvest/`. Run the review step on them before doing new searches.
2. **Enrich the S/A tiers and the 5 high-priority creators.** Twitch metrics, country and most business emails are `Unknown`, because YouTube shows business emails only behind a captcha and Twitch pages are JavaScript-only. A browser-capable pass over the About and Twitch pages would raise contact scores.
3. **Expand related-game queries:** Security 51, Shift at Midnight, Scrutinized, Diapers Please, Animaly Bar and Japan Stigmatized Property. These appeared repeatedly in accepted creators' recent uploads (see `exports/discovered_games.md`).
4. **Mine Tier 3 last.** Tier 3 searches produced many generic horror channels, as the brief warned. Accept Tier 3-only creators only when they also cover inspection, deduction or job-sim titles.
5. **Use more specific queries for Not Tonight and Death and Taxes,** such as `"Not Tonight" bouncer` and `"Death and Taxes" Placeholder Gameworks`. Both names collide with songs and a card-game deck.
