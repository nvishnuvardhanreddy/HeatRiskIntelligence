from abc import ABC, abstractmethod


class WeatherUnavailable(RuntimeError):
    """Raised when a provider cannot return trustworthy weather data."""


class WeatherProvider(ABC):
    source = "unknown"

    @abstractmethod
    def get_current_weather(self, latitude: float, longitude: float) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_hourly_weather(self, latitude: float, longitude: float) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_forecast(self, latitude: float, longitude: float) -> list[dict]:
        raise NotImplementedError

