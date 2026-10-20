"""CHIRPS daily rainfall over the Navotas polygon, via Earth Engine (needs EE_PROJECT)."""
import pandas as pd


def chirps_daily(start: str, end: str, city_geojson: dict) -> pd.DataFrame:
    """Area-weighted mean rain in mm per day -> columns date, rain_mm.

    The 0.05 deg pixels on the coast cover Manila Bay; weight by area inside the city polygon.
    """
    raise NotImplementedError
