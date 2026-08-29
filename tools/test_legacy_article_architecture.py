"""Contracts for S9-S15 supporting informational pages."""

from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path


class LegacyArticleArchitectureTests(unittest.TestCase):
    def test_articles_are_information_only_and_cover_every_legacy_hub(self) -> None:
        from tools.seo_semantics.legacy_article_architecture import (
            LEGACY_ARTICLE_COUNTS,
            build_legacy_article_rows,
        )

        rows = build_legacy_article_rows()
        self.assertEqual(11, len(rows))
        self.assertEqual(
            {
                "S9": 2,
                "S10": 2,
                "S11": 1,
                "S12": 1,
                "S13": 2,
                "S14": 2,
                "S15": 1,
            },
            dict(Counter(row["service_id"] for row in rows)),
        )
        self.assertEqual(dict(LEGACY_ARTICLE_COUNTS), dict(Counter(row["service_id"] for row in rows)))
        self.assertEqual(11, len({row["destination_id"] for row in rows}))
        self.assertEqual(11, len({row["canonical_url"] for row in rows}))
        for row in rows:
            self.assertEqual("article", row["page_role"])
            self.assertEqual(f"{row['service_id']}-HUB", row["parent_destination_id"])
            self.assertEqual("ready", row["publication_status"])
            self.assertEqual("reviewed", row["review_status"])
            self.assertIn("yandex_serp", row["evidence_refs"])
            self.assertIn("wordstat", row["evidence_refs"])
            self.assertIn("Информационная граница:", row["rationale"])

    def test_selected_queries_keep_recorded_regional_frequency(self) -> None:
        from tools.seo_semantics.legacy_article_architecture import (
            build_legacy_article_rows,
        )

        rows = {row["destination_id"]: row for row in build_legacy_article_rows()}
        self.assertEqual("14", rows["S9-ARTICLE-STUMP-DIY"]["regional_monthly_frequency"])
        self.assertEqual("5", rows["S13-ARTICLE-CARPORT-DIY"]["regional_monthly_frequency"])
        self.assertEqual("1", rows["S15-ARTICLE-DEMOLITION-PERMIT"]["regional_monthly_frequency"])

    def test_csv_and_review_are_deterministic(self) -> None:
        from tools.seo_semantics.legacy_article_architecture import (
            write_legacy_article_artifacts,
        )

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "articles.csv"
            review_path = Path(tmp) / "articles.md"
            count = write_legacy_article_artifacts(csv_path, review_path)
            first_csv = csv_path.read_bytes()
            first_review = review_path.read_bytes()
            second = write_legacy_article_artifacts(csv_path, review_path)
            second_csv = csv_path.read_bytes()
            second_review = review_path.read_bytes()
        self.assertEqual(11, count)
        self.assertEqual(count, second)
        self.assertEqual(first_csv, second_csv)
        self.assertEqual(first_review, second_review)
        self.assertFalse(first_csv.startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
