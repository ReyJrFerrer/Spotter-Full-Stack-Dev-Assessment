from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from spotter_eld.utils import (
    round_to_quarter_hour,
    format_time_label,
    format_date_label,
    format_date_string,
    resolve_timezone,
    to_local,
)
from spotter_eld.types import (
    DutyStatus,
    GeocodedLocation,
    ItineraryItem,
    DailyLogSheet,
    TimelineBlock,
    DailyLogRemarks,
)


def partition_into_daily_logs(
    itinerary: List[ItineraryItem],
    start_time: datetime,
    end_time: datetime,
    dropoff: GeocodedLocation,
    carrier_name: str = "",
    tractor_number: str = "",
    trailer_number: str = "",
    trip_timezone: str = "UTC",
) -> List[DailyLogSheet]:
    tz = resolve_timezone(trip_timezone)

    if start_time.tzinfo is None:
        # Naive datetime: interpret in the trip timezone.
        start_time = start_time.replace(tzinfo=tz)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=tz)

    start_local = to_local(start_time, tz)
    end_local = to_local(end_time, tz)

    day_start = start_local.replace(hour=0, minute=0, second=0, microsecond=0)

    daily_logs: List[DailyLogSheet] = []
    target_date = day_start

    while target_date <= end_local:
        next_date = target_date + timedelta(days=1)

        target_start_ms = target_date.timestamp() * 1000
        target_end_ms = next_date.timestamp() * 1000

        day_timeline: List[TimelineBlock] = []
        day_remarks: List[DailyLogRemarks] = []
        miles_driven_today = 0.0
        last_mapped_hour = 0.0

        for item in itinerary:
            item_start = datetime.fromisoformat(item.start_time)
            item_end = datetime.fromisoformat(item.end_time)
            if item_start.tzinfo is None:
                item_start = item_start.replace(tzinfo=ZoneInfo("UTC"))
            if item_end.tzinfo is None:
                item_end = item_end.replace(tzinfo=ZoneInfo("UTC"))

            item_start_ms = item_start.timestamp() * 1000
            item_end_ms = item_end.timestamp() * 1000

            if item_end_ms <= target_start_ms or item_start_ms >= target_end_ms:
                continue

            overlap_start_ms = max(target_start_ms, item_start_ms)
            overlap_end_ms = min(target_end_ms, item_end_ms)

            start_hour_raw = (overlap_start_ms - target_start_ms) / (1000 * 60 * 60)
            end_hour_raw = (overlap_end_ms - target_start_ms) / (1000 * 60 * 60)

            start_hour = round_to_quarter_hour(start_hour_raw)
            end_hour = round_to_quarter_hour(end_hour_raw)

            if end_hour <= start_hour:
                continue

            if start_hour > last_mapped_hour:
                day_timeline.append(
                    TimelineBlock(
                        status=DutyStatus.OFF,
                        start_hour=last_mapped_hour,
                        end_hour=start_hour,
                        location_name=item.location_name,
                        remarks="Off Duty",
                    )
                )

            day_timeline.append(
                TimelineBlock(
                    status=item.status,
                    start_hour=start_hour,
                    end_hour=end_hour,
                    location_name=item.location_name,
                    remarks=item.remarks,
                )
            )

            if item.status == DutyStatus.D:
                item_duration_ms = item_end_ms - item_start_ms
                overlap_duration_ms = overlap_end_ms - overlap_start_ms
                fraction = overlap_duration_ms / item_duration_ms if item_duration_ms > 0 else 0
                miles_driven_today += item.distance_miles * fraction

            if item_start_ms >= target_start_ms and item_start_ms < target_end_ms:
                day_remarks.append(
                    DailyLogRemarks(
                        time_label=format_time_label(item_start, tz),
                        status=item.status,
                        location=item.location_name,
                        remarks_text=item.remarks or item.activity_name,
                    )
                )

            last_mapped_hour = end_hour

        if last_mapped_hour < 24.0:
            last_location = (
                itinerary[-1].location_name
                if itinerary
                else f"{dropoff.city}, {dropoff.state}"
            )
            day_timeline.append(
                TimelineBlock(
                    status=DutyStatus.OFF,
                    start_hour=last_mapped_hour,
                    end_hour=24.0,
                    location_name=last_location,
                    remarks="Off Duty (Trip complete or idle)",
                )
            )

        off_sum = 0.0
        sb_sum = 0.0
        d_sum = 0.0
        on_sum = 0.0

        for block in day_timeline:
            dur = block.end_hour - block.start_hour
            if block.status == DutyStatus.OFF:
                off_sum += dur
            elif block.status == DutyStatus.SB:
                sb_sum += dur
            elif block.status == DutyStatus.D:
                d_sum += dur
            elif block.status == DutyStatus.ON:
                on_sum += dur

        total = off_sum + sb_sum + d_sum + on_sum
        if abs(total - 24.0) > 0.001:
            diff = 24.0 - total
            off_sum += diff
            if day_timeline:
                day_timeline[-1].end_hour = 24.0

        daily_logs.append(
            DailyLogSheet(
                date_string=format_date_string(target_date, tz),
                date_label=format_date_label(target_date, tz),
                total_miles_driven=round(miles_driven_today),
                tractor_number=tractor_number,
                trailer_number=trailer_number,
                carrier_name=carrier_name,
                timeline=day_timeline,
                totals={
                    "OFF": round_to_quarter_hour(off_sum),
                    "SB": round_to_quarter_hour(sb_sum),
                    "D": round_to_quarter_hour(d_sum),
                    "ON": round_to_quarter_hour(on_sum),
                },
                remarks=day_remarks,
                timezone=trip_timezone,
            )
        )

        target_date = next_date

    return daily_logs
