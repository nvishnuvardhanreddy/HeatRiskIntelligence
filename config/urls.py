from django.urls import path

from core import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("analysis/", views.analysis_page, name="analysis"),
    path("forecast/", views.forecast_page, name="forecast"),
    path("hourly/", views.hourly_page, name="hourly"),
    path("map/", views.map_page, name="map"),
    path("health-risk/", views.health_page, name="health"),
    path("workers/", views.workers_page, name="workers"),
    path("history/", views.history_page, name="history"),
    path("compare/", views.compare_page, name="compare"),
    path("alerts/", views.alerts_page, name="alerts"),
    path("data-sources/", views.sources_page, name="sources"),
    path("about/", views.about_page, name="about"),
    path("methodology/", views.methodology_page, name="methodology"),
    path("api/locations/search/", views.location_search, name="location-search"),
    path("api/locations/coordinates/", views.reverse_geocode, name="coordinates"),
    path("api/locations/reverse-geocode/", views.reverse_geocode, name="reverse-geocode"),
    path("api/weather/current/", views.weather_current, name="weather-current"),
    path("api/weather/hourly/", views.weather_hourly, name="weather-hourly"),
    path("api/weather/forecast/", views.weather_forecast, name="weather-forecast"),
    path("api/risk/current/", views.risk_current, name="risk-current"),
    path("api/risk/forecast/", views.risk_forecast, name="risk-forecast"),
    path("api/risk/health/", views.risk_health, name="risk-health"),
    path("api/thermal/<slug:metric>/", views.thermal_metric, name="thermal-metric"),
]
