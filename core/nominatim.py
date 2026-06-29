from __future__ import annotations

import time
import requests

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "BirdDiversityRanking/1.0 (mccallionmark@hotmail.co.uk)"
_cache: dict[str, dict | None] = {}
_last_call_time: float = 0.0


def search_place(name: str) -> dict | None:
    """Return place info for *name* or None if not found.

    Result dict:
        display_name  str
        bbox          [min_lat, max_lat, min_lon, max_lon]  (floats)
        geojson       GeoJSON geometry dict (Polygon/MultiPolygon) or None
    """
    key = name.strip().lower()
    if key in _cache:
        return _cache[key]

    _rate_limit()

    params = {
        "q": name,
        "format": "jsonv2",
        "polygon_geojson": "1",
        "limit": "1",
    }
    response = requests.get(_NOMINATIM_URL, params=params, headers={"User-Agent": _USER_AGENT}, timeout=10)
    response.raise_for_status()

    results = response.json()
    if not results:
        _cache[key] = None
        return None

    hit = results[0]
    raw_bbox = hit["boundingbox"]  # [min_lat_str, max_lat_str, min_lon_str, max_lon_str]
    bbox = [float(raw_bbox[0]), float(raw_bbox[1]), float(raw_bbox[2]), float(raw_bbox[3])]

    result = {
        "display_name": hit["display_name"],
        "bbox": bbox,
        "geojson": hit.get("geojson"),
    }
    _cache[key] = result
    return result


def clear_cache() -> None:
    _cache.clear()


def _rate_limit() -> None:
    global _last_call_time
    elapsed = time.monotonic() - _last_call_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_call_time = time.monotonic()
