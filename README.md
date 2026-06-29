# Bird Diversity Ranking

A web application that compares bird species diversity across towns and villages using real observation data from [eBird](https://ebird.org) and location boundaries from [OpenStreetMap](https://www.openstreetmap.org).

## Features

- **Location search** — type any town or village name, see its boundary drawn on a live map
- **Species count** — fetches all eBird observations within the boundary and counts unique species
- **Leaderboard** — compare multiple locations side by side, ranked by species richness
- **CLI leaderboard** — run batch comparisons from the terminal using a plain text file

## Architecture

```
Vercel (Next.js frontend)
  └── calls → Render (Flask REST API)
               ├── Nominatim (OpenStreetMap geocoding)
               └── eBird API v2 (species observations)
```

All services used are **free**. No database required.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, CSS Modules |
| Backend | Python 3, Flask, flask-cors |
| Map | Leaflet.js + OpenStreetMap tiles |
| Geocoding | Nominatim API (OpenStreetMap) |
| Bird data | eBird API v2 (Cornell Lab of Ornithology) |
| Frontend hosting | Vercel |
| Backend hosting | Render |
| Frontend tests | Jest, React Testing Library |
| Backend tests | pytest, pytest-cov |
| CI | GitHub Actions |

## Project Structure

```
DiversityRankingProject/
├── app.py                    # Flask API server
├── leaderboard.py            # CLI leaderboard script
├── towns.txt                 # Example towns for CLI script
├── core/
│   ├── nominatim.py          # OpenStreetMap geocoding client
│   ├── ebird.py              # eBird API client
│   └── geo_utils.py          # Bounding box / centroid utilities
├── tests/
│   ├── unit/                 # Unit tests (geo_utils, nominatim, ebird)
│   └── integration/          # Integration tests (Flask routes, CLI)
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   └── components/       # React components
│   └── __tests__/            # Jest component tests
├── .github/workflows/ci.yml  # GitHub Actions CI
├── render.yaml               # Render deployment config
└── requirements.txt
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- A free [eBird API key](https://ebird.org/api/keygen)

## Local Development

### Backend (Flask)

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env and add your eBird API key

# Run the API server
flask run
# API available at http://localhost:5000
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# .env.local already points to http://localhost:5000

# Run the dev server
npm run dev
# App available at http://localhost:3000
```

### CLI Leaderboard

```bash
# Compare towns from a file
python leaderboard.py --file towns.txt

# Compare towns from command line arguments
python leaderboard.py "Skibbereen, Ireland" "Bantry, Ireland" "Kinsale, Ireland"

# Specify how many days back to search (1–30, default 30)
python leaderboard.py --file towns.txt --back 14
```

Example output:

```
Bird Species Leaderboard — last 30 days
--------------------------------------------------------------
#   Location                                         Species
--------------------------------------------------------------
1   Kinsale, County Cork, Munster, Ireland                40
2   Clonakilty, County Cork, Munster, Ireland             13
3   Bantry, County Cork, Munster, Ireland                 10
4   Skibbereen, County Cork, Munster, Ireland              9
5   Schull, County Cork, Munster, Ireland                  5
--------------------------------------------------------------
```

## API Reference

All endpoints are served by the Flask backend.

### `GET /api/search?q=<town>`

Geocodes a town name using OpenStreetMap Nominatim.

**Response:**
```json
{
  "display_name": "Skibbereen, County Cork, Munster, Ireland",
  "bbox": [51.534, 51.558, -9.285, -9.252],
  "center_lat": 51.546,
  "center_lon": -9.269
}
```

### `GET /api/species?q=<town>&back=<days>`

Returns unique bird species recorded within a town's boundary.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | required | Town or village name |
| `back` | integer | 30 | Days back to search (1–30) |

**Response:**
```json
{
  "town": "Skibbereen, County Cork, Munster, Ireland",
  "species_count": 9,
  "species_list": [
    { "speciesCode": "mallard", "comName": "Mallard", "sciName": "Anas platyrhynchos" }
  ],
  "back_days": 30
}
```

### `POST /api/leaderboard`

Ranks a list of towns by species count.

**Request body:**
```json
{ "towns": ["Skibbereen, Ireland", "Bantry, Ireland"], "back": 30 }
```

**Response:**
```json
{
  "leaderboard": [
    { "rank": 1, "town": "Bantry, Ireland", "display_name": "Bantry, County Cork", "species_count": 10 },
    { "rank": 2, "town": "Skibbereen, Ireland", "display_name": "Skibbereen, County Cork", "species_count": 9 }
  ],
  "back_days": 30
}
```

## Running Tests

### Backend

```bash
pytest
```

Coverage report is printed automatically. The suite requires ≥ 85% coverage to pass (currently ~97%).

### Frontend

```bash
cd frontend
npm test
```

### CI

GitHub Actions runs both test suites on every push and pull request to `main`. No real API keys are used — all external calls are mocked.

## Deployment

### Backend — Render

The `render.yaml` file configures automatic deployment. When connecting the repository in Render, set the `EBIRD_API_KEY` environment variable in the dashboard.

### Frontend — Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → import this repository
2. Set **Root Directory** to `frontend`
3. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL
4. Deploy

## Data Sources & Attribution

- Location boundaries: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (via Nominatim)
- Bird observation data: [eBird](https://ebird.org), Cornell Lab of Ornithology
- Map tiles: © OpenStreetMap contributors

## Colour Scheme

The UI uses the colour palette of the [National Biodiversity Data Centre Ireland](https://biodiversityireland.ie).
