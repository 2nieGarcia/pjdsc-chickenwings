from f2f import config, fixtures


def test_fixtures_pass_contracts(tmp_path):
    cfg = config.load(config.BASE.parent / "carina_2024.yaml")
    out = fixtures.write(tmp_path / "fx", cfg)
    assert {p.name for p in out.iterdir()} == {
        "forecast.parquet", "barangay_index_resident.parquet", "barangay_index_daytime.parquet"}
