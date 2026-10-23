"""Pooled event model: Logistic GLM for P(elevated week) at horizon h."""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm


class EventGLM:
    """Logistic GLM for elevated week prediction, pooled across cities."""

    def __init__(self, h: int, cfg: dict):
        self.h = h
        self.cfg = cfg
        self._model = None
        self._feature_names = None
        self._feature_means = None
        self._feature_stds = None
        self._cutoff = cfg["alerts"].get("p_cutoff") or 0.35

    def _make_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Build leakage-safe feature matrix for horizon h."""
        df = df.copy()
        
        week = df["week_start"].dt.isocalendar().week.astype(float)
        angle1 = 2 * np.pi * week / 52.1775
        angle2 = 4 * np.pi * week / 52.1775
        df["sin1"] = np.sin(angle1)
        df["cos1"] = np.cos(angle1)
        df["sin2"] = np.sin(angle2)
        df["cos2"] = np.cos(angle2)

        city_dummies = pd.get_dummies(df["city_psgc"], prefix="city", drop_first=True, dtype=float)
        
        rain_cols = []
        if self.h <= 1:
            rain_cols.append("rain_cum6_lag1_mm")
        if self.h <= 2:
            rain_cols.append("rain_lag2_mm")
        if self.h <= 3:
            rain_cols.append("rain_lag3_mm")
            
        df["heavy_days_safe"] = df.groupby("city_psgc")["heavy_days"].shift(self.h).fillna(0.0).astype(float)
        df["flood_event_safe"] = df.groupby("city_psgc")["flood_event"].shift(self.h).fillna(0.0).astype(float)
        df["gate_impaired_safe"] = df.groupby("city_psgc")["gate_impaired"].shift(self.h).fillna(0.0).astype(float)
        
        flag_cols = ["heavy_days_safe", "flood_event_safe", "gate_impaired_safe"]

        base_cols = ["sin1", "cos1", "sin2", "cos2"] + rain_cols + flag_cols
        X = pd.concat([df[base_cols], city_dummies], axis=1).fillna(0.0).astype(float)
        
        if fit:
            non_constant = X.columns[X.std() > 1e-8].tolist()
            X = X[non_constant]
            
            self._feature_names = X.columns.tolist()
            self._feature_means = X.mean()
            self._feature_stds = X.std().replace(0, 1)
        else:
            X = X.reindex(columns=self._feature_names, fill_value=0.0)
            
        X = (X - self._feature_means) / self._feature_stds
        
        return X

    def fit(self, df: pd.DataFrame) -> "EventGLM":
        df = df.dropna(subset=["elevated"]).copy()
        if df.empty:
            raise ValueError("No valid data to fit")

        X = self._make_features(df, fit=True)
        X = sm.add_constant(X).astype(float)
        y = df["elevated"].astype(float)

        self._model = sm.Logit(y, X).fit(disp=0, maxiter=200, method='bfgs')
        return self
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict probabilities, alerts, and drivers for the evaluation frame."""
        if self._model is None:
            raise RuntimeError("Model must be fitted before predicting")

        X = self._make_features(df, fit=False)
        X_pred = sm.add_constant(X, has_constant="add").astype(float)
        
        p = self._model.predict(X_pred)
        p = np.nan_to_num(p, nan=0.0)
        p = np.clip(p, 0.0, 1.0)
        
        alert = np.full(len(df), "none", dtype=object)
        
        if "rain_lag2_mm" in X.columns:
            raw_rain_lag2 = df["rain_lag2_mm"].fillna(0.0).to_numpy()
            alert = np.where(raw_rain_lag2 >= 320, "warning", alert)
            alert = np.where((raw_rain_lag2 >= 160) & (alert == "none"), "watch", alert)
            
        if "flood_event_safe" in X.columns:
            raw_flood = df.groupby("city_psgc")["flood_event"].shift(self.h).fillna(0.0).to_numpy()
            alert = np.where(raw_flood > 0.5, "warning", alert)
            
        alert = np.where(p >= self._cutoff, "warning", alert)
        alert = np.where(pd.isna(alert), "none", alert)

        contribs = X * self._model.params[1:]
        top_indices = np.argsort(-np.abs(contribs.to_numpy()), axis=1)[:, :3]
        
        drivers_list = []
        for i in range(len(X)):
            row_drivers = []
            for idx in top_indices[i]:
                fname = self._feature_names[idx]
                val = float(contribs.iloc[i, idx])
                row_drivers.append({"feature": fname, "contrib": round(val, 4)})
            drivers_list.append(json.dumps(row_drivers))

        q50 = np.where(p >= 0.5, 3.0, 0.0)
        q95 = np.where(p >= 0.5, 5.0, 0.0)
        q05 = np.zeros(len(df))

        return pd.DataFrame(
            {
                "p_elevated": p,
                "q05": q05,
                "q50": q50,
                "q95": q95,
                "alert": alert,
                "drivers": drivers_list,
                "model": "event_glm",
            },
            index=df.index,
        )