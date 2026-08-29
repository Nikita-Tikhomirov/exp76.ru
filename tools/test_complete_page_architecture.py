"""Contracts for the content-ready S1-S15 destination ledger."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tools.site_content.contracts import (
    load_page_architecture,
    validate_release_manifest,
)


class CompletePageArchitectureTests(unittest.TestCase):
    def test_ledger_preserves_noncommercial_pages_and_adds_all_hubs_and_children(self) -> None:
        from tools.seo_semantics.complete_page_architecture import (
            build_complete_page_destinations,
        )

        destinations = build_complete_page_destinations()
        roles = Counter(item.page_role for item in destinations)
        self.assertEqual(
            {
                "frozen": 6,
                "article": 23,
                "special": 3,
                "hub": 15,
                "child_service": 65,
            },
            roles,
        )
        self.assertEqual(112, len(destinations))
        self.assertEqual(112, len({item.destination_id for item in destinations}))
        self.assertEqual(112, len({item.canonical_url for item in destinations}))
        self.assertNotIn(
            "S5-CHILD-STUMPS",
            {item.destination_id for item in destinations},
        )
        self.assertIn(
            "S9-CHILD-STUMPS",
            {item.destination_id for item in destinations},
        )
        self.assertIn(
            "S15-ARTICLE-DEMOLITION-PERMIT",
            {item.destination_id for item in destinations},
        )
        legacy_articles = [
            item
            for item in destinations
            if item.page_role == "article" and item.service_id in {f"S{n}" for n in range(9, 16)}
        ]
        self.assertEqual(11, len(legacy_articles))
        self.assertTrue(all(item.publication_status == "ready" for item in legacy_articles))

    def test_only_seasonal_child_reuses_an_existing_child_owner(self) -> None:
        from tools.seo_semantics.complete_page_architecture import (
            build_complete_page_destinations,
        )

        reused = [
            item
            for item in build_complete_page_destinations()
            if item.page_role == "child_service" and item.url_action == "reuse"
        ]
        self.assertEqual(["S7-CHILD-HOLIDAY"], [item.destination_id for item in reused])
        self.assertEqual("https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/", reused[0].canonical_url)

    def test_legacy_base_normalization_merges_duplicate_cost_article(self) -> None:
        from tools.seo_semantics.complete_page_architecture import (
            BASE_PAGE_ARCHITECTURE_PATH,
            build_complete_page_destinations,
        )

        with BASE_PAGE_ARCHITECTURE_PATH.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        cost = next(row for row in rows if row["destination_id"] == "S1-ARTICLE-505521C7EF8C")
        cost["canonical_url"] = (
            "https://exp76.ru/kak-rasschitat-stoimost-blagoustrojstva-sa-sotku/"
        )
        cost["proposed_url"] = cost["canonical_url"]
        duplicate = dict(cost)
        duplicate.update(
            destination_id="S1-ARTICLE-72FBB49E67C8",
            canonical_url=(
                "https://exp76.ru/kak-rasschitat-inzhenernoe-blagoustrojstvo-uchastka/"
            ),
            proposed_url=(
                "https://exp76.ru/kak-rasschitat-inzhenernoe-blagoustrojstvo-uchastka/"
            ),
            primary_cluster_id="HOLD-72FBB49E67C8",
            source_cluster_ids="HOLD-72FBB49E67C8",
        )
        rows.append(duplicate)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy-base.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            destinations = build_complete_page_destinations(path)

        by_id = {item.destination_id: item for item in destinations}
        self.assertEqual(112, len(destinations))
        self.assertNotIn("S1-ARTICLE-72FBB49E67C8", by_id)
        self.assertEqual(
            "https://exp76.ru/kak-rasschitat-stoimost-blagoustrojstva-za-sotku/",
            by_id["S1-ARTICLE-505521C7EF8C"].canonical_url,
        )

    def test_written_csv_is_deterministic_and_loadable_by_content_contract(self) -> None:
        from tools.seo_semantics.complete_page_architecture import (
            write_complete_page_architecture,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "complete_page_architecture.csv"
            count = write_complete_page_architecture(path)
            first = path.read_bytes()
            second = write_complete_page_architecture(path)
            second_bytes = path.read_bytes()
            architecture = load_page_architecture(path)
        self.assertEqual(112, count)
        self.assertEqual(count, second)
        self.assertEqual(112, len(architecture))
        self.assertEqual(first, second_bytes)
        self.assertFalse(first.startswith(b"\xef\xbb\xbf"))

    def test_release_manifest_contains_only_publishable_content_artifacts(self) -> None:
        from tools.seo_semantics.complete_page_architecture import (
            write_complete_page_architecture,
            write_release_manifest,
        )

        with tempfile.TemporaryDirectory() as tmp:
            architecture_path = Path(tmp) / "complete_page_architecture.csv"
            manifest_path = Path(tmp) / "release-manifest.json"
            write_complete_page_architecture(architecture_path)
            first_count = write_release_manifest(manifest_path)
            first = manifest_path.read_bytes()
            second_count = write_release_manifest(manifest_path)
            second = manifest_path.read_bytes()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            architecture = load_page_architecture(architecture_path)

        self.assertEqual(100, first_count)
        self.assertEqual(first_count, second_count)
        self.assertEqual(first, second)
        self.assertEqual("ready", manifest["release_status"])
        self.assertEqual(91, len(manifest["managed_pages"]))
        self.assertEqual(9, len(manifest["preserved_pages"]))
        statuses = Counter(row["content_status"] for row in manifest["managed_pages"])
        self.assertEqual({"validated": 91}, dict(statuses))
        self.assertTrue(
            all(row["architecture_status"] == "ready" for row in manifest["managed_pages"])
        )
        self.assertEqual([], validate_release_manifest(manifest, architecture))


if __name__ == "__main__":
    unittest.main()
