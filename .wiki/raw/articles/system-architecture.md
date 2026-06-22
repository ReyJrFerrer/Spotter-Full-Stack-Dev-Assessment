---
title: "System Architecture Specifications"
type: source
summary: "System architecture for the Spotter Assessment project — React frontend + Django backend with map API and HOS engine"
tags: [architecture, react, django, api, deployment]
date: 2026-06-22
confidence: high
source: system-architecture.md
---

# System Architecture Specifications

**Source:** `system-architecture.md` (project root)

## Frontend (React)

- **Framework:** React SPA with `axios` for HTTP
- **UI:** Material UI (MUI) card-based layout
- **Typography:** Tabular lining for all numerical data; theme toggle (Light Mode + True Dark Mode #121212)
- **Visual Rendering:** ELD Log Grid component drawing solid continuous lines across 24-hour grid for Off Duty, Sleeper Berth, Driving, On Duty

## Backend (Django)

- **Framework:** Django + DRF for RESTful API
- **Routing:** Free Map API for driving distance, route paths, estimated time
- **HOS Algorithm:** Iterative scheduler enforcing FMCSA constraints:
  - 1h on-duty for pickup/dropoff
  - Fueling every 1,000 miles
  - 11h driving limit + 14h window + 10h reset
  - 30-min break after 8h driving
  - 70h/8-day cycle tracking
- **Serialization:** DRF serializers for itinerary, stops, 15-min logbook grid

## Inter-System Communication & Deployment

- CORS via `django-cors-headers`
- Deploy via Vercel
