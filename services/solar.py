"""Deterministic clear-sky irradiance estimate used when a provider omits it."""
from datetime import datetime
import math


def _solar_elevation(when, latitude, longitude):
    """Return solar elevation angle in radians for the given local datetime and coordinates.

    The timestamp is treated as local civil time at the given longitude.
    A longitude-based UTC offset correction and the equation of time are applied
    to compute true solar time before calculating elevation.
    """
    lat_r = math.radians(float(latitude))
    lon = float(longitude)
    day_of_year = when.timetuple().tm_yday

    # Derive UTC offset: use tzinfo if available, otherwise approximate from longitude.
    if when.tzinfo is not None and when.utcoffset() is not None:
        utc_offset_hours = when.utcoffset().total_seconds() / 3600
    else:
        utc_offset_hours = lon / 15.0

    local_hour = when.hour + when.minute / 60 + when.second / 3600

    # Longitude correction: offset between standard meridian for this UTC zone and
    # the actual longitude, expressed in hours.
    standard_meridian = round(utc_offset_hours) * 15
    longitude_correction = (lon - standard_meridian) / 15.0  # hours

    # Equation of time (Spencer 1971 compact form), in minutes.
    b_rad = math.radians((360 / 365) * (day_of_year - 81))
    equation_of_time = (
        9.87 * math.sin(2 * b_rad)
        - 7.53 * math.cos(b_rad)
        - 1.5 * math.sin(b_rad)
    )

    # True solar time in fractional hours.
    solar_time = local_hour + longitude_correction + equation_of_time / 60

    declination = math.radians(
        23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
    )
    hour_angle = math.radians(15 * (solar_time - 12))
    elevation = math.asin(
        math.sin(lat_r) * math.sin(declination)
        + math.cos(lat_r) * math.cos(declination) * math.cos(hour_angle)
    )
    return elevation


def estimate_solar_radiation(timestamp, latitude, cloud_cover=0, longitude=0):
    """Estimate W/m² from solar position and observed cloud cover.

    The timestamp returned by Open-Meteo is local to the requested coordinate
    (when timezone=auto is used). The solar position is corrected for the
    difference between the location's standard meridian and its actual
    longitude, and for the equation of time, so that solar noon is accurate.

    Args:
        timestamp:   ISO-8601 string or datetime.  Timezone-aware values are
                     used as-is; naive values are treated as local civil time
                     at the given longitude.
        latitude:    Decimal degrees, −90 … 90.
        cloud_cover: Percentage 0–100.  Defaults to 0 (clear sky).
        longitude:   Decimal degrees, −180 … 180.  Required for an accurate
                     solar-noon correction.  Defaults to 0 (prime meridian).
    """
    try:
        when = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        elevation = _solar_elevation(when, latitude, longitude)
        if elevation <= 0:
            return 0.0
        air_mass = 1 / max(0.1, math.sin(elevation))
        clear_sky = 1361 * math.sin(elevation) * math.exp(-0.14 * air_mass)
        cloud = max(0.0, min(100.0, float(cloud_cover)))
        transmission = 1 - 0.75 * (cloud / 100) ** 3
        return round(max(0.0, clear_sky * transmission), 1)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            "A valid weather timestamp and latitude are required for solar estimation."
        )


def is_daytime(timestamp, latitude=20.0, longitude=78.0):
    """Return whether a provider timestamp falls in the daylight window.

    Uses the true solar elevation angle computed from latitude/longitude rather
    than a hard-coded 6–18 h clock window, so early morning, late evening, and
    high-latitude edge cases are handled correctly.  A −3° civil-twilight buffer
    is included so the transition hours are treated as daytime.

    Falls back to a simple 5–19 h heuristic if coordinate-based calculation
    fails.
    """
    try:
        when = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        try:
            elevation = _solar_elevation(when, latitude, longitude)
            # Include civil twilight (sun within 3° below horizon).
            return elevation > math.radians(-3)
        except (TypeError, ValueError, OverflowError):
            # Fallback: simple hour-based heuristic on local timestamp.
            return 5 <= when.hour <= 19
    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            "A valid weather timestamp is required for daylight detection."
        )
