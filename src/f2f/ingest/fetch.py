"""python -m f2f.ingest.fetch

Downloads every raw input that has a public URL into data/raw/. Skips files already there;
--force re-downloads. About 260 MB, most of it the CCHAIN climate table.
"""
import sys
import urllib.request
from pathlib import Path

from f2f import config

# Project CCHAIN on HDX (Thinking Machines, CC BY 4.0). Resource ids are stable across HDX re-uploads.
_HDX = "https://data.humdata.org/dataset/5b580664-365e-4d7e-b5e5-2990df8f12a5/resource/{}/download/{}"
_CCHAIN = {
    "disease_pidsr_totals.csv": "b93c1427-797a-40a4-b99e-872e152d1c86",
    "disease_lgu_disaggregated_totals.csv": "1f10c8ee-37a9-40b6-a18a-e8fbe4bb7173",
    "climate_atmosphere_downscaled.csv": "a070a35e-5b75-44de-a1b2-08bc7aa2ff07",
    "worldpop_population.csv": "53b885f1-c90c-4f79-b618-8af9530366aa",
    "location.csv": "31a3dddb-decc-4fd7-a0f7-acff922a7a76",
    "project_noah_hazards.csv": "b767e99d-8044-4ebb-a68a-0803a8a15c2b",
    "google_open_buildings.csv": "107da350-6d50-48cd-b001-d5dcdfaafee7",
    "geoportal_doh_poi_health.csv": "3ca89d0e-3671-4f63-8dff-9af3e05b93cc",
    "mapbox_health_facility_brgy_isochrones.csv": "d8b70ecf-d796-4d0e-a028-04c83904e905",
}
_FAELDON = ("https://raw.githubusercontent.com/faeldon/philippines-json-maps/8eeead560246863c8c820c31ca6fbca81a279477/"
            "2023/geojson/municities/medres/bgysubmuns-municity-1380900000.0.01.json")

SOURCES = {
    **{f"cchain/{name}": _HDX.format(rid, name) for name, rid in _CCHAIN.items()},
    "boundaries/navotas_brgy.geojson": _FAELDON,  # MIT, PSA/NAMRIA 2023 boundaries, 18 barangays
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
    print(f"raw inputs in {raw}")
