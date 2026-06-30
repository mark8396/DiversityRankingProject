from __future__ import annotations

import time
import requests
import core.db as db

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

    Cache hierarchy:
        L1 — in-memory dict (zero I/O, lost on process restart)
        L2 — PostgreSQL nominatim_cache (survives Render restarts)
        L3 — Nominatim API (rate-limited at 1 req/sec)
    """
    key = name.strip().lower()

    # L1: in-memory cache
    if key in _cache:
        return _cache[key]

    # L2: PostgreSQL cache (survives restarts; skipped gracefully if DB is down)
    try:
        place = db.load_place(key)
        if place is not None:
            _cache[key] = place
            return place
    except Exception:
        pass

    # L3: Nominatim API
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

    # Persist to DB so future cold starts skip the API call.
    # None results are not persisted — the 60 leaderboard towns all exist.
    try:
        db.save_place(key, result)
    except Exception:
        pass

    return result


def clear_cache() -> None:
    _cache.clear()


def _rate_limit() -> None:
    global _last_call_time
    elapsed = time.monotonic() - _last_call_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_call_time = time.monotonic()
