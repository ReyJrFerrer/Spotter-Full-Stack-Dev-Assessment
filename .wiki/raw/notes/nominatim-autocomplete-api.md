---
title: "Nominatim Autocomplete API"
type: note
summary: "Backend endpoint and frontend component for Nominatim-powered US city autocomplete"
tags: [backend, frontend, autocomplete, nominatim, geocoding, api]
date: 2026-06-24
confidence: high
sources: []
---

# Nominatim Autocomplete API

## Summary

Added a `GET /api/locations/autocomplete/?q=query` endpoint that proxies Nominatim's search API (filtered to US only with `countrycodes=us`) and returns matching incorporated places as typed-ahead suggestions. The frontend `LocationAutocomplete` component consumes this endpoint with 300ms debounce.

## Backend Implementation

**File:** `spotter-bed/backend/spotter_eld/geocoding.py`

### Key Additions

| Addition | Description |
|---|---|
| `STATE_ABBREVIATIONS` | Dict mapping full state names (e.g. "california") to USPS codes ("CA") |
| `_AUTOCOMPLETE_CACHE` | Dict-based TTL cache (300s) to respect Nominatim's 1 req/sec rate limit |
| `_fetch_json_list()` | Variant of `_fetch_json` that returns a list instead of dict |
| `_extract_city()` | Extracts city name from Nominatim `address` object, trying keys: city, town, village, hamlet, municipality, county |
| `_extract_state_abbr()` | Maps full state name to USPS abbreviation |
| `_serialize_autocomplete()` | Filters Nominatim results to place/boundary types (city, town, village, etc.) and serializes to `{label, city, state, lat, lng}` |
| `nominatim_autocomplete()` | Main function: checks TTL cache → calls Nominatim with `addressdetails=1&countrycodes=us&limit=10` → filters → caches |

### API Endpoint

**`GET /api/locations/autocomplete/?q=los`**

Response:
```json
[
  {"label": "Los Angeles, CA", "city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437},
  {"label": "Los Gatos, CA", "city": "Los Gatos", "state": "CA", "lat": 37.2266, "lng": -121.9747}
]
```

## Frontend Implementation

**File:** `spotter-fed/src/components/LocationAutocomplete.tsx`

Key changes from static list to API-driven:

- Removed `options` prop, added `apiUrl` prop pointing to backend autocomplete endpoint
- 300ms debounce on keystroke before calling API
- Request ID counter (`requestIdRef`) prevents stale responses from out-of-order API calls
- Loading spinner shown during fetch
- "No matching US city found" for empty results
- "Could not fetch cities" for network errors
- Requires minimum 2 characters before triggering a search

**File:** `spotter-fed/src/components/TripDetailsForm.tsx`

- Computes `AUTOCOMPLETE_URL` from `VITE_API_URL` env var
- Passes `apiUrl` to all three `LocationAutocomplete` instances (current, pickup, dropoff)
- Removed static `US_CITIES` import and `constants/usCities.ts` file
