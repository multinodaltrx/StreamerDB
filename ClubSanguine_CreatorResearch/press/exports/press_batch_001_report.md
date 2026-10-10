# Press Batch 001 report

Research only. Nobody was contacted. Report date: 2026-10-10. Target: **Steam Next Fest, February 2027**.

## Totals

| Metric | Value |
|---|---|
| Outlets in `press/outlets.csv` | 134 |
| Journalists / hosts / authors in `press/journalists.csv` | 200 |
| Raw records from the four research segments | 161 outlets · 220 journalists |
| Merged as duplicates (same outlet site, or same person with matching name) | 27 outlets · 20 journalists |
| Searches logged in `press/search_history.csv` | 267 |
| Validation issues (`validate_press.py`) | 0 |
| Rows with at least one evidence URL | 334 / 334 |
| Evidence URLs that resolve (HTTP check, 380 URLs) | 364 return 200; 16 return bot-block codes (403 / 454 / 503); **0 dead (404)** |

## Outlets by type and tier

| Type | Count |
|---|---|
| Indie site/blog | 53 |
| Podcast | 28 |
| Major outlet | 25 |
| Newsletter | 16 |
| YouTube press | 11 |
| Roundup/curator | 1 |

- **Outlet tiers:** S 9 · A 15 · B 24 · C 59 · Long Tail 27
- **Journalist tiers:** S 1 · A 8 · B 31 · C 80 · Long Tail 80

Journalists score lower than outlets because a single person rarely has 3+ comparable games plus Next Fest coverage on record. Sort journalists by fit, but also look at outlet fit.

## Contactability

| Route | Outlets | Journalists |
|---|---|---|
| Public email | 45 | 32 |
| Submission form | 22 | (via outlet) |
| Social profile only | 12 | 48 |
| Unknown | 55 | 120 |

- **Journalists without a personal email:** the dashboard shows their outlet's published email and submission form on their card. With that, **103 of 200 journalists have an email route**: 32 personal and 71 via their outlet.
- **Cloudflare-protected emails:** several outlet emails sat behind Cloudflare's anti-spam email protection on the outlet's own contact page, and agents decoded them. These are published addresses, the same ones any browser displays, not guesses:
  - GameLuster, Noisy Pixel, GodisaGeek, TheXboxHub, But Why Tho?
  - Dread Central, VGamingNews, Indie Game Reviewer
  - Gaming In The Wild

## Top outlets (by fit score)

| ID | Outlet | Type | Fit | Contact | Comparable coverage |
|---|---|---|---|---|---|
| O0042 | PC Gamer | Major | 95 S | tips@pcgamer.com | Quarantine Zone, No I'm Not a Human, Papers Please, Not Tonight, Mortuary Assistant, Buckshot Roulette… |
| O0043 | GamesRadar+ | Major | 94 S | contactus@gamesradar.com | No I'm Not a Human, Papers Please, Killer Frequency, Buckshot Roulette, Scarlet Hollow, Exit 8 |
| O0048 | Destructoid | Major | 91 S | tips@destructoid.com | That's Not My Neighbor, No I'm Not a Human, Quarantine Zone, World of Horror, Papers Please |
| O0013 | GameSpew | Indie | 90 S | hello@gamespew.com | Quarantine Zone, Mortuary Assistant, Contraband Police, No I'm Not a Human, Buckshot Roulette |
| O0049 | Game Rant | Major | 90 S | form | No I'm Not a Human, Quarantine Zone, Papers Please, That's Not My Neighbor, Inscryption |
| O0050 | TheGamer | Major | 90 S | form | That's Not My Neighbor, No I'm Not a Human, Quarantine Zone, Shift at Midnight, Kiosk, Exit 8 |
| O0051 | TechRaptor | Major | 90 S | pr@techraptor.net | No I'm Not a Human, Mortuary Assistant, World of Horror, Papers Please, Not Tonight |
| O0111 | Save Your Game | Podcast | 90 S | published show email | No I'm Not a Human, Strange Horticulture, Papers Please, Obra Dinn |
| O0052 | PCGamesN | Major | 85 S | form | Quarantine Zone, Papers Please, Buckshot Roulette, Beholder |
| O0008 | Bloody Disgusting | Horror site | 83 A | form | Quarantine Zone, No I'm Not a Human, Mortuary Assistant, Buckshot Roulette |
| O0046 | Kotaku | Major | 82 A | tips@kotaku.com | Quarantine Zone, Buckshot Roulette, Kiosk, Papers Please |
| O0108 | The Game Club Podcast | Podcast | 82 A | social | Mortuary Assistant, Contraband Police, No I'm Not a Human, Buckshot Roulette, Exit 8 |

## Top journalists

| ID | Name | Outlet | Fit | Why |
|---|---|---|---|---|
| J0061 | Ashley Bardhan | GamesRadar+ | 89 S | Weird Next Fest horror every edition; No I'm Not a Human "Papers, Please" piece; email on author page |
| J0053 | Joshua Wolens | PC Gamer | 84 A | Repeated Papers-Please-like and grimy indie horror demos; email on author page |
| J0167 | John Rogers | Gaming In The Wild | 79 A | Covers every Next Fest; indie horror roundup |
| J0166 | Tim Slade | The Game Club Podcast | 76 A | Covered Mortuary Assistant, Contraband Police, No I'm Not a Human, Buckshot, Exit 8 |
| J0156 | Simon Carless | GameDiscoverCo | 75 A | Contraband Police / Quarantine Zone case studies; read by devs and press |
| J0181–2 | Tommy Dassalo, Ben Vernel | Filthy Casuals | 75 A | Buckshot Roulette, Inscryption, Papers Please |
| J0080 | Paula Vaynshteyn | Destructoid | 74 A | Two That's Not My Neighbor pieces; horror-demo Next Fest list |
| J0086 | Dylan Whitehall | Game Rant | 74 A | Next Fest top 10 with No I'm Not a Human ("Uncanny Papers Please") |

Also worth a manual look, though they rank lower because their game lists are short:
- **Mike Wilson** (Bloody Disgusting): covers almost every small horror demo.
- **Ben Sledge** (TheGamer): picked three Papers-Please-likes in one Next Fest list.
- **Yuliya Geikhman** (Screen Rant).
- **Hadley Vincent** (Destructoid): Indie Gems column.
- **Edwin Evans-Thirlwell** (Rock Paper Shotgun).
- **The Part Time Gamers podcast:** ran four episodes in a row on Papers Please, Not Tonight, That's Not My Neighbor and Quarantine Zone.

## Strongest and weakest search clusters

- **Strongest:**
  - Reviews of No, I'm Not a Human, Quarantine Zone and Buckshot Roulette (2025–26). These surface current writers who cover exactly this niche.
  - Next Fest "best demos" lists (Feb, June and Oct editions). 90 journalists have a Next Fest roundup on record.
- **Weakest:**
  - Generic "indie horror podcast" queries, which mostly return inactive shows.
  - Polygon, IGN and VG247, which block search and fetch tools. Nothing verifiable was found there, so they are not covered.

## Known caveats

Each affected row says so in `notes`.

- **Evidence from search results only:** PC Gamer, GamesRadar+, GameSpot, Push Square, Dot Esports and Gematsu returned 403 to page fetches. Some bylines and dates there come from search results, not the article page.
- **Podcast evidence:** mostly episode listings and RSS descriptions; nobody listened to episodes. About 8 Substack items were verified by title, date and byline only.
- **Roles:** staff vs. freelance is often inferred, and noted as unconfirmed.
- **Possibly left their outlet:** Ed Smith, Eric Van Allen, Dylan Pamintuan and Ben Lyons.
- **Paid services:** Fix Gaming Channel sells paid services to developers. Treat it as a vendor, not press.
- **Old evidence:** some outlet evidence is from 2013–2022, and the recency score reflects that.
- **Overlap with the creator DB:** some YouTube press rows (Nookrium, MaeMayhem and others) may already be in `creators.csv`. Don't message them twice.

## Recommendations for the next press batch

1. **Fill gaps by outlet:** Rock Paper Shotgun, Eurogamer and Polygon writers, using their RSS tag feeds, which worked for RPS and Eurogamer.
2. **Fill gaps by region:** UK and Australian indie sites.
3. **Re-verify before pitching:** in **early January 2027**, re-check the top 50 targets (still at the outlet, recent bylines) before the mid-January press push.
4. **Platforms (owner decision):** decide whether to use paid press-distribution platforms (Keymailer, game.press, Woovit). Several outlets say they take keys only through them.
