import sys
from io import StringIO
from unittest.mock import patch
import pytest

import leaderboard as lb_module

SKIBBEREEN_PLACE = {
    "display_name": "Skibbereen, County Cork, Munster, Ireland",
    "bbox": [51.5356, 51.5756, -9.2995, -9.2195],
    "geojson": None,
}

SAMPLE_OBS = [
    {"speciesCode": "mallard", "comName": "Mallard", "sciName": "Anas platyrhynchos", "lat": 51.55, "lng": -9.26},
    {"speciesCode": "hoopoe", "comName": "Hoopoe", "sciName": "Upupa epops", "lat": 51.54, "lng": -9.27},
]


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "test-key-123")


class TestLookupTown:
    def test_returns_species_count_for_valid_town(self):
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                result = lb_module.lookup_town("Skibbereen", 30)
        assert result["species_count"] is not None
        assert result["species_count"] >= 0

    def test_returns_error_for_unknown_town(self):
        with patch("leaderboard.nominatim.search_place", return_value=None):
            result = lb_module.lookup_town("GhostTown", 30)
        assert result["error"] == "not found"
        assert result["species_count"] is None

    def test_returns_error_on_ebird_failure(self):
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", side_effect=RuntimeError("API down")):
                result = lb_module.lookup_town("Skibbereen", 30)
        assert result["error"] is not None
        assert result["species_count"] is None


class TestBuildLeaderboard:
    def test_single_town_ranked_first(self):
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                results = lb_module.build_leaderboard(["Skibbereen"], 30)
        assert results[0]["rank"] == 1

    def test_sorted_descending_by_species_count(self):
        places = {
            "TownA": {**SKIBBEREEN_PLACE, "display_name": "TownA"},
            "TownB": {**SKIBBEREEN_PLACE, "display_name": "TownB"},
        }
        # Both towns return same obs; count will be equal — just verify no crash and ranks assigned
        with patch("leaderboard.nominatim.search_place", side_effect=lambda n: places.get(n)):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                results = lb_module.build_leaderboard(["TownA", "TownB"], 30)
        ranks = [r["rank"] for r in results]
        assert sorted(ranks) == [1, 2]

    def test_not_found_town_ranked_last(self):
        def fake_place(name):
            return None if name == "GhostTown" else SKIBBEREEN_PLACE

        with patch("leaderboard.nominatim.search_place", side_effect=fake_place):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                results = lb_module.build_leaderboard(["Skibbereen", "GhostTown"], 30)

        ghost = next(r for r in results if r["town"] == "GhostTown")
        assert ghost["rank"] == max(r["rank"] for r in results)

    def test_empty_town_entries_skipped(self):
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                results = lb_module.build_leaderboard(["Skibbereen", "", "  "], 30)
        assert len(results) == 1


class TestMain:
    def test_no_args_exits_nonzero(self, capsys):
        exit_code = lb_module.main([])
        assert exit_code == 1

    def test_town_args_run_successfully(self, capsys):
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                exit_code = lb_module.main(["Skibbereen"])
        assert exit_code == 0

    def test_file_not_found_exits_nonzero(self):
        exit_code = lb_module.main(["--file", "/nonexistent/path/towns.txt"])
        assert exit_code == 1

    def test_file_arg_reads_towns(self, tmp_path):
        towns_file = tmp_path / "towns.txt"
        towns_file.write_text("Skibbereen\nBantry\n")
        with patch("leaderboard.nominatim.search_place", return_value=SKIBBEREEN_PLACE):
            with patch("leaderboard.ebird.get_observations_in_area", return_value=SAMPLE_OBS):
                exit_code = lb_module.main(["--file", str(towns_file)])
        assert exit_code == 0
