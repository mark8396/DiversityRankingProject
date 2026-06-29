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
