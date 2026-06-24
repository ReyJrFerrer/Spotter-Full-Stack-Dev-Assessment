# Activity Log

## [2026-06-22] init | Wiki initialized with skill setup
- Created `.opencode/skills/llm-wiki/` based on Karpathy LLM Wiki pattern
- Initialized `.wiki/` with `_index.md`, `log.md`, `config.md`
- Created `AGENTS.md` with project architecture for AI coding agents

## [2026-06-22] ingest | Ingested project specification documents and codebase state
- Ingested 3 spec documents as raw/articles: backend-specifications, system-architecture, ui-specifications
- Ingested 2 codebase audit notes as raw/notes: project-codebase-state, tech-stack-details
- Created 4 concept pages: hours-of-service, eld-log-generation, trip-routing-engine, eld-log-grid
- Created 2 entity pages: frontend-components, backend-django
- Created 3 reference pages: project-architecture, api-specification, design-system
- Updated _index.md and log.md

## [2026-06-23] ingest | Ingested backend implementation into wiki
- Created 4 raw notes from actual codebase: hos-engine-implementation, eld-generator-implementation, geocoding-routing-implementation, backend-implementation-details
- Created backend-codebase-update note reflecting post-implementation state
- Rewrote concept pages (hours-of-service, eld-log-generation, trip-routing-engine) with actual Python implementation details
- Rewrote backend-django entity page with actual file map and class structure
- Rewrote api-specification and project-architecture references with DRF endpoint details
- Updated _index.md with new sources and updated summaries

## [2026-06-23] lint | Initial wiki health check
- Verified all 9 wiki articles have valid YAML frontmatter
- Verified all wikilinks resolve to existing files
- Checked for orphan pages and contradictions
- All pages properly cross-referenced; no orphans found

## [2026-06-23] ingest | Ingested frontend integration changes
- Ingested 1 raw note: frontend-integration-update
- Updated 3 wiki pages: frontend-components, project-architecture, api-specification
- Removed references to Express server, hosSimulator.ts from wiki articles
- Added apiTransform.ts layer documentation
- Updated _index.md with new source entry and stats

## [2026-06-23] lint | Frontend integration health check
- Verified all wiki articles updated with consistent integration information
- Checked for stale claims about Express server or hosSimulator (none found)
- Verified all 9 wiki articles + 11 raw sources have valid YAML frontmatter
- Verified all wikilinks resolve to existing files

## [2026-06-24] ingest | Ingested Vercel deployment progress
- Created 1 raw note from git commit analysis: deployment-progress-update
- Updated 2 wiki pages: project-architecture (added Vercel deployment section), backend-django (updated settings/wsgi/urls, deployment artifacts, Python version)
- Updated _index.md with new source entry and stats (12 raw sources)

## [2026-06-24] edit | Restrict CalculatedMap to US continental bounds
- Added Leaflet `maxBounds` (CONUS: [24,-126] → [50,-65]), `maxBoundsViscosity: 0.15`, `minZoom: 3` to map initialization options
- Created raw note: map-us-bounds-restriction
- Updated frontend-components wiki article with new map constraint details
- Updated _index.md with new source entry and stats (13 raw sources, 9 wiki articles, 0 uncompiled)

## [2026-06-24] edit | Nominatim autocomplete API + LocationAutocomplete component
- Backend: Added `nominatim_autocomplete()` with 300s TTL cache in geocoding.py, `LocationAutocompleteView` in views.py, new URL
- Frontend: Rewrote LocationAutocomplete to call backend API with 300ms debounce; removed static US_CITIES constant
- Changed backend error message "Could not geocode one or more locations" → "US cities and states only"
- Added Boston, NY, Atlanta to backend CITY_DATABASE
- Created raw note: nominatim-autocomplete-api
- Updated frontend-components, api-specification wiki articles
- Updated _index.md with new source entry and stats (14 raw sources, 9 wiki articles, 0 uncompiled)

## [2026-06-24] edit | Added scrollable static city list on autocomplete focus
- Recreated `usCities.ts` with 50 state capitals + top metros (~100 entries)
- Updated LocationAutocomplete to show `staticOptions` scrollable list when input is empty + focused
- When user types 2+ chars, switches to API-driven Nominatim results
- Updated frontend-components wiki article
