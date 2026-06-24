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
  - raw/notes/deployment-progress-update.md
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

## Deployment (Vercel)

Both frontend and backend are configured for Vercel deployment.

### Backend (`spotter-bed/`)

| Artifact | Purpose |
|---|---|
| `vercel.json` | `@vercel/python` build from `backend/backend/wsgi.py`, wildcard route |
| `.vercelignore` | Skips `venv/`, `__pycache__/`, tests/ |
| `requirements.txt` | Django 6.0.6, DRF 3.17.1, django-cors-headers 4.9.0 |
| `.python-version` | Python 3.12 |

**Stateless mode:** `settings.py` checks for `VERCEL` env var — when set, `DATABASES = {}` and all config is read from environment variables (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `SECRET_KEY`, `DEBUG`).

**WSGI module resolution:** `wsgi.py` inserts the `backend/` parent directory into `sys.path` before importing Django, fixing module discovery on Vercel.

### Frontend (`spotter-fed/`)

| Artifact | Purpose |
|---|---|
| `vercel.json` | SPA rewrites — all routes served by `/index.html` |
| `App.tsx` | `VITE_API_URL` env var, trailing-slash stripped |

**API base URL:** configured via `VITE_API_URL` env var, with trailing slash stripped to avoid double-slash in requests.

### CORS

- Default origins: `http://localhost:5173` (Vite dev), `http://127.0.0.1:3000`
- Configured via comma-separated `CORS_ALLOWED_ORIGINS` env var

### Notes

- Docker configuration not yet implemented
- Vercel deployment configuration was iterated over 7 commits on June 24, 2026
- Key iteration: module resolution fix (`sys.path`), stateless DB, env-driven config

## Cross-References

- [[frontend-components|Frontend Components]] — React component details
- [[backend-django|Django Backend Structure]] — Backend implementation
- [[api-specification|API Specification]] — Endpoint definitions
- [[hours-of-service|FMCSA HOS Rules]] — Core business logic
- [[deployment-progress-update|Deployment Progress Update]] — Full commit analysis
