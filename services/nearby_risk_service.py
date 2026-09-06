from math import asin, cos, radians, sin, sqrt

from services.location_service import reverse_geocode
from services.risk_service import thermal_summary
from services.solar import estimate_solar_radiation, is_daytime
from services.weather_service import get_current, search
from population.services.population_service import population_for_location
from population.services.population_provider import PopulationUnavailable


def _distance_km(lat1, lon1, lat2, lon2):
    earth_radius = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    value = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return round(earth_radius * 2 * asin(sqrt(value)), 1)


def _band(score):
    if score <= 20:
        return "LOW"
    if score <= 40:
        return "MODERATE"
    if score <= 60:
        return "HIGH"
    if score <= 80:
        return "VERY HIGH"
    return "EXTREME"


def _candidate_queries(location):
    values = [location.get("name"), location.get("district")]
    return [value for value in values if value and value != "Selected location"]


def nearby_risk(latitude, longitude):
    selected = reverse_geocode(latitude, longitude)
    candidates = [{
        "name": selected.get("name") or "Selected area",
        "latitude": float(latitude),
        "longitude": float(longitude),
        "admin_area": selected.get("admin_area", ""),
        "district": selected.get("district", ""),
        "country": selected.get("country", ""),
    }]
    for query in _candidate_queries(selected):
        for result in search(query, count=10):
            try:
                result_lat = float(result["latitude"])
                result_lon = float(result["longitude"])
            except (KeyError, TypeError, ValueError, PopulationUnavailable):
                continue
            if not (6 <= result_lat <= 37 and 68 <= result_lon <= 98):
                continue
            if _distance_km(latitude, longitude, result_lat, result_lon) <= 120:
                candidates.append(result)

    unique = {}
    for candidate in candidates:
        key = (round(float(candidate["latitude"]), 4), round(float(candidate["longitude"]), 4))
        unique[key] = candidate

    rows = []
    for candidate in unique.values():
        distance = _distance_km(latitude, longitude, candidate["latitude"], candidate["longitude"])
        try:
            weather = get_current(candidate["latitude"], candidate["longitude"])
            provider_is_day = weather.get("is_day")
            daytime = bool(provider_is_day) if provider_is_day is not None else is_daytime(
                weather.get("timestamp"), candidate["latitude"], candidate["longitude"]
            )
            if weather.get("solar_radiation") is None or (
                float(weather.get("solar_radiation") or 0) <= 0 and daytime
            ):
                weather["solar_radiation"] = estimate_solar_radiation(
                    weather.get("timestamp"), candidate["latitude"],
                    weather.get("cloud_cover", 0), candidate["longitude"]
                )
            thermal = thermal_summary(weather)
            population = population_for_location(candidate["latitude"], candidate["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        score = float(thermal["htsi"]["score"])
        total_population = max(0, int(population.get("population") or 0))
        rows.append({
            "area": candidate.get("name") or "Selected area",
            "ward": candidate.get("ward"),
            "district": candidate.get("district") or selected.get("district"),
            "state": candidate.get("admin_area") or selected.get("admin_area"),
            "latitude": candidate["latitude"],
            "longitude": candidate["longitude"],
            "distance_km": distance,
            "population": total_population,
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "wind_speed": weather.get("wind_speed"),
            "solar_radiation": weather.get("solar_radiation"),
            "heat_index": thermal["heat_index"],
            "wbgt": thermal["wbgt"],
            "utci": thermal["utci"],
            "htsi": score,
            "risk": _band(score),
        })

    maximum_population = max((row["population"] for row in rows), default=1)
    for row in rows:
        population_factor = row["population"] / maximum_population if maximum_population else 0
        row["priority_score"] = round((0.7 * row["htsi"]) + (0.3 * population_factor * 100), 1)
        row["priority"] = "HIGH" if row["priority_score"] >= 61 else "MODERATE" if row["priority_score"] >= 41 else "LOW"
    rows.sort(key=lambda row: (row["priority_score"], row["htsi"]), reverse=True)

    district_rows = [row for row in rows if row["district"] == selected.get("district")] or rows
    total_population = sum(row["population"] for row in district_rows)
    weighted_htsi = (
        sum(row["htsi"] * row["population"] for row in district_rows) / total_population
        if total_population else sum(row["htsi"] for row in district_rows) / max(len(district_rows), 1)
    )
    district = {
        "name": selected.get("district") or selected.get("name") or "Selected district",
        "population": total_population,
        "average_htsi": round(weighted_htsi, 1),
        "risk": _band(weighted_htsi),
        "highest_risk_area": max(district_rows, key=lambda row: row["htsi"])["area"] if district_rows else "Selected area",
        "high_risk_areas": sum(row["htsi"] >= 41 for row in district_rows),
    }
    return {"areas": rows[:5], "district": district}
