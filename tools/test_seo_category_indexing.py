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

EXPECTED_CATEGORY_DESCRIPTIONS = {
    87: "Дренаж участка под ключ",
    88: "Отмостка вокруг дома под ключ",
    89: "Укладка тротуарной плитки под ключ",
    90: "Осушение участка под ключ",
    91: "Ливневая канализация под ключ",
    92: "Автополив участка под ключ",
}

EXPECTED_CITY_DESCRIPTIONS = {
    "yaroslavl": "Услуги по благоустройству участков в Ярославле",
    "rybinsk": "Услуги по благоустройству участков в Рыбинске",
    "uglich": "Услуги по благоустройству участков в Угличе",
    "tutaev": "Услуги по благоустройству участков в Тутаеве",
    "pereslavl": "Услуги по благоустройству участков в Переславле-Залесском",
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

    def test_new_service_categories_have_unique_aioseo_descriptions(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("aioseo_description", source)
        for category_id, description_start in EXPECTED_CATEGORY_DESCRIPTIONS.items():
            self.assertRegex(
                source,
                rf"{category_id}\s*=>\s*['\"]{re.escape(description_start)}",
            )

    def test_city_hubs_have_unique_aioseo_descriptions(self):
        source = MODULE.read_text(encoding="utf-8")
        for slug, description_start in EXPECTED_CITY_DESCRIPTIONS.items():
            self.assertRegex(
                source,
                rf"['\"]{slug}['\"]\s*=>\s*['\"]{re.escape(description_start)}",
            )


if __name__ == "__main__":
    unittest.main()
