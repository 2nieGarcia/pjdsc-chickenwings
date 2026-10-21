import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from f2f import config, fixtures

APP = str(Path(__file__).parents[1] / "app" / "streamlit_app.py")


def test_empty_state(tmp_path, monkeypatch):
    monkeypatch.setenv("F2F_ARTIFACTS", str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception
    assert "No artifacts yet" in at.info[0].value


def test_tier_map_on_fixtures(tmp_path, monkeypatch):
    fixtures.write(tmp_path / "00000000-fixture", config.load(config.BASE.parent / "carina_2024.yaml"))
    monkeypatch.setenv("F2F_ARTIFACTS", str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception
    deck = json.loads(at.get("deck_gl_json_chart")[0].proto.json)
    feats = deck["layers"][0]["data"]["features"]
    assert len(feats) == 18
    assert {f["properties"]["tier"] for f in feats} == {"act now", "prepare", "monitor"}

    at.sidebar.radio[0].set_value("daytime").run()
    assert not at.exception


def test_index_only_run(tmp_path, monkeypatch):
    run = fixtures.write(tmp_path / "00000000-fixture", config.load(config.BASE.parent / "carina_2024.yaml"))
    (run / "forecast.parquet").unlink()
    monkeypatch.setenv("F2F_ARTIFACTS", str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception
    assert any("No forecast" in i.value for i in at.info)
