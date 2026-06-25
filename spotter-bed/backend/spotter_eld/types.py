from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class DutyStatus:
    OFF = "OFF"
    SB = "SB"
    D = "D"
    ON = "ON"


@dataclass
class GeocodedLocation:
    label: str
    city: str
    state: str
    lat: float
    lng: float


@dataclass
class RouteLeg:
    from_location: GeocodedLocation
    to_location: GeocodedLocation
    distance_miles: int
    duration_hours: float


@dataclass
class ItineraryItem:
    id: str
    status: str
    activity_name: str
    location_name: str
    start_time: str
    end_time: str
    duration_hours: float
    distance_miles: float
    coordinates: Tuple[float, float]
    remarks: str


@dataclass
class TimelineBlock:
    status: str
    start_hour: float
    end_hour: float
    location_name: str
    remarks: Optional[str] = None


@dataclass
class DailyLogRemarks:
    time_label: str
    status: str
    location: str
    remarks_text: str


@dataclass
class DailyLogSheet:
    date_string: str
    date_label: str
    total_miles_driven: int
    tractor_number: str
    trailer_number: str
    carrier_name: str
    timeline: List[TimelineBlock]
    totals: dict
    remarks: List[DailyLogRemarks]
    timezone: str = "UTC"


@dataclass
class TripGenerationResult:
    current: GeocodedLocation
    pickup: GeocodedLocation
    dropoff: GeocodedLocation
    legs: List[RouteLeg]
    total_distance_miles: int
    total_duration_hours: float
    itinerary: List[ItineraryItem]
    daily_logs: List[DailyLogSheet]
    timezone: str = "UTC"
