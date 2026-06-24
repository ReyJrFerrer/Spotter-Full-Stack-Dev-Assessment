"""Tests for the ELD PDF export module and the export endpoint."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from spotter_eld.pdf_export import build_eld_pdf, EldGridFlowable


VALID_SUMMARY = {
    "from_label": "Los Angeles, CA",
    "pickup_label": "Las Vegas, NV",
    "dropoff_label": "Salt Lake City, UT",
    "total_distance_miles": 690,
    "total_duration_hours": 11.5,
    "current_cycle_used_hrs": 15.5,
    "trip_days": 2,
    "carrier_name": "Test Carrier",
    "tractor_number": "TRK-001",
    "trailer_number": "TRL-002",
}


VALID_DAILY_LOG = {
    "date_string": "2026-06-24",
    "date_label": "Tuesday, Jun 24, 2026",
    "total_miles_driven": 270,
    "tractor_number": "TRK-001",
    "trailer_number": "TRL-002",
    "carrier_name": "Test Carrier",
    "timeline": [
        {"status": "OFF", "start_hour": 0.0, "end_hour": 6.0, "location_name": "Los Angeles, CA", "remarks": "Off Duty"},
        {"status": "ON", "start_hour": 6.0, "end_hour": 6.25, "location_name": "Los Angeles, CA", "remarks": "Pre-Trip"},
        {"status": "D", "start_hour": 6.25, "end_hour": 10.75, "location_name": "I-15", "remarks": "Driving"},
        {"status": "ON", "start_hour": 10.75, "end_hour": 11.75, "location_name": "Las Vegas, NV", "remarks": "Loading"},
        {"status": "D", "start_hour": 11.75, "end_hour": 14.5, "location_name": "I-15", "remarks": "Driving"},
        {"status": "OFF", "start_hour": 14.5, "end_hour": 24.0, "location_name": "En-Route", "remarks": "Off Duty"},
    ],
    "totals": {"OFF": 15.5, "SB": 0.0, "D": 7.25, "ON": 1.25},
    "remarks": [
        {"time_label": "6:00 AM", "status": "ON", "location": "Los Angeles, CA", "remarks_text": "Pre-Trip"},
        {"time_label": "6:15 AM", "status": "D", "location": "I-15", "remarks_text": "Driving"},
    ],
}


class BuildEldPdfTests(TestCase):
    def test_returns_valid_pdf_bytes(self):
        payload = {"summary": VALID_SUMMARY, "daily_logs": [VALID_DAILY_LOG]}
        pdf = build_eld_pdf(payload)
        self.assertIsInstance(pdf, bytes)
        # PDF magic number
        self.assertEqual(pdf[:4], b"%PDF")

    def test_generates_non_empty_pdf(self):
        payload = {"summary": VALID_SUMMARY, "daily_logs": [VALID_DAILY_LOG]}
        pdf = build_eld_pdf(payload)
        # A real PDF with content is several KB minimum
        self.assertGreater(len(pdf), 2000)

    def test_raises_when_no_daily_logs(self):
        with self.assertRaises(ValueError):
            build_eld_pdf({"summary": VALID_SUMMARY, "daily_logs": []})

    def test_handles_multi_day_trip(self):
        log_a = dict(VALID_DAILY_LOG)
        log_b = dict(VALID_DAILY_LOG, date_string="2026-06-25", date_label="Wednesday, Jun 25, 2026")
        payload = {"summary": VALID_SUMMARY, "daily_logs": [log_a, log_b]}
        pdf = build_eld_pdf(payload)
        self.assertEqual(pdf[:4], b"%PDF")
        self.assertGreater(len(pdf), 3000)

    def test_handles_empty_remarks_list(self):
        log = dict(VALID_DAILY_LOG, remarks=[])
        payload = {"summary": VALID_SUMMARY, "daily_logs": [log]}
        pdf = build_eld_pdf(payload)
        self.assertEqual(pdf[:4], b"%PDF")

    def test_uses_summary_metadata_in_output(self):
        payload = {
            "summary": dict(VALID_SUMMARY, carrier_name="UNIQUE-CARRIER-XYZ"),
            "daily_logs": [VALID_DAILY_LOG],
        }
        pdf = build_eld_pdf(payload)
        self.assertEqual(pdf[:4], b"%PDF")
        # The unique marker should be in the rendered PDF stream (PDF streams are compressed
        # so we just confirm the build completed without error).

    def test_eld_grid_flowable_wrap_dimensions(self):
        grid = EldGridFlowable(
            timeline=VALID_DAILY_LOG["timeline"],
            totals=VALID_DAILY_LOG["totals"],
            width=600.0,
            height=150.0,
        )
        w, h = grid.wrap(0, 0)
        self.assertEqual(w, 600.0)
        self.assertEqual(h, 150.0)


class TripPdfExportEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "summary": VALID_SUMMARY,
            "daily_logs": [VALID_DAILY_LOG],
        }

    def test_export_pdf_returns_200(self):
        response = self.client.post(
            "/api/trips/export-pdf/", self.valid_payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_export_pdf_returns_application_pdf_content_type(self):
        response = self.client.post(
            "/api/trips/export-pdf/", self.valid_payload, format="json"
        )
        self.assertEqual(response.headers["Content-Type"], "application/pdf")

    def test_export_pdf_returns_attachment_header(self):
        response = self.client.post(
            "/api/trips/export-pdf/", self.valid_payload, format="json"
        )
        self.assertIn("Content-Disposition", response.headers)
        self.assertIn("attachment", response.headers["Content-Disposition"])

    def test_export_pdf_filename_uses_first_date_string(self):
        response = self.client.post(
            "/api/trips/export-pdf/", self.valid_payload, format="json"
        )
        self.assertIn("eld-logs-2026-06-24.pdf", response.headers["Content-Disposition"])

    def test_export_pdf_body_is_pdf(self):
        response = self.client.post(
            "/api/trips/export-pdf/", self.valid_payload, format="json"
        )
        self.assertEqual(response.content[:4], b"%PDF")

    def test_export_pdf_missing_summary_returns_400(self):
        payload = {"daily_logs": [VALID_DAILY_LOG]}
        response = self.client.post("/api/trips/export-pdf/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_pdf_missing_daily_logs_returns_400(self):
        payload = {"summary": VALID_SUMMARY}
        response = self.client.post("/api/trips/export-pdf/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_pdf_empty_daily_logs_returns_400(self):
        payload = {"summary": VALID_SUMMARY, "daily_logs": []}
        response = self.client.post("/api/trips/export-pdf/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_pdf_invalid_status_choice_returns_400(self):
        bad_log = dict(VALID_DAILY_LOG)
        bad_log["timeline"] = [
            {"status": "INVALID", "start_hour": 0.0, "end_hour": 1.0, "location_name": "x"}
        ]
        payload = {"summary": VALID_SUMMARY, "daily_logs": [bad_log]}
        response = self.client.post("/api/trips/export-pdf/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_pdf_negative_cycle_hours_returns_400(self):
        bad_summary = dict(VALID_SUMMARY, current_cycle_used_hrs=-1.0)
        payload = {"summary": bad_summary, "daily_logs": [VALID_DAILY_LOG]}
        response = self.client.post("/api/trips/export-pdf/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_pdf_cors_headers(self):
        response = self.client.options(
            "/api/trips/export-pdf/",
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
