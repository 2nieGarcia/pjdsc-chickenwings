"""Tests for the pooled event model (Issue #7)."""
import json
import warnings
import numpy as np
import pandas as pd
import pytest

from f2f.forecast.event_model import EventGLM

NAVOTAS = "1380900000"
OTHER = "1376000000"


def _make_cfg() -> dict:
    return {
        "alerts": {"p_cutoff": 0.35},
        "city": {"psgc10": NAVOTAS},
    }


def _make_synthetic_panel(n_weeks: int = 400) -> pd.DataFrame:
    """Generate a synthetic C1-shaped panel with the features EventGLM needs."""
    dates = pd.date_range("2015-01-05", periods=n_weeks, freq="7D")
    cities = [NAVOTAS, OTHER]
    
    np.random.seed(42)
    frames = []
    for city in cities:
        rain_lag1 = np.random.exponential(50, n_weeks)
        rain_lag2 = np.random.exponential(50, n_weeks)
        rain_lag3 = np.random.exponential(50, n_weeks)
        
        cases = np.random.poisson(0.5, n_weeks)
        elevated = cases >= 3
        
        frames.append(pd.DataFrame({
            "city_psgc": city,
            "week_start": dates,
            "cases": pd.array(cases, dtype="Int64"),
            "elevated": pd.array(elevated, dtype="boolean"),
            "rain_cum6_lag1_mm": rain_lag1,
            "rain_lag2_mm": rain_lag2,
            "rain_lag3_mm": rain_lag3,
            "heavy_days": np.random.randint(0, 3, n_weeks),
            "flood_event": np.random.choice([True, False], n_weeks, p=[0.1, 0.9]),
            "gate_impaired": np.random.choice([True, False], n_weeks, p=[0.05, 0.95]),
        }))
        
    return pd.concat(frames, ignore_index=True)


def test_event_glm_fit_and_predict_shape() -> None:
    panel = _make_synthetic_panel()
    train = panel[panel["week_start"].dt.year <= 2018]
    test = panel[panel["week_start"].dt.year == 2019]
    
    model = EventGLM(h=1, cfg=_make_cfg())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(train)
    preds = model.predict(test)
    
    expected_cols = {"p_elevated", "q05", "q50", "q95", "alert", "drivers", "model"}
    assert expected_cols.issubset(set(preds.columns))
    assert len(preds) == len(test)
    assert (preds["model"] == "event_glm").all()


def test_event_glm_drivers_are_valid_json() -> None:
    panel = _make_synthetic_panel()
    train = panel[panel["week_start"].dt.year <= 2018]
    test = panel[panel["week_start"].dt.year == 2019]
    
    model = EventGLM(h=1, cfg=_make_cfg())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(train)
    preds = model.predict(test)
    
    drivers = json.loads(preds["drivers"].iloc[0])
    assert isinstance(drivers, list)
    assert len(drivers) == 3
    assert "feature" in drivers[0]
    assert "contrib" in drivers[0]


def test_event_glm_no_leakage_h3() -> None:
    """Shuffling future rain (lag1, lag2) must not change h=3 predictions.
    
    This is the mandatory leakage test from Issue #7.
    For h=3, lag1 (k=1) and lag2 (k=2) are strictly forbidden (k < h).
    """
    panel = _make_synthetic_panel()
    train = panel[panel["week_start"].dt.year <= 2018]
    test = panel[panel["week_start"].dt.year == 2019].copy()
    
    model = EventGLM(h=3, cfg=_make_cfg())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(train)
    
    preds_original = model.predict(test)
    
    test_shuffled = test.copy()
    test_shuffled["rain_cum6_lag1_mm"] = np.random.permutation(test_shuffled["rain_cum6_lag1_mm"])
    test_shuffled["rain_lag2_mm"] = np.random.permutation(test_shuffled["rain_lag2_mm"])
    
    preds_shuffled = model.predict(test_shuffled)
    
    pd.testing.assert_series_equal(
        preds_original["p_elevated"], 
        preds_shuffled["p_elevated"],
        check_names=False
    )