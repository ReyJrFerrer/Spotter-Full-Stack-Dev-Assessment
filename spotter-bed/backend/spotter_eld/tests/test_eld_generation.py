from django.test import TestCase
from datetime import datetime, timezone, timedelta

from spotter_eld import eld_generator
from spotter_eld.types import DutyStatus, ItineraryItem, GeocodedLocation


def _td(hours: float) -> timedelta:
    return timedelta(seconds=hours * 3600)


class PartitionIntoDailyLogsTests(TestCase):
    def setUp(self):
        self.dropoff = GeocodedLocation(
            label="Salt Lake City, UT",
            city="Salt Lake City",
            state="UT",
            lat=40.7608,
            lng=-111.8910,
        )

    def _make_item(
        self,
        status: str,
        activity: str,
        start: datetime,
        duration_hours: float,
        distance: float = 0.0,
        location: str = "Test Location",
    ) -> ItineraryItem:
        end = start + _td(duration_hours)
        return ItineraryItem(
            id="item-1",
            status=status,
            activity_name=activity,
            location_name=location,
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            duration_hours=duration_hours,
            distance_miles=distance,
            coordinates=(0.0, 0.0),
            remarks=f"{activity} in {location}",
        )

    def test_single_day_trip_returns_one_log(self):
        """Trip within a single day returns exactly one daily log."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 2.0, 120),
            self._make_item(DutyStatus.ON, "Loading", t + _td(2.25), 1.0),
            self._make_item(DutyStatus.D, "Driving", t + _td(3.25), 3.0, 180),
            self._make_item(DutyStatus.ON, "Unloading", t + _td(6.25), 1.0),
        ]
        end_t = t + _td(7.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertEqual(len(logs), 1)

    def test_multi_day_trip_returns_two_logs(self):
        """Trip spanning midnight returns two daily logs."""
        t = datetime(2026, 6, 22, 20, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(
                DutyStatus.D, "Driving", t + _td(0.25), 5.0, 300
            ),
            self._make_item(DutyStatus.ON, "Loading", t + _td(5.25), 1.0),
        ]
        end_t = t + _td(6.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertGreaterEqual(len(logs), 2)

    def test_each_day_totals_sum_to_24(self):
        """Each daily log totals sum to exactly 24 hours."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 2.0, 120),
            self._make_item(DutyStatus.ON, "Loading", t + _td(2.25), 1.0),
            self._make_item(DutyStatus.D, "Driving", t + _td(3.25), 3.0, 180),
            self._make_item(DutyStatus.ON, "Unloading", t + _td(6.25), 1.0),
        ]
        end_t = t + _td(7.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        for log in logs:
            total = sum(log.totals.values())
            self.assertAlmostEqual(total, 24.0, places=2)

    def test_gaps_filled_with_off_duty(self):
        """Gaps before first event and after last event are filled with OFF."""
        t = datetime(2026, 6, 22, 10, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(
                DutyStatus.D, "Driving", t, 2.0, 120
            ),
        ]
        end_t = t + _td(2.0)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertEqual(len(logs), 1)
        blocks = logs[0].timeline
        first_block = blocks[0]
        last_block = blocks[-1]

        self.assertEqual(first_block.status, DutyStatus.OFF)
        self.assertAlmostEqual(first_block.start_hour, 0.0, places=1)
        self.assertAlmostEqual(last_block.end_hour, 24.0, places=1)

    def test_totals_contain_all_statuses(self):
        """Totals dict has all four status keys."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 2.0, 120),
            self._make_item(DutyStatus.SB, "Sleep", t + _td(2.25), 1.0),
            self._make_item(DutyStatus.OFF, "Off", t + _td(3.25), 1.0),
            self._make_item(DutyStatus.D, "Driving", t + _td(4.25), 1.0, 60),
            self._make_item(DutyStatus.ON, "Unloading", t + _td(5.25), 1.0),
        ]
        end_t = t + _td(6.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        totals = logs[0].totals
        self.assertIn("OFF", totals)
        self.assertIn("SB", totals)
        self.assertIn("D", totals)
        self.assertIn("ON", totals)

    def test_remarks_generated_for_status_changes(self):
        """Remarks are generated at status transitions."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 2.0, 120),
            self._make_item(DutyStatus.ON, "Loading", t + _td(2.25), 1.0),
        ]
        end_t = t + _td(3.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertGreater(len(logs[0].remarks), 0)

    def test_date_string_format(self):
        """Date string is in YYYY-MM-DD format."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 1.0, 60),
        ]
        end_t = t + _td(1.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertEqual(logs[0].date_string, "2026-06-22")

    def test_miles_driven_tracked(self):
        """Miles driven in a day are tracked."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.D, "Driving", t, 2.0, 120),
        ]
        end_t = t + _td(2.0)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        self.assertEqual(logs[0].total_miles_driven, 120)

    def test_timeline_coords_on_quarter_hour_boundaries(self):
        """Timeline start/end hours are on 0.25 increments."""
        t = datetime(2026, 6, 22, 8, 7, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.23),
            self._make_item(
                DutyStatus.D, "Driving", t + _td(0.23), 1.37, 80
            ),
        ]
        end_t = t + _td(1.6)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
        )

        for block in logs[0].timeline:
            self.assertAlmostEqual(
                block.start_hour * 4, round(block.start_hour * 4), places=5
            )
            self.assertAlmostEqual(
                block.end_hour * 4, round(block.end_hour * 4), places=5
            )

    def test_carrier_metadata_passed_through(self):
        """Carrier name and truck/trailer numbers appear in daily logs."""
        t = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)
        itinerary = [
            self._make_item(DutyStatus.ON, "Pre-Trip", t, 0.25),
            self._make_item(DutyStatus.D, "Driving", t + _td(0.25), 1.0, 60),
        ]
        end_t = t + _td(1.25)

        logs = eld_generator.partition_into_daily_logs(
            itinerary=itinerary,
            start_time=t,
            end_time=end_t,
            dropoff=self.dropoff,
            carrier_name="Test Carrier",
            tractor_number="TRK-001",
            trailer_number="TRL-002",
        )

        self.assertEqual(logs[0].carrier_name, "Test Carrier")
        self.assertEqual(logs[0].tractor_number, "TRK-001")
        self.assertEqual(logs[0].trailer_number, "TRL-002")
