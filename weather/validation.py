from datetime import datetime


def validate_observation(observation: dict) -> list[str]:
    errors = []
    required = ("temperature", "humidity", "wind_speed", "solar_radiation", "pressure", "timestamp")
    for key in required:
        if observation.get(key) is None:
            errors.append(f"Missing {key}.")
    if observation.get("humidity") is not None and not 0 <= float(observation["humidity"]) <= 100:
        errors.append("Humidity must be between 0 and 100%.")
    if observation.get("wind_speed") is not None and float(observation["wind_speed"]) < 0:
        errors.append("Wind speed cannot be negative.")
    if observation.get("solar_radiation") is not None and float(observation["solar_radiation"]) < 0:
        errors.append("Solar radiation cannot be negative.")
    if observation.get("pressure") is not None and float(observation["pressure"]) <= 0:
        errors.append("Pressure must be positive.")
    if observation.get("timestamp"):
        try:
            datetime.fromisoformat(str(observation["timestamp"]).replace("Z", "+00:00"))
        except ValueError:
            errors.append("Timestamp is not valid ISO format.")
    return errors


def forecast_anomalies(rows: list[dict]) -> list[str]:
    warnings = []
    for previous, current in zip(rows, rows[1:]):
        if abs(float(current.get("temperature_max", 0)) - float(previous.get("temperature_max", 0))) > 10:
            warnings.append(f"Large forecast temperature change near {current.get('date', 'unknown date')}.")
    return warnings

