"""Deterministic clear-sky irradiance estimate used when a provider omits it."""
from datetime import datetime
import math


def estimate_solar_radiation(timestamp, latitude, cloud_cover=0):
    """Estimate W/m² from solar position and observed cloud cover.

    The timestamp returned by Open-Meteo is local to the requested coordinate.
    A compact NOAA-style solar-position approximation is used, then attenuated
    by a deterministic cloud-transmission factor.
    """
    try:
        when = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        lat = math.radians(float(latitude))
        day_of_year = when.timetuple().tm_yday
        fractional_hour = when.hour + when.minute / 60 + when.second / 3600
        equation_of_time = 9.87 * math.sin(math.radians(2 * (360 / 365) * (day_of_year - 81))) - 7.53 * math.cos(math.radians((360 / 365) * (day_of_year - 81))) - 1.5 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
        solar_time = fractional_hour + equation_of_time / 60
        declination = math.radians(23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year))))
        hour_angle = math.radians(15 * (solar_time - 12))
        elevation = math.asin(math.sin(lat) * math.sin(declination) + math.cos(lat) * math.cos(declination) * math.cos(hour_angle))
        if elevation <= 0:
            return 0.0
        air_mass = 1 / max(0.1, math.sin(elevation))
        clear_sky = 1361 * math.sin(elevation) * math.exp(-0.14 * air_mass)
        cloud = max(0.0, min(100.0, float(cloud_cover)))
        transmission = 1 - 0.75 * (cloud / 100) ** 3
        return round(max(0.0, clear_sky * transmission), 1)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("A valid weather timestamp and latitude are required for solar estimation.")
