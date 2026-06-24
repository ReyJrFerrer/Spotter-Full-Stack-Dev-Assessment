---
title: "API Specification"
type: reference
summary: "API endpoints for the Spotter Assessment — Django DRF backend with health and trip generation endpoints."
tags: [api, endpoint, rest, drf, django]
date: 2026-06-23
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/notes/backend-implementation-details.md
  - raw/notes/backend-codebase-update.md
---

# API Specification

## Production API (Django DRF)

### `GET /api/health/`

**Response:**
```json
{ "status": "ok" }
```

### `GET /api/locations/autocomplete/?q=los`

**Response:**
```json
[
  {"label": "Los Angeles, CA", "city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437},
  {"label": "Los Gatos, CA", "city": "Los Gatos", "state": "CA", "lat": 37.2266, "lng": -121.9747}
]
```

Returns up to 10 US city suggestions from Nominatim search (filtered to `countrycodes=us` and place types: city, town, village, hamlet, municipality, county). Results are TTL-cached (5 min) on the backend to respect Nominatim's 1 req/sec rate limit. Requires minimum 2 characters in `q`.

### `POST /api/trips/generate/`

**Request body:**
```json
{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Las Vegas, NV",
  "dropoff_location": "Salt Lake City, UT",
  "current_cycle_used_hrs": 15.5
}
```

All 4 fields are required. `current_cycle_used_hrs` must be a float between 0.0 and 70.0 (inclusive).

**Response:**
```json
{
  "route_geometry": [[34.05, -118.24], [36.17, -115.14], [40.76, -111.89]],
  "current": { "label": "...", "city": "...", "state": "...", "lat": 34.05, "lng": -118.24 },
  "pickup": { ... },
  "dropoff": { ... },
  "legs": [
    {
      "from_location": { ... },
      "to_location": { ... },
      "distance_miles": 270,
      "duration_hours": 4.5
    }
  ],
  "total_distance_miles": 690,
  "total_duration_hours": 11.75,
  "itinerary": [
    {
      "id": "item-1",
      "status": "ON",
      "activity_name": "Pre-Trip Inspection",
      "location_name": "Los Angeles, CA",
      "start_time": "2026-06-22T08:00:00+00:00",
      "end_time": "2026-06-22T08:15:00+00:00",
      "duration_hours": 0.25,
      "distance_miles": 0,
      "coordinates": [34.0522, -118.2437],
      "remarks": "15-min Post/Pre-Trip Commercial Vehicle Inspection"
    }
  ],
  "daily_logs": [
    {
      "date_string": "2026-06-22",
      "date_label": "Monday, Jun 22, 2026",
      "total_miles_driven": 450,
      "tractor_number": "",
      "trailer_number": "",
      "carrier_name": "",
      "timeline": [
        { "status": "OFF", "start_hour": 0.0, "end_hour": 8.0, "location_name": "...", "remarks": "Off Duty" },
        { "status": "ON", "start_hour": 8.0, "end_hour": 8.25, "location_name": "...", "remarks": "..." },
        { "status": "D", "start_hour": 8.25, "end_hour": 10.25, "location_name": "...", "remarks": "..." }
      ],
      "totals": { "OFF": 10.5, "SB": 0.0, "D": 10.0, "ON": 3.5 },
      "remarks": [
        { "time_label": "8:00 AM", "status": "ON", "location": "Los Angeles, CA", "remarks_text": "..." }
      ]
    }
  ]
}
```

## Frontend Integration

The frontend (`spotter-fed/`) calls this endpoint directly via Vite proxy. The `apiTransform.ts` utility converts snake_case response fields to camelCase (e.g. `route_geometry` → `routeCoordinates`, `activity_name` → `activityName`) for use in React components.

## Data Types

| Type | Fields | Defined In |
|---|---|---|
| `GeocodedLocation` | label, city, state, lat, lng | `types.py` |
| `RouteLeg` | from_location, to_location, distance_miles, duration_hours | `types.py` |
| `ItineraryItem` | id, status, activity_name, location_name, start_time, end_time, duration_hours, distance_miles, coordinates, remarks | `types.py` |
| `DailyLogSheet` | date_string, date_label, total_miles_driven, tractor_number, trailer_number, carrier_name, timeline[], totals{}, remarks[] | `types.py` |

## Cross-References

- [[trip-routing-engine|Trip Routing Engine]] — the algorithm called by the API
- [[backend-django|Django Backend Structure]] — backend implementation details
- [[project-architecture|Project Architecture]] — how the API fits in the system
