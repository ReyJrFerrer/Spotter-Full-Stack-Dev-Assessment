from django.test import TestCase
from datetime import datetime, timezone

from spotter_eld import utils


class RoundToQuarterHourTests(TestCase):
    def test_rounds_exact_hour(self):
        self.assertEqual(utils.round_to_quarter_hour(1.0), 1.0)

    def test_rounds_quarter_hour(self):
        self.assertEqual(utils.round_to_quarter_hour(1.25), 1.25)

    def test_rounds_half_hour(self):
        self.assertEqual(utils.round_to_quarter_hour(1.5), 1.5)

    def test_rounds_three_quarter_hour(self):
        self.assertEqual(utils.round_to_quarter_hour(1.75), 1.75)

    def test_rounds_up_to_nearest_quarter(self):
        self.assertEqual(utils.round_to_quarter_hour(1.1), 1.0)

    def test_rounds_down_to_nearest_quarter(self):
        self.assertEqual(utils.round_to_quarter_hour(1.3), 1.25)

    def test_rounds_zero(self):
        self.assertEqual(utils.round_to_quarter_hour(0.0), 0.0)

    def test_rounds_24_hours(self):
        self.assertEqual(utils.round_to_quarter_hour(24.0), 24.0)

    def test_rounds_small_value(self):
        self.assertEqual(utils.round_to_quarter_hour(0.1), 0.0)

    def test_rounds_midpoint_up(self):
        self.assertEqual(utils.round_to_quarter_hour(0.125), 0.0)


class FormatTimeLabelTests(TestCase):
    def test_midnight(self):
        dt = datetime(2026, 6, 22, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.format_time_label(dt), "12:00 AM")

    def test_noon(self):
        dt = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.format_time_label(dt), "12:00 PM")

    def test_morning(self):
        dt = datetime(2026, 6, 22, 8, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.format_time_label(dt), "8:15 AM")

    def test_afternoon(self):
        dt = datetime(2026, 6, 22, 14, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.format_time_label(dt), "2:30 PM")

    def test_evening(self):
        dt = datetime(2026, 6, 22, 22, 45, 0, tzinfo=timezone.utc)
        self.assertEqual(utils.format_time_label(dt), "10:45 PM")


class FormatDateLabelTests(TestCase):
    def test_weekday_format(self):
        dt = datetime(2026, 6, 22, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_label(dt), "Monday, Jun 22, 2026")

    def test_weekend_format(self):
        dt = datetime(2026, 6, 20, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_label(dt), "Saturday, Jun 20, 2026")

    def test_january(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_label(dt), "Thursday, Jan 1, 2026")

    def test_december(self):
        dt = datetime(2026, 12, 25, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_label(dt), "Friday, Dec 25, 2026")


class FormatDateStringTests(TestCase):
    def test_basic_format(self):
        dt = datetime(2026, 6, 22, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_string(dt), "2026-06-22")

    def test_single_digit_month(self):
        dt = datetime(2026, 1, 5, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_string(dt), "2026-01-05")

    def test_single_digit_day(self):
        dt = datetime(2026, 12, 1, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_string(dt), "2026-12-01")

    def test_new_year(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(utils.format_date_string(dt), "2026-01-01")


class InterpolateCoordinatesTests(TestCase):
    def test_interpolate_halfway(self):
        result = utils.interpolate_coordinates((0.0, 0.0), (10.0, 10.0), 0.5)
        self.assertAlmostEqual(result[0], 5.0)
        self.assertAlmostEqual(result[1], 5.0)

    def test_interpolate_start(self):
        result = utils.interpolate_coordinates((0.0, 0.0), (10.0, 10.0), 0.0)
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[1], 0.0)

    def test_interpolate_end(self):
        result = utils.interpolate_coordinates((0.0, 0.0), (10.0, 10.0), 1.0)
        self.assertAlmostEqual(result[0], 10.0)
        self.assertAlmostEqual(result[1], 10.0)

    def test_interpolate_one_third(self):
        result = utils.interpolate_coordinates((0.0, 0.0), (9.0, 9.0), 1 / 3)
        self.assertAlmostEqual(result[0], 3.0)
        self.assertAlmostEqual(result[1], 3.0)

    def test_interpolate_negative_coordinates(self):
        result = utils.interpolate_coordinates((-10.0, -10.0), (10.0, 10.0), 0.5)
        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[1], 0.0)
