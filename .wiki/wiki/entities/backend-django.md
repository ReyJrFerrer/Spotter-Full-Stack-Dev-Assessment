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
---

# Django Backend Structure

## Current State (Fully Implemented)

The `spotter-bed/` directory contains a fully implemented Django 6.0.6 + DRF 3.17.1 backend:

```
spotter-bed/
├── Pipfile              # django, djangorestframework, django-cors-headers
├── venv/                # Python 3.14 virtual environment
└── backend/
    ├── manage.py
    ├── backend/         # Django project config
    │   ├── settings.py  # DRF, CORS (localhost:3000), spotter_eld registered
    │   ├── urls.py      # Includes spotter_eld.urls
    │   └── wsgi.py / asgi.py
    └── spotter_eld/      # Django app (fully implemented)
        ├── types.py         # Data classes (82 lines)
        ├── hos_engine.py    # HOS algorithm engine (387 lines)
        ├── eld_generator.py # ELD log partitioning (176 lines)
        ├── geocoding.py     # Geocoding + OSRM routing (135 lines)
        ├── views.py         # HealthView + TripGenerateView (131 lines)
        ├── serializers.py   # TripInputSerializer (8 lines)
        ├── utils.py         # Rounding, formatting, interpolation (35 lines)
        ├── urls.py          # API routes: /api/health/, /api/trips/generate/
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

- Python 3.14
- Django 6.0.6
- djangorestframework 3.17.1
- django-cors-headers 4.9.0

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
- No tests for 14hr window / 11hr limit enforcement
- No fueling stop injection test for 1000+ mile trips

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — business logic implemented in hos_engine.py
- [[project-architecture|Project Architecture]] — overall system design
- [[api-specification|API Specification]] — endpoint details
