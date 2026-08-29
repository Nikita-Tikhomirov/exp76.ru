"""The checked semantic review must cover every S9-S15 destination."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.seo_semantics.legacy_service_architecture import (
    all_legacy_destinations,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW = (
    ROOT
    / "seo-data"
    / "2026-08-exp76-services"
    / "reviews"
    / "legacy_semantic_validation.md"
)


class LegacySemanticReviewTests(unittest.TestCase):
    def test_every_legacy_destination_has_one_wordstat_row(self) -> None:
        text = REVIEW.read_text(encoding="utf-8")
        rows = re.findall(r"^\| (S(?:9|1[0-5])-[A-Z0-9-]+) \| .+ \| (\d+) \|$", text, re.MULTILINE)
        self.assertEqual(36, len(rows))
        self.assertEqual(
            {page.destination_id for page in all_legacy_destinations()},
            {destination_id for destination_id, _ in rows},
        )
        self.assertEqual(774, int(dict(rows)["S13-CHILD-CARPORT"]))

    def test_review_records_the_serp_merge_decision(self) -> None:
        text = REVIEW.read_text(encoding="utf-8")
        self.assertIn("вариант для каркасного дома удалён", text)
        self.assertIn("S12-CHILD-BATHHOUSE", text)
        self.assertNotIn("S12-CHILD-FRAME-HOUSE", text)


if __name__ == "__main__":
    unittest.main()
