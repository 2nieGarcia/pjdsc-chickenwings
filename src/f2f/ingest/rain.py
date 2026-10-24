"""python -m f2f.ingest.rain

CHIRPS v2.0 daily rain over the Navotas polygon, 2015-01-01 to 2024-08-31, written to
data/raw/chirps/navotas_daily.csv. Pulled from the IRI Data Library mirror of UCSB CHIRPS,
which needs no login. Earth Engine has the same dataset (`.[ee]` extra) but is not required.
"""
import json
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import netcdf_file

from f2f import config

IRI = ("https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.daily-improved/.global/.0p05/.prcp/"
       "X/{x0}/{x1}/RANGEEDGES/Y/{y0}/{y1}/RANGEEDGES/T/({t0})/({t1})/RANGEEDGES/data.nc")
START, END = "2015-01-01", "2024-08-31"
JD_UNIX = 2440587.5  # julian day of 1970-01-01


def _polygons(geojson: dict) -> list:
    """FeatureCollection, Feature or geometry -> list of polygons (each a list of rings)."""
    if "features" in geojson:
        return [p for f in geojson["features"] for p in _polygons(f)]
    g = geojson.get("geometry", geojson)
    return [g["coordinates"]] if g["type"] == "Polygon" else list(g["coordinates"])


def _in_ring(px: np.ndarray, py: np.ndarray, ring) -> np.ndarray:
    """Ray casting, vectorised over points."""
    r = np.asarray(ring, dtype=float)[:, :2]
    x0, y0, x1, y1 = r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]
    px, py = px[:, None], py[:, None]
    crosses = (y0 > py) != (y1 > py)
    with np.errstate(divide="ignore", invalid="ignore"):
        xi = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
    return (crosses & (px < xi)).sum(axis=1) % 2 == 1


def pixel_weights(x: np.ndarray, y: np.ndarray, geojson: dict, step: float = 0.001) -> np.ndarray:
    """(len(y), len(x)) share of the city's area inside each pixel, summing to 1.

    Samples a step-degree point grid; holes handled by even-odd over each polygon's rings.
    """
    polys = _polygons(geojson)
    pts = np.concatenate([np.asarray(ring, dtype=float)[:, :2] for p in polys for ring in p])
    gx = np.arange(pts[:, 0].min(), pts[:, 0].max() + step, step) + step / 2
    gy = np.arange(pts[:, 1].min(), pts[:, 1].max() + step, step) + step / 2
    px, py = (a.ravel() for a in np.meshgrid(gx, gy))
    inside = np.zeros(px.size, bool)
    for p in polys:
        inside |= np.logical_xor.reduce([_in_ring(px, py, ring) for ring in p])
    px, py = px[inside], py[inside]
    dx, dy = abs(x[1] - x[0]) if len(x) > 1 else 0.05, abs(y[1] - y[0]) if len(y) > 1 else 0.05
    ix, iy = np.abs(px[:, None] - x).argmin(1), np.abs(py[:, None] - y).argmin(1)
    if (np.abs(px - x[ix]) > dx / 2 + 1e-6).any() or (np.abs(py - y[iy]) > dy / 2 + 1e-6).any():
        raise ValueError("city polygon extends past the CHIRPS pixels supplied")
    w = np.zeros((len(y), len(x)))
    np.add.at(w, (iy, ix), 1)
    return w / w.sum()


def area_mean(prcp: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """(T, Y, X) mm/day with NaN for missing -> (T,) mean, weights renormalised over valid pixels each day."""
    valid = np.isfinite(prcp)
    w = weights[None] * valid
    tot = w.sum(axis=(1, 2))
    with np.errstate(invalid="ignore"):
        return np.where(tot > 0, (np.where(valid, prcp, 0) * w).sum(axis=(1, 2)) / tot, np.nan)


def _download(url: str, dest: Path, tries: int = 5, timeout: int = 300) -> None:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                tmp = dest.with_suffix(".part")
                tmp.write_bytes(r.read())
            tmp.replace(dest)  # only whole files land, so a cached quarter is always complete
            return
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(10 * (i + 1))


def _read(path: Path):
    """netCDF3 from IRI -> x, y, dates, prcp (T, Y, X) with NaN for missing (sea pixels)."""
    with netcdf_file(path, mmap=False) as f:
        v = f.variables
        prcp = v["prcp"][:].astype(float)
        prcp[prcp == float(v["prcp"].missing_value)] = np.nan
        dates = pd.to_datetime(v["T"][:].astype(float) - JD_UNIX, unit="D").floor("D")
        return v["X"][:].astype(float), v["Y"][:].astype(float), dates, prcp


def chirps_daily(start: str, end: str, city_geojson: dict, cache: Path | None = None) -> pd.DataFrame:
    """Area-weighted mean rain in mm per day -> columns date, rain_mm.

    The 0.05 deg pixels on the coast cover Manila Bay; weight by area inside the city polygon.
    Pulled one quarter at a time: IRI answers a quarter in ~10 s but times out on a full year, and
    sometimes on a quarter. With `cache`, each quarter's netCDF is kept there, so a rerun resumes.
    """
    pts = np.concatenate([np.asarray(r, dtype=float)[:, :2] for p in _polygons(city_geojson) for r in p])
    box = dict(x0=pts[:, 0].min(), x1=pts[:, 0].max(), y0=pts[:, 1].min(), y1=pts[:, 1].max())
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    out, weights = [], None
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(cache) if cache else Path(tmp)
        folder.mkdir(parents=True, exist_ok=True)
        for q in pd.period_range(start, end, freq="Q"):
            t0, t1 = max(start, q.start_time.normalize()), min(end, q.end_time.normalize())
            url = IRI.format(**{k: f"{v:.4f}" for k, v in box.items()},
                             t0=urllib.parse.quote(f"{t0:%d %b %Y}"), t1=urllib.parse.quote(f"{t1:%d %b %Y}"))
            nc = folder / f"{q}_{t0:%m%d}_{t1:%m%d}.nc"
            if not nc.exists():
                _download(url, nc)
            x, y, dates, prcp = _read(nc)
            want = pd.date_range(t0, t1)
            if not dates.equals(want):
                raise ValueError(f"CHIRPS {q}: got {dates[0]:%F}..{dates[-1]:%F} ({len(dates)} days), wanted {t0:%F}..{t1:%F}")
            weights = pixel_weights(x, y, city_geojson) if weights is None else weights
            out.append(pd.DataFrame({"date": dates, "rain_mm": area_mean(prcp, weights)}))
    return pd.concat(out, ignore_index=True)


def to_reference(x: np.ndarray, src: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Empirical quantile mapping: each value of x moves from its quantile in src to the same quantile in ref.

    CHIRPS reads ~20% drier than CCHAIN over Navotas 2015-2022 and rarely reaches the 320 mm weekly
    line (0 weeks vs 11), while the model and alert thresholds are on the CCHAIN scale. Mapping fit on
    2015-19 and checked on 2020-22 recovered 10 of 17 CCHAIN weeks >= 160 mm (raw 6, one scale factor 7).
    Values past src's range clamp to ref's extremes.
    """
    q = np.linspace(0, 1, 1001)
    return np.interp(x, np.quantile(src, q), np.quantile(ref, q))


def load_chirps(raw: Path, city_psgc: str = "1380900000") -> pd.DataFrame:
    """Navotas daily CHIRPS rain in the cchain.load_climate shape: city_psgc, date, rain_mm."""
    df = pd.read_csv(Path(raw) / "chirps" / "navotas_daily.csv", parse_dates=["date"])
    return pd.DataFrame({"city_psgc": city_psgc, "date": df["date"], "rain_mm": df["rain_mm"]})


if __name__ == "__main__":
    raw = Path(config.load()["paths"]["raw"])
    city = json.loads((raw / "boundaries" / "navotas_brgy.geojson").read_text(encoding="utf-8"))
    df = chirps_daily(*(sys.argv[1:3] or (START, END)), city, cache=raw / "chirps" / "nc")
    dest = raw / "chirps" / "navotas_daily.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False, date_format="%Y-%m-%d", float_format="%.3f")
    print(f"{len(df)} days -> {dest}")
