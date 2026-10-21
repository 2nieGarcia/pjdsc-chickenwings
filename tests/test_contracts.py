from pathlib import Path

import pandas as pd
import pytest

from f2f.config import load, merge
from f2f.contracts import check


def city_week():
    df = pd.DataFrame({
        "city_psgc": ["1380900000"] * 2,
        "week_start": pd.to_datetime(["2022-08-01", "2022-08-08"]),
        "cases": pd.array([0, None], dtype="Int64"),
        "elevated": pd.array([False, None], dtype="boolean"),
        "pop": [252878, 252878],
        "rain_wk_mm": [120.0, 340.5],
        "rain_cum6_lag1_mm": [600.0, 610.0],
        "heavy_days": [1, 3],
        "flood_event": [False, True],
        "gate_impaired": [False, False],
        "source": ["cchain_pidsr"] * 2,
    })
    for k in range(1, 7):
        df[f"rain_lag{k}_mm"] = 50.0
    return df


def forecast():
    return pd.DataFrame({
        "issue_date": pd.to_datetime(["2024-07-22"]),
        "city_psgc": ["1380900000"],
        "h": [2],
        "target_week": pd.to_datetime(["2024-08-05"]),
        "p_elevated": [0.62],
        "q05": [0.0], "q50": [2.0], "q95": [7.0],
        "alert": ["warning"],
        "drivers": ['[{"feature": "rain_lag2_mm", "contrib": 0.31}]'],
        "model": ["event_glm"],
        "rain_through": pd.to_datetime(["2024-07-21"]),
        "cases_through": pd.to_datetime(["2022-12-26"]),
    })


def test_valid_frames_pass():
    check(city_week(), "city_week")
    check(forecast(), "forecast")


def test_non_monday_rejected():
    df = city_week()
    df.loc[1, "week_start"] = pd.Timestamp("2022-08-09")
    with pytest.raises(ValueError, match="Monday"):
        check(df, "city_week")


def test_missing_column_named():
    with pytest.raises(ValueError, match="missing column heavy_days"):
        check(city_week().drop(columns="heavy_days"), "city_week")


def test_forecast_leak_and_range():
    df = forecast()
    df["rain_through"] = pd.to_datetime(["2024-07-29"])
    df["p_elevated"] = [1.3]
    with pytest.raises(ValueError) as e:
        check(df, "forecast")
    assert "p_elevated" in str(e.value) and "issue_date" in str(e.value)


def test_config_overlay():
    assert merge({"a": {"b": 1, "c": 2}}, {"a": {"c": 3}}) == {"a": {"b": 1, "c": 3}}
    cfg = load(Path(__file__).parents[1] / "configs" / "carina_2024.yaml")
    assert cfg["target"]["elevated_min_cases"] == 3
    assert cfg["replay"]["name"] == "carina_2024"


def test_boundaries_contract():
    from f2f.contracts import check_boundaries
    sq = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    feats = [{"type": "Feature", "geometry": sq, "properties": {"psgc10": f"13809000{i:02d}", "name": f"b{i}"}}
             for i in range(1, 19)]
    check_boundaries({"type": "FeatureCollection", "features": feats})
    with pytest.raises(ValueError, match="18 features"):
        check_boundaries({"type": "FeatureCollection", "features": feats[:17]})
    feats[0]["geometry"] = {"type": "Point", "coordinates": [0, 0]}
    with pytest.raises(ValueError, match="Polygon"):
        check_boundaries({"type": "FeatureCollection", "features": feats})


def test_metrics_contract():
    ok = pd.DataFrame({"model": ["b0_zero", "event_glm"], "h": [2, 2], "split": ["test", "test"],
                       "metric": ["mae", "mae"], "value": [0.49, float("nan")]})
    check(ok, "metrics")
    with pytest.raises(ValueError, match="metric not in"):
        check(ok.assign(metric=["mae", "accuracy"]), "metrics")
    with pytest.raises(ValueError, match="duplicate"):
        check(ok.assign(model="b0_zero"), "metrics")
