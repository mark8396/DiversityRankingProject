import math
import pytest
from core.geo_utils import bbox_centroid, bbox_radius_km, point_in_bbox

# Skibbereen bounding box: [min_lat, max_lat, min_lon, max_lon]
BBOX = [51.5356, 51.5756, -9.2995, -9.2195]


class TestBboxCentroid:
    def test_returns_midpoint_lat(self):
        lat, _ = bbox_centroid(BBOX)
        assert lat == pytest.approx((51.5356 + 51.5756) / 2)

    def test_returns_midpoint_lon(self):
        _, lon = bbox_centroid(BBOX)
        assert lon == pytest.approx((-9.2995 + -9.2195) / 2)

    def test_centroid_inside_bbox(self):
        lat, lon = bbox_centroid(BBOX)
        assert BBOX[0] < lat < BBOX[1]
        assert BBOX[2] < lon < BBOX[3]

    def test_square_bbox(self):
        lat, lon = bbox_centroid([0.0, 2.0, 0.0, 2.0])
        assert lat == pytest.approx(1.0)
        assert lon == pytest.approx(1.0)


class TestBboxRadiusKm:
    def test_returns_positive_float(self):
        radius = bbox_radius_km(BBOX)
        assert radius > 0

    def test_radius_covers_half_diagonal(self):
        radius = bbox_radius_km(BBOX)
        # Minimum side of bbox in km should be less than the full radius
        import math
        R = 6371.0
        dlat = math.radians(BBOX[1] - BBOX[0])
        lat_km = R * dlat
        assert radius >= lat_km / 2

    def test_larger_bbox_gives_larger_radius(self):
        small = bbox_radius_km([51.0, 51.1, -9.0, -8.9])
        large = bbox_radius_km([51.0, 52.0, -9.0, -8.0])
        assert large > small

    def test_tiny_bbox_nonzero(self):
        radius = bbox_radius_km([51.0, 51.001, -9.0, -8.999])
        assert radius > 0


class TestPointInBbox:
    def test_point_inside_returns_true(self):
        assert point_in_bbox(51.55, -9.26, BBOX) is True

    def test_point_outside_lat_returns_false(self):
        assert point_in_bbox(52.0, -9.26, BBOX) is False

    def test_point_outside_lon_returns_false(self):
        assert point_in_bbox(51.55, -10.0, BBOX) is False

    def test_point_on_min_lat_boundary_returns_false(self):
        assert point_in_bbox(BBOX[0], -9.26, BBOX) is False

    def test_point_on_max_lat_boundary_returns_false(self):
        assert point_in_bbox(BBOX[1], -9.26, BBOX) is False

    def test_point_on_min_lon_boundary_returns_false(self):
        assert point_in_bbox(51.55, BBOX[2], BBOX) is False

    def test_point_on_max_lon_boundary_returns_false(self):
        assert point_in_bbox(51.55, BBOX[3], BBOX) is False

    def test_far_away_point_returns_false(self):
        assert point_in_bbox(99.0, 99.0, BBOX) is False
