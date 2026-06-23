from datetime import datetime, timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from spotter_eld.serializers import TripInputSerializer
from spotter_eld.geocoding import geocode_location, osrm_route
from spotter_eld.hos_engine import simulate_trip


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class TripGenerateView(APIView):
    def post(self, request):
        serializer = TripInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        current_loc = geocode_location(data["current_location"])
        pickup_loc = geocode_location(data["pickup_location"])
        dropoff_loc = geocode_location(data["dropoff_location"])

        if not current_loc or not pickup_loc or not dropoff_loc:
            return Response(
                {"error": "Could not geocode one or more locations"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        osrm_result = osrm_route([current_loc, pickup_loc, dropoff_loc])
        route_geometry = []
        osrm_legs = None
        if osrm_result is not None:
            osrm_legs, route_geometry = osrm_result

        result = simulate_trip(
            current=current_loc,
            pickup=pickup_loc,
            dropoff=dropoff_loc,
            current_cycle_used=data["current_cycle_used_hrs"],
            start_time_iso=datetime.now(timezone.utc),
            external_legs=osrm_legs,
        )

        return Response(_serialize_result(result, route_geometry))


def _serialize_result(result, route_geometry=None):
    if route_geometry is None:
        route_geometry = []
    return {
        "route_geometry": [[lat, lng] for lat, lng in route_geometry],
        "current": _serialize_location(result.current),
        "pickup": _serialize_location(result.pickup),
        "dropoff": _serialize_location(result.dropoff),
        "legs": [
            {
                "from_location": _serialize_location(leg.from_location),
                "to_location": _serialize_location(leg.to_location),
                "distance_miles": leg.distance_miles,
                "duration_hours": leg.duration_hours,
            }
            for leg in result.legs
        ],
        "total_distance_miles": result.total_distance_miles,
        "total_duration_hours": result.total_duration_hours,
        "itinerary": [
            {
                "id": item.id,
                "status": item.status,
                "activity_name": item.activity_name,
                "location_name": item.location_name,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "duration_hours": item.duration_hours,
                "distance_miles": item.distance_miles,
                "coordinates": list(item.coordinates),
                "remarks": item.remarks,
            }
            for item in result.itinerary
        ],
        "daily_logs": [
            {
                "date_string": log.date_string,
                "date_label": log.date_label,
                "total_miles_driven": log.total_miles_driven,
                "tractor_number": log.tractor_number,
                "trailer_number": log.trailer_number,
                "carrier_name": log.carrier_name,
                "timeline": [
                    {
                        "status": block.status,
                        "start_hour": block.start_hour,
                        "end_hour": block.end_hour,
                        "location_name": block.location_name,
                        "remarks": block.remarks,
                    }
                    for block in log.timeline
                ],
                "totals": log.totals,
                "remarks": [
                    {
                        "time_label": r.time_label,
                        "status": r.status,
                        "location": r.location,
                        "remarks_text": r.remarks_text,
                    }
                    for r in log.remarks
                ],
            }
            for log in result.daily_logs
        ],
    }


def _serialize_location(loc):
    return {
        "label": loc.label,
        "city": loc.city,
        "state": loc.state,
        "lat": loc.lat,
        "lng": loc.lng,
    }
