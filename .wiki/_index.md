# Spotter Assessment Wiki

> LLM-compiled knowledge base for the Spotter Assessment project.

## Wiki Info

- **Root**: `.wiki/`
- **Created**: 2026-06-22
- **Last updated**: 2026-06-22
- **Last lint**: Never

## Index

### Concepts

| Page | Summary |
|---|---|
| [[hours-of-service\|FMCSA HOS Rules]] ([concepts/hours-of-service](wiki/concepts/hours-of-service.md)) | FMCSA Hours of Service regulations — duty statuses, 11/14/70-hour limits, 30-min break, fueling requirements |
| [[eld-log-generation\|ELD Log Data Generation]] ([concepts/eld-log-generation](wiki/concepts/eld-log-generation.md)) | Trip timeline partitioning into 24-hour daily log sheets with 15-min grid coordinates |
| [[trip-routing-engine\|Trip Routing Engine]] ([concepts/trip-routing-engine](wiki/concepts/trip-routing-engine.md)) | Core algorithm: geocoding, route legs, iterative HOS scheduling loop |
| [[eld-log-grid\|ELD Log Grid]] ([concepts/eld-log-grid](wiki/concepts/eld-log-grid.md)) | Standardized 24-hour SVG grid for duty status visualization |

### Entities

| Page | Summary |
|---|---|
| [[frontend-components\|Frontend Components]] ([entities/frontend-components](wiki/entities/frontend-components.md)) | React components: TripDetailsForm, CalculatedMap, ItineraryPanel, EldLogSheets |
| [[backend-django\|Django Backend Structure]] ([entities/backend-django](wiki/entities/backend-django.md)) | Current scaffolded Django project and planned DRF implementation |

### References

| Page | Summary |
|---|---|
| [[project-architecture\|Project Architecture Reference]] ([references/project-architecture](wiki/references/project-architecture.md)) | Complete system architecture overview — React frontend, Express/Django API, HOS engine |
| [[api-specification\|API Specification]] ([references/api-specification](wiki/references/api-specification.md)) | Current Express API endpoints and planned Django DRF endpoint |
| [[design-system\|Design System Reference]] ([references/design-system](wiki/references/design-system.md)) | UI/UX design system — colors, typography, theming, layout conventions |

### Sources

| Page | Type | Summary |
|---|---|---|
| [[backend-specifications\|Backend Specifications]] ([raw/articles/backend-specifications](../raw/articles/backend-specifications.md)) | Article | Django DRF API spec with FMCSA HOS rules |
| [[system-architecture\|System Architecture]] ([raw/articles/system-architecture](../raw/articles/system-architecture.md)) | Article | React + Django architecture with CORS, deployment |
| [[ui-specifications\|UI/UX Specifications]] ([raw/articles/ui-specifications](../raw/articles/ui-specifications.md)) | Article | MUI design system, ELD grid, map, theming |
| [[project-codebase-state\|Project Codebase State]] ([raw/notes/project-codebase-state](../raw/notes/project-codebase-state.md)) | Note | Current codebase snapshot — what exists vs. what's missing |
| [[tech-stack-details\|Tech Stack Details]] ([raw/notes/tech-stack-details](../raw/notes/tech-stack-details.md)) | Note | Technology versions and dependencies |

## Stats

| Area | Count |
|---|---|
| Raw sources | 5 |
| Wiki articles | 9 |
| Uncompiled | 0 |
