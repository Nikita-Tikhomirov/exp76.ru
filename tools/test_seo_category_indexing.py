import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "ftp_dump_minimal/wp-content/themes/land76wp/inc/seo-category-indexing.php"
SITEMAP = ROOT / "land76-seo-categories-sitemap.xml"

EXPECTED_IDS = {87, 88, 89, 90, 91, 92}
EXPECTED_URLS = {
    "https://exp76.ru/category/drenazh-uchastka/",
    "https://exp76.ru/category/otmostka-vokrug-doma/",
    "https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
    "https://exp76.ru/category/osushenie-uchastka/",
    "https://exp76.ru/category/livnevaya-kanalizatsiya/",
    "https://exp76.ru/category/avtopoliv-na-uchastke/",
}


class SeoCategoryIndexingTest(unittest.TestCase):
    def test_only_new_service_categories_are_opened_for_indexing(self):
        source = MODULE.read_text(encoding="utf-8")
        match = re.search(r"return array\(([^)]+)\);", source)
        self.assertIsNotNone(match)
        ids = {int(value) for value in re.findall(r"\d+", match.group(1))}
        self.assertEqual(EXPECTED_IDS, ids)
        self.assertIn("unset($attributes['noindex'])", source)
        self.assertIn("$attributes['index'] = 'index'", source)

    def test_category_sitemap_contains_every_new_service_category(self):
        xml = SITEMAP.read_text(encoding="utf-8")
        urls = set(re.findall(r"<loc>([^<]+)</loc>", xml))
        self.assertEqual(EXPECTED_URLS, urls)

    def test_category_sitemap_is_added_to_aioseo_index(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("aioseo_sitemap_indexes", source)
        self.assertIn("land76-seo-categories-sitemap.xml", source)


if __name__ == "__main__":
    unittest.main()
