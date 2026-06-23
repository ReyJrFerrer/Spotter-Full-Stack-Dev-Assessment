---
title: "FMCSA Hours of Service (HOS) Rules"
type: concept
summary: "Federal Motor Carrier Safety Administration Hours of Service regulations for property-carrying commercial truck drivers, as implemented in the Spotter Assessment project."
tags: [fmcsa, hos, regulations, driving-limits, duty-status]
date: 2026-06-23
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/notes/hos-engine-implementation.md
  - raw/notes/backend-implementation-details.md
---

# FMCSA Hours of Service (HOS) Rules

The Spotter Assessment project enforces FMCSA HOS regulations for property-carrying commercial truck drivers. These rules govern when a driver may operate a commercial motor vehicle (CMV).

## Duty Status Categories

Four duty statuses defined by FMCSA:

| Status | Code | Description |
|---|---|---|
| Off Duty | OFF | Rest, personal time, not working |
| Sleeper Berth | SB | Rest in the sleeper compartment |
| Driving | D | Operating a CMV |
| On Duty (Not Driving) | ON | All work except driving (loading, inspections, fueling) |

## Key Constraints

### 11-Hour Driving Limit
Maximum 11 hours of driving after 10 consecutive hours off duty. Once 11 hours is reached, the driver must take a 10-hour break before driving again.

### 14-Hour Duty Window
A driver cannot drive after the 14th consecutive hour after coming on duty, following a 10-hour off-duty period. All driving must cease when this window expires.

### 30-Minute Rest Break
After 8 cumulative hours of driving (not necessarily consecutive), the driver must take a 30-minute consecutive break before continuing to drive.

### 70-Hour/8-Day Limit
A driver may not drive after accumulating 70 hours of on-duty (all Driving + On Duty time) in 8 consecutive days.

### Fueling Requirement
The algorithm mandates a fueling stop at least once every 1,000 miles.

## Algorithm Implementation (Python)

The HOS engine is implemented in `spotter_eld/hos_engine.py` (387 lines). It is an iterative scheduler that:

1. Starts with a 15-minute pre-trip inspection (On Duty)
2. Simulates Leg 1 (Current → Pickup) in 2-hour max driving chunks
3. Injects pickup: 1 hour On Duty
4. Simulates Leg 2 (Pickup → Dropoff) in 2-hour max driving chunks
5. Injects dropoff: 1 hour On Duty
6. Partitions into daily logs

During each leg, it checks all constraints in order and injects breaks/resets as needed.

## Reset Types

- **10-Hour Daily Reset (8/2 Split)**: 8 hours Sleeper Berth + 2 hours Off Duty. Resets the 11-hour and 14-hour clocks per 49 CFR § 395.1(g).
- **30-Minute Break**: 0.5 hours Off Duty. Resets the continuous driving clock after 8 cumulative hours of driving.
- **34-Hour Weekly Reset**: 34 hours Off Duty. Resets the 70-hour/8-day clock to zero.

## Cross-References

- [[eld-log-generation|ELD Log Data Generation]] — how the timeline is sliced into daily log sheets
- [[trip-routing-engine|Trip Routing Engine]] — how HOS constraints are applied during route simulation
- [[api-specification|API Specification]] — POST endpoint that triggers the engine
