from __future__ import annotations

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

import core.nominatim as nominatim
import core.ebird as ebird
from core.geo_utils import bbox_centroid, bbox_radius_km

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://*.vercel.app"])


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


@app.route("/api/leaderboard", methods=["POST"])
def api_leaderboard():
    body = request.get_json(silent=True) or {}
    towns = body.get("towns", [])
    if not towns:
        return jsonify({"error": "'towns' list must not be empty"}), 400

    back = int(body.get("back", 30))
    results = []

    for town in towns:
        town = town.strip()
        if not town:
            continue
        place = nominatim.search_place(town)
        if place is None:
            results.append({"town": town, "display_name": town, "species_count": None, "error": "not found"})
            continue

        bbox = place["bbox"]
        center_lat, center_lon = bbox_centroid(bbox)
        radius_km = bbox_radius_km(bbox)

        try:
            observations = ebird.get_observations_in_area(center_lat, center_lon, radius_km, back_days=back)
            count, _ = ebird.count_unique_species(observations, bbox)
            results.append({"town": town, "display_name": place["display_name"], "species_count": count})
        except RuntimeError as exc:
            results.append({"town": town, "display_name": place["display_name"], "species_count": None, "error": str(exc)})

    results.sort(key=lambda r: (r["species_count"] is None, -(r["species_count"] or 0)))
    for i, row in enumerate(results, 1):
        row["rank"] = i

    return jsonify({"leaderboard": results, "back_days": back})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
