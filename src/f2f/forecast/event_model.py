"""P(elevated week), one direct model per horizon, fit on the pooled 12-city panel.

Sprint 1: logistic GLM with a level per city, Fourier season (K=2) and the two most recent rain weeks
that are complete on the issue Monday. Counts come from an NB GLM on the same terms. Flood and gate
flags stay out of the fit: they're False for every training row (the log covers 2024 only), so they
reach the forecast through the alert rule instead. LightGBM joins in Sprint 2 as an ensemble member.

Lags: the target week is issue_date + h, so rain_lag{k} of the target week is complete before the
issue Monday only if k >= h + 1. rain_lag{h} is the week that starts on the issue date.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import nbinom
from sklearn.metrics import fbeta_score

WEEK = pd.Timedelta(weeks=1)


class EventGLM:
    def __init__(self, h: int, cfg: dict):
        self.h = h
        self.cfg = cfg
        self.rain_cols = [f"rain_lag{h + 1}_mm", f"rain_lag{h + 2}_mm"]
        self._cutoff = cfg["alerts"].get("p_cutoff") or 0.35
        self._logit = None

    def _design(self, df: pd.DataFrame) -> pd.DataFrame:
        week = df["week_start"].dt.isocalendar().week.astype(float).to_numpy()
        X = pd.DataFrame(index=df.index)
        for k in (1, 2):
            X[f"sin{k}"] = np.sin(2 * np.pi * k * week / 52.1775)
            X[f"cos{k}"] = np.cos(2 * np.pi * k * week / 52.1775)
        for c in self.rain_cols:
            X[c] = (df[c].astype(float) - self._mean[c]) / self._std[c]
        city = df["city_psgc"].to_numpy()
        for c in self._cities[1:]:
            X[f"city_{c}"] = (city == c).astype(float)  # unknown city -> base level
        return sm.add_constant(X, has_constant="add")

    def fit(self, df: pd.DataFrame) -> "EventGLM":
        df = df.dropna(subset=["elevated", "cases", *self.rain_cols])
        if df.empty:
            raise ValueError("no weeks with cases and rain to fit on")
        self._cities = sorted(df["city_psgc"].unique())
        self._mean = df[self.rain_cols].astype(float).mean()
        self._std = df[self.rain_cols].astype(float).std().replace(0, 1)
        X = self._design(df)
        self._logit = sm.Logit(df["elevated"].astype(float).to_numpy(), X).fit(disp=0, maxiter=200, method="bfgs")
        # counts: same moment-then-IRLS NB fit as B2
        y = df["cases"].astype(float).to_numpy()
        mu = sm.GLM(y, X, family=sm.families.Poisson()).fit().fittedvalues
        self._alpha = float(np.clip(np.mean(((y - mu) ** 2 - y) / mu ** 2), 1e-3, 50))
        self._count = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=self._alpha)).fit()
        return self

    def _alerts(self, df: pd.DataFrame, p: np.ndarray) -> np.ndarray:
        """C2 rule, on what is known at the issue date (target_week - h)."""
        a = self.cfg["alerts"]
        # the rule's "rain two weeks back" is the last complete week before the issue Monday;
        # for h = 1 that is exactly rain_lag2 of the target week
        rain = df[f"rain_lag{self.h + 1}_mm"].astype(float).to_numpy()
        flood = np.zeros(len(df), bool)
        if "flood_event" in df:
            fl = df.set_index(["city_psgc", "week_start"])["flood_event"].astype(bool)
            for k in (self.h + 1, self.h + 2):  # floods in the two weeks before the issue date
                key = pd.MultiIndex.from_arrays([df["city_psgc"], df["week_start"] - k * WEEK])
                flood |= fl.reindex(key).fillna(False).to_numpy(bool)
        warn = (rain >= a.get("warning_rain_lag2_mm", 320)) | flood | (p >= self._cutoff)
        return np.select([warn, rain >= a.get("watch_rain_lag2_mm", 160)], ["warning", "watch"], "none")

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._logit is None:
            raise RuntimeError("fit before predict")
        missing = df[self.rain_cols].isna().any(axis=1)
        if missing.any():
            weeks = sorted(df.loc[missing, "week_start"].dt.strftime("%Y-%m-%d").unique())
            raise ValueError(f"no rain for target weeks {weeks[:3]}{'...' if len(weeks) > 3 else ''}; "
                             f"CCHAIN rain ends in 2022, run python -m f2f.ingest.rain for CHIRPS (#3)")
        X = self._design(df)
        p = np.clip(np.asarray(self._logit.predict(X), float), 0, 1)
        mu = np.asarray(self._count.predict(X), float)
        n, prob = 1 / self._alpha, 1 / (1 + self._alpha * mu)
        q = {f"q{int(x * 100):02d}": nbinom.ppf(x, n, prob) for x in (0.05, 0.5, 0.95)}

        # drivers: rain terms one by one, the four Fourier terms as one "season"; city levels aren't drivers
        coef = self._logit.params
        parts = pd.DataFrame({c: X[c] * coef[c] for c in self.rain_cols})
        parts["season"] = sum(X[c] * coef[c] for c in ("sin1", "cos1", "sin2", "cos2"))
        drivers = [json.dumps([{"feature": f, "contrib": round(float(v), 4)}
                               for f, v in sorted(row.items(), key=lambda kv: -abs(kv[1]))[:3]])
                   for _, row in parts.iterrows()]
        return pd.DataFrame({"p_elevated": p, **q, "alert": self._alerts(df, p), "drivers": drivers,
                             "model": "event_glm"}, index=df.index)


def tune_cutoff(panel: pd.DataFrame, cfg: dict) -> tuple[float, float]:
    """F2-best cutoff for h = 1: fit on weeks through 2018, score the city on 2019-20. Never sees 2021-22."""
    m = EventGLM(1, cfg).fit(panel[panel["week_start"].dt.year <= 2018])
    ev = panel[(panel["city_psgc"] == cfg["city"]["psgc10"]) & panel["week_start"].dt.year.between(2019, 2020)]
    ev = ev.dropna(subset=["elevated", *m.rain_cols])
    p = np.asarray(m._logit.predict(m._design(ev)), float)
    y = ev["elevated"].astype(bool).to_numpy()
    grid = np.round(np.arange(0.05, 0.61, 0.01), 2)
    f2 = [fbeta_score(y, p >= c, beta=2, zero_division=0) for c in grid]
    best = int(np.argmax(f2))
    return float(grid[best]), float(f2[best])


if __name__ == "__main__":
    # python -m f2f.forecast.event_model [config]: print the tuned cutoff to freeze in base.yaml
    from f2f import config, features
    from f2f.ingest import cchain
    cfg = config.load(*sys.argv[1:2])
    raw = Path(cfg["paths"]["raw"])
    panel = features.build_city_week(cchain.load_pidsr(raw), cchain.load_climate(raw), cchain.load_population(raw), cfg)
    cutoff, f2 = tune_cutoff(panel, cfg)
    print(f"p_cutoff {cutoff} (F2 {f2:.3f} on 2019-20, h=1)")
