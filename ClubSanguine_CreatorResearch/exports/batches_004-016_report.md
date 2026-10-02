# Discovery run 2 — Batches 004–016 report

Research only. No outreach happened; `outreach_status` is blank for every row. Report date: 2026-10-02.

## Totals

| Metric | Value |
|---|---|
| Creators in `creators.csv` | 1,598 (up from 307) |
| Added in this run (Batches 004–016) | 1,291 |
| Validation issues (`validate_data.py`) | 0 |
| Rows with at least one evidence URL | 1,598 / 1,598 |
| Tiers (whole file) | S 6 · A 185 · B 1024 · C 383 |
| High priority | 14 |

## Contact coverage

The new acceptance rule was applied: every creator added in this run had to show a public contact route. Routes are only what the creator publishes:
- a business email in the channel description
- YouTube's "View email address" business-email button (it requires sign-in to view; I did not bypass it)
- About-page links such as Discord, website, link-in-bio or socials

Nothing was invented.

| Public contact method | All rows | Added this run |
|---|---|---|
| YouTube About business email (sign-in required to view) | 893 | 743 |
| Public social profile | 266 | 224 |
| Public business email | 193 | 156 |
| Public community/contact page | 170 | 145 |
| Unknown | 76 | 23 |

- **Rows still `Unknown`:**
  - 53 from Batches 001–003 genuinely list no contact anywhere.
  - 23 added this run only link Patreon, merch or other non-contact pages.
  - All of these can be filtered with `public_contact_method = Unknown`.
- **YouTube-gated business emails:** a human can reveal these by signing in to YouTube and opening the channel's About panel.

## Twitch coverage

- **Twitch links:** 883 rows have a Twitch channel URL, taken from the creator's own YouTube About links.
- **Viewer metrics:** 42 rows have a TwitchTracker average-viewer figure. The static page doesn't label the period, so it's noted as unverified.
  - TwitchTracker rate-limited 805 of 878 lookups (HTTP 429). A slow retry was also blocked. Re-run `twitch` lookups later, or use the Twitch API, then run `exports/import_batch.py enrich-contacts`.
- **Twitch followers** stay `Unknown`; they aren't in TwitchTracker's static HTML.
- **Twitch-only streamers** with no YouTube channel are not covered. That needs official Twitch API credentials.

## Funnel (run 2)

| Step | Count |
|---|---|
| New YouTube searches (plans 2–6, see `search_history.csv`) | 410 |
| Channels with a title-matched comparable game (cumulative) | 5,412 |
| Channel pages cached | 5,525 |
| About pages cached | 3,335 |
| Reviewed manually (22 chunks) | 2,004 |
| Accepted | 1,304 |
| Rejected | 700 |
| Same-creator second channels merged or skipped | about 12 (shared Twitch username or business email) |

Most common rejections:
- off-genre focus: Roblox / Minecraft kids content, GTA RP, gacha, competitive shooters, AAA walkthroughs
- non-English content
- walkthrough / no-commentary formats
- too-sparse channels
- fan-run clip channels
- song-title false matches

Reviews were done by parallel review agents. Each followed one shared rubric with worked examples from the 565 reviews done by hand in run 1. Uncertain calls were spot-checked:
- English-language creators based in Germany and France were confirmed acceptable.
- A high-acceptance chunk (77/84) was sampled and confirmed on-genre.

## New comparable games used for graph expansion

These came from repeated appearances in accepted creators' uploads. They are listed in `exports/discovered_games.md` and are not added to `seed_games.txt`:
- Animaly Bar
- Shift at Midnight
- Scrutinized
- Diapers Please
- Can I Come In
- Who's at the Door
- Dread Neighbor
- Not My Dad
- Human Shaped
- The Pale Mimic
- The Unfamiliars
- The Cabin Factory
- Photomaly
- Kiosk
- Roadhouse Simulator
- Endacopia
- Gas Station Case
- The Floor Above
- and others

These count as related evidence only, never as `direct_comparable_count`.

## Batches

| Batch | Rows | S | A | B | C |
|---|---|---|---|---|---|
| 001 | 100 | 3 | 56 | 40 | 1 |
| 002 | 100 | 0 | 13 | 85 | 2 |
| 003 | 107 | 0 | 11 | 72 | 24 |
| 004 | 99 | 0 | 8 | 60 | 31 |
| 005 | 99 | 2 | 31 | 57 | 9 |
| 006 | 100 | 0 | 8 | 65 | 27 |
| 007 | 100 | 0 | 4 | 77 | 19 |
| 008 | 100 | 0 | 0 | 67 | 33 |
| 009 | 100 | 1 | 18 | 74 | 7 |
| 010 | 97 | 0 | 3 | 73 | 21 |
| 011 | 100 | 0 | 0 | 60 | 40 |
| 012 | 99 | 0 | 13 | 58 | 28 |
| 013 | 100 | 0 | 0 | 32 | 68 |
| 014 | 100 | 0 | 15 | 52 | 33 |
| 015 | 99 | 0 | 5 | 91 | 3 |
| 016 | 98 | 0 | 0 | 61 | 37 |

## Top 20 added in this run

| ID | Creator | Score | Tier | YouTube subs | Twitch avg viewers | Comparable games | Public contact |
|---|---|---|---|---|---|---|---|
| C0810 | [MysticHeartGaming](https://youtube.com/@mysticheartgaming) | 95 | S | 1,490 | Unknown | Papers, Please; That's Not My Neighbor; Quarantine Zone; Security 51; Take Care of the Dog | Public social profile |
| C0424 | [Buffpup Vods](https://youtube.com/@buffpupvods) | 87 | S | 18,700 | Unknown | Contraband Police; Quarantine Zone; Buckshot Roulette; I'm on Observation Duty | YouTube About business email (sign-in required to view) |
| C0425 | [Cheep Games](https://youtube.com/@cheepgames1) | 87 | S | 4,590 | Unknown | Contraband Police; Quarantine Zone; Buckshot Roulette; The Exit 8 | YouTube About business email (sign-in required to view) |
| C0309 | [Tomato's Trash](https://youtube.com/@tomatostrash) | 84 | A | 130,000 | Unknown | Contraband Police; I'm on Observation Duty; World of Horror; Shift at Midnight; Welcome to | YouTube About business email (sign-in required to view) |
| C0811 | [JazzyGuns](https://youtube.com/@jazzyguns) | 84 | A | 624,000 | Unknown | Quarantine Zone; That's Not My Neighbor; Killer Frequency; Cult of the Lamb; No, I'm Not a | YouTube About business email (sign-in required to view) |
| C0423 | [RanbooVODS](https://youtube.com/@ranboovods) | 82 | A | 656,000 | Unknown | Papers, Please; Quarantine Zone; I'm on Observation Duty; Killer Frequency; Shift at Midni | YouTube About business email (sign-in required to view) |
| C0434 | [YumiLive](https://youtube.com/@yumiliveofficial) | 81 | A | 160,000 | Unknown | Contraband Police; Quarantine Zone | Public business email |
| C1349 | [RainmrowTV](https://youtube.com/@rainmrowtv) | 81 | A | 256 | Unknown | Quarantine Zone; Contraband Police; Fears to Fathom; Project Threshold | YouTube About business email (sign-in required to view) |
| C0308 | [CrypticFox](https://youtube.com/@crypticfoxgaming) | 80 | A | 133,000 | Unknown | Contraband Police; Papers, Please; Security 51 | YouTube About business email (sign-in required to view) |
| C0426 | [MansNotWet](https://youtube.com/@mansnotwet) | 80 | A | 110 | Unknown | Papers, Please; Quarantine Zone; Buckshot Roulette; Shift at Midnight | Public community/contact page |
| C0541 | [Becky B Plays](https://youtube.com/@beckybplays) | 80 | A | 11,400 | Unknown | I'm on Observation Duty; The Mortuary Assistant; Fears to Fathom; Alternate Watch; The Exi | YouTube About business email (sign-in required to view) |
| C0435 | [IRONMOUSE VODS](https://youtube.com/@ironmousevods) | 79 | A | 134,000 | Unknown | Contraband Police; Quarantine Zone | YouTube About business email (sign-in required to view) |
| C0451 | [Chasing Skyler Gaming](https://youtube.com/@chasingskylergaming) | 79 | A | 246,000 | Unknown | Quarantine Zone; Fears to Fathom; Shift at Midnight | YouTube About business email (sign-in required to view) |
| C0814 | [The_Brotaterchip](https://youtube.com/@the_brotaterchip) | 79 | A | 16,400 | Unknown | Quarantine Zone; The Floor Above; Gas Station Case; Photomaly | Public business email |
| C0464 | [Saruei Archive](https://youtube.com/@sarueiarchive) | 78 | A | 145,000 | Unknown | Quarantine Zone; Shift at Midnight | Public business email |
| C1141 | [phillyyyphilll](https://youtube.com/@phillyyyphilll) | 78 | A | 2,670 | Unknown | Fears to Fathom; Gas Station Case; Photomaly; The Skin Stapler; Shift at Midnight | Public business email |
| C0313 | [MrKravin](https://youtube.com/@mrkravin) | 77 | A | 144,000 | Unknown | I'm on Observation Duty; The Mortuary Assistant; Shift at Midnight | Public business email |
| C0342 | [Zoozlebadoozle](https://youtube.com/@zoozlebadoozle) | 77 | A | 21,000 | Unknown | Fears to Fathom; No, I'm Not a Human; Shift at Midnight; Animaly Bar | Public business email |
| C0430 | [Reapz](https://youtube.com/@reapzshow) | 77 | A | 1,070,000 | Unknown | That's Not My Neighbor; Quarantine Zone; No, I'm Not a Human | YouTube About business email (sign-in required to view) |
| C0441 | [The Gaming Corner](https://youtube.com/@the_gaming_corner) | 77 | A | 7,580 | Unknown | Quarantine Zone; The Mortuary Assistant; Do Not Feed the Monkeys | YouTube About business email (sign-in required to view) |

## High priority (whole file)

- C0001 MetalCanyon — Papers, Please; Contraband Police
- C0021 Jezabelle Live — Quarantine Zone; That's Not My Neighbor; The Mortuary Assistant; Fears to Fathom
- C0022 Jacob Forster — Papers, Please; Quarantine Zone; I'm on Observation Duty
- C0025 JMXP — Contraband Police; Quarantine Zone; Airport Contraband
- C0026 Neodyinamite — Papers, Please; Contraband Police; Airport Contraband
- C0029 Neyreyan — Contraband Police; Papers, Please; Security 51
- C0035 RTGame Stream Archive — Not Tonight; Papers, Please
- C0059 NIRDSTUFF — Quarantine Zone; Papers, Please; Security 51
- C0095 Synissta — That's Not My Neighbor; Quarantine Zone
- C0308 CrypticFox — Contraband Police; Papers, Please; Security 51
- C0424 Buffpup Vods — Contraband Police; Quarantine Zone; Buckshot Roulette; I'm on Observation Duty
- C0425 Cheep Games — Contraband Police; Quarantine Zone; Buckshot Roulette; The Exit 8
- C0434 YumiLive — Contraband Police; Quarantine Zone
- C0435 IRONMOUSE VODS — Contraband Police; Quarantine Zone

## Caveats

- **Many accepts cover only related games.** These are anomaly or impostor indie horror titles rather than an original seed. They score `direct_comparable_count = 0` and land mostly in B/C, as intended.
- **Some creators have more than one channel.** Main and VOD channels sharing a Twitch username were merged. Other second channels (for example "X VODS") may remain where nothing links them; check before outreach.
- **Sub counts and activity are as of 2026-10-02.** `last_active_date` is derived from YouTube's relative "N days ago" label.

## Next steps

1. **Human review:** S/A and high-priority creators.
2. **Reveal gated emails:** for shortlisted creators, sign in to YouTube and open the About panel.
3. **Optional:** provide Twitch API keys for Twitch-only discovery and follower counts.
4. **Backlog:** the cache in `exports/harvest/` still holds filtered but unreviewed channels from plan 6.
