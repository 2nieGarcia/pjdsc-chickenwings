"""python -m f2f.run --config configs/carina_2024.yaml

Raw data in, one artifact folder out. The app only ever reads that folder.
"""
import argparse
import json
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd

from f2f import config, contracts, features, index, replay
from f2f.forecast import backtest, event_model
from f2f.forecast.baselines import B0Zero, B1Median, B2SeasonalNB
from f2f.ingest import cchain, events


def run_id() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "nogit"
    return f"{date.today():%Y%m%d}-{sha}"


def get_backtest_models(cfg: dict) -> dict:
    """Return baselines plus the event_glm factory for the harness."""
    return {
        "b0_zero": B0Zero(),
        "b1_median": B1Median(),
        "b2_seasonal_nb": B2SeasonalNB(),
        "event_glm": lambda h: event_model.EventGLM(h=h, cfg=cfg),
    }

def write_metrics(panel: pd.DataFrame, out: Path, cfg: dict) -> pd.DataFrame:
    """Score all models on the pooled panel and write C7 into the run folder."""
    cutoff = cfg["alerts"]["p_cutoff"] or backtest.DEFAULT_CUTOFF
    metrics = backtest.run_backtest(
        panel,
        cfg["city"]["psgc10"],
        models=get_backtest_models(cfg),  # <--- THIS LINE MUST BE HERE
        horizons=tuple(cfg["horizons"]),
        cutoff=cutoff,
    )
    checked = contracts.check(metrics, "metrics")
    checked.to_parquet(out / "metrics.parquet")
    return checked


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/carina_2024.yaml")
    args = ap.parse_args(argv)

    cfg = config.load(args.config)
    raw = Path(cfg["paths"]["raw"])
    out = Path(cfg["paths"]["artifacts"]) / run_id()
    out.mkdir(parents=True, exist_ok=True)

    layers = index.load_layers(raw, cfg)
    for mode in ("resident", "daytime"):
        idx = contracts.check(index.build_index(layers, cfg, mode), "barangay_index")
        idx.to_parquet(out / f"barangay_index_{mode}.parquet")
    fc = contracts.check_boundaries(index.boundaries(raw))
    (out / "barangays.geojson").write_text(json.dumps(fc), encoding="utf-8")

    flood_log = events.load_flood_log(raw) if (raw / "events" / "flood_log.csv").exists() else None
    panel = features.build_city_week(cchain.load_pidsr(raw), cchain.load_climate(raw), cchain.load_population(raw),
                                     cfg, flood_log)
    contracts.check(panel, "city_week").to_parquet(out / "city_week.parquet")

    write_metrics(panel, out, cfg)

    # C2 forecast generation for Carina replay (True rolling replay)
    # C2 forecast generation for Carina replay (True rolling replay)
    issues = replay.issue_dates(cfg)
    target_city = cfg["city"]["psgc10"]
    
    forecast_rows = []
    for issue_date in issues:
        for h in cfg["horizons"]:
            target_week = issue_date + pd.Timedelta(weeks=h)
            
            # Train ONLY on data up to the issue date to prevent future leakage
            train_panel = panel[panel["week_start"] <= issue_date].reset_index(drop=True)
            if train_panel.empty:
                continue
                
            model = event_model.EventGLM(h=h, cfg=cfg)
            model.fit(train_panel)
            
            # Evaluate only on the specific target week for this issue/horizon
            eval_panel = panel[
                (panel["week_start"] == target_week) & 
                (panel["city_psgc"] == target_city)
            ].copy().reset_index(drop=True)
            
            if eval_panel.empty:
                continue
                
            # Concat to provide history for .shift(h) in feature engineering
            pred_input = pd.concat([train_panel, eval_panel], ignore_index=True)
            full_preds = model.predict(pred_input)
            
            # Slice back to eval rows and reset index
            preds = full_preds.iloc[-len(eval_panel):].reset_index(drop=True)
            
            # Reconstruct the dataframe with city_psgc to satisfy C2 contract
            preds_df = eval_panel[["city_psgc", "week_start"]].copy()
            preds_df[["p_elevated", "q05", "q50", "q95", "alert", "drivers", "model"]] = preds.to_numpy()
            
            for _, row in preds_df.iterrows():
                forecast_rows.append({
                    "issue_date": issue_date,
                    "city_psgc": row["city_psgc"],
                    "h": h,
                    "target_week": target_week,
                    "p_elevated": row["p_elevated"],
                    "q05": row["q05"],
                    "q50": row["q50"],
                    "q95": row["q95"],
                    "alert": row["alert"],
                    "drivers": row["drivers"],
                    "model": row["model"],
                    "rain_through": issue_date,
                    "cases_through": issue_date,
                })

    fc_df = pd.DataFrame(forecast_rows)
    contracts.check(fc_df, "forecast").to_parquet(out / "forecast.parquet")
    print(f"artifacts -> {out}")


if __name__ == "__main__":
    main()