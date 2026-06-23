---
title: "Project Architecture Reference"
type: reference
summary: "Complete system architecture overview of the Spotter Assessment — a full-stack Django/React application for ELD log generation."
tags: [architecture, overview, system-design]
date: 2026-06-23
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/articles/ui-specifications.md
  - raw/notes/backend-implementation-details.md
  - raw/notes/backend-codebase-update.md
  - raw/notes/project-codebase-state.md
---

# Project Architecture Reference

## High-Level Overview

The Spotter Assessment is a full-stack web application that generates optimized trucking routes and FMCSA-compliant ELD daily log sheets.

## Architecture

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   React SPA              │     │   Django Backend          │
│   (spotter-fed/)         │◄───►│   (spotter-bed/)          │
│                           │     │                           │
│  Tailwind CSS Components  │     │  DRF: POST /api/trips/    │
│  Leaflet Map              │     │  HOS Engine (Python)      │
│  SVG ELD Grid             │     │  OSRM Routing API         │
│  Dark/Light Theme (spec)  │     │  Nominatim Geocoding      │
│                           │     │  CORS Whitelisting        │
└─────────────────────────┘     └─────────────┬───────────────┘
                                               │
                                               ↓
                                        ┌──────────────┐
                                        │  External     │
                                        │  Map APIs     │
                                        │  (OSRM/       │
                                        │   Nominatim)  │
                                        └──────────────┘
```

## Data Flow

1. User submits trip form → `POST /api/trips/generate/`
2. Backend geocodes locations (city DB → Nominatim fallback)
3. Backend calls OSRM for route distance/geometry (falls back to Euclidean estimate)
4. HOS engine (Python) simulates trip with constraint enforcement
5. Trip partitioned into daily log sheets
6. JSON response returned with: route coordinates, itinerary, daily logs
7. Frontend renders map, itinerary, ELD grids

## Backend (spotter-bed/)

| File | Purpose |
|---|---|
| `spotter_eld/hos_engine.py` | HOS algorithm engine — iterative scheduler |
| `spotter_eld/eld_generator.py` | Daily log partitioning |
| `spotter_eld/geocoding.py` | City DB + Nominatim + OSRM routing |
| `spotter_eld/views.py` | DRF API views |
| `spotter_eld/types.py` | Data class definitions |
| `spotter_eld/tests/` | 114 tests across 7 files |

## Frontend (spotter-fed/)

| File | Purpose |
|---|---|
| `src/components/TripDetailsForm.tsx` | Input form (4 fields) |
| `src/components/CalculatedMap.tsx` | Leaflet map with route tracing |
| `src/components/ItineraryPanel.tsx` | Chronological stop timeline |
| `src/components/EldLogSheets.tsx` | SVG ELD log grid with 15-min increments |
| `src/utils/apiTransform.ts` | Backend snake_case → frontend camelCase transformer |
| `src/App.tsx` | Root component — orchestrates layout and API calls |

## Deployment

- Vercel deployment target for both frontend and backend
- Docker configuration not yet implemented

## Cross-References

- [[frontend-components|Frontend Components]] — React component details
- [[backend-django|Django Backend Structure]] — Backend implementation
- [[api-specification|API Specification]] — Endpoint definitions
- [[hours-of-service|FMCSA HOS Rules]] — Core business logic
