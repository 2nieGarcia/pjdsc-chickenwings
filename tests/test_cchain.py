import pandas as pd
import pytest

from f2f.ingest import cchain


def write(raw, name, text):
    p = raw / "cchain" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding="utf-8")


@pytest.fixture
def raw(tmp_path):
    write(tmp_path, "disease_pidsr_totals.csv", """
uuid,freq,date,source_name,source_filename,adm3_pcode,disease_icd10_code,disease_common_name,case_total
a,W,2008-01-07,PIDSR-DOH,f,PH137503000,A27,LEPTOSPIROSIS,0
b,W,2008-01-14,PIDSR-DOH,f,PH137503000,A27,LEPTOSPIROSIS,4
c,W,2008-01-14,PIDSR-DOH,f,PH137503000,A90-A91,DENGUE,9
d,W,2008-01-07,PIDSR-DOH,f,PH137401000,A27,LEPTOSPIROSIS,1
""")
    write(tmp_path, "location.csv", """
x,adm1_en,adm1_pcode,adm2_en,adm2_pcode,adm3_en,adm3_pcode,adm4_en,adm4_pcode,brgy_total_area
0,NCR,PH1,D3,PH2,Navotas,PH137503000,A,PH137503001,1.0
1,NCR,PH1,D3,PH2,Navotas,PH137503000,B,PH137503002,3.0
""")
    write(tmp_path, "climate_atmosphere_downscaled.csv", """
date,adm4_pcode,tmin,tmax,tave,pr
2007-09-30,PH137503001,24,30,27,99
2008-01-07,PH137503001,24,30,27,10
2008-01-07,PH137503002,24,30,27,20
""")
    write(tmp_path, "worldpop_population.csv", """
uuid,adm4_pcode,date,freq,pop_count_total
a,PH137503001,2020-01-01,Y,100.4
b,PH137503002,2020-01-01,Y,200.4
""")
    return tmp_path


def test_pidsr_keeps_only_a27_on_a_full_weekly_grid(raw):
    df = cchain.load_pidsr(raw)
    weeks = len(pd.date_range(cchain.FIRST_WEEK, cchain.LAST_WEEK, freq="W-MON"))
    assert len(df) == 2 * weeks
    nav = df[df["city_psgc"] == "1380900000"].set_index("week_start")["cases"]
    assert nav[pd.Timestamp("2008-01-14")] == 4  # dengue row ignored
    assert pd.isna(nav[pd.Timestamp("2008-01-21")])  # absent from source -> missing, not 0
    assert str(df["cases"].dtype) == "Int64"


def test_pidsr_rejects_unknown_city(raw):
    p = raw / "cchain" / "disease_pidsr_totals.csv"
    p.write_text(p.read_text() + "e,W,2008-01-07,PIDSR-DOH,f,PH999999000,A27,LEPTOSPIROSIS,1\n")
    with pytest.raises(ValueError, match="PH999999000"):
        cchain.load_pidsr(raw)


def test_climate_is_area_weighted_and_starts_on_time(raw):
    df = cchain.load_climate(raw)
    assert list(df["date"]) == [pd.Timestamp("2008-01-07")]
    assert df["rain_mm"].iloc[0] == pytest.approx((10 * 1 + 20 * 3) / 4)
    assert df["city_psgc"].iloc[0] == "1380900000"


def test_population_sums_barangays(raw):
    df = cchain.load_population(raw)
    assert df.to_dict("records") == [{"city_psgc": "1380900000", "year": 2020, "pop": 301}]
