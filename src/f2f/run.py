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


def run_id() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "nogit"
    return f"{date.today():%Y%m%d}-{sha}"


def write_metrics(panel: pd.DataFrame, out: Path, cfg: dict) -> pd.DataFrame:
    """Score B0/B1/B2 on the pooled panel and write C7 into the run folder."""
    cutoff = cfg["alerts"]["p_cutoff"] or backtest.DEFAULT_CUTOFF
    metrics = backtest.run_backtest(
        panel,
        cfg["city"]["psgc10"],
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

    issues = replay.issue_dates(cfg)
    fc = [event_model.predict(event_model.fit(panel, h, cfg), panel, issues, h) for h in cfg["horizons"]]
    contracts.check(pd.concat(fc), "forecast").to_parquet(out / "forecast.parquet")

    print(f"artifacts -> {out}")


if __name__ == "__main__":
    main()