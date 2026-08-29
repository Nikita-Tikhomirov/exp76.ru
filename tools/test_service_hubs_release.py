"""End-to-end contracts for the unified child-service and article release."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.legacy_article_content import DEFAULT_ARTICLE_DIR, load_and_validate_articles
from tools.seo_semantics.legacy_article_architecture import build_legacy_article_rows
from tools.service_page_content import (
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_PAGES_DIR,
    build_import_items,
    item_checksum,
    load_default_architecture,
    load_evidence,
    load_pages,
)


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
SOURCE_PAYLOAD = ROOT / "seo-content" / "service-pages" / "import" / "service-pages-import.json"
SOURCE_DEPLOYMENT_MANIFEST = (
    ROOT / "seo-content" / "service-pages" / "import" / "service-pages-release-manifest.json"
)
THEME_PAYLOAD = THEME / "import" / "service-hubs-import.json"
THEME_DEPLOYMENT_MANIFEST = THEME / "import" / "service-hubs-release-manifest.json"
SOURCE_RELEASE_MANIFEST = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
ARCHITECTURE_CSV = (
    ROOT / "seo-data" / "2026-08-exp76-services" / "processed" / "page_architecture.csv"
)

EXPECTED_READY_ARTICLES = {
    "S9-ARTICLE-STUMP-DIY",
    "S9-ARTICLE-OVERGROWN-SITE",
    "S10-ARTICLE-POND-DIY",
    "S10-ARTICLE-POND-CARE",
    "S11-ARTICLE-PRESSURE",
    "S12-ARTICLE-PILE-PROS-CONS",
    "S13-ARTICLE-CARPORT-DIY",
    "S13-ARTICLE-POLYCARBONATE-DIY",
    "S14-ARTICLE-BRICK-GRILL-DIY",
    "S14-ARTICLE-HEATING-STOVE-DIY",
    "S15-ARTICLE-DEMOLITION-PERMIT",
}


def _release_module(test_case: unittest.TestCase):
    try:
        return importlib.import_module("tools.service_hubs_release")
    except ModuleNotFoundError:
        test_case.fail("tools.service_hubs_release must build the unified release")


def _child_items() -> list[dict[str, object]]:
    architecture = load_default_architecture()
    return build_import_items(
        load_pages(DEFAULT_PAGES_DIR),
        architecture,
        load_evidence(DEFAULT_EVIDENCE_PATH),
    )


def _backlog_article_ids() -> set[str]:
    with ARCHITECTURE_CSV.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream)
        return {
            row["destination_id"]
            for row in rows
            if row["page_role"] == "article" and row["publication_status"] != "ready"
        }


class UnifiedReleaseGeneratorTests(unittest.TestCase):
    def test_article_item_matches_unified_importer_contract(self) -> None:
        release = _release_module(self)
        source = json.loads(
            (DEFAULT_ARTICLE_DIR / "S9-ARTICLE-STUMP-DIY.json").read_text(encoding="utf-8")
        )

        item = release.build_article_import_item(source)

        self.assertEqual("S9-ARTICLE-STUMP-DIY", item["page_key"])
        self.assertEqual("S9", item["service_id"])
        self.assertEqual("S9", item["topic_key"])
        self.assertEqual("article", item["role"])
        self.assertEqual(
            ["S9-HUB", "S9-CHILD-STUMPS"],
            item["related_service_page_keys"],
        )
        self.assertEqual(
            {
                "url": source["featured_image_url"],
                "alt": source["acf"]["blogseo_main_image_alt"],
            },
            item["main_image"],
        )
        self.assertEqual(
            {
                "title": source["acf"]["blogseo_seo_title"],
                "description": source["acf"]["blogseo_seo_description"],
            },
            item["seo"],
        )
        self.assertNotIn("related_service_slugs", item)
        self.assertNotIn("blogseo_related_service_slugs", item["acf"])
        self.assertEqual(item_checksum(item), item["checksum"])

    def test_release_has_65_children_and_only_11_ready_articles_with_backlinks(self) -> None:
        release = _release_module(self)
        children = _child_items()
        articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR, require_complete=True)

        items = release.build_unified_import_items(children, articles)

        children_by_key = {
            item["page_key"]: item for item in items if item["role"] == "child_service"
        }
        article_items = [item for item in items if item["role"] == "article"]
        self.assertEqual(76, len(items))
        self.assertEqual(65, len(children_by_key))
        self.assertEqual(11, len(article_items))
        self.assertEqual(EXPECTED_READY_ARTICLES, {item["page_key"] for item in article_items})
        self.assertTrue(_backlog_article_ids().isdisjoint({item["page_key"] for item in items}))

        backlink_count = 0
        for article in article_items:
            service_id = article["service_id"]
            relations = article["related_service_page_keys"]
            self.assertIn(f"{service_id}-HUB", relations)
            child_keys = [key for key in relations if "-CHILD-" in key]
            self.assertEqual(1, len(child_keys), article["page_key"])
            child = children_by_key[child_keys[0]]
            self.assertEqual(service_id, child["service_id"])
            self.assertIn(article["page_key"], child["related_article_page_keys"])

        for child in children_by_key.values():
            related_articles = child.get("related_article_page_keys", [])
            backlink_count += len(related_articles)
            self.assertEqual(len(related_articles), len(set(related_articles)))
            self.assertTrue(set(related_articles).issubset(EXPECTED_READY_ARTICLES))
        self.assertEqual(11, backlink_count)

    def test_release_merge_is_idempotent_and_does_not_mutate_child_items(self) -> None:
        release = _release_module(self)
        children = _child_items()
        original_children = copy.deepcopy(children)
        articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR, require_complete=True)

        first = release.build_unified_import_items(children, articles)
        second = release.build_unified_import_items(first[:65], articles)

        self.assertEqual(original_children, children)
        self.assertEqual(first, second)

    def test_release_rejects_partial_ready_article_inventory(self) -> None:
        release = _release_module(self)
        articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR, require_complete=True)

        with self.assertRaisesRegex(ValueError, "article inventory"):
            release.build_unified_import_items(_child_items(), articles[:-1])

    def test_bundle_rejects_a_draft_or_incomplete_source_manifest(self) -> None:
        release = _release_module(self)
        source_manifest = json.loads(SOURCE_RELEASE_MANIFEST.read_text(encoding="utf-8"))
        mutations = (
            lambda manifest: manifest.update(release_status="draft"),
            lambda manifest: manifest["managed_pages"].pop(),
        )
        for mutate in mutations:
            broken = copy.deepcopy(source_manifest)
            mutate(broken)
            with self.subTest(mutate=mutate):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "release-manifest.json"
                    path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "source release manifest"):
                        release.build_default_deployment_bundle(path)


class CheckedReleaseBundleTests(unittest.TestCase):
    def test_checked_payload_and_manifest_bind_exact_76_item_inventory(self) -> None:
        payload = json.loads(SOURCE_PAYLOAD.read_text(encoding="utf-8"))
        manifest = json.loads(SOURCE_DEPLOYMENT_MANIFEST.read_text(encoding="utf-8"))
        items = payload["items"]
        roles = {role: [item for item in items if item["role"] == role] for role in {"child_service", "article"}}

        self.assertEqual(76, len(items))
        self.assertEqual(65, len(roles["child_service"]))
        self.assertEqual(11, len(roles["article"]))
        self.assertEqual(EXPECTED_READY_ARTICLES, {item["page_key"] for item in roles["article"]})
        self.assertTrue(_backlog_article_ids().isdisjoint({item["page_key"] for item in items}))
        self.assertTrue(all(item["checksum"] == item_checksum(item) for item in items))

        expected_inventory = sorted(
            ({"page_key": item["page_key"], "checksum": item["checksum"]} for item in items),
            key=lambda row: (row["page_key"], row["checksum"]),
        )
        self.assertEqual(expected_inventory, manifest["items"])
        self.assertEqual(
            hashlib.sha256(SOURCE_DEPLOYMENT_MANIFEST.read_bytes()).hexdigest(),
            payload["manifest_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(SOURCE_RELEASE_MANIFEST.read_bytes()).hexdigest(),
            manifest["source_manifest_sha256"],
        )
        self.assertEqual(SOURCE_PAYLOAD.read_bytes(), THEME_PAYLOAD.read_bytes())
        self.assertEqual(
            SOURCE_DEPLOYMENT_MANIFEST.read_bytes(),
            THEME_DEPLOYMENT_MANIFEST.read_bytes(),
        )

    def test_checked_article_and_child_relations_are_bidirectional(self) -> None:
        items = json.loads(SOURCE_PAYLOAD.read_text(encoding="utf-8"))["items"]
        by_key = {item["page_key"]: item for item in items}

        for article_key in EXPECTED_READY_ARTICLES:
            self.assertIn(article_key, by_key)
            article = by_key[article_key]
            child_keys = [
                key for key in article["related_service_page_keys"] if "-CHILD-" in key
            ]
            self.assertEqual(1, len(child_keys), article_key)
            self.assertIn(article_key, by_key[child_keys[0]]["related_article_page_keys"])

    def test_ready_article_architecture_is_exactly_the_release_article_set(self) -> None:
        expected = {row["destination_id"] for row in build_legacy_article_rows()}
        payload = json.loads(SOURCE_PAYLOAD.read_text(encoding="utf-8"))
        actual = {item["page_key"] for item in payload["items"] if item["role"] == "article"}

        self.assertEqual(EXPECTED_READY_ARTICLES, expected)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
