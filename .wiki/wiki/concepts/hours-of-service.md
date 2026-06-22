---
title: "FMCSA Hours of Service (HOS) Rules"
type: concept
summary: "Federal Motor Carrier Safety Administration Hours of Service regulations for property-carrying commercial truck drivers, as implemented in the Spotter Assessment project."
tags: [fmcsa, hos, regulations, driving-limits, duty-status]
date: 2026-06-22
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/notes/project-codebase-state.md
---

# FMCSA Hours of Service (HOS) Rules

The Spotter Assessment project enforces FMCSA HOS regulations for property-carrying commercial truck drivers. These rules govern when a driver may operate a commercial motor vehicle (CMV).

## Duty Status Categories

Four [[duty-statuses|Duty Statuses]] defined by FMCSA:

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

## Algorithm Implementation

The HOS algorithm is implemented in two forms:

1. **TypeScript engine** (`spotter-fed/src/utils/hosSimulator.ts`): Fully functional, currently used via the Express server. Enforces all constraints through an iterative scheduler that steps through route legs in configurable driving segments.

2. **Python port (pending)**: The Django backend spec requires porting this logic into a Python DRF backend.

## Reset Types

- **10-Hour Daily Reset**: Sleeper Berth or Off Duty for 10 consecutive hours resets the 11-hour and 14-hour clocks.
- **34-Hour Weekly Reset**: Off Duty for 34 consecutive hours resets the 70-hour/8-day clock to zero.

## Cross-References

- [[eld-log-generation|ELD Log Data Generation]] — how the timeline is sliced into daily log sheets
- [[trip-routing-engine|Trip Routing Engine]] — how HOS constraints are applied during route simulation
