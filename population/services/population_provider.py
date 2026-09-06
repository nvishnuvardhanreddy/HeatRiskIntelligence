from typing import Any

import requests
from django.conf import settings


class PopulationUnavailable(Exception):
    """Raised when no configured population source can answer a request."""


def get_population(latitude: float, longitude: float) -> dict[str, Any]:
    url = settings.POPULATION_API_URL
    if not url:
        return {
            "status": "DATA UNAVAILABLE",
            "population": None,
            "source": "No population provider configured",
        }
    try:
        response = requests.get(
            url,
            params={
                "lat": latitude,
                "lon": longitude,
                "latitude": latitude,
                "longitude": longitude,
            },
            headers={"Authorization": f"Bearer {settings.POPULATION_API_KEY}"} if settings.POPULATION_API_KEY else {},
            timeout=settings.WEATHER_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise PopulationUnavailable("The population provider is temporarily unavailable.") from exc
    return {
        "status": "LIVE",
        "population": payload.get("population", payload.get("total_population")),
        "population_source": payload.get("population_source") or payload.get("source") or url,
        "population_year": payload.get("population_year") or payload.get("year"),
        "ward": payload.get("ward"),
        "district": payload.get("district"),
        "state": payload.get("state"),
        "subgroups": payload.get("subgroups") or {},
    }
