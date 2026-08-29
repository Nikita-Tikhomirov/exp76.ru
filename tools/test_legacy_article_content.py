from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.legacy_article_content import (
    ArticleValidationError,
    DEFAULT_ARTICLE_DIR,
    article_word_count,
    build_blog_import_payload,
    load_and_validate_articles,
    validate_article,
    write_blog_import_payload,
)
from tools.seo_semantics.legacy_article_architecture import build_legacy_article_rows


FOCUS_DESTINATIONS = {
    "S9-ARTICLE-STUMP-DIY",
    "S9-ARTICLE-OVERGROWN-SITE",
    "S10-ARTICLE-POND-DIY",
    "S10-ARTICLE-POND-CARE",
    "S11-ARTICLE-PRESSURE",
    "S12-ARTICLE-PILE-PROS-CONS",
}

LEGACY_IMPORTER_PATH = (
    Path(__file__).resolve().parents[1]
    / "ftp_dump_minimal"
    / "wp-content"
    / "themes"
    / "land76wp"
    / "inc"
    / "import-drenazh-blog.php"
)
REFERENCE_PAYLOAD_PATH = (
    Path(__file__).resolve().parents[1]
    / "seo-content"
    / "drenazh-uchastka"
    / "import"
    / "drenazh-blog-import.json"
)


class LegacyArticleContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.architecture = {row["destination_id"]: row for row in build_legacy_article_rows()}

    def _load_focus(self) -> list[dict]:
        return [
            json.loads((DEFAULT_ARTICLE_DIR / f"{destination_id}.json").read_text(encoding="utf-8"))
            for destination_id in sorted(FOCUS_DESTINATIONS)
        ]

    def test_s9_s12_articles_are_production_complete(self) -> None:
        articles = self._load_focus()
        self.assertEqual({article["destination_id"] for article in articles}, FOCUS_DESTINATIONS)
        for article in articles:
            validate_article(article, expected=self.architecture[article["destination_id"]])
            self.assertGreaterEqual(article_word_count(article), 800)
            self.assertGreaterEqual(len(article["acf"]["blogseo_sections"]), 6)
            self.assertGreaterEqual(len(article["acf"]["blogseo_faq_items"]), 5)

    def test_internal_links_are_rendered_and_owned_by_same_hub(self) -> None:
        for article in self._load_focus():
            html = " ".join(section["body"] for section in article["acf"]["blogseo_sections"])
            keys = {link["page_key"] for link in article["internal_links"]}
            self.assertIn(f"{article['service_id']}-HUB", keys)
            self.assertTrue(any(key.startswith(f"{article['service_id']}-CHILD-") for key in keys))
            for link in article["internal_links"]:
                self.assertIn(link["url"], html)

    def test_missing_rendered_link_is_rejected(self) -> None:
        article = copy.deepcopy(self._load_focus()[0])
        article["internal_links"][0]["url"] = "https://exp76.ru/not-rendered/"
        with self.assertRaisesRegex(ArticleValidationError, "not rendered"):
            validate_article(article, expected=self.architecture[article["destination_id"]])

    def test_incomplete_directory_is_rejected_in_complete_mode(self) -> None:
        article_path = DEFAULT_ARTICLE_DIR / "S9-ARTICLE-STUMP-DIY.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / article_path.name
            target.write_text(article_path.read_text(encoding="utf-8"), encoding="utf-8")
            self.assertEqual(len(load_and_validate_articles(Path(temp_dir))), 1)
            with self.assertRaisesRegex(ArticleValidationError, "article package differs"):
                load_and_validate_articles(Path(temp_dir), require_complete=True)

    def test_blog_import_payload_matches_existing_importer_contract(self) -> None:
        architecture_order = [row["destination_id"] for row in build_legacy_article_rows()]
        source_articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR)
        source_by_id = {article["destination_id"]: article for article in source_articles}
        payload = build_blog_import_payload(source_articles)

        self.assertEqual(payload["type"], "legacy_services_blog_posts")
        self.assertEqual(payload["category_ids"], [72])
        expected_ids = [destination_id for destination_id in architecture_order if destination_id in source_by_id]
        self.assertEqual(len(payload["posts"]), len(expected_ids))

        expected_keys = {
            "slug",
            "post_title",
            "post_excerpt",
            "post_content",
            "menu_order",
            "categories",
            "featured_image_url",
            "acf",
        }
        for menu_order, (destination_id, post) in enumerate(zip(expected_ids, payload["posts"])):
            source = source_by_id[destination_id]
            self.assertEqual(set(post), expected_keys)
            self.assertEqual(post["menu_order"], menu_order)
            self.assertEqual(post["categories"], [72])
            self.assertEqual(post["slug"], source["slug"])
            self.assertEqual(post["post_title"], source["post_title"])
            self.assertEqual(post["post_excerpt"], source["post_excerpt"])
            self.assertEqual(post["post_content"], source["post_content"])
            self.assertEqual(post["featured_image_url"], source["featured_image_url"])
            self.assertEqual(post["acf"], source["acf"])

    def test_blog_import_payload_is_written_as_deterministic_utf8_json(self) -> None:
        articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR)
        expected = build_blog_import_payload(articles)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "legacy-services-blog-import.json"
            count = write_blog_import_payload(output_path, articles)
            raw = output_path.read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            self.assertNotIn("\\u04", raw)
            self.assertEqual(json.loads(raw), expected)
            self.assertEqual(count, len(articles))

    def test_blog_import_payload_matches_checked_in_php_and_reference_keys(self) -> None:
        importer = LEGACY_IMPORTER_PATH.read_text(encoding="utf-8")
        reference = json.loads(REFERENCE_PAYLOAD_PATH.read_text(encoding="utf-8"))
        payload = build_blog_import_payload(load_and_validate_articles(DEFAULT_ARTICLE_DIR))

        self.assertIn("land76wp_drenazh_blog_import_upsert_post", importer)
        self.assertIn("$post_payload['categories']", importer)
        self.assertIn("$post_payload['featured_image_url']", importer)
        self.assertIn("blogseo_related_service_slugs", importer)
        self.assertEqual(set(payload["posts"][0]), set(reference["posts"][0]))
        self.assertEqual(set(payload["posts"][0]["acf"]), set(reference["posts"][0]["acf"]))


if __name__ == "__main__":
    unittest.main()
