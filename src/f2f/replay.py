"""Event replay: forecasts as they would have been issued each Monday of the window."""
import pandas as pd


def issue_dates(cfg: dict) -> pd.DatetimeIndex:
    r = cfg["replay"]
    return pd.date_range(r["issue_start"], r["issue_end"], freq="W-MON")
