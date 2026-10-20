"""P(elevated week), one direct model per horizon, fit on the pooled 12-city panel.

Sprint 1: logistic GLM with city intercept, Fourier season (K=2), rain_cum6_lag1, rain lag 2-3,
heavy_days, flood/gate flags. LightGBM joins in Sprint 2 as an ensemble member, not a replacement.
"""
import pandas as pd


def fit(panel: pd.DataFrame, h: int, cfg: dict):
    raise NotImplementedError


def predict(model, panel: pd.DataFrame, issue_dates: pd.DatetimeIndex, h: int) -> pd.DataFrame:
    """Rows shaped like contract C2 (forecast)."""
    raise NotImplementedError
