# Handoff: the frozen demo run `20261024-83d68d3` (#18)

For the PM: what this run did, what changed and what didn't, what was tested, and what's left. Written 24 Oct 2026 on branch `data/18-frozen-run`, off `main` at `83d68d3`.

## Executive summary

We rebuilt the demo's data from scratch on a clean laptop, this time with the Carina flood log, and froze the result as run **`20261024-83d68d3`**. That run is now the single source for the demo, the backup video and the pitch deck.

It matters because the previous demo run was built without the flood log, so one of the project's three local signals, the broken Tangos-Tanza gate, never showed up in the replay. With the log in, the replay warns in early July (the gate's tide flood on 24 June) and holds the warning through 12 August (Carina's flood reports).

Nothing in the model or the code changed apart from one dashboard label. Every probability, rain figure, ranking, stock number and backtest score is identical to the previous run. Only the alert levels moved, and we proved that by recomputing the run with the flood log switched off.

## The project in one picture

```
public data ──────────► pipeline (Python) ──────────► one frozen run folder ──► dashboard (offline)
CCHAIN cases + rain      forecast model                forecasts, rankings,      replay slider, map,
CHIRPS satellite rain    barangay priority index       backtest scores,          stock plan,
flood log (hand-built)   backtest vs 3 baselines       manifest of inputs        approve / reject (logged)
```

- **Forecast.** A statistical model (logistic regression, pooled over 12 cities' weekly cases, 2008-2022) gives the chance of a week with 3 or more cases, 1, 2 and 3 weeks ahead. It uses only season and recent rain. An alert rule on top turns that into none / watch / warning.
- **Priority index.** Ranks the 18 barangays on flood hazard, people exposed, vulnerability and distance to care, with a band that shows how stable each rank is.
- **Stock planner.** Turns exposure into doxycycline capsule need and compares it with stock on hand (a labelled synthetic number). An official approves or rejects; the decision is logged and nothing is sent.
- **Demo.** Replays Typhoon Carina (July-August 2024) week by week, using only what was known each Monday.

## Before vs after

| | Before (run `52d538a`, and `4b8e6d6` for dry run 1) | After (run `20261024-83d68d3`) |
|---|---|---|
| Code and architecture | Pipeline, model, index, planner, dashboard | Same. One label changed |
| Inputs | CCHAIN + CHIRPS; **no flood log** on the build machine | CCHAIN + CHIRPS + flood log (14 rows); all re-downloaded on a clean machine |
| Flood signal | Off: `flood_event` False everywhere, the flood part of the alert rule never fired | On: flood weeks 3 Jun, 24 Jun, 22 Jul, 29 Jul 2024 |
| Replay alerts | Warning only on 29 Jul (and 5 Aug, week +1) | Warning on 1 and 8 Jul, 29 Jul, 5 Aug and 12 Aug; quiet on 15 and 22 Jul |
| Probabilities, rain, rankings, plans, backtest | — | Identical to before |
| Stock label | "22 Jul plan", whatever week the slider is on | "Plan issued 22 Jul · same for every replay week" |
| Demo script and handoffs | Tied to the old run; backup video without flood warnings | DEMO.md re-checked number by number; video checklist and deck outline written |
| Reproducibility | Built once on one machine | Rebuilt end to end from public sources on a second machine |

## Major changes

| File | What | Why |
|---|---|---|
| `web/src/main.js` | Stock label reads "Plan issued 22 Jul · same for every replay week · …"; the full text is also a tooltip | The plan comes from the barangay index, which doesn't change by week. The old label read like a bug |
| `docs/DEMO.md` | New run id; beat 1 rain wording (71-145 mm, the old 45-145 was wrong); new beat 3 ("the gate flood already had the city on warning") and the click path through 12 Aug; flood-log alert table; two new "must not claim" items; two Q&A rows; rain-scale counts restated; dry run 1b row; empty dry run 2 row | So the script matches what the judges will see in this run |
| `docs/handoff/18-demo-video.md` | Recording checklist: setup, click path, expected value on screen per beat, reset steps | For recording the backup video from this run |
| `docs/handoff/18-pitch-deck-outline.md` | Slide outline with every number, its source file and the run id; screenshot list | For building the deck without running anything |
| `docs/handoff/18-frozen-run.md` | This file | PM review |

Outside git:

- `data/raw/events/flood_log.csv` uploaded to Drive → [Data Handoff](https://drive.google.com/drive/folders/1bgDX8nMi6x-VAr-oe7XzpabIcsDxsEEN) ([file](https://drive.google.com/file/d/15jF783vMsMJ5T1fQJWX2cpvc5v6irCu4/view)), checksum verified (md5 `e02b59faf5ba54208112efdb8f2e83e9`).
- The run folder `data/artifacts/20261024-83d68d3/` and 13 screenshots in `data/demo/screens_20261024-83d68d3/` are on Charles's laptop. `data/` is gitignored.

## Alerts and warnings

There are two unrelated kinds.

### Alert levels on the dashboard: risk signals, not faults

From `src/f2f/forecast/event_model.py` (`_alerts`) and contract C2 in `docs/CONTRACTS.md`:

| Level | Fires when | Means |
|---|---|---|
| **Warning** | Any one of: rain in the last complete week before the issue Monday ≥ 320 mm; a flood logged in either of the two weeks before the issue Monday; the model's probability ≥ 0.26 (`alerts.p_cutoff`) | High-risk condition: get ready. It also switches on the act-now list |
| **Watch** | Not a warning, and that week's rain ≥ 160 mm | Elevated rain. It doesn't occur in this replay: no week fell between 160 and 320 mm |
| **None** | Neither | Quiet; the act-now list goes to standby |

What fired in this run:

| Issue | Model (week +1/+2/+3) | Alert | Trigger |
|---|---|---|---|
| 1 Jul | 3/4/6% | warning | 24 Jun gate tide flood |
| 8 Jul | 3/4/6% | warning | 24 Jun flood |
| 15 Jul | 4/5/8% | none | |
| 22 Jul | 7/9/11% | none | |
| 29 Jul | 37/50/33% | warning | Model past the cutoff, 396 mm, 22 Jul flood |
| 5 Aug | 35/16/17% | warning | Floods on 22 and 29 Jul; the model alone holds week +1 |
| 12 Aug | 5/6/9% | warning | 29 Jul flood only |

The new warnings are expected behaviour, defined in the contract since #4 and #8. They mean "a flood happened recently", not "the model predicts a bad week", which is why a card can read WARNING next to 3%. Two cautions:

- **The flood trigger is blunt.** One news report keeps all three cards on warning for two weeks, and the log can't tell a tide flood from a rain flood.
- **The flood trigger has never been backtested.** The 2021-22 test period has no flood data, so the backtest scores (AUC 0.95 and the rest) say nothing about it.

### System messages: none that affect reliability fired

| Message | Effect if it appears | This run |
|---|---|---|
| `step '…': missing <file>`, contract check errors | Hard failure; the run stops | None |
| `warning: no …chirps…csv` | Replay has no real rain; the dashboard falls back to rain labelled "illustrative" | Didn't occur |
| `warning: no …flood_log.csv` | Flood trigger off everywhere | Didn't occur; `manifest.json` has `flood_log: true` |
| `forecast_synthetic` / `rain_synthetic` / `metrics_synthetic` in `meta.json` | Dashboard labels the fake parts | All false |
| 15 × `Pandas4Warning` (`Series.dt.dayofweek`) in the tests | None today; breaks on a future pandas major release | Harmless now; worth a small fix later |
| Vite "chunks larger than 500 kB" | Load-speed hint | Harmless offline |

## Validation and testing

What was actually checked, on Charles's laptop (Windows 11, Python 3.12, pandas 3.1, numpy 2.5, Node 22):

| Check | Result |
|---|---|
| `pytest -q` | 86 passed (15 deprecation warnings, above) |
| `npm test` in `web/` | 4 passed |
| Pipeline from scratch: `f2f.ingest.fetch`, `f2f.ingest.rain`, `f2f.run`, `f2f.export`, `npm run build` | All succeeded. CHIRPS took about 30 min (IRI was slow); its quarters are cached |
| `manifest.json` | `flood_log: true`; rain sources `cchain`, `chirps`; cases through 26 Dec 2022; rain through 25 Aug 2024 |
| Flood-log effect, isolated | Recomputed the forecast with the flood log off: probabilities identical (max difference 0.0); alerts match the old run; 11 of 21 issue-and-horizon cells change to warning with the log |
| Every DEMO.md number | Extracted from the run's files and compared one by one; all match except the beat 1 rain wording, now fixed |
| Rain-scale claims | CHIRPS = 0.80 × CCHAIN and 0 vs 11 weeks ≥ 320 mm reproduce. #48's heavy-week counts reproduce for raw (6) and one scale factor (7); quantile mapping gives 11 where #48 had 10 |
| Dashboard, scripted with Playwright (Chrome, 1600×1000) | Every beat's on-screen values match the files. No console errors. No request outside 127.0.0.1 |
| New label at 1280, 1366 and 1920 px | The key text is always visible; only "f2f.planner" is cut off, and the tooltip has it |
| Drive upload | Downloaded back; md5 matches |

Not tested in this run:

- **Approve / reject.** Not clicked, so no `audit.jsonl` was written. Dry run 1 checked it on the earlier run.
- **Dry run 2 with the speaker and a timer.** Still to do.
- **The actual demo laptop.** This run was built and checked on Charles's laptop only.
- **The flood trigger against outcomes.** There's no data for it.
- **The Streamlit fallback app.** Only through its unit test.

## Known limitations

- **No case data after 2022.** 2024 is a replay on rain, season and floods. Nothing is checked against real 2024 cases.
- **Satellite rain still reads dry after mapping** (above).
- **The flood log is small and one-sided.** 14 hand-collected reports from June-August 2024. A week with no report isn't a dry week, and tide and rain floods aren't separated.
- **Floods aren't in the model fit.** The training years have no flood data, so floods only enter through the alert rule.
- **Stock on hand (20,000 capsules) is synthetic.** City-level cases only, so the barangay ranking can't be checked against barangay cases.
- **Sprint 1 model.** One logistic regression per horizon. It weakens with distance: AUC 0.95 at 1 week, 0.87 at 2, 0.78 at 3. LightGBM is planned for Sprint 2.
- **No on-screen reason for a warning.** A card can read "WARNING 3%" with nothing saying why. The script and Q&A cover it; a "flood" tag on the card would fix it properly (post-demo).

## Current status

| | State |
|---|---|
| Frozen run `20261024-83d68d3` | Ready |
| Dashboard build with the label fix | Ready (offline-checked) |
| DEMO.md, video checklist, deck outline | Ready for review (this PR) |
| Dry run 2 (speaker, timer) | Pending |
| Backup / demo video | In production. The competition limit is now **3 minutes**, so the 5-minute DEMO.md script will be cut down for the video |
| Pitch deck | In production. The limit is **20 slides**; the outline in `18-pitch-deck-outline.md` will be reworked to fit and complement the video |
| #19 request letters | Waiting on the adviser's signature |
| Narration for the video | Choosing a tool (AI voice); see the PR discussion |

### For the PM to review

1. **The new beat 3 story.** The replay now opens on WARNING at 3-6%, explained as the gate flood. Is that the line we want in front of judges?
2. **The flood trigger.** Keep it as is for the demo, given it's blunt and untested? The alternative is counting only rain-driven floods, which needs a new column in the log.
3. **Stale docs, not edited in this PR:**
   - `docs/SPRINTS.md` beat 3 skips the early-July warnings; beat 4 still says the tiers "reshuffle".
   - `docs/handoff/4-carina-flood-log.md` still asks #13 to record the log in the manifest (done in #45), lists San Jose on the gate list (removed in #44), and leaves #8's flood decision open (settled in DEMO.md).
   - `data/README.md` and the #4 handoff link the parent Drive folder, not Data Handoff.
   - `src/f2f/ingest/rain.py` describes the 10-of-17 check as "recovered", which reads as hits; it's a count of heavy weeks.

## Recommended next steps

- **Don't rerun the pipeline for the demo.** The run id is the date plus the git sha, so after this PR merges a rerun gets a new id and every reference needs re-checking. To rebuild the dashboard, export this run explicitly: `python -m f2f.export --run data/artifacts/20261024-83d68d3`.
- **Copy the run folder to the demo laptop as is**, rather than rebuilding there.
- **After the competition:**
  - Add a flood or rain reason tag to the alert cards.
  - Add a tide/rain column to the flood log, and extend it back to 2015 so the flood trigger can be backtested.
  - Replace `dt.dayofweek` before the next pandas major release.
  - Fix the stale docs listed above.
- **Data requests (#19).** Barangay-level weekly cases from MMCHD, CESU or DOH would allow a real 2023-25 test and a barangay-level check of the index.
