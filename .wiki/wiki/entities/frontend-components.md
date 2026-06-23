---
title: "Frontend Components"
type: entity
summary: "React components in the Spotter Assessment frontend — TripDetailsForm, CalculatedMap, ItineraryPanel, EldLogSheets"
tags: [react, components, frontend, typescript, ui]
date: 2026-06-22
confidence: high
sources:
  - raw/notes/project-codebase-state.md
  - raw/notes/tech-stack-details.md
  - raw/notes/frontend-integration-update.md
---

# Frontend Components

## Architecture

- **Framework:** React 19 with TypeScript, Vite 6 bundler, Tailwind CSS 4
- **API layer:** Vite proxy → Django DRF backend at `localhost:8000`
- **API transform:** `apiTransform.ts` converts backend snake_case → frontend camelCase
- **State:** Component-local state + prop drilling

## Components

### TripDetailsForm (`src/components/TripDetailsForm.tsx`)
- Input form with 4 required fields (current location, pickup, dropoff, cycle hours)
- Plus optional: carrier name, tractor#, trailer#, start time
- 3 preset route buttons (LA→Vegas, Midwest, East Coast)
- Handles form submission via `onSubmit` callback

### CalculatedMap (`src/components/CalculatedMap.tsx`)
- Leaflet interactive map with CartoDB light tiles
- Route polyline (dashed, editorial styling)
- Custom HTML div icons for stops (start, pickup, dropoff, resets, breaks, fueling)
- Legend overlay and recenter button
- Error handling with recovery UI

### ItineraryPanel (`src/components/ItineraryPanel.tsx`)
- Chronological timeline display with vertical timeline
- Each item shows: activity name, status badge, date/time range, location, distance, duration, remarks
- Color-coded status badges and activity icons

### EldLogSheets (`src/components/EldLogSheets.tsx`)
- SVG-based 24-hour log grid rendering
- Pagination for multi-day trips
- Grid with hour/15-min tick marks, 4 status rows
- Solid line segments with vertical transitions
- Right-side totals column
- Remarks table with status badges
- Mock DOT portal submission button

## API Transform Layer (`src/utils/apiTransform.ts`)
- `mapBackendResponse(data)` — Converts backend snake_case to frontend camelCase
- `mergeUserMetadata(result, carrier, tractor, trailer)` — Patches user-entered metadata onto all daily logs after backend response
- Handles all type renames: `route_geometry` → `routeCoordinates`, `activity_name` → `activityName`, `start_hour` → `startHour`, etc.

## Main App (`src/App.tsx`)
- Orchestrates all components
- Auto-loads default trip on mount
- Sends `POST /api/trips/generate/` with 4 snake_case fields
- Transforms response via `mapBackendResponse()`, then merges user metadata
- Layout: Header → Form → Map + Itinerary (7-col) + Logs (5-col)
- Error handling with alert banner (displays backend error messages directly)
- Footer with compliance branding

## Cross-References

- [[eld-log-grid|ELD Log Grid]] — the SVG grid component
- [[trip-routing-engine|Trip Routing Engine]] — the HOS simulation logic (now Python back end)
- [[api-specification|API Specification]] — the API endpoint consumed
- [[design-system|Design System Reference]] — UI/UX design system, colors, typography, theming
