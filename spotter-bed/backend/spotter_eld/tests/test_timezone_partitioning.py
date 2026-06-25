from django.test import TestCase
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from spotter_eld import eld_generator
from spotter_eld.types import DutyStatus, ItineraryItem, GeocodedLocation


def _td(hours: float) -> timedelta:
    return timedelta(seconds=hours * 3600)


class TimezonePartitioningTests(TestCase):
    """Verify that daily log partitioning follows the trip's IANA timezone,
    not UTC, so that the driver's local midnight splits the log days."""

    def setUp(self):
        self.dropoff = GeocodedLocation(
            label="Los Angeles, CA",
            city="Los Angeles",
            state="CA",
            lat=34.0522,
            lng=-118.2437,
        )

    def _make_item(
        self,
        status: str,
        activity: str,
        start_utc: datetime,
        duration_hours: float,
        distance: float = 0.0,
        location: str = "En-Route",
    ) -> ItineraryItem:
        end = start_utc + _td(duration_hours)
        return ItineraryItem(
            id="item-tz",
            status=status,
            activity_name=activity,
            location_name=location,
            start_time=start_utc.isoformat(),
            end_time=end.isoformat(),
            duration_hours=duration_hours,
            distance_miles=distance,
            coordinates=(0.0, 0.0),
            remarks=f"{activity} in {location}",
        )

    def test_local_midnight_splits_log_in_local_tz(self):
        """An 8 PM Pacific trip start should appear on the local calendar date
        (not the next UTC day)."""
        pacific = ZoneInfo("America/Los_Angeles")
        start_local = datetime(2026, 6, 22, 20, 0, 0, tzinfo=pacific)
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
            self._make_item(DutyStatus.D, "Driving", start_utc + _td(0.25), 3.0, 180),
        ]
        end_utc = start_utc + _td(3.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/Los_Angeles",
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].date_string, "2026-06-22")
        self.assertEqual(logs[0].timezone, "America/Los_Angeles")

    def test_midnight_boundary_in_local_tz_differs_from_utc(self):
        """A trip that starts at 11 PM Pacific is on the next UTC day.
        With local timezone partitioning, the local day is preserved for
        trips that don't cross local midnight."""
        pacific = ZoneInfo("America/Los_Angeles")
        start_local = datetime(2026, 6, 22, 23, 0, 0, tzinfo=pacific)
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
            self._make_item(DutyStatus.D, "Driving", start_utc + _td(0.25), 0.5, 30),
        ]
        end_utc = start_utc + _td(0.75)

        logs_utc = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="UTC",
        )
        logs_local = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/Los_Angeles",
        )

        self.assertEqual(len(logs_utc), 1)
        self.assertEqual(logs_utc[0].date_string, "2026-06-23")
        self.assertEqual(len(logs_local), 1)
        self.assertEqual(logs_local[0].date_string, "2026-06-22")

    def test_remarks_time_label_in_local_tz(self):
        """Remarks time_label is rendered in the trip's local timezone."""
        eastern = ZoneInfo("America/New_York")
        start_local = datetime(2026, 6, 22, 6, 0, 0, tzinfo=eastern)
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
        ]
        end_utc = start_utc + _td(0.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/New_York",
        )

        remarks = logs[0].remarks
        self.assertEqual(remarks[0].time_label, "6:00 AM")

    def test_remarks_time_label_differs_from_utc(self):
        """When the local timezone is east of UTC, the time label should
        reflect local time, not UTC."""
        eastern = ZoneInfo("America/New_York")
        start_utc = datetime(2026, 6, 22, 6, 0, 0, tzinfo=ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
        ]
        end_utc = start_utc + _td(0.25)

        logs_utc = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="UTC",
        )

        itinerary_eastern = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
        ]
        logs_eastern = eld_generator.partition_into_daily_logs(
            itinerary=itinerary_eastern,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/New_York",
        )

        self.assertEqual(logs_utc[0].remarks[0].time_label, "6:00 AM")
        self.assertEqual(logs_eastern[0].remarks[0].time_label, "2:00 AM")

    def test_default_timezone_is_utc(self):
        """When trip_timezone is omitted, behavior is UTC-equivalent."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
        ]
        end_t = t + _td(0.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertEqual(logs[0].timezone, "UTC")
        self.assertEqual(logs[0].date_string, "2026-06-22")
        self.assertEqual(logs[0].remarks[0].time_label, "8:00 AM")

    def test_invalid_timezone_falls_back_to_utc(self):
        """An unknown IANA timezone string should not crash; it should
        gracefully fall back to UTC."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
        ]
        end_t = t + _td(0.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
            trip_timezone="Not/A_Real_Zone",
        )

        self.assertEqual(logs[0].timezone, "Not/A_Real_Zone")
        self.assertEqual(logs[0].date_string, "2026-06-22")

    def test_multi_day_trip_local_midnight_split(self):
        """A trip spanning two local days produces two log sheets split at
        local midnight."""
        pacific = ZoneInfo("America/Los_Angeles")
        start_local = datetime(2026, 6, 22, 22, 0, 0, tzinfo=pacific)
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
            self._make_item(DutyStatus.D, "Driving", start_utc + _td(0.25), 4.0, 240),
        ]
        end_utc = start_utc + _td(4.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/Los_Angeles",
        )

        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].date_string, "2026-06-22")
        self.assertEqual(logs[1].date_string, "2026-06-23")

    def test_first_block_starts_at_local_midnight_on_day_two(self):
        """The first block of day 2 should begin at hour 0.0 (local midnight)."""
        pacific = ZoneInfo("America/Los_Angeles")
        start_local = datetime(2026, 6, 22, 22, 0, 0, tzinfo=pacific)
        start_utc = start_local.astimezone(ZoneInfo("UTC"))
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", start_utc, 0.25),
            self._make_item(DutyStatus.D, "Driving", start_utc + _td(0.25), 4.0, 240),
        ]
        end_utc = start_utc + _td(4.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=start_utc,
            end_time=end_utc,
            dropoff=self.dropoff,
            trip_timezone="America/Los_Angeles",
        )

        day2_first_block = logs[1].timeline[0]
        self.assertAlmostEqual(day2_first_block.start_hour, 0.0, places=1)
