# Flood-to-Fever

Leptospirosis early warning and decision support for Navotas City. PJDSC 2026 entry, team Chicken Wings.

Each week it answers four questions for the City Health Office:

1. **How likely is an elevated leptospirosis week 1-3 weeks out?** Probability of ≥ 3 reported cases, with count ranges, driven by lagged rainfall, observed floods and the navigational-gate status.
2. **Which barangays go first?** INFORM-style index (hazard, exposure, vulnerability, coping gap), shown as rank bands, not one number.
3. **Who is exposed but doesn't live there?** Resident vs daytime exposure, mainly the Navotas Fish Port workforce.
4. **Is there enough doxycycline?** Capsule need vs usable stock, allocated by tier, never past what's on hand. An official approves or rejects every plan.

It does not diagnose, prescribe, decide eligibility, or send anything on its own.

## Why "elevated week" and not case counts

Navotas reported 471 cases in 780 weeks (2008-2022), 75% of them zero weeks. On MAE, "predict zero every week" beats most models, including during outbreaks. So the primary output is the probability of an elevated week, scored on Brier, episode recall and lead time, with MAE reported as a secondary number against three baselines. Details in [docs/DATASETS.md](docs/DATASETS.md).

## Quickstart

Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use source .venv/bin/activate elsewhere
pip install -e ".[dev]"
pytest -q
```

No data yet? `python -m f2f.fixtures` writes a fake artifact folder so you can work on the app straight away.

Get the raw data into `data/raw/` (see [data/README.md](data/README.md)), then:

```bash
python -m f2f.ingest.fetch                           # CCHAIN tables from HDX + polygons, ~260 MB
python -m f2f.run --config configs/carina_2024.yaml   # writes data/artifacts/<run_id>/
python -m f2f.export                                 # artifacts -> web/public/data/*.json
cd web && npm install && npm run dev                 # the dashboard, http://127.0.0.1:5173
```

The dashboard is a static Vite app (three.js + GSAP, fonts bundled), so it runs with Wi-Fi off once `npm install` has run. For the demo, build it and serve it with the local recorder, which also writes plan decisions to the run's `audit.jsonl`:

```bash
cd web && npm run build && cd ..
python -m f2f.serve                                  # http://127.0.0.1:8600, localhost only
```

Two views: **Replay** (the Carina 2024 replay) and **Backtest** (`#backtest`: the event model against the B0/B1/B2 baselines, the demo's closing beat). In `npm run dev`, Vite proxies `/api` to the same server, so start `python -m f2f.serve` alongside it to record decisions. Without it the stock panel is read-only. The older Streamlit app (`streamlit run app/streamlit_app.py`) still works as a fallback. The visual system is in [DESIGN.md](DESIGN.md).

CHIRPS rain comes from the IRI Data Library mirror with no login (`python -m f2f.ingest.rain`). Earth Engine is optional: `pip install -e ".[ee]"` and `EE_PROJECT` set (copy `.env.example` to `.env`).

## Layout

```
web/            the dashboard: Vite + three.js + GSAP, reads web/public/data/*.json
app/            older Streamlit dashboard (fallback)
configs/        base.yaml + one file per replay scenario
data/           not in git; raw/, interim/, artifacts/
docs/           architecture, contracts, datasets, sprint plan
src/f2f/        pipeline: ingest -> features -> forecast / index -> planner
tests/
```

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/CONTRACTS.md](docs/CONTRACTS.md). Using an LLM? Paste [docs/MASTER_PROMPT.md](docs/MASTER_PROMPT.md) first. If you change an artifact's shape, change `src/f2f/contracts.py` and `docs/CONTRACTS.md` in the same PR.

## Data rules

- No raw data, no patient-level records, no credentials in git.
- Synthetic stock is labelled synthetic everywhere it shows up and never mixed with real records.
- PIDSR and FHSIS counts are never summed.
- LiPAD layers stay internal (EULA bars redistribution). Publish NOAH-derived layers instead.

## Team

Chicken Wings: Matthew John T. Bote, Charles John R. Cabatian, Antonio B. Garcia Jr., Ken Ira L. Lacson, Renz Jerik C. Viloria.

## Data credits

Project CCHAIN (Thinking Machines, CC BY 4.0), CHIRPS (UCSB CHC), PSA PSGC and 2024 POPCEN, UP NOAH, Google Open Buildings, Mapbox isochrones and the DOH health facility geoportal (all via CCHAIN), DSWD DROMIC reports, barangay boundaries from faeldon/philippines-json-maps (MIT).
