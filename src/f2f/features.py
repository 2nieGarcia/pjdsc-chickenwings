"""Builds the city_week panel (contract C1).

Leakage rule: a feature lagged k weeks behind the target week may feed horizon h only if k >= h.
Case lags also need the reporting delay added to h.
"""
import pandas as pd


def build_city_week(pidsr: pd.DataFrame, rain: pd.DataFrame, flood_log: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    raise NotImplementedError
