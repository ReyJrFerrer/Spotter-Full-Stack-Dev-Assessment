import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Tuple, List

from spotter_eld.types import GeocodedLocation, RouteLeg
from spotter_eld.utils import round_to_quarter_hour


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
USER_AGENT = "SpotterAssessment/1.0 (trucking-route-planner)"

STATE_ABBREVIATIONS: dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "district of columbia": "DC", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
    "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
    "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}


_AUTOCOMPLETE_CACHE: dict[str, tuple[float, list[dict]]] = {}
_AUTOCOMPLETE_CACHE_TTL = 300  # 5 minutes

CITY_DATABASE: dict[str, GeocodedLocation] = {
    "los angeles": GeocodedLocation(label="Los Angeles, CA", city="Los Angeles", state="CA", lat=34.0522, lng=-118.2437),
    "las vegas": GeocodedLocation(label="Las Vegas, NV", city="Las Vegas", state="NV", lat=36.1699, lng=-115.1398),
    "salt lake city": GeocodedLocation(label="Salt Lake City, UT", city="Salt Lake City", state="UT", lat=40.7608, lng=-111.8910),
    "bakersfield": GeocodedLocation(label="Bakersfield, CA", city="Bakersfield", state="CA", lat=35.3733, lng=-119.0187),
    "phoenix": GeocodedLocation(label="Phoenix, AZ", city="Phoenix", state="AZ", lat=33.4484, lng=-112.0740),
    "denver": GeocodedLocation(label="Denver, CO", city="Denver", state="CO", lat=39.7392, lng=-104.9903),
    "seattle": GeocodedLocation(label="Seattle, WA", city="Seattle", state="WA", lat=47.6062, lng=-122.3321),
    "portland": GeocodedLocation(label="Portland, OR", city="Portland", state="OR", lat=45.5152, lng=-122.6784),
    "san francisco": GeocodedLocation(label="San Francisco, CA", city="San Francisco", state="CA", lat=37.7749, lng=-122.4194),
    "san diego": GeocodedLocation(label="San Diego, CA", city="San Diego", state="CA", lat=32.7157, lng=-117.1611),
    "albuquerque": GeocodedLocation(label="Albuquerque, NM", city="Albuquerque", state="NM", lat=35.0853, lng=-106.6056),
    "houston": GeocodedLocation(label="Houston, TX", city="Houston", state="TX", lat=29.7604, lng=-95.3698),
    "dallas": GeocodedLocation(label="Dallas, TX", city="Dallas", state="TX", lat=32.7767, lng=-96.7970),
    "chicago": GeocodedLocation(label="Chicago, IL", city="Chicago", state="IL", lat=41.8781, lng=-87.6298),
    "new york": GeocodedLocation(label="New York, NY", city="New York", state="NY", lat=40.7128, lng=-74.0060),
    "boston": GeocodedLocation(label="Boston, MA", city="Boston", state="MA", lat=42.3601, lng=-71.0589),
    "atlanta": GeocodedLocation(label="Atlanta, GA", city="Atlanta", state="GA", lat=33.7490, lng=-84.3880),
}


def _parse_location(location_str: str) -> Tuple[str, str]:
    parts = re.split(r",\s*", location_str.strip(), maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return location_str.strip(), ""


def _fetch_json(url: str, timeout: int = 10) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _fetch_json_list(url: str, timeout: int = 10) -> Optional[list]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _extract_city(address: dict) -> str:
    for key in ("city", "town", "village", "hamlet", "municipality", "county"):
        val = address.get(key)
        if val:
            return val
    return ""


def _extract_state_abbr(state_name: str) -> str:
    key = state_name.strip().lower()
    return STATE_ABBREVIATIONS.get(key, state_name)


def _serialize_autocomplete(result: dict) -> Optional[dict]:
    if result.get("class") not in ("place", "boundary"):
        return None
    place_type = result.get("type", "")
    if place_type not in ("city", "town", "village", "hamlet", "municipality", "county", "administrative"):
        return None

    address = result.get("address", {})
    city_name = _extract_city(address)
    if not city_name:
        display_name = result.get("display_name", "")
        city_name = display_name.split(",")[0].strip()
        if not city_name:
            return None

    state_name = address.get("state", "")
    state_abbr = _extract_state_abbr(state_name) if state_name else ""

    if not state_abbr:
        return None

    return {
        "label": f"{city_name}, {state_abbr}",
        "city": city_name,
        "state": state_abbr,
        "lat": float(result.get("lat", 0)),
        "lng": float(result.get("lon", 0)),
    }


def nominatim_autocomplete(query: str) -> list[dict]:
    now = time.time()
    cached = _AUTOCOMPLETE_CACHE.get(query)
    if cached:
        timestamp, data = cached
        if now - timestamp < _AUTOCOMPLETE_CACHE_TTL:
            return data

    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "us",
    })
    url = f"{NOMINATIM_URL}?{params}"
    raw = _fetch_json_list(url)
    if not raw:
        return []

    results: list[dict] = []
    seen = set()
    for item in raw:
        serialized = _serialize_autocomplete(item)
        if serialized and serialized["label"] not in seen:
            seen.add(serialized["label"])
            results.append(serialized)

    _AUTOCOMPLETE_CACHE[query] = (now, results)
    return results


def nominatim_geocode(location_str: str) -> Optional[GeocodedLocation]:
    params = urllib.parse.urlencode({
        "q": location_str,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    })
    url = f"{NOMINATIM_URL}?{params}"
    data = _fetch_json(url)
    if not data or not isinstance(data, list) or len(data) == 0:
        return None

    result = data[0]
    lat = float(result.get("lat", 0))
    lng = float(result.get("lon", 0))
    display_name = result.get("display_name", location_str)

    city, state = _parse_location(location_str)
    return GeocodedLocation(
        label=display_name,
        city=city or display_name.split(",")[0].strip(),
        state=state or "",
        lat=lat,
        lng=lng,
    )


def geocode_location(location_str: str) -> Optional[GeocodedLocation]:
    city, state = _parse_location(location_str)
    key = city.lower()
    if key in CITY_DATABASE:
        loc = CITY_DATABASE[key]
        return GeocodedLocation(
            label=loc.label,
            city=loc.city,
            state=loc.state,
            lat=loc.lat,
            lng=loc.lng,
        )
    return nominatim_geocode(location_str)


def osrm_route(
    waypoints: List[GeocodedLocation],
) -> Optional[Tuple[List[RouteLeg], List[Tuple[float, float]]]]:
    if len(waypoints) < 2:
        return None

    coords_str = ";".join(f"{w.lng},{w.lat}" for w in waypoints)
    params = urllib.parse.urlencode({
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    })
    url = f"{OSRM_URL}/{coords_str}?{params}"
    data = _fetch_json(url)
    if not data or data.get("code") != "Ok":
        return None

    route_data = data.get("routes", [{}])[0]
    legs_data = route_data.get("legs", [])

    legs: List[RouteLeg] = []
    for i, leg_data in enumerate(legs_data):
        dist_meters = leg_data.get("distance", 0)
        dur_seconds = leg_data.get("duration", 0)
        dist_miles = max(1, round(dist_meters / 1609.344))
        dur_hours = max(0.25, round_to_quarter_hour(dur_seconds / 3600))
        legs.append(
            RouteLeg(
                from_location=waypoints[i],
                to_location=waypoints[i + 1],
                distance_miles=dist_miles,
                duration_hours=dur_hours,
            )
        )

    geometry: List[Tuple[float, float]] = []
    raw_geometry = route_data.get("geometry", {})
    if isinstance(raw_geometry, dict) and raw_geometry.get("type") == "LineString":
        coords = raw_geometry.get("coordinates", [])
        geometry = [(lat, lng) for lng, lat in coords]

    if not legs:
        return None
    return (legs, geometry)
