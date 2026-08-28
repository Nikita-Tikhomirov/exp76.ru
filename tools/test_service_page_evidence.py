"""Fail-closed contracts for production service-page evidence."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.seo_semantics.final_service_architecture import build_final_service_rows


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "seo-content" / "service-pages" / "evidence.json"
REQUIRED_SERVICE_FIELDS = {
    "destination_id",
    "evidence_class",
    "exact_case_ids",
    "exact_case_urls",
    "contextual_page_ids",
    "media_pool",
    "media",
    "asset_kind",
    "safe_caption_rule",
    "caveat",
    "needs_client_asset_or_generated_illustration",
}
VALID_EVIDENCE_CLASSES = {"A", "B", "C"}
VALID_ASSET_KINDS = {
    "case_photo",
    "service_photo",
    "context_photo",
    "illustration",
    "missing",
}
EXPECTED_CLASS_COUNTS = {"A": 15, "B": 13, "C": 9}
ILLUSTRATION_POOLS = {"M1", "M7", "M9", "M10"}


class ServicePageEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.services = cls.registry["services"]

    def test_registry_covers_the_exact_final_37_once(self) -> None:
        expected_ids = {
            row["destination_id"] for row in build_final_service_rows()
        }
        actual_ids = [row["destination_id"] for row in self.services]

        self.assertEqual(1, self.registry["schema_version"])
        self.assertEqual(37, len(actual_ids))
        self.assertEqual(37, len(set(actual_ids)))
        self.assertEqual(expected_ids, set(actual_ids))
        self.assertEqual(
            EXPECTED_CLASS_COUNTS,
            {
                evidence_class: sum(
                    row["evidence_class"] == evidence_class
                    for row in self.services
                )
                for evidence_class in VALID_EVIDENCE_CLASSES
            },
        )

    def test_every_entry_has_valid_evidence_and_media_shapes(self) -> None:
        for row in self.services:
            with self.subTest(destination_id=row.get("destination_id")):
                self.assertEqual(REQUIRED_SERVICE_FIELDS, set(row))
                self.assertIn(row["evidence_class"], VALID_EVIDENCE_CLASSES)
                self.assertIn(row["asset_kind"], VALID_ASSET_KINDS)
                self.assertIsInstance(row["exact_case_ids"], list)
                self.assertIsInstance(row["exact_case_urls"], list)
                self.assertEqual(
                    len(row["exact_case_ids"]), len(row["exact_case_urls"])
                )
                self.assertEqual(
                    len(row["exact_case_ids"]), len(set(row["exact_case_ids"]))
                )
                for page_id in row["exact_case_ids"] + row["contextual_page_ids"]:
                    self.assertIsInstance(page_id, int)
                    self.assertGreater(page_id, 0)
                for url in row["exact_case_urls"]:
                    self.assertRegex(url, r"^https://exp76\.ru/.+/$")
                self.assertIsInstance(row["media"], list)
                if row["asset_kind"] != "missing":
                    self.assertIsInstance(row["media_pool"], str)
                    self.assertTrue(row["media_pool"].strip())
                self.assertTrue(row["safe_caption_rule"].strip())
                self.assertTrue(row["caveat"].strip())
                self.assertIsInstance(
                    row["needs_client_asset_or_generated_illustration"], bool
                )
                for media in row["media"]:
                    self.assertEqual(
                        {
                            "attachment_id",
                            "url",
                            "pool",
                            "asset_kind",
                            "source_page_id",
                        },
                        set(media),
                    )
                    self.assertIsInstance(media["attachment_id"], int)
                    self.assertGreater(media["attachment_id"], 0)
                    self.assertRegex(
                        media["url"],
                        r"^https://exp76\.ru/wp-content/uploads/.+\.webp$",
                    )
                    self.assertTrue(media["pool"])
                    self.assertIn(media["asset_kind"], VALID_ASSET_KINDS - {"missing"})
                    self.assertIsInstance(media["source_page_id"], int)
                    self.assertGreater(media["source_page_id"], 0)
                    if media["asset_kind"] == "case_photo":
                        self.assertIn(media["source_page_id"], row["exact_case_ids"])
                    else:
                        self.assertIn(
                            media["source_page_id"],
                            row["contextual_page_ids"] + row["exact_case_ids"],
                        )

    def test_classes_fail_closed_on_missing_or_non_case_assets(self) -> None:
        for row in self.services:
            with self.subTest(destination_id=row["destination_id"]):
                evidence_class = row["evidence_class"]
                if evidence_class == "A":
                    self.assertTrue(row["exact_case_ids"])
                    self.assertEqual("case_photo", row["asset_kind"])
                    self.assertFalse(
                        row["needs_client_asset_or_generated_illustration"]
                    )
                    self.assertTrue(
                        any(item["asset_kind"] == "case_photo" for item in row["media"])
                    )
                elif evidence_class == "B":
                    self.assertFalse(row["exact_case_ids"])
                    self.assertIn(row["asset_kind"], {"service_photo", "illustration"})
                    self.assertTrue(row["media"])
                    self.assertFalse(
                        row["needs_client_asset_or_generated_illustration"]
                    )
                else:
                    self.assertFalse(row["exact_case_ids"])
                    self.assertTrue(
                        row["needs_client_asset_or_generated_illustration"]
                    )
                    if row["asset_kind"] == "missing":
                        self.assertIsNone(row["media_pool"])
                        self.assertEqual([], row["media"])
                    else:
                        self.assertIn(
                            row["asset_kind"], {"service_photo", "context_photo"}
                        )
                        self.assertTrue(row["media"])

    def test_illustrations_can_never_be_presented_as_completed_objects(self) -> None:
        policy = self.registry["caption_policy"]
        self.assertEqual(
            ILLUSTRATION_POOLS,
            set(policy["never_completed_object_pools"]),
        )
        self.assertEqual("Иллюстрация:", policy["illustration_caption_prefix"])
        self.assertTrue(policy["illustration_forbidden_claims"])

        for row in self.services:
            illustration_media = [
                item for item in row["media"] if item["asset_kind"] == "illustration"
            ]
            if not illustration_media:
                continue
            with self.subTest(destination_id=row["destination_id"]):
                self.assertEqual("illustration", row["asset_kind"])
                self.assertIn("Иллюстрация:", row["safe_caption_rule"])
                self.assertIn("не указывать", row["safe_caption_rule"].lower())
                for media in illustration_media:
                    self.assertIn(media["pool"], ILLUSTRATION_POOLS)
                    self.assertNotEqual("case_photo", media["asset_kind"])

    def test_every_current_page_has_a_valid_existing_main_image(self) -> None:
        for row in self.services:
            with self.subTest(destination_id=row["destination_id"]):
                self.assertNotEqual("missing", row["asset_kind"])
                self.assertTrue(row["media"])
                self.assertGreater(row["media"][0]["attachment_id"], 0)

    def test_non_case_photos_are_explicitly_not_case_proof(self) -> None:
        for row in self.services:
            if row["asset_kind"] not in {"service_photo", "context_photo"}:
                continue
            with self.subTest(destination_id=row["destination_id"]):
                rule = row["safe_caption_rule"].lower()
                self.assertIn("не называть", rule)
                self.assertIn("выполненным объектом", rule)


if __name__ == "__main__":
    unittest.main()
