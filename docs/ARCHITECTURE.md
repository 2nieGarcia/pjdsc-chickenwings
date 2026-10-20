# Architecture

```
data/raw ──> ingest/*  ──> data/interim/*.parquet
                │
                ├─> features.py ──> city_week          (C1)
                │                      │
                │                      ├─> forecast/*  ──> forecast        (C2)
                │                      │
                ├─> index.py ─────────────────────────> barangay_index    (C3)
                │
                └──────────── all of the above land in data/artifacts/<run_id>/

app/streamlit_app.py
    reads   artifacts/<run_id>/*.parquet
    runs    planner.make_plan in-process (pure function)          (C4)
    writes  plans/<plan_id>.json + audit.jsonl on approve/reject  (C5)
```

## Boundary

In: weekly city forecast, barangay ranking, exposure scenarios, capsule arithmetic, a record of who approved what.

Out: diagnosis, eligibility, dispatching stock, sending alerts, patient-level data, live feeds. The app records a decision; a person acts on it.

## Decisions

**Batch, file-based, no API server.** The pipeline runs once per scenario and writes a folder. The app reads the folder. The folder layout and the contracts are the interface between lanes. A server buys us nothing for a demo with weekly data, and offline works on a venue Wi-Fi that won't.

**Replay is pre-computed.** For Carina 2024 the pipeline issues a forecast every Monday from 1 Jul to 15 Aug as if it were that day: only data up to `issue_date` is visible. The slider just picks rows. `contracts.check` rejects any row whose `rain_through` or `cases_through` is after its `issue_date`.

**One direct model per horizon.** h = 1, 2, 3 each get their own fit. A feature lagged k weeks behind the target may feed horizon h only if k ≥ h. Case lags add the reporting delay on top.

**Event target, pooled panel.** See [DATASETS.md](DATASETS.md). Short version: Navotas alone has ~40 positive weeks.

**Index ranks with bands.** 18 units and no barangay outcomes means weights are a guess. We show the median rank and the 5-95% band from 10,000 jittered-weight draws, and the four components separately.

**Planner is a pure function.** Same inputs, same allocation. Greedy by tier then score, capped at usable stock, rounded up per barangay. Tested for over-allocation on random inputs.

## Run

```
python -m f2f.run --config configs/carina_2024.yaml
```

`run_id` is `YYYYMMDD-<short sha>`. Re-running on the same commit overwrites the same folder, which is what we want during the sprint. Tag the folder you demo from.

## Adding a step

1. Write the function in `src/f2f/`.
2. If it produces an artifact, add its spec to `contracts.py` and `docs/CONTRACTS.md`.
3. Call it from `run.py` and run `contracts.check` on the output before writing it.
