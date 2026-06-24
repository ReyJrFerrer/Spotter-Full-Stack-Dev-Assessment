from datetime import datetime, timezone
from typing import List, Tuple


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


def project_point_onto_segment(
    point: Coordinate,
    segment_start: Coordinate,
    segment_end: Coordinate,
) -> Coordinate:
    px, py = point
    ax, ay = segment_start
    bx, by = segment_end

    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq == 0:
        return segment_start

    t = (apx * abx + apy * aby) / ab_len_sq
    t = max(0.0, min(1.0, t))

    return (ax + t * abx, ay + t * aby)


def snap_point_to_polyline(
    point: Coordinate,
    polyline: List[Coordinate],
) -> Coordinate:
    if not polyline:
        return point

    best_point = point
    best_dist_sq = float("inf")

    for i in range(len(polyline) - 1):
        proj = project_point_onto_segment(point, polyline[i], polyline[i + 1])
        dx = point[0] - proj[0]
        dy = point[1] - proj[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best_point = proj

    return best_point
