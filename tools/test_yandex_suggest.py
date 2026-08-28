"""Contracts for bounded Yandex Suggest expansion of the final SEO silo."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.expanded_architecture import all_expanded_pages
from tools.seo_semantics.manifest import register_source
from tools.seo_semantics.reviewed_service_architecture import all_reviewed_children
from tools.seo_semantics.yandex_suggest import (
    build_expanded_suggest_queue,
    build_reviewed_suggest_queue,
    collect_suggestions,
    load_suggestion_evidence,
    suggestion_assignments,
    read_suggest_queue,
)


class FakeSuggestTransport:
    def __init__(self, payloads: dict[str, object]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, int]] = []

    def fetch(self, seed: str, region_id: int) -> object:
        self.calls.append((seed, region_id))
        return self.payloads[seed]


class YandexSuggestTests(unittest.TestCase):
    def test_checked_in_reviewed_v6_is_exact_and_provenance_bound(self) -> None:
        data_root = (
            Path(__file__).resolve().parents[1]
            / "seo-data"
            / "2026-08-exp76-services"
        )
        raw_root = data_root / "raw" / "reviewed-suggest-v6"
        queue = read_suggest_queue(raw_root / "suggest-queue.csv")
        evidence = load_suggestion_evidence(
            queue,
            raw_root,
            raw_root / "source-manifest.json",
        )
        self.assertEqual(74, len(queue))
        self.assertEqual(74, len(evidence))
        self.assertEqual(build_reviewed_suggest_queue(start_query_number=505), queue)
        self.assertEqual(
            {page.destination_id for page in all_reviewed_children()},
            {row["destination_id"] for row in queue},
        )

        manifest_path = data_root / "processed" / "source-manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = {entry["path"]: entry for entry in payload["files"]}
        required = {
            "../raw/reviewed-suggest-v6/source-manifest.json",
            "../raw/reviewed-suggest-v6/suggest-queue.csv",
            "reviewed_suggestion_candidates_v6.csv",
        }
        self.assertTrue(required <= set(entries))
        for relative in required:
            entry = entries[relative]
            target = (manifest_path.parent / relative).resolve()
            data = target.read_bytes()
            self.assertEqual(len(data), entry["byte_count"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

    def test_queue_covers_every_page_and_adds_transactional_child_probe(self) -> None:
        rows = build_expanded_suggest_queue(start_query_number=1)
        pages = all_expanded_pages()
        page_ids = {page.destination_id for page in pages}

        self.assertEqual(page_ids, {row["destination_id"] for row in rows})
        self.assertEqual("YS000001", rows[0]["query_id"])
        self.assertEqual(len(rows), len({row["query_id"] for row in rows}))
        self.assertLessEqual(len(rows), 150)
        self.assertEqual({"10841"}, {row["region_id"] for row in rows})
        for page in pages:
            page_rows = [row for row in rows if row["destination_id"] == page.destination_id]
            expected = 2 if page.page_role == "child_service" else 1
            self.assertEqual(expected, len(page_rows), page.destination_id)

    def test_reviewed_queue_uses_only_the_final_publishable_children(self) -> None:
        rows = build_reviewed_suggest_queue(start_query_number=137)
        pages = all_reviewed_children()

        self.assertEqual(74, len(rows))
        self.assertEqual(
            {page.destination_id for page in pages},
            {row["destination_id"] for row in rows},
        )
        self.assertEqual("YS000137", rows[0]["query_id"])
        self.assertEqual("YS000210", rows[-1]["query_id"])
        self.assertEqual({"child_service"}, {row["page_role"] for row in rows})
        for page in pages:
            self.assertEqual(
                2,
                sum(row["destination_id"] == page.destination_id for row in rows),
                page.destination_id,
            )

    def test_collection_is_resumable_bound_and_never_logs_a_credential(self) -> None:
        queue = [
            {
                "query_id": "YS000001",
                "seed": "подпорная стенка из камня",
                "service_id": "S6",
                "destination_id": "S6-CHILD-STONE",
                "page_role": "child_service",
                "region_id": "10841",
                "reason": "expanded_suggest_root[S6-CHILD-STONE]",
            }
        ]
        transport = FakeSuggestTransport(
            {
                "подпорная стенка из камня": [
                    "подпорная стенка из камня",
                    [
                        "подпорная стенка из природного камня",
                        "подпорная стенка из камня своими руками",
                    ],
                    {"r": 10841},
                ]
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = collect_suggestions(
                queue,
                root,
                root / "source-manifest.json",
                "2026-08-28T23:30:00+03:00",
                transport=transport,
                pause_seconds=0,
            )
            second = collect_suggestions(
                queue,
                root,
                root / "source-manifest.json",
                "2026-08-28T23:31:00+03:00",
                transport=transport,
                pause_seconds=0,
            )
            evidence = load_suggestion_evidence(
                queue,
                root,
                root / "source-manifest.json",
            )

        self.assertEqual(1, len(written))
        self.assertEqual((), second)
        self.assertEqual(1, len(transport.calls))
        self.assertEqual(
            [
                "подпорная стенка из природного камня",
                "подпорная стенка из камня своими руками",
            ],
            evidence["YS000001"]["suggestions"],
        )

    def test_evidence_fails_closed_on_queue_or_payload_drift(self) -> None:
        queue = [
            {
                "query_id": "YS000001",
                "seed": "газон рулонный",
                "service_id": "S2",
                "destination_id": "S2-CHILD-ROLL",
                "page_role": "child_service",
                "region_id": "10841",
                "reason": "expanded_suggest_root[S2-CHILD-ROLL]",
            }
        ]
        record = {
            **queue[0],
            "checked_at": "2026-08-28T23:30:00+03:00",
            "suggestions": ["рулонный газон с укладкой"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "yandex-suggest-YS000001.jsonl"
            path.write_text(
                json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            manifest = root / "source-manifest.json"
            register_source(path, "yandex_suggest", record["checked_at"], manifest)
            changed = [dict(queue[0], seed="посевной газон")]
            with self.assertRaisesRegex(ValueError, "differs from queue"):
                load_suggestion_evidence(changed, root, manifest)

            record["suggestions"] = ["", "валидная подсказка"]
            path.write_text(
                json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "manifest hash differs"):
                load_suggestion_evidence(queue, root, manifest)

    def test_cross_destination_duplicates_are_review_conflicts(self) -> None:
        queue = [
            {
                "query_id": "YS000001",
                "seed": "устройство газона",
                "service_id": "S2",
                "destination_id": "S2-HUB",
                "page_role": "hub",
                "region_id": "10841",
                "reason": "test",
            },
            {
                "query_id": "YS000002",
                "seed": "подготовка грунта под газон",
                "service_id": "S2",
                "destination_id": "S2-CHILD-SOIL",
                "page_role": "child_service",
                "region_id": "10841",
                "reason": "test",
            },
        ]
        evidence = {
            "YS000001": {**queue[0], "suggestions": ["подготовка участка под газон"]},
            "YS000002": {**queue[1], "suggestions": ["Подготовка  участка под газон"]},
        }

        rows = suggestion_assignments(queue, evidence)

        self.assertEqual(2, len(rows))
        self.assertEqual({"needs_destination_review"}, {row["assignment_status"] for row in rows})
        self.assertEqual(
            {"S2-CHILD-SOIL|S2-HUB"},
            {row["conflicting_destination_ids"] for row in rows},
        )

    def test_cross_service_duplicates_are_review_conflicts(self) -> None:
        queue = [
            {
                "query_id": "YS000001",
                "seed": "вертикальная планировка участка",
                "service_id": "S1",
                "destination_id": "S1-CHILD-RELIEF",
                "page_role": "child_service",
                "region_id": "10841",
                "reason": "test",
            },
            {
                "query_id": "YS000002",
                "seed": "выравнивание участка",
                "service_id": "S5",
                "destination_id": "S5-CHILD-VERTICAL",
                "page_role": "child_service",
                "region_id": "10841",
                "reason": "test",
            },
        ]
        evidence = {
            "YS000001": {**queue[0], "suggestions": ["план вертикальной планировки участка"]},
            "YS000002": {**queue[1], "suggestions": ["План вертикальной планировки участка"]},
        }

        rows = suggestion_assignments(queue, evidence)

        self.assertEqual(
            {"needs_destination_review"},
            {row["assignment_status"] for row in rows},
        )
        self.assertEqual(
            {"S1-CHILD-RELIEF|S5-CHILD-VERTICAL"},
            {row["conflicting_destination_ids"] for row in rows},
        )


if __name__ == "__main__":
    unittest.main()
