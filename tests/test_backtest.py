import numpy as np
import pandas as pd
import pytest

from f2f import contracts
from f2f.forecast.backtest import _episodes, run_backtest

NAVOTAS = "1380900000"
OTHER = "1376000000"


def _panel() -> pd.DataFrame:
    weeks = pd.to_datetime(
        [
            "2018-07-02",
            "2019-07-01",
            "2020-07-06",
            "2021-07-05",
            "2021-07-12",
            "2021-07-19",
            "2022-07-04",
        ]
    )
    navotas_cases = [0, 0, 0, 4, 3, 0, 0]
    other_cases = [2, 1, 0, 1, 1, 0, 0]
    frames = []
    for psgc, cases in [(NAVOTAS, navotas_cases), (OTHER, other_cases)]:
        frames.append(
            pd.DataFrame(
                {
                    "city_psgc": psgc,
                    "week_start": weeks,
                    "cases": pd.array(cases, dtype="Int64"),
                    "elevated": pd.array([c >= 3 for c in cases], dtype="boolean"),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


class _AlwaysWarn:
    """Dummy fit/predict pair proving the harness is model-agnostic."""

    def fit(self, df):
        return self

    def predict(self, df):
        return pd.DataFrame(
            {
                "p_elevated": 0.9,
                "q05": 4.0,
                "q50": 4.0,
                "q95": 4.0,
            },
            index=df.index,
        )


def test_output_is_c7_shaped() -> None:
    out = run_backtest(_panel(), NAVOTAS)

    assert list(out.columns) == ["model", "h", "split", "metric", "value"]
    assert not out.duplicated(["model", "h", "split", "metric"]).any()
    assert set(out["model"]) == {"b0_zero", "b1_median", "b2_seasonal_nb"}
    assert set(out["h"]) == {1, 2, 3}
    assert set(out["split"]) == {"train", "tune", "test"}
    assert set(out["metric"]) == {
        "mae", "mae_nonzero", "brier", "auc", "episode_recall", "lead_time_wk"
    }
    contracts.check(out, "metrics")


def test_probability_metrics_stay_in_unit_range() -> None:
    out = run_backtest(_panel(), NAVOTAS)
    bounded = out[out["metric"].isin(["brier", "auc", "episode_recall"])]
    vals = bounded["value"].dropna()
    assert ((vals >= 0.0) & (vals <= 1.0)).all()


def test_b0_never_warns() -> None:
    out = run_backtest(_panel(), NAVOTAS)
    b0 = out[(out["model"] == "b0_zero") & (out["split"] == "test")]

    # test weeks are 4, 3, 0, 0 for Navotas
    mae = b0.loc[b0["metric"] == "mae", "value"]
    assert np.allclose(mae.to_numpy(), 1.75, atol=1e-9)
    assert b0.loc[b0["metric"] == "episode_recall", "value"].eq(0.0).all()
    assert b0.loc[b0["metric"] == "lead_time_wk", "value"].isna().all()


def test_harness_accepts_any_fit_predict_pair() -> None:
    out = run_backtest(_panel(), NAVOTAS, models={"always_warn": _AlwaysWarn()})

    assert set(out["model"]) == {"always_warn"}
    test = out[(out["split"] == "test") & (out["h"] == 1)]
    assert test.loc[test["metric"] == "episode_recall", "value"].iloc[0] == 1.0
    assert test.loc[test["metric"] == "lead_time_wk", "value"].iloc[0] == 1.0

def test_quiet_weeks_split_episodes() -> None:
    weeks = pd.date_range("2021-01-04", periods=20, freq="W-MON")
    elevated = np.zeros(20, bool)
    elevated[[3, 4, 12, 17, 18]] = True
    eps = _episodes(pd.DataFrame({"week_start": weeks, "elevated": elevated}))
    assert [(s.strftime("%m-%d"), e.strftime("%m-%d")) for s, e in eps] == [
        ("01-25", "02-01"), ("03-29", "03-29"), ("05-03", "05-10")]


class _Spy(_AlwaysWarn):
    seen = []

    def __init__(self, h):
        self.h = h

    def predict(self, df):
        self.seen.append((self.h, "rain_lag1_mm" in df.columns))
        return super().predict(df)


def test_models_get_h_and_feature_rows() -> None:
    panel = _panel().assign(rain_lag1_mm=10.0)
    run_backtest(panel, NAVOTAS, models={"spy": _Spy}, horizons=(1, 3))
    assert {h for h, _ in _Spy.seen} == {1, 3}
    assert all(has_rain for _, has_rain in _Spy.seen)
