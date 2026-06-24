---
title: "Django Backend Structure"
type: entity
summary: "Fully implemented Django DRF backend for route and ELD log generation."
tags: [backend, django, drf, python, implementation]
date: 2026-06-23
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/notes/backend-implementation-details.md
  - raw/notes/backend-codebase-update.md
  - raw/notes/hos-engine-implementation.md
  - raw/notes/eld-generator-implementation.md
  - raw/notes/geocoding-routing-implementation.md
  - raw/notes/deployment-progress-update.md
---

# Django Backend Structure

## Current State (Fully Implemented)

The `spotter-bed/` directory contains a fully implemented Django 6.0.6 + DRF 3.17.1 backend:

```
spotter-bed/
├── vercel.json              # @vercel/python WSGI build config
├── .vercelignore            # Excludes venv/, tests/, __pycache__/
├── requirements.txt         # Django 6.0.6, DRF 3.17.1, cors-headers 4.9.0
├── .python-version          # 3.12
├── Pipfile                  # django, djangorestframework, django-cors-headers
├── venv/                    # Python 3.12 virtual environment
└── backend/
    ├── manage.py
    ├── backend/             # Django project config
    │   ├── settings.py      # DRF, CORS (localhost:5173), spotter_eld registered, env-driven config
    │   ├── urls.py          # Includes spotter_eld.urls
    │   └── wsgi.py          # sys.path hack for Vercel module resolution
    └── spotter_eld/          # Django app (fully implemented)
        ├── types.py         # Data classes (82 lines)
        ├── hos_engine.py    # HOS algorithm engine (387 lines)
        ├── eld_generator.py # ELD log partitioning (176 lines)
        ├── geocoding.py     # Geocoding + OSRM routing (135 lines)
        ├── views.py         # HealthView + TripGenerateView (131 lines)
        ├── serializers.py   # TripInputSerializer (8 lines)
        ├── utils.py         # Rounding, formatting, interpolation (35 lines)
        ├── urls.py          # API routes: /api/health/, /api/trips/generate/, root endpoint
        └── tests/           # 7 test files, 114 tests
```

## API Endpoints

### `GET /api/health/`
Returns `{"status": "ok"}`. No authentication.

### `POST /api/trips/generate/`
Accepts: `{ current_location, pickup_location, dropoff_location, current_cycle_used_hrs }`

Returns full trip result with:
- Geocoded locations (current, pickup, dropoff)
- Route legs with distance/duration
- Route geometry (GeoJSON coordinates for map)
- Chronological itinerary with all stops/breaks/resets
- Daily log sheets with timeline blocks, totals, remarks

## Dependencies

- Python 3.12 (Vercel runtime)
- Django 6.0.6
- djangorestframework 3.17.1
- django-cors-headers 4.9.0

## Deployment Configuration

### Settings (`backend/backend/settings.py`)

Key configuration decisions for Vercel:
- **Env-driven**: `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `SECRET_KEY`, `DEBUG` all read from environment variables with sensible defaults
- **Stateless DB**: `DATABASES = {}` when `VERCEL` env is present (read-only on serverless); SQLite for local dev
- **CORS defaults**: `http://localhost:5173` (Vite) and `http://127.0.0.1:3000`
- **Installed apps**: Minimal set — `rest_framework`, `corsheaders`, `spotter_eld`, plus `django.contrib.contenttypes` and `django.contrib.auth` (restored after initial removal attempt)
- **WSGI**: `backend.wsgi.application`

### WSGI (`backend/backend/wsgi.py`)

Modified for Vercel deployment:
- Inserts `backend/` parent directory into `sys.path` before importing Django
- Necessary because Vercel runs the WSGI app from a different working directory

### URL Structure (`backend/spotter_eld/urls.py`)

Three routes:
- `""` → `api_root` — JSON service metadata (status, available endpoints)
- `"api/health/"` → `HealthView`
- `"api/trips/generate/"` → `TripGenerateView`

## Test Suite

114 tests across 7 files — all passing:
- `test_hos_engine.py` — 15 HOS rule tests
- `test_eld_generation.py` — 10 partitioning tests
- `test_geocoding.py` — 19 geocoding/routing tests
- `test_serializers.py` — 9 input validation tests
- `test_utils.py` — 29 utility function tests
- `test_views.py` — 13 API endpoint tests
- `test_integration.py` — 17 end-to-end flow tests

## Outstanding Gaps

- No Docker configuration (spec requirement)
- No production database strategy for serverless mode

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — business logic implemented in hos_engine.py
- [[project-architecture|Project Architecture]] — overall system design
- [[api-specification|API Specification]] — endpoint details
- [[deployment-progress-update|Deployment Progress Update]] — full commit analysis
