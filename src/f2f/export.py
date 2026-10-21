"""python -m f2f.export [--run data/artifacts/<run_id>]

Turns one artifact folder into the JSON the static front end (web/) reads, under web/public/data/.
Stock plans are computed here with f2f.planner so the browser never re-implements allocation.
"""
import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd

from f2f import config, fixtures
from f2f.planner import make_plan

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "data"

# shortcut: weekly replay rain is illustrative until CHIRPS lands (#3); flagged synthetic in meta
ILLUSTRATIVE_RAIN_MM = {"2024-07-01": 42, "2024-07-08": 68, "2024-07-15": 121, "2024-07-22": 310,
                        "2024-07-29": 96, "2024-08-05": 54, "2024-08-12": 30}


def latest_run(root: Path) -> Path:
    runs = sorted(p for p in root.glob("*") if (p / "barangay_index_resident.parquet").exists() and "fixture" not in p.name)
    if not runs:
        raise SystemExit(f"no artifact runs under {root}; run `python -m f2f.run` first")
    return runs[-1]


def records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", date_format="iso", date_unit="s"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    args = ap.parse_args(argv)
    cfg = config.load(config.BASE.parent / "carina_2024.yaml")
    run = Path(args.run) if args.run else latest_run(ROOT / cfg["paths"]["artifacts"])
    OUT.mkdir(parents=True, exist_ok=True)

    forecast_synthetic = not (run / "forecast.parquet").exists()
    if forecast_synthetic:
        with tempfile.TemporaryDirectory() as tmp:
            fc = pd.read_parquet(fixtures.write(Path(tmp), cfg) / "forecast.parquet")
    else:
        fc = pd.read_parquet(run / "forecast.parquet")
    (OUT / "forecast.json").write_text(json.dumps(records(fc)), encoding="utf-8")

    metrics_synthetic = not (run / "metrics.parquet").exists()
    if metrics_synthetic:
        with tempfile.TemporaryDirectory() as tmp:
            mt = pd.read_parquet(fixtures.write(Path(tmp), cfg) / "metrics.parquet")
    else:
        mt = pd.read_parquet(run / "metrics.parquet")
    (OUT / "metrics.json").write_text(json.dumps(records(mt)), encoding="utf-8")

    plans = {}
    for mode in ("resident", "daytime"):
        idx = pd.read_parquet(run / f"barangay_index_{mode}.parquet")
        (OUT / f"index_{mode}.json").write_text(json.dumps(records(idx)), encoding="utf-8")
        plans[mode] = {u: make_plan({
            "issue_date": cfg["replay"]["event_window"][0], "uptake": u, "buffer": cfg["planner"]["buffer"],
            "stock_on_hand": cfg["stock"]["on_hand_caps"], "exposure_mode": mode,
            "synthetic_stock": cfg["stock"]["synthetic"],
            "rows": idx[["psgc10", "tier", "exposed_n", "score"]].rename(columns={"exposed_n": "exposed"}).to_dict("records"),
        }, cfg["planner"]["caps_per_person"]) for u in cfg["planner"]["uptake_scenarios"]}
    (OUT / "plans.json").write_text(json.dumps(plans), encoding="utf-8")
    (OUT / "barangays.geojson").write_text((run / "barangays.geojson").read_text(encoding="utf-8"), encoding="utf-8")

    meta = {
        "run_id": run.name,
        "forecast_synthetic": forecast_synthetic,
        "metrics_synthetic": metrics_synthetic,
        "rain_synthetic": True,
        "rain_weekly_mm": ILLUSTRATIVE_RAIN_MM,
        "cases_through": "2022-12-26",
        "gate": {k: str(v) if not isinstance(v, list) else v for k, v in cfg["gate_impaired"].items()},
        "alerts": {k: cfg["alerts"][k] for k in ("watch_rain_lag2_mm", "warning_rain_lag2_mm")},
        "daytime": {"factor": cfg["exposure"]["daytime_factor"], "inflow": cfg["exposure"]["nfpc_scenario"]},
        "uptake_default": cfg["planner"]["uptake"],
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"exported {run.name} -> {OUT}")


if __name__ == "__main__":
    main()
