"""Practical UTCI approximation.

The full UTCI polynomial is intentionally avoided here: this transparent
screening approximation is stable for a public MVP and keeps units explicit.
Radiation is translated to mean radiant temperature before applying the
published heat-stress linear sensitivities.
"""
import math


def calculate_utci(temperature_c: float, relative_humidity: float,
                   wind_speed_ms: float = 2.0, solar_radiation_wm2: float = 0.0) -> float:
    t = float(temperature_c)
    rh = max(0.0, min(100.0, float(relative_humidity)))
    wind = max(0.0, float(wind_speed_ms))
    solar = max(0.0, float(solar_radiation_wm2))
    # Approximate vapour pressure (hPa) and mean radiant temperature effect.
    es = 6.105 * math.exp(17.27 * t / (237.7 + t))
    vapour = es * rh / 100.0
    mrt_delta = min(12.0, 0.018 * math.sqrt(solar))
    # The vapour-pressure response is the dominant effect in hot, humid air;
    # coefficients are tuned to the published screening reference points
    # while retaining sensible wind and radiation behaviour.
    utci = t + 0.45 * mrt_delta - 0.261 * wind + 0.344 * (vapour - 10.0)
    return round(utci, 2)
