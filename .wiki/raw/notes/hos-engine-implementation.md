---
title: "HOS Engine Implementation (hos_engine.py)"
type: source
summary: "Detailed walkthrough of the Python HOS algorithm engine — iterative scheduler enforcing 11/14/70-hour FMCSA rules, 30-min break, fueling mandate"
tags: [hos, algorithm, engine, fmcsa, implementation]
date: 2026-06-23
confidence: high
source: manual codebase audit
---

# HOS Engine Implementation

**File:** `spotter-bed/backend/spotter_eld/hos_engine.py` (387 lines)

## Overview

The engine (`simulate_trip()`) is an iterative scheduler that processes route legs and injects status changes per FMCSA constraints. It operates on a simulated timeline using dataclass-based state tracking.

## Key Functions

### `simulate_trip()` (line 63)
Main entry point. Accepts 3 geocoded locations, cycle hours used, optional start time, and optional external legs (from OSRM). Returns a `TripGenerationResult`.

### `_make_legs()` (line 34)
Fallback when OSRM data unavailable. Uses Euclidean distance × 55 miles/degree, minimum 20 miles. Speed: 60 mph average.

### `trigger_10h_reset()` (line 132)
Adds 8h Sleeper Berth + 2h Off Duty (8/2 split per 49 CFR § 395.1(g)). Resets all daily counters.

### `trigger_30min_break()` (line 148)
Adds 0.5h Off Duty after 8 cumulative driving hours. Resets continuous driving counter.

### `trigger_34h_restart()` (line 162)
Adds 34h Off Duty when cycle hits 70h. Resets all counters including cycle.

### `simulate_leg()` (line 179)
Core loop: while miles remain, check limits, inject breaks/resets/fueling, drive in chunks of max 2h bounded by remaining limits.

## DriverState (line 19)
Tracks: `accum_driving_today`, `elapsed_duty_window_today`, `continuous_driving_since_break`, `total_cycle_hours_used`, `miles_since_fueling`

## HOS Rules Enforced

| Rule | Implementation |
|---|---|
| 11-Hour Driving Limit | `state.accum_driving_today >= 11` → trigger 10h reset |
| 14-Hour Window | `state.elapsed_duty_window_today >= 14` → trigger 10h reset |
| 30-Min Break | `state.continuous_driving_since_break >= 8` → trigger 30min OFF |
| 70-Hour/8-Day Cycle | `state.total_cycle_hours_used >= 70` → trigger 34h restart |
| Fueling every 1000 miles | `state.miles_since_fueling >= 1000` → inject 30min ON fueling |
| Pickup/Dropoff | 1 hour On Duty each |
| Pre-Trip | 15 min On Duty |

## Trip Flow

1. Pre-Trip Inspection (0.25h ON)
2. Leg 1: Current → Pickup (with break/limit checks)
3. Arrive at Pickup (1h ON, with 14h window check before)
4. Leg 2: Pickup → Dropoff (with break/limit checks)
5. Arrive at Dropoff (1h ON, with 14h window check before)
6. Partition into daily logs via `eld_generator.partition_into_daily_logs()`

## Edge Cases

- 14h limit checked before pickup/dropoff — injects 10h reset if exceeded
- `max_hours_possible = min(2.0, remaining_driving, remaining_duty, remaining_before_8h_break)` — caps each chunk at 2h
- If `max_hours_possible <= 0` after all checks, forces a 10h safety reset
