# data/

Nothing in here is committed except this file.

```
raw/        as downloaded, never edited by hand (except events/)
interim/    cleaned parquet, safe to delete and rebuild
artifacts/  <run_id>/ folders the app reads; one per pipeline run
```

## What goes in raw/

| Path | Source | How |
|---|---|---|
| `raw/cchain/*.csv` | Project CCHAIN on HDX (official, CC BY 4.0): disease, downscaled climate, WorldPop, location, NOAH, Open Buildings, Mapbox isochrones, DOH geoportal | `python -m f2f.ingest.fetch`. Navotas is `adm3_pcode == PH137503000` |
| `raw/boundaries/navotas_brgy.geojson` | faeldon/philippines-json-maps 2023, 18 barangays | `python -m f2f.ingest.fetch` |
| `raw/chirps/` | CHIRPS v2 daily via the IRI Data Library mirror (no login) | `python -m f2f.ingest.rain` -> `navotas_daily.csv`, area-weighted over the Navotas polygon, 2015-01-01 to 2024-08-31 |
| `raw/events/flood_log.csv` | DSWD DROMIC PDFs, MMDA posts, news | Built by hand, see below. Columns: `date, barangay, kind, depth_code, affected, source_url`. `kind` is `flood`, `gate_down` or `gate_up`. Every row needs a source URL |
| `raw/psa/` | Not needed | The 18-barangay codes and populations ship in `src/f2f/ref/navotas_barangays.csv` (see `docs/DATASETS.md`) |
| `raw/requests/` | Anything from MMCHD, CESU or FOI | Keep the cover letter and date received next to the file |

## Flood log

One row per barangay per source report. The Carina 2024 log (#4) covers 1 Jun to 31 Aug 2024: 14 rows, 7 Jun to 24 Aug. It's not in git; get it from the [team Drive](https://drive.google.com/drive/folders/1DhX718zN8rEeTwgC2A0noxeRgA2WeDqs?usp=sharing). What it means for the model, replay, index and demo issues is in [docs/handoff/4-carina-flood-log.md](../docs/handoff/4-carina-flood-log.md).

- `date`: the day the source reports the condition; for DROMIC, the report's "as of" date. Later revisions of the same event don't get a row, because every `kind=flood` row marks its week as a flood week.
- `barangay`: the 18-barangay `name` from `src/f2f/ref/navotas_barangays.csv` ("Tanza I" or "Tanza Uno" is `Tanza 1`). Use the CCHAIN parent name (`Tanza`, `Tangos`) when the source doesn't say which child, and leave it blank when the source only gives a city figure.
- `gate_down` / `gate_up`: the day the Tangos-Tanza gate stopped / started holding back high tide. Gate rows go on Tanza 1, where the gate is.
- `depth_code`: MMDA's depth terms: `below_gutter` (under 8 in), `gutter` (8), `half_knee` (9-10), `half_tire` (13), `knee` (19), `tire` (26), `waist` (37), `chest` (45). Blank if the source gives none.
- `affected`: persons. Blank when the source only gives families.

Known gaps: the DROMIC Carina reports never name Navotas barangays, only city totals. No 2024 source names San Jose (Pob.), so it is off the config gate list (#39); the only 2024 mention found is its barangay hall used as an evacuation centre (Manila Bulletin, 24 Jul 2024). Sources say "Tangos", never North or South, so both stay on the list.

## Artifacts

`artifacts/<YYYYMMDD>-<git sha>/`:

```
city_week.parquet
forecast.parquet
barangay_index_resident.parquet
barangay_index_daytime.parquet
barangays.geojson         18 polygons for the map
metrics.parquet           backtest scores (#6)
manifest.json             inputs, git sha and freshness dates (#13)
plans/<plan_id>.json      written by the app on approve/reject
audit.jsonl               written by the app
```

Shapes are in [docs/CONTRACTS.md](../docs/CONTRACTS.md). `python -m f2f.export` copies the newest run into `web/public/data/` as JSON for the dashboard (also gitignored).
