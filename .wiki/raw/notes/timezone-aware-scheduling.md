---
title: "Timezone-Aware Trip Scheduling"
type: note
summary: "Frontend calendar/timezone picker + backend IANA timezone support for consistent itinerary and ELD log display across the dispatch tool."
tags: [timezone, fix, ita, frontend, backend, eld, dispatch]
date: 2026-06-25
confidence: high
source: "bug fix from user-reported issue (Itinerary vs ELD log time mismatch; driver starting on-duty at 12 AM)"
---

# Timezone-Aware Trip Scheduling

## Motivation

User reported two related bugs:

1. **Itinerary and ELD logs showed different times** for the same events.
2. **Driver started on-duty around 12 AM** (midnight) — unrealistic for a real commercial shift.

After the first round of fixes, the user reported a follow-up: **the first (auto-mount) calculation matched the picked date/time, but the second (form-submit) calculation rolled the date back to yesterday and the departure time to 10 PM**.

### Root Causes (round 1 — fixed)

1. `spotter-bed/backend/spotter_eld/views.py:64` hardcoded `start_time_iso=datetime.now(timezone.utc)`. When the API was called near midnight UTC, the pre-trip inspection would be at 00:00 UTC. The user had no control over the start time.
2. `App.tsx:32,47-52` collected `startTime` from the form (default `new Date().toISOString()`) but never sent it to the backend. The backend always used UTC, breaking the consistency contract.
3. `ItineraryPanel.tsx:84-86` used `toLocaleTimeString()` which converted UTC to **browser local time**.
4. `EldLogSheets.tsx` consumed `block.startHour` (hours-since-midnight) computed by `eld_generator.py:32-33` using `start_time.year/month/day` in **UTC**.
5. Net effect: itinerary showed local clock time; ELD grid was dated/sliced by UTC midnight. Date labels and times did not agree.

### Root Cause (round 2 — second-submit regression)

The form's `handleFormSubmit` did:

```ts
const localIso = new Date(`${startDate}T${startTimeOfDay}:00`).toISOString();
```

`new Date("2026-06-22T06:00:00")` is parsed as **browser local time** and `.toISOString()` returns the **UTC** representation. Meanwhile, the form's timezone selector defaulted to `"UTC"` whenever the browser IANA zone was not in the curated US list (e.g. a user in `Asia/Singapore` at UTC+8).

Trace for a user in Singapore picking 2026-06-22 06:00 with the form's timezone stuck on `UTC`:
- Form converts: 06:00 Singapore = `2026-06-21T22:00:00.000Z`
- Backend receives: `start_time = 2026-06-21 22:00 UTC`, `timezone = "UTC"`
- Backend partitions at UTC midnight → ELD dated `2026-06-21`, remarks show `10:00 PM`

The first (auto-mount) calculation worked because `App.tsx` used `tripTimezone` from its own state (browser-detected IANA = `Asia/Singapore`), so the backend re-projected correctly.

Additionally, DRF's built-in `DateTimeField` silently interprets an ISO string without an offset as **UTC** (not naive). This meant the naive intent of the form was lost at the serializer boundary.

## Solution Summary

A single IANA timezone string (`America/Los_Angeles`, `UTC`, etc.) anchors the entire trip. All timeline coordinates, ELD date splits, and display formatting use that timezone as the source of truth.

### Backend Changes

- `spotter_eld/utils.py` — Added `resolve_timezone()` and `to_local()` helpers. `format_time_label`, `format_date_label`, `format_date_string` now accept an optional `ZoneInfo` and convert to local time before formatting.
- `spotter_eld/serializers.py` — `TripInputSerializer` now accepts optional `start_time` (ISO) and `timezone` (IANA). Invalid IANA names return 400.
- `spotter_eld/views.py` — `TripGenerateView` reads `start_time` and `timezone` from the payload, falls back to `datetime.now(UTC)` and `"UTC"`, and propagates them through `_serialize_result()`. Response includes a top-level `timezone` plus per-log `timezone`.
- `spotter_eld/hos_engine.py` — `simulate_trip()` accepts `trip_timezone`, attaches it to the `TripGenerationResult`, and threads it to the daily-log partitioner.
- `spotter_eld/eld_generator.py` — `partition_into_daily_logs()` converts the start time to the trip timezone, then walks day boundaries at **local midnight**. All remarks time labels and date labels are rendered in that local zone. Trip `timezone` echoed on each `DailyLogSheet`.
- `spotter_eld/types.py` — `TripGenerationResult` and `DailyLogSheet` gained a `timezone: str` field (default `"UTC"` for backward compatibility).

### Frontend Changes

- `spotter-fed/src/types.ts` — `TripInputs` gains `timezone`. `TripGenerationResult` and `DailyLogSheet` carry `timezone`.
- `spotter-fed/src/components/TripDetailsForm.tsx` — Replaced the single `datetime-local` field with a dedicated **Dispatch Schedule** block containing a calendar (`<input type="date">`), time picker (`<input type="time">` with 15-min steps), and a timezone `<select>` (Pacific, Mountain, Central, Eastern, Alaska, Hawaii, UTC). The form auto-detects the browser timezone via `Intl.DateTimeFormat().resolvedOptions().timeZone` and surfaces the UTC offset. Default start time is now **today at 06:00 local** (realistic for a commercial pre-trip).
- `spotter-fed/src/utils/apiTransform.ts` — Maps the new `timezone` field from `data.timezone` and per-log `log.timezone`. Defaults to `"UTC"` if missing.
- `spotter-fed/src/App.tsx` — Sends `start_time` and `timezone` in the POST body. Uses the browser-detected timezone on initial load.
- `spotter-fed/src/components/ItineraryPanel.tsx` — Accepts a `tripTimezone` prop and passes `timeZone: tripTimezone` to `toLocaleTimeString()` / `toLocaleDateString()`. Shows a globe icon + IANA name in the header so the user knows which clock is being shown.
- `spotter-fed/src/components/EldLogSheets.tsx` — Displays the active log's IANA timezone in a metadata strip below the carrier info. Backend-provided `time_label` is already in the trip zone, so display naturally agrees.

## Behavior After Fix

- A driver who picks **"Departure Date: 2026-06-22, Time: 06:00, Timezone: America/Los_Angeles"** will see the pre-trip inspection at 6:00 AM in the Itinerary and the first ELD log dated `2026-06-22` with the first status block at hour 6.0. ELD `time_label` for that block reads `6:00 AM`.
- A Pacific-coast driver calling the API at 23:00 local will see the trip start at 11:00 PM local, not 7:00 AM the next day in UTC. ELD log is correctly dated `2026-06-22`, not `2026-06-23`.
- The Itinerary and ELD grids show the **same wall-clock time and date** because both consume the same trip-anchored timezone.

## Test Coverage

- New file `tests/test_timezone_partitioning.py` — 8 tests covering local midnight split, multi-day trips, remarks time labels in local TZ, UTC fallback, invalid TZ fallback.
- `tests/test_views.py` — 3 new endpoint tests: accept `start_time`+`timezone`, default to UTC, reject invalid IANA names.
- All 142 previously-passing tests still pass. The single pre-existing CORS test failure is unrelated to this change.

## Default UI State

| Field | Default |
|---|---|
| Departure Date | Today (browser local) |
| Departure Time | 06:00 local |
| Timezone | Browser-detected IANA (falls back to UTC select option) |
| Browser detected hint | `<IANA> (UTC±HH:MM)` shown under the picker |

## Cross-References

- [[hours-of-service|FMCSA HOS Rules]] — constraints enforced regardless of timezone
- [[eld-log-generation|ELD Log Data Generation]] — partitioning now follows trip local midnight
- [[trip-routing-engine|Trip Routing Engine]] — engine accepts trip timezone
- [[api-specification|API Specification]] — request/response includes timezone
- [[frontend-components|Frontend Components]] — TripDetailsForm, ItineraryPanel, EldLogSheets
