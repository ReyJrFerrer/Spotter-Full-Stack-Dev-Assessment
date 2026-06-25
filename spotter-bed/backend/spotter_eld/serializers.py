from rest_framework import serializers
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class _NaiveDateTimeField(serializers.Field):
    """Parses an ISO 8601 datetime string. If the string has no timezone
    offset (the frontend form's contract: "user picked wall-clock in the
    trip timezone"), the result is a naive datetime so the view can
    anchor it in the trip timezone. If the string has an explicit offset
    (e.g. "...Z" or "...+05:00"), the result is kept aware so the view
    respects the caller's intent."""

    def to_internal_value(self, value):
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise serializers.ValidationError("Must be an ISO 8601 datetime string")
        try:
            dt = datetime.fromisoformat(value)
        except ValueError as exc:
            raise serializers.ValidationError(f"Invalid ISO 8601 datetime: {exc}")
        return dt

    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    pickup_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    dropoff_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    current_cycle_used_hrs = serializers.FloatField(required=True, min_value=0.0, max_value=70.0)
    start_time = _NaiveDateTimeField(required=False, allow_null=True)
    timezone = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_timezone(self, value):
        if not value:
            return "UTC"
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise serializers.ValidationError(f"Unknown IANA timezone: {value}")
        return value


class LocationSerializer(serializers.Serializer):
    label = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)


class TripSummarySerializer(serializers.Serializer):
    from_label = serializers.CharField(required=True, allow_blank=True)
    pickup_label = serializers.CharField(required=True, allow_blank=True)
    dropoff_label = serializers.CharField(required=True, allow_blank=True)
    total_distance_miles = serializers.IntegerField(required=True, min_value=0)
    total_duration_hours = serializers.FloatField(required=True, min_value=0.0)
    current_cycle_used_hrs = serializers.FloatField(required=True, min_value=0.0, max_value=70.0)
    trip_days = serializers.IntegerField(required=True, min_value=1)
    carrier_name = serializers.CharField(required=True, allow_blank=True)
    tractor_number = serializers.CharField(required=True, allow_blank=True)
    trailer_number = serializers.CharField(required=True, allow_blank=True)


class TimelineBlockSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OFF", "SB", "D", "ON"], required=True)
    start_hour = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)
    end_hour = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)
    location_name = serializers.CharField(required=True, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TotalsSerializer(serializers.Serializer):
    OFF = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)
    SB = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)
    D = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)
    ON = serializers.FloatField(required=True, min_value=0.0, max_value=24.0)


class RemarksSerializer(serializers.Serializer):
    time_label = serializers.CharField(required=True)
    status = serializers.ChoiceField(choices=["OFF", "SB", "D", "ON"], required=True)
    location = serializers.CharField(required=True, allow_blank=True)
    remarks_text = serializers.CharField(required=True, allow_blank=True)


class DailyLogSerializer(serializers.Serializer):
    date_string = serializers.CharField(required=True)
    date_label = serializers.CharField(required=True)
    total_miles_driven = serializers.IntegerField(required=True, min_value=0)
    tractor_number = serializers.CharField(required=True, allow_blank=True)
    trailer_number = serializers.CharField(required=True, allow_blank=True)
    carrier_name = serializers.CharField(required=True, allow_blank=True)
    timeline = TimelineBlockSerializer(many=True, required=True)
    totals = TotalsSerializer(required=True)
    remarks = RemarksSerializer(many=True, required=True)


class PdfExportRequestSerializer(serializers.Serializer):
    summary = TripSummarySerializer(required=True)
    daily_logs = DailyLogSerializer(many=True, required=True)
