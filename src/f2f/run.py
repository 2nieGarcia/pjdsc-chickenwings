"""python -m f2f.run --config configs/carina_2024.yaml

Raw data in, one artifact folder out. The app only ever reads that folder.
"""
import argparse
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd

from f2f import config, contracts, features, index, replay
from f2f.forecast import event_model
from f2f.ingest import cchain, events, rain


def run_id() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "nogit"
    return f"{date.today():%Y%m%d}-{sha}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/carina_2024.yaml")
    args = ap.parse_args(argv)

    cfg = config.load(args.config)
    raw = Path(cfg["paths"]["raw"])
    out = Path(cfg["paths"]["artifacts"]) / run_id()
    out.mkdir(parents=True, exist_ok=True)

    pidsr = cchain.load_pidsr(raw)
    # from 2015 so CHIRPS overlaps CCHAIN climate for the distribution check
    rain_daily = rain.chirps_daily("2015-01-01", str(cfg["replay"]["issue_end"]), {})  # TODO city polygon
    flood_log = events.load_flood_log(raw)

    panel = contracts.check(features.build_city_week(pidsr, rain_daily, flood_log, cfg), "city_week")
    panel.to_parquet(out / "city_week.parquet")

    issues = replay.issue_dates(cfg)
    fc = [event_model.predict(event_model.fit(panel, h, cfg), panel, issues, h) for h in cfg["horizons"]]
    contracts.check(pd.concat(fc), "forecast").to_parquet(out / "forecast.parquet")

    for mode in ("resident", "daytime"):
        idx = contracts.check(index.build_index(None, cfg, mode), "barangay_index")  # TODO layers loader
        idx.to_parquet(out / f"barangay_index_{mode}.parquet")

    print(f"artifacts -> {out}")


if __name__ == "__main__":
    main()
