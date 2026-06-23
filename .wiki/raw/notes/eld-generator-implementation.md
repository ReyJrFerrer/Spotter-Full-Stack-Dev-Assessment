---
title: "ELD Generator Implementation (eld_generator.py)"
type: source
summary: "Daily log sheet partitioning logic — 24-hour slicing, quarter-hour grid coordinates, remarks generation, per-day totals"
tags: [eld, log, generator, partitioning, implementation]
date: 2026-06-23
confidence: high
source: manual codebase audit
---

# ELD Generator Implementation

**File:** `spotter-bed/backend/spotter_eld/eld_generator.py` (176 lines)

## Overview

`partition_into_daily_logs()` splits the chronological itinerary into 24-hour daily chunks, creates timeline blocks with 15-min grid coordinates, generates remarks at status transitions, and computes per-day totals.

## Key Logic

### Date Slicing (line 32-43)
- Creates list of midnight-to-midnight date boundaries from trip start to end
- Each day gets its own `DailyLogSheet`

### Timeline Mapping (line 58-116)
For each itinerary item:
- Checks overlap with target day's 24h window
- Converts timestamps to hours since midnight (quarter-hour rounded)
- Fills gaps between items with Off Duty blocks
- Appends overlapping portion as `TimelineBlock`

### Mileage Tracking (line 100-104)
- Pro-rates miles for items crossing midnight boundaries
- `fraction = overlap_duration_ms / item_duration_ms`
- `miles_driven_today += item.distance_miles * fraction`

### Remarks Generation (line 106-114)
- Captures remarks for items that start within the target day
- Includes: time_label (HH:MM AM/PM), status, location, remarks_text

### Totals Computation (line 134-155)
- Sums hours per status across timeline blocks
- If total != 24h (due to rounding), injects remaining time as Off Duty on last block
- Returns rounded-to-quarter-hour values for each of OFF/SB/D/ON

### Metadata (line 157-174)
- Each log includes: date_string (YYYY-MM-DD), date_label (Mon, Jun DD, YYYY), miles driven, carrier/truck/trailer info

## Data Types

- `DailyLogSheet` — top-level log container with timeline, totals, remarks
- `TimelineBlock` — contiguous status block with start/end hours and location
- `DailyLogRemarks` — single remark entry with time, status, location, text
