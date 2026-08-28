"""Contracts for the expanded S1-S8 service silo registry."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.expanded_architecture import (
    EXPANDED_ARTICLES,
    EXPANDED_CHILDREN,
    TARGETED_SERP_QUERIES,
    build_expanded_serp_queue,
    build_targeted_serp_queue,
    validate_expanded_registry,
    write_expanded_serp_queue,
    write_targeted_serp_queue,
)


class ExpandedServiceArchitectureTests(unittest.TestCase):
    def test_every_hub_has_five_or_six_commercial_children(self):
        self.assertEqual(set(EXPANDED_CHILDREN), {f"S{index}" for index in range(1, 9)})
        self.assertEqual(
            {service_id: len(pages) for service_id, pages in EXPANDED_CHILDREN.items()},
            {
                "S1": 5,
                "S2": 5,
                "S3": 5,
                "S4": 6,
                "S5": 6,
                "S6": 5,
                "S7": 6,
                "S8": 6,
            },
        )
        for pages in EXPANDED_CHILDREN.values():
            self.assertTrue(all(page.page_role == "child_service" for page in pages))

    def test_articles_are_a_separate_five_to_seven_page_layer(self):
        self.assertEqual(set(EXPANDED_ARTICLES), set(EXPANDED_CHILDREN))
        for pages in EXPANDED_ARTICLES.values():
            self.assertGreaterEqual(len(pages), 5)
            self.assertLessEqual(len(pages), 7)
            self.assertTrue(all(page.page_role == "article" for page in pages))

    def test_registry_is_complete_unique_and_protected_owner_safe(self):
        self.assertEqual(validate_expanded_registry(), [])

    def test_search_queue_has_one_representative_query_per_candidate(self):
        rows = build_expanded_serp_queue(start_query_number=155)
        expected_count = sum(map(len, EXPANDED_CHILDREN.values())) + sum(
            map(len, EXPANDED_ARTICLES.values())
        )

        self.assertEqual(len(rows), expected_count)
        self.assertEqual(rows[0]["query_id"], "Q000155")
        self.assertEqual(rows[-1]["query_id"], f"Q{154 + expected_count:06d}")
        self.assertEqual(len({row["destination_id"] for row in rows}), expected_count)
        self.assertEqual({row["region"] for row in rows}, {"Yaroslavl"})
        self.assertEqual({row["device"] for row in rows}, {"desktop"})
        self.assertEqual(
            {row["intent"] for row in rows},
            {"transactional", "informational"},
        )

    def test_queue_writer_is_utf8_and_yandex_search_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "serp-queue.csv"
            count = write_expanded_serp_queue(output, start_query_number=155)
            with output.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(count, len(rows))
        self.assertEqual(
            set(rows[0]),
            {
                "query_id",
                "query",
                "service_id",
                "intent",
                "region",
                "device",
                "destination_id",
                "reason",
            },
        )

    def test_targeted_queue_rechecks_ambiguous_commercial_candidates(self):
        rows = build_targeted_serp_queue(start_query_number=247)

        self.assertEqual(len(rows), 23)
        self.assertEqual(len(TARGETED_SERP_QUERIES), 23)
        self.assertEqual(rows[0]["query_id"], "Q000247")
        self.assertEqual(rows[-1]["query_id"], "Q000269")
        self.assertEqual({row["intent"] for row in rows}, {"transactional"})
        self.assertEqual(len({row["query"] for row in rows}), 23)
        self.assertTrue(
            {row["destination_id"] for row in rows}
            <= {
                page.destination_id
                for pages in EXPANDED_CHILDREN.values()
                for page in pages
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "targeted.csv"
            count = write_targeted_serp_queue(output, start_query_number=247)
            with output.open("r", encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))
        self.assertEqual(count, 23)
        self.assertEqual(written, rows)


if __name__ == "__main__":
    unittest.main()
