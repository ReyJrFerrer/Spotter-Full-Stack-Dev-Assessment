# Spotter Assessment — Agent Guide

## Project Overview

Full-stack web application (Django + React) that generates AI-optimized trucking routes and FMCSA-compliant ELD (Electronic Logging Device) daily log sheets. Accepts trip inputs (current location, pickup, dropoff, cycle hours used), integrates a free Map API, and enforces strict Hours of Service (HOS) rules.

---

## Architecture

### Frontend: `spotter-fed/` (React SPA)

| Aspect | Convention |
|---|---|
| Framework | React with Material UI (MUI) components |
| HTTP | `axios` for async backend calls |
| State | Component-local state + prop drilling (SPA) |
| Typography | Tabular lining (`font-variant-numeric: tabular-nums`) on all numeric data |
| Theming | Light Mode (data-dense) + True Dark Mode (`#121212` background) |
| Layout | Modular MUI Card-based layout — input form, map, ELD logs in separate cards |

**Key Components:**
- Trip input form (4 fields: current_location, pickup_location, dropoff_location, current_cycle_used_hrs)
- Interactive map card with route tracing (AI-accent colored route line)
- Stop callouts (color-coded: blue = pickup/dropoff/fueling, amber/red = HOS rest)
- ELD Log Grid — draws solid continuous lines across a 24-hour grid for Off Duty, Sleeper Berth, Driving, On Duty
- Theme toggle between Light and Dark modes

### Backend: `spotter-bed/` (Django + DRF)

| Aspect | Convention |
|---|---|
| Framework | Django + Django REST Framework |
| CORS | `django-cors-headers` whitelisting frontend origin |
| Structure | Modular Django apps (routing engine, HOS logic separate from core settings) |
| Deployment | Docker + Vercel |

**API Endpoint:**
- `POST /api/trips/generate/`
  - Request: `{ current_location, pickup_location, dropoff_location, current_cycle_used_hrs }`
  - Response: route map coords, scheduled stops array, daily log sheet objects (multiple if trip >24h)

**External Integration:**
- Free Map API for distance, route paths, estimated driving time

---

## HOS Algorithm Engine (Core Business Logic)

Iterative scheduler that processes Map API route data and injects status changes per FMCSA constraints:

| Constraint | Rule |
|---|---|
| Duty Statuses | Off Duty, Sleeper Berth, Driving, On Duty (Not Driving) |
| Pickup/Dropoff | 1 hour On Duty each |
| Fueling | At least once every 1,000 miles |
| 11-Hour Limit | Max 11h driving → 10h off-duty reset |
| 14-Hour Window | 14 consecutive hours from coming on duty; no driving after |
| 30-Min Break | After 8 cumulative driving hours |
| 70-Hour/8-Day | Track cycle used + new trip time; halt at 70h |
| Scope | No adverse conditions, hauling property |

---

## ELD Log Data Generation

- Timeline split at midnight into daily 24h chunks
- 15-min increment grid coordinates for frontend line drawing
- Remarks string at each duty status change (location + activity)
- Per-day totals: hours in each of 4 statuses (sum=24) + miles driven
- Header metadata: Date, Miles, Truck/Trailer, Carrier

---

## UI/UX Conventions

### Color Palette
| Role | Color |
|---|---|
| Primary | High-trust tech blues |
| Accent (AI) | Electric blue / subtle neon purple |
| Driving/Compliant | Vibrant green |
| Near-limit warning | High-vis amber/orange |
| Violation/stop | Crimson red |

### ELD Log Grid Layout
- Time axis: Midnight-to-Midnight, hour markers + 15-min ticks
- 4 status rows: Off Duty, Sleeper Berth, Driving, On Duty
- Solid color-coded lines drawn across grid
- Remarks section below grid (city, state, 45° flag mark)
- Daily totals column (right side, tabular lining, sum=24)

---

## Project Structure

```
spotter-assessment/
├── AGENTS.md              # This file
├── system-architecture.md
├── backend-specifications.md
├── ui-specifications.md
├── spotter-bed/           # Django backend
│   ├── (Django project)
│   ├── (DRF views/serializers)
│   ├── (HOS algorithm app)
│   └── (routing integration app)
├── spotter-fed/           # React frontend
│   ├── (React components)
│   ├── (MUI theme config)
│   ├── (ELD grid component)
│   └── (map integration)
├── .opencode/
│   └── skills/
│       └── llm-wiki/      # LLM Wiki skill
│           ├── SKILL.md
│           └── references/
│               ├── ingestion.md
│               └── maintenance.md
└── .wiki/                 # LLM Wiki knowledge base
    ├── _index.md
    ├── log.md
    └── config.md
```

---

## Development Workflow

1. Backend-first: implement HOS algorithm + API endpoint
2. Frontend: build input form → map display → ELD grid
3. Wire CORS, test full flow
4. Theme toggling, polish, deploy to Vercel

### Naming Conventions
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- JavaScript/React: `camelCase` for functions/variables, `PascalCase` for components
- Django apps: lowercase with underscores (e.g. `hos_engine`, `route_api`)
- React components: PascalCase (e.g. `TripForm`, `EldLogGrid`, `RouteMap`)
