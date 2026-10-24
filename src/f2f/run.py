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
from f2f.forecast import event_model, backtest
from f2f.ingest import cchain, events

WEEK = pd.Timedelta(weeks=1)


def run_id() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "nogit"
    return f"{date.today():%Y%m%d}-{sha}"


def write_metrics(panel: pd.DataFrame, out: Path, cfg: dict) -> pd.DataFrame:
    """Score B0/B1/B2 and the event model on the pooled panel and write C7 into the run folder."""
    cutoff = cfg["alerts"]["p_cutoff"] or backtest.DEFAULT_CUTOFF
    models = {**backtest.default_models(), "event_glm": lambda h: event_model.EventGLM(h, cfg)}
    metrics = backtest.run_backtest(
        panel,
        cfg["city"]["psgc10"],
        models=models,
        horizons=tuple(cfg["horizons"]),
        cutoff=cutoff,
    )
    checked = contracts.check(metrics, "metrics")
    checked.to_parquet(out / "metrics.parquet")
    return checked


def forecast(panel: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """C2 for every replay issue date and horizon. Each fit sees only weeks complete before the issue Monday."""
    city = cfg["city"]["psgc10"]
    nav = panel[panel["city_psgc"] == city]
    rows = []
    for issue in replay.issue_dates(cfg):
        past = panel[panel["week_start"] + WEEK <= issue]
        mine = past[past["city_psgc"] == city]
        through = {"cases_through": mine.loc[mine["cases"].notna(), "week_start"].max(),
                   "rain_through": mine.loc[mine["rain_wk_mm"].notna(), "week_start"].max() + pd.Timedelta(days=6)}
        for h in cfg["horizons"]:
            target = issue + h * WEEK
            # pass the weeks before the target too: the flood part of the alert looks back from the issue date
            upto = nav[nav["week_start"] <= target]
            pred = event_model.EventGLM(h, cfg).fit(past).predict(upto)
            rows.append(pred[(upto["week_start"] == target).to_numpy()].assign(issue_date=issue, city_psgc=city, h=h,
                                                                  target_week=target, **through))
    return pd.concat(rows, ignore_index=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/carina_2024.yaml")
    args = ap.parse_args(argv)

    cfg = config.load(args.config)
    raw = Path(cfg["paths"]["raw"])
    out = Path(cfg["paths"]["artifacts"]) / run_id()
    out.mkdir(parents=True, exist_ok=True)

    # static layers first: the index doesn't wait on case data or the forecast
    layers = index.load_layers(raw, cfg)
    for mode in ("resident", "daytime"):
        idx = contracts.check(index.build_index(layers, cfg, mode), "barangay_index")
        idx.to_parquet(out / f"barangay_index_{mode}.parquet")
    fc = contracts.check_boundaries(index.boundaries(raw))
    (out / "barangays.geojson").write_text(json.dumps(fc), encoding="utf-8")

    # CCHAIN rain stops at 2022; CHIRPS (#3) fills 2023-24 for the replay once ingest.rain is done
    flood_log = events.load_flood_log(raw) if (raw / "events" / "flood_log.csv").exists() else None
    panel = features.build_city_week(cchain.load_pidsr(raw), cchain.load_climate(raw), cchain.load_population(raw),
                                     cfg, flood_log)
    contracts.check(panel, "city_week").to_parquet(out / "city_week.parquet")

    # C7 before the forecast step: #6 must not wait on the event model (#7)
    write_metrics(panel, out, cfg)

    contracts.check(forecast(panel, cfg), "forecast").to_parquet(out / "forecast.parquet")

    print(f"artifacts -> {out}")


if __name__ == "__main__":
    main()
