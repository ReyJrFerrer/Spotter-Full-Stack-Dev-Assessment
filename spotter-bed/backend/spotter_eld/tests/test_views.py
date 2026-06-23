from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


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
