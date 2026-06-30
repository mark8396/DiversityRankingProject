from __future__ import annotations

import json
import os
from datetime import datetime

import psycopg2


def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(url)


def load_cache(back_days: int) -> dict | None:
    """Return cached leaderboard for the given back_days, or None if not cached."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT results, updated_at FROM leaderboard_cache WHERE back_days = %s",
                (back_days,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        results, updated_at = row
        return {
            "leaderboard": results,
            "back_days": back_days,
            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
        }
    finally:
        conn.close()


def save_cache(back_days: int, leaderboard_rows: list) -> None:
    """Upsert leaderboard results for the given back_days."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leaderboard_cache (back_days, results, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (back_days) DO UPDATE
                  SET results = EXCLUDED.results,
                      updated_at = EXCLUDED.updated_at
                """,
                (back_days, json.dumps(leaderboard_rows)),
            )
        conn.commit()
    finally:
        conn.close()


def init_nominatim_cache() -> None:
    """Create the nominatim_cache table if it does not already exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nominatim_cache (
                    name_key   TEXT      PRIMARY KEY,
                    place_data TEXT      NOT NULL,
                    cached_at  TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def load_place(name_key: str) -> dict | None:
    """Return the cached place dict for name_key, or None if not in DB."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT place_data FROM nominatim_cache WHERE name_key = %s",
                (name_key,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row[0])
    finally:
        conn.close()


def save_place(name_key: str, place: dict) -> None:
    """Upsert a geocoded place dict into the nominatim_cache table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO nominatim_cache (name_key, place_data, cached_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (name_key) DO UPDATE
                  SET place_data = EXCLUDED.place_data,
                      cached_at  = EXCLUDED.cached_at
                """,
                (name_key, json.dumps(place)),
            )
        conn.commit()
    finally:
        conn.close()
