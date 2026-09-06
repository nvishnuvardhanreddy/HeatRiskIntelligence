"""NOAA heat-index calculation in Celsius.

The Rothfusz regression is applied in Fahrenheit for warm conditions. For
cooler conditions a simple Steadman-style blend avoids implying heat stress.
"""


def calculate_heat_index(temperature_c: float, relative_humidity: float) -> float:
    t = float(temperature_c)
    rh = max(0.0, min(100.0, float(relative_humidity)))
    tf = t * 9 / 5 + 32
    if tf < 80:
        hi_f = 0.5 * (tf + 61.0 + (tf - 68.0) * 1.2 + rh * 0.094)
        return round((hi_f - 32) * 5 / 9, 2)
    hi_f = (
        -42.379 + 2.04901523 * tf + 10.14333127 * rh
        - 0.22475541 * tf * rh - 0.00683783 * tf * tf
        - 0.05481717 * rh * rh + 0.00122874 * tf * tf * rh
        + 0.00085282 * tf * rh * rh - 0.00000199 * tf * tf * rh * rh
    )
    # NOAA adjustments for unusually dry/humid conditions.
    if rh < 13 and 80 <= tf <= 112:
        hi_f -= ((13 - rh) / 4) * ((17 - abs(tf - 95)) / 17) ** 0.5
    elif rh > 85 and 80 <= tf <= 87:
        hi_f += ((rh - 85) / 10) * ((87 - tf) / 5)
    return round((hi_f - 32) * 5 / 9, 2)

