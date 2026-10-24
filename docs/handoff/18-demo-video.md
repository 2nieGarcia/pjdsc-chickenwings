# Handoff: recording the demo video from the frozen run (#18)

A checklist for recording the backup video from run `20261024-83d68d3`. The talk track is [docs/DEMO.md](../DEMO.md); this file is the click path and what must be on screen at each beat. If the two ever disagree, DEMO.md wins and this file is out of date.

## The run

| | |
|---|---|
| Run id | `20261024-83d68d3` (main at `83d68d3`, plus the uncommitted stock-label fix in `web/src/main.js`, which changes no artifact) |
| Folder | `data/artifacts/20261024-83d68d3/` |
| Inputs (`manifest.json`) | CCHAIN (9 tables, cases through 26 Dec 2022), CHIRPS daily 2015-01-01 to 2024-08-31 (rain through 25 Aug 2024), `flood_log: true` (14 rows, md5 `e02b59faf5ba54208112efdb8f2e83e9`) |
| Tests | 86 Python, 4 web, all passing |

## Setup

1. Laptop on power, notifications off (Windows: Focus assist / Do not disturb), every other window closed.
2. From the repo root, with the project venv:
   ```
   .venv\Scripts\python -m f2f.export --run data/artifacts/20261024-83d68d3
   cd web && npm run build && cd ..
   ```
   Pass `--run` so a later run folder can't be picked up by accident.
3. Reset the approval beat: delete `data/artifacts/20261024-83d68d3/audit.jsonl` and the folder `data/artifacts/20261024-83d68d3/plans/` if they exist. Do this before **every** take: a plan can be approved once, so a second take's **Approve plan** would fail.
4. Wi-Fi off. Then `.venv\Scripts\python -m f2f.serve` and open http://127.0.0.1:8600 in Chrome.
5. Browser at 100% zoom, full screen (F11), 1920×1080 if the screen allows. The screenshots in `data/demo/screens_20261024-83d68d3/` were taken at 1600×1000.
6. Check the header reads **run 20261024-83d68d3**, the rain chip **Rain through 21 Jul 2024** and the cases chip **Cases through 26 Dec 2022 (PIDSR)**.
7. The page opens on 22 Jul. Press **Prev week** 3 times: the date reads **1 Jul 2024**. Start recording here.
8. Recorder: OBS or Xbox Game Bar (Win+Alt+R) both work. Save as `backup_20261024-83d68d3` with whatever extension the recorder gives (`.webm` or `.mp4`). If it isn't `.webm`, change the filename in DEMO.md "Before you start" step 6 to match.

## Click path and what's on screen

"Say" is the key line; the full words are in the DEMO.md row with the same number.

| # | Do | On screen (check before moving on) | Say (key line) |
|---|---|---|---|
| 0 | Nothing; slider on **1 Jul 2024** | Cards: Week +1 **WARNING 3%**, Week +2 **WARNING 4%**, Week +3 **WARNING 6%**. Rain bars all "not yet". Act-now list on. Don't explain the warnings yet | "471 cases in 780 weeks, 2008-2022; three weeks in four had none." |
| 1 | **Next week** ×4, to **29 Jul 2024**. Point at the rain bars | Bars 71, 89, 145, **396**, then "not yet" ×3. 396 is above the red "warning 320 mm" line | "The week of 22 Jul is Carina: 396 mm, past the 320 mm warning line. The three weeks before it are 71 to 145." |
| 2 | Point at the gate note under the map | "Gate impaired since 7 Jun 2024 · Tanza 1, Tanza 2, Tangos North, Tangos South" | "Hit by a barge on 7 June … open to the tide all through Carina." |
| 3 | On 29 Jul, the three cards. Then **Next week** to 5 Aug, and again to **12 Aug 2024**. Stay on 12 Aug | 29 Jul: **WARNING 37% / 50% / 33%**. 5 Aug: **WARNING 35% / 16% / 17%**. 12 Aug: **WARNING 5% / 6% / 9%**; bars 71, 89, 145, 396, 42, 89 | "Before Carina, the gate flood already had the city on warning … By 12 August it's back to 5-9%, and only Carina's flood reports keep it on warning." |
| 4 | Act-now list; hover a rank band | 1 Tanza 2 (6.70, 1–3), 2 Tangos South (6.50, 1–2), 3 Tangos North (6.41, 2–4), 4 Tanza 1 (6.03, 3–4), 5 Bagumbayan South (5.44, 5–6) | "Tanza 2, Tangos South, Tangos North, Tanza 1, Bagumbayan South … the top four are solid." |
| 5 | **Daytime** toggle (top right of the map) | Map caption "daytime scenario: residents × 0.93 + 30,000 port workers". Stock: need **350,119**, unmet **330,119**, "16.5× on hand". Act-now names unchanged | "Exposure there goes from 41,000 to 55,000 people, and the capsule need from 294,000 to 350,000 at 50% uptake." |
| 6 | **Residents** toggle. Stock panel: point at the numbers, type a name in **Official**, click **Approve plan** | On hand **20,000** (synthetic), need **294,414**, unmet **274,414**, "13.7× on hand", 50% uptake selected. Label "Plan issued 22 Jul · same for every replay week · residents …". After approve: an **approved** stamp with your name, "logged to audit.jsonl. Nothing is dispatched from here." | "20,000 on hand, labelled synthetic … 13.7 times what's on hand … It's one plan, issued 22 July, the same every replay week … nothing is dispatched." |
| 7 | **Backtest** (left rail), then **Week +1** | MAE 0.49 for the event model and for "predict zero"; AUC **0.95**; episodes caught **67%** against 0% for every baseline; median lead **1.0** weeks | "Predicting zero ties us at 0.49 … the event model catches two of three, a week ahead, AUC 0.95." |

Stop recording. Check the file plays, then reset again (setup step 3) so the live demo starts clean.

## What not to claim

From DEMO.md, the ones the recording can most easily get wrong:

- The 1 and 8 Jul warnings are **not** the model seeing Carina. They're the 24 June gate flood tripping the flood rule; the model said 3-6%. Same for 12 Aug (model 5-9%).
- It saw no cases after 2022. Don't say it predicted the surge from case data, and don't quote hospital numbers.
- The rain bars are on the CCHAIN scale, not raw CHIRPS (raw for Carina's week is 211 mm).
- Daytime need is +19%, not tenfold.
- Tiers don't reshuffle through the replay; only the alert switches the list on and off.
- San Jose isn't a gate barangay.
- The stock number is synthetic.

## After recording

- Upload the video to Drive → Data Handoff (https://drive.google.com/drive/folders/1bgDX8nMi6x-VAr-oe7XzpabIcsDxsEEN).
- Keep a copy in `data/demo/` on this laptop.
- Fill in the dry run 2 row of DEMO.md (date, time, issues).
