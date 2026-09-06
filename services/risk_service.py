from thermal.htsi import calculate_htsi
from thermal.heat_index import calculate_heat_index
from thermal.utci import calculate_utci
from thermal.wbgt import calculate_wbgt
from ml_models.prediction import predict_health_risk


def thermal_summary(observation: dict) -> dict:
    t = float(observation["temperature"])
    rh = float(observation["humidity"])
    wind = float(observation.get("wind_speed") or 0)
    solar = float(observation.get("solar_radiation") or 0)
    hi = calculate_heat_index(t, rh)
    wb = calculate_wbgt(t, rh, wind, solar)
    uc = calculate_utci(t, rh, wind, solar)
    htsi = calculate_htsi(t, rh, wind, solar, heat_index=hi, wbgt=wb, utci=uc)
    return {"heat_index": hi, "wbgt": wb, "utci": uc, "htsi": htsi}


def daily_risk(day: dict) -> dict:
    observation = {
        "temperature": day["temperature_max"],
        "humidity": day["humidity"],
        "wind_speed": day["wind_speed"],
        "solar_radiation": day["solar_radiation"],
    }
    result = thermal_summary({**observation, "temperature": day["temperature_max"]})
    score = result["htsi"]["score"]
    # This is a transparent baseline estimate, not a clinical prediction.
    health = predict_health_risk({
        "htsi": score, "temperature": float(day["temperature_max"]),
        "humidity": float(day["humidity"]), "wind_speed": float(day["wind_speed"]),
        "solar_radiation": float(day["solar_radiation"]), "night_temperature": float(day["temperature_min"]),
        "vulnerability": 0,
    })
    return {**day, **result, "health_risk": health["score"], "health_band": result["htsi"]["band"],
            "health_label": health["label"], "status": "FORECAST"}
