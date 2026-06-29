#!/usr/bin/env python3
"""CLI leaderboard: compare bird species diversity across towns/villages.

Usage:
    python leaderboard.py --file towns.txt
    python leaderboard.py --file towns.txt --back 14
    python leaderboard.py "Skibbereen, Ireland" "Bantry, Ireland"
"""
from __future__ import annotations

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

import core.nominatim as nominatim
import core.ebird as ebird
from core.geo_utils import bbox_centroid, bbox_radius_km


def lookup_town(name: str, back_days: int) -> dict:
    place = nominatim.search_place(name)
    if place is None:
        return {"town": name, "display_name": name, "species_count": None, "error": "not found"}

    bbox = place["bbox"]
    center_lat, center_lon = bbox_centroid(bbox)
    radius_km = bbox_radius_km(bbox)

    try:
        observations = ebird.get_observations_in_area(center_lat, center_lon, radius_km, back_days=back_days)
        count, _ = ebird.count_unique_species(observations, bbox)
        return {"town": name, "display_name": place["display_name"], "species_count": count}
    except RuntimeError as exc:
        return {"town": name, "display_name": place["display_name"], "species_count": None, "error": str(exc)}


def build_leaderboard(towns: list[str], back_days: int) -> list[dict]:
    results = []
    total = len(towns)
    for i, town in enumerate(towns, 1):
        town = town.strip()
        if not town:
            continue
        print(f"  [{i}/{total}] {town}…", end=" ", flush=True)
        row = lookup_town(town, back_days)
        if row.get("error"):
            print(f"ERROR: {row['error']}")
        else:
            print(f"{row['species_count']} species")
        results.append(row)

    results.sort(key=lambda r: (r["species_count"] is None, -(r["species_count"] or 0)))
    for rank, row in enumerate(results, 1):
        row["rank"] = rank
    return results


def print_table(results: list[dict], back_days: int) -> None:
    col_rank = 4
    col_town = max(len(r.get("display_name", r["town"]) or r["town"]) for r in results) + 2
    col_town = max(col_town, 8)
    col_count = 10

    header = f"{'#':<{col_rank}}{'Location':<{col_town}}{'Species':>{col_count}}"
    separator = "-" * len(header)

    print(f"\nBird Species Leaderboard — last {back_days} day{'s' if back_days != 1 else ''}")
    print(separator)
    print(header)
    print(separator)

    for row in results:
        display = row.get("display_name") or row["town"]
        if row.get("error"):
            count_col = f"({row['error']})"
        else:
            count_col = str(row["species_count"])
        print(f"{row['rank']:<{col_rank}}{display:<{col_town}}{count_col:>{col_count}}")

    print(separator)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank towns by bird species diversity using eBird.")
    parser.add_argument("towns", nargs="*", help="Town/village names to compare")
    parser.add_argument("--file", "-f", help="Path to a text file with one town per line")
    parser.add_argument("--back", "-b", type=int, default=30, help="Days back to search (1–30, default 30)")
    args = parser.parse_args(argv)

    towns: list[str] = list(args.towns)
    if args.file:
        try:
            with open(args.file) as fh:
                towns.extend(line.strip() for line in fh if line.strip())
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1

    towns = [t for t in towns if t]
    if not towns:
        parser.print_help()
        return 1

    back_days = max(1, min(30, args.back))
    print(f"Looking up {len(towns)} location(s) (back={back_days} days)…\n")
    results = build_leaderboard(towns, back_days)
    print_table(results, back_days)
    return 0


if __name__ == "__main__":
    sys.exit(main())
