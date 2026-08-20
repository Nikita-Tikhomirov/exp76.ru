import unittest

from tools.seo_semantics.normalize import normalize_query


class SemanticNormalizeTest(unittest.TestCase):
    def test_normalizes_case_yo_spacing_and_square_meters(self):
        self.assertEqual(
            normalize_query("  Цена Ёлочного газона 100 м²  "),
            "цена елочного газона 100 м2",
        )

    def test_preserves_numbers_cities_and_commercial_modifiers(self):
        self.assertEqual(
            normalize_query("Въезд 6 метров под ключ — Ярославль"),
            "въезд 6 метров под ключ ярославль",
        )

    def test_collapses_equivalent_area_notation(self):
        self.assertEqual(normalize_query("газон 50 кв. м"), "газон 50 м2")
