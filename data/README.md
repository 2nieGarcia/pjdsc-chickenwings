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
| `raw/cchain/*.csv` | Project CCHAIN, Kaggle doi 10.34740/kaggle/ds/4918229 | Download the whole set. Navotas is `adm3_pcode == PH137503000` |
| `raw/chirps/` | CHIRPS v2 daily via Earth Engine | `f2f.ingest.rain.chirps_daily`, Navotas polygon, 2015-2024 |
| `raw/events/flood_log.csv` | DSWD DROMIC PDFs, MMDA posts, news | Built by hand. Columns: `date, barangay, kind, depth_code, affected, source_url`. `kind` is `flood`, `gate_down` or `gate_up`. Every row needs a source URL |
| `raw/boundaries/` | HDX COD-AB Philippines (adm4) | Check that all 18 Navotas barangays exist; fall back to CCHAIN's 14 if not |
| `raw/psa/` | PSA PSGC 3Q-2026 datafile, 2024 POPCEN barangay table | XLSX as published |
| `raw/requests/` | Anything from MMCHD, CESU or FOI | Keep the cover letter and date received next to the file |

## Artifacts

`artifacts/<YYYYMMDD>-<git sha>/`:

```
city_week.parquet
forecast.parquet
barangay_index_resident.parquet
barangay_index_daytime.parquet
plans/<plan_id>.json      written by the app on approve/reject
audit.jsonl               written by the app
```

Shapes are in [docs/CONTRACTS.md](../docs/CONTRACTS.md).
