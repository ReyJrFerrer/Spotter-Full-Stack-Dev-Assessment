---
title: "Trip Routing Engine"
type: concept
summary: "Core algorithm (Python) that processes trip inputs, geocodes locations, calculates route legs, and schedules stops per FMCSA constraints."
tags: [routing, algorithm, geocoding, itinerary, scheduling, hos-engine]
date: 2026-06-23
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/notes/hos-engine-implementation.md
  - raw/notes/geocoding-routing-implementation.md
  - raw/notes/backend-implementation-details.md
---

# Trip Routing Engine

The trip routing engine (`hos_engine.py`) is the core computational component that transforms raw trip inputs into a fully scheduled, HOS-compliant itinerary.

## Input Processing

Accepts four required inputs:
1. **Current location**
2. **Pickup location**
3. **Dropoff location**
4. **Current cycle hours used** (0–70)

Plus optional metadata: carrier name, tractor/trailer numbers, **start time (ISO 8601)**, **trip IANA timezone** (e.g. `America/Los_Angeles`), and external OSRM route legs. When the start time and timezone are omitted, the engine uses the current UTC time and the `UTC` timezone.

## Geocoding Pipeline

Locations are resolved to coordinates via a two-tier system in `geocoding.py`:

1. **City Database** (primary): 14 major US cities with hardcoded lat/lng — case-insensitive lookup
2. **Nominatim API** (fallback): OpenStreetMap geocoding for cities not in the database

For routing, the engine uses **OSRM** (Open Source Routing Machine) to get:
- Distance in miles per leg
- Estimated driving time (quarter-hour rounded)
- GeoJSON LineString route geometry for map rendering

If OSRM is unavailable, the engine falls back to Euclidean distance estimation (55 miles/degree, minimum 20 miles, 60 mph average speed).

## Route Legs

The trip is divided into two legs:
- **Leg 1**: Current → Pickup (deadhead or initial leg)
- **Leg 2**: Pickup → Dropoff (loaded leg)

## Trip Flow

```
Pre-Trip (0.25h ON)
  → Leg 1: Current → Pickup (iterative HOS scheduling)
  → Pickup (1h ON) [with 14h window check before]
  → Leg 2: Pickup → Dropoff (iterative HOS scheduling)
  → Dropoff (1h ON) [with 14h window check before]
  → Partition into daily logs
```

## HOS Scheduling Loop (simulate_leg)

The iterative scheduler for each leg:

1. Check 70-hour cycle limit → trigger 34-hour reset
2. Check 14-hour window or 11-hour limit → trigger 10-hour reset
3. Check 8-hour continuous driving → trigger 30-minute break
4. Check 1,000-mile fueling threshold → trigger fueling stop
5. Determine max driving segment: `min(2h, remaining_driving, remaining_duty, remaining_break_time)`
6. Drive the segment, update accumulators
7. Repeat until leg distance is consumed

## DriverState Tracker

| Field | Purpose | Reset By |
|---|---|---|
| `accum_driving_today` | Cumulative driving hours | 10h reset, 34h restart |
| `elapsed_duty_window_today` | Time since coming on duty | 10h reset, 34h restart |
| `continuous_driving_since_break` | Driving since last 30-min break | 30-min break, 10h reset |
| `total_cycle_hours_used` | Sum of D+ON hours (input + trip) | 34h restart only |
| `miles_since_fueling` | Miles since last fueling | Fueling stop, 34h restart |

## Itinerary Items

Each scheduling event produces an `ItineraryItem` with:
- Status, activity name, location
- Start/end times (ISO format, always UTC, tzinfo-aware)
- Duration, distance, coordinates
- Remarks string

The accompanying `TripGenerationResult` carries a `timezone` field (IANA) that downstream consumers (including `eld_generator.partition_into_daily_logs()`) use to render local-clock displays and to split days at local midnight.

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — the constraints enforced during scheduling
- [[eld-log-generation|ELD Log Data Generation]] — how the itinerary is partitioned into daily logs
- [[api-specification|API Specification]] — the endpoint that triggers routing
- [[backend-django|Django Backend Structure]] — entity page for the backend
- [[timezone-aware-scheduling|Timezone-Aware Trip Scheduling]] — frontend + backend timezone flow
