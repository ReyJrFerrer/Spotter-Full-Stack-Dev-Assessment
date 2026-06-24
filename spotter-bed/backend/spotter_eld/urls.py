from django.http import JsonResponse
from django.urls import path

from spotter_eld.views import HealthView, LocationAutocompleteView, TripGenerateView, TripPdfExportView

def api_root(request):
    return JsonResponse({
        "service": "Spotter ELD API",
        "status": "running",
        "endpoints": {
            "health": "/api/health/",
            "generate": "/api/trips/generate/",
            "export_pdf": "/api/trips/export-pdf/",
            "autocomplete": "/api/locations/autocomplete/?q=city"
        }
    })

urlpatterns = [
    path("", api_root, name="api-root"),
    path("api/health/", HealthView.as_view(), name="api-health"),
    path("api/trips/generate/", TripGenerateView.as_view(), name="api-trips-generate"),
    path("api/trips/export-pdf/", TripPdfExportView.as_view(), name="api-trips-export-pdf"),
    path("api/locations/autocomplete/", LocationAutocompleteView.as_view(), name="api-locations-autocomplete"),
]
