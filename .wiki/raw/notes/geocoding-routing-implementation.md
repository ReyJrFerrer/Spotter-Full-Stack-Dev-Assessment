---
title: "Geocoding and Routing Implementation (geocoding.py)"
type: source
summary: "Geocoding via local city database + Nominatim fallback, routing via OSRM with GeoJSON route geometry"
tags: [geocoding, routing, osrm, nominatim, api-integration]
date: 2026-06-23
confidence: high
source: manual codebase audit
---

# Geocoding and Routing Implementation

**File:** `spotter-bed/backend/spotter_eld/geocoding.py` (135 lines)

## Overview

Two-tier geocoding system with optional OSRM routing integration. All external APIs are free and open-source.

## Geocoding Pipeline

### City Database (`CITY_DATABASE`, line 16-31)
- 14 major US cities with hardcoded lat/lng
- Cities: Los Angeles, Las Vegas, Salt Lake City, Bakersfield, Phoenix, Denver, Seattle, Portland, San Francisco, San Diego, Albuquerque, Houston, Dallas, Chicago
- Case-insensitive lookup via `.lower()`

### `geocode_location()` (line 77)
1. Parse "City, State" from input string
2. Look up lowercase city name in `CITY_DATABASE`
3. If found → return cached location
4. If not found → fall back to Nominatim API

### Nominatim API (line 50)
- `GET https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1&countrycodes=us`
- Custom User-Agent: `SpotterAssessment/1.0 (trucking-route-planner)`
- 10-second timeout
- Returns `None` on network failure or empty results

## Routing

### `osrm_route()` (line 92)
- `GET https://router.project-osrm.org/route/v1/driving/{lng,lat};{lng,lat};{lng,lat}?overview=full&geometries=geojson`
- Requires 2+ waypoints
- Returns `(List[RouteLeg], List[coordinate_pairs])` on success
- Returns `None` on error, `NoRoute` code, or network failure

### Route Leg Parsing (line 112-125)
- Converts meters → miles (÷ 1609.344), minimum 1 mile
- Converts seconds → hours, minimum 0.25h, quarter-hour rounded

### Route Geometry (line 127-131)
- Extracts GeoJSON LineString coordinates
- Reverses from (lng, lat) to (lat, lng) for frontend consumption
