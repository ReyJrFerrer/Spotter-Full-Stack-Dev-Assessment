---
title: "UI/UX Specifications"
type: source
summary: "UI/UX specifications for the Spotter Assessment frontend — design system, ELD log grid, map display"
tags: [ui, ux, design, react, eld, map]
date: 2026-06-22
confidence: high
source: ui-specifications.md
---

# UI/UX Specifications

**Source:** `ui-specifications.md` (project root)

## Global Design System

- **Framework:** Material UI (MUI) card-based layout
- **Typography:** Clean sans-serif (Inter/Roboto), tabular lining for all numerical data
- **Color Palette:**
  - Primary: High-trust tech blues
  - Accent: Electric blue / subtle neon purple (AI insights)
  - Functional: Vibrant Green (driving/compliant), Amber/Orange (near-limit warning), Crimson Red (violation/rest stops)
- **Theme Toggling:** Light Mode (data-dense) + True Dark Mode (#121212 for cabin glare prevention)

## Input Dashboard

- MUI card with fields: current location, pickup, dropoff, current cycle hours
- Primary blue CTA button for AI routing

## Results Dashboard 1: Map & Route

- Interactive map card with free map API
- AI-accent colors on route line (electric blue/purple)
- Stop callouts: Blue (pickup/dropoff/fueling), Amber/Red (HOS rests)
- Collapsible chronological itinerary list

## Results Dashboard 2: ELD Daily Log

- Multiple sheets in stacked MUI cards (pagination if >24h)
- 24-hour grid: Midnight-to-Midnight, hour markers + 15-min ticks
- 4 status rows: Off Duty, Sleeper Berth, Driving, On Duty
- Solid color-coded lines (Green for Driving, Red/Amber for resets)
- Header metadata: Date, Miles, Truck/Trailer, Carrier
- Remarks section with city/state + 45° flag mark
- Daily totals column (right side, tabular lining, sum=24)
