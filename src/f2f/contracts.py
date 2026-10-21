"""Column specs and invariants for every artifact the app reads.

docs/CONTRACTS.md is the readable version. Change both or neither.
"""
import pandas as pd
from pandas.api import types as pt

ALERTS = {"none", "watch", "warning"}
TIERS = {"act_now", "prepare", "monitor"}
EXPOSURE_MODES = {"resident", "daytime"}
SPLITS = {"train", "tune", "test"}
# lower is better for the first three, higher for the rest
METRICS = {"mae", "mae_nonzero", "brier", "auc", "episode_recall", "lead_time_wk"}
PROBABILITY_METRICS = {"brier", "auc", "episode_recall"}

_RAIN_LAGS = {f"rain_lag{k}_mm": "num" for k in range(1, 7)}

SPECS = {
    "city_week": {
        "city_psgc": "str",
        "week_start": "date",
        "cases": "int",
        "elevated": "bool",
        "pop": "int",
        "rain_wk_mm": "num",
        **_RAIN_LAGS,
        "rain_cum6_lag1_mm": "num",
        "heavy_days": "int",
        "flood_event": "bool",
        "gate_impaired": "bool",
        "source": "str",
    },
    "forecast": {
        "issue_date": "date",
        "city_psgc": "str",
        "h": "int",
        "target_week": "date",
        "p_elevated": "num",
        "q05": "num",
        "q50": "num",
        "q95": "num",
        "alert": "str",
        "drivers": "str",
        "model": "str",
        "rain_through": "date",
        "cases_through": "date",
    },
    "metrics": {
        "model": "str",
        "h": "int",
        "split": "str",
        "metric": "str",
        "value": "num",
    },
    "barangay_index": {
        "psgc10": "str",
        "name": "str",
        "parent_psgc_cchain": "str",
        "hazard": "num",
        "exposure_res": "num",
        "exposure_day": "num",
        "vulnerability": "num",
        "coping_gap": "num",
        "exposed_n": "int",
        "score": "num",
        "tier": "str",
        "rank": "int",
        "rank_p05": "int",
        "rank_p95": "int",
        "exposure_mode": "str",
    },
}

_KIND_OK = {
    "str": lambda s: pt.is_string_dtype(s) or s.isna().all(),
    "date": pt.is_datetime64_any_dtype,
    "int": lambda s: pt.is_integer_dtype(s) and not pt.is_bool_dtype(s),
    "num": lambda s: pt.is_numeric_dtype(s) and not pt.is_bool_dtype(s),
    "bool": pt.is_bool_dtype,
}


def check(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Raise ValueError listing every problem; return df untouched if clean."""
    spec = SPECS[name]
    errors = [f"missing column {c}" for c in spec if c not in df.columns]
    errors += [
        f"{c}: expected {kind}, got {df[c].dtype}"
        for c, kind in spec.items()
        if c in df.columns and not _KIND_OK[kind](df[c])
    ]
    if not errors:
        errors = _INVARIANTS[name](df)
    if errors:
        raise ValueError(f"{name} contract broken:\n  " + "\n  ".join(errors))
    return df


def _city_week(df):
    errs = []
    if (df["week_start"].dt.dayofweek != 0).any():
        errs.append("week_start must be a Monday")
    if df.duplicated(["city_psgc", "week_start"]).any():
        errs.append("duplicate (city_psgc, week_start)")
    return errs


def _forecast(df):
    errs = []
    if not df["h"].isin([1, 2, 3]).all():
        errs.append("h must be 1, 2 or 3")
    if not df["p_elevated"].between(0, 1).all():
        errs.append("p_elevated outside [0, 1]")
    if ((df["q05"] > df["q50"]) | (df["q50"] > df["q95"])).any():
        errs.append("quantiles not ordered q05 <= q50 <= q95")
    if not df["alert"].isin(ALERTS).all():
        errs.append(f"alert not in {sorted(ALERTS)}")
    # data newer than the issue date means the replay leaked the future
    if (df["rain_through"] > df["issue_date"]).any() or (df["cases_through"] > df["issue_date"]).any():
        errs.append("rain_through/cases_through after issue_date")
    return errs


def _barangay_index(df):
    errs = []
    comps = ["hazard", "exposure_res", "exposure_day", "vulnerability", "coping_gap"]
    if not df[comps].apply(lambda s: s.between(1, 10)).all().all():
        errs.append("component scores must sit in [1, 10]")
    if not df["tier"].isin(TIERS).all():
        errs.append(f"tier not in {sorted(TIERS)}")
    if not df["exposure_mode"].isin(EXPOSURE_MODES).all():
        errs.append(f"exposure_mode not in {sorted(EXPOSURE_MODES)}")
    if df.duplicated(["psgc10", "exposure_mode"]).any():
        errs.append("duplicate (psgc10, exposure_mode)")
    if (df["rank_p05"] > df["rank_p95"]).any():
        errs.append("rank_p05 > rank_p95")
    return errs


def _metrics(df):
    errs = []
    if not df["h"].isin([1, 2, 3]).all():
        errs.append("h must be 1, 2 or 3")
    if not df["split"].isin(SPLITS).all():
        errs.append(f"split not in {sorted(SPLITS)}")
    if not df["metric"].isin(METRICS).all():
        errs.append(f"metric not in {sorted(METRICS)}")
    if df.duplicated(["model", "h", "split", "metric"]).any():
        errs.append("duplicate (model, h, split, metric)")
    prob = df[df["metric"].isin(PROBABILITY_METRICS)]["value"].dropna()
    if not prob.between(0, 1).all():
        errs.append(f"{sorted(PROBABILITY_METRICS)} must be in [0, 1] (write 0.64, not 64)")
    return errs


_INVARIANTS = {"city_week": _city_week, "forecast": _forecast, "barangay_index": _barangay_index, "metrics": _metrics}


def check_boundaries(fc: dict) -> dict:
    """barangays.geojson: FeatureCollection, 18 Polygon/MultiPolygon features, unique psgc10 + name properties."""
    errs = []
    feats = fc.get("features", []) if fc.get("type") == "FeatureCollection" else None
    if feats is None:
        errs.append("not a FeatureCollection")
    else:
        codes = [f.get("properties", {}).get("psgc10") for f in feats]
        if len(feats) != 18 or len(set(codes)) != 18 or not all(isinstance(c, str) for c in codes):
            errs.append("need 18 features with unique string psgc10")
        if any(not f.get("properties", {}).get("name") for f in feats):
            errs.append("every feature needs a name")
        if any((f.get("geometry") or {}).get("type") not in ("Polygon", "MultiPolygon") for f in feats):
            errs.append("geometries must be Polygon or MultiPolygon")
    if errs:
        raise ValueError("barangays.geojson contract broken:\n  " + "\n  ".join(errs))
    return fc
