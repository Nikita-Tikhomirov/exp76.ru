"""Integrity and decision tests for the last paid SERP probes."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.finalization_serp_review import (
    build_finalization_serp_audit,
    validate_finalization_serp_evidence,
    write_finalization_serp_audit,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "seo-data" / "2026-08-exp76-services"


class FinalizationSerpReviewTests(unittest.TestCase):
    def test_manifest_queue_and_results_are_complete_and_immutable(self) -> None:
        self.assertEqual([], validate_finalization_serp_evidence(DATA_ROOT))
        rows = build_finalization_serp_audit(DATA_ROOT)
        self.assertEqual(8, len(rows))
        self.assertEqual(
            [f"Q{number:06d}" for number in range(273, 281)],
            [row.query_id for row in rows],
        )
        self.assertEqual({10}, {row.result_count for row in rows})

    def test_pipe_material_probes_are_merged_by_measured_overlap(self) -> None:
        rows = {row.query_id: row for row in build_finalization_serp_audit(DATA_ROOT)}
        self.assertEqual(7, rows["Q000277"].pipe_overlap)
        self.assertEqual(7, rows["Q000278"].pipe_overlap)
        self.assertEqual(6, rows["Q000279"].pipe_overlap)
        self.assertEqual(
            {"merge_to_generic_pipe"},
            {rows[qid].decision for qid in ("Q000277", "Q000278", "Q000279")},
        )

    def test_business_evidence_and_serp_limits_are_reported_honestly(self) -> None:
        rows = {row.query_id: row for row in build_finalization_serp_audit(DATA_ROOT)}
        self.assertEqual(5, rows["Q000273"].modifier_specific_results)
        self.assertEqual(0, rows["Q000276"].modifier_specific_results)
        self.assertEqual(4, rows["Q000280"].modifier_specific_results)
        self.assertEqual("defer_business_confirmation", rows["Q000275"].decision)
        self.assertEqual(
            "keep_business_proven_low_frequency",
            rows["Q000276"].decision,
        )
        self.assertEqual("keep", rows["Q000273"].decision)
        self.assertEqual("keep", rows["Q000274"].decision)
        self.assertEqual("keep", rows["Q000280"].decision)

    def test_tampered_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "seo-data"
            source = DATA_ROOT / "raw" / "expanded-serp-finalization"
            target = copied_root / "raw" / "expanded-serp-finalization"
            shutil.copytree(source, target)
            result = target / "yandex-api-Q000273.jsonl"
            data = bytearray(result.read_bytes())
            data[-2] ^= 1
            result.write_bytes(data)
            errors = validate_finalization_serp_evidence(copied_root)
            self.assertTrue(any("hash mismatch" in error for error in errors))

    def test_writer_is_deterministic(self) -> None:
        expected = build_finalization_serp_audit(DATA_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "audit.csv"
            self.assertEqual(8, write_finalization_serp_audit(DATA_ROOT, output))
            first = output.read_bytes()
            self.assertEqual(8, write_finalization_serp_audit(DATA_ROOT, output))
            self.assertEqual(first, output.read_bytes())
            checked_in = DATA_ROOT / "reviews" / "finalization_serp_decisions.csv"
            self.assertEqual(checked_in.read_bytes(), output.read_bytes())
        self.assertEqual("Q000273", expected[0].query_id)


if __name__ == "__main__":
    unittest.main()
