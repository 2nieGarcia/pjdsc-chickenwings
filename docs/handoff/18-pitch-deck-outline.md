# Handoff: pitch deck outline (#18)

For building the deck without running anything. Every number below is from the frozen run **`20261024-83d68d3`** (24 Oct 2026) or a cited source, and matches [docs/DEMO.md](../DEMO.md). If a number isn't in this file, don't put it on a slide; ask first.

"Source" names the file in `data/artifacts/20261024-83d68d3/` it came from (or the dashboard JSON exported from it), so anyone can check a slide later. Put a small source line on every slide that has a number, e.g. "Run 20261024-83d68d3 · forecast.parquet".

## Shape

12 slides, about 5 minutes of talk plus the 5-minute live demo, which sits after slide 4. If the demo fails, play the backup video at the same point. Slides 5-9 repeat the demo's numbers so the deck still stands up without it.

## Slides

### 1. Flood-to-Fever

- **Message:** Leptospirosis early warning and decision support for Navotas City. PJDSC 2026, team Chicken Wings.
- **Visual:** Title over a crop of the 3D barangay map (`02_beat1-4_29jul.png`, map area only).

### 2. Floods in Navotas turn into leptospirosis weeks later

- **Message:** Leptospirosis cases follow flood exposure, often within weeks, which is why we look 1-3 weeks ahead. Navotas floods from rain and, in 2024, from the tide through a broken navigational gate.
- **Numbers:** 471 reported cases in 780 weeks, 2008-2022. About 80% of cases fall July-October. Source: `docs/DATASETS.md` (CCHAIN PIDSR on HDX).
- **Visual:** None needed, or a simple timeline: flood → exposure → cases 1-3 weeks later.

### 3. Why we forecast a probability, not a case count

- **Message:** Three weeks in four have zero cases, so a model that always says "zero" looks accurate and never warns anyone. We forecast the chance of a bad week (3 or more cases) instead.
- **Numbers:** 74.6% of weeks have zero cases (round to "three in four"). 40 weeks in 2008-2022 had 3 or more cases. Source: `docs/DATASETS.md`, `city_week.parquet`.
- **Visual:** One bar or waffle: 75% zero weeks vs 25% with cases.

### 4. Every Monday, four answers for the City Health Office

- **Message:** (1) How likely is a bad week 1-3 weeks out? (2) Which barangays first? (3) Who is exposed by day but doesn't live there? (4) Is there enough doxycycline? An official approves or rejects every plan; nothing is sent automatically.
- **Visual:** Full dashboard screenshot, `02_beat1-4_29jul.png`, with the four areas labelled 1-4 (cards, map/act-now list, Daytime toggle, stock panel).
- **Then:** live demo (or backup video).

### 5. The Carina replay: warning before the August surge

- **Message:** Replaying 2024 week by week with only what was known each Monday. The broken gate's tide flood had the city on warning in early July. Carina's 396 mm week pushed all three weeks to warning on 29 July, covering 5-19 August.
- **Numbers** (source: `forecast.parquet`, `city_week.parquet`):

  | Issue Monday | Chance of a bad week (next 1/2/3 weeks) | Alert | Why |
  |---|---|---|---|
  | 1 Jul | 3/4/6% | Warning | Gate flood on 24 Jun |
  | 8 Jul | 3/4/6% | Warning | Gate flood on 24 Jun |
  | 15 Jul | 4/5/8% | None | |
  | 22 Jul | 7/9/11% | None | |
  | 29 Jul | 37/50/33% | Warning | Model, 396 mm rain, Carina floods |
  | 5 Aug | 35/16/17% | Warning | Carina floods, model on week +1 |
  | 12 Aug | 5/6/9% | Warning | Carina flood reports only |

  Rain on the model's scale: 71, 89, 145, **396** (Carina, week of 22 Jul), 42, 89 mm. Warning line 320 mm.
- **Visual:** `02_beat1-4_29jul.png` (cards and rain bars on 29 Jul). Optional small strip: `01_beat0_1jul.png` and `04b_12aug.png`.
- **Say carefully:** the early-July and 12 Aug warnings come from the flood rule, not the model (it said 3-9%).

### 6. Which barangays first, and how sure we are

- **Message:** A priority index ranks the 18 barangays on hazard, exposure, vulnerability and access to care. The rank band shows how much a rank moves when we change the weights by ±20%. The top four are solid.
- **Numbers** (source: `barangay_index_resident.parquet`):

  | Rank | Barangay | Score | Rank band |
  |---|---|---|---|
  | 1 | Tanza 2 | 6.70 | 1-3 |
  | 2 | Tangos South | 6.50 | 1-2 |
  | 3 | Tangos North | 6.41 | 2-4 |
  | 4 | Tanza 1 | 6.03 | 3-4 |
  | 5 | Bagumbayan South | 5.44 | 5-6 |

  The four gate barangays are Tanza 1, Tanza 2, Tangos North and Tangos South (gate damaged 7 Jun 2024). Source: `configs/carina_2024.yaml`, flood log.
- **Visual:** Crop of the act-now list from `02_beat1-4_29jul.png`.

### 7. Daytime: the fish port workers

- **Message:** By day about 30,000 fish port workers are in the three NBBS barangays. Counting them raises exposure there by a third and doxycycline need by about a fifth.
- **Numbers:** NBBS exposure 41,021 → 54,618 people. Capsule need at 50% uptake 294,414 → 350,119 (+19%). Sources: `barangay_index_resident.parquet`, `barangay_index_daytime.parquet`, `plans.json`; 30,000 from DA 2026, day/night factor 0.93 from MUCEP (`configs/base.yaml`).
- **Visual:** `05_beat5_daytime_29jul.png`.

### 8. Is there enough doxycycline? A plan an official signs off

- **Message:** Need vs stock on hand, allocated act-now first and never past what's there. An official approves or rejects; the decision is logged and nothing is dispatched. There is one plan per run (issued 22 Jul), the same every replay week.
- **Numbers** (source: `plans.json`, residents, 50% uptake): on hand 20,000 capsules (**synthetic**, say so on the slide), need 294,414, unmet 274,414, 13.7× what's on hand. At 30% uptake unmet is 156,650; at 70%, 392,175.
- **Visual:** `06_stock_panel_resident.png`. Better: a capture after **Approve plan** showing the "approved" stamp (Charles takes it during recording, see below).

### 9. Does it work? Held-out test, 2021-22

- **Message:** On the usual error measure, "always zero" ties us. On what matters for action, it catches nothing and we catch two of three outbreak episodes, a week ahead.
- **Numbers** (source: `metrics.parquet`, test split 2021-22):

  | | Event model | Always zero | 5-yr median | Seasonal model |
  |---|---|---|---|---|
  | MAE, next week (lower better) | 0.49 | 0.49 | 0.50 | 0.49 |
  | AUC, next week (higher better) | 0.95 | 0.50 | 0.76 | 0.76 |
  | Episodes caught, next week | 67% (2 of 3) | 0% | 0% | 0% |
  | Median lead time | 1 week | – | – | – |

  Further out the model is weaker: AUC 0.87 at 2 weeks and 0.78 at 3; episodes caught 33% at 2 weeks, 0% at 3.
- **Visual:** `07_beat7_backtest_h1.png`, or rebuild the table above.

### 10. What it can't do yet

- **Message:** Honest limits.
  - It saw no case data after 2022 (that's all that's public). 2024 is a replay on rain, season and floods.
  - 2023-24 rain is satellite (CHIRPS) put on the model's rain scale. It still reads dry: of 17 heavy weeks (≥ 160 mm) in 2020-22 it catches 7.
  - The flood log is hand-built from 14 news and DSWD reports, June-August 2024 only. A week with no report isn't a dry week.
  - Stock on hand is a made-up number until the City Health Office shares the real one.
  - City-level cases only, so the barangay ranking can't be checked against barangay cases yet.
- **Sources:** `docs/DEMO.md` ("Rain scale", "Flood log"), `docs/DATASETS.md`.

### 11. Next: real data from the city

- **Message:** Requests going to the Metro Manila Center for Health Development, the Navotas CESU and DOH (FOI) for barangay-level, weekly cases. Two earlier DOH FOI requests for leptospirosis data are marked released; we haven't opened them yet. With them: a real 2023-25 test and a barangay-level check of the index. Also: extend the flood log back to 2015.
- **Source:** issue #19, `docs/requests/`.
- **Visual:** None.

### 12. Close

- **Message:** "Carina, two weeks early": the warning was up on 29 July for the weeks of 5-19 August, from rain and floods alone. A probability, a ranked list and a signed-off plan, every Monday.
- **Visual:** `02_beat1-4_29jul.png` again, or the title image.

## Must not claim

Same list as DEMO.md:

- **"It predicted the surge from case data."** It saw no cases after 2022. Don't quote hospital numbers it didn't see.
- **"The model saw Carina coming on 1 July."** The 1 and 8 Jul warnings are the June gate flood (tide, no storm); the model said 3-6%. The 12 Aug warning is Carina's flood reports, model at 5-9%.
- **"No flood week means dry."** The log only has days a source reported a flood.
- **Raw satellite millimetres.** The 396 mm is on the model's rain scale; raw CHIRPS for that week is 211 mm.
- **"Need jumps tenfold in daytime."** It's +19% (294,414 to 350,119).
- **"The map reshuffles tiers through the replay."** Tiers are fixed per run.
- **San Jose as a gate barangay.** No 2024 source names it.
- **Real stock.** 20,000 is synthetic.

## Screenshots

Already taken from this run at 1600×1000, 2× scale, in `data/demo/screens_20261024-83d68d3/` on Charles's laptop (Charles uploads them to Drive → Data Handoff):

| File | Shows | Slide |
|---|---|---|
| `00_opens_22jul.png` | Page as it opens, 22 Jul, standby | spare |
| `01_beat0_1jul.png` | 1 Jul, WARNING 3/4/6% (gate flood) | 5 |
| `01b_8jul.png`, `01c_15jul.png`, `01d_22jul.png` | 8, 15, 22 Jul | 5 (optional strip) |
| `02_beat1-4_29jul.png` | 29 Jul, WARNING 37/50/33%, rain bars with 396 mm, act-now list | 1, 4, 5, 6, 12 |
| `03_gate_note.png` | Gate note close-up | 6 |
| `04a_5aug.png`, `04b_12aug.png` | 5 and 12 Aug, still on warning | 5 |
| `05_beat5_daytime_29jul.png` | Daytime mode | 7 |
| `06_stock_panel_resident.png`, `06b_stock_panel_daytime.png` | Stock panel close-ups | 8 |
| `07_beat7_backtest_h1.png` | Backtest, Week +1 | 9 |

Still to capture (Charles, during the video session): the stock panel **after Approve plan**, with the "approved" stamp, for slide 8. Reset `audit.jsonl` and `plans/` afterwards (see `docs/handoff/18-demo-video.md`).
