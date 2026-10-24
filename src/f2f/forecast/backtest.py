"""Backtest harness: score any fit/predict model into a C7 metrics frame."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from f2f.forecast.baselines import B0Zero, B1Median, B2SeasonalNB

WEEK = pd.Timedelta(weeks=1)
HORIZONS = (1, 2, 3)
DEFAULT_CUTOFF = 0.35  # interim until #7 freezes alerts.p_cutoff on 2019-20
SPLITS = {"train": (2008, 2018), "tune": (2019, 2020), "test": (2021, 2022)}  # mirrors base.yaml split; move together


def default_models() -> dict:
    return {
        "b0_zero": B0Zero(),
        "b1_median": B1Median(),
        "b2_seasonal_nb": B2SeasonalNB(),
    }


def _fit_window(panel: pd.DataFrame, split: str, h: int) -> pd.DataFrame:
    lo, hi = SPLITS[split]
    if split == "train":
        # No data exists before 2008, so train rows are in-sample by necessity.
        return panel[panel["week_start"].dt.year <= hi]
    start = panel.loc[panel["week_start"].dt.year.between(lo, hi), "week_start"].min()
    return panel[panel["week_start"] <= start - h * WEEK]


def _episodes(df: pd.DataFrame) -> list:
    """Runs of consecutive elevated weeks; a quiet week or a gap in the weeks ends a run."""
    d = df[df["elevated"].astype(bool)].sort_values("week_start")
    block = (d["week_start"].diff() != WEEK).cumsum()
    return [(g["week_start"].min(), g["week_start"].max()) for _, g in d.groupby(block)]


def _score(eval_df: pd.DataFrame, h: int, cutoff: float) -> dict:
    eps = _episodes(eval_df)
    y = eval_df["cases"].to_numpy(dtype=float)
    e = eval_df["elevated"].astype(bool).to_numpy()
    p = eval_df["p"].to_numpy(dtype=float)
    q = eval_df["q50"].to_numpy(dtype=float)

    scores = {}
    scores["mae"] = float(np.mean(np.abs(q - y)))
    nz = y > 0
    scores["mae_nonzero"] = float(np.mean(np.abs(q[nz] - y[nz]))) if nz.any() else np.nan
    scores["brier"] = float(np.mean((p - e) ** 2))
    scores["auc"] = float(roc_auc_score(e, p)) if 0 < e.sum() < e.size else np.nan

    leads = []
    recalled = 0
    for s, end in eps:
        cand = eval_df[
            (eval_df["week_start"] >= s)
            & (eval_df["week_start"] <= end)
            & (eval_df["week_start"] < s + h * WEEK)
        ]
        hit = cand[cand["p"] >= cutoff]
        if len(hit):
            recalled += 1
            first = hit["week_start"].min()
            leads.append(h + (s - first).days / 7)
    scores["episode_recall"] = recalled / len(eps) if eps else np.nan
    scores["lead_time_wk"] = float(np.median(leads)) if leads else np.nan
    return scores


def run_backtest(
    panel: pd.DataFrame,
    city_psgc: str,
    models: dict | None = None,
    cutoff: float = DEFAULT_CUTOFF,
    horizons: tuple = HORIZONS,
) -> pd.DataFrame:
    """Fit each model per (split, h) on the pooled panel, score on city_psgc.

    A model is a fit/predict object, or a callable h -> object for models that depend on the
    horizon. predict() gets the full C1 rows of the weeks it scores, so lagged features are there.
    """
    models = default_models() if models is None else models
    city = panel[panel["city_psgc"] == city_psgc]
    rows = []
    for split, (lo, hi) in SPLITS.items():
        in_split = city["week_start"].dt.year.between(lo, hi)
        for h in horizons:
            train_df = _fit_window(panel, split, h)
            eval_df = city[in_split & city["cases"].notna()].copy()
            if eval_df.empty:
                continue
            for name, model in models.items():
                model = model(h) if callable(model) else model
                preds = model.fit(train_df.copy()).predict(eval_df.drop(columns=["p", "q50"], errors="ignore"))
                eval_df["p"] = preds["p_elevated"].to_numpy(dtype=float)
                eval_df["q50"] = preds["q50"].to_numpy(dtype=float)
                for metric, value in _score(eval_df, h, cutoff).items():
                    rows.append(
                        {"model": name, "h": h, "split": split, "metric": metric, "value": value}
                    )
    return pd.DataFrame(rows, columns=["model", "h", "split", "metric", "value"])
