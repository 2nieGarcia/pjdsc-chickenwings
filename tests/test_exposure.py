import pytest

from f2f import config, exposure


@pytest.fixture
def cfg():
    return config.load()


def test_totals_add_up(cfg):
    df = exposure.present_population(cfg, inflow=40000)
    assert df["pop_daytime"].sum() == pytest.approx(252878 * 0.93 + 40000)
    assert df["nfpc_inflow"].sum() == pytest.approx(40000)


def test_only_port_barangays_get_inflow(cfg):
    df = exposure.present_population(cfg)
    got = set(df.loc[df["nfpc_inflow"] > 0, "psgc10"])
    assert got == set(cfg["exposure"]["nfpc_barangays"])
    assert df["nfpc_inflow"].sum() == pytest.approx(cfg["exposure"]["nfpc_scenario"])


def test_rejects_bad_inputs(cfg):
    with pytest.raises(ValueError):
        exposure.present_population(cfg, inflow=-1)
    cfg["exposure"]["nfpc_barangays"] = ["1380900099"]
    with pytest.raises(ValueError, match="aren't Navotas"):
        exposure.present_population(cfg)
