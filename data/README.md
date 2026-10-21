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
| `raw/chirps/` | CHIRPS v2 daily via Earth Engine | `f2f.ingest.rain.chirps_daily`, Navotas polygon, 2015-2024 |
| `raw/events/flood_log.csv` | DSWD DROMIC PDFs, MMDA posts, news | Built by hand. Columns: `date, barangay, kind, depth_code, affected, source_url`. `kind` is `flood`, `gate_down` or `gate_up`. Every row needs a source URL |
| `raw/psa/` | Not needed | The 18-barangay codes and populations ship in `src/f2f/ref/navotas_barangays.csv` (see `docs/DATASETS.md`) |
| `raw/requests/` | Anything from MMCHD, CESU or FOI | Keep the cover letter and date received next to the file |

## Artifacts

`artifacts/<YYYYMMDD>-<git sha>/`:

```
city_week.parquet
forecast.parquet
barangay_index_resident.parquet
barangay_index_daytime.parquet
barangays.geojson         18 polygons for the map
plans/<plan_id>.json      written by the app on approve/reject
audit.jsonl               written by the app
```

Shapes are in [docs/CONTRACTS.md](../docs/CONTRACTS.md). `python -m f2f.export` copies the newest run into `web/public/data/` as JSON for the dashboard (also gitignored).
