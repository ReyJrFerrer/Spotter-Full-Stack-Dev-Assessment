---
title: "API Specification"
type: reference
summary: "API endpoints for the Spotter Assessment — currently Express-based, with Django DRF endpoint planned."
tags: [api, endpoint, rest, drf, express]
date: 2026-06-22
confidence: medium
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/notes/project-codebase-state.md
---

# API Specification

## Current API (Express)

### `POST /api/generate-trip`

**Request body:**
```json
{
  "currentLocation": "Los Angeles, CA",
  "pickupLocation": "Las Vegas, NV",
  "dropoffLocation": "Salt Lake City, UT",
  "currentCycleUsed": 15.5,
  "carrierName": "Swift Logistical Transit Group",
  "tractorNumber": "TRK-9801C",
  "trailerNumber": "TRL-552A",
  "startTime": "2026-06-22T08:00:00.000Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current": { "label": "...", "city": "...", "state": "...", "lat": 0, "lng": 0 },
    "pickup": { ... },
    "dropoff": { ... },
    "legs": [{ "from": ..., "to": ..., "distanceMiles": 270, "durationHours": 4.5 }],
    "totalDistanceMiles": 670,
    "totalDurationHours": 11.25,
    "itinerary": [ ... ],
    "dailyLogs": [ ... ],
    "usingGemini": true
  }
}
```

### `GET /api/health`

Returns `{ "status": "ok", "using_gemini": true|false }`

## Planned API (Django DRF)

Per [[backend-specifications|Backend Specifications]]:

### `POST /api/trips/generate/`

**Request:** `{ current_location, pickup_location, dropoff_location, current_cycle_used_hrs }`

**Response:** route map coords, scheduled stops array, daily log sheet data objects

## Data Types

See TypeScript type definitions in `spotter-fed/src/types.ts` for the type definitions used in the frontend/Express API.

### Key Types

- `DutyStatus`: Enum (OFF, SB, D, ON)
- `GeocodedLocation`: label, city, state, lat, lng
- `RouteLeg`: from, to, distanceMiles, durationHours
- `ItineraryItem`: status, activityName, locationName, startTime, endTime, durationHours, distanceMiles, coordinates, remarks
- `DailyLogSheet`: dateString, dateLabel, totalMilesDriven, timeline[], totals{}, remarks[]
- `TripGenerationResult`: complete response with locations, legs, itinerary, logs

## Cross-References

- [[trip-routing-engine|Trip Routing Engine]] — the algorithm called by the API
- [[backend-django|Django Backend Structure]] — planned backend implementation
- [[project-architecture|Project Architecture]] — how the API fits in the system
