from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from spotter_eld.hos_engine import simulate_trip
from spotter_eld.types import GeocodedLocation
from datetime import datetime, timezone


class FullTripLifecycleTests(TestCase):
    """End-to-end integration tests using the HOS engine directly."""

    def setUp(self):
        self.la = GeocodedLocation(
            label="Los Angeles, CA", city="Los Angeles", state="CA",
            lat=34.0522, lng=-118.2437,
        )
        self.lv = GeocodedLocation(
            label="Las Vegas, NV", city="Las Vegas", state="NV",
            lat=36.1699, lng=-115.1398,
        )
        self.slc = GeocodedLocation(
            label="Salt Lake City, UT", city="Salt Lake City", state="UT",
            lat=40.7608, lng=-111.8910,
        )
        self.start = datetime(2026, 6, 22, 8, 0, 0, tzinfo=timezone.utc)

    def test_la_to_lv_to_slc_yields_itinerary(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        self.assertGreater(len(result.itinerary), 5)
        self.assertEqual(len(result.legs), 2)

    def test_itinerary_starts_with_pre_trip_and_ends_with_unload(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        self.assertIn("Pre-Trip", result.itinerary[0].activity_name)
        self.assertIn("Unloading", result.itinerary[-1].activity_name)

    def test_all_itinerary_times_are_chronological(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        for i in range(1, len(result.itinerary)):
            prev_end = datetime.fromisoformat(result.itinerary[i - 1].end_time)
            curr_start = datetime.fromisoformat(result.itinerary[i].start_time)
            self.assertGreaterEqual(curr_start, prev_end)

    def test_each_daily_log_totals_24(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        for log in result.daily_logs:
            total = sum(log.totals.values())
            self.assertAlmostEqual(total, 24.0, places=1)

    def test_daily_logs_have_remarks(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        for log in result.daily_logs:
            self.assertGreater(len(log.remarks), 0)

    def test_leg_distances_match_total(self):
        result = simulate_trip(
            current=self.la, pickup=self.lv, dropoff=self.slc,
            current_cycle_used=15.5, start_time_iso=self.start,
        )
        leg_sum = sum(leg.distance_miles for leg in result.legs)
        self.assertEqual(result.total_distance_miles, leg_sum)


class APIIntegrationTests(TestCase):
    """End-to-end tests hitting the API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        }

    def test_full_api_flow_returns_valid_structure(self):
        response = self.client.post(
            "/api/trips/generate/", self.payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn("current", data)
        self.assertEqual(data["current"]["city"], "Los Angeles")
        self.assertIn("pickup", data)
        self.assertEqual(data["pickup"]["city"], "Las Vegas")
        self.assertIn("dropoff", data)
        self.assertEqual(data["dropoff"]["city"], "Salt Lake City")
        self.assertGreater(len(data["itinerary"]), 0)
        self.assertGreater(len(data["daily_logs"]), 0)
        self.assertGreater(data["total_distance_miles"], 0)

    def test_api_health_endpoint(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_api_unknown_location_returns_error(self):
        payload = {
            "current_location": "NonExistentCity, XX",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        }
        response = self.client.post(
            "/api/trips/generate/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_empty_payload_returns_400(self):
        response = self.client.post(
            "/api/trips/generate/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_legs_have_expected_keys(self):
        response = self.client.post(
            "/api/trips/generate/", self.payload, format="json"
        )
        legs = response.json()["legs"]
        for leg in legs:
            self.assertIn("from_location", leg)
            self.assertIn("to_location", leg)
            self.assertIn("distance_miles", leg)
            self.assertIn("duration_hours", leg)

    def test_api_itinerary_items_have_required_fields(self):
        response = self.client.post(
            "/api/trips/generate/", self.payload, format="json"
        )
        items = response.json()["itinerary"]
        for item in items:
            self.assertIn("status", item)
            self.assertIn("activity_name", item)
            self.assertIn("start_time", item)
            self.assertIn("end_time", item)
            self.assertIn("coordinates", item)
            self.assertIn("remarks", item)

    def test_api_daily_logs_have_required_fields(self):
        response = self.client.post(
            "/api/trips/generate/", self.payload, format="json"
        )
        logs = response.json()["daily_logs"]
        for log in logs:
            self.assertIn("date_string", log)
            self.assertIn("date_label", log)
            self.assertIn("total_miles_driven", log)
            self.assertIn("timeline", log)
            self.assertIn("totals", log)
            self.assertIn("remarks", log)

    def test_api_returns_json_content_type(self):
        response = self.client.post(
            "/api/trips/generate/", self.payload, format="json"
        )
        self.assertEqual(
            response.headers["Content-Type"], "application/json"
        )
