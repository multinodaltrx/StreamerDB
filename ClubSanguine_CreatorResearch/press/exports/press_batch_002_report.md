# Press Batch 002 report

Research only. Nobody was contacted. Report date: 2026-10-10. Target: **Steam Next Fest, February 2027**.

## Totals

| Metric | After Batch 001 | After Batch 002 |
|---|---|---|
| Outlets (`press/outlets.csv`) | 134 | **185** (+51) |
| Journalists / hosts / authors (`press/journalists.csv`) | 199 | **284** (+85) |
| Outlets with a public email | 45 | 82 |
| Outlets with a submission form | 22 | 39 |
| Journalists with a public email (own or via outlet route) | 32 | 68 |
| Searches logged in `press/search_history.csv` | 267 | 394 |
| Validation issues (`validate_press.py`) | 0 | 0 |

## Segments

| File | Label | Result |
|---|---|---|
| `research/b002_enrich_journalists.json` | Press Batch 002 (journalist contact enrichment) | Published emails/socials added to existing journalists |
| `research/b002_enrich_outlets.json` | Press Batch 002 (outlet contact enrichment) | 77 outlets enriched: 24 emails, 11 forms, 65 socials, 17 press-policy notes |
| `research/b002_major.json` | Press Batch 002 (major outlets) | 41 journalists, 15 new outlets, 8 merged |
| `research/b002_indie.json` | Press Batch 002 (indie and regional sites) | 44 journalists, 36 new outlets |

## Standouts

- **Cass Marshall (Rogue, ex-Polygon):** cass@rogue.site. She reviewed Contraband Police with a Papers, Please angle, and has written about Buckshot Roulette, The Mortuary Assistant and Mouthwashing. She also runs Next Fest horror demo roundups. She is the top journalist (S 97).
- **Aftermath:** tips@aftermath.site. Riley MacLeod writes almost all of its Next Fest demo pieces.
- **Hey Poor Player:** posts a Next Fest demo list every fest (Josh Speer). Review requests go to Deadpixels@heypoorplayer.com.
- **Adventure Game Hotspot:** covered No, I'm Not a Human and Killer Frequency, and runs frequent demo items.
- **Gaming.net:** reviewed Quarantine Zone, Contraband Police and Shift at Midnight (Jul 2026).
- **Regional:**
  - SIFTER (AU, contact@sifter.com.au)
  - MKAU Gaming (AU)
  - Gert Lush Gaming (UK)
  - Expansive (DLC@expansivedlc.com)
  - COGconnected and CGMagazine (CA)
  - Gameffine and Outlook Respawn (IN)
- **Others with published contacts:**
  - Ted Litchfield (PC Gamer)
  - Vikki Blake (horror freelancer, sign-up form for her press list)
  - TheBigBois (press@thebigbois.com)
  - Nindie Spotlight
  - Steam Deck HQ (form, plus freelancer Oliver Stogden)

## Caveats (from the researchers)

- **Blocked sites:** RPS, Eurogamer, Polygon, IGN, VG247, The Guardian, The Verge and Wired block automated reading. Nintendo Life, Pure Xbox, GameSpot and Unwinnable return 403. Their bylines come from OpenCritic review lists and Wikipedia references, and social profiles were confirmed through Bluesky's public API. Records whose evidence was seen only as a listing say so in `notes`. Open them before pitching.
- **People who may have moved on:** Alice Bell, Katharine Castle and Alex McHugh (last work 2024–25). Kudzuey's Game Vine is a strong fit but has been inactive since Feb 2025.
- **Byline conflicts:** TheBigBois (Anna/ColdMoon vs Zachary Holmes) and PSU (Thea Severance vs Timothy Nunes).
- **Personal addresses:** some emails belong to a person rather than a tips@ inbox (Analog Stick's jeff@, Game Wisdom's josh@, HG101's kurt@). All are published as the contact route.
- **Gaps:** no Irish or NZ outlets were found, and no dedicated horror-film sites with a games section turned up.
- **Redirects:** pcinvasion.com now redirects to primagames.com, and Paste's games section redirects to The A.V. Club.

## Next

- Open the dashboard **Press** tab, filter tier S/A plus Email, and check each evidence link before pitching.
- Pitch window: mid-January 2027 (3–4 weeks before the fest). See HANDOVER section 7.
