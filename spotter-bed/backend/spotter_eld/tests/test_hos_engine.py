from django.test import TestCase
from datetime import datetime, timezone, timedelta

from spotter_eld import hos_engine
from spotter_eld.types import DutyStatus, GeocodedLocation


class HOSEngineTests(TestCase):
    def setUp(self):
        self.los_angeles = GeocodedLocation(
            label="Los Angeles, CA",
            city="Los Angeles",
            state="CA",
            lat=34.0522,
            lng=-118.2437,
        )
        self.las_vegas = GeocodedLocation(
            label="Las Vegas, NV",
            city="Las Vegas",
            state="NV",
            lat=36.1699,
            lng=-115.1398,
        )
        self.salt_lake_city = GeocodedLocation(
            label="Salt Lake City, UT",
            city="Salt Lake City",
            state="UT",
            lat=40.7608,
            lng=-111.8910,
        )
        self.bakersfield = GeocodedLocation(
            label="Bakersfield, CA",
            city="Bakersfield",
            state="CA",
            lat=35.3733,
            lng=-119.0187,
        )
        self.start_time = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)

    def _run_engine(
        self, current, pickup, dropoff, cycle_used=0.0
    ):
        return hos_engine.simulate_trip(
            current=current,
            pickup=pickup,
            dropoff=dropoff,
            current_cycle_used=cycle_used,
            start_time_iso=self.start_time,
        )

    def test_duty_status_enum_values(self):
        """Verify four statuses exist."""
        self.assertEqual(DutyStatus.OFF, "OFF")
        self.assertEqual(DutyStatus.SB, "SB")
        self.assertEqual(DutyStatus.D, "D")
        self.assertEqual(DutyStatus.ON, "ON")

    def test_pre_trip_inspection_injected(self):
        """Every trip starts with a 15-min pre-trip inspection."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas
        )
        first = result.itinerary[0]
        self.assertEqual(first.status, DutyStatus.ON)
        self.assertIn("Pre-Trip", first.activity_name)
        self.assertAlmostEqual(first.duration_hours, 0.25, places=2)

    def test_pickup_injects_one_hour_on_duty(self):
        """Pickup event inserts 1 hour of On Duty."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas
        )
        pickup_items = [
            item
            for item in result.itinerary
            if item.status == DutyStatus.ON and "Loading" in item.activity_name
        ]
        self.assertEqual(len(pickup_items), 1)
        self.assertAlmostEqual(pickup_items[0].duration_hours, 1.0, places=2)

    def test_dropoff_injects_one_hour_on_duty(self):
        """Dropoff event inserts 1 hour of On Duty."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas
        )
        dropoff_items = [
            item
            for item in result.itinerary
            if item.status == DutyStatus.ON and "Unloading" in item.activity_name
        ]
        self.assertEqual(len(dropoff_items), 1)
        self.assertAlmostEqual(dropoff_items[0].duration_hours, 1.0, places=2)

    def test_short_trip_no_breaks(self):
        """Short trip under 8h generates no forced rest breaks."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas
        )
        off_items = [
            item
            for item in result.itinerary
            if item.status
            in (DutyStatus.OFF, DutyStatus.SB)
            and "Break" in item.activity_name
        ]
        self.assertEqual(len(off_items), 0)

    def test_30_min_break_after_8_hours_driving(self):
        """Trip over 8h driving injects a 30-min break."""
        # LA to Salt Lake City is a long leg (~590 miles, ~10h)
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        break_items = [
            item
            for item in result.itinerary
            if "30-Minute" in item.activity_name
        ]
        self.assertGreaterEqual(len(break_items), 1)
        self.assertAlmostEqual(break_items[0].duration_hours, 0.5, places=2)

    def test_trip_returns_route_legs(self):
        """Result contains two route legs with distances."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        self.assertEqual(len(result.legs), 2)
        self.assertGreater(result.legs[0].distance_miles, 0)
        self.assertGreater(result.legs[1].distance_miles, 0)

    def test_trip_returns_itinerary_with_sequence(self):
        """Itinerary items are in chronological order."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        self.assertGreater(len(result.itinerary), 0)
        for i in range(1, len(result.itinerary)):
            prev_end = datetime.fromisoformat(result.itinerary[i - 1].end_time)
            curr_start = datetime.fromisoformat(result.itinerary[i].start_time)
            self.assertGreaterEqual(
                curr_start, prev_end - timedelta(seconds=1)
            )

    def test_total_distance_positive(self):
        """Total distance is positive."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        self.assertGreater(result.total_distance_miles, 0)

    def test_high_cycle_used_triggers_34h_restart(self):
        """Cycle near limit triggers 34h restart."""
        result = self._run_engine(
            self.los_angeles,
            self.las_vegas,
            self.salt_lake_city,
            cycle_used=68.0,
        )
        restart_items = [
            item
            for item in result.itinerary
            if "34-Hour" in item.activity_name
        ]
        self.assertGreaterEqual(len(restart_items), 1)

    def test_itinerary_items_have_remarks(self):
        """Every itinerary item has a remarks string."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        for item in result.itinerary:
            self.assertTrue(item.remarks)

    def test_fueling_stop_every_1000_miles_no_stop_short_trip(self):
        """Short trip under 1000 miles has no fueling stop."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas
        )
        fuel_items = [
            item
            for item in result.itinerary
            if "Fueling" in item.activity_name
        ]
        self.assertEqual(len(fuel_items), 0)

    def test_zero_cycle_used_starts_fresh(self):
        """Zero cycle used means no initial restart needed."""
        result = self._run_engine(
            self.los_angeles, self.bakersfield, self.las_vegas, cycle_used=0.0
        )
        restart_items = [
            item
            for item in result.itinerary
            if "34-Hour" in item.activity_name or "10-Hour" in item.activity_name
        ]
        self.assertEqual(len(restart_items), 0)

    def test_pickup_location_matches(self):
        """Pickup location name appears in pickup event."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        pickup_items = [
            item
            for item in result.itinerary
            if "Loading" in item.activity_name
        ]
        self.assertIn("Las Vegas", pickup_items[0].location_name)

    def test_dropoff_location_matches(self):
        """Dropoff location name appears in dropoff event."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        dropoff_items = [
            item
            for item in result.itinerary
            if "Unloading" in item.activity_name
        ]
        self.assertIn("Salt Lake City", dropoff_items[0].location_name)

    def test_driving_segments_have_distance(self):
        """Driving segments report miles driven."""
        result = self._run_engine(
            self.los_angeles, self.las_vegas, self.salt_lake_city
        )
        driving_items = [
            item
            for item in result.itinerary
            if item.status == DutyStatus.D
        ]
        for item in driving_items:
            self.assertGreater(item.distance_miles, 0)
