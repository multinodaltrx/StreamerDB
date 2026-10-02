# Batch 003 — report

Research only. No outreach happened; `outreach_status` is blank for every row. Report date: 2026-10-02.

Creators C0201–C0307: mostly single Tier-2 (Killer Frequency, I'm on Observation Duty, Death and Taxes, Buckshot Roulette) and smaller channels. This is the long-tail end of the run.

## Summary

| Metric | Value |
|---|---|
| Records in batch | 107 |
| New creators discovered this run | 107 |
| Duplicates skipped / merged | 0 merged at import (see funnel for same-creator channels skipped) |
| Validation issues (`validate_data.py`) | 0 |
| S-tier | 0 |
| A-tier | 4 |
| B-tier | 71 |
| C-tier | 32 |
| High priority | 0 |
| Creators with a public business email | 12 |

## Top 10 candidates

| ID | Creator | Score | Tier | YouTube subs | Comparable games | Public contact |
|---|---|---|---|---|---|---|
| C0232 | [FunkyFrogPlays](https://youtube.com/@funkyfrogplays) | 76 | A | 357,000 | Killer Frequency; The Mortuary Assistant; No, I'm Not a Human | Public business email |
| C0206 | [Chriz zirhC](https://youtube.com/@chriz_zirhc) | 71 | A | 6,280 | That's Not My Neighbor | Public business email |
| C0231 | [I Dream of Indie Games](https://youtube.com/@idreamofindie) | 71 | A | 63,200 | Death and Taxes; Killer Frequency; World of Horror | Public business email |
| C0216 | [MaJerati](https://youtube.com/@majerati) | 70 | A | 1,210 | That's Not My Neighbor | Unknown |
| C0215 | [NickDrivesSlow](https://youtube.com/@nickdrivesslow) | 69 | B | 59,600 | That's Not My Neighbor | Unknown |
| C0305 | [Woklz](https://youtube.com/@woklzyt) | 69 | B | 321 | Not Tonight | Public business email |
| C0204 | [Dekaff](https://youtube.com/@dekaif) | 68 | B | 191,000 | That's Not My Neighbor | Public business email |
| C0205 | [Cam2r Live](https://youtube.com/@cam2rlive) | 68 | B | 51,200 | That's Not My Neighbor | Unknown |
| C0207 | [AngelOfHorrorSim](https://youtube.com/@angelofhorrorsim) | 68 | B | 2,960 | That's Not My Neighbor | Unknown |
| C0222 | [Batkiller-Gaming](https://youtube.com/@batkillergaming) | 68 | B | 1,500 | That's Not My Neighbor | Public business email |

## Search clusters

- **Strongest:** Killer Frequency and I'm on Observation Duty.
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
