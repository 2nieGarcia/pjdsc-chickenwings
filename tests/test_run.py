import warnings

import pandas as pd
import pytest

from f2f import config, contracts
from f2f.run import forecast, write_metrics
from test_event_model import NAVOTAS, _panel


@pytest.fixture(autouse=True)
def quiet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


def _cfg(horizons=(1, 2, 3)) -> dict:
    cfg = config.load()
    cfg["horizons"] = list(horizons)
    cfg["city"] = {"psgc10": NAVOTAS}
    return cfg


def _long_panel() -> pd.DataFrame:
    # weeks 2015-2022 so every split has rows to score
    return _panel(n_weeks=52 * 8)


def test_write_metrics_writes_c7(tmp_path) -> None:
    write_metrics(_long_panel(), tmp_path, _cfg())
    on_disk = contracts.check(pd.read_parquet(tmp_path / "metrics.parquet"), "metrics")
    assert set(on_disk["model"]) == {"b0_zero", "b1_median", "b2_seasonal_nb", "event_glm"}
    assert set(on_disk["split"]) == {"train", "tune", "test"}


def test_write_metrics_honours_config_horizons(tmp_path) -> None:
    write_metrics(_long_panel(), tmp_path, _cfg(horizons=[1]))
    assert set(pd.read_parquet(tmp_path / "metrics.parquet")["h"]) == {1}


def test_forecast_is_c2_and_says_how_fresh_it_is() -> None:
    panel = _panel()  # 2015-01-05 .. 2022-08-29
    panel.loc[panel["week_start"] >= "2022-06-06", ["cases", "elevated"]] = pd.NA  # cases stop, rain goes on
    cfg = _cfg()
    cfg["replay"] = {"issue_start": "2022-07-04", "issue_end": "2022-07-25"}
    fc = contracts.check(forecast(panel, cfg), "forecast")
    assert len(fc) == 4 * 3
    assert (fc["target_week"] == fc["issue_date"] + pd.to_timedelta(fc["h"], unit="W")).all()
    assert (fc["cases_through"] == pd.Timestamp("2022-05-30")).all()
    assert (fc["rain_through"] == fc["issue_date"] - pd.Timedelta(days=1)).all()
