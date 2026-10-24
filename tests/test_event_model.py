"""Tests for the pooled event model (Issue #7)."""
import json
import warnings

import numpy as np
import pandas as pd
import pytest

from f2f import config
from f2f.forecast.event_model import EventGLM

NAVOTAS = "1380900000"
OTHER = "1376000000"


@pytest.fixture(autouse=True)
def quiet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


def _cfg() -> dict:
    return config.load()


def _panel(n_weeks: int = 400) -> pd.DataFrame:
    """C1-shaped panel where elevated weeks follow rain two weeks earlier."""
    dates = pd.date_range("2015-01-05", periods=n_weeks, freq="7D")
    rng = np.random.default_rng(42)
    frames = []
    for city in (NAVOTAS, OTHER):
        rain = rng.exponential(60, n_weeks + 6)
        lags = {f"rain_lag{k}_mm": rain[6 - k:6 - k + n_weeks] for k in range(1, 7)}
        cases = rng.poisson(0.3 + lags["rain_lag2_mm"] / 60)
        frames.append(pd.DataFrame({
            "city_psgc": city, "week_start": dates,
            "cases": pd.array(cases, dtype="Int64"), "elevated": pd.array(cases >= 3, dtype="boolean"),
            "rain_wk_mm": rain[6:], **lags, "flood_event": False, "gate_impaired": False,
        }))
    return pd.concat(frames, ignore_index=True)


def _split(panel):
    return panel[panel["week_start"].dt.year <= 2018], panel[panel["week_start"].dt.year == 2019].copy()


def test_fit_and_predict_shape() -> None:
    train, test = _split(_panel())
    preds = EventGLM(h=1, cfg=_cfg()).fit(train).predict(test)
    assert list(preds.columns) == ["p_elevated", "q05", "q50", "q95", "alert", "drivers", "model"]
    assert len(preds) == len(test) and (preds["model"] == "event_glm").all()
    assert preds["p_elevated"].between(0, 1).all()
    assert ((preds["q05"] <= preds["q50"]) & (preds["q50"] <= preds["q95"])).all()


def test_drivers_name_rain_and_season_only() -> None:
    train, test = _split(_panel())
    drivers = json.loads(EventGLM(h=1, cfg=_cfg()).fit(train).predict(test)["drivers"].iloc[0])
    assert {d["feature"] for d in drivers} == {"rain_lag2_mm", "rain_lag3_mm", "season"}


@pytest.mark.parametrize("h", [1, 2, 3])
def test_rain_from_the_issue_week_or_later_is_not_used(h) -> None:
    """Target = issue + h. rain_lag{k} for k <= h covers days on or after the issue Monday."""
    train, test = _split(_panel())
    model = EventGLM(h=h, cfg=_cfg()).fit(train)
    shuffled = test.copy()
    for k in range(1, h + 1):
        shuffled[f"rain_lag{k}_mm"] = np.random.default_rng(k).permutation(shuffled[f"rain_lag{k}_mm"].to_numpy())
    pd.testing.assert_frame_equal(model.predict(test), model.predict(shuffled))


def test_a_flood_in_the_two_weeks_before_issue_warns() -> None:
    panel = _panel()
    train, _ = _split(panel)
    model = EventGLM(h=1, cfg=_cfg()).fit(train)
    nav = panel[panel["city_psgc"] == NAVOTAS].copy()
    for col in [c for c in nav if c.startswith("rain_")]:
        nav[col] = 0.0  # no rain: only the flood can raise the alert
    issue = pd.Timestamp("2019-07-01")
    nav.loc[nav["week_start"] == issue - pd.Timedelta(weeks=2), "flood_event"] = True
    alerts = model.predict(nav).set_index(nav["week_start"])["alert"]
    assert alerts[issue + pd.Timedelta(weeks=1)] == "warning"  # flood is lag 2 from the issue date
    assert alerts[issue + pd.Timedelta(weeks=3)] == "none"     # lag 4 from its issue date: too old


def test_missing_rain_fails_loudly() -> None:
    train, test = _split(_panel())
    model = EventGLM(h=1, cfg=_cfg()).fit(train)
    with pytest.raises(ValueError, match="#3"):
        model.predict(test.assign(rain_lag2_mm=np.nan))
