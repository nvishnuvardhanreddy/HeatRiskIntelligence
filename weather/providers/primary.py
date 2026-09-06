from datetime import datetime
import logging
from typing import Any

import requests
from time import sleep
from django.conf import settings

from .base import WeatherProvider, WeatherUnavailable

logger = logging.getLogger(__name__)


class OpenMeteoProvider(WeatherProvider):
    source = "Open-Meteo"
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"

    def _get(self, url: str, params: dict[str, Any]) -> dict:
        last_error = None
        for attempt in range(3):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=max(10, settings.WEATHER_REQUEST_TIMEOUT),
                    headers={"Accept": "application/json", "User-Agent": "GroundZero/1.0"},
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Weather provider returned an invalid response.")
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                logger.warning("Open-Meteo request failed (attempt %s/3): %s", attempt + 1, exc)
                if attempt < 2:
                    sleep(0.5 * (attempt + 1))
        raise WeatherUnavailable("The weather provider is temporarily unavailable.") from last_error

    @staticmethod
    def _coords(latitude, longitude):
        try:
            lat, lon = float(latitude), float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError("Coordinates must be numeric.") from exc
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError("Coordinates are outside valid geographic bounds.")
        return lat, lon

    def _params(self, latitude, longitude, *, include_current=False, include_hourly=False, include_daily=False):
        lat, lon = self._coords(latitude, longitude)
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto",
        }
        if include_current:
            params["current"] = ",".join([
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "wind_speed_10m", "wind_direction_10m", "shortwave_radiation",
                "surface_pressure", "cloud_cover", "precipitation", "uv_index",
                "dew_point_2m", "is_day",
            ])
        if include_hourly:
            params["forecast_days"] = 3
            params["hourly"] = ",".join([
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "wind_speed_10m", "wind_direction_10m", "shortwave_radiation",
                "surface_pressure", "cloud_cover", "precipitation", "uv_index", "dew_point_2m",
            ])
        if include_daily:
            params["forecast_days"] = 6
            params["daily"] = ",".join([
                "temperature_2m_min", "temperature_2m_max", "relative_humidity_2m_mean",
                "wind_speed_10m_max", "shortwave_radiation_sum", "precipitation_sum",
            ])
        return params

    @staticmethod
    def _at(data: dict, key: str, index: int, default: float = 0.0):
        values = data.get(key) or []
        value = values[index] if index < len(values) else default
        return default if value is None else value

    def _hourly_rows(self, payload: dict) -> list[dict]:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        rows = []
        for index, timestamp in enumerate(times):
            rows.append({
                "timestamp": timestamp,
                "temperature": self._at(hourly, "temperature_2m", index),
                "humidity": self._at(hourly, "relative_humidity_2m", index),
                "apparent_temperature": self._at(hourly, "apparent_temperature", index),
                "wind_speed": self._at(hourly, "wind_speed_10m", index) / 3.6,
                "wind_speed_unit": "m/s",
                "wind_direction": self._at(hourly, "wind_direction_10m", index),
                "solar_radiation": self._at(hourly, "shortwave_radiation", index),
                "pressure": self._at(hourly, "surface_pressure", index),
                "cloud_cover": self._at(hourly, "cloud_cover", index),
                "precipitation": self._at(hourly, "precipitation", index),
                "uv_index": self._at(hourly, "uv_index", index),
                "dew_point": self._at(hourly, "dew_point_2m", index),
                "source": self.source,
            })
        return rows

    def get_current_weather(self, latitude, longitude) -> dict:
        payload = self._get(self.forecast_url, self._params(latitude, longitude, include_current=True))
        current = payload.get("current") or {}
        wind_kmh = current.get("wind_speed_10m")
        return {
            "timestamp": current.get("time") or datetime.utcnow().isoformat(),
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            # Open-Meteo publishes wind in km/h; normalize the provider
            # contract to m/s for thermal calculations.
            "wind_speed": None if wind_kmh is None else float(wind_kmh) / 3.6,
            "wind_speed_unit": "m/s",
            "wind_direction": current.get("wind_direction_10m"),
            "solar_radiation": current.get("shortwave_radiation"),
            "pressure": current.get("surface_pressure"),
            "cloud_cover": current.get("cloud_cover"),
            "precipitation": current.get("precipitation"),
            "uv_index": current.get("uv_index"),
            "dew_point": current.get("dew_point_2m"),
            # is_day=1 means daytime per Open-Meteo; forwarded so the view can
            # use it as the authoritative signal instead of estimating from the
            # solar elevation angle.
            "is_day": current.get("is_day"),
            "source": self.source,
            "timezone": payload.get("timezone"),
        }

    def get_hourly_weather(self, latitude, longitude) -> list[dict]:
        return self._hourly_rows(self._get(self.forecast_url, self._params(latitude, longitude, include_hourly=True)))

    def get_forecast(self, latitude, longitude) -> list[dict]:
        payload = self._get(self.forecast_url, self._params(latitude, longitude, include_daily=True))
        daily = payload.get("daily") or {}
        times = daily.get("time") or []
        rows = []
        for index, day in enumerate(times[:5]):
            rows.append({
                "date": day,
                "temperature_min": self._at(daily, "temperature_2m_min", index),
                "temperature_max": self._at(daily, "temperature_2m_max", index),
                "humidity": self._at(daily, "relative_humidity_2m_mean", index),
                "wind_speed": self._at(daily, "wind_speed_10m_max", index) / 3.6,
                "wind_speed_unit": "m/s",
                # Daily radiation is MJ/m²; convert to a 24-hour mean W/m²
                # so the same thermal functions can consume it.
                "solar_radiation": self._at(daily, "shortwave_radiation_sum", index) * 1000000 / 86400,
                "precipitation": self._at(daily, "precipitation_sum", index),
                "source": self.source,
            })
        return rows

    def search(self, query: str, count: int = 8) -> list[dict]:
        payload = self._get(self.geocode_url, {"name": query, "count": count, "language": "en", "format": "json"})
        return [
            {
                "name": item.get("name"),
                "admin_area": item.get("admin1") or item.get("admin2") or "",
                "country": item.get("country") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
                "source": "Open-Meteo geocoding",
            }
            for item in payload.get("results", [])
        ]
