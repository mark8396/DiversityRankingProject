"""
One-time script to pre-populate the nominatim_cache DB table with the 60
fixed Irish leaderboard towns so that leaderboard refreshes are fast from
the very first run.

Usage (requires DATABASE_URL and EBIRD_API_KEY in .env or environment):
    python seed_nominatim.py

Takes ~60 s on first run (Nominatim 1 req/sec rate limit). Safe to re-run —
already-cached towns are skipped via the L1 in-memory cache and the DB
ON CONFLICT upsert.
"""

from __future__ import annotations

import sys
from dotenv import load_dotenv

load_dotenv()

import core.db as db
import core.nominatim as nominatim

TOWNS = [
    "Dublin", "Belfast", "Cork", "Limerick", "Galway", "Derry",
    "Newtownabbey", "Bangor, Northern Ireland", "Waterford", "Lisburn", "Drogheda",
    "Dundalk", "Swords", "Navan, Ireland", "Bray, Wicklow", "Ballymena", "Newtownards",
    "Lurgan", "Carrickfergus", "Ennis", "Newry", "Carlow", "Kilkenny",
    "Naas", "Tralee", "Antrim, Northern Ireland", "Coleraine", "Newbridge", "Balbriggan",
    "Portlaoise", "Athlone", "Mullingar", "Letterkenny", "Greystones",
    "Wexford", "Portadown", "Sligo", "Celbridge", "Omagh", "Larne",
    "Malahide", "Clonmel", "Carrigaline", "Banbridge", "Maynooth",
    "Leixlip", "Armagh", "Dungannon", "Ashbourne, Meath", "Laytown",
    "Tullamore", "Killarney", "Cobh", "Enniskillen", "Midleton",
    "Strabane", "Mallow", "Arklow", "Castlebar", "Wicklow",
]


def main() -> None:
    print(f"Seeding nominatim_cache for {len(TOWNS)} towns…\n")

    try:
        db.init_nominatim_cache()
    except Exception as exc:
        print(f"ERROR: could not initialise DB table: {exc}", file=sys.stderr)
        sys.exit(1)

    ok = 0
    failed = []

    for i, town in enumerate(TOWNS, 1):
        try:
            place = nominatim.search_place(town)
            if place is None:
                print(f"  [{i:2}/{len(TOWNS)}] NOT FOUND  {town}")
                failed.append(town)
            else:
                print(f"  [{i:2}/{len(TOWNS)}] OK         {town}  →  {place['display_name']}")
                ok += 1
        except Exception as exc:
            print(f"  [{i:2}/{len(TOWNS)}] ERROR      {town}  →  {exc}", file=sys.stderr)
            failed.append(town)

    print(f"\nDone. {ok} cached, {len(failed)} failed.")
    if failed:
        print("Failed towns:", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
