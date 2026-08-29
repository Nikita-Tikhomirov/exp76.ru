"""Contracts for the superseding fifteen-hub child architecture."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.complete_service_architecture import (
    COMPLETE_CHILD_COUNTS,
    COMPLETE_SERVICE_ORDER,
    build_complete_service_rows,
    render_complete_service_structure,
    write_complete_service_architecture,
)


EXPECTED_COUNTS = {
    "S1": 5,
    "S2": 4,
    "S3": 5,
    "S4": 5,
    "S5": 5,
    "S6": 3,
    "S7": 5,
    "S8": 4,
    "S9": 3,
    "S10": 5,
    "S11": 3,
    "S12": 3,
    "S13": 4,
    "S14": 5,
    "S15": 6,
}


class CompleteServiceArchitectureTests(unittest.TestCase):
    def test_complete_rows_cover_all_fifteen_hubs_without_old_stump_child(self) -> None:
        rows = build_complete_service_rows()

        self.assertEqual(tuple(EXPECTED_COUNTS), COMPLETE_SERVICE_ORDER)
        self.assertEqual(EXPECTED_COUNTS, dict(COMPLETE_CHILD_COUNTS))
        self.assertEqual(65, len(rows))
        self.assertEqual(65, len({row["destination_id"] for row in rows}))
        self.assertEqual(65, len({row["target_url"] for row in rows}))
        self.assertNotIn("S5-CHILD-STUMPS", {row["destination_id"] for row in rows})
        self.assertNotIn(
            "https://exp76.ru/services/vykorchevyvanie-pnejj-spil-derevev/",
            {row["target_url"] for row in rows},
        )
        self.assertIn("S9-CHILD-STUMPS", {row["destination_id"] for row in rows})
        self.assertEqual(
            EXPECTED_COUNTS,
            {
                service_id: sum(row["service_id"] == service_id for row in rows)
                for service_id in COMPLETE_SERVICE_ORDER
            },
        )
        for row in rows:
            self.assertEqual(f'{row["service_id"]}-HUB', row["parent_hub"])
            self.assertTrue(row["parent_hub_url"].startswith("https://exp76.ru/services/"))
            self.assertEqual("ready", row["publication_status"])

    def test_only_the_seasonal_s7_page_reuses_an_existing_child_url(self) -> None:
        rows = build_complete_service_rows()
        reused = [row for row in rows if row["url_action"] == "reuse"]

        self.assertEqual(1, len(reused))
        self.assertEqual("S7-CHILD-HOLIDAY", reused[0]["destination_id"])
        self.assertEqual("10381", reused[0]["current_wp_id"])
        self.assertEqual(reused[0]["current_url"], reused[0]["target_url"])
        self.assertEqual("servicepost.php", reused[0]["target_template"])

    def test_markdown_and_csv_are_deterministic_and_report_65_children(self) -> None:
        markdown = render_complete_service_structure()
        self.assertIn("Всего дочерних услуг: **65**", markdown)
        self.assertIn("## S15 —", markdown)
        self.assertIn("WP 9838", markdown)

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "complete.csv"
            markdown_path = Path(tmp) / "complete.md"
            count = write_complete_service_architecture(csv_path, markdown_path)
            first_csv = csv_path.read_bytes()
            first_markdown = markdown_path.read_bytes()
            second = write_complete_service_architecture(csv_path, markdown_path)
            self.assertEqual(65, count)
            self.assertEqual(count, second)
            self.assertEqual(first_csv, csv_path.read_bytes())
            self.assertEqual(first_markdown, markdown_path.read_bytes())
            self.assertFalse(first_csv.startswith(b"\xef\xbb\xbf"))
            with csv_path.open("r", encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
        self.assertEqual(65, len(rows))


if __name__ == "__main__":
    unittest.main()
