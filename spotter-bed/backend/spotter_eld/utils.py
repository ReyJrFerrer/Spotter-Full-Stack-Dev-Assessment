from datetime import datetime, timezone
from typing import Tuple


def round_to_quarter_hour(hours: float) -> float:
    return round(hours * 4) / 4


def format_time_label(dt: datetime) -> str:
    hh = dt.hour
    mm = dt.minute
    ampm = "PM" if hh >= 12 else "AM"
    hh12 = hh % 12
    if hh12 == 0:
        hh12 = 12
    return f"{hh12}:{mm:02d} {ampm}"


def format_date_label(dt: datetime) -> str:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{days[dt.weekday()]}, {months[dt.month - 1]} {dt.day}, {dt.year}"


def format_date_string(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"


Coordinate = Tuple[float, float]


def interpolate_coordinates(coord1: Coordinate, coord2: Coordinate, fraction: float) -> Coordinate:
    lat = coord1[0] + (coord2[0] - coord1[0]) * fraction
    lng = coord1[1] + (coord2[1] - coord1[1]) * fraction
    return (lat, lng)
