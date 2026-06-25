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
  - raw/notes/map-us-bounds-restriction.md
  - raw/notes/nominatim-autocomplete-api.md
---

# Frontend Components

## Architecture

- **Framework:** React 19 with TypeScript, Vite 6 bundler, Tailwind CSS 4
- **API layer:** Vite proxy → Django DRF backend at `localhost:8000`
- **API transform:** `apiTransform.ts` converts backend snake_case → frontend camelCase
- **State:** Component-local state + prop drilling

## Components

### TripDetailsForm (`src/components/TripDetailsForm.tsx`)
- Input form with 3 location autocompletes (current, pickup, dropoff) backed by Nominatim API, plus cycle hours
- Plus optional: carrier name, tractor#, trailer#
- **Dispatch Schedule block:** separate date picker, time picker (15-min steps), and IANA timezone `<select>` (Pacific/Mountain/Central/Eastern/Alaska/Hawaii/UTC). Auto-detects browser timezone via `Intl.DateTimeFormat()` and shows UTC offset. Default start = today at 06:00 local.
- 3 preset route buttons (LA→Vegas, Midwest, East Coast)
- Handles form submission via `onSubmit` callback, sending `start_time` + `timezone` to the backend

### CalculatedMap (`src/components/CalculatedMap.tsx`)
- Leaflet interactive map with CartoDB light tiles
- Route polyline (dashed, editorial styling)
- Custom HTML div icons for stops (start, pickup, dropoff, resets, breaks, fueling)
- Legend overlay and recenter button
- Error handling with recovery UI
- **US bounds restriction:** `maxBounds` set to CONUS bounding box (`[24,-126]` → `[50,-65]`), `maxBoundsViscosity: 0.15` for soft bounce-back, `minZoom: 3` to prevent zooming too far out

### LocationAutocomplete (`src/components/LocationAutocomplete.tsx`)
- Reusable searchable autocomplete for US city, state inputs
- **Empty/focused state:** shows scrollable static list of ~100 capitals + top metros for instant browsing
- **Typing 2+ chars:** calls backend `GET /api/locations/autocomplete/?q=...` with 300ms debounce, showing Nominatim results
- Keyboard navigation (arrow keys, enter, escape)
- Loading spinner, empty state, and error state

### ItineraryPanel (`src/components/ItineraryPanel.tsx`)
- Chronological timeline display with vertical timeline
- Each item shows: activity name, status badge, date/time range, location, distance, duration, remarks
- **Trip-timezone aware:** accepts a `tripTimezone` prop and renders every date/time using `Intl.DateTimeFormat({ timeZone: tripTimezone })`. Header shows a globe icon + IANA name so the user can verify the anchor clock.
- Color-coded status badges and activity icons

### EldLogSheets (`src/components/EldLogSheets.tsx`)
- SVG-based 24-hour log grid rendering
- Pagination for multi-day trips
- Grid with hour/15-min tick marks, 4 status rows
- Solid line segments with vertical transitions
- Right-side totals column
- Remarks table with status badges
- **Trip-timezone aware:** shows the active log's IANA timezone in the metadata strip; backend-supplied `time_label` values are already in the trip local time so the grid and itinerary agree.
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
- [[timezone-aware-scheduling|Timezone-Aware Trip Scheduling]] — calendar/timezone UI flow
