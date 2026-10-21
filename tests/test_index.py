import math

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
        small_bldg_share=0.85, built_up_pct=45.0, pop_density=60000.0, km_to_care=0.8)
    for col, vals in over.items():
        df[col] = vals
    return df


@pytest.fixture
def cfg():
    return config.load()


def test_output_meets_contract(cfg):
    rng = np.random.default_rng(1)
    ly = layers(flood25_any=rng.uniform(5, 70, 18), km_to_care=rng.uniform(0.2, 2, 18),
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
    assert geo.haversine_km(120.94, 14.65, 120.94, 14.66) == pytest.approx(1.112, rel=0.01)
    assert math.isclose(geo.haversine_km(1, 1, 1, 1), 0)
