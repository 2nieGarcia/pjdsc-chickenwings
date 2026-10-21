# Contracts

What each artifact looks like. `src/f2f/contracts.py` enforces C1-C3 and C7 (`check`) and C6 (`check_boundaries`); `src/f2f/planner.py` enforces C4-C5. Change the code and this file together.

Types: `str`, `date` (pandas datetime64), `int` (nullable `Int64` ok), `num` (int or float), `bool` (nullable `boolean` ok).

## C1 `city_week.parquet`

One row per city per week. Pooled panel, all 12 CCHAIN cities, every Monday from 2008-01-07 through the replay `issue_end` plus 3 weeks. Built by `features.build_city_week`.

| Column | Type | Notes |
|---|---|---|
| `city_psgc` | str | 10-digit PSGC |
| `week_start` | date | Monday |
| `cases` | int | Reported PIDSR cases. Null after 2022, and for 2012-12-31 and 2018-01-01 (missing from source) |
| `elevated` | bool | `cases >= target.elevated_min_cases`. Null where cases is null |
| `pop` | int | WorldPop city total for the year (via CCHAIN; 2021+ repeat 2020). About 16% above census for Navotas; use it as an offset, not a headcount |
| `rain_wk_mm` | num | Sum of daily rain, Mon-Sun. Null unless all 7 days exist. CCHAIN ends 2022-12-31, so 2023+ is null until CHIRPS (#3) |
| `rain_lag1_mm` … `rain_lag6_mm` | num | `rain_wk_mm` k weeks earlier |
| `rain_cum6_lag1_mm` | num | Sum of lags 1-6 |
| `heavy_days` | int | Days ≥ `alerts.heavy_day_mm` that week. Null where `rain_wk_mm` is null |
| `flood_event` | bool | Any `kind=flood` row in the flood log that week (Navotas only). All False until #4's log exists |
| `gate_impaired` | bool | Navotas only; any day of the week inside the config's `gate_impaired` window |
| `source` | str | `cchain` for now; `chirps` rows arrive with #3 |

Invariants: `week_start` is a Monday; `(city_psgc, week_start)` unique.

## C2 `forecast.parquet`

One row per issue date per horizon.

| Column | Type | Notes |
|---|---|---|
| `issue_date` | date | The Monday the forecast is "made" |
| `city_psgc` | str | |
| `h` | int | 1, 2 or 3 |
| `target_week` | date | `issue_date + h weeks` |
| `p_elevated` | num | [0, 1] |
| `q05`, `q50`, `q95` | num | Count quantiles, ordered |
| `alert` | str | `none`, `watch`, `warning` |
| `drivers` | str | JSON list: `[{"feature": "rain_lag2_mm", "contrib": 0.31}, ...]`, top 3 |
| `model` | str | e.g. `event_glm`, `b1_median` |
| `rain_through` | date | Last rain day used. ≤ `issue_date` |
| `cases_through` | date | Last case week used. ≤ `issue_date` |

Alert rule: `watch` if `rain_lag2_mm ≥ 160`; `warning` if `≥ 320` or a flood in lags 1-2 or `p_elevated ≥ alerts.p_cutoff`. The cutoff is tuned on 2019-20 for F2 and frozen in config.

## C3 `barangay_index_<mode>.parquet`

One file per exposure mode, one row per barangay (18).

| Column | Type | Notes |
|---|---|---|
| `psgc10` | str | 10-digit PSGC |
| `name` | str | |
| `parent_psgc_cchain` | str | Pre-2018 parent in CCHAIN's 14 |
| `hazard`, `exposure_res`, `exposure_day`, `vulnerability`, `coping_gap` | num | Each in [1, 10] |
| `exposed_n` | int | People counted as exposed under this mode; feeds the planner |
| `score` | num | Geometric mean of hazard, exposure (mode), vulnerability, coping_gap |
| `tier` | str | `act_now` (top 5), `prepare` (next 6), `monitor` |
| `rank` | int | Under default weights |
| `rank_p05`, `rank_p95` | int | Monte Carlo band |
| `exposure_mode` | str | `resident` or `daytime` |

## C6 `barangays.geojson`

The map's shapes. A FeatureCollection with exactly 18 features, each a Polygon or MultiPolygon in lon/lat (EPSG:4326). Properties are only:

| Property | Type | Notes |
|---|---|---|
| `psgc10` | str | Joins to C3 |
| `name` | str | From `src/f2f/ref/navotas_barangays.csv` |

The pipeline writes it from `data/raw/boundaries/navotas_brgy.geojson`; fixtures write a fake grid. The app adds tier, rank and component values at render time, and never writes them back.

## C7 `metrics.parquet`

Backtest scores, written by the baseline harness (#6). The dashboard's Backtest view reads it.

| Column | Type | Notes |
|---|---|---|
| `model` | str | `event_glm`, `b0_zero`, `b1_median`, `b2_seasonal_nb` (the dashboard shows these four) |
| `h` | int | 1, 2 or 3 |
| `split` | str | `train`, `tune`, `test`; the dashboard shows `test` |
| `metric` | str | `mae`, `mae_nonzero`, `brier` (lower is better); `auc`, `episode_recall` (0-1), `lead_time_wk` (higher is better) |
| `value` | num | NaN where a metric does not apply (B0 has no lead time) |

Invariants: `(model, h, split, metric)` unique; `brier`, `auc` and `episode_recall` in [0, 1] (write 0.64, not 64). Until #6 writes it, `python -m f2f.export` falls back to the fixture scores and flags them `metrics_synthetic`.

## C4 plan

Request (built by the app):

```json
{
  "issue_date": "2024-07-22",
  "uptake": 0.5,
  "buffer": 0.15,
  "stock_on_hand": 20000,
  "exposure_mode": "daytime",
  "synthetic_stock": true,
  "rows": [{"psgc10": "1380900016", "tier": "act_now", "exposed": 1081, "score": 8.4}]
}
```

Response:

```json
{
  "plan_id": "3f9a1c2e",
  "issue_date": "2024-07-22",
  "exposure_mode": "daytime",
  "uptake": 0.5,
  "buffer": 0.15,
  "allocations": [{"psgc10": "1380900016", "need_caps": 2487, "alloc_caps": 2487, "unmet_caps": 0}],
  "total_need": 2487,
  "total_alloc": 2487,
  "stock_on_hand": 20000,
  "status": "draft",
  "synthetic_stock": true
}
```

`plan_id` is the first 8 hex of a SHA-1 over the request, so the same inputs always give the same id.

`need_caps = ceil(exposed × uptake × caps_per_person[tier] × (1 + buffer))`. Allocation goes `act_now → prepare → monitor`, higher score first within a tier.

Invariants: `total_alloc ≤ stock_on_hand`; `0 ≤ alloc_caps ≤ need_caps`; `unmet_caps = need_caps − alloc_caps`. Bad uptake, buffer, stock, mode, tier, negative counts or duplicate barangays raise.

## C5 `audit.jsonl` and `plans/`

One JSON object per line:

```json
{"ts": "2026-10-27T09:14:02+00:00", "plan_id": "3f9a1c2e", "action": "approved", "actor": "CHO duty officer", "note": "pre-position at Tanza 2 HC"}
```

States: `created → approved | rejected`. Both are final; a changed plan is a new `plan_id`. `actor` is required. The full plan is saved as `plans/<plan_id>.json` before it is logged.
