"""python -m f2f.fixtures

Writes a fake artifact folder (data/artifacts/00000000-fixture) shaped exactly like the real one,
so app and planner work doesn't wait on the pipeline. Numbers are made up. Never demo from it.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from f2f import barangays, config
from f2f.contracts import check, check_boundaries


def write(out: Path, cfg: dict) -> Path:
    rng = np.random.default_rng(0)
    out.mkdir(parents=True, exist_ok=True)

    issues = pd.date_range(cfg["replay"]["issue_start"], cfg["replay"]["issue_end"], freq="W-MON")
    peak = pd.Timestamp(cfg["replay"]["event_window"][0])
    rows = []
    for d in issues:
        for h in cfg["horizons"]:
            target = d + pd.Timedelta(weeks=h)
            p = float(np.clip(0.08 + 0.8 * np.exp(-(((target - peak).days - 14) / 10) ** 2), 0, 1))
            rows.append({"issue_date": d, "city_psgc": cfg["city"]["psgc10"], "h": h, "target_week": target,
                         "p_elevated": round(p, 3), "q05": 0.0, "q50": round(4 * p, 1), "q95": round(12 * p + 2, 1),
                         "alert": "warning" if p >= 0.5 else "watch" if p >= 0.25 else "none",
                         "drivers": json.dumps([{"feature": "rain_lag2_mm", "contrib": round(p / 2, 2)}]),
                         "model": "fixture", "rain_through": d - pd.Timedelta(days=1),
                         "cases_through": pd.Timestamp("2022-12-26")})
    check(pd.DataFrame(rows), "forecast").to_parquet(out / "forecast.parquet")

    brgy = barangays.load()
    base = brgy[["psgc10", "name", "parent_psgc_cchain"]].assign(
        hazard=rng.uniform(1, 10, 18).round(2), exposure_res=rng.uniform(1, 10, 18).round(2),
        vulnerability=rng.uniform(1, 10, 18).round(2), coping_gap=rng.uniform(1, 10, 18).round(2))
    base["exposure_day"] = base["exposure_res"].where(~base["name"].str.startswith("NBBS"), 10.0)
    pop = brgy["pop_2024"].to_numpy()
    for mode in ("resident", "daytime"):
        df = base.copy()
        exp = df["exposure_day" if mode == "daytime" else "exposure_res"]
        df["score"] = (df["hazard"] * exp * df["vulnerability"] * df["coping_gap"]) ** 0.25
        df["rank"] = df["score"].rank(ascending=False, method="first").astype(int)
        df["rank_p05"] = (df["rank"] - 2).clip(lower=1)
        df["rank_p95"] = (df["rank"] + 2).clip(upper=18)
        df["tier"] = np.select([df["rank"] <= 5, df["rank"] <= 11], ["act_now", "prepare"], "monitor")
        nfpc = df["name"].str.startswith("NBBS") * (cfg["exposure"]["nfpc_inflow"][0] // 3 if mode == "daytime" else 0)
        df["exposed_n"] = (pop * df["hazard"] / 20).astype(int) + nfpc
        df["exposure_mode"] = mode
        check(df, "barangay_index").to_parquet(out / f"barangay_index_{mode}.parquet")

    # backtest scores, invented but shaped like #6's output: the event model loses on MAE and wins on episodes
    base = {"b0_zero": [0.49, 1.92, 0.051, 0.50, 0.00, float("nan")],
            "b1_median": [0.48, 1.74, 0.049, 0.61, 0.25, 0.0],
            "b2_seasonal_nb": [0.52, 1.61, 0.046, 0.66, 0.25, 0.5],
            "event_glm": [0.55, 1.18, 0.038, 0.79, 0.75, 1.5]}
    names = ["mae", "mae_nonzero", "brier", "auc", "episode_recall", "lead_time_wk"]
    worse = {"mae": 1.04, "mae_nonzero": 1.06, "brier": 1.08, "auc": 0.95, "episode_recall": 0.85, "lead_time_wk": 0.8}
    rows = [{"model": m, "h": h, "split": "test", "metric": k, "value": round(v * worse[k] ** (h - 1), 3)}
            for m, vals in base.items() for h in cfg["horizons"] for k, v in zip(names, vals)]
    check(pd.DataFrame(rows), "metrics").to_parquet(out / "metrics.parquet")

    # 3 x 6 grid of squares, not real shapes; those come from `python -m f2f.ingest.fetch`
    feats = []
    for i, r in enumerate(brgy.itertuples()):
        x, y = 120.93 + (i % 3) * 0.006, 14.64 + (i // 3) * 0.006
        ring = [[x, y], [x + 0.005, y], [x + 0.005, y + 0.005], [x, y + 0.005], [x, y]]
        feats.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                      "properties": {"psgc10": r.psgc10, "name": r.name}})
    fc = check_boundaries({"type": "FeatureCollection", "features": feats})
    (out / "barangays.geojson").write_text(json.dumps(fc), encoding="utf-8")
    return out


if __name__ == "__main__":
    cfg = config.load(config.BASE.parent / "carina_2024.yaml")
    root = config.BASE.parents[1]
    print(f"fixtures -> {write(root / cfg['paths']['artifacts'] / '00000000-fixture', cfg)}")
