import pandas as pd

from f2f import contracts
from f2f.run import write_metrics

NAVOTAS = "1380900000"
OTHER = "1376000000"


def _cfg(horizons=None) -> dict:
    return {
        "city": {"psgc10": NAVOTAS},
        "horizons": horizons or [1, 2, 3],
        "alerts": {"p_cutoff": None},
    }


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


def test_write_metrics_writes_c7(tmp_path) -> None:
    write_metrics(_panel(), tmp_path, _cfg())

    assert (tmp_path / "metrics.parquet").exists()
    on_disk = pd.read_parquet(tmp_path / "metrics.parquet")
    contracts.check(on_disk, "metrics")
    assert set(on_disk["model"]) == {"b0_zero", "b1_median", "b2_seasonal_nb"}
    assert set(on_disk["split"]) == {"train", "tune", "test"}


def test_write_metrics_honours_config_horizons(tmp_path) -> None:
    write_metrics(_panel(), tmp_path, _cfg(horizons=[1]))

    on_disk = pd.read_parquet(tmp_path / "metrics.parquet")
    assert set(on_disk["h"]) == {1}