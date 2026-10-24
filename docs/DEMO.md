# Demo script: "Carina, two weeks early"

Five minutes, offline, from one frozen artifact run. Every number below comes from that run or a cited source; the right-hand column says which. Re-check the numbers after any new `python -m f2f.run`.

## Before you start

1. Wi-Fi off. Laptop on power. Close everything else.
2. `data/raw/events/flood_log.csv` and `data/raw/chirps/navotas_daily.csv` are in place (team Drive, Data Handoff / `python -m f2f.ingest.rain`). Without them the run warns and the replay has no flood flags or no rain. `manifest.json` must say `"flood_log": true` and list `chirps` under `rain_sources`.
3. Frozen run: `python -m f2f.run --config configs/carina_2024.yaml`, then `python -m f2f.export`, then `cd web && npm run build && cd ..`.
4. `python -m f2f.serve` and open http://127.0.0.1:8600. Check the run id in the header matches the frozen run.
5. Delete `audit.jsonl` and `plans/` from the run folder so the approval beat starts clean.
6. Backup: the screen recording in the team Drive (`backup_20261024-83d68d3.webm`, also in `data/demo/` on the build machine). If the browser dies, play it and narrate from the same beat.
7. The page opens on 22 Jul: press **Prev week** 3 times before you start talking.

## Script

Numbers are from run `20261024-83d68d3`: real CCHAIN to 2022, CHIRPS for 2023-24 mapped onto the CCHAIN rain scale (see "Rain scale"), and the Carina flood log (14 rows, #4; see "Flood log").

| # | Time | Do | Say | Backed by |
|---|---|---|---|---|
| 0 | 0:00-0:30 | Replay view, slider on 1 Jul 2024. The three cards already read **WARNING** at 3/4/6%; don't explain it yet, beat 3 does | "Navotas reported 471 leptospirosis cases in 780 weeks, 2008-2022; three weeks in four had none. Every Monday this asks: how likely is a week with 3 or more cases, 1-3 weeks out, where first, and is there enough doxycycline?" | README, `docs/DATASETS.md` |
| 1 | 0:30-1:10 | Press **Next week** to 29 Jul. Point at the rain bars | "Rain bars are CHIRPS satellite rain over the city, put on the same scale as the rain the model learned from. The week of 22 Jul is Carina: 396 mm, past the 320 mm warning line. The three weeks before it are 71 to 145." | `city_week.parquet`, `data/raw/chirps/navotas_daily.csv` |
| 2 | 1:10-1:30 | Point at the gate note under the map | "The Tangos-Tanza navigational gate was hit by a barge on 7 June. Tanza 1 and 2 and Tangos North and South were open to the tide all through Carina." | flood log (ABS-CBN 19 Jun 2024, Inquirer 29 Aug 2024), `configs/carina_2024.yaml` |
| 3 | 1:30-2:30 | On 29 Jul: the three week cards. Then **Next week** to 5 Aug and to 12 Aug; stay on 12 Aug | "Before Carina, the gate flood already had the city on warning. On 1 and 8 July the model said only 3-6%, but the broken gate flooded Tanza on 24 June with no storm, and a logged flood in the last two weeks is a warning on its own. By 15 and 22 July that flood is too far back: quiet, 4-11%. On 29 July, the Monday after Carina, the chance of a bad week jumps to 37%, 50% and 33% for the next three weeks: past the model's cutoff, past 320 mm, and Carina's floods logged. That covers the weeks of 5, 12 and 19 August, before the August hospital-surge headlines. On 5 August the model still says 35% for next week. By 12 August it's back to 5-9%, and only Carina's flood reports keep it on warning. The model never saw cases after 2022: this is rain, season and the flood log." | `forecast.parquet`, `city_week.parquet` (`flood_event`) |
| 4 | 2:30-2:55 | Act-now list, hover a rank band | "While a week is on alert, the priority list switches on. Tanza 2, Tangos South, Tangos North, Tanza 1, Bagumbayan South. The bar is how far each rank moves when we jitter the index weights by 20%: the top four are solid, the middle of the list is a coin flip." | `barangay_index_resident.parquet` (rank_p05/p95) |
| 5 | 2:55-3:20 | Toggle **Daytime** | "By day, about 30,000 fish port workers are in the NBBS barangays. Exposure there goes from 41,000 to 55,000 people, and the capsule need from 294,000 to 350,000 at 50% uptake." | `index_daytime.json`, `plans.json`, `configs/base.yaml` (MUCEP, DA 2026) |
| 6 | 3:20-4:10 | Toggle back to **Residents**. Stock panel: point at on-hand vs need, type a name, **Approve plan** | "20,000 capsules on hand, and that number is labelled synthetic. Need is 294,000, so 274,000 short, 13.7 times what's on hand; allocation goes act-now first and never past what's there. It's one plan, issued 22 July, the same every replay week, because the index doesn't change by week. An official approves or rejects. That's logged; nothing is dispatched." | `plans.json`, `audit.jsonl` |
| 7 | 4:10-5:00 | **Backtest** view, click **Week +1** | "Held-out 2021-22. On MAE, predicting zero every week ties us at 0.49, because 75% of weeks are zero. But zero catches none of the outbreak episodes. The event model catches two of three, a week ahead, with an AUC of 0.95. That's why the output is a probability, not a count." | `metrics.parquet` |

## What the demo must not claim

- **"It predicted the surge from case data."** It saw no cases after 2022. The 29 Jul warning comes from rain, season and the flood log. Don't quote hospital numbers it didn't see.
- **"The model saw Carina coming on 1 July."** The 1 and 8 Jul warnings are the June gate flood (a tide flood, no storm) tripping the flood rule; the model itself said 3-6%. The 12 Aug warning is Carina's flood reports, with the model at 5-9%.
- **"No flood week means dry."** The log only has the days a source reported a flood; the weeks between are unknown, not flood-free.
- **Raw CHIRPS millimetres.** The bars are on the CCHAIN scale (raw CHIRPS for that week is 211 mm). Say "on the scale the model learned from" if asked.
- **"Need jumps tenfold in daytime mode."** It's +19% (294,414 to 350,119 capsules at 50% uptake).
- **"The map reshuffles tiers through the replay."** Tiers are fixed per run; the replay switches the priority list on and off with the alert. The act-now five are the same in resident and daytime mode.
- **San Jose as a gate barangay.** No 2024 source (#39).

## Rain scale

The model and the 160/320 mm lines were built on CCHAIN rain, which stops in 2022. CHIRPS reads about 20% drier over Navotas (0.80 of CCHAIN's total, 2015-2022) and almost never reaches 320 mm in a week (0 weeks in 2015-2022 against CCHAIN's 11), so raw CHIRPS would understate any storm. `run.city_rain()` maps CHIRPS onto the CCHAIN distribution (empirical quantile mapping, fit on 2015-2022). Checked out of sample (fit 2015-19, test 2020-22), CCHAIN has 17 weeks ≥ 160 mm. The mapped series has 11 weeks ≥ 160 mm, raw CHIRPS 6 and one scale factor 7 (#48, on an earlier CHIRPS pull, had 10, 6 and 7). Counting only weeks that are ≥ 160 mm in both CCHAIN and the series, it's 7 of 17 mapped, 5 raw and 6 scaled. Either way mapping does best and still errs dry. Details on #3 and #48.

## Flood log

`data/raw/events/flood_log.csv` (#4, team Drive → Data Handoff) has flood rows in the weeks of 3 Jun, 24 Jun, 22 Jul and 29 Jul 2024, and `flood_event` is True for Navotas in exactly those weeks. The alert rule warns when a flood is logged in either of the two complete weeks before the issue Monday, on top of the rain and probability rules, so the flood rows change the alerts but not one probability:

| Issue | Alert, all three weeks | Model (h = 1/2/3) | Why |
|---|---|---|---|
| 1 Jul | warning | 3/4/6% | 24 Jun tide flood from the broken gate (1 week back) |
| 8 Jul | warning | 3/4/6% | 24 Jun flood (2 weeks back) |
| 15 Jul | none | 4/5/8% | No flood in the two weeks before; rain under 160 mm |
| 22 Jul | none | 7/9/11% | Same |
| 29 Jul | warning | 37/50/33% | Model past the 0.26 cutoff, 396 mm the week before, 22 Jul flood |
| 5 Aug | warning | 35/16/17% | 29 Jul and 22 Jul floods; the model holds week +1 on its own |
| 12 Aug | warning | 5/6/9% | 29 Jul flood (2 weeks back) only |

Without the log, 1, 8 and 12 Aug were quiet and 5 Aug warned on week +1 only. The 24 Jun row is a tide flood, not a rain flood; the log has no column to tell them apart (see `docs/handoff/4-carina-flood-log.md`).

## If someone asks

| Question | Answer | Source |
|---|---|---|
| Why not predict case counts? | 75% of Navotas weeks have zero cases. On MAE, "predict zero" ties the best model (0.490). It never warns anyone. | `metrics.parquet`, test split |
| Why does it say WARNING at 3%? | The warning has three triggers: the model's probability, heavy rain, and a logged flood in the last two weeks. On 1 and 8 Jul it's the gate flood of 24 June. A flood is a reason to get ready even when the model, which only knows rain and season, is calm. | `forecast.parquet`, flood log, `docs/CONTRACTS.md` (C2) |
| Is the stock real? | No. 20,000 capsules on hand is a labelled synthetic number. The need side is real exposure × dosing guideline. | `configs/carina_2024.yaml`, PSMID CPG 2010 |
| Why is the plan the same every week? | The plan comes from the barangay index, which is fixed per run; the replay only switches the alert. The panel says "Plan issued 22 Jul · same for every replay week". | `plans.json`, `web/src/main.js` |
| Does it diagnose or send alerts? | No. It drafts a plan; an official approves or rejects it, and that is logged. Nothing is dispatched. | `f2f.serve`, `audit.jsonl` |
| Why is h = 3 weaker? | Three weeks out, only rain from four and five weeks before the target week is known. AUC drops from 0.95 (h = 1) to 0.78. | `metrics.parquet` |
| Where does 2024 rain come from? | CHIRPS v2.0 daily, area-weighted over the city polygon. CCHAIN rain stops in 2022. | `data/raw/chirps/`, `manifest.json` |
| Why isn't San Jose a gate barangay? | No 2024 source names it. It was on the list until #39. | `data/README.md`, flood log |

## Dry runs

| Run | Date | Time | Issues found |
|---|---|---|---|
| 1 (scripted click-through, no speaker) | 24 Oct 2026 | 111 s of clicks; the talk track is about 5 min | Earlier run, before the flood log was on the build machine; its recording is superseded. No console errors. All 17 requests go to 127.0.0.1 (fonts and data are bundled), so Wi-Fi off is safe. Approve wrote `created` + `approved` to `audit.jsonl`; deleting it and `plans/` resets the beat. Notes: the page opens on 22 Jul, so press **Prev week** 3 times for beat 0; Backtest opens on Week +2, so click **Week +1**. |
| 1b (scripted screenshots of `20261024-83d68d3`, no speaker) | 24 Oct 2026 | | No console errors, no request outside 127.0.0.1. On screen: 1 and 8 Jul WARNING 3/4/6%; 15 Jul 4/5/8%; 22 Jul 7/9/11%; 29 Jul WARNING 37/50/33%; 5 Aug WARNING 35/16/17%; 12 Aug WARNING 5/6/9%. Stock label reads "Plan issued 22 Jul · same for every replay week · residents · f2f.plan…" (cut at the module name at 1280-1920 px; full text on hover). Approve not clicked. Screenshots in `data/demo/screens_20261024-83d68d3/`. |
| 2 (with the speaker, timed) | | | |
