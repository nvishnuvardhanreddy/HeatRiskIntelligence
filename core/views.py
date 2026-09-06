from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from services.location_service import reverse_geocode as lookup_location
from services.risk_service import daily_risk, thermal_summary
from services.solar import estimate_solar_radiation
from ml_models.prediction import predict_health_risk
from services.weather_service import get_current, get_forecast, get_hourly, search
from weather.providers.base import WeatherUnavailable
from weather.validation import forecast_anomalies, validate_observation
from population.services.population_service import population_for_location
from population.services.population_provider import PopulationUnavailable


def _coordinates(request):
    try:
        latitude = float(request.GET.get("lat", request.GET.get("latitude")))
        longitude = float(request.GET.get("lon", request.GET.get("longitude")))
    except (TypeError, ValueError):
        raise ValueError("Provide numeric lat and lon query parameters.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates are outside valid geographic bounds.")
    return latitude, longitude


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _current_payload(request):
    latitude, longitude = _coordinates(request)
    observation = get_current(latitude, longitude)
    # Open-Meteo exposes observed shortwave radiation. If it is missing, the
    # response says so rather than presenting a made-up measurement.
    if observation.get("solar_radiation") is None:
        observation["solar_radiation"] = estimate_solar_radiation(
            observation.get("timestamp"), latitude, observation.get("cloud_cover", 0)
        )
        observation["solar_status"] = "ESTIMATED"
    else:
        observation["solar_status"] = "LIVE"
    errors = validate_observation(observation)
    if errors:
        raise ValueError("Weather data failed validation: " + " ".join(errors))
    return latitude, longitude, observation, thermal_summary(observation)


def _page(request, template, title):
    return render(request, template, {"page_title": title})


def dashboard(request):
    return _page(request, "dashboard.html", "Monitor")


def overview_page(request):
    return _page(request, "overview.html", "Overview")


def what_if_page(request):
    return _page(request, "what_if.html", "What-if simulation")


def analysis_page(request):
    return _page(request, "analysis.html", "Thermal analysis")


def forecast_page(request):
    return _page(request, "forecast.html", "Five-day forecast")


def hourly_page(request):
    return _page(request, "hourly.html", "Hourly heat")


def map_page(request):
    return _page(request, "map.html", "India risk map")


def health_page(request):
    return _page(request, "health.html", "Health risk")


def workers_page(request):
    return _page(request, "workers.html", "Outdoor worker view")


def history_page(request):
    return _page(request, "history.html", "Historical analysis")


def compare_page(request):
    return _page(request, "compare.html", "Compare locations")


def alerts_page(request):
    return _page(request, "alerts.html", "Heat alerts")


def sources_page(request):
    return _page(request, "sources.html", "Data sources")


def about_page(request):
    return _page(request, "about.html", "About Ground Zero")


def methodology_page(request):
    return _page(request, "methodology.html", "Methodology")


@require_GET
def location_search(request):
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return _error("Search requires at least two characters.")
    try:
        return JsonResponse({"results": search(query)})
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def reverse_geocode(request):
    try:
        latitude, longitude = _coordinates(request)
        return JsonResponse({"location": lookup_location(latitude, longitude)})
    except ValueError as exc:
        return _error(str(exc))


@require_GET
def population_location(request):
    try:
        latitude, longitude = _coordinates(request)
        return JsonResponse(population_for_location(latitude, longitude))
    except ValueError as exc:
        return _error(str(exc))
    except PopulationUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def weather_current(request):
    try:
        latitude, longitude, observation, thermal = _current_payload(request)
        location = lookup_location(latitude, longitude)
        return JsonResponse({
            "location": location,
            "weather": observation,
            "thermal": thermal,
            "labels": {"weather": "LIVE", "thermal": "CALCULATED",
                       "solar": observation["solar_status"]},
        })
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def weather_hourly(request):
    try:
        latitude, longitude = _coordinates(request)
        rows = []
        for row in get_hourly(latitude, longitude):
            try:
                rows.append({**row, "thermal": thermal_summary(row), "status": "FORECAST"})
            except (KeyError, TypeError, ValueError):
                # Keep the provider value visible but flag incomplete rows.
                rows.append({**row, "status": "DATA QUALITY NOTE"})
        return JsonResponse({"latitude": latitude, "longitude": longitude, "hourly": rows, "label": "FORECAST"})
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def weather_forecast(request):
    try:
        latitude, longitude = _coordinates(request)
        rows = [daily_risk(row) for row in get_forecast(latitude, longitude)]
        return JsonResponse({
            "latitude": latitude, "longitude": longitude, "forecast": rows,
            "anomalies": forecast_anomalies(rows), "label": "FORECAST",
        })
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def risk_current(request):
    try:
        latitude, longitude, observation, thermal = _current_payload(request)
        score = thermal["htsi"]["score"]
        health = predict_health_risk({
            "htsi": score, "temperature": float(observation["temperature"]),
            "humidity": float(observation["humidity"]), "wind_speed": float(observation["wind_speed"]),
            "solar_radiation": float(observation["solar_radiation"]),
            "night_temperature": float(observation["temperature"]), "vulnerability": 0,
        })
        return JsonResponse({
            "location": lookup_location(latitude, longitude),
            "weather": observation,
            "thermal": thermal,
            "risk": {"score": score, "band": thermal["htsi"]["band"],
                     "label": "CALCULATED", "reason": risk_reason(observation, thermal)},
            "health": {"score": health["score"], "band": thermal["htsi"]["band"], "label": health["label"]},
        })
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def risk_forecast(request):
    try:
        latitude, longitude = _coordinates(request)
        rows = [daily_risk(row) for row in get_forecast(latitude, longitude)]
        return JsonResponse({"latitude": latitude, "longitude": longitude, "forecast": rows,
                             "anomalies": forecast_anomalies(rows), "label": "CALCULATED"})
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def risk_health(request):
    try:
        _, _, observation, thermal = _current_payload(request)
        score = predict_health_risk({
            "htsi": thermal["htsi"]["score"], "temperature": float(observation["temperature"]),
            "humidity": float(observation["humidity"]), "wind_speed": float(observation["wind_speed"]),
            "solar_radiation": float(observation["solar_radiation"]), "night_temperature": float(observation["temperature"]),
            "vulnerability": 0,
        })["score"]
        return JsonResponse({
            "score": score, "band": thermal["htsi"]["band"], "label": "MODEL ESTIMATE",
            "factors": ["Thermal stress", "Exposure duration", "Humidity",
                        "Night-time temperature", "Vulnerability"],
            "disclaimer": "Baseline estimate — not a clinical or mortality prediction.",
        })
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


@require_GET
def health_check(request):
    """Small unauthenticated probe for Render and load balancers."""
    return JsonResponse({"status": "ok", "service": "ground-zero"})


@require_http_methods(["GET", "POST"])
def what_if_api(request):
    """Calculate a scenario from user-entered weather values.

    Scenarios are deliberately separate from the Open-Meteo observation APIs:
    they never masquerade as measured weather and are labelled as simulated.
    """
    inputs = request.GET if request.method == "GET" else request.POST

    def value(*names):
        for name in names:
            raw = inputs.get(name)
            if raw not in (None, ""):
                return float(raw)
        raise ValueError(f"Provide a numeric {names[0]} value.")

    try:
        temperature = value("temperature", "temp")
        humidity = value("humidity", "rh")
        wind = value("wind_speed", "wind")
        solar = value("solar_radiation", "solar")
        if not -80 <= temperature <= 70:
            raise ValueError("Temperature must be between -80 and 70 °C.")
        if not 0 <= humidity <= 100:
            raise ValueError("Humidity must be between 0 and 100%.")
        if wind < 0 or solar < 0:
            raise ValueError("Wind and solar radiation cannot be negative.")
        thermal = thermal_summary({
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind,
            "solar_radiation": solar,
        })
        return JsonResponse({
            "scenario": {
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind,
                "solar_radiation": solar,
            },
            "thermal": thermal,
            "risk": thermal["htsi"],
            "label": "SIMULATED",
            "disclaimer": "A what-if calculation, not observed or forecast weather.",
        })
    except (TypeError, ValueError) as exc:
        return _error(str(exc))


@require_GET
def thermal_metric(request, metric):
    try:
        _, _, observation, thermal = _current_payload(request)
        values = {"heat-index": "heat_index", "wbgt": "wbgt", "utci": "utci", "htsi": "htsi"}
        key = values.get(metric)
        if not key:
            return _error("Unknown thermal metric.")
        return JsonResponse({"metric": metric, "value": thermal[key], "label": "CALCULATED"})
    except ValueError as exc:
        return _error(str(exc))
    except WeatherUnavailable as exc:
        return _error(str(exc), 503)


def risk_reason(observation, thermal):
    reasons = []
    if float(observation["temperature"]) >= 35:
        reasons.append("Temperature is elevated.")
    if float(observation["humidity"]) >= 60:
        reasons.append("Humidity is increasing perceived heat.")
    if float(observation.get("wind_speed") or 0) < 2:
        reasons.append("Wind speed is low.")
    if float(observation.get("solar_radiation") or 0) >= 500:
        reasons.append("Solar radiation is strong.")
    return reasons or ["Current atmospheric conditions are within a lower-stress range."]
