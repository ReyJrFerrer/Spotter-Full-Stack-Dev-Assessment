import re
from typing import Optional, Tuple

from spotter_eld.types import GeocodedLocation


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
}


def _parse_location(location_str: str) -> Tuple[str, str]:
    parts = re.split(r",\s*", location_str.strip(), maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return location_str.strip(), ""


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
    return None
