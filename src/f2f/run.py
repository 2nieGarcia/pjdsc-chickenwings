"""python -m f2f.run --config configs/carina_2024.yaml

Raw data in, one artifact folder out. The app only ever reads that folder. manifest.json (C8) says
what went in and how fresh it is; a step that can't run stops the run with its name and the file it wanted.
"""
import argparse
import json
import subprocess
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from f2f import config, contracts, features, index, replay
from f2f.forecast import event_model, backtest
from f2f.ingest import cchain, events, rain

WEEK = pd.Timedelta(weeks=1)


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "nogit"


def run_id() -> str:
    return f"{date.today():%Y%m%d}-{git_sha()}"


@contextmanager
def step(name: str):
    """Name the step in the error, so a missing input or stub reads as what to do next."""
    try:
        yield
    except FileNotFoundError as e:
        raise SystemExit(f"step '{name}': missing {e.filename}. See data/README.md for where it comes from.") from e
    except NotImplementedError as e:
        raise SystemExit(f"step '{name}': not implemented yet ({e or 'stub'})") from e
    except Exception as e:
        raise RuntimeError(f"step '{name}' failed: {type(e).__name__}: {e}") from e


def city_rain(raw: Path, cfg: dict) -> pd.DataFrame:
    """CCHAIN daily rain for all cities; CHIRPS (#3) continues the city's series after CCHAIN stops in 2022."""
    cc = cchain.load_climate(raw).assign(source="cchain")
    if not (raw / "chirps" / "navotas_daily.csv").exists():
        print("warning: no data/raw/chirps/navotas_daily.csv; run python -m f2f.ingest.rain, or the replay has no rain")
        return cc
    city = cfg["city"]["psgc10"]
    ch = rain.load_chirps(raw, city).assign(source="chirps")
    mine = cc[cc["city_psgc"] == city]
    # put CHIRPS on the CCHAIN scale the model and thresholds were built on, fit where both exist
    both = mine.merge(ch, on="date", suffixes=("_cc", "_ch")).dropna(subset=["rain_mm_cc", "rain_mm_ch"])
    if len(both) < 365 * 3:
        raise ValueError(f"only {len(both)} days where CHIRPS and CCHAIN overlap; pull CHIRPS from 2015 "
                         "(python -m f2f.ingest.rain) to scale it")
    ch["rain_mm"] = rain.to_reference(ch["rain_mm"].to_numpy(), both["rain_mm_ch"].to_numpy(), both["rain_mm_cc"].to_numpy())
    return pd.concat([cc, ch[ch["date"] > mine["date"].max()]], ignore_index=True)


def manifest(out: Path, cfg: dict, config_path: str, raw: Path, panel: pd.DataFrame) -> dict:
    """C8: what this run read and how far its data goes."""
    mine = panel[panel["city_psgc"] == cfg["city"]["psgc10"]]
    rain = mine.loc[mine["rain_wk_mm"].notna(), ["week_start", "source"]]
    files = sorted(f for f in raw.rglob("*") if f.is_file())
    return {
        "run_id": out.name,
        "config": str(config_path),
        "git_sha": git_sha(),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cases_through": f"{mine.loc[mine['cases'].notna(), 'week_start'].max():%Y-%m-%d}",
        "rain_through": f"{rain['week_start'].max() + pd.Timedelta(days=6):%Y-%m-%d}",
        "rain_sources": sorted(rain["source"].unique()),
        "flood_log": (raw / "events" / "flood_log.csv").exists(),
        "sources": [{"path": f.relative_to(raw).as_posix(), "bytes": f.stat().st_size,
                     "modified": f"{datetime.fromtimestamp(f.stat().st_mtime, timezone.utc):%Y-%m-%d}"} for f in files],
    }


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
    with step("index"):
        layers = index.load_layers(raw, cfg)
        for mode in ("resident", "daytime"):
            idx = contracts.check(index.build_index(layers, cfg, mode), "barangay_index")
            idx.to_parquet(out / f"barangay_index_{mode}.parquet")
    with step("boundaries"):
        fc = contracts.check_boundaries(index.boundaries(raw))
        (out / "barangays.geojson").write_text(json.dumps(fc), encoding="utf-8")

    with step("city_week"):
        flood_log = events.load_flood_log(raw) if (raw / "events" / "flood_log.csv").exists() else None
        panel = features.build_city_week(cchain.load_pidsr(raw), city_rain(raw, cfg), cchain.load_population(raw),
                                         cfg, flood_log)
        contracts.check(panel, "city_week").to_parquet(out / "city_week.parquet")
    with step("manifest"):
        m = manifest(out, cfg, args.config, raw, panel)
        (out / "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
        if not m["flood_log"]:
            print("warning: no data/raw/events/flood_log.csv, so flood_event is False everywhere (see data/README.md)")

    # C7 before the forecast step: #6 must not wait on the event model (#7)
    with step("metrics"):
        write_metrics(panel, out, cfg)
    with step("forecast"):
        contracts.check(forecast(panel, cfg), "forecast").to_parquet(out / "forecast.parquet")

    print(f"artifacts -> {out}")


if __name__ == "__main__":
    main()
