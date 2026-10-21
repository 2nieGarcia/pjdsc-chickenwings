"""Project CCHAIN tables (Thinking Machines, CC BY 4.0). `python -m f2f.ingest.fetch` downloads them from HDX.

Cities are re-keyed from CCHAIN's 9-digit adm3_pcode to 10-digit PSGC with ref/cchain_cities.csv.
"""
from pathlib import Path

import pandas as pd

CITIES = Path(__file__).parents[1] / "ref" / "cchain_cities.csv"
A27 = "A27"  # leptospirosis
FIRST_WEEK, LAST_WEEK = "2008-01-07", "2022-12-26"


def cities() -> pd.DataFrame:
    """adm3_pcode, psgc10, name for the 12 CCHAIN cities."""
    return pd.read_csv(CITIES, dtype=str)


def _to_psgc10(adm3: pd.Series) -> pd.Series:
    out = adm3.map(cities().set_index("adm3_pcode")["psgc10"])
    if out.isna().any():
        raise ValueError(f"adm3_pcode not in cchain_cities.csv: {sorted(adm3[out.isna()].unique())}")
    return out


def load_pidsr(raw: Path) -> pd.DataFrame:
    """Weekly leptospirosis (A27) for all 12 CCHAIN cities: city_psgc, week_start, cases.

    Every Monday from 2008-01-07 to 2022-12-26 is present. Weeks missing from the source
    (2012-12-31 and 2018-01-01, both year-boundary weeks) come back as <NA>, not 0.
    Never mix with FHSIS rows: PIDSR counts are already inside the FHSIS annual totals.
    """
    df = pd.read_csv(Path(raw) / "cchain" / "disease_pidsr_totals.csv",
                     usecols=["date", "adm3_pcode", "disease_icd10_code", "source_name", "case_total"])
    df = df[df["disease_icd10_code"] == A27]
    if set(df["source_name"]) != {"PIDSR-DOH"}:
        raise ValueError(f"unexpected sources in PIDSR table: {set(df['source_name'])}")
    df = pd.DataFrame({"city_psgc": _to_psgc10(df["adm3_pcode"]),
                       "week_start": pd.to_datetime(df["date"]),
                       "cases": df["case_total"].astype("Int64")})
    if (df["week_start"].dt.dayofweek != 0).any():
        raise ValueError("PIDSR dates are not all Mondays")
    if df.duplicated(["city_psgc", "week_start"]).any():
        raise ValueError("duplicate city-weeks in PIDSR")

    grid = pd.MultiIndex.from_product([sorted(df["city_psgc"].unique()),
                                       pd.date_range(FIRST_WEEK, LAST_WEEK, freq="W-MON")],
                                      names=["city_psgc", "week_start"])
    return df.set_index(["city_psgc", "week_start"]).reindex(grid).reset_index()


def load_climate(raw: Path, start: str = "2007-10-01") -> pd.DataFrame:
    """Daily rain per city: city_psgc, date, rain_mm.

    From climate_atmosphere_downscaled (reanalysis downscaled to 0.02 deg, 2003-2022), averaged
    over each city's barangays weighted by barangay area. Starts early enough for 6-week lags in 2008.
    """
    cc = Path(raw) / "cchain"
    df = pd.read_csv(cc / "climate_atmosphere_downscaled.csv", usecols=["date", "adm4_pcode", "pr"])
    df = df[df["date"] >= start].dropna(subset=["pr"])
    area = pd.read_csv(cc / "location.csv", usecols=["adm4_pcode", "brgy_total_area"]).set_index("adm4_pcode")["brgy_total_area"]
    df["w"] = df["adm4_pcode"].map(area)
    if df["w"].isna().any():
        raise ValueError("barangays in the climate table missing from location.csv")
    df["adm3_pcode"] = df["adm4_pcode"].str[:8] + "000"
    df["wpr"] = df["pr"] * df["w"]
    g = df.groupby(["adm3_pcode", "date"])[["wpr", "w"]].sum().reset_index()
    return pd.DataFrame({"city_psgc": _to_psgc10(g["adm3_pcode"]),
                         "date": pd.to_datetime(g["date"]),
                         "rain_mm": g["wpr"] / g["w"]})


def load_population(raw: Path) -> pd.DataFrame:
    """Yearly city population: city_psgc, year, pop. WorldPop via CCHAIN, 2000-2020; later years repeat 2020."""
    df = pd.read_csv(Path(raw) / "cchain" / "worldpop_population.csv", usecols=["adm4_pcode", "date", "pop_count_total"])
    df["adm3_pcode"] = df["adm4_pcode"].str[:8] + "000"
    df["year"] = df["date"].str[:4].astype(int)
    g = df.groupby(["adm3_pcode", "year"])["pop_count_total"].sum().reset_index()
    return pd.DataFrame({"city_psgc": _to_psgc10(g["adm3_pcode"]), "year": g["year"],
                         "pop": g["pop_count_total"].round().astype(int)})


def brgy_lepto_rows(raw: Path, adm3: str = "PH137503000") -> pd.DataFrame:
    """Navotas A27 rows in disease_lgu_disaggregated_totals. Empty as of the 2024 CCHAIN release."""
    df = pd.read_csv(Path(raw) / "cchain" / "disease_lgu_disaggregated_totals.csv", dtype={"adm4_pcode": str})
    return df[(df["adm3_pcode"] == adm3) & df["disease_icd10_code"].astype(str).str.startswith(A27)]
