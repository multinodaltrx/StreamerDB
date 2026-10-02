# Batch 002 — report

Research only. No outreach happened; `outreach_status` is blank for every row. Report date: 2026-10-02.

Creators C0101–C0200: mostly single-Tier-1 or Tier-1 + Tier-2 creators who were active recently.

## Summary

| Metric | Value |
|---|---|
| Records in batch | 100 |
| New creators discovered this run | 100 |
| Duplicates skipped / merged | 0 merged at import (see funnel for same-creator channels skipped) |
| Validation issues (`validate_data.py`) | 0 |
| S-tier | 0 |
| A-tier | 7 |
| B-tier | 89 |
| C-tier | 4 |
| High priority | 0 |
| Creators with a public business email | 5 |

## Top 10 candidates

| ID | Creator | Score | Tier | YouTube subs | Comparable games | Public contact |
|---|---|---|---|---|---|---|
| C0169 | [YDU Games](https://youtube.com/@ydugames) | 79 | A | 353 | Quarantine Zone; Contraband Police; Death and Taxes; Security 51 | Unknown |
| C0170 | [Egg Ezra](https://youtube.com/@eggezra) | 74 | A | 2,680 | That's Not My Neighbor; Death and Taxes | Public business email |
| C0127 | [MoreAnt](https://youtube.com/@moreant) | 73 | A | 338,000 | That's Not My Neighbor; Fears to Fathom | Unknown |
| C0131 | [Kahli Plays Games](https://youtube.com/@kahliplaysgames) | 73 | A | 11,400 | Papers, Please | Public business email |
| C0103 | [Britani](https://youtube.com/@britani) | 72 | A | 255,000 | That's Not My Neighbor; Fears to Fathom | Unknown |
| C0163 | [BaerTaffy](https://youtube.com/@baertaffy) | 71 | A | 153,000 | Papers, Please | Public business email |
| C0186 | [fatnap](https://youtube.com/@ayofatnap) | 71 | A | 116,000 | Quarantine Zone | Unknown |
| C0101 | [LightskinNightmare](https://youtube.com/@lightskinnightmare) | 69 | B | 373,000 | That's Not My Neighbor; Fears to Fathom | Unknown |
| C0130 | [Rebecca's Pixel Quest](https://youtube.com/@rebeccaspixelquest) | 69 | B | 2,730 | Papers, Please | Unknown |
| C0192 | [YanSlays](https://youtube.com/@yanslays) | 69 | B | 49,900 | Quarantine Zone | Unknown |

## Search clusters

- **Strongest:** That's Not My Neighbor and Contraband Police single-game coverage.
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
