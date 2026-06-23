from unittest.mock import patch, MagicMock
from django.test import TestCase

from spotter_eld import geocoding
from spotter_eld.types import GeocodedLocation, RouteLeg


class ParseLocationTests(TestCase):
    def test_parse_city_state(self):
        city, state = geocoding._parse_location("Los Angeles, CA")
        self.assertEqual(city, "Los Angeles")
        self.assertEqual(state, "CA")

    def test_parse_city_only(self):
        city, state = geocoding._parse_location("Denver")
        self.assertEqual(city, "Denver")
        self.assertEqual(state, "")

    def test_parse_whitespace(self):
        city, state = geocoding._parse_location("  Dallas ,  TX  ")
        self.assertEqual(city, "Dallas")
        self.assertEqual(state, "TX")

    def test_parse_multi_word_city(self):
        city, state = geocoding._parse_location("Salt Lake City, UT")
        self.assertEqual(city, "Salt Lake City")
        self.assertEqual(state, "UT")


class CityDatabaseTests(TestCase):
    def test_known_city_returns_location(self):
        loc = geocoding.geocode_location("Los Angeles, CA")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.city, "Los Angeles")
        self.assertEqual(loc.state, "CA")
        self.assertAlmostEqual(loc.lat, 34.0522, places=2)
        self.assertAlmostEqual(loc.lng, -118.2437, places=2)

    def test_unknown_city_returns_nominatim(self):
        with patch("spotter_eld.geocoding.nominatim_geocode") as mock:
            mock.return_value = GeocodedLocation(
                label="Boise, ID", city="Boise", state="ID",
                lat=43.6150, lng=-116.2023,
            )
            loc = geocoding.geocode_location("Boise, ID")
            self.assertIsNotNone(loc)
            self.assertEqual(loc.city, "Boise")
            mock.assert_called_once_with("Boise, ID")

    def test_case_insensitive_lookup(self):
        loc = geocoding.geocode_location("LOS ANGELES, CA")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.city, "Los Angeles")

    def test_unknown_city_nominatim_fails_returns_none(self):
        with patch("spotter_eld.geocoding.nominatim_geocode") as mock:
            mock.return_value = None
            loc = geocoding.geocode_location("NonExistentCity, XX")
            self.assertIsNone(loc)

    def test_all_database_cities_geocode(self):
        for key in geocoding.CITY_DATABASE:
            loc = geocoding.geocode_location(f"{key.title()}, CA")
            self.assertIsNotNone(loc, f"Failed for {key}")


class NominatimGeocodeTests(TestCase):
    def test_successful_geocode(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"lat": "43.6150", "lon": "-116.2023", "display_name": "Boise, Ada County, Idaho, USA"}]'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            loc = geocoding.nominatim_geocode("Boise, ID")
            self.assertIsNotNone(loc)
            self.assertAlmostEqual(loc.lat, 43.6150, places=4)
            self.assertAlmostEqual(loc.lng, -116.2023, places=4)

    def test_empty_results(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[]'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            loc = geocoding.nominatim_geocode("NonPlace, XX")
            self.assertIsNone(loc)

    def test_network_error(self):
        with patch("spotter_eld.geocoding.urllib.request.urlopen", side_effect=OSError("timeout")):
            loc = geocoding.nominatim_geocode("Boise, ID")
            self.assertIsNone(loc)

    def test_user_agent_header(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"lat": "40.0", "lon": "-100.0", "display_name": "Test"}]'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen") as mock_open:
            mock_open.return_value = mock_response
            geocoding.nominatim_geocode("Test City")
            call_args = mock_open.call_args
            req = call_args[0][0]
            self.assertEqual(req.get_header("User-agent"), geocoding.USER_AGENT)


_ROUTE_GEOJSON = (
    '"geometry": {"type": "LineString", "coordinates": [[-118.24, 34.05], [-115.14, 36.17], [-111.89, 40.76]]}'
)


class OsrmRouteTests(TestCase):
    def test_successful_route(self):
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"code": "Ok", "routes": [{"legs": [{"distance": 434567.2, "duration": 15642.1}, '
            b'{"distance": 652134.8, "duration": 23473.5}], '
            + _ROUTE_GEOJSON.encode()
            + b'}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            waypoints = [
                GeocodedLocation(label="LA", city="Los Angeles", state="CA", lat=34.05, lng=-118.24),
                GeocodedLocation(label="LV", city="Las Vegas", state="NV", lat=36.17, lng=-115.14),
                GeocodedLocation(label="SLC", city="Salt Lake City", state="UT", lat=40.76, lng=-111.89),
            ]
            result = geocoding.osrm_route(waypoints)
            self.assertIsNotNone(result)
            legs, geometry = result
            self.assertEqual(len(legs), 2)
            self.assertGreater(legs[0].distance_miles, 0)
            self.assertGreater(legs[1].distance_miles, 0)
            self.assertEqual(legs[0].from_location.city, "Los Angeles")
            self.assertEqual(legs[0].to_location.city, "Las Vegas")
            self.assertEqual(legs[1].from_location.city, "Las Vegas")
            self.assertEqual(legs[1].to_location.city, "Salt Lake City")
            self.assertGreater(len(geometry), 0)

    def test_osrm_error_code(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"code": "NoRoute", "routes": []}'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            waypoints = [
                GeocodedLocation(label="A", city="A", state="", lat=0, lng=0),
                GeocodedLocation(label="B", city="B", state="", lat=1, lng=1),
            ]
            result = geocoding.osrm_route(waypoints)
            self.assertIsNone(result)

    def test_network_error(self):
        with patch("spotter_eld.geocoding.urllib.request.urlopen", side_effect=OSError("connection refused")):
            waypoints = [
                GeocodedLocation(label="A", city="A", state="", lat=0, lng=0),
                GeocodedLocation(label="B", city="B", state="", lat=1, lng=1),
            ]
            result = geocoding.osrm_route(waypoints)
            self.assertIsNone(result)

    def test_single_waypoint_returns_none(self):
        waypoints = [
            GeocodedLocation(label="A", city="A", state="", lat=0, lng=0),
        ]
        result = geocoding.osrm_route(waypoints)
        self.assertIsNone(result)

    def test_empty_waypoints_returns_none(self):
        result = geocoding.osrm_route([])
        self.assertIsNone(result)

    def test_distance_converted_to_miles(self):
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"code": "Ok", "routes": [{"legs": [{"distance": 1609.344, "duration": 3600}], '
            + _ROUTE_GEOJSON.encode()
            + b'}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            waypoints = [
                GeocodedLocation(label="A", city="A", state="", lat=0, lng=0),
                GeocodedLocation(label="B", city="B", state="", lat=1, lng=0),
            ]
            result = geocoding.osrm_route(waypoints)
            self.assertIsNotNone(result)
            legs, _ = result
            self.assertEqual(legs[0].distance_miles, 1)
            self.assertAlmostEqual(legs[0].duration_hours, 1.0, places=2)

    def test_min_duration_enforced(self):
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"code": "Ok", "routes": [{"legs": [{"distance": 100, "duration": 60}], '
            + _ROUTE_GEOJSON.encode()
            + b'}]}'
        )
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("spotter_eld.geocoding.urllib.request.urlopen", return_value=mock_response):
            waypoints = [
                GeocodedLocation(label="A", city="A", state="", lat=0, lng=0),
                GeocodedLocation(label="B", city="B", state="", lat=0, lng=0.01),
            ]
            result = geocoding.osrm_route(waypoints)
            self.assertIsNotNone(result)
            legs, _ = result
            self.assertGreaterEqual(legs[0].duration_hours, 0.25)
