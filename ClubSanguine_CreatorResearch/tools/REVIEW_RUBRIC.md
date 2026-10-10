# Creator review rubric

This rubric is for whoever reviews chunks with `tools/review.py`, whether a human or an agent. It was distilled from about 2,700 review decisions made on 2026-10-02.

**About the game.** Club Sanguine is a stylized first-person deduction / management / dark-comedy horror game. You play a supernatural nightclub bouncer who inspects guests (humans, vampires, monsters) and decides who gets in. The shorthand is "Papers, Please meets supernatural nightclub bouncer". The full brief is in `CLUB_SANGUINE_CREATOR_BRIEF.md`.

**Who we want.** English-language creators whose audience already watches:
- inspection, gatekeeper, deduction or impostor games
- anomaly games
- odd-job sims
- indie (comedy) horror

Personality-driven commentary matters.

**What has already been filtered.** Candidates reaching review already passed these automatic filters:
- a video title names a comparable game
- an upload in roughly the last 90 days
- size limits
- not obviously non-English
- at least one public contact route

Your job is a quality judgement from the line alone. **Don't browse and don't invent data.**

## Line format (`python tools/review.py show K`)

`idx|name|subs|days since latest upload|games matched|country|C:<public link hosts>[+gated]|E:<emails>|recent titles|D:<description start>`

- Games are abbreviated, for example `PapersPle`, `ThatsNotM`, `Contraban`, `Quarantin`, `NotTonigh`, `TheMortua`, `KillerFre`, `BuckshotR`, `ImonObser`, `DeathandT`, `ShiftatMi`, `AnimalyBa`, `Security5`.
- `+gated` means YouTube shows a business email behind sign-in. That counts as a contact route.

## Reject (`idx:R=<short reason>`)

Reject a channel if it is any of the following:
- **Non-English.** The titles or the description are mostly another language. A creator based in Germany, France, Brazil and so on is fine when their titles and content are in English.
- **A false title match.**
  - Music, song, karaoke or reaction channels ("Not Tonight" is a common song title).
  - Magic: The Gathering ("Death and Taxes" is a deck).
  - "Subliminal" audio channels.
  - Titles that only *compare* to a game, such as "Papers Please but…".
- **Off-genre focus.** Mostly:
  - AAA walkthroughs
  - CoD, Fortnite, Warzone, Valorant, Overwatch, League or Marvel Rivals
  - Roblox or Minecraft kids content
  - sports games
  - MMOs
  - gacha games
  - GTA RP
  - card games
  - truck-sim mod showcases
  - IRL or vlog channels
- **The wrong format.**
  - No-commentary, walkthrough, longplay, "full game movie", "all endings" or "all jumpscares" uploads.
  - Guide, tip or trophy channels.
  - Performance-test channels.
- **A fan-made clip, edit or reupload channel.** This includes a VOD or archive channel that says it is run by someone other than the creator. An official VOD channel is fine.
- **A media outlet, publisher, developer, trailer or news channel.**
- **Too sparse.** Roughly under 20 subscribers with only a few random uploads. Family or kids upload channels also fall here.
- **An agency VTuber who mainly does music, covers, singing or ASMR roleplay.**
- **A second channel of a creator who is already accepted, or whose main channel is over about 3M subscribers.** Name the creator in the reason.

## Accept (`idx:g=..,p=..,i=..[,s=..][,e=..][,n=..]`)

**Always give explicit g/p/i scores.** Unlisted indexes get defaults, so list every index.

**Genre fit `g`:**

| Score | Who |
|---|---|
| 18–20 | Repeated inspection / gatekeeper / deduction / anomaly / odd-job horror coverage; several comparables |
| 15–17 | Indie horror or comedy-horror regular with 1–2 comparables |
| 13–14 | Variety indie or sim channel with a comparable |
| 11–12 | Mostly other genres, but the comparable is real and there's some indie content |

**Personality `p`:**

| Score | Who |
|---|---|
| 5 | Loud, reactive, comedic |
| 4 | Normal commentary let's play |
| 3 | Low-key or unclear |
| 1–2 | Commentary unverified (add a note) |

**Indie affinity `i`:**

| Score | Who |
|---|---|
| 5 | Mostly small indies |
| 4 | Frequent indies |
| 3 | Mixed |
| 2 | Rare |

**Optional fields:**
- `s=` content style. No commas. For example `Horror gameplay commentary`, `Stream VOD archive`, `VTuber let's plays`, `Indie first looks`, `100% completion videos`, `Duo gameplay commentary`.
- `e=` which listed email to use. Use it when the description lists both a fan-mail and a business address.
- `n=` a short note. It must come last and may contain commas, but no `|`, double quotes or `$`.

## Examples

- `3:g=17,p=5,i=5,s=Horror gameplay commentary` — horror channel playing That's Not My Neighbor and Shift at Midnight
- `9:g=17,p=4,i=4,n=Recent series on Scrutinized (inspection game).`
- `35:g=18,p=5,i=5` — "DO NOT LET THE HUMANS THROUGH", anomaly games
- `21:R=trailer channel`
- `37:R=false title match (music / reaction channel)`
- `8:R=false title match (Magic: The Gathering 'Death and Taxes' deck)`
- `56:R=non-English (Spanish)`
- `13:R=longplay format`
- `48:R=likely fan-run stream archive`
- `24:R=same creator as <accepted channel>`

## Recording

Run `decide` exactly once per chunk:

```
python tools/review.py decide K "0:g=16,p=5,i=4|1:R=non-English (Spanish)|2:g=13,p=4,i=3,s=VTuber let's plays,n=Second channel of X."
```

It writes `exports/review_log/pool_cK.json` and `rejected_cK.json`, and refuses to overwrite an existing pool.

## Benchmarks

On 2026-10-02 acceptance ran 40–65% per chunk. A chunk accepting over 85% deserves a spot-check. One did (77/84) and turned out to be fine: it was dense in anomaly-game creators.
