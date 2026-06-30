from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import core.db as db


def make_mock_conn(fetchone_return=None):
    """Build a mock psycopg2 connection with a cursor context manager."""
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = fetchone_return
    mock_cur.__enter__ = lambda s: s
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


class TestGetConnection:
    def test_raises_when_no_env_var(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            db.get_connection()

    def test_calls_psycopg2_connect(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://test")
        with patch("psycopg2.connect") as mock_connect:
            db.get_connection()
        mock_connect.assert_called_once_with("postgresql://test")


class TestLoadCache:
    def test_returns_none_when_no_row(self, monkeypatch):
        mock_conn, _ = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            result = db.load_cache(30)
        assert result is None

    def test_returns_dict_when_row_exists(self, monkeypatch):
        rows = [{"rank": 1, "town": "Dublin", "species_count": 50}]
        updated_at = datetime(2026, 6, 30, 12, 0, 0)
        mock_conn, _ = make_mock_conn(fetchone_return=(rows, updated_at))
        with patch("core.db.get_connection", return_value=mock_conn):
            result = db.load_cache(30)
        assert result is not None
        assert result["back_days"] == 30
        assert result["leaderboard"] == rows
        assert result["updated_at"] == "2026-06-30T12:00:00"

    def test_closes_connection_on_success(self):
        mock_conn, _ = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            db.load_cache(7)
        mock_conn.close.assert_called_once()

    def test_closes_connection_on_error(self):
        mock_conn, mock_cur = make_mock_conn()
        mock_cur.execute.side_effect = Exception("DB error")
        with patch("core.db.get_connection", return_value=mock_conn):
            with pytest.raises(Exception, match="DB error"):
                db.load_cache(7)
        mock_conn.close.assert_called_once()

    def test_queries_correct_back_days(self):
        mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            db.load_cache(14)
        mock_cur.execute.assert_called_once()
        call_args = mock_cur.execute.call_args
        assert call_args[0][1] == (14,)


class TestSaveCache:
    def test_executes_upsert(self):
        mock_conn, mock_cur = make_mock_conn()
        rows = [{"rank": 1, "town": "Cork", "species_count": 42}]
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_cache(7, rows)
        mock_cur.execute.assert_called_once()
        call_args = mock_cur.execute.call_args[0]
        assert "INSERT INTO leaderboard_cache" in call_args[0]
        assert "ON CONFLICT" in call_args[0]
        assert call_args[1][0] == 7
        assert json.loads(call_args[1][1]) == rows

    def test_commits_transaction(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_cache(30, [])
        mock_conn.commit.assert_called_once()

    def test_closes_connection(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_cache(30, [])
        mock_conn.close.assert_called_once()


class TestNominatimCache:
    # --- init_nominatim_cache ---

    def test_init_creates_table(self):
        mock_conn, mock_cur = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.init_nominatim_cache()
        sql = mock_cur.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS nominatim_cache" in sql

    def test_init_commits(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.init_nominatim_cache()
        mock_conn.commit.assert_called_once()

    def test_init_closes_connection(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.init_nominatim_cache()
        mock_conn.close.assert_called_once()

    # --- load_place ---

    def test_load_place_returns_none_on_miss(self):
        mock_conn, _ = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            result = db.load_place("skibbereen")
        assert result is None

    def test_load_place_returns_dict_when_found(self):
        place = {"display_name": "Skibbereen", "bbox": [51.5, 51.6, -9.3, -9.2], "geojson": None}
        mock_conn, _ = make_mock_conn(fetchone_return=(json.dumps(place),))
        with patch("core.db.get_connection", return_value=mock_conn):
            result = db.load_place("skibbereen")
        assert result == place

    def test_load_place_queries_with_correct_key(self):
        mock_conn, mock_cur = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            db.load_place("dublin")
        call_args = mock_cur.execute.call_args[0]
        assert call_args[1] == ("dublin",)

    def test_load_place_closes_connection_on_success(self):
        mock_conn, _ = make_mock_conn(fetchone_return=None)
        with patch("core.db.get_connection", return_value=mock_conn):
            db.load_place("cork")
        mock_conn.close.assert_called_once()

    def test_load_place_closes_connection_on_error(self):
        mock_conn, mock_cur = make_mock_conn()
        mock_cur.execute.side_effect = Exception("DB error")
        with patch("core.db.get_connection", return_value=mock_conn):
            with pytest.raises(Exception, match="DB error"):
                db.load_place("galway")
        mock_conn.close.assert_called_once()

    # --- save_place ---

    def test_save_place_executes_upsert(self):
        mock_conn, mock_cur = make_mock_conn()
        place = {"display_name": "Dublin", "bbox": [53.2, 53.4, -6.4, -6.1], "geojson": None}
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_place("dublin", place)
        sql = mock_cur.execute.call_args[0][0]
        assert "INSERT INTO nominatim_cache" in sql
        assert "ON CONFLICT (name_key) DO UPDATE" in sql

    def test_save_place_serialises_place_as_json(self):
        mock_conn, mock_cur = make_mock_conn()
        place = {"display_name": "Limerick", "bbox": [52.6, 52.7, -8.7, -8.5], "geojson": None}
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_place("limerick", place)
        params = mock_cur.execute.call_args[0][1]
        assert params[0] == "limerick"
        assert json.loads(params[1]) == place

    def test_save_place_commits(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_place("galway", {"display_name": "Galway", "bbox": [], "geojson": None})
        mock_conn.commit.assert_called_once()

    def test_save_place_closes_connection(self):
        mock_conn, _ = make_mock_conn()
        with patch("core.db.get_connection", return_value=mock_conn):
            db.save_place("galway", {"display_name": "Galway", "bbox": [], "geojson": None})
        mock_conn.close.assert_called_once()
