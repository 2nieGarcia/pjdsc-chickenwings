# Handoff: Carina 2024 flood and gate log (#4)

What #4 delivered, what it changes for the issues that read it, and what's still open. Conventions for the file itself are in [data/README.md](../../data/README.md#flood-log).

## What landed

- `data/raw/events/flood_log.csv`, 14 rows, 7 Jun to 24 Aug 2024. Not in git (`data/` is ignored). Copy in the team Drive: https://drive.google.com/drive/folders/1DhX718zN8rEeTwgC2A0noxeRgA2WeDqs?usp=sharing. Put it at that path before running the pipeline.
- `configs/carina_2024.yaml`: `gate_impaired.start` is now 2024-06-07 (was 2024-06-21). The end stays 2025-08-31.

| date | barangay | kind | depth_code | affected | source |
|---|---|---|---|---|---|
| 2024-06-07 | Tanza 1 | gate_down | | | ABS-CBN, 19 Jun 2024 |
| 2024-06-07 | Tanza 1 | flood | | 2000 | DROMIC, Flooding Incident in Navotas City #1 |
| 2024-06-24 | Tanza | flood | | | ABS-CBN, 25 Jun 2024 |
| 2024-07-23 | Tanza | flood | knee | | DZRH, 23 Jul 2024 |
| 2024-07-24 | (city) | flood | | 53 | DROMIC Carina #4 |
| 2024-07-24 | (city) | flood | | 407 | DROMIC Carina #5 |
| 2024-07-24 | (city) | flood | | | Inquirer, 25 Jul 2024 (mayor: 80% of the city flooded) |
| 2024-07-25 | (city) | flood | | 254 | DROMIC Carina #6 |
| 2024-07-25 | Tanza 2 | flood | below_gutter | | GMA, 25 Jul 2024 |
| 2024-07-25 | Sipac-Almacen | flood | below_gutter | | GMA, 25 Jul 2024 |
| 2024-07-25 | Tangos | flood | | | GMA, 25 Jul 2024 ("caused by damaged floodgate") |
| 2024-07-26 | Tanza | flood | | | Philstar, 27 Jul 2024 |
| 2024-07-30 | (city) | flood | | | GMA, 30 Jul 2024 (MMDA: two Navotas barangays flood at high tide) |
| 2024-08-24 | Tanza 1 | gate_up | | | Inquirer, 29 Aug 2024 |

Full URLs are in the CSV.

## What the panel sees now

`build_city_week` with this log and the current config:

- `flood_event` is true for Navotas in the weeks of **2024-06-03, 06-24, 07-22 and 07-29**, and nowhere else.
- `gate_impaired` is true for Navotas from the week of **2024-06-03** to the end of the panel. Moving the start from 21 Jun added the weeks of 3 and 10 Jun; replay weeks didn't change.

Two things to keep in mind when reading these flags:

- **`flood_event = False` doesn't mean dry.** DROMIC says the June gate flooding in Tanza I "subsides minutes or hours after" and kept coming back with the tide. The log only has the days a source reported it, so the weeks between are unknown, not flood-free.
- **The 24 Jun row is a tide flood, not a rain flood.** It comes from the broken gate, with no storm. If a rule should only react to rain-driven floods, it needs to tell these apart. The log has no column for that; the source text does.

## Per issue

### #7 Pooled event model

The flags can't be learned from the training data. Training runs 2008-2022, and the log covers 2024 only, so `flood_event` and `gate_impaired` are False for every training row in all 12 cities. A GLM given a constant column will return a NaN or meaningless coefficient for it. Leave both out of the fit for Sprint 1. They come back once the 2015-2023 back-fill exists (Sprint 2), and even then only for Navotas.

### #8 Carina replay forecasts

The flags reach the forecast through the alert rule ("warning if there is a flood in lags 1-2"). If lag 1 means the complete week before the issue Monday, these issue dates get a flood-driven warning:

| issue date | flood week behind it |
|---|---|
| 2024-07-01 | 06-24 (lag 1) |
| 2024-07-08 | 06-24 (lag 2) |
| 2024-07-15 | none |
| 2024-07-22 | none |
| 2024-07-29 | 07-22 (lag 1) |
| 2024-08-05 | 07-29 (lag 1), 07-22 (lag 2) |
| 2024-08-12 | 07-29 (lag 2) |

So the replay starts in warning because of the June tide flood, drops out for 15 and 22 Jul unless rain or `p_elevated` holds it up, then warns again from 29 Jul. That's honest, but it doesn't match the demo line "the alarm rises around the event" (docs/SPRINTS.md). Whoever owns #8 decides between keeping it and saying so, counting only rain-event floods, or something else. The leakage rule still applies: a flood k weeks before the target week can feed horizon h only if k ≥ h.

### #11 Monte Carlo rank bands

`gate_affected` (the hazard indicator from `gate_impaired.barangays`) is 1 for Tanza 1, Tanza 2, Tangos North, Tangos South and San Jose (Pob.). The 2024 sources support Tanza and Tangos, but **no 2024 source names San Jose**. Worth one extra row in the sensitivity table: ranks with San Jose off the gate list.

### #13 End-to-end run

- `run.py` loads the log only if the file exists, and quietly leaves `flood_event` all False when it doesn't. The CSV isn't in git, so a fresh clone runs without it. Record it in `manifest.json` like the other inputs (path and modified date), and record its absence too, so a run without floods is visible.
- The demo laptop needs the Drive copy at `data/raw/events/flood_log.csv`.

### #18 Demo script

Claims the log can back, each with its source in the CSV:

- The Tangos-Tanza navigational gate was damaged by a barge on 7 Jun 2024, in Brgy. Tanza 1 (ABS-CBN, MMDA).
- DROMIC counted 500 families / 2,000 persons affected by the gate flooding in Tanza I as of 4 Jul.
- On 24 Jul the mayor said 80% of the city was flooded (Inquirer).
- MMDA closed the gate again on 24 Aug 2024, but it wasn't fully working yet (Inquirer, 29 Aug).

Careful with beat 2 in docs/SPRINTS.md. It lists San Jose among the gate barangays, and no 2024 source says so. Either drop San Jose from the spoken line or find a source first. The gate note on the dashboard now reads "since 7 Jun 2024" after the next export.

### Dashboard (web/)

- The gate note (`web/src/main.js:47`) picks up the new start date on the next `python -m f2f.export`.
- Water depth stays a rain proxy (`main.js:124`). Only 3 rows have a `depth_code`, which isn't enough to drive the water per week.

### Index (#10, closed)

The hazard component doesn't use flood-log days (#10 shipped without them, as planned). I'd leave it that way for Sprint 1. Tanza (1, 2 or unspecified) has 5 of the 7 barangay-level flood rows because the gate story put reporters there, so counting rows would rank news coverage as much as flooding. The S3 idea of validating the index against flood-event frequency has the same problem at 14 rows.

## Open gaps

- **San Jose (Pob.).** On the config gate list and in the issue, but in no 2024 source. The Navotas PIO's July 2024 Facebook flood updates are the best bet; they couldn't be read from a script.
- **Tangos North vs South.** Sources say "Tangos" (and "C4 Tangos"), never which one.
- **Unverified leads.** Manila Bulletin, 24 Jul 2024, "223 families rescued in Navotas City", lists evacuation centres by barangay. RTVM has 183 families / 862 people at Tanza NHS (Tanza 2) on 25 Jul. Both block scripted reads; check them in a browser.
- **DROMIC's later Carina totals** for Navotas (8,777 persons by #23, 17,054 by #55, 21,054 by #63 on 25 Sep) aren't rows. They add families displaced outside evacuation centres, with no date of displacement, so they'd create false flood weeks.

## For the 2015-2023 back-fill (Sprint 2)

- DROMIC: search `https://dromic.dswd.gov.ph/?s=Navotas` (or its RSS at `/search/Navotas/feed/rss2/`). Each event page links its report PDFs; extract the text and search it for the 18 barangay names as well as "Navotas". The typhoon-wide series give only city lines. Single-city incident reports, like the June 2024 one, sometimes name the barangay.
- Check every result's publish date. Searches for 2024 events kept returning 2025 ones (San Jose river wall, a second presidential visit to Tanza NHS).
- Manila Bulletin, RTVM and the PCO mirror block scripts; GMA, Inquirer, Philstar, ABS-CBN, DZRH, Tribune and DROMIC don't.
