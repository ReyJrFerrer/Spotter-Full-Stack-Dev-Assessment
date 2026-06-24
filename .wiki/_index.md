# Spotter Assessment Wiki

> LLM-compiled knowledge base for the Spotter Assessment project.

## Wiki Info

- **Root**: `.wiki/`
- **Created**: 2026-06-22
- **Last updated**: 2026-06-23
- **Last lint**: 2026-06-23

## Index

### Concepts

| Page | Summary |
|---|---|
| [[hours-of-service\|FMCSA HOS Rules]] ([concepts/hours-of-service](wiki/concepts/hours-of-service.md)) | FMCSA Hours of Service regulations — 11/14/70-hour limits, 30-min break, 8/2 sleeper berth split, fueling requirements |
| [[eld-log-generation\|ELD Log Data Generation]] ([concepts/eld-log-generation](wiki/concepts/eld-log-generation.md)) | Python implementation of trip timeline partitioning into 24-hour daily log sheets with 15-min grid coordinates |
| [[trip-routing-engine\|Trip Routing Engine]] ([concepts/trip-routing-engine](wiki/concepts/trip-routing-engine.md)) | Python iterative HOS scheduler — geocoding pipeline, route legs, constraint enforcement loop |
| [[eld-log-grid\|ELD Log Grid]] ([concepts/eld-log-grid](wiki/concepts/eld-log-grid.md)) | Standardized 24-hour SVG grid for duty status visualization |

### Entities

| Page | Summary |
|---|---|
| [[frontend-components\|Frontend Components]] ([entities/frontend-components](wiki/entities/frontend-components.md)) | React components: TripDetailsForm, CalculatedMap, ItineraryPanel, EldLogSheets |
| [[backend-django\|Django Backend Structure]] ([entities/backend-django](wiki/entities/backend-django.md)) | Fully implemented Django DRF backend — HOS engine, ELD generator, geocoding/routing, 114 tests |

### References

| Page | Summary |
|---|---|
| [[project-architecture\|Project Architecture Reference]] ([references/project-architecture](wiki/references/project-architecture.md)) | Complete system architecture — React frontend, Django DRF backend, OSRM/Nominatim APIs |
| [[api-specification\|API Specification]] ([references/api-specification](wiki/references/api-specification.md)) | Django DRF API endpoints — request/response format for trip generation |
| [[design-system\|Design System Reference]] ([references/design-system](wiki/references/design-system.md)) | UI/UX design system — colors, typography, theming, layout conventions |

### Sources

| Page | Type | Summary |
|---|---|---|
| [[backend-specifications\|Backend Specifications]] ([raw/articles/backend-specifications](../raw/articles/backend-specifications.md)) | Article | Django DRF API spec with FMCSA HOS rules |
| [[system-architecture\|System Architecture]] ([raw/articles/system-architecture](../raw/articles/system-architecture.md)) | Article | React + Django architecture with CORS, deployment |
| [[ui-specifications\|UI/UX Specifications]] ([raw/articles/ui-specifications](../raw/articles/ui-specifications.md)) | Article | MUI design system, ELD grid, map, theming |
| [[project-codebase-state\|Project Codebase State]] ([raw/notes/project-codebase-state](../raw/notes/project-codebase-state.md)) | Note | Codebase snapshot as of June 22 (pre-implementation) |
| [[backend-codebase-update\|Backend Codebase Update]] ([raw/notes/backend-codebase-update](../raw/notes/backend-codebase-update.md)) | Note | Post-implementation backend state — 114 tests, all features built |
| [[tech-stack-details\|Tech Stack Details]] ([raw/notes/tech-stack-details](../raw/notes/tech-stack-details.md)) | Note | Technology versions and dependencies |
| [[hos-engine-implementation\|HOS Engine Implementation]] ([raw/notes/hos-engine-implementation](../raw/notes/hos-engine-implementation.md)) | Note | Detailed walkthrough of hos_engine.py — iterative scheduler |
| [[eld-generator-implementation\|ELD Generator Implementation]] ([raw/notes/eld-generator-implementation](../raw/notes/eld-generator-implementation.md)) | Note | Daily log partitioning logic in eld_generator.py |
| [[geocoding-routing-implementation\|Geocoding and Routing Implementation]] ([raw/notes/geocoding-routing-implementation](../raw/notes/geocoding-routing-implementation.md)) | Note | City DB, Nominatim, OSRM integration in geocoding.py |
| [[backend-implementation-details\|Backend Implementation Details]] ([raw/notes/backend-implementation-details](../raw/notes/backend-implementation-details.md)) | Note | Complete backend file map, data types, views, test suite |
| [[frontend-integration-update\|Frontend Integration Update]] ([raw/notes/frontend-integration-update](../raw/notes/frontend-integration-update.md)) | Note | Frontend refactored: Express removed, Vite proxy to Django, hosSimulator deleted, apiTransform created |
| [[deployment-progress-update\|Deployment Progress Update]] ([raw/notes/deployment-progress-update](../raw/notes/deployment-progress-update.md)) | Note | Vercel deployment configuration — 7 commits, WSGI module fix, env-driven config, stateless DB, CORS port change |

## Stats

| Area | Count |
|---|---|
| Raw sources | 12 |
| Wiki articles | 9 |
| Uncompiled | 0 |
