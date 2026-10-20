"""Hand-built flood and gate log (data/raw/events/flood_log.csv). One row per barangay per report."""
from pathlib import Path

import pandas as pd

COLUMNS = ["date", "barangay", "kind", "depth_code", "affected", "source_url"]
KINDS = {"flood", "gate_down", "gate_up"}


def load_flood_log(raw: Path) -> pd.DataFrame:
    df = pd.read_csv(Path(raw) / "events" / "flood_log.csv", parse_dates=["date"])
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"flood_log.csv missing {sorted(missing)}")
    bad = set(df["kind"]) - KINDS
    if bad:
        raise ValueError(f"flood_log.csv unknown kind {sorted(bad)}")
    if df["source_url"].isna().any():
        raise ValueError("every row in flood_log.csv needs a source_url")
    return df
