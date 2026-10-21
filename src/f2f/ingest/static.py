"""python -m f2f.ingest.static

Downloads the static barangay layers into data/raw/. Skips files that are already there.
URLs are pinned to a commit so everyone gets the same bytes.
"""
import sys
import urllib.request
from pathlib import Path

from f2f import config

# public mirror of the CCHAIN tables we need (CC BY 4.0); swap for the official Kaggle files once #1 lands
_CCHAIN = "https://raw.githubusercontent.com/jairo3224/Leptospiros_Case_Estimation/eae8992e9070c24b5f21d5469bd9a5f8b9ecab43/data/"
_FAELDON = ("https://raw.githubusercontent.com/faeldon/philippines-json-maps/8eeead560246863c8c820c31ca6fbca81a279477/"
            "2023/geojson/municities/medres/bgysubmuns-municity-1380900000.0.01.json")

SOURCES = {
    "cchain/location.csv": _CCHAIN + "location.csv",
    "cchain/project_noah_hazards.csv": _CCHAIN + "project_noah_hazards.csv",
    "cchain/google_open_buildings.csv": _CCHAIN + "google_open_buildings.csv",
    "boundaries/navotas_brgy.geojson": _FAELDON,  # MIT, PSA/NAMRIA 2023 boundaries, 18 barangays
    # HOT OSM export, ODbL; refreshed upstream, so this one isn't pinned
    "osm/hotosm_phl_health_facilities.zip":
        "https://production-raw-data-api.s3.amazonaws.com/ISO3/PHL/health_facilities/hotosm_phl_health_facilities_osm_geojson.zip",
}


def fetch(raw: Path, force: bool = False) -> list[Path]:
    got = []
    for rel, url in SOURCES.items():
        dest = Path(raw) / rel
        if dest.exists() and not force:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
        got.append(dest)
    return got


if __name__ == "__main__":
    raw = Path(config.load()["paths"]["raw"])
    for p in fetch(raw, force="--force" in sys.argv):
        print(f"fetched {p}")
    print(f"static layers in {raw}")
