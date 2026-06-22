---
title: "Project Architecture Reference"
type: reference
summary: "Complete system architecture overview of the Spotter Assessment — a full-stack Django/React application for ELD log generation."
tags: [architecture, overview, system-design]
date: 2026-06-22
confidence: high
sources:
  - raw/articles/backend-specifications.md
  - raw/articles/system-architecture.md
  - raw/articles/ui-specifications.md
  - raw/notes/project-codebase-state.md
---

# Project Architecture Reference

## High-Level Overview

The Spotter Assessment is a full-stack web application that generates AI-optimized trucking routes and FMCSA-compliant ELD daily log sheets.

```
[User] → [React SPA] → [Express/Django API] → [Map API]
                               ↓
                    [HOS Algorithm Engine]
                               ↓
                    [ELD Log Data Generator]
                               ↓
                    [JSON Response → Frontend]
```

## Current Architecture (as built)

```
┌─────────────────────────────────────────────────────┐
│                   React SPA (spotter-fed/)           │
│                                                      │
│  TripDetailsForm → Express API (server.ts)           │
│       ↓                      ↓                       │
│  CalculatedMap       hosSimulator.ts                 │
│  ItineraryPanel        (HOS Engine)                  │
│  EldLogSheets                                        │
└─────────────────────────────────────────────────────┘
```

The Express server (`server.ts`) acts as the current API layer, handling geocoding (Gemini AI or local) and calling the TypeScript HOS engine.

## Planned Architecture (per spec)

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   React SPA             │     │   Django Backend         │
│   (spotter-fed/)        │◄───►│   (spotter-bed/)         │
│                         │     │                          │
│  MUI Components         │     │  DRF: POST /api/trips/   │
│  Leaflet Map            │     │  HOS Engine (Python)     │
│  SVG ELD Grid           │     │  Map API Integration     │
│  Dark/Light Theme       │     │  CORS Whitelisting       │
└─────────────────────────┘     └─────────────────────────┘
```

## Data Flow

1. User submits trip form → `POST /api/generate-trip`
2. Server geocodes locations (Gemini AI or mock database)
3. HOS engine simulates trip with constraint enforcement
4. Trip partitioned into daily log sheets
5. JSON response returned with:
   - Route coordinates for map
   - Chronological itinerary
   - Daily log sheet objects with grid coordinates
6. Frontend renders map, itinerary, and ELD grids

## Key Files

| File | Purpose |
|---|---|
| `spotter-fed/src/utils/hosSimulator.ts` | HOS algorithm engine (TypeScript) |
| `spotter-fed/server.ts` | Express API server |
| `spotter-fed/src/App.tsx` | Main React component |
| `spotter-fed/src/components/TripDetailsForm.tsx` | Input form |
| `spotter-fed/src/components/CalculatedMap.tsx` | Map display |
| `spotter-fed/src/components/ItineraryPanel.tsx` | Chronological timeline |
| `spotter-fed/src/components/EldLogSheets.tsx` | ELD log grid |
| `spotter-fed/src/types.ts` | TypeScript type definitions |
| `spotter-bed/backend/backend/settings.py` | Django settings |
| `spotter-bed/backend/backend/urls.py` | Django URL config |

## Deployment

- Docker containerization for backend
- Vercel deployment for both frontend and backend

## Cross-References

- [[frontend-components|Frontend Components]] — React component details
- [[backend-django|Django Backend Structure]] — Backend implementation
- [[api-specification|API Specification]] — Endpoint definitions
- [[hours-of-service|FMCSA HOS Rules]] — Core business logic
