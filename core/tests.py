from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse


SAMPLE_CURRENT = {
    "timestamp": "2026-09-06T12:00",
    "temperature": 35.0,
    "humidity": 65.0,
    "apparent_temperature": 40.0,
    "wind_speed": 2.0,
    "wind_direction": 180,
    "solar_radiation": 650.0,
    "pressure": 1008.0,
    "cloud_cover": 20,
    "precipitation": 0,
    "uv_index": 7,
    "dew_point": 27.0,
    "source": "Open-Meteo",
}


class ApiTests(TestCase):
    def test_health_endpoint(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_overview_and_what_if_pages(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/what-if/").status_code, 200)

    def test_what_if_api_is_explicitly_simulated(self):
        response = self.client.get(
            "/api/what-if/?temperature=35&humidity=65&wind_speed=2&solar_radiation=500"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["label"], "SIMULATED")
        self.assertIn("heat_index", body["thermal"])
        self.assertIn("risk", body)

    @patch("core.views.lookup_location", return_value={
        "name": "Test City", "admin_area": "Test State", "country": "India",
        "latitude": 17.7, "longitude": 83.2,
    })
    @patch("core.views.get_current", return_value=SAMPLE_CURRENT)
    def test_current_risk_api_returns_labels(self, current, location):
        response = self.client.get("/api/risk/current/?lat=17.7&lon=83.2")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("thermal", body)
        self.assertEqual(body["risk"]["label"], "CALCULATED")
        self.assertEqual(body["health"]["label"], "MODEL ESTIMATE")

    def test_invalid_coordinates_are_rejected(self):
        response = self.client.get("/api/weather/current/?lat=200&lon=20")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_population_endpoint_is_explicit_when_unconfigured(self):
        response = self.client.get("/api/population/location/?lat=17.7&lon=83.2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "PROTOTYPE ESTIMATE")
        self.assertGreater(response.json()["population"], 0)

    @patch("core.views.get_forecast", return_value=[
        {"date": "2026-09-06", "temperature_min": 27, "temperature_max": 35,
         "humidity": 60, "wind_speed": 3, "solar_radiation": 500, "precipitation": 0, "source": "test"}
    ])
    def test_forecast_returns_thermal_metrics(self, forecast):
        response = self.client.get("/api/weather/forecast/?lat=17.7&lon=83.2")
        self.assertEqual(response.status_code, 200)
        row = response.json()["forecast"][0]
        self.assertIn("htsi", row)
        self.assertIn("risk_score", row)
        self.assertIn("heat_index", row)
        self.assertEqual(row["status"], "FORECAST")
