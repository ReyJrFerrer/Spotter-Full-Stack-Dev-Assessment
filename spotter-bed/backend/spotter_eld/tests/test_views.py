from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from spotter_eld.types import GeocodedLocation, RouteLeg


MOCK_LA = GeocodedLocation(
    label="Los Angeles, CA", city="Los Angeles", state="CA",
    lat=34.0522, lng=-118.2437,
)
MOCK_LV = GeocodedLocation(
    label="Las Vegas, NV", city="Las Vegas", state="NV",
    lat=36.1699, lng=-115.1398,
)
MOCK_SLC = GeocodedLocation(
    label="Salt Lake City, UT", city="Salt Lake City", state="UT",
    lat=40.7608, lng=-111.8910,
)
MOCK_LEGS = [
    RouteLeg(from_location=MOCK_LA, to_location=MOCK_LV, distance_miles=270, duration_hours=4.5),
    RouteLeg(from_location=MOCK_LV, to_location=MOCK_SLC, distance_miles=420, duration_hours=7.0),
]
MOCK_ROUTE_GEOMETRY = [(34.05, -118.24), (36.17, -115.14), (40.76, -111.89)]
MOCK_OSRM_RESULT = (MOCK_LEGS, MOCK_ROUTE_GEOMETRY)


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_returns_200(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_returns_json(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.headers["Content-Type"], "application/json")

    def test_health_has_status_key(self):
        response = self.client.get("/api/health/")
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "ok")


class TripGenerateEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        }
        self._geocode_patcher = patch(
            "spotter_eld.views.geocode_location",
            side_effect=lambda s: MOCK_LA if "Los" in s else MOCK_LV if "Vegas" in s else MOCK_SLC,
        )
        self._osrm_patcher = patch(
            "spotter_eld.views.osrm_route",
            return_value=MOCK_OSRM_RESULT,
        )
        self._geocode_mock = self._geocode_patcher.start()
        self._osrm_mock = self._osrm_patcher.start()

    def tearDown(self):
        self._geocode_patcher.stop()
        self._osrm_patcher.stop()

    def test_generate_trip_success_returns_200(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_generate_trip_returns_expected_structure(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        self.assertIn("current", data)
        self.assertIn("pickup", data)
        self.assertIn("dropoff", data)
        self.assertIn("legs", data)
        self.assertIn("total_distance_miles", data)
        self.assertIn("total_duration_hours", data)
        self.assertIn("itinerary", data)
        self.assertIn("daily_logs", data)
        self.assertIn("route_geometry", data)
        self.assertIsInstance(data["route_geometry"], list)

    def test_generate_trip_legs_is_array(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        self.assertIsInstance(data["legs"], list)
        self.assertEqual(len(data["legs"]), 2)

    def test_generate_trip_itinerary_not_empty(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        self.assertGreater(len(data["itinerary"]), 0)

    def test_generate_trip_daily_logs_not_empty(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        self.assertGreater(len(data["daily_logs"]), 0)

    def test_generate_trip_missing_field_returns_400(self):
        payload = {
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        }
        response = self.client.post(
            "/api/trips/generate/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_trip_invalid_type_returns_400(self):
        payload = {
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": "not-a-number",
        }
        response = self.client.post(
            "/api/trips/generate/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_trip_daily_log_has_24h_total(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        for log in data["daily_logs"]:
            total = sum(log["totals"].values())
            self.assertAlmostEqual(total, 24.0, places=1)

    def test_generate_trip_each_leg_has_distance(self):
        response = self.client.post(
            "/api/trips/generate/", self.valid_payload, format="json"
        )
        data = response.json()
        for leg in data["legs"]:
            self.assertGreater(leg["distance_miles"], 0)

    def test_cors_headers_present(self):
        response = self.client.options(
            "/api/trips/generate/",
            HTTP_ORIGIN="http://localhost:3000",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
