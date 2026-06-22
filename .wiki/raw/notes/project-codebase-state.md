---
title: "Project Codebase State (2026-06-22)"
type: source
summary: "Snapshot of the Spotter Assessment codebase — what exists and what is missing as of June 22, 2026"
tags: [codebase, state, audit, gap-analysis]
date: 2026-06-22
confidence: high
source: manual codebase audit
---

# Project Codebase State

**Date:** 2026-06-22

## What Exists and Works

### Frontend (`spotter-fed/`)
- React 19 + TypeScript + Vite 6 + Tailwind CSS 4 + Express
- 4 fully implemented components: `TripDetailsForm`, `CalculatedMap`, `ItineraryPanel`, `EldLogSheets`
- Complete HOS simulation engine in `hosSimulator.ts` (~597 lines) enforcing all major FMCSA rules
- Leaflet interactive map with route tracing and stop callouts
- SVG-based ELD log grid with 15-min increment rendering
- Express server (`server.ts`) acting as current API host
- Geocoding via Google Gemini AI or local fallback
- Auto-loads default trip (LA → Las Vegas → Salt Lake City) on mount

### Backend (`spotter-bed/`)
- Scaffolded Django 6.0.6 project with Python 3.14
- One app (`spotter-eld`) created but empty
- SQLite database configured
- Pipfile with only `django` listed

## What Is Missing / Needs Building

1. **Django REST Framework** not installed or configured
2. **django-cors-headers** not installed or configured
3. **spotter_eld app not registered** in `INSTALLED_APPS`
4. **No DRF views, serializers, or API endpoints** — spec calls for `POST /api/trips/generate/`
5. **No models** defined in `models.py`
6. **No external Map API integration** in backend (currently Express handles geocoding)
7. **Dark mode** not yet implemented (current app uses light editorial theme only)
8. **MUI not used** — frontend uses Tailwind CSS + custom styling instead

## Key Architecture Divergence

The current implementation uses an Express server as the API layer with the HOS engine running in TypeScript. The spec calls for a Django DRF backend. The frontend HOS engine (`hosSimulator.ts`) would need to be ported to Python.
