"""Human Thermal Stress Index, normalized to 0–100."""
from .heat_index import calculate_heat_index
from .wbgt import calculate_wbgt
from .utci import calculate_utci


def risk_band(score: float) -> str:
    if score <= 20:
        return "LOW"
    if score <= 40:
        return "MODERATE"
    if score <= 60:
        return "HIGH"
    if score <= 80:
        return "VERY HIGH"
    return "EXTREME"


def calculate_htsi(temperature_c: float, relative_humidity: float,
                   wind_speed_ms: float = 2.0, solar_radiation_wm2: float = 0.0,
                   *, heat_index: float | None = None, wbgt: float | None = None,
                   utci: float | None = None) -> dict:
    t, rh, wind, solar = map(float, (temperature_c, relative_humidity, wind_speed_ms, solar_radiation_wm2))
    hi = calculate_heat_index(t, rh) if heat_index is None else float(heat_index)
    wb = calculate_wbgt(t, rh, wind, solar) if wbgt is None else float(wbgt)
    uc = calculate_utci(t, rh, wind, solar) if utci is None else float(utci)
    # Components are interpretable stress contributions. Clamp each to avoid
    # a single unusual provider value dominating the index.
    temp_component = max(0, min(100, (t - 20) * 3.2))
    humidity_component = max(0, min(100, rh * 0.45))
    wind_component = max(0, min(100, 35 - wind * 7))
    solar_component = max(0, min(100, solar / 12))
    thermal_component = max(0, min(100, (0.35 * hi + 0.4 * wb + 0.25 * uc - 20) * 2.0))
    score = round(max(0, min(100, 0.32 * thermal_component + 0.2 * temp_component
                              + 0.18 * humidity_component + 0.12 * wind_component
                              + 0.18 * solar_component)), 1)
    return {
        "score": score,
        "band": risk_band(score),
        "components": {
            "temperature": round(temp_component, 1),
            "humidity": round(humidity_component, 1),
            "wind": round(wind_component, 1),
            "solar": round(solar_component, 1),
        },
        "metrics": {"heat_index": hi, "wbgt": wb, "utci": uc},
    }

