---
title: "Tech Stack Details"
type: source
summary: "Detailed technology versions and dependencies used across the project"
tags: [tech-stack, dependencies, versions]
date: 2026-06-22
confidence: high
source: manual codebase audit
---

# Tech Stack Details

## Frontend (`spotter-fed/package.json`)

| Dependency | Version |
|---|---|
| React | ^19.0.1 |
| TypeScript | ~5.8.2 |
| Vite | ^6.2.3 |
| Express | ^4.21.2 |
| Tailwind CSS | ^4.1.14 |
| Leaflet | ^1.9.4 |
| @google/genai | ^2.4.0 |
| lucide-react | ^0.546.0 |
| motion | ^12.23.24 |
| dotenv | ^17.2.3 |

### Dev Dependencies
| Dependency | Version |
|---|---|
| tsx | ^4.21.0 |
| esbuild | ^0.25.0 |
| @types/express | ^4.17.21 |
| @types/leaflet | ^1.9.21 |
| @types/node | ^22.14.0 |
| autoprefixer | ^10.4.21 |

## Backend (`spotter-bed/Pipfile`)

| Dependency | Version |
|---|---|
| Python | 3.14 |
| Django | * (latest = 6.0.6 installed) |

**Note:** DRF and django-cors-headers are not yet installed.

## Scripts

### Frontend
- `npm run dev` — runs `tsx server.ts` (Express + Vite dev middleware)
- `npm run build` — Vite build + esbuild server bundle
- `npm run start` — run production server
- `npm run lint` — `tsc --noEmit` type check

### Backend
- Standard Django manage.py commands
