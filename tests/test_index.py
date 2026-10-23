import numpy as np
import pandas as pd
import pytest

from f2f import barangays, config, geo, index
from f2f.contracts import check


def layers(**over):
    b = barangays.load()
    df = b[["psgc10", "name", "parent_psgc_cchain"]].assign(
        flood25_any=40.0, flood100_medhigh=30.0, gate_affected=0.0,
        pop_resident=b["pop_2024"].astype(float), pop_daytime=b["pop_2024"] * 0.93,
        small_bldg_share=0.85, built_up_pct=45.0, pop_density=60000.0,
        no_hc_15min=20.0, no_hosp_15min=10.0, m_to_primary=800.0)
    for col, vals in over.items():
        df[col] = vals
    return df


@pytest.fixture
def cfg():
    return config.load()


def varied(seed=3):
    rng = np.random.default_rng(seed)
    return layers(flood25_any=rng.uniform(5, 70, 18), flood100_medhigh=rng.uniform(2, 60, 18),
                  pop_resident=rng.uniform(8000, 60000, 18), pop_daytime=rng.uniform(9000, 70000, 18),
                  small_bldg_share=rng.uniform(0.5, 0.95, 18), built_up_pct=rng.uniform(20, 90, 18),
                  pop_density=rng.uniform(20000, 120000, 18), no_hc_15min=rng.uniform(0, 100, 18),
                  no_hosp_15min=rng.uniform(0, 100, 18), m_to_primary=rng.uniform(100, 5000, 18))


def test_bands_are_seeded_and_stay_in_range(cfg):
    ly = varied()
    a = index.build_index(ly, cfg, "resident")
    b = index.build_index(ly, cfg, "resident")
    assert a.equals(b)  # same seed, same bands every run
    assert a["rank_p05"].between(1, 18).all()
    assert a["rank_p95"].between(1, 18).all()
    assert (a["rank_p05"] < a["rank_p95"]).any()  # the jitter actually moves ranks


def test_band_always_holds_the_rank(cfg):
    a = index.build_index(varied(48), cfg, "resident")  # seed 48: rank 10 fell outside a raw band of 11-12
    assert a["rank"].between(a["rank_p05"], a["rank_p95"]).all()


def test_sensitivity_covers_both_modes_and_aggregations(cfg):
    ly = varied()
    frames = {mode: index.build_index(ly, cfg, mode) for mode in ("resident", "daytime")}
    table = index.sensitivity(frames, cfg)
    assert len(table) == 4 * 18
    assert set(table["aggregation"]) == set(index.AGGREGATIONS)
    assert set(table["exposure_mode"]) == {"resident", "daytime"}
    assert (table["mean_abs_shift"] >= 0).all()
    geo = table[table["aggregation"] == "geometric"].set_index(["exposure_mode", "psgc10"])["median_rank"]
    ari = table[table["aggregation"] == "arithmetic"].set_index(["exposure_mode", "psgc10"])["median_rank"]
    assert not geo.equals(ari)  # geometric and arithmetic are not the same index


def test_output_meets_contract(cfg):
    rng = np.random.default_rng(1)
    ly = layers(flood25_any=rng.uniform(5, 70, 18), m_to_primary=rng.uniform(0, 3000, 18), no_hc_15min=rng.uniform(0, 100, 18),
                small_bldg_share=rng.uniform(0.5, 0.95, 18))
    for mode in ("resident", "daytime"):
        out = check(index.build_index(ly, cfg, mode), "barangay_index")
        assert out["tier"].value_counts().to_dict() == {"monitor": 7, "prepare": 6, "act_now": 5}
        assert sorted(out["rank"]) == list(range(1, 19))


def test_crowding_alone_cant_make_act_now(cfg):
    # the last barangay is by far the most crowded but floods least; an arithmetic mean would still lift it
    n = 18
    ly = layers(flood25_any=np.r_[np.linspace(20, 70, n - 1), 1.0],
                flood100_medhigh=np.r_[np.linspace(15, 60, n - 1), 1.0],
                pop_resident=np.r_[np.linspace(10000, 30000, n - 1), 200000.0],
                pop_daytime=np.r_[np.linspace(10000, 30000, n - 1), 200000.0])
    out = index.build_index(ly, cfg, "resident").set_index("psgc10")
    crowded = out.loc[ly["psgc10"].iloc[-1]]
    assert crowded["hazard"] == 1.0
    assert crowded["exposure_res"] == 10.0
    assert crowded["tier"] == "monitor"


def test_constant_indicator_is_ignored():
    assert index.scale(pd.Series([3.0] * 5)).isna().all()
    s = index.scale(pd.Series([1.0, 2.0, 3.0, 4.0, 100.0]), winsor=(0, 1))
    assert s.min() == 1 and s.max() == 10


def test_exposed_n_uses_flood_share(cfg):
    out = index.build_index(layers(flood25_any=50.0), cfg, "resident")
    b = barangays.load().set_index("psgc10")["pop_2024"]
    got = out.set_index("psgc10")["exposed_n"].sort_index()
    assert got.equals((b * 0.5).round().astype(int).sort_index().rename("exposed_n"))


def test_geo_square():
    # ~1.11 km x ~1.08 km box at Navotas latitude
    sq = {"type": "Polygon", "coordinates": [[[120.94, 14.65], [120.95, 14.65], [120.95, 14.66], [120.94, 14.66], [120.94, 14.65]]]}
    a, x, y = geo.area_centroid(sq)
    assert a == pytest.approx(1.1119 * 1.0757, rel=0.01)
    assert (x, y) == (pytest.approx(120.945), pytest.approx(14.655))
