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


def _fake_steps(monkeypatch, tmp_path):
    """Every step returns fixture-shaped data, so only run.main's wiring is under test."""
    import json as _json
    from types import SimpleNamespace
    from f2f import fixtures, run

    fx = fixtures.write(tmp_path / "fx", config.load("configs/carina_2024.yaml"))
    raw = tmp_path / "raw"
    (raw / "cchain").mkdir(parents=True)
    (raw / "cchain" / "disease_pidsr_totals.csv").write_text("x\n", encoding="utf-8")
    panel = _panel().assign(source="cchain")
    panel.loc[panel["week_start"] >= "2022-06-06", "cases"] = pd.NA

    cfg = config.load()
    cfg["paths"] = {"raw": str(raw), "artifacts": str(tmp_path / "artifacts")}
    cfg["city"] = {"psgc10": NAVOTAS}
    monkeypatch.setattr(run.config, "load", lambda path=None: cfg)
    monkeypatch.setattr(run.contracts, "check", lambda df, name: df)
    monkeypatch.setattr(run.contracts, "check_boundaries", lambda fc: fc)
    monkeypatch.setattr(run, "index", SimpleNamespace(
        load_layers=lambda raw, cfg: None,
        build_index=lambda layers, cfg, mode: pd.read_parquet(fx / f"barangay_index_{mode}.parquet"),
        boundaries=lambda raw: _json.loads((fx / "barangays.geojson").read_text(encoding="utf-8"))))
    monkeypatch.setattr(run, "cchain", SimpleNamespace(load_pidsr=lambda raw: None, load_climate=lambda raw: None,
                                                       load_population=lambda raw: None))
    monkeypatch.setattr(run.features, "build_city_week", lambda *a, **k: panel)
    monkeypatch.setattr(run, "write_metrics", lambda panel, out, cfg: pd.read_parquet(fx / "metrics.parquet").to_parquet(out / "metrics.parquet"))
    monkeypatch.setattr(run, "forecast", lambda panel, cfg: pd.read_parquet(fx / "forecast.parquet"))
    monkeypatch.setattr(run, "run_id", lambda: "20240101-test")
    return run, tmp_path / "artifacts" / "20240101-test"


def test_run_writes_the_whole_folder_and_a_manifest(monkeypatch, tmp_path) -> None:
    import json as _json
    run, out = _fake_steps(monkeypatch, tmp_path)
    run.main([])
    assert sorted(p.name for p in out.iterdir()) == [
        "barangay_index_daytime.parquet", "barangay_index_resident.parquet", "barangays.geojson",
        "city_week.parquet", "forecast.parquet", "manifest.json", "metrics.parquet"]
    m = _json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert m["run_id"] == "20240101-test"
    assert m["cases_through"] == "2022-05-30"
    assert m["rain_through"] == "2022-09-04"  # last rain week 2022-08-29 + 6 days
    assert m["flood_log"] is False and m["rain_sources"] == ["cchain"]
    assert [s["path"] for s in m["sources"]] == ["cchain/disease_pidsr_totals.csv"]


def test_a_missing_input_names_the_step_and_file(monkeypatch, tmp_path) -> None:
    run, _ = _fake_steps(monkeypatch, tmp_path)

    def missing(raw):
        raise FileNotFoundError(2, "No such file", "data/raw/cchain/disease_pidsr_totals.csv")
    monkeypatch.setattr(run.cchain, "load_pidsr", missing)
    with pytest.raises(SystemExit, match="step 'city_week': missing data/raw/cchain/disease_pidsr_totals.csv"):
        run.main([])
