from rest_framework import serializers


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    pickup_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    dropoff_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    current_cycle_used_hrs = serializers.FloatField(required=True, min_value=0.0, max_value=70.0)


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
