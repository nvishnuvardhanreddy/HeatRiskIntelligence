import requests
from django.conf import settings


def reverse_geocode(latitude, longitude):
    """Best-effort public reverse geocode; never invents a ward boundary."""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": latitude, "lon": longitude, "format": "jsonv2", "zoom": 10},
            headers={"User-Agent": "GroundZero/1.0 public heat safety dashboard"},
            timeout=settings.WEATHER_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        address = response.json().get("address", {})
        return {
            "name": address.get("city") or address.get("town") or address.get("village") or "Selected location",
            "admin_area": address.get("state") or address.get("county") or "",
            "district": address.get("state_district") or address.get("county") or "",
            "country": address.get("country") or "",
            "postcode": address.get("postcode") or "",
            "latitude": float(latitude),
            "longitude": float(longitude),
            "ward": None,
            "ward_note": "Ward-level data unavailable for this location.",
            "source": "OpenStreetMap Nominatim",
        }
    except (requests.RequestException, ValueError, TypeError):
        return {
            "name": "Selected location",
            "admin_area": "India" if 6 <= float(latitude) <= 37 and 68 <= float(longitude) <= 98 else "",
            "district": "",
            "country": "India" if 6 <= float(latitude) <= 37 and 68 <= float(longitude) <= 98 else "",
            "postcode": "",
            "latitude": float(latitude),
            "longitude": float(longitude),
            "ward": None,
            "ward_note": "Ward-level data unavailable for this location.",
            "source": "Coordinate input",
        }

