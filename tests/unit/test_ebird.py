import os
from unittest.mock import MagicMock, patch
import pytest
import requests

import core.ebird as ebird_module

BBOX = [51.5356, 51.5756, -9.2995, -9.2195]


def _mock_response(data, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    if status_code == 401:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    elif status_code >= 400:
        mock.raise_for_status.side_effect = requests.HTTPError(response=mock)
    else:
        mock.raise_for_status.return_value = None
    return mock


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "test-key-123")


class TestGetObservationsInArea:
    def test_happy_path_returns_list(self, ebird_fixture):
        with patch("core.ebird.requests.get", return_value=_mock_response(ebird_fixture)):
            result = ebird_module.get_observations_in_area(51.55, -9.26, 5.0)
        assert isinstance(result, list)
        assert len(result) == len(ebird_fixture)

    def test_returns_dicts_with_expected_keys(self, ebird_fixture):
        with patch("core.ebird.requests.get", return_value=_mock_response(ebird_fixture)):
            result = ebird_module.get_observations_in_area(51.55, -9.26, 5.0)
        for obs in result:
            assert "speciesCode" in obs
            assert "comName" in obs

    def test_empty_response_returns_empty_list(self):
        with patch("core.ebird.requests.get", return_value=_mock_response([])):
            result = ebird_module.get_observations_in_area(51.55, -9.26, 5.0)
        assert result == []

    def test_auth_error_raises_runtime_error(self):
        with patch("core.ebird.requests.get", return_value=_mock_response({}, status_code=401)):
            with pytest.raises(RuntimeError, match="401"):
                ebird_module.get_observations_in_area(51.55, -9.26, 5.0)

    def test_radius_capped_at_50km(self, ebird_fixture):
        with patch("core.ebird.requests.get", return_value=_mock_response(ebird_fixture)) as mock_get:
            ebird_module.get_observations_in_area(51.55, -9.26, 200.0)
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["dist"] == 50

    def test_back_days_capped_at_30(self, ebird_fixture):
        with patch("core.ebird.requests.get", return_value=_mock_response(ebird_fixture)) as mock_get:
            ebird_module.get_observations_in_area(51.55, -9.26, 5.0, back_days=60)
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["back"] == 30

    def test_api_key_sent_in_header(self, ebird_fixture):
        with patch("core.ebird.requests.get", return_value=_mock_response(ebird_fixture)) as mock_get:
            ebird_module.get_observations_in_area(51.55, -9.26, 5.0)
        _, kwargs = mock_get.call_args
        assert kwargs["headers"]["X-eBirdApiToken"] == "test-key-123"

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("EBIRD_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="EBIRD_API_KEY"):
            ebird_module.get_observations_in_area(51.55, -9.26, 5.0)

    def test_429_retries_and_succeeds(self, ebird_fixture):
        rate_limited = _mock_response({}, status_code=429)
        success = _mock_response(ebird_fixture)
        with patch("core.ebird.requests.get", side_effect=[rate_limited, success]):
            with patch("core.ebird.time.sleep") as mock_sleep:
                result = ebird_module.get_observations_in_area(51.55, -9.26, 5.0)
        assert result == ebird_fixture
        mock_sleep.assert_called_once_with(1)  # 2**0 = 1 s on first retry

    def test_429_three_times_raises_runtime_error(self):
        rate_limited = _mock_response({}, status_code=429)
        with patch("core.ebird.requests.get", return_value=rate_limited):
            with patch("core.ebird.time.sleep"):
                with pytest.raises(RuntimeError, match="429"):
                    ebird_module.get_observations_in_area(51.55, -9.26, 5.0)


class TestCountUniqueSpecies:
    def test_deduplicates_species(self, ebird_fixture):
        # gyrfal appears twice in fixture but should count once
        count, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        codes = [s["speciesCode"] for s in species]
        assert codes.count("gyrfal") == 1

    def test_filters_out_of_bbox(self, ebird_fixture):
        # outsid1 at (99, 99) should be excluded
        _, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        codes = [s["speciesCode"] for s in species]
        assert "outsid1" not in codes

    def test_filters_missing_coords(self, ebird_fixture):
        # nolatlng has no lat/lng and should be excluded
        _, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        codes = [s["speciesCode"] for s in species]
        assert "nolatlng" not in codes

    def test_count_matches_species_list_length(self, ebird_fixture):
        count, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        assert count == len(species)

    def test_species_sorted_alphabetically(self, ebird_fixture):
        _, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        names = [s["comName"] for s in species]
        assert names == sorted(names)

    def test_empty_observations_returns_zero(self):
        count, species = ebird_module.count_unique_species([], BBOX)
        assert count == 0
        assert species == []

    def test_all_outside_bbox_returns_zero(self):
        obs = [{"speciesCode": "test1", "comName": "Test Bird", "sciName": "Testus birdus", "lat": 99.0, "lng": 99.0}]
        count, species = ebird_module.count_unique_species(obs, BBOX)
        assert count == 0

    def test_species_list_contains_required_fields(self, ebird_fixture):
        _, species = ebird_module.count_unique_species(ebird_fixture, BBOX)
        for s in species:
            assert "speciesCode" in s
            assert "comName" in s
            assert "sciName" in s
