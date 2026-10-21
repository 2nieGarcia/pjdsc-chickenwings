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
| `raw/cchain/location.csv`, `project_noah_hazards.csv`, `google_open_buildings.csv` | Project CCHAIN (public mirror for now) | `python -m f2f.ingest.static` |
| `raw/boundaries/navotas_brgy.geojson` | faeldon/philippines-json-maps 2023, 18 barangays | `python -m f2f.ingest.static` |
| `raw/osm/hotosm_phl_health_facilities.zip` | HOT OSM via HDX | `python -m f2f.ingest.static` |
| `raw/cchain/*.csv` (the rest) | Project CCHAIN, Kaggle doi 10.34740/kaggle/ds/4918229 | Download the whole set (#1). Navotas is `adm3_pcode == PH137503000` |
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

Shapes are in [docs/CONTRACTS.md](../docs/CONTRACTS.md).
