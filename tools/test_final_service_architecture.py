"""Contracts for the deterministic final service-child export."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.final_service_architecture import (
    CSV_COLUMNS,
    build_final_service_rows,
    render_final_service_structure,
    write_final_service_architecture,
)
from tools.seo_semantics.reviewed_service_architecture import URL_DECISIONS


EXPECTED_COUNTS = {
    "S1": 5,
    "S2": 4,
    "S3": 5,
    "S4": 5,
    "S5": 6,
    "S6": 3,
    "S7": 5,
    "S8": 4,
}
EXPECTED_COLUMNS = (
    "destination_id",
    "service_id",
    "title",
    "slug",
    "query",
    "parent_hub",
    "parent_hub_url",
    "current_url",
    "target_url",
    "url_action",
    "current_wp_id",
    "current_post_type",
    "target_template",
    "excluded_primary_intents",
    "business_evidence",
    "semantic_evidence",
    "boundary",
    "publication_status",
)


class FinalServiceArchitectureTests(unittest.TestCase):
    def test_rows_export_every_reviewed_child_once_in_service_order(self) -> None:
        rows = build_final_service_rows()

        self.assertEqual(37, len(rows))
        self.assertEqual(EXPECTED_COLUMNS, CSV_COLUMNS)
        self.assertEqual(list(EXPECTED_COLUMNS), list(rows[0]))
        self.assertEqual(
            EXPECTED_COUNTS,
            {
                service_id: sum(row["service_id"] == service_id for row in rows)
                for service_id in EXPECTED_COUNTS
            },
        )
        self.assertEqual(37, len({row["destination_id"] for row in rows}))
        self.assertEqual(
            [f"S{index}" for index in range(1, 9)],
            list(dict.fromkeys(row["service_id"] for row in rows)),
        )
        self.assertEqual({"ready"}, {row["publication_status"] for row in rows})
        for row in rows:
            self.assertEqual(f'{row["service_id"]}-HUB', row["parent_hub"])
            self.assertTrue(row["parent_hub_url"].startswith("https://exp76.ru/services/"))

    def test_rows_preserve_explicit_url_decisions_and_existing_wp_owner(self) -> None:
        rows = {row["destination_id"]: row for row in build_final_service_rows()}

        self.assertEqual(
            {
                "S6-CHILD-WOOD": (
                    "Деревянные подпорные стенки",
                    "podpornaya-stenka-iz-dereva",
                    "Q000276",
                ),
            },
            {
                destination_id: (
                    rows[destination_id]["title"],
                    rows[destination_id]["slug"],
                    rows[destination_id]["semantic_evidence"].split("|")[1],
                )
                for destination_id in (
                    "S6-CHILD-WOOD",
                )
            },
        )
        holiday = rows["S7-CHILD-HOLIDAY"]
        self.assertEqual("reuse", holiday["url_action"])
        self.assertEqual("10381", holiday["current_wp_id"])
        self.assertEqual(holiday["current_url"], holiday["target_url"])
        stumps = rows["S5-CHILD-STUMPS"]
        self.assertEqual("reuse", stumps["url_action"])
        self.assertEqual("6870", stumps["current_wp_id"])
        self.assertEqual(stumps["current_url"], stumps["target_url"])
        self.assertEqual("page", stumps["current_post_type"])
        self.assertEqual("servicepost.php", stumps["target_template"])
        self.assertEqual(
            "обрезка|спил деревьев|фрезеровка пней",
            stumps["excluded_primary_intents"],
        )
        self.assertEqual("page", holiday["current_post_type"])
        self.assertEqual("servicepost.php", holiday["target_template"])
        for destination_id, row in rows.items():
            self.assertEqual(
                URL_DECISIONS[destination_id].target_url,
                row["target_url"],
            )
            if destination_id in {"S5-CHILD-STUMPS", "S7-CHILD-HOLIDAY"}:
                continue
            self.assertEqual("create", row["url_action"])
            self.assertEqual("", row["current_url"])
            self.assertEqual("", row["current_wp_id"])

    def test_export_fails_closed_when_url_decision_coverage_is_tampered(self) -> None:
        incomplete = dict(URL_DECISIONS)
        incomplete.pop("S1-CHILD-SKETCH")

        with self.assertRaisesRegex(ValueError, "URL decision coverage"):
            build_final_service_rows(url_decisions=incomplete)

    def test_markdown_reports_every_hub_count_and_sparse_reason(self) -> None:
        markdown = render_final_service_structure()

        self.assertIn("Всего дочерних услуг: **37**", markdown)
        for service_id, count in EXPECTED_COUNTS.items():
            marker = f"## {service_id} —"
            self.assertIn(marker, markdown)
            section = markdown.split(marker, 1)[1].split("\n## ", 1)[0]
            self.assertIn(f"Дочерних услуг: **{count}**", section)
        self.assertIn("Q000253", markdown)
        self.assertIn("Q000276", markdown)
        self.assertIn("Q000277", markdown)
        self.assertIn("WP 6870, шаблон `servicepost.php`", markdown)
        self.assertEqual(3, markdown.count("Почему хаб разрежен:"))

    def test_writer_is_utf8_and_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "processed" / "final.csv"
            markdown_path = Path(tmp) / "reviews" / "final.md"

            count = write_final_service_architecture(csv_path, markdown_path)
            first_csv = csv_path.read_bytes()
            first_markdown = markdown_path.read_bytes()
            second_count = write_final_service_architecture(csv_path, markdown_path)

            self.assertEqual(37, count)
            self.assertEqual(count, second_count)
            self.assertEqual(first_csv, csv_path.read_bytes())
            self.assertEqual(first_markdown, markdown_path.read_bytes())
            self.assertFalse(first_csv.startswith(b"\xef\xbb\xbf"))
            self.assertIn("Подпорные стенки".encode("utf-8"), first_markdown)
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                written_rows = list(csv.DictReader(handle))

        self.assertEqual(37, len(written_rows))
        self.assertEqual(list(EXPECTED_COLUMNS), list(written_rows[0]))


if __name__ == "__main__":
    unittest.main()
