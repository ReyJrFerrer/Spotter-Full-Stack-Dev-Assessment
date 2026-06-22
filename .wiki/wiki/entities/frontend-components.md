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
---

# Frontend Components

## Architecture

- **Framework:** React 19 with TypeScript, Vite 6 bundler, Tailwind CSS 4
- **Current API layer:** Express server (`server.ts`)
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

## Main App (`src/App.tsx`)
- Orchestrates all components
- Auto-loads default trip on mount
- Layout: Header → Form → Map + Itinerary (7-col) + Logs (5-col)
- Error handling with alert banner
- Footer with compliance branding

## Cross-References

- [[eld-log-grid|ELD Log Grid]] — the SVG grid component
- [[trip-routing-engine|Trip Routing Engine]] — the HOS simulation logic
- [[api-specification|API Specification]] — the API endpoint consumed
