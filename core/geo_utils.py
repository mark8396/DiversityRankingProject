from __future__ import annotations

import math


def bbox_centroid(bbox: list[float]) -> tuple[float, float]:
    """Return (lat, lon) midpoint of [min_lat, max_lat, min_lon, max_lon]."""
    min_lat, max_lat, min_lon, max_lon = bbox
    return (min_lat + max_lat) / 2, (min_lon + max_lon) / 2


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def bbox_radius_km(bbox: list[float]) -> float:
    """Return the radius (km) of the smallest circle enclosing the bounding box.

    Uses half the diagonal distance so an eBird radius query is guaranteed to
    cover every point inside the box.
    """
    min_lat, max_lat, min_lon, max_lon = bbox
    diagonal = _haversine_km(min_lat, min_lon, max_lat, max_lon)
    return diagonal / 2


def point_in_bbox(lat: float, lon: float, bbox: list[float]) -> bool:
    """Return True if (lat, lon) falls strictly inside the bounding box."""
    min_lat, max_lat, min_lon, max_lon = bbox
    return min_lat < lat < max_lat and min_lon < lon < max_lon
