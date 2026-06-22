---
title: "ELD Log Grid"
type: concept
summary: "Standardized 24-hour grid for visualizing duty status changes with horizontal/vertical line segments, 15-minute ticks, and daily totals."
tags: [eld, grid, svg, visualization, log-sheet]
date: 2026-06-22
confidence: high
sources:
  - raw/articles/ui-specifications.md
  - raw/notes/project-codebase-state.md
---

# ELD Log Grid

The ELD Log Grid is a visual representation of a driver's 24-hour duty status timeline, rendered as an SVG graphic.

## Grid Structure

- **Dimensions**: 800×180px viewBox (scalable)
- **Time axis**: Midnight to Midnight, hours labeled (M = Midnight, N = Noon)
- **Vertical lines**: Hour lines (bold), 15/30/45-minute tick lines (subtle)
- **Rows**: 4 horizontal lanes for Off Duty, Sleeper Berth, Driving, On Duty

## Line Drawing

Solid horizontal line segments are drawn at the midpoint of each row, spanning the duration of each duty block. Vertical lines connect transitions between statuses, creating a continuous path across the grid.

## Right-Side Totals Column

Each of the 4 rows has a total hours value displayed on the right, formatted with tabular lining. The footer displays "24.00 hr" as certification.

## Header Information

Above the grid: Date label, carrier name, tractor/trailer numbers, total miles driven today.

## Remarks Section

Below the grid: A table listing each duty status change with:
- Time
- Status badge
- Location (city/state)
- Remarks text

## Implementation

Rendered by the `EldLogSheets` component in `spotter-fed/src/components/EldLogSheets.tsx`. Supports pagination when the trip spans multiple days.

## Cross-References

- [[eld-log-generation|ELD Log Data Generation]] — the data that feeds the grid
- [[frontend-components|Frontend Components]] — `EldLogSheets` component details
