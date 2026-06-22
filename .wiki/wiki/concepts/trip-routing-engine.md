---
title: "Trip Routing Engine"
type: concept
summary: "Core algorithm that processes trip inputs, geocodes locations, calculates route legs, and schedules stops per FMCSA constraints."
tags: [routing, algorithm, geocoding, itinerary, scheduling]
date: 2026-06-22
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/notes/project-codebase-state.md
---

# Trip Routing Engine

The trip routing engine is the core computational component that transforms raw trip inputs into a fully scheduled, HOS-compliant itinerary.

## Input Processing

Accepts four required inputs:
1. **Current location**
2. **Pickup location**
3. **Dropoff location**
4. **Current cycle hours used** (0–70)

Plus optional metadata: carrier name, tractor/trailer numbers, start time.

## Geocoding

Locations are resolved to coordinates via two methods:

1. **Google Gemini AI** (primary): Uses structured output with `@google/genai` SDK to return lat/lng, city, state, and distance estimates.
2. **Local fallback** (deterministic): A mock cities database with 14 major US cities. Falls back to Euclidean distance estimation with a 1.2x road factor.

## Route Legs

The trip is divided into two legs:
- **Leg 1**: Current → Pickup (deadhead or initial leg)
- **Leg 2**: Pickup → Dropoff (loaded leg)

Each leg is simulated iteratively in configurable driving segments (capped at 2 hours per segment).

## HOS Scheduling Loop

The iterative scheduler for each leg:

1. Check 70-hour cycle limit → trigger 34-hour reset if exceeded
2. Check 14-hour window or 11-hour limit → trigger 10-hour reset
3. Check 8-hour continuous driving → trigger 30-minute break
4. Check 1,000-mile fueling threshold → trigger fueling stop
5. Determine max driving segment: min(2h, remaining driving hours, remaining duty hours, remaining break time)
6. Drive the segment, update accumulators
7. Repeat until leg distance is consumed

## Itinerary Items

Each scheduling event produces an [[itinerary-item|ItineraryItem]] with:
- Status, activity name, location
- Start/end times (ISO)
- Duration, distance, coordinates
- Remarks string

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — the constraints enforced during scheduling
- [[eld-log-generation|ELD Log Data Generation]] — how the itinerary is partitioned into daily logs
- [[api-specification|API Specification]] — the endpoint that triggers routing
