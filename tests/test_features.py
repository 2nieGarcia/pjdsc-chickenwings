import numpy as np
import pandas as pd
import pytest

from f2f import config
from f2f.contracts import check
from f2f.features import build_city_week

NAV = "1380900000"
OTHER = "1380500000"


@pytest.fixture
def cfg():
    cfg = config.load(config.BASE.parent / "carina_2024.yaml")
    cfg["replay"]["issue_end"] = "2008-04-28"  # keep the synthetic panel short
    cfg["gate_impaired"] = {"start": "2008-03-05", "end": "2008-03-12", "barangays": []}
    return cfg


def inputs():
    weeks = pd.date_range("2008-01-07", "2008-03-31", freq="W-MON")
    pidsr = pd.concat([pd.DataFrame({"city_psgc": c, "week_start": weeks,
                                     "cases": pd.array([0, 1, 3, 5] * 3 + [None], dtype="Int64")}) for c in (NAV, OTHER)])
    days = pd.date_range("2007-10-01", "2008-04-06", freq="D")
    # rain on day d = week number since 2007-10-01, so weekly sums identify the week
    wk = (days - days[0]).days // 7
    rain = pd.concat([pd.DataFrame({"city_psgc": c, "date": days, "rain_mm": wk.astype(float)}) for c in (NAV, OTHER)])
    rain.loc[rain["date"] == "2008-03-25", "rain_mm"] = 80.0  # one heavy day, after the weeks the lag test reads
    pop = pd.DataFrame({"city_psgc": [NAV, OTHER], "year": [2008, 2008], "pop": [250000, 400000]})
    return pidsr, rain, pop


def test_panel_meets_contract(cfg):
    df = check(build_city_week(*inputs(), cfg), "city_week")
    assert df["week_start"].max() == pd.Timestamp("2008-05-19")  # issue_end + 3 weeks
    assert df.loc[df["week_start"] > "2008-03-31", "cases"].isna().all()


def test_lag_k_is_k_weeks_back(cfg):
    df = build_city_week(*inputs(), cfg).set_index(["city_psgc", "week_start"])
    for k in range(1, 7):
        here = df.loc[(NAV, pd.Timestamp("2008-03-03")), "rain_wk_mm"]
        back = df.loc[(NAV, pd.Timestamp("2008-03-03") - pd.Timedelta(weeks=k)), "rain_wk_mm"]
        assert df.loc[(NAV, pd.Timestamp("2008-03-03")), f"rain_lag{k}_mm"] == back
        assert here - back == pytest.approx(7 * k)  # each week's daily value is one higher
    row = df.loc[(NAV, pd.Timestamp("2008-03-03"))]
    assert row["rain_cum6_lag1_mm"] == pytest.approx(sum(row[f"rain_lag{k}_mm"] for k in range(1, 7)))


def test_first_week_lags_come_from_before_the_panel(cfg):
    df = build_city_week(*inputs(), cfg)
    first = df[(df["city_psgc"] == NAV) & (df["week_start"] == "2008-01-07")].iloc[0]
    assert not np.isnan(first["rain_lag6_mm"])


def test_elevated_heavy_days_and_flags(cfg):
    df = build_city_week(*inputs(), cfg).set_index(["city_psgc", "week_start"])
    assert df.loc[(NAV, pd.Timestamp("2008-01-21")), "elevated"]  # 3 cases
    assert not df.loc[(NAV, pd.Timestamp("2008-01-14")), "elevated"]  # 1 case
    assert pd.isna(df.loc[(NAV, pd.Timestamp("2008-03-31")), "elevated"])
    assert df.loc[(NAV, pd.Timestamp("2008-03-24")), "heavy_days"] == 1
    assert df.loc[(NAV, pd.Timestamp("2008-03-17")), "heavy_days"] == 0
    assert pd.isna(df.loc[(NAV, pd.Timestamp("2008-04-07")), "heavy_days"])  # no rain data that week
    gate = df.xs(NAV)["gate_impaired"]
    assert list(gate[gate].index) == [pd.Timestamp("2008-03-03"), pd.Timestamp("2008-03-10")]
    assert not df.xs(OTHER)["gate_impaired"].any()
    assert not df["flood_event"].any()


def test_flood_log_marks_navotas_weeks(cfg):
    log = pd.DataFrame({"date": pd.to_datetime(["2008-02-07", "2008-02-08"]), "barangay": "Tanza 1",
                        "kind": "flood", "depth_code": None, "affected": None, "source_url": "x"})
    df = build_city_week(*inputs(), cfg, flood_log=log)
    hit = df[df["flood_event"]]
    assert set(zip(hit["city_psgc"], hit["week_start"])) == {(NAV, pd.Timestamp("2008-02-04"))}
