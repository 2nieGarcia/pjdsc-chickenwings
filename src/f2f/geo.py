"""Just enough geometry for 18 small polygons, so we don't need geopandas at runtime."""
import math

R_KM = 6371.0088


def _ring_area_centroid(ring, lat0):
    """Shoelace on an equirectangular projection around lat0. Returns (area_km2, lon, lat)."""
    kx = R_KM * math.cos(math.radians(lat0)) * math.pi / 180
    ky = R_KM * math.pi / 180
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        cross = (x0 * kx) * (y1 * ky) - (x1 * kx) * (y0 * ky)
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a /= 2
    return abs(a), cx / (6 * a), cy / (6 * a)


def area_centroid(geometry: dict) -> tuple[float, float, float]:
    """GeoJSON Polygon/MultiPolygon -> (area_km2, lon, lat), outer rings only.

    shortcut: holes ignored; fine for Navotas barangays, wrong for anything with large holes.
    """
    polys = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    lat0 = polys[0][0][0][1]
    parts = [_ring_area_centroid([tuple(p[:2]) for p in poly[0]], lat0) for poly in polys]
    total = sum(a for a, _, _ in parts)
    return (total,
            sum(a * x for a, x, _ in parts) / total,
            sum(a * y for a, _, y in parts) / total)


def haversine_km(lon1, lat1, lon2, lat2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R_KM * math.asin(math.sqrt(h))
