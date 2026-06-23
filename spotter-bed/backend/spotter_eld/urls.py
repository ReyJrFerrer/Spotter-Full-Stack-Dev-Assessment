from django.urls import path

from spotter_eld.views import HealthView, TripGenerateView

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="api-health"),
    path("api/trips/generate/", TripGenerateView.as_view(), name="api-trips-generate"),
]
