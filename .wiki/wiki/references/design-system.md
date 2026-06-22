---
title: "Design System Reference"
type: reference
summary: "UI/UX design system for the Spotter Assessment — colors, typography, theming, and layout conventions."
tags: [design, ui, ux, theming, colors, typography]
date: 2026-06-22
confidence: high
sources:
  - raw/articles/ui-specifications.md
  - raw/notes/project-codebase-state.md
---

# Design System Reference

## Current Implementation vs Spec

The current frontend uses a bespoke editorial design system with Tailwind CSS, not MUI as specified. The implemented look uses high-contrast black/cream/orange with shadow effects.

## Spec Colors

| Role | Color |
|---|---|
| Primary | High-trust tech blues |
| Accent (AI) | Electric blue / subtle neon purple |
| Driving/Compliant | Vibrant green |
| Near-limit warning | High-vis amber/orange |
| Violation/stop | Crimson red |

## Current Colors (as implemented)

| Role | Color | Hex |
|---|---|---|
| Background | Warm cream | `#F4F1ED` |
| Text/Accents | Near-black | `#1A1A1A` |
| Accent | Burnt orange | `#FF6B00` |
| Neutral | Warm gray | `#E8E4DF` |
| Grid bg | White | `#FFFFFF` |

## Typography

- **Font stack**: System sans-serif (editorial)
- **Tabular lining**: `font-mono` class for all numerical data
- **Headings**: Serif italic for brand (`font-serif italic font-black`)

## Theming

- **Current**: Light mode only (editorial aesthetic)
- **Spec requires**: True Dark Mode (#121212 background) for driver cabin use
- Dark mode not yet implemented

## Layout

- Max-width: 7xl (80rem / 1280px)
- Grid: 12-column for results (map+itinerary 7-col, logs 5-col)
- Heavy border + shadow effects (`shadow-[6px_6px_0px_#1A1A1A]`)
- Modular card-based sections

## Cross-References

- [[frontend-components|Frontend Components]] — component implementations
- [[eld-log-grid|ELD Log Grid]] — the primary data visualization
- [[project-architecture|Project Architecture]] — how design fits the system
