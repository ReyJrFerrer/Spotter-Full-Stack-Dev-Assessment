import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional

from spotter_eld.utils import round_to_quarter_hour, interpolate_coordinates
from spotter_eld.types import (
    DutyStatus,
    GeocodedLocation,
    RouteLeg,
    ItineraryItem,
    TripGenerationResult,
)


AVERAGE_SPEED_MPH = 60


@dataclass
class DriverState:
    accum_driving_today: float = 0.0
    elapsed_duty_window_today: float = 0.0
    continuous_driving_since_break: float = 0.0
    total_cycle_hours_used: float = 0.0
    miles_since_fueling: float = 0.0


def _estimate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    lat_diff = lat2 - lat1
    lng_diff = lng2 - lng1
    return max(20, round(math.sqrt(lat_diff * lat_diff + lng_diff * lng_diff) * 55))


def _make_legs(
    current: GeocodedLocation,
    pickup: GeocodedLocation,
    dropoff: GeocodedLocation,
) -> Tuple[List[RouteLeg], int, float]:
    dist1 = _estimate_distance(current.lat, current.lng, pickup.lat, pickup.lng)
    dist2 = _estimate_distance(pickup.lat, pickup.lng, dropoff.lat, dropoff.lng)
    dur1 = max(0.25, round_to_quarter_hour(dist1 / AVERAGE_SPEED_MPH))
    dur2 = max(0.25, round_to_quarter_hour(dist2 / AVERAGE_SPEED_MPH))

    legs = [
        RouteLeg(
            from_location=current,
            to_location=pickup,
            distance_miles=dist1,
            duration_hours=dur1,
        ),
        RouteLeg(
            from_location=pickup,
            to_location=dropoff,
            distance_miles=dist2,
            duration_hours=dur2,
        ),
    ]
    total_distance = dist1 + dist2
    total_duration = dur1 + dur2
    return legs, total_distance, total_duration


def simulate_trip(
    current: GeocodedLocation,
    pickup: GeocodedLocation,
    dropoff: GeocodedLocation,
    current_cycle_used: float,
    start_time_iso: Optional[datetime] = None,
    carrier_name: str = "",
    tractor_number: str = "",
    trailer_number: str = "",
    external_legs: Optional[List[RouteLeg]] = None,
) -> TripGenerationResult:
    if start_time_iso is None:
        start_time_iso = datetime.now(timezone.utc)
    current_time = start_time_iso

    if external_legs and len(external_legs) == 2:
        legs = external_legs
        total_distance_miles = sum(leg.distance_miles for leg in legs)
        total_duration_hours = sum(leg.duration_hours for leg in legs)
    else:
        legs, total_distance_miles, total_duration_hours = _make_legs(
            current, pickup, dropoff
        )

    state = DriverState(total_cycle_hours_used=current_cycle_used)
    itinerary: List[ItineraryItem] = []
    item_counter = [1]

    def add_itinerary(
        status: str,
        activity_name: str,
        location_name: str,
        duration_hours: float,
        distance_miles: float,
        coords: Tuple[float, float],
        remarks: str,
    ) -> None:
        nonlocal current_time
        s_time = current_time
        duration_sec = duration_hours * 3600
        e_time = current_time + timedelta(seconds=duration_sec)
        current_time = e_time

        itinerary.append(
            ItineraryItem(
                id=f"item-{item_counter[0]}",
                status=status,
                activity_name=activity_name,
                location_name=location_name,
                start_time=s_time.isoformat(),
                end_time=e_time.isoformat(),
                duration_hours=duration_hours,
                distance_miles=distance_miles,
                coordinates=coords,
                remarks=remarks,
            )
        )
        item_counter[0] += 1

        if status == DutyStatus.D:
            state.accum_driving_today += duration_hours
            state.continuous_driving_since_break += duration_hours
            state.total_cycle_hours_used += duration_hours
            state.miles_since_fueling += distance_miles
        elif status == DutyStatus.ON:
            state.total_cycle_hours_used += duration_hours

        state.elapsed_duty_window_today += duration_hours

    def trigger_10h_reset(
        location: str, coords: Tuple[float, float], reason: str
    ) -> None:
        add_itinerary(
            DutyStatus.SB,
            "10-Hour Daily Reset - Sleeper Berth",
            location,
            8.0,
            0,
            coords,
            f"Sleeper Berth: 8 hrs (part of 10-hour HOS reset, {reason})",
        )
        add_itinerary(
            DutyStatus.OFF,
            "10-Hour Daily Reset - Off Duty",
            location,
            2.0,
            0,
            coords,
            f"Off Duty: 2 hrs (completing 10-hour HOS reset, {reason})",
        )
        state.accum_driving_today = 0.0
        state.elapsed_duty_window_today = 0.0
        state.continuous_driving_since_break = 0.0

    def trigger_30min_break(
        location: str, coords: Tuple[float, float], reason: str
    ) -> None:
        add_itinerary(
            DutyStatus.OFF,
            "30-Minute Rest Break",
            location,
            0.5,
            0,
            coords,
            f"Mandatory 30-min consecutive break ({reason})",
        )
        state.continuous_driving_since_break = 0.0

    def trigger_34h_restart(
        location: str, coords: Tuple[float, float]
    ) -> None:
        add_itinerary(
            DutyStatus.OFF,
            "34-Hour Weekly Cycle Reset",
            location,
            34.0,
            0,
            coords,
            "34-Hour consecutive Off-Duty cycle reset (70-hour clock restored)",
        )
        state.total_cycle_hours_used = 0.0
        state.accum_driving_today = 0.0
        state.elapsed_duty_window_today = 0.0
        state.continuous_driving_since_break = 0.0

    def simulate_leg(
        leg_distance: int,
        leg_coords_start: Tuple[float, float],
        leg_coords_end: Tuple[float, float],
        leg_from_city: str,
        leg_to_city: str,
        leg_label_from: str,
        leg_label_to: str,
    ) -> None:
        nonlocal current_time
        miles_left = leg_distance

        while miles_left > 0:
            if state.total_cycle_hours_used >= 70:
                trigger_34h_restart(leg_label_from, leg_coords_start)

            if (
                state.elapsed_duty_window_today >= 14
                or state.accum_driving_today >= 11
            ):
                fraction = (leg_distance - miles_left) / leg_distance
                coords = interpolate_coordinates(
                    leg_coords_start, leg_coords_end, fraction
                )
                reason = (
                    "14hr Duty Limit"
                    if state.elapsed_duty_window_today >= 14
                    else "11hr Driving Limit"
                )
                trigger_10h_reset(
                    f"En-Route ({leg_label_from} to {leg_label_to})",
                    coords,
                    reason,
                )

            if state.continuous_driving_since_break >= 8:
                fraction = (leg_distance - miles_left) / leg_distance
                coords = interpolate_coordinates(
                    leg_coords_start, leg_coords_end, fraction
                )
                trigger_30min_break(
                    f"En-Route Rest Area ({leg_label_from} to {leg_label_to})",
                    coords,
                    "8-hour continuous driving threshold",
                )

            if state.miles_since_fueling >= 1000:
                fraction = (leg_distance - miles_left) / leg_distance
                coords = interpolate_coordinates(
                    leg_coords_start, leg_coords_end, fraction
                )
                add_itinerary(
                    DutyStatus.ON,
                    "Commercial Vehicle Fueling Stop",
                    "En-Route Truck Plaza",
                    0.5,
                    0,
                    coords,
                    "Refueling commercial vehicle",
                )
                state.miles_since_fueling = 0.0

            max_driving_hours_left_today = 11 - state.accum_driving_today
            max_duty_hours_left_today = 14 - state.elapsed_duty_window_today
            max_driving_hours_break = 8 - state.continuous_driving_since_break

            max_hours_possible = min(
                2.0,
                max_driving_hours_left_today,
                max_duty_hours_left_today,
                max_driving_hours_break,
            )

            if max_hours_possible <= 0:
                fraction = (leg_distance - miles_left) / leg_distance
                coords = interpolate_coordinates(
                    leg_coords_start, leg_coords_end, fraction
                )
                trigger_10h_reset(
                    "En-Route Safety Stop",
                    coords,
                    "Safety Threshold",
                )
                continue

            miles_potential = max_hours_possible * AVERAGE_SPEED_MPH
            miles_to_drive = min(miles_left, miles_potential)
            driving_time = round_to_quarter_hour(
                miles_to_drive / AVERAGE_SPEED_MPH
            )
            resolved_hours = driving_time if driving_time > 0 else 0.25

            fraction_start = (leg_distance - miles_left) / leg_distance
            miles_left -= miles_to_drive
            fraction_end = (leg_distance - miles_left) / leg_distance

            mid_coords = interpolate_coordinates(
                leg_coords_start,
                leg_coords_end,
                (fraction_start + fraction_end) / 2,
            )

            add_itinerary(
                DutyStatus.D,
                "Driving",
                f"I-15 Corridor (En Route)",
                resolved_hours,
                miles_to_drive,
                mid_coords,
                f"Driving Commercial Truck en route to {leg_label_to} ({round(miles_to_drive)} miles)",
            )

    current_coords = (current.lat, current.lng)

    # Pre-trip inspection
    add_itinerary(
        DutyStatus.ON,
        "Pre-Trip Inspection",
        f"{current.city}, {current.state}",
        0.25,
        0,
        current_coords,
        "15-min Post/Pre-Trip Commercial Vehicle Inspection",
    )

    # Leg 1: Current → Pickup
    simulate_leg(
        leg_distance=legs[0].distance_miles,
        leg_coords_start=(current.lat, current.lng),
        leg_coords_end=(pickup.lat, pickup.lng),
        leg_from_city=current.city,
        leg_to_city=pickup.city,
        leg_label_from=current.city,
        leg_label_to=pickup.city,
    )

    # Arrive at pickup
    current_coords = (pickup.lat, pickup.lng)

    if state.elapsed_duty_window_today >= 14:
        trigger_10h_reset(
            f"{pickup.city}, {pickup.state}",
            current_coords,
            "14h limit prior to loading",
        )

    add_itinerary(
        DutyStatus.ON,
        "Cargo Loading & Inspection",
        f"{pickup.city}, {pickup.state}",
        1.0,
        0,
        current_coords,
        "Scheduled 1-hour Cargo Loading, Securement and Manifest Inspection",
    )

    # Leg 2: Pickup → Dropoff
    simulate_leg(
        leg_distance=legs[1].distance_miles,
        leg_coords_start=(pickup.lat, pickup.lng),
        leg_coords_end=(dropoff.lat, dropoff.lng),
        leg_from_city=pickup.city,
        leg_to_city=dropoff.city,
        leg_label_from=pickup.city,
        leg_label_to=dropoff.city,
    )

    # Arrive at dropoff
    current_coords = (dropoff.lat, dropoff.lng)

    if state.elapsed_duty_window_today >= 14:
        trigger_10h_reset(
            f"{dropoff.city}, {dropoff.state}",
            current_coords,
            "14h limit prior to unloading",
        )

    add_itinerary(
        DutyStatus.ON,
        "Cargo Unloading & Post-Trip Inspection",
        f"{dropoff.city}, {dropoff.state}",
        1.0,
        0,
        current_coords,
        "Cargo discharge and final Post-Trip vehicle evaluation",
    )

    from spotter_eld.eld_generator import partition_into_daily_logs

    daily_logs = partition_into_daily_logs(
        itinerary=itinerary,
        start_time=start_time_iso,
        end_time=current_time,
        dropoff=dropoff,
        carrier_name=carrier_name,
        tractor_number=tractor_number,
        trailer_number=trailer_number,
    )

    return TripGenerationResult(
        current=current,
        pickup=pickup,
        dropoff=dropoff,
        legs=legs,
        total_distance_miles=round(total_distance_miles),
        total_duration_hours=round_to_quarter_hour(total_duration_hours),
        itinerary=itinerary,
        daily_logs=daily_logs,
    )
