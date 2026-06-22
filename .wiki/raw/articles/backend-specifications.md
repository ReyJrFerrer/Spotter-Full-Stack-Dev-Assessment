---
title: "Backend Specifications"
type: source
summary: "Full backend specification for the Spotter Assessment project — Django DRF API with FMCSA HOS enforcement"
tags: [backend, django, api, hos, fmcsa]
date: 2026-06-22
confidence: high
source: backend-specifications.md
---

# Backend Specifications

**Source:** `backend-specifications.md` (project root)

## Overview

Full-stack web application (Django + React) for route and ELD log generation for property-carrying commercial truck drivers. Accepts 4 inputs: current location, pickup, dropoff, current cycle hours used. Uses free Map API, enforces FMCSA HOS regulations, generates step-by-step route instructions and 24-hour ELD log sheets.

## Core System & Environment

- Python Django + DRF for decoupled API
- `django-cors-headers` whitelisting frontend origin
- Modular Django app structure (routing engine + HOS logic separate from core settings)
- Docker containerization for production

## API Endpoint

- **POST** `/api/trips/generate/`
- Request: `{ current_location, pickup_location, dropoff_location, current_cycle_used_hrs }`
- Response: route map coords, scheduled stops array, daily log sheet objects (multiple if trip >24h)

## External API

- Free Map API for distance, route paths, estimated driving time

## FMCSA Constraints (HOS Algorithm)

1. **4 Duty Statuses:** Off Duty, Sleeper Berth, Driving, On Duty (Not Driving)
2. **Pickup/Dropoff:** 1 hour On Duty each
3. **Fueling:** At least once every 1,000 miles
4. **11-Hour Limit:** Max 11h driving → 10h off-duty reset
5. **14-Hour Window:** 14 consecutive hours from coming on duty; no driving after
6. **30-Min Break:** After 8 cumulative driving hours
7. **70-Hour/8-Day:** Track cycle used + new trip time; halt at 70h
8. **Scope:** No adverse conditions, hauling property

## ELD Log Data Generation

- Timeline split at midnight into daily 24h chunks
- 15-min increment grid coordinates for frontend line drawing
- Remarks string at each duty status change (location + activity)
- Per-day totals: hours in each of 4 statuses (sum=24) + miles driven
- Header metadata: Date, Miles, Truck/Trailer, Carrier
