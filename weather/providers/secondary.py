"""Secondary-provider seam.

Open-Meteo is the no-key primary provider for the MVP. A future provider can
implement WeatherProvider here without changing the views or thermal engine.
"""
from .base import WeatherProvider, WeatherUnavailable


class SecondaryProvider(WeatherProvider):
    source = "secondary provider (not configured)"

    def _unavailable(self):
        raise WeatherUnavailable("No secondary weather provider is configured.")

    def get_current_weather(self, latitude, longitude):
        self._unavailable()

    def get_hourly_weather(self, latitude, longitude):
        self._unavailable()

    def get_forecast(self, latitude, longitude):
        self._unavailable()
