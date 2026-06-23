---
title: "Backend Implementation Details"
type: source
summary: "Complete backend file map, data types, views, serializers, utilities, and test suite"
tags: [backend, django, drf, implementation, structure]
date: 2026-06-23
confidence: high
source: manual codebase audit
---

# Backend Implementation Details

**Project:** `spotter-bed/`

## File Map

| File | Lines | Purpose |
|---|---|---|
| `backend/settings.py` | 128 | Django 6.0.6 config, DRF, CORS (localhost:3000) |
| `backend/urls.py` | 23 | Root URL routing |
| `spotter_eld/types.py` | 82 | Data classes: DutyStatus, GeocodedLocation, RouteLeg, ItineraryItem, DailyLogSheet, TripGenerationResult |
| `spotter_eld/hos_engine.py` | 387 | Core HOS algorithm (iterative scheduler) |
| `spotter_eld/eld_generator.py` | 176 | Daily log partitioning |
| `spotter_eld/geocoding.py` | 135 | Geocoding + OSRM routing |
| `spotter_eld/views.py` | 131 | DRF API views: HealthView (GET), TripGenerateView (POST) |
| `spotter_eld/serializers.py` | 8 | TripInputSerializer (4 fields) |
| `spotter_eld/utils.py` | 35 | Round-to-quarter-hour, time/date formatting, coordinate interpolation |
| `spotter_eld/urls.py` | 8 | App URL routes: `/api/health/`, `/api/trips/generate/` |

## Data Types (`types.py`)

- `DutyStatus` — constants: OFF, SB, D, ON
- `GeocodedLocation` — label, city, state, lat, lng
- `RouteLeg` — two GeocodedLocations + distance_miles, duration_hours
- `ItineraryItem` — id, status, activity, location, times, duration, distance, coords, remarks
- `TimelineBlock` — status, start_hour, end_hour, location, remarks
- `DailyLogRemarks` — time_label, status, location, remarks_text
- `DailyLogSheet` — date, miles, truck/trailer/carrier, timeline, totals, remarks
- `TripGenerationResult` — full result with all locations, legs, itinerary, logs

## Views (`views.py`)

### `HealthView` (GET `/api/health/`)
- Returns `{"status": "ok"}`
- No auth required

### `TripGenerateView` (POST `/api/trips/generate/`)
1. Validates input via `TripInputSerializer`
2. Geocodes all 3 locations → returns 400 if any fails
3. Calls OSRM for route (optional — falls back to Euclidean estimates)
4. Calls `simulate_trip()` with external legs
5. Serializes result to JSON with route geometry

## Tests (`tests/`)

| File | Tests | Scope |
|---|---|---|
| `test_hos_engine.py` | 15 | HOS rules, breaks, resets, itinerary ordering, remarks |
| `test_eld_generation.py` | 10 | Daily log partitioning, totals, gap filling, metadata |
| `test_geocoding.py` | 19 | Location parsing, city DB, Nominatim, OSRM |
| `test_serializers.py` | 9 | Input validation, boundaries, missing fields |
| `test_utils.py` | 29 | Rounding, formatting, interpolation |
| `test_views.py` | 13 | Health, trip generation, response structure, CORS |
| `test_integration.py` | 17 | End-to-end engine and API flows |
| **Total** | **114** | All passing |

## Dependencies

- Python 3.14
- Django 6.0.6
- djangorestframework 3.17.1
- django-cors-headers 4.9.0
