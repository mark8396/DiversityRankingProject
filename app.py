from __future__ import annotations

import concurrent.futures
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

import core.nominatim as nominatim
import core.ebird as ebird
import core.db as db
from core.geo_utils import bbox_centroid, bbox_radius_km

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", r"https://.*\.vercel\.app"])

try:
    db.init_nominatim_cache()
except Exception:
    pass  # non-fatal: DATABASE_URL not set in test environments


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    place = nominatim.search_place(q)
    if place is None:
        return jsonify({"error": f"Place not found: {q}"}), 404

    center_lat, center_lon = bbox_centroid(place["bbox"])
    return jsonify({
        "display_name": place["display_name"],
        "bbox": place["bbox"],
        "center_lat": center_lat,
        "center_lon": center_lon,
    })


@app.route("/api/species")
def api_species():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        back = int(request.args.get("back", 30))
    except ValueError:
        return jsonify({"error": "'back' must be an integer (1–30)"}), 400

    place = nominatim.search_place(q)
    if place is None:
        return jsonify({"error": f"Place not found: {q}"}), 404

    bbox = place["bbox"]
    center_lat, center_lon = bbox_centroid(bbox)
    radius_km = bbox_radius_km(bbox)

    try:
        observations = ebird.get_observations_in_area(center_lat, center_lon, radius_km, back_days=back)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    count, species_list = ebird.count_unique_species(observations, bbox)
    return jsonify({
        "town": place["display_name"],
        "species_count": count,
        "species_list": species_list,
        "bbox": bbox,
        "back_days": back,
    })


@app.route("/api/leaderboard/cached")
def api_leaderboard_cached():
    try:
        back = int(request.args.get("back", 30))
    except ValueError:
        return jsonify({"error": "'back' must be an integer"}), 400

    try:
        cached = db.load_cache(back)
    except Exception:
        cached = None

    if cached is None:
        return jsonify({"leaderboard": [], "back_days": back, "updated_at": None})
    return jsonify(cached)


@app.route("/api/leaderboard", methods=["POST"])
def api_leaderboard():
    body = request.get_json(silent=True) or {}
    towns = body.get("towns", [])
    if not towns:
        return jsonify({"error": "'towns' list must not be empty"}), 400

    back = int(body.get("back", 30))

    # Phase 1 — geocode sequentially.
    # Nominatim's _rate_limit() mutates a module-level float (_last_call_time);
    # running it from multiple threads would race. With the DB cache warm, each
    # lookup is a fast DB read and the whole phase completes in under a second.
    geocoded = []
    for raw_town in towns:
        town = raw_town.strip()
        if not town:
            continue
        place = nominatim.search_place(town)
        geocoded.append({"town": town, "place": place})

    # Phase 2 — fetch eBird data in parallel.
    # Each worker is independent; no shared mutable state is accessed.
    def fetch_town(entry: dict) -> dict:
        town_name = entry["town"]
        place = entry["place"]
        if place is None:
            return {"town": town_name, "display_name": town_name, "species_count": None, "error": "not found"}
        bbox = place["bbox"]
        center_lat, center_lon = bbox_centroid(bbox)
        radius_km = bbox_radius_km(bbox)
        try:
            observations = ebird.get_observations_in_area(center_lat, center_lon, radius_km, back_days=back)
            count, _ = ebird.count_unique_species(observations, bbox)
            return {"town": town_name, "display_name": place["display_name"], "species_count": count}
        except RuntimeError as exc:
            return {"town": town_name, "display_name": place["display_name"], "species_count": None, "error": str(exc)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_town, geocoded))

    results.sort(key=lambda r: (r["species_count"] is None, -(r["species_count"] or 0)))
    for i, row in enumerate(results, 1):
        row["rank"] = i

    try:
        db.save_cache(back, results)
    except Exception:
        pass  # Cache write failure is non-fatal

    return jsonify({"leaderboard": results, "back_days": back})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
