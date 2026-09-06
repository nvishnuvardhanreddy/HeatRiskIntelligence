from functools import lru_cache

from weather.providers.primary import OpenMeteoProvider


@lru_cache(maxsize=128)
def provider():
    return OpenMeteoProvider()


def get_current(latitude, longitude):
    return provider().get_current_weather(latitude, longitude)


def get_hourly(latitude, longitude):
    return provider().get_hourly_weather(latitude, longitude)


def get_forecast(latitude, longitude):
    return provider().get_forecast(latitude, longitude)


def search(query):
    return provider().search(query)

