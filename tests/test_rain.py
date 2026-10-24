import numpy as np
import pytest

from f2f.ingest.rain import area_mean, pixel_weights

# two 0.05 deg pixels side by side, centres at x = 0.025 and 0.075
X, Y = np.array([0.025, 0.075]), np.array([0.025])


def square(x0, x1, y0=0.0, y1=0.05):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def test_weights_follow_area_share():
    # 0.03 deg in the left pixel, 0.01 in the right -> 3:1
    w = pixel_weights(X, Y, square(0.02, 0.06))
    assert w.sum() == pytest.approx(1)
    assert w[0] == pytest.approx([0.75, 0.25], abs=0.03)


def test_multipolygon_and_feature_collection():
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": square(0.01, 0.02)},
        {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [square(0.06, 0.09)["coordinates"]]}}]}
    assert pixel_weights(X, Y, fc)[0] == pytest.approx([0.25, 0.75], abs=0.03)


def test_masked_pixel_dropped_and_weights_renormalised():
    w = np.array([[0.75, 0.25]])
    prcp = np.array([[[10.0, 50.0]],       # both valid: 0.75*10 + 0.25*50
                     [[np.nan, 50.0]],     # sea pixel missing: the land pixel carries all the weight
                     [[np.nan, np.nan]]])  # nothing valid
    out = area_mean(prcp, w)
    assert out[:2] == pytest.approx([20.0, 50.0])
    assert np.isnan(out[2])


def test_polygon_outside_pixels_raises():
    with pytest.raises(ValueError):
        pixel_weights(X, Y, square(0.02, 0.2))
