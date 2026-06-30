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
