"""The 18 Navotas barangays, their CCHAIN parents and population. Every barangay layer joins on psgc10.

Sources (docs/DATASETS.md has links):
- psgc10 / corr_code / names: PSA PSGC, as mirrored in jeffreybernadas/psgc-api and faeldon/philippines-json-maps
- pop_2020: PSA 2020 CPH, per barangay
- pop_2024: PSA 2024 POPCEN. PSA publishes Tangos, Tanza and NBBS as pre-2018 parents, so their
  children get parent_2024 x child's 2020 share (largest-remainder rounding, sums are exact).
  pop_2024_source says which rows that applies to.
- parent_psgc_cchain: CCHAIN `location` table, 14 pre-2018 units

Splits (RA 10933-10935, plebiscite Jan 2018): NBBS -> Kaunlaran / Dagat-dagatan / Proper,
Tangos -> South / North, Tanza -> 1 / 2. The original code stays with the first child.
"""
from pathlib import Path

import pandas as pd

REF = Path(__file__).parent / "ref" / "navotas_barangays.csv"
CITY_POP_2020 = 247543
CITY_POP_2024 = 252878


def load() -> pd.DataFrame:
    """18 rows: psgc10, corr_code, name, parent_psgc_cchain, parent_name_cchain, pop_2020, pop_2024,
    pop_2024_source, pop_share_of_parent."""
    df = pd.read_csv(REF, dtype={"psgc10": str, "corr_code": str})
    df["pop_share_of_parent"] = df["pop_2024"] / df.groupby("parent_psgc_cchain")["pop_2024"].transform("sum")
    _validate(df)
    return df


def _validate(df):
    errs = []
    if len(df) != 18 or df["psgc10"].duplicated().any():
        errs.append("expected 18 unique psgc10")
    if df["pop_2020"].sum() != CITY_POP_2020:
        errs.append(f"pop_2020 sums to {df['pop_2020'].sum()}, PSA says {CITY_POP_2020}")
    if df["pop_2024"].sum() != CITY_POP_2024:
        errs.append(f"pop_2024 sums to {df['pop_2024'].sum()}, PSA says {CITY_POP_2024}")
    if df["parent_psgc_cchain"].nunique() != 14:
        errs.append("expected 14 CCHAIN parents")
    if not (df["psgc10"].str[-3:] == df["corr_code"].str[-3:]).all():
        errs.append("psgc10 and corr_code disagree on the barangay number")
    if errs:
        raise ValueError("navotas_barangays.csv: " + "; ".join(errs))


def to_children(parent_df: pd.DataFrame, intensive: list[str], extensive: list[str] = ()) -> pd.DataFrame:
    """Spread a table keyed on parent_psgc_cchain (CCHAIN's 14) to the 18 barangays.

    Intensive columns (percentages, densities, shares) are copied to each child.
    Extensive columns (counts) are split by pop_share_of_parent.
    """
    brgy = load()[["psgc10", "name", "parent_psgc_cchain", "pop_share_of_parent"]]
    missing = set(brgy["parent_psgc_cchain"]) - set(parent_df["parent_psgc_cchain"])
    if missing:
        raise ValueError(f"no parent rows for {sorted(missing)}")
    out = brgy.merge(parent_df[["parent_psgc_cchain", *intensive, *extensive]], on="parent_psgc_cchain", how="left")
    for c in extensive:
        out[c] = out[c] * out["pop_share_of_parent"]
    return out.drop(columns="pop_share_of_parent")
