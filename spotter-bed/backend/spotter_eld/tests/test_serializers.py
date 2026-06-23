from django.test import TestCase
from rest_framework.exceptions import ValidationError

from spotter_eld.serializers import TripInputSerializer


class TripInputSerializerTests(TestCase):
    def test_valid_input(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        })
        self.assertTrue(serializer.is_valid())

    def test_missing_current_location(self):
        serializer = TripInputSerializer(data={
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("current_location", serializer.errors)

    def test_missing_pickup_location(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 15.5,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("pickup_location", serializer.errors)

    def test_missing_dropoff_location(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "current_cycle_used_hrs": 15.5,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("dropoff_location", serializer.errors)

    def test_missing_current_cycle_used(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("current_cycle_used_hrs", serializer.errors)

    def test_cycle_used_negative(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": -1.0,
        })
        self.assertFalse(serializer.is_valid())

    def test_cycle_used_exceeds_70(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 71.0,
        })
        self.assertFalse(serializer.is_valid())

    def test_cycle_used_zero_is_valid(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 0.0,
        })
        self.assertTrue(serializer.is_valid())

    def test_cycle_used_exactly_70_is_valid(self):
        serializer = TripInputSerializer(data={
            "current_location": "Los Angeles, CA",
            "pickup_location": "Las Vegas, NV",
            "dropoff_location": "Salt Lake City, UT",
            "current_cycle_used_hrs": 70.0,
        })
        self.assertTrue(serializer.is_valid())

    def test_empty_location_strings(self):
        serializer = TripInputSerializer(data={
            "current_location": "",
            "pickup_location": "",
            "dropoff_location": "",
            "current_cycle_used_hrs": 15.5,
        })
        self.assertFalse(serializer.is_valid())
