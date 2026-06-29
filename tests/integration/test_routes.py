import json
from unittest.mock import patch
import pytest


SKIBBEREEN_PLACE = {
    "display_name": "Skibbereen, County Cork, Munster, Ireland",
    "bbox": [51.5356, 51.5756, -9.2995, -9.2195],
    "geojson": {"type": "Polygon", "coordinates": []},
}

SAMPLE_OBS = [
    {"speciesCode": "mallard", "comName": "Mallard", "sciName": "Anas platyrhynchos", "lat": 51.55, "lng": -9.26},
    {"speciesCode": "hoopoe", "comName": "Hoopoe", "sciName": "Upupa epops", "lat": 51.54, "lng": -9.27},
]


class TestCORS:
    def test_cors_header_present_on_api_response(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            res = client.get(
                "/api/search?q=Skibbereen",
                headers={"Origin": "http://localhost:3000"},
            )
        assert res.status_code == 200
        assert "Access-Control-Allow-Origin" in res.headers

    def test_cors_allows_vercel_origin(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            res = client.get(
                "/api/search?q=Skibbereen",
                headers={"Origin": "https://diversity-ranking-project.vercel.app"},
            )
        assert res.status_code == 200
        assert "Access-Control-Allow-Origin" in res.headers

    def test_cors_header_present_on_preflight(self, client):
        res = client.options(
            "/api/search",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.status_code in (200, 204)


class TestSearchRoute:
    def test_missing_q_returns_400(self, client):
        res = client.get("/api/search")
        assert res.status_code == 400
        data = res.get_json()
        assert "error" in data

    def test_empty_q_returns_400(self, client):
        res = client.get("/api/search?q=")
        assert res.status_code == 400

    def test_not_found_returns_404(self, client):
        with patch("app.nominatim.search_place", return_value=None):
            res = client.get("/api/search?q=NonExistentXYZVillage")
        assert res.status_code == 404
        data = res.get_json()
        assert "error" in data

    def test_happy_path_returns_expected_fields(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            res = client.get("/api/search?q=Skibbereen")
        assert res.status_code == 200
        data = res.get_json()
        assert "display_name" in data
        assert "bbox" in data
        assert "center_lat" in data
        assert "center_lon" in data

    def test_happy_path_centroid_inside_bbox(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            res = client.get("/api/search?q=Skibbereen")
        data = res.get_json()
        bbox = data["bbox"]
        assert bbox[0] < data["center_lat"] < bbox[1]
        assert bbox[2] < data["center_lon"] < bbox[3]


class TestSpeciesRoute:
    def test_missing_q_returns_400(self, client):
        res = client.get("/api/species")
        assert res.status_code == 400

    def test_invalid_back_returns_400(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            res = client.get("/api/species?q=Skibbereen&back=notanumber")
        assert res.status_code == 400

    def test_not_found_returns_404(self, client):
        with patch("app.nominatim.search_place", return_value=None):
            res = client.get("/api/species?q=NonExistent")
        assert res.status_code == 404

    def test_happy_path_returns_species_count(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("app.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                res = client.get("/api/species?q=Skibbereen&back=30")
        assert res.status_code == 200
        data = res.get_json()
        assert "species_count" in data
        assert "species_list" in data
        assert isinstance(data["species_count"], int)

    def test_ebird_error_returns_503(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("app.ebird.get_observations_in_area", side_effect=RuntimeError("API key invalid")):
                res = client.get("/api/species?q=Skibbereen")
        assert res.status_code == 503
        data = res.get_json()
        assert "error" in data

    def test_zero_species_for_empty_area(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("app.ebird.get_observations_in_area", return_value=[]):
                res = client.get("/api/species?q=Skibbereen")
        data = res.get_json()
        assert data["species_count"] == 0
        assert data["species_list"] == []


class TestLeaderboardRoute:
    def test_empty_towns_returns_400(self, client):
        res = client.post("/api/leaderboard", json={"towns": [], "back": 30})
        assert res.status_code == 400

    def test_missing_body_returns_400(self, client):
        res = client.post("/api/leaderboard", json={})
        assert res.status_code == 400

    def test_happy_path_returns_sorted_leaderboard(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("app.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                res = client.post("/api/leaderboard", json={"towns": ["Skibbereen", "Bantry"], "back": 30})

        assert res.status_code == 200
        data = res.get_json()
        assert "leaderboard" in data
        assert len(data["leaderboard"]) == 2
        assert data["leaderboard"][0]["rank"] == 1

    def test_not_found_town_included_with_error(self, client):
        def fake_place(name):
            return None if name == "GhostTown" else SKIBBEREEN_PLACE

        with patch("app.nominatim.search_place", side_effect=fake_place):
            with patch("app.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                res = client.post("/api/leaderboard", json={"towns": ["Skibbereen", "GhostTown"], "back": 30})

        data = res.get_json()
        errors = [r for r in data["leaderboard"] if r.get("error")]
        assert len(errors) == 1
        assert errors[0]["town"] == "GhostTown"

    def test_leaderboard_sorted_descending_by_count(self, client):
        with patch("app.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("app.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                res = client.post("/api/leaderboard", json={"towns": ["TownA", "TownB"], "back": 30})

        data = res.get_json()
        counts = [r["species_count"] for r in data["leaderboard"] if r.get("species_count") is not None]
        assert counts == sorted(counts, reverse=True)
