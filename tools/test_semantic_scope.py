import unittest
from pathlib import Path

from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "seo-data/2026-08-exp76-services/scope.json"


class SemanticScopeTest(unittest.TestCase):
    def test_scope_contains_exactly_the_approved_services(self):
        scope = load_scope(SCOPE)
        self.assertEqual(
            {service.service_id for service in scope.services},
            {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"},
        )
        self.assertEqual(len(scope.services), 8)

    def test_scope_freezes_the_six_existing_category_hubs(self):
        scope = load_scope(SCOPE)
        self.assertEqual(len(scope.frozen_urls), 6)
        self.assertIn("https://exp76.ru/category/drenazh-uchastka/", scope.frozen_urls)
        self.assertIn("https://exp76.ru/category/avtopoliv-na-uchastke/", scope.frozen_urls)

    def test_scope_rejects_duplicate_urls(self):
        scope = load_scope(SCOPE)
        urls = [service.current_url for service in scope.services]
        self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    unittest.main()
