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
  coping_gap     km_to_care        straight-line km from the barangay centroid to the nearest
                                   hospital/clinic/health post in OSM, any city

Each indicator: log1p where skewed, winsorised, min-max to [1, 10]. A constant indicator carries no
information and is dropped. Dimensions are the mean of their indicators; score is the geometric
mean of hazard, exposure (by mode), vulnerability and coping_gap, so a barangay that doesn't flood
can't rank high on crowding alone. Rank bands (#11) are left equal to the rank for now.
"""
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from f2f import barangays, exposure, geo

DIMENSIONS = {
    "hazard": ["flood25_any", "flood100_medhigh", "gate_affected"],
    "exposure_res": ["pop_resident"],
    "exposure_day": ["pop_daytime"],
    "vulnerability": ["small_bldg_share", "built_up_pct", "pop_density"],
    "coping_gap": ["km_to_care"],
}
LOG = {"pop_resident", "pop_daytime", "pop_density", "km_to_care"}
CARE_AMENITY = {"hospital", "clinic", "doctors", "health_post"}
CARE_HEALTHCARE = {"hospital", "clinic", "centre", "community_health_worker", "doctor"}


def load_layers(raw: Path, cfg: dict) -> pd.DataFrame:
    """One row per barangay with every raw indicator. Needs `python -m f2f.ingest.static` first."""
    raw = Path(raw)
    cc = raw / "cchain"
    noah = pd.read_csv(cc / "project_noah_hazards.csv")
    bldg = pd.read_csv(cc / "google_open_buildings.csv")
    parent = noah.assign(
        flood25_any=noah.filter(regex=r"flood_hazard_25yr_").sum(axis=1),
        flood100_medhigh=noah["pct_area_flood_hazard_100yr_med"] + noah["pct_area_flood_hazard_100yr_high"],
    )[["adm4_pcode", "flood25_any", "flood100_medhigh"]].merge(
        bldg.assign(small_bldg_share=bldg["google_bldgs_count_lt100_sqm"] / bldg["google_bldgs_count"],
                    built_up_pct=bldg["google_bldgs_pct_built_up_area"])
        [["adm4_pcode", "small_bldg_share", "built_up_pct"]], on="adm4_pcode",
    ).rename(columns={"adm4_pcode": "parent_psgc_cchain"})
    df = barangays.to_children(parent, intensive=["flood25_any", "flood100_medhigh", "small_bldg_share", "built_up_pct"])

    shapes = polygons(raw)
    df = df.merge(shapes, on="psgc10", how="left")
    if df["area_km2"].isna().any():
        raise ValueError(f"no polygon for {df.loc[df['area_km2'].isna(), 'name'].tolist()}")

    pop = exposure.present_population(cfg)[["psgc10", "pop_resident", "pop_daytime"]]
    df = df.merge(pop, on="psgc10")
    df["pop_density"] = df["pop_resident"] / df["area_km2"]
    df["gate_affected"] = df["psgc10"].isin(cfg.get("gate_impaired", {}).get("barangays", [])).astype(float)

    care = care_points(raw)
    df["km_to_care"] = [min(geo.haversine_km(x, y, cx, cy) for cx, cy in care) for x, y in zip(df["lon"], df["lat"])]
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


def care_points(raw: Path, pad: float = 0.05) -> list[tuple[float, float]]:
    """Primary-care points from the HOT OSM export, within `pad` degrees of Navotas.

    City tags in that export are unreliable (Navotas City Hospital is tagged Caloocan), so filter by
    distance, not by city. shortcut: straight-line distance, OSM coverage of barangay health
    centres is thin; swap in the CLUP facility list or OSRM walking time when someone has them.
    """
    with zipfile.ZipFile(Path(raw) / "osm" / "hotosm_phl_health_facilities.zip") as z:
        fc = json.loads(z.read("health_facilities.geojson"))
    pts = []
    for f in fc["features"]:
        p, g = f["properties"], f["geometry"]
        if not g or not (p.get("amenity") in CARE_AMENITY or p.get("healthcare") in CARE_HEALTHCARE):
            continue
        if any(w in (p.get("name") or "").lower() for w in ("dental", "animal", "dialysis")):
            continue
        if g["type"] == "Point":
            x, y = g["coordinates"][:2]
        elif "Polygon" in g["type"]:
            _, x, y = geo.area_centroid(g)
        else:
            continue
        if 120.92 - pad <= x <= 120.97 + pad and 14.63 - pad <= y <= 14.70 + pad:
            pts.append((x, y))
    if not pts:
        raise ValueError("no health facilities found near Navotas")
    return pts


def scale(s: pd.Series, winsor=(0.05, 0.95), log: bool = False, lo: float = 1, hi: float = 10) -> pd.Series:
    """log1p (optional) -> winsorise -> min-max to [lo, hi]. NaN for a constant series."""
    s = np.log1p(s) if log else s.astype(float)
    s = s.clip(s.quantile(winsor[0]), s.quantile(winsor[1]))
    span = s.max() - s.min()
    return lo + (hi - lo) * (s - s.min()) / span if span > 0 else pd.Series(np.nan, index=s.index)


def build_index(layers: pd.DataFrame, cfg: dict, exposure_mode: str) -> pd.DataFrame:
    if exposure_mode not in ("resident", "daytime"):
        raise ValueError("exposure_mode must be resident or daytime")
    ic = cfg["index"]
    out = layers[["psgc10", "name", "parent_psgc_cchain"]].copy()
    for dim, cols in DIMENSIONS.items():
        scaled = pd.concat([scale(layers[c], tuple(ic["winsor"]), c in LOG) for c in cols], axis=1)
        out[dim] = scaled.mean(axis=1).fillna(1.0)  # every indicator constant -> no signal, floor it

    expo = out["exposure_day" if exposure_mode == "daytime" else "exposure_res"]
    out["score"] = (out["hazard"] * expo * out["vulnerability"] * out["coping_gap"]) ** 0.25
    out["rank"] = out["score"].rank(ascending=False, method="first").astype(int)
    out["rank_p05"] = out["rank"]
    out["rank_p95"] = out["rank"]
    out["tier"] = np.select([out["rank"] <= ic["act_now_top"], out["rank"] <= ic["act_now_top"] + ic["prepare_next"]],
                            ["act_now", "prepare"], "monitor")
    pop = layers["pop_daytime" if exposure_mode == "daytime" else "pop_resident"]
    out["exposed_n"] = (pop * layers["flood25_any"] / 100).round().astype(int)
    out["exposure_mode"] = exposure_mode
    return out.sort_values("rank").reset_index(drop=True)
