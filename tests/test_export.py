import json

from f2f import config, export, fixtures


def test_export_writes_everything_the_web_app_reads(tmp_path, monkeypatch):
    run = fixtures.write(tmp_path / "00000000-fixture", config.load(config.BASE.parent / "carina_2024.yaml"))
    (run / "forecast.parquet").unlink()  # forecast stub: export falls back to the synthetic one
    out = tmp_path / "data"
    monkeypatch.setattr(export, "OUT", out)
    export.main(["--run", str(run)])

    assert {p.name for p in out.iterdir()} == {
        "meta.json", "forecast.json", "index_resident.json", "index_daytime.json", "plans.json", "barangays.geojson"}
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["forecast_synthetic"] and meta["rain_synthetic"]
    plans = json.loads((out / "plans.json").read_text(encoding="utf-8"))
    for mode in ("resident", "daytime"):
        for plan in plans[mode].values():
            assert plan["total_alloc"] <= plan["stock_on_hand"]
            assert plan["synthetic_stock"]
