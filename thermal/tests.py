from django.test import SimpleTestCase

from .heat_index import calculate_heat_index
from .htsi import calculate_htsi
from .utci import calculate_utci
from .wbgt import calculate_wbgt


class ThermalCalculationTests(SimpleTestCase):
    def test_heat_index_is_hotter_than_air_in_humid_heat(self):
        self.assertGreater(calculate_heat_index(40, 70), 40)

    def test_heat_index_dry_condition_is_bounded(self):
        self.assertGreater(calculate_heat_index(40, 20), 35)

    def test_thermal_metrics_are_finite_and_ordered(self):
        wbgt = calculate_wbgt(40, 70, 2, 800)
        utci = calculate_utci(40, 70, 2, 800)
        self.assertTrue(20 < wbgt < 50)
        self.assertTrue(30 < utci < 70)

    def test_htsi_has_documented_band(self):
        result = calculate_htsi(40, 70, 2, 800)
        self.assertIn(result["band"], {"LOW", "MODERATE", "HIGH", "VERY HIGH", "EXTREME"})
        self.assertTrue(0 <= result["score"] <= 100)
