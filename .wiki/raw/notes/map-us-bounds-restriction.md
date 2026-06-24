---
title: "Map US Bounds Restriction"
type: note
summary: "Leaflet map restricted to continental US with maxBounds, minZoom, and viscosity"
tags: [map, leaflet, us-bounds, geolimiting]
date: 2026-06-24
confidence: high
sources: []
---

# Map US Bounds Restriction

## Summary

The CalculatedMap component was updated to restrict the interactive Leaflet map to the continental United States (CONUS). Users cannot pan or zoom beyond US borders.

## Implementation

**File:** `spotter-fed/src/components/CalculatedMap.tsx`

### US Bounds Definition

A `US_BOUNDS` constant defines the southwest-to-northeast bounding box:

```typescript
const US_BOUNDS: L.LatLngBoundsExpression = [
  [24.0, -126.0],  // Southwest (padded)
  [50.0, -65.0]    // Northeast (padded)
];
```

These coordinates encompass the 48 contiguous states with slight padding to avoid clipping at the borders.

### Map Options

Three Leaflet map options enforce the restriction:

| Option | Value | Effect |
|---|---|---|
| `maxBounds` | `US_BOUNDS` | Geographic bounding box the camera cannot exceed |
| `maxBoundsViscosity` | `0.15` | Soft resistance at edges; user feels friction but can briefly overshoot before bouncing back |
| `minZoom` | `3` | Prevents zooming out so far that the US becomes a tiny portion of the viewport |

### Behavior

- **Panning:** Drag attempts beyond the bounds encounter resistance and snap back
- **Zooming:** Zoom level cannot drop below 3; max zoom remains 19 (tile server limit)
- **Recenter button:** Unaffected — still fits bounds to route markers within US

## Reasoning

The application is a US FMCSA-compliant ELD trucking tool. Routes, pickup/dropoff locations, and HOS stops all operate within US territory. Restricting the map prevents confusion, keeps the UI focused, and avoids rendering empty ocean/foreign territory once markers are placed.
