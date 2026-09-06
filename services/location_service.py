import requests
from django.conf import settings


def _component(components, component_type):
    for component in components:
        if component_type in component.get("types", []):
            return component.get("long_name", "")
    return ""


def _location_payload(latitude, longitude, address, source):
    city = (
        _component(address, "locality")
        or _component(address, "postal_town")
        or _component(address, "sublocality_level_1")
        or _component(address, "administrative_area_level_3")
        or _component(address, "administrative_area_level_2")
        or "Selected location"
    )
    district = (
        _component(address, "administrative_area_level_2")
        or _component(address, "administrative_area_level_3")
        or ""
    )
    return {
        "name": city,
        "admin_area": _component(address, "administrative_area_level_1"),
        "district": district,
        "country": _component(address, "country"),
        "postcode": _component(address, "postal_code"),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "ward": _component(address, "sublocality_level_2") or None,
        "ward_note": "Ward-level data unavailable for this location.",
        "source": source,
    }


def _google_reverse_geocode(latitude, longitude):
    if not settings.GOOGLE_MAPS_API_KEY:
        return None
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={
            "latlng": f"{latitude},{longitude}",
            "key": settings.GOOGLE_MAPS_API_KEY,
            "language": "en",
            "region": "in",
        },
        timeout=settings.WEATHER_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "OK" or not payload.get("results"):
        return None
    return _location_payload(
        latitude,
        longitude,
        payload["results"][0].get("address_components", []),
        "Google Maps Geocoding",
    )


def reverse_geocode(latitude, longitude):
    """Resolve a readable area name, preferring Google Maps when configured."""
    try:
        google_location = _google_reverse_geocode(latitude, longitude)
        if google_location:
            return google_location
    except (requests.RequestException, ValueError, TypeError):
        pass
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": latitude, "lon": longitude, "format": "jsonv2", "zoom": 10},
            headers={"User-Agent": "GroundZero/1.0 public heat safety dashboard"},
            timeout=settings.WEATHER_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        address = response.json().get("address", {})
        return _location_payload(
            latitude,
            longitude,
            [
                {"types": ["locality"], "long_name": address.get("city") or address.get("town") or address.get("village") or ""},
                {"types": ["administrative_area_level_1"], "long_name": address.get("state") or ""},
                {"types": ["administrative_area_level_2"], "long_name": address.get("state_district") or address.get("county") or ""},
                {"types": ["country"], "long_name": address.get("country") or ""},
                {"types": ["postal_code"], "long_name": address.get("postcode") or ""},
            ],
            "OpenStreetMap Nominatim",
        )
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
