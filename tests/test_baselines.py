import pandas as pd
import numpy as np 

from f2f.forecast.baselines import B0Zero, B1Median, B2SeasonalNB, PRED_COLS

CITY = "1380900000"


def _make_panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_psgc": [CITY, CITY, CITY, CITY],
            "week_start": pd.to_datetime(
                [
                    "2015-01-05",
                    "2015-01-12",
                    "2015-01-19",
                    "2015-01-26",
                ]
            ),
            "cases": pd.array([0, 2, 4, 0], dtype="Int64"),
            "elevated": pd.array([False, False, True, False], dtype="boolean"),
        }
    )


def test_b0_returns_exact_prediction_columns_and_zeros() -> None:
    df = _make_panel()

    preds = B0Zero().fit(df).predict(df)

    assert list(preds.columns) == PRED_COLS
    assert (preds[PRED_COLS] == 0.0).all().all()


def test_b1_same_week_median_and_probability() -> None:
    train = pd.DataFrame(
        {
            "city_psgc": [CITY, CITY],
            "week_start": pd.to_datetime(["2014-01-06", "2015-01-05"]),
            "cases": pd.array([1, 3], dtype="Int64"),
            "elevated": pd.array([False, True], dtype="boolean"),
        }
    )
    test = train.tail(1).copy()

    preds = B1Median(lookback_years=5).fit(train).predict(test)

    assert list(preds.columns) == PRED_COLS
    assert preds["q50"].tolist() == [2.0]
    assert preds["p_elevated"].tolist() == [0.5]


def test_b1_lookback_drops_old_years() -> None:
    train = pd.DataFrame(
        {
            "city_psgc": [CITY, CITY],
            "week_start": pd.to_datetime(["2014-01-06", "2015-01-05"]),
            "cases": pd.array([100, 2], dtype="Int64"),
            "elevated": pd.array([True, True], dtype="boolean"),
        }
    )
    test = train.tail(1).copy()

    preds = B1Median(lookback_years=1).fit(train).predict(test)

    # max year is 2015, cutoff is 2014, so only 2015 remains.
    assert preds["q50"].tolist() == [2.0]


def test_b1_null_weeks_are_not_turned_into_zero_history() -> None:
    train = _make_panel()

    train.loc[train.index[0], "cases"] = pd.NA
    train.loc[train.index[0], "elevated"] = pd.NA

    model = B1Median(lookback_years=5).fit(train)
    preds = model.predict(train.iloc[[0]])

    # The null week has no usable same-week history, so prediction falls back to zero.
    assert preds["q50"].iloc[0] == 0.0
    assert preds["p_elevated"].iloc[0] == 0.0


def test_b1_quantiles_are_ordered_and_nonnegative() -> None:
    train = pd.DataFrame(
        {
            "city_psgc": [CITY, CITY, CITY],
            "week_start": pd.to_datetime(
                [
                    "2013-01-07",
                    "2014-01-06",
                    "2015-01-05",
                ]
            ),
            "cases": pd.array([0, 10, 100], dtype="Int64"),
            "elevated": pd.array([False, True, True], dtype="boolean"),
        }
    )
    test = train.tail(1).copy()

    preds = B1Median(lookback_years=5).fit(train).predict(test)

    row = preds.iloc[0]

    assert row["q05"] >= 0.0
    assert row["q05"] <= row["q50"]
    assert row["q50"] <= row["q95"]


def test_b1_empty_fit_predicts_zeros() -> None:
    empty = _make_panel().iloc[0:0]
    test = _make_panel()

    preds = B1Median().fit(empty).predict(test)

    assert list(preds.columns) == PRED_COLS
    assert (preds[PRED_COLS] == 0.0).all().all()

def test_b2_seasonal_nb_fits_and_predicts() -> None:
    dates = pd.date_range("2015-01-05", periods=52 * 3, freq="7D")
    week_of_year = dates.isocalendar().week.astype(float)
    angle = 2 * np.pi * week_of_year / 52.1775
    
    mu = np.exp(1.0 + 0.5 * np.sin(angle) + 0.5 * np.cos(angle))
    
    from scipy.stats import nbinom
    alpha = 0.5
    p_true = 1.0 / (1.0 + alpha * mu)
    n_true = 1.0 / alpha
    
    np.random.seed(42)
    cases = nbinom.rvs(n_true, p_true)
    elevated = cases >= 3
    
    df = pd.DataFrame({
        "city_psgc": ["1380900000"] * len(dates),
        "week_start": dates,
        "cases": pd.array(cases, dtype="Int64"),
        "elevated": pd.array(elevated, dtype="boolean"),
    })
    
    train = df.iloc[:52*2]
    test = df.iloc[52*2:]
    
    model = B2SeasonalNB().fit(train)
    assert model._fallback_model is None  # the NB fit itself must work, not the B1 fallback
    preds = model.predict(test)
    
    assert list(preds.columns) == PRED_COLS
    assert (preds["p_elevated"] >= 0.0).all()
    assert (preds["p_elevated"] <= 1.0).all()
    assert (preds["q05"] <= preds["q50"]).all()
    assert (preds["q50"] <= preds["q95"]).all()

def test_b2_fallback_on_empty_data() -> None:
    empty = pd.DataFrame(columns=["city_psgc", "week_start", "cases", "elevated"])
    test = _make_panel()
    
    model = B2SeasonalNB().fit(empty)
    preds = model.predict(test)
    
    assert (preds[PRED_COLS] == 0.0).all().all()