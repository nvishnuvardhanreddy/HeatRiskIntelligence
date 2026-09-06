"""Documented clear-sky solar estimate used only when a provider omits radiation."""
from datetime import datetime
import math


def estimate_solar_radiation(timestamp, latitude, cloud_cover=0):
    """Estimate W/m² from UTC hour, latitude and cloud cover.

    This is a planning estimate, not an observation, and callers must label it
    ``ESTIMATED``. It intentionally returns zero at night.
    """
    try:
        when = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        hour = when.hour + when.minute / 60
        lat_factor = max(0.25, math.cos(math.radians(float(latitude) - 20)))
        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        cloud_factor = max(0.0, 1 - max(0.0, min(100.0, float(cloud_cover))) / 100 * 0.75)
        return round(950 * daylight * lat_factor * cloud_factor, 1)
    except (TypeError, ValueError):
        return 0.0
