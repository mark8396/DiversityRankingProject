import json
import os
import pathlib
import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture()
def nominatim_fixture() -> list[dict]:
    return json.loads((FIXTURES_DIR / "nominatim_response.json").read_text())


@pytest.fixture()
def ebird_fixture() -> list[dict]:
    return json.loads((FIXTURES_DIR / "ebird_response.json").read_text())


@pytest.fixture()
def skibbereen_place() -> dict:
    return {
        "display_name": "Skibbereen, County Cork, Munster, Ireland",
        "bbox": [51.5356, 51.5756, -9.2995, -9.2195],
        "geojson": {"type": "Polygon", "coordinates": []},
    }


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("EBIRD_API_KEY", "test-key-123")
    import app as flask_app
    flask_app.app.config["TESTING"] = True
    return flask_app.app


@pytest.fixture()
def client(app):
    return app.test_client()
