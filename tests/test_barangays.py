import pandas as pd
import pytest

from f2f import barangays


def test_reference_table_is_consistent():
    df = barangays.load()
    assert len(df) == 18
    assert df["pop_2024"].sum() == 252878
    assert df.groupby("parent_psgc_cchain")["pop_share_of_parent"].sum().round(9).eq(1).all()


def test_split_parents():
    df = barangays.load()
    kids = df.groupby("parent_psgc_cchain")["name"].apply(sorted).to_dict()
    assert kids["PH137503009"] == ["NBBS Dagat-dagatan", "NBBS Kaunlaran", "NBBS Proper"]
    assert kids["PH137503013"] == ["Tangos North", "Tangos South"]
    assert kids["PH137503014"] == ["Tanza 1", "Tanza 2"]
    # popcen 2024 parent totals survive the split exactly
    assert df[df["parent_psgc_cchain"] == "PH137503009"]["pop_2024"].sum() == 74725
    assert df[df["parent_psgc_cchain"] == "PH137503013"]["pop_2024"].sum() == 36355
    assert df[df["parent_psgc_cchain"] == "PH137503014"]["pop_2024"].sum() == 31979


def test_to_children_copies_intensive_and_splits_counts():
    parents = barangays.load().drop_duplicates("parent_psgc_cchain")[["parent_psgc_cchain"]].assign(pct=50.0, bldgs=1000.0)
    out = barangays.to_children(parents, intensive=["pct"], extensive=["bldgs"])
    assert len(out) == 18
    assert (out["pct"] == 50.0).all()
    assert out.groupby("parent_psgc_cchain")["bldgs"].sum().round(6).eq(1000.0).all()


def test_to_children_needs_every_parent():
    with pytest.raises(ValueError, match="no parent rows"):
        barangays.to_children(pd.DataFrame({"parent_psgc_cchain": ["PH137503001"], "x": [1.0]}), intensive=["x"])
