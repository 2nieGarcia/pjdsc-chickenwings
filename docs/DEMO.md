# Demo script: "Carina, two weeks early"

Five minutes, offline, from one frozen artifact run. Every number below comes from that run or a cited source; the right-hand column says which. Re-check the numbers after any new `python -m f2f.run`.

## Before you start

1. Wi-Fi off. Laptop on power. Close everything else.
2. `data/raw/events/flood_log.csv` and `data/raw/chirps/navotas_daily.csv` are in place (team Drive / `python -m f2f.ingest.rain`). Without them the run warns and the replay has no flood flags or no rain.
3. Frozen run: `python -m f2f.run --config configs/carina_2024.yaml`, then `python -m f2f.export`, then `cd web && npm run build && cd ..`.
4. `python -m f2f.serve` and open http://127.0.0.1:8600. Check the run id in the header matches the frozen run.
5. Delete `audit.jsonl` and `plans/` from the run folder so the approval beat starts clean.
6. Backup: the screen recording in the team Drive (`backup_20261024-52d538a.webm`, also in `data/demo/` on the build machine). If the browser dies, play it and narrate from the same beat.
7. The page opens on 22 Jul: press **Prev week** 3 times before you start talking.

## Script

Numbers are from run `20261024-52d538a`: real CCHAIN to 2022, and CHIRPS for 2023-24 mapped onto the CCHAIN rain scale (see "Rain scale"). There was no flood log on the machine that built it (see "Flood log").

| # | Time | Do | Say | Backed by |
|---|---|---|---|---|
| 0 | 0:00-0:30 | Replay view, slider on 1 Jul 2024 | "Navotas reported 471 leptospirosis cases in 780 weeks, 2008-2022; three weeks in four had none. Every Monday this asks: how likely is a week with 3 or more cases, 1-3 weeks out, where first, and is there enough doxycycline?" | README, `docs/DATASETS.md` |
| 1 | 0:30-1:10 | Press **Next week** to 29 Jul. Point at the rain bars | "Rain bars are CHIRPS satellite rain over the city, put on the same scale as the rain the model learned from. The week of 22 Jul is Carina: 396 mm, past the 320 mm warning line. The weeks around it are 45-145." | `city_week.parquet`, `data/raw/chirps/navotas_daily.csv` |
| 2 | 1:10-1:30 | Point at the gate note under the map | "The Tangos-Tanza navigational gate was hit by a barge on 7 June. Tanza 1 and 2 and Tangos North and South were open to the tide all through Carina." | flood log (ABS-CBN 19 Jun 2024, Inquirer 29 Aug 2024), `configs/carina_2024.yaml` |
| 3 | 1:30-2:20 | On 29 Jul: the three week cards | "A week earlier, on 22 July, everything is quiet: 7-11%. On 29 July, the Monday after Carina, the chance of a bad week jumps to 37%, 50% and 33% for the next three weeks, and all three go to **warning**: past the model's cutoff and past 320 mm of rain. That covers the weeks of 5, 12 and 19 August, before the August hospital-surge headlines. On 5 August next week is still on warning; by 12 August it's quiet. The model never saw cases after 2022: this is rain and season alone." | `forecast.parquet` |
| 4 | 2:20-2:50 | Act-now list, hover a rank band | "While a week is on alert, the priority list switches on. Tanza 2, Tangos South, Tangos North, Tanza 1, Bagumbayan South. The bar is how far each rank moves when we jitter the index weights by 20%: the top four are solid, the middle of the list is a coin flip." | `barangay_index_resident.parquet` (rank_p05/p95) |
| 5 | 2:50-3:20 | Toggle **Daytime** | "By day, about 30,000 fish port workers are in the NBBS barangays. Exposure there goes from 41,000 to 55,000 people, and the capsule need from 294,000 to 350,000 at 50% uptake." | `index_daytime.json`, `plans.json`, `configs/base.yaml` (MUCEP, DA 2026) |
| 6 | 3:20-4:10 | Stock panel: point at on-hand vs need, type a name, **Approve plan** | "20,000 capsules on hand, and that number is labelled synthetic. Need is 294,000, so 274,000 short, 13.7 times what's on hand; allocation goes act-now first and never past what's there. An official approves or rejects. That's logged; nothing is dispatched." | `plans.json`, `audit.jsonl` |
| 7 | 4:10-5:00 | **Backtest** view, click **Week +1** | "Held-out 2021-22. On MAE, predicting zero every week ties us at 0.49, because 75% of weeks are zero. But zero catches none of the outbreak episodes. The event model catches two of three, a week ahead, with an AUC of 0.95. That's why the output is a probability, not a count." | `metrics.parquet` |

## What the demo must not claim

- **"It predicted the surge from case data."** It saw no cases after 2022. The 29 Jul warning comes from rain and season. Don't quote hospital numbers it didn't see.
- **Raw CHIRPS millimetres.** The bars are on the CCHAIN scale (raw CHIRPS for that week is 211 mm). Say "on the scale the model learned from" if asked.
- **"Need jumps tenfold in daytime mode."** It's +19% (294,414 to 350,119 capsules at 50% uptake). The old line in SPRINTS.md beat 5 is wrong for the real layers.
- **"The map reshuffles tiers through the replay."** Tiers are fixed per run; the replay switches the priority list on and off with the alert. The act-now five are the same in resident and daytime mode.
- **San Jose as a gate barangay.** No 2024 source (#39).

## Rain scale

The model and the 160/320 mm lines were built on CCHAIN rain, which stops in 2022. CHIRPS reads about 20% drier over Navotas and almost never reaches 320 mm in a week (0 weeks in 2015-2022 against CCHAIN's 11), so raw CHIRPS would understate any storm. `run.city_rain()` maps CHIRPS onto the CCHAIN distribution (empirical quantile mapping, fit on 2015-2022). Checked out of sample (fit 2015-19, test 2020-22), it recovers 10 of 17 CCHAIN weeks ≥ 160 mm, against 6 for raw CHIRPS and 7 for one scale factor, so it still errs dry. Details on #3.

## Flood log

`data/raw/events/flood_log.csv` (team Drive, #4) wasn't on the machine that built this run, so `flood_event` is False everywhere. With it, the alert rule's flood branch also puts **warning** on the 1 and 8 Jul issues (the 24 Jun tide flood, from the broken gate, no storm) and on every horizon of 5 and 12 Aug (flood rows in the weeks of 22 and 29 Jul). 15 and 22 Jul stay quiet. Copy it in and rebuild before the frozen run, then re-check row 3: the early-July warnings change the "quiet before Carina" line, and the honest version is "the gate flood already had the city on warning".

## If someone asks

| Question | Answer | Source |
|---|---|---|
| Why not predict case counts? | 75% of Navotas weeks have zero cases. On MAE, "predict zero" ties the best model (0.490). It never warns anyone. | `metrics.parquet`, test split |
| Is the stock real? | No. 20,000 capsules on hand is a labelled synthetic number. The need side is real exposure × dosing guideline. | `configs/carina_2024.yaml`, PSMID CPG 2010 |
| Does it diagnose or send alerts? | No. It drafts a plan; an official approves or rejects it, and that is logged. Nothing is dispatched. | `f2f.serve`, `audit.jsonl` |
| Why is h = 3 weaker? | Three weeks out, only rain from four and five weeks before the target week is known. AUC drops from 0.95 (h = 1) to 0.78. | `metrics.parquet` |
| Where does 2024 rain come from? | CHIRPS v2.0 daily, area-weighted over the city polygon. CCHAIN rain stops in 2022. | `data/raw/chirps/`, `manifest.json` |
| Why isn't San Jose a gate barangay? | No 2024 source names it. It was on the list until #39. | `data/README.md`, flood log |

## Dry runs

| Run | Date | Time | Issues found |
|---|---|---|---|
| 1 (scripted click-through, no speaker) | 24 Oct 2026 | 111 s of clicks; the talk track is about 5 min | No console errors. All 17 requests go to 127.0.0.1 (fonts and data are bundled), so Wi-Fi off is safe. 22 Jul reads 7/9/11%, 29 Jul WARNING 37/50/33%. Approve wrote `created` + `approved` to `audit.jsonl`; deleting it and `plans/` resets the beat. Notes: the page opens on 22 Jul, so press **Prev week** 3 times for beat 0; Backtest opens on Week +2, so click **Week +1**; no flood log on the build machine (see above). Recording: `data/demo/backup_20261024-52d538a.webm` (silent; narrate over it). |
| 2 (with the speaker, timed) | | | |
