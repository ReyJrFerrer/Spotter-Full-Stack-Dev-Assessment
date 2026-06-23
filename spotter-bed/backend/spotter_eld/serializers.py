from rest_framework import serializers


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    pickup_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    dropoff_location = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)
    current_cycle_used_hrs = serializers.FloatField(required=True, min_value=0.0, max_value=70.0)
