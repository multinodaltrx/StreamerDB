# Discovery run 3: Batches 017–019 report

Research only. No outreach happened, and `outreach_status` is blank for every row. Report date: 2026-10-10.

## Totals

| Metric | Value |
|---|---|
| Creators in `creators.csv` | **1,798** (was 1,598) |
| Added in this run | 200 (202 accepted; 2 were the same channel as an existing row, so they only filled its `Unknown` fields) |
| Validation issues (`validate_data.py`) | 0 |
| Tiers of the new rows | S 1 · A 15 · B 136 · C 48 |
| Tiers of the whole file | S 7 · A 200 · B 1,160 · C 431 |
| High priority (whole file) | 15 |
| New rows with a Twitch channel | 114 |

## How they were found

- **Searches:** plans 7, 8 and 9 (144 YouTube searches, all logged in `search_history.csv`). Plan 9 targeted seed and related games no earlier plan had searched:
  - Death and Taxes, Fears to Fathom, Scarlet Hollow, World of Horror
  - The Skin Stapler, Take Care of the Dog, Obey the Voice, Strange Horticulture
  - Servant of the Lake, Night Plane, Get Upstairs and others
- **Pipeline:** `tools/pipeline.sh` fetched each channel page, then the About page of every candidate that passed the automatic filters (language, size, activity, clips, commentary, contact).
- **Review:** 412 candidates were reviewed by hand in `exports/review_log/chunks/chunk_1..5`. 202 were accepted and 210 rejected. Each rejection reason is recorded in `rejected_cN.json`: non-English, off-genre, clips or VOD reuploads, music/art/animation, guide or no-commentary formats, or too sparse (under about 30 subscribers with little history).

## Contact routes (new rows)

| Route | Count |
|---|---|
| YouTube About business email (sign-in required to view) | 97 |
| Public social profile | 47 |
| Public business email | 27 |
| Public community/contact page | 27 |
| Unknown | 2 |

## Socials for every creator

`tools/build_creator_links.py` now exports every link on each creator's About page to `exports/creator_links.csv`:
- About pages are cached for all 1,798 creators.
- 1,592 creators have at least one link, 5,041 links in total.

The Outreach Desk and `start_all.ps1` use these links to show buttons for Twitch, X, Bluesky, Instagram, TikTok, Discord and site links next to each creator.

## Top new creators

| Tier | Fit | Creator | Subs | Comparable games |
|---|---|---|---|---|
| S | 86 | theRCLman | 29,000 | Papers, Please; Quarantine Zone; Security 51; The Exit 8 |
| A | 77 | TheJorwynn | 381 | Quarantine Zone; Animaly Bar; Gas Station Case; The Skin Stapler |
| A | 75 | MaadTV | 1,010 | The Mortuary Assistant; Rehaunted; Hariti; Photomaly |
| A | 74 | JayBux | 102,000 | Animaly Bar; The Skin Stapler; Photomaly; The Floor Above |
| A | 74 | BerryCrepe VT | 57,900 | Quarantine Zone; Shift at Midnight |
| A | 74 | Simulated Mind | 3,850 | Quarantine Zone; Roadside Research |
| A | 72 | CthuLuck | 4,630 | Papers, Please; Security 51 |

## Next

The next import starts at **Batch 020**, from review_log chunk 6 onward. The harvest cache is complete, so another cycle only needs a new plan file plus `tools/run_plan.sh`, then `tools/pipeline.sh`, then review. Growing to 3,000 still needs the owner's go-ahead.
