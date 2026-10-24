import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import nbinom

PRED_COLS = ["p_elevated", "q05", "q50", "q95"]

def _empty_stats() -> pd.DataFrame:
    return pd.DataFrame(columns=["city_psgc", "week", *PRED_COLS])

def _order_quantiles(df: pd.DataFrame) -> pd.DataFrame:
    # C2 requires ordered count quantiles when these values are used downstream.
    q = np.sort(df[["q05", "q50", "q95"]].to_numpy(dtype=float), axis=1)
    df[["q05", "q50", "q95"]] = np.maximum(q, 0.0)
    return df

class B0Zero:
    """Baseline 0: all-zero probability and all-zero counts."""

    def fit(self, df: pd.DataFrame) -> "B0Zero":
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "p_elevated": np.zeros(len(df), dtype=float),
                "q05": np.zeros(len(df), dtype=float),
                "q50": np.zeros(len(df), dtype=float),
                "q95": np.zeros(len(df), dtype=float),
            },
            index=df.index,
        )[PRED_COLS]

class B1Median:
    """Baseline 1: same-week median and historical elevated probability."""

    def __init__(self, lookback_years: int = 5):
        self.lookback_years = lookback_years
        self._stats = None

    def fit(self, df: pd.DataFrame) -> "B1Median":
        df = df.copy()

        if df.empty:
            self._stats = _empty_stats()
            return self

        if self.lookback_years:
            cutoff = df["week_start"].dt.year.max() - self.lookback_years
            df = df[df["week_start"].dt.year > cutoff]

        if df.empty:
            self._stats = _empty_stats()
            return self

        # C1 allows null cases and null elevated. Missing weeks must stay missing.
        df = df.dropna(subset=["cases", "elevated"])

        if df.empty:
            self._stats = _empty_stats()
            return self

        # ISO week is the epidemiological week key.
        df["week"] = df["week_start"].dt.isocalendar().week.astype(int)

        # Cast to float so nullable Int64/boolean values aggregate cleanly.
        df["cases"] = df["cases"].astype(float)
        df["elevated"] = df["elevated"].astype(float)

        stats = (
            df.groupby(["city_psgc", "week"], as_index=False)
            .agg(
                q05=("cases", lambda x: x.quantile(0.05)),
                q50=("cases", lambda x: x.quantile(0.50)),
                q95=("cases", lambda x: x.quantile(0.95)),
                p_elevated=("elevated", "mean"),
            )
        )

        for col in PRED_COLS:
            stats[col] = stats[col].fillna(0.0).astype(float)

        stats["p_elevated"] = stats["p_elevated"].clip(0.0, 1.0)
        stats = _order_quantiles(stats)

        self._stats = stats[["city_psgc", "week", *PRED_COLS]]
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._stats is None:
            raise RuntimeError("fit before predict")

        if self._stats.empty:
            return pd.DataFrame(0.0, index=df.index, columns=PRED_COLS)

        out = df[["city_psgc", "week_start"]].copy()
        out["week"] = out["week_start"].dt.isocalendar().week.astype(int)

        merged = out.merge(
            self._stats,
            on=["city_psgc", "week"],
            how="left",
        )

        for col in PRED_COLS:
            merged[col] = merged[col].fillna(0.0).astype(float)

        merged["p_elevated"] = merged["p_elevated"].clip(0.0, 1.0)
        merged = _order_quantiles(merged)
        merged.index = df.index

        return merged[PRED_COLS]

class B2SeasonalNB:
    """Baseline 2: Seasonal Negative Binomial GLM."""

    def __init__(self):
        self._params = None
        self._alpha = None
        self._fallback_model = None
        self._cities = []

    def _make_features(self, df: pd.DataFrame) -> pd.DataFrame:
        week_of_year = df["week_start"].dt.isocalendar().week.astype(float)
        angle = 2 * np.pi * week_of_year / 52.1775
        X = pd.DataFrame({
            "const": 1.0,
            "sin_week": np.sin(angle),
            "cos_week": np.cos(angle),
        }, index=df.index)
        # one level per city after the first: the pooled panel mixes cities of very different size
        for c in self._cities[1:]:
            X[f"city_{c}"] = (df["city_psgc"] == c).astype(float)
        return X

    def fit(self, df: pd.DataFrame) -> "B2SeasonalNB":
        df = df.copy()
        if df.empty:
            self._fallback_model = B1Median().fit(df)
            return self

        df = df.dropna(subset=["cases", "elevated"])
        if df.empty:
            self._fallback_model = B1Median().fit(df)
            return self

        y = df["cases"].astype(float).values
        self._cities = sorted(df["city_psgc"].unique())
        X = self._make_features(df)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Poisson IRLS for the means, moment estimate for the NB2 dispersion, then NB IRLS.
                # Full NB maximum likelihood diverged once the city levels added a dozen parameters.
                mu = sm.GLM(y, X, family=sm.families.Poisson()).fit().fittedvalues
                self._alpha = float(np.clip(np.mean(((y - mu) ** 2 - y) / mu ** 2), 1e-3, 50))
                res = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=self._alpha)).fit()
                if not np.isfinite(res.params).all():
                    raise ValueError("NB fit diverged")
                self._params = res.params
        except Exception:
            # Fallback to B1 if NB fails to converge
            self._fallback_model = B1Median().fit(df)

        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._fallback_model is not None:
            return self._fallback_model.predict(df)

        if self._params is None:
            raise RuntimeError("fit before predict")

        X = self._make_features(df)
        
        # Clip linear predictor to prevent exp overflow
        eta = np.clip(X @ self._params, -20, 20)
        mu = np.exp(eta)
        
        # NB2 parameterization: var = mu + alpha * mu^2
        # scipy nbinom: mean = n(1-p)/p, var = n(1-p)/p^2
        # p = 1 / (1 + alpha * mu), n = 1 / alpha
        p = 1.0 / (1.0 + self._alpha * mu)
        n = 1.0 / self._alpha
        
        # Prevent scipy errors at boundaries
        n = np.maximum(n, 1e-6)
        p = np.clip(p, 1e-6, 1.0 - 1e-6)
        
        # Prob elevated (cases >= 3) -> 1 - P(X <= 2)
        p_elevated = 1.0 - nbinom.cdf(2, n, p)
        
        q05 = nbinom.ppf(0.05, n, p)
        q50 = nbinom.ppf(0.50, n, p)
        q95 = nbinom.ppf(0.95, n, p)
        
        preds = pd.DataFrame({
            "p_elevated": p_elevated,
            "q05": q05,
            "q50": q50,
            "q95": q95,
        }, index=df.index)
        
        for col in PRED_COLS:
            preds[col] = preds[col].fillna(0.0).astype(float)
            
        preds["p_elevated"] = preds["p_elevated"].clip(0.0, 1.0)
        preds = _order_quantiles(preds)
        
        return preds[PRED_COLS]
