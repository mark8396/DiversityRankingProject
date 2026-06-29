# DiversityRankingProject — Claude Context

## What this project is
A bird species diversity ranking web application. Users search for a town or village, see its boundary on a map, and get a count of unique bird species recorded there using eBird data. A leaderboard compares multiple locations side by side. There is also a CLI script for batch comparisons.

## Architecture
Two separate deployed services:

```
Vercel (Next.js frontend)  →  Render (Flask REST API)
                                ├── Nominatim (OpenStreetMap geocoding, free, no key)
                                └── eBird API v2 (bird data, free key required)
```

- **Frontend**: `frontend/` — Next.js 15, TypeScript, CSS Modules, Leaflet map
- **Backend**: project root — Python Flask, API-only (no HTML rendering)
- **CLI**: `leaderboard.py` — standalone script, shares core/ modules with Flask

## Live URLs
- Frontend (Vercel): https://diversity-ranking-project.vercel.app
- Backend (Render): https://bird-diversity-ranking.onrender.com

## Tech stack
| Layer | Tech |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, CSS Modules |
| Backend | Python 3.9+, Flask 3.1, flask-cors |
| Map | Leaflet.js + OpenStreetMap tiles (CDN) |
| Frontend tests | Jest 29, React Testing Library 16 |
| Backend tests | pytest, pytest-cov (≥85% coverage enforced) |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |
| Frontend deploy | Vercel (root directory: `frontend`) |
| Backend deploy | Render (`render.yaml` config present) |

## Key files
```
app.py                        Flask API server (3 routes: /api/search, /api/species, /api/leaderboard)
leaderboard.py                CLI script: python leaderboard.py --file towns.txt --back 30
towns.txt                     Example input for CLI leaderboard
core/nominatim.py             Nominatim geocoding client (1 req/sec rate limit, in-memory cache)
core/ebird.py                 eBird API client (center+radius query, bbox filter)
core/geo_utils.py             Pure math: centroid, enclosing radius, point-in-bbox
frontend/src/app/page.tsx     Search page
frontend/src/app/leaderboard/ Leaderboard page
frontend/src/components/      Navbar, Footer, Map, SpeciesResult, LeaderboardTable
frontend/__tests__/           Jest component tests (26 tests)
tests/                        pytest suite (70 tests, 97% coverage)
```

## Environment variables
| Variable | Where | Purpose |
|---|---|---|
| `EBIRD_API_KEY` | Backend `.env` / Render dashboard | eBird API authentication |
| `NEXT_PUBLIC_API_URL` | Frontend `.env.local` / Vercel dashboard | Points Next.js at the Flask API |

Local `.env` already contains the real eBird API key. Never commit `.env`.

## Running locally
```bash
# Backend (from project root)
source .venv/bin/activate
flask run                         # http://localhost:5000

# Frontend (from frontend/)
npm run dev                       # http://localhost:3000

# CLI leaderboard
python leaderboard.py --file towns.txt --back 30
```

## Running tests
```bash
# Backend (from project root)
pytest                            # 70 tests, coverage report printed

# Frontend (from frontend/)
npm test                          # 26 Jest component tests
```

## Commit conventions
- **Small, focused commits** — one logical change per commit (one component, one module, one test file)
- User reviews each commit before the next one builds on it
- Always run tests before committing

## Key design decisions
- eBird has no bounding-box query — uses center+radius (max 50 km), then filters results to the Nominatim bounding box in Python
- Species metric: unique species recorded in the last N days (1–30, default 30)
- No database — in-process dict cache for Nominatim results
- No shapely — simple bbox filter is accurate enough for village-scale queries
- CORS on Flask allows `localhost:3000` and `*.vercel.app` origins

## GitHub
Repository: https://github.com/mark8396/DiversityRankingProject
CI runs on every push/PR to `main` — requires both pytest and Jest to pass.
