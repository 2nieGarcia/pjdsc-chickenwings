"""B0 all-zero, B1 5-year same-week median, B2 seasonal NB GLM. Every model gets scored against all three."""
import pandas as pd


def b0_zero(panel: pd.DataFrame, h: int) -> pd.DataFrame:
    raise NotImplementedError


def b1_same_week_median(panel: pd.DataFrame, h: int, years: int = 5) -> pd.DataFrame:
    raise NotImplementedError


def b2_seasonal_nb(panel: pd.DataFrame, h: int) -> pd.DataFrame:
    raise NotImplementedError
