from __future__ import annotations

import os
import requests
from core.geo_utils import point_in_bbox

_EBIRD_BASE = "https://api.ebird.org/v2"


def _api_key() -> str:
    key = os.environ.get("EBIRD_API_KEY", "")
    if not key:
        raise RuntimeError("EBIRD_API_KEY environment variable is not set")
    return key


def get_observations_in_area(
    lat: float,
    lon: float,
    radius_km: float,
    back_days: int = 30,
) -> list[dict]:
    """Return raw observation records from eBird near (lat, lon).

    Each record contains at minimum:
        speciesCode, comName, sciName, lat, lng, obsDt, subId
    """
    dist = min(int(round(radius_km)), 50)  # eBird caps at 50 km
    params = {
        "lat": lat,
        "lng": lon,
        "dist": dist,
        "back": min(back_days, 30),
        "maxResults": 10000,
        "detail": "full",
        "includeProvisional": "true",
    }
    headers = {"X-eBirdApiToken": _api_key()}
    response = requests.get(f"{_EBIRD_BASE}/data/obs/geo/recent", params=params, headers=headers, timeout=15)
    if response.status_code == 401:
        raise RuntimeError("eBird API key is invalid or expired (HTTP 401)")
    response.raise_for_status()
    return response.json()


def count_unique_species(observations: list[dict], bbox: list[float]) -> tuple[int, list[dict]]:
    """Filter *observations* to those inside *bbox* and return (count, species_list).

    species_list entries: {speciesCode, comName, sciName}
    """
    seen: set[str] = set()
    species: list[dict] = []
    for obs in observations:
        obs_lat = obs.get("lat")
        obs_lon = obs.get("lng")
        if obs_lat is None or obs_lon is None:
            continue
        if not point_in_bbox(obs_lat, obs_lon, bbox):
            continue
        code = obs.get("speciesCode", "")
        if code and code not in seen:
            seen.add(code)
            species.append({
                "speciesCode": code,
                "comName": obs.get("comName", ""),
                "sciName": obs.get("sciName", ""),
            })
    species.sort(key=lambda s: s["comName"])
    return len(species), species
