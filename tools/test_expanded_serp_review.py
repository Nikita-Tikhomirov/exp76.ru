from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.seo_semantics.expanded_architecture import all_expanded_pages
from tools.seo_semantics.expanded_serp_review import (
    FORMAT_NAMES,
    RELEVANCE_NAMES,
    REVIEW_COLUMNS,
    build_expanded_destination_reviews,
    validate_expanded_review_rows,
    write_expanded_destination_reviews,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "seo-data" / "2026-08-exp76-services"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def update_manifest_hash(manifest_path: Path, relative_path: str) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = manifest_path.parent / relative_path
    data = target.read_bytes()
    for entry in payload["files"]:
        if entry["path"] == relative_path:
            entry["sha256"] = hashlib.sha256(data).hexdigest()
            entry["byte_count"] = len(data)
            break
    else:
        raise AssertionError(f"manifest entry not found: {relative_path}")
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def copy_review_evidence(destination: Path) -> Path:
    copied_root = destination / "seo-data" / "2026-08-exp76-services"
    copied_raw = copied_root / "raw"
    copied_raw.mkdir(parents=True)
    shutil.copytree(DATA_ROOT / "raw" / "expanded-serp", copied_raw / "expanded-serp")
    shutil.copytree(
        DATA_ROOT / "raw" / "expanded-serp-targeted",
        copied_raw / "expanded-serp-targeted",
    )
    (copied_raw / "serp").mkdir()
    for name in (
        "serp-queue.csv",
        "yandex-organic-2026-08-20-part-004.jsonl",
        "yandex-api-Q000040.jsonl",
        "yandex-api-Q000063.jsonl",
        "yandex-api-Q000078.jsonl",
        "yandex-api-Q000098.jsonl",
        "yandex-api-Q000104.jsonl",
        "yandex-api-Q000109.jsonl",
        "yandex-api-Q000117.jsonl",
    ):
        shutil.copy2(DATA_ROOT / "raw" / "serp" / name, copied_raw / "serp" / name)
    shutil.copy2(DATA_ROOT / "raw" / "source-manifest.json", copied_raw)
    return copied_root


class ExpandedSerpReviewTest(unittest.TestCase):
    def test_build_links_exactly_92_destinations_to_primary_and_targeted_probes(self) -> None:
        primary_queue = read_csv(DATA_ROOT / "raw" / "expanded-serp" / "serp-queue.csv")
        targeted_queue = read_csv(
            DATA_ROOT / "raw" / "expanded-serp-targeted" / "serp-queue.csv"
        )
        rows = build_expanded_destination_reviews(DATA_ROOT)
        self.assertEqual(92, len(rows))
        self.assertEqual(
            [queue_row["destination_id"] for queue_row in primary_queue],
            [row["destination_id"] for row in rows],
        )
        self.assertEqual(
            [f"Q{number:06d}" for number in range(155, 247)],
            [row["primary_query_id"] for row in rows],
        )
        targeted = {
            queue_row["destination_id"]: queue_row["query_id"]
            for queue_row in targeted_queue
        }
        self.assertEqual(
            targeted,
            {
                row["destination_id"]: row["targeted_query_id"]
                for row in rows
                if row["targeted_query_id"]
            },
        )
        for row in rows:
            for field in ("primary_format_counts",):
                counts = json.loads(row[field])
                self.assertEqual(set(FORMAT_NAMES), set(counts))
                self.assertEqual(10, sum(counts.values()))
            relevance = json.loads(row["primary_relevance_counts"])
            self.assertEqual(set(RELEVANCE_NAMES), set(relevance))
            self.assertEqual(10, sum(relevance.values()))
            if row["targeted_query_id"]:
                self.assertEqual(10, sum(json.loads(row["targeted_format_counts"]).values()))
                self.assertEqual(10, sum(json.loads(row["targeted_relevance_counts"]).values()))
            else:
                self.assertEqual("", row["targeted_format_counts"])
                self.assertEqual("", row["targeted_relevance_counts"])
            for field in (
                "primary_legacy_hub_overlap",
                "max_legacy_hub_overlap",
                "max_sibling_overlap",
                "max_cross_service_overlap",
            ):
                self.assertIn(int(row[field]), range(11))
            self.assertTrue(row["ruling_id"])
            self.assertTrue(row["rationale"])
            self.assertTrue(row["boundary"])

    def test_primary_is_not_superseded_by_targeted_and_cross_service_risk_is_visible(self) -> None:
        by_id = {row["destination_id"]: row for row in build_expanded_destination_reviews(DATA_ROOT)}
        relief = by_id["S1-CHILD-RELIEF"]
        self.assertEqual("Q000159", relief["max_cross_service_left_query_id"])
        self.assertEqual("S5-CHILD-VERTICAL", relief["max_cross_service_destination_id"])
        self.assertEqual("Q000203", relief["max_cross_service_right_query_id"])
        self.assertEqual("5", relief["max_cross_service_overlap"])
        self.assertEqual("needs_review", relief["final_decision"])
        self.assertEqual("blocked_cannibalization", relief["final_status"])

    def test_irrelevant_gazon_next_results_force_an_explicit_rejection(self) -> None:
        by_id = {row["destination_id"]: row for row in build_expanded_destination_reviews(DATA_ROOT)}
        initial = by_id["S2-CHILD-INITIAL-CARE"]
        self.assertGreaterEqual(json.loads(initial["targeted_relevance_counts"])["irrelevant"], 7)
        self.assertEqual("reject", initial["final_decision"])
        self.assertEqual("rejected", initial["final_status"])
        self.assertIn("M002", initial["manual_ruling_ids"])
        self.assertIn("Q000253", initial["manual_ruling_evidence_refs"])
        headwalls = by_id["S8-CHILD-HEADWALLS"]
        self.assertGreaterEqual(json.loads(headwalls["targeted_relevance_counts"])["product"], 1)

    def test_required_cross_service_boundaries_have_manual_pair_rulings(self) -> None:
        by_id = {row["destination_id"]: row for row in build_expanded_destination_reviews(DATA_ROOT)}
        expected = {
            "M001": ("S1-CHILD-RELIEF", "S5-CHILD-VERTICAL"),
            "M002": ("S2-CHILD-INITIAL-CARE", "S4-CHILD-LAWN-CARE"),
            "M003": ("S2-CHILD-SOIL", "S5-CHILD-FOR-LAWN"),
        }
        for ruling_id, pair in expected.items():
            for destination_id in pair:
                self.assertIn(ruling_id, by_id[destination_id]["manual_ruling_ids"])
                self.assertTrue(by_id[destination_id]["manual_ruling_evidence_refs"])

    def test_high_overlap_is_not_automatically_kept_and_manual_merges_are_explicit(self) -> None:
        by_id = {row["destination_id"]: row for row in build_expanded_destination_reviews(DATA_ROOT)}
        concrete = by_id["S6-CHILD-CONCRETE"]
        self.assertGreaterEqual(int(concrete["max_sibling_overlap"]), 4)
        self.assertEqual("needs_review", concrete["final_decision"])
        self.assertTrue(concrete["final_status"].startswith("blocked_"))
        self.assertEqual("merge", by_id["S7-ARTICLE-SCHEME"]["final_decision"])
        self.assertEqual("S7-ARTICLE-DIY", by_id["S7-ARTICLE-SCHEME"]["merge_target"])
        self.assertEqual("merge", by_id["S8-ARTICLE-DIAMETER"]["final_decision"])
        self.assertEqual("S8-ARTICLE-PIPE", by_id["S8-ARTICLE-DIAMETER"]["merge_target"])

    def test_writer_is_deterministic_without_publishing_a_stale_production_ledger(self) -> None:
        expected = build_expanded_destination_reviews(DATA_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "review.csv"
            self.assertEqual(92, write_expanded_destination_reviews(DATA_ROOT, output))
            self.assertEqual(expected, read_csv(output))
            self.assertEqual(tuple(REVIEW_COLUMNS), tuple(read_csv_header(output)))

    def test_review_tolerates_a_revised_registry_with_fewer_commercial_children(self) -> None:
        removed = {
            "S2-CHILD-INITIAL-CARE",
            "S3-CHILD-DECIDUOUS",
            "S4-CHILD-SEASONAL",
            "S5-CHILD-SOIL",
            "S5-CHILD-FOR-LAWN",
            "S6-CHILD-SLOPE",
            "S6-CHILD-BLOCKS",
            "S7-CHILD-PATHS",
            "S7-CHILD-SECURITY",
            "S8-CHILD-BASE",
            "S8-CHILD-HEADWALLS",
        }
        active = tuple(page for page in all_expanded_pages() if page.destination_id not in removed)
        with patch(
            "tools.seo_semantics.expanded_serp_review.all_expanded_pages",
            return_value=active,
        ):
            rows = build_expanded_destination_reviews(DATA_ROOT)
        self.assertEqual(92, len(rows))
        by_id = {row["destination_id"]: row for row in rows}
        self.assertEqual(
            {"removed_from_registry"},
            {by_id[destination_id]["offer_status"] for destination_id in removed},
        )
        self.assertEqual(
            {"reject"},
            {by_id[destination_id]["final_decision"] for destination_id in removed},
        )
        child_candidates = [row for row in rows if row["page_role"] == "child_service"]
        self.assertEqual(36, len(child_candidates) - len(removed) + 3)  # HEDGE, GABIONS, HOLIDAY

    def test_review_validation_rejects_duplicate_row_and_missing_evidence(self) -> None:
        rows = build_expanded_destination_reviews(DATA_ROOT)
        corrupted = [dict(row) for row in rows]
        corrupted[-1]["destination_id"] = corrupted[0]["destination_id"]
        corrupted[0]["evidence_refs"] += "|raw/expanded-serp/does-not-exist.jsonl|Q999999"
        errors = validate_expanded_review_rows(corrupted, DATA_ROOT)
        self.assertTrue(any("destination coverage mismatch" in error for error in errors))
        self.assertTrue(any("evidence path does not exist" in error for error in errors))

    def test_manifest_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = copy_review_evidence(Path(temporary))
            result_path = copied / "raw" / "expanded-serp" / "yandex-api-Q000155.jsonl"
            data = bytearray(result_path.read_bytes())
            data[0] ^= 1
            result_path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "manifest hash mismatch"):
                build_expanded_destination_reviews(copied)

    def test_queue_mismatch_is_rejected_even_with_a_matching_manifest_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = copy_review_evidence(Path(temporary))
            queue_path = copied / "raw" / "expanded-serp" / "serp-queue.csv"
            rows = read_csv(queue_path)
            rows[0]["destination_id"] = rows[1]["destination_id"]
            with queue_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            update_manifest_hash(queue_path.parent / "source-manifest.json", "serp-queue.csv")
            with self.assertRaisesRegex(ValueError, "primary queue mismatch"):
                build_expanded_destination_reviews(copied)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


if __name__ == "__main__":
    unittest.main()
