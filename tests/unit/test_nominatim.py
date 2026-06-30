from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
import pytest
import requests

import core.nominatim as nominatim_module


@pytest.fixture(autouse=True)
def clear_cache():
    nominatim_module.clear_cache()
    yield
    nominatim_module.clear_cache()


@pytest.fixture(autouse=True)
def mock_nominatim_db():
    """Prevent real DB calls in all nominatim unit tests.

    load_place returns None (L2 miss) so every test falls through to L3 (the
    mocked API) exactly as before this cache layer was added.
    """
    with patch("core.nominatim.db.load_place", return_value=None), \
         patch("core.nominatim.db.save_place"):
        yield


def _mock_response(data: list | dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    if status_code >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    else:
        mock.raise_for_status.return_value = None
    return mock


class TestSearchPlace:
    def test_happy_path_returns_display_name(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)) as mock_get:
            with patch("core.nominatim.time.sleep"):
                result = nominatim_module.search_place("Skibbereen")
        assert result is not None
        assert result["display_name"] == nominatim_fixture[0]["display_name"]

    def test_happy_path_returns_float_bbox(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)):
            with patch("core.nominatim.time.sleep"):
                result = nominatim_module.search_place("Skibbereen")
        assert isinstance(result["bbox"], list)
        assert all(isinstance(v, float) for v in result["bbox"])
        assert len(result["bbox"]) == 4

    def test_happy_path_returns_geojson(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)):
            with patch("core.nominatim.time.sleep"):
                result = nominatim_module.search_place("Skibbereen")
        assert result["geojson"] is not None
        assert result["geojson"]["type"] == "Polygon"

    def test_no_results_returns_none(self):
        with patch("core.nominatim.requests.get", return_value=_mock_response([])):
            with patch("core.nominatim.time.sleep"):
                result = nominatim_module.search_place("NonExistentXYZVillage")
        assert result is None

    def test_http_error_raises(self):
        with patch("core.nominatim.requests.get", return_value=_mock_response({}, status_code=500)):
            with patch("core.nominatim.time.sleep"):
                with pytest.raises(requests.HTTPError):
                    nominatim_module.search_place("Skibbereen")

    def test_cache_prevents_second_http_call(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)) as mock_get:
            with patch("core.nominatim.time.sleep"):
                nominatim_module.search_place("Skibbereen")
                nominatim_module.search_place("Skibbereen")
        assert mock_get.call_count == 1

    def test_cache_is_case_insensitive(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)) as mock_get:
            with patch("core.nominatim.time.sleep"):
                nominatim_module.search_place("skibbereen")
                nominatim_module.search_place("SKIBBEREEN")
        assert mock_get.call_count == 1

    def test_none_result_is_cached(self):
        with patch("core.nominatim.requests.get", return_value=_mock_response([])) as mock_get:
            with patch("core.nominatim.time.sleep"):
                nominatim_module.search_place("NonExistent")
                nominatim_module.search_place("NonExistent")
        assert mock_get.call_count == 1

    def test_user_agent_header_is_set(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)) as mock_get:
            with patch("core.nominatim.time.sleep"):
                nominatim_module.search_place("Skibbereen")
        _, kwargs = mock_get.call_args
        assert "User-Agent" in kwargs["headers"]
        assert kwargs["headers"]["User-Agent"]


class TestSearchPlaceDBCache:
    def test_l2_hit_returns_cached_result_without_api_call(self, nominatim_fixture):
        place = {"display_name": "Skibbereen", "bbox": [51.5, 51.6, -9.3, -9.2], "geojson": None}
        with patch("core.nominatim.db.load_place", return_value=place), \
             patch("core.nominatim.requests.get") as mock_get:
            result = nominatim_module.search_place("Skibbereen")
        assert result == place
        mock_get.assert_not_called()

    def test_l2_hit_populates_l1_so_second_call_skips_both(self, nominatim_fixture):
        place = {"display_name": "Skibbereen", "bbox": [51.5, 51.6, -9.3, -9.2], "geojson": None}
        with patch("core.nominatim.db.load_place", return_value=place) as mock_load, \
             patch("core.nominatim.requests.get") as mock_get:
            nominatim_module.search_place("Skibbereen")
            nominatim_module.search_place("Skibbereen")
        mock_get.assert_not_called()
        mock_load.assert_called_once()  # only on first call; L1 hit on second

    def test_l1_hit_skips_db_lookup(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)), \
             patch("core.nominatim.time.sleep"), \
             patch("core.nominatim.db.load_place", return_value=None) as mock_load, \
             patch("core.nominatim.db.save_place"):
            nominatim_module.search_place("Skibbereen")  # populates L1
            nominatim_module.search_place("Skibbereen")  # L1 hit
        mock_load.assert_called_once()  # only on the first call

    def test_l3_success_saves_place_to_db(self, nominatim_fixture):
        with patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)), \
             patch("core.nominatim.time.sleep"), \
             patch("core.nominatim.db.load_place", return_value=None), \
             patch("core.nominatim.db.save_place") as mock_save:
            result = nominatim_module.search_place("Skibbereen")
        mock_save.assert_called_once()
        saved_key, saved_place = mock_save.call_args[0]
        assert saved_key == "skibbereen"
        assert saved_place == result

    def test_l3_none_result_does_not_save_to_db(self):
        with patch("core.nominatim.requests.get", return_value=_mock_response([])), \
             patch("core.nominatim.time.sleep"), \
             patch("core.nominatim.db.load_place", return_value=None), \
             patch("core.nominatim.db.save_place") as mock_save:
            nominatim_module.search_place("NonExistent")
        mock_save.assert_not_called()

    def test_db_load_error_falls_through_to_api(self, nominatim_fixture):
        with patch("core.nominatim.db.load_place", side_effect=Exception("DB down")), \
             patch("core.nominatim.db.save_place"), \
             patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)) as mock_get, \
             patch("core.nominatim.time.sleep"):
            result = nominatim_module.search_place("Skibbereen")
        mock_get.assert_called_once()
        assert result is not None

    def test_db_save_error_is_nonfatal(self, nominatim_fixture):
        with patch("core.nominatim.db.load_place", return_value=None), \
             patch("core.nominatim.db.save_place", side_effect=Exception("DB down")), \
             patch("core.nominatim.requests.get", return_value=_mock_response(nominatim_fixture)), \
             patch("core.nominatim.time.sleep"):
            result = nominatim_module.search_place("Skibbereen")
        assert result is not None  # exception from save_place must not propagate
