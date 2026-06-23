---
title: "Frontend Integration Update"
type: note
summary: "Frontend refactored from self-contained Express architecture to thin client communicating with Django backend via Vite proxy"
source: "codebase audit"
date: 2026-06-23
author: "Agent"
tags: [frontend, integration, api, refactor, dependencies]
confidence: high
---

# Frontend Integration Update

## Summary

The frontend (`spotter-fed/`) has been refactored from a self-contained Express-based architecture to a thin client that communicates with the Django Django backend at `localhost:8000`. Key changes: removed the Express dev server and its dependencies, removed the client-side HOS simulator (now handled by Django), and configured Vite to proxy `/api/*` requests to the backend.

## Changes Made

### Deleted Files
- `server.ts` (295 lines) — Express server with Gemini AI geocoding, mock city database, and `POST /api/generate-trip` handler
- `src/utils/hosSimulator.ts` (597 lines) — Full TypeScript HOS algorithm (duplicate of Django backend logic)

### Created Files
- `src/utils/apiTransform.ts` (~80 lines) — Transforms Django snake_case API responses to frontend camelCase types. Includes `mapBackendResponse()` and `mergeUserMetadata()` helper.

### Modified Files
- `src/App.tsx` — API endpoint changed to `POST /api/trips/generate/`; request body reduced to 4 snake_case fields (`current_location`, `pickup_location`, `dropoff_location`, `current_cycle_used_hrs`); response handling now expects direct object (no `success.data` wrapper); error handling reads backend error messages; header badge updated to "OSRM + NOMINATIM"
- `src/types.ts` — Added `routeCoordinates: [number, number][]` to `TripGenerationResult`
- `vite.config.ts` — Added `/api` proxy to `http://localhost:8000`
- `package.json` — Changed `"dev"` from `tsx server.ts` to `vite`; simplified build scripts; removed `express`, `@google/genai`, `dotenv`, `esbuild`, `tsx`, `autoprefixer` and their `@types` dev dependencies

### Components Unchanged
- `TripDetailsForm.tsx` — Still collects all 8 fields (4 required + 4 metadata); metadata merged client-side after response
- `CalculatedMap.tsx` — Unchanged; receives `routeCoordinates` prop mapped from backend `route_geometry`
- `ItineraryPanel.tsx` — Unchanged; all fields map via apiTransform
- `EldLogSheets.tsx` — Unchanged; carrier/tractor/trailer metadata patched via `mergeUserMetadata()` for all logs

## Data Flow (After Integration)

1. User fills form with 4 location/cycle fields + optional metadata (carrier, tractor, trailer, start time)
2. Frontend sends only 4 required snake_case fields to `POST /api/trips/generate/`
3. Vite proxy forwards request to Django backend at `http://localhost:8000`
4. Django geocodes via city DB + Nominatim, routes via OSRM, simulates HOS
5. Django returns snake_case response directly
6. `mapBackendResponse()` transforms to frontend camelCase types
7. `mergeUserMetadata()` patches carrier/tractor/trailer onto all daily log sheets
8. Components render with unchanged prop interfaces

## Dev Environment

- `npm run dev` — Vite dev server on `http://localhost:5173`
- Django backend on `http://localhost:8000`
- Vite proxies `/api/*` to backend

## Remaining Gaps

- Dark mode not yet implemented (spec requirement)
- No MUI components (uses Tailwind CSS custom design system)
- `motion` library still in dependencies but unused
