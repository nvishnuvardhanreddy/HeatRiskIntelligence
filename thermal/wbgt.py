"""Outdoor WBGT approximation with estimated globe temperature.

When globe temperature is unavailable, solar radiation and wind are used to
estimate it. The response explicitly labels this metric as calculated.
"""
import math


def _wet_bulb(temperature_c: float, rh: float) -> float:
    # Stull (2011) approximation, valid for ordinary outdoor conditions.
    t, h = float(temperature_c), max(1.0, min(100.0, float(rh)))
    return round(
        t * math.atan(0.151977 * math.sqrt(h + 8.313659))
        + math.atan(t + h)
        - math.atan(h - 1.676331)
        + 0.00391838 * h ** 1.5 * math.atan(0.023101 * h)
        - 4.686035,
        3,
    )


def calculate_wbgt(temperature_c: float, relative_humidity: float,
                   wind_speed_ms: float = 2.0, solar_radiation_wm2: float = 0.0) -> float:
    t = float(temperature_c)
    rh = max(0.0, min(100.0, float(relative_humidity)))
    wind = max(0.1, float(wind_speed_ms))
    solar = max(0.0, float(solar_radiation_wm2))
    tw = _wet_bulb(t, rh)
    # Empirical outdoor globe estimate; never presented as an observation.
    globe = t + 0.00025 * solar / (1 + 0.12 * math.sqrt(wind)) - 0.18 * math.sqrt(wind)
    wbgt = 0.7 * tw + 0.2 * globe + 0.1 * t
    return round(wbgt, 2)

