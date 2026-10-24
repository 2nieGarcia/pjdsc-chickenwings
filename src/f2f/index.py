"""Barangay priority index (contract C3), INFORM-style.

Indicators, all "higher = worse":

  hazard         flood25_any       % area in NOAH 25-yr flood zone, any depth (CCHAIN, parent level)
                 flood100_medhigh  % area in NOAH 100-yr medium/high depth (CCHAIN, parent level)
                 gate_affected     1 if the barangay is on gate_impaired.barangays in config
  exposure       pop_resident      POPCEN 2024
                 pop_daytime       f2f.exposure scenario (used instead in daytime mode)
  vulnerability  small_bldg_share  share of buildings under 100 m2, informal-housing proxy (Open Buildings 2023, parent level)
                 built_up_pct      % of area built up (Open Buildings 2023, parent level)
                 pop_density       residents per km2 (POPCEN 2024 / polygon area)
  coping_gap     no_hc_15min       % of residents not within 15 min of a barangay health centre (Mapbox isochrones 2022, parent level)
                 no_hosp_15min     % of residents not within 15 min of a hospital (Mapbox isochrones 2022, parent level)
                 m_to_primary      metres to the nearest DOH barangay health station or RHU (DOH geoportal 2013, parent level)

Each indicator: log1p where skewed, winsorised, min-max to [1, 10]. A constant indicator carries no
information and is dropped. Dimensions are the mean of their indicators; score is the geometric
mean of hazard, exposure (by mode), vulnerability and coping_gap, so a barangay that doesn't flood
can't rank high on crowding alone.

Rank bands (#11): the four equal weights are jittered by +-index.weight_jitter and renormalised,
index.mc_draws times. Each draw ranks all 18 barangays; rank_p05/p95 are the 5th/95th percentiles
of those ranks. Seeded, so the same components always give the same band.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from f2f import barangays, config, exposure, geo

SEED = 0
AGGREGATIONS = ("geometric", "arithmetic")

DIMENSIONS = {
    "hazard": ["flood25_any", "flood100_medhigh", "gate_affected"],
    "exposure_res": ["pop_resident"],
    "exposure_day": ["pop_daytime"],
    "vulnerability": ["small_bldg_share", "built_up_pct", "pop_density"],
    "coping_gap": ["no_hc_15min", "no_hosp_15min", "m_to_primary"],
}
LOG = {"pop_resident", "pop_daytime", "pop_density", "m_to_primary"}
PARENT = ["flood25_any", "flood100_medhigh", "small_bldg_share", "built_up_pct", "no_hc_15min", "no_hosp_15min", "m_to_primary"]


def load_layers(raw: Path, cfg: dict) -> pd.DataFrame:
    """One row per barangay with every raw indicator. Needs `python -m f2f.ingest.fetch` first."""
    raw = Path(raw)
    cc = raw / "cchain"
    noah = pd.read_csv(cc / "project_noah_hazards.csv")
    bldg = pd.read_csv(cc / "google_open_buildings.csv")
    iso = pd.read_csv(cc / "mapbox_health_facility_brgy_isochrones.csv")
    doh = pd.read_csv(cc / "geoportal_doh_poi_health.csv")
    parent = noah.assign(
        flood25_any=noah.filter(regex=r"flood_hazard_25yr_").sum(axis=1),
        flood100_medhigh=noah["pct_area_flood_hazard_100yr_med"] + noah["pct_area_flood_hazard_100yr_high"],
    )[["adm4_pcode", "flood25_any", "flood100_medhigh"]].merge(
        bldg.assign(small_bldg_share=bldg["google_bldgs_count_lt100_sqm"] / bldg["google_bldgs_count"],
                    built_up_pct=bldg["google_bldgs_pct_built_up_area"])
        [["adm4_pcode", "small_bldg_share", "built_up_pct"]], on="adm4_pcode",
    ).merge(
        iso.assign(no_hc_15min=100 - iso["brgy_healthcenter_pop_reached_pct_15min"],
                   no_hosp_15min=100 - iso["hospital_pop_reached_pct_15min"])
        [["adm4_pcode", "no_hc_15min", "no_hosp_15min"]], on="adm4_pcode",
    ).merge(
        doh.assign(m_to_primary=doh[["doh_brgy_health_station_nearest", "doh_rural_health_unit_nearest"]].min(axis=1))
        [["adm4_pcode", "m_to_primary"]], on="adm4_pcode",
    ).rename(columns={"adm4_pcode": "parent_psgc_cchain"})
    df = barangays.to_children(parent, intensive=PARENT)

    shapes = polygons(raw)
    df = df.merge(shapes, on="psgc10", how="left")
    if df["area_km2"].isna().any():
        raise ValueError(f"no polygon for {df.loc[df['area_km2'].isna(), 'name'].tolist()}")

    pop = exposure.present_population(cfg)[["psgc10", "pop_resident", "pop_daytime"]]
    df = df.merge(pop, on="psgc10")
    df["pop_density"] = df["pop_resident"] / df["area_km2"]
    df["gate_affected"] = df["psgc10"].isin(cfg.get("gate_impaired", {}).get("barangays", [])).astype(float)
    return df


def polygons(raw: Path) -> pd.DataFrame:
    """psgc10, area_km2, lon, lat from data/raw/boundaries/navotas_brgy.geojson."""
    fc = json.loads((Path(raw) / "boundaries" / "navotas_brgy.geojson").read_text(encoding="utf-8"))
    rows = []
    for f in fc["features"]:
        a, x, y = geo.area_centroid(f["geometry"])
        rows.append({"psgc10": str(f["properties"]["adm4_psgc"]), "area_km2": a, "lon": x, "lat": y})
    return pd.DataFrame(rows)


def boundaries(raw: Path) -> dict:
    """The barangay polygons trimmed to psgc10 + name, for the map artifact."""
    fc = json.loads((Path(raw) / "boundaries" / "navotas_brgy.geojson").read_text(encoding="utf-8"))
    names = barangays.load().set_index("psgc10")["name"]
    feats = [{"type": "Feature", "geometry": f["geometry"],
              "properties": {"psgc10": str(f["properties"]["adm4_psgc"]),
                             "name": names[str(f["properties"]["adm4_psgc"])]}}
             for f in fc["features"]]
    return {"type": "FeatureCollection", "features": feats}


def scale(s: pd.Series, winsor=(0.05, 0.95), log: bool = False, lo: float = 1, hi: float = 10) -> pd.Series:
    """log1p (optional) -> winsorise -> min-max to [lo, hi]. NaN for a constant series."""
    s = np.log1p(s) if log else s.astype(float)
    s = s.clip(s.quantile(winsor[0]), s.quantile(winsor[1]))
    span = s.max() - s.min()
    return lo + (hi - lo) * (s - s.min()) / span if span > 0 else pd.Series(np.nan, index=s.index)


def _exposure(exposure_mode: str) -> str:
    return "exposure_day" if exposure_mode == "daytime" else "exposure_res"


def _score(dims: np.ndarray, weights: np.ndarray, how: str) -> np.ndarray:
    """(draws, 4) weights x (18, 4) components -> (draws, 18) scores."""
    if how == "geometric":
        return np.exp(weights @ np.log(dims).T)
    if how == "arithmetic":
        return weights @ dims.T
    raise ValueError(f"aggregation must be one of {AGGREGATIONS}")


def _rank(scores: np.ndarray) -> np.ndarray:
    """1 is the highest score. Stable, so equal scores keep row order."""
    return (-scores).argsort(axis=1, kind="stable").argsort(axis=1) + 1


def bands(frame: pd.DataFrame, cfg: dict, exposure_mode: str, how: str = "geometric") -> pd.DataFrame:
    """Median rank, 90% band and mean absolute rank shift under jittered equal weights.

    `frame` is C3-shaped: the four dimension columns plus psgc10 and name. The shift is against
    the equal-weight rank of the same rows, so it says how far a draw usually moves a barangay.
    """
    dims = frame[["hazard", _exposure(exposure_mode), "vulnerability", "coping_gap"]].to_numpy(float)
    ic = cfg["index"]
    rng = np.random.default_rng(SEED)
    w = 1 + rng.uniform(-ic["weight_jitter"], ic["weight_jitter"], size=(ic["mc_draws"], dims.shape[1]))
    w /= w.sum(axis=1, keepdims=True)
    ranks = _rank(_score(dims, w, how))
    base = _rank(_score(dims, np.full((1, dims.shape[1]), 0.25), how))[0]
    return pd.DataFrame({
        "psgc10": frame["psgc10"].to_numpy(),
        "name": frame["name"].to_numpy(),
        "median_rank": np.median(ranks, axis=0),
        "rank_p05": np.quantile(ranks, 0.05, axis=0, method="lower").astype(int),
        "rank_p95": np.quantile(ranks, 0.95, axis=0, method="higher").astype(int),
        "mean_abs_shift": np.abs(ranks - base).mean(axis=0).round(2),
    })


def sensitivity(frames: dict[str, pd.DataFrame], cfg: dict) -> pd.DataFrame:
    """One long table: per exposure mode and aggregation, the bands and shift for all 18 barangays."""
    rows = [bands(f, cfg, mode, how).assign(exposure_mode=mode, aggregation=how)
            for mode, f in frames.items() for how in AGGREGATIONS]
    cols = ["exposure_mode", "aggregation", "psgc10", "name", "median_rank", "rank_p05", "rank_p95",
            "mean_abs_shift"]
    return pd.concat(rows, ignore_index=True)[cols]


def build_index(layers: pd.DataFrame, cfg: dict, exposure_mode: str) -> pd.DataFrame:
    if exposure_mode not in ("resident", "daytime"):
        raise ValueError("exposure_mode must be resident or daytime")
    ic = cfg["index"]
    out = layers[["psgc10", "name", "parent_psgc_cchain"]].copy()
    for dim, cols in DIMENSIONS.items():
        scaled = pd.concat([scale(layers[c], tuple(ic["winsor"]), c in LOG) for c in cols], axis=1)
        out[dim] = scaled.mean(axis=1).fillna(1.0)  # every indicator constant -> no signal, floor it

    expo = out[_exposure(exposure_mode)]
    out["score"] = (out["hazard"] * expo * out["vulnerability"] * out["coping_gap"]) ** 0.25
    out["rank"] = out["score"].rank(ascending=False, method="first").astype(int)
    band = bands(out, cfg, exposure_mode)
    # the equal-weight rank can sit in the draws' 5% tail; keep it inside its own band
    out["rank_p05"] = np.minimum(band["rank_p05"].to_numpy(), out["rank"])
    out["rank_p95"] = np.maximum(band["rank_p95"].to_numpy(), out["rank"])
    out["tier"] = np.select([out["rank"] <= ic["act_now_top"], out["rank"] <= ic["act_now_top"] + ic["prepare_next"]],
                            ["act_now", "prepare"], "monitor")
    pop = layers["pop_daytime" if exposure_mode == "daytime" else "pop_resident"]
    out["exposed_n"] = (pop * layers["flood25_any"] / 100).round().astype(int)
    out["exposure_mode"] = exposure_mode
    return out.sort_values("rank").reset_index(drop=True)


def main(run: Path) -> pd.DataFrame:
    """Print the sensitivity table for one artifact folder (both exposure modes)."""
    frames = {mode: pd.read_parquet(Path(run) / f"barangay_index_{mode}.parquet")
              for mode in ("resident", "daytime")}
    table = sensitivity(frames, config.load())
    print(table.to_string(index=False))
    return table


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m f2f.index <run_dir>, e.g. data/artifacts/00000000-fixture")
    main(Path(sys.argv[1]))
