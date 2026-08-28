import base64
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.seo_semantics.cli import main
from tools.seo_semantics.manifest import register_source
from tools.seo_semantics.yandex_search import (
    ApiCredentials,
    assert_complete_coverage,
    build_collection_plan,
    load_api_credentials,
    poll_submitted,
    submit_pending,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request_json(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        return self.responses.pop(0)


class YandexSearchApiTest(unittest.TestCase):
    def test_plan_cli_is_read_only_and_needs_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 1)

            result = main(["serp-api-plan", "--queue", str(queue), "--serp-dir", str(serp_dir)])

            self.assertEqual(result, 0)
            self.assertEqual(sorted(path.name for path in serp_dir.iterdir()), ["serp-queue.csv"])

    def test_plan_accepts_a_globally_unique_consecutive_offset_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 13, start=142)

            plan = build_collection_plan(queue, serp_dir)

            self.assertEqual("Q000142", plan.pending_query_ids[0])
            self.assertEqual("Q000154", plan.pending_query_ids[-1])
            self.assertEqual(13, len(plan.pending_query_ids))

    def test_plan_resumes_after_26_captures_and_enforces_exact_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 141)
            self._write_capture(serp_dir / "part-001.jsonl", range(1, 27))

            plan = build_collection_plan(queue, serp_dir)

            self.assertEqual(len(plan.completed_query_ids), 26)
            self.assertEqual(len(plan.pending_query_ids), 115)
            self.assertEqual(plan.pending_query_ids[0], "Q000027")
            self.assertEqual(plan.pending_query_ids[-1], "Q000141")
            self.assertEqual(str(plan.estimated_cost_rub), "3.5075")
            self.assertEqual(plan.max_requests, 115)
            self.assertEqual(str(plan.max_cost_rub), "10")

    def test_plan_rejects_an_empty_capture_as_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 1)
            (serp_dir / "part-001.jsonl").write_text(
                json.dumps(
                    {
                        "query_id": "Q000001",
                        "query": "query 1",
                        "region": "Yaroslavl",
                        "device": "desktop",
                        "checked_at": "2026-08-20T12:00:00+03:00",
                        "results": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "exact ranks 1-10"):
                build_collection_plan(queue, serp_dir)

    def test_plan_rejects_a_capture_bound_to_another_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 1)
            capture = serp_dir / "part-001.jsonl"
            self._write_capture(capture, [1], query_prefix="stale query")

            with self.assertRaisesRegex(ValueError, "differs from queue.*query"):
                build_collection_plan(queue, serp_dir)

    def test_plan_rejects_empty_titles_and_yandex_ad_tracking_urls(self):
        for field, value, message in (
            ("title", "", "title"),
            ("url", "https://yandex.ru/an/count/click", "ad tracking URL"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                serp_dir = Path(tmp) / "serp"
                serp_dir.mkdir()
                queue = self._write_queue(serp_dir, 1)
                capture = serp_dir / "part-001.jsonl"
                self._write_capture(capture, [1])
                record = json.loads(capture.read_text(encoding="utf-8"))
                record["results"][0][field] = value
                capture.write_text(json.dumps(record) + "\n", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, message):
                    build_collection_plan(queue, serp_dir)

    def test_plan_rejects_more_than_115_billable_async_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 116)

            with self.assertRaisesRegex(ValueError, "115-request budget guard"):
                build_collection_plan(queue, serp_dir)

    def test_credentials_require_key_folder_and_explicit_active_billing(self):
        for env in (
            {},
            {"YANDEX_SEARCH_API_KEY": "key", "YANDEX_CLOUD_FOLDER_ID": "folder"},
            {
                "YANDEX_SEARCH_API_KEY": "key",
                "YANDEX_CLOUD_FOLDER_ID": "folder",
                "YANDEX_SEARCH_API_BILLING_ACTIVE": "false",
            },
        ):
            with self.subTest(env=env):
                with self.assertRaisesRegex(ValueError, "billing|credential|folder"):
                    load_api_credentials(env)

        credentials = load_api_credentials(
            {
                "YANDEX_SEARCH_API_KEY": "key",
                "YANDEX_CLOUD_FOLDER_ID": "folder",
                "YANDEX_SEARCH_API_BILLING_ACTIVE": "true",
            }
        )
        self.assertEqual(credentials.folder_id, "folder")

    def test_submit_refuses_inactive_credentials_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            transport = FakeTransport([])

            with self.assertRaisesRegex(ValueError, "active billing"):
                submit_pending(
                    build_collection_plan(queue, serp_dir),
                    ApiCredentials(api_key="key", folder_id="folder", billing_active=False),
                    serp_dir,
                    root / "raw" / "source-manifest.json",
                    "2026-08-20T12:00:00+03:00",
                    transport,
                )
            self.assertEqual(transport.calls, [])

    def test_submit_refuses_invalid_collection_timestamp_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            transport = FakeTransport([{"id": "operation-1"}])

            with self.assertRaisesRegex(ValueError, "ISO-8601|timezone"):
                submit_pending(
                    build_collection_plan(queue, serp_dir),
                    ApiCredentials(api_key="key", folder_id="folder", billing_active=True),
                    serp_dir,
                    root / "raw" / "source-manifest.json",
                    "not-a-timestamp",
                    transport,
                )

            self.assertEqual(transport.calls, [])
            self.assertEqual(list(serp_dir.glob("*-operation.json")), [])

    def test_submit_refuses_an_invalid_manifest_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            manifest.write_text("{broken", encoding="utf-8")
            transport = FakeTransport([{"id": "operation-1"}])

            with self.assertRaisesRegex(ValueError, "manifest"):
                submit_pending(
                    build_collection_plan(queue, serp_dir),
                    ApiCredentials(api_key="key", folder_id="folder", billing_active=True),
                    serp_dir,
                    manifest,
                    "2026-08-20T12:00:00+03:00",
                    transport,
                    pause_seconds=0,
                )

            self.assertEqual(transport.calls, [])
            self.assertEqual(list(serp_dir.glob("*-operation.json")), [])

    def test_submit_refuses_an_incomplete_manifest_entry_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            manifest.write_text(json.dumps({"files": [{}]}), encoding="utf-8")
            transport = FakeTransport([{"id": "operation-1"}])

            with self.assertRaisesRegex(ValueError, "manifest entry"):
                submit_pending(
                    build_collection_plan(queue, serp_dir),
                    ApiCredentials(api_key="key", folder_id="folder", billing_active=True),
                    serp_dir,
                    manifest,
                    "2026-08-20T12:00:00+03:00",
                    transport,
                    pause_seconds=0,
                )

            self.assertEqual(transport.calls, [])
            self.assertEqual(list(serp_dir.glob("*-operation.json")), [])

    def test_submit_is_resumable_immutable_registered_and_never_persists_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            transport = FakeTransport([{"id": "operation-1", "done": False, "createdBy": "account"}])
            credentials = ApiCredentials(api_key="super-secret", folder_id="folder", billing_active=True)
            plan = build_collection_plan(queue, serp_dir)

            written = submit_pending(
                plan,
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                transport,
            )

            self.assertEqual(len(written), 1)
            raw = written[0].read_text(encoding="utf-8")
            self.assertNotIn("super-secret", raw)
            self.assertNotIn("createdBy", raw)
            saved = json.loads(raw)
            self.assertEqual(saved["query_id"], "Q000001")
            self.assertEqual(saved["operation_id"], "operation-1")
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest_payload["files"]), 1)

            resumed = build_collection_plan(queue, serp_dir)
            self.assertEqual(resumed.submitted_query_ids, ("Q000001",))
            self.assertEqual(resumed.pending_query_ids, ())
            self.assertEqual(
                submit_pending(
                    resumed,
                    credentials,
                    serp_dir,
                    manifest,
                    "2026-08-20T12:00:00+03:00",
                    transport,
                ),
                (),
            )
            self.assertEqual(len(transport.calls), 1)

    def test_submit_binds_operations_to_the_full_queue_and_request_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 2)
            manifest = root / "raw" / "source-manifest.json"
            transport = FakeTransport([{"id": "operation-1"}, {"id": "operation-2"}])
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)

            paths = submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                transport,
                pause_seconds=0,
            )

            records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
            self.assertEqual(len(records[0]["queue_sha256"]), 64)
            self.assertEqual(records[0]["queue_sha256"], records[1]["queue_sha256"])
            self.assertEqual(records[0]["batch_sha256"], records[1]["batch_sha256"])
            self.assertNotEqual(records[0]["request_sha256"], records[1]["request_sha256"])

            queue.write_text(
                queue.read_text(encoding="utf-8").replace("query 2", "changed query"),
                encoding="utf-8",
            )
            poll_transport = FakeTransport([{"done": False}, {"done": False}])
            with self.assertRaisesRegex(ValueError, "queue snapshot"):
                poll_submitted(
                    build_collection_plan(queue, serp_dir),
                    credentials,
                    serp_dir,
                    manifest,
                    "2026-08-20T12:10:00+03:00",
                    poll_transport,
                    pause_seconds=0,
                )
            self.assertEqual(poll_transport.calls, [])

    def test_poll_rejects_a_manifest_hash_mismatch_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            operation_path = submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}]),
                pause_seconds=0,
            )[0]
            operation_path.write_text(
                operation_path.read_text(encoding="utf-8").replace("operation-1", "operation-X"),
                encoding="utf-8",
            )
            transport = FakeTransport([{"done": False}])

            with self.assertRaisesRegex(ValueError, "manifest"):
                poll_submitted(
                    build_collection_plan(queue, serp_dir),
                    credentials,
                    serp_dir,
                    manifest,
                    "2026-08-20T12:10:00+03:00",
                    transport,
                    pause_seconds=0,
                )
            self.assertEqual(transport.calls, [])

    def test_lifetime_budget_keeps_completed_submissions_billable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 115)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": f"operation-{index}"} for index in range(1, 116)]),
                pause_seconds=0,
            )
            self._write_capture(serp_dir / "completed.jsonl", range(1, 116))

            completed_plan = build_collection_plan(queue, serp_dir)

            self.assertEqual(str(completed_plan.estimated_cost_rub), "3.5075")
            expanded_queue = self._write_queue(serp_dir, 116)
            with self.assertRaisesRegex(ValueError, "115-request budget guard"):
                build_collection_plan(expanded_queue, serp_dir)

    def test_poll_reports_completed_remaining_and_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 3)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}, {"id": "operation-2"}, {"id": "operation-3"}]),
                pause_seconds=0,
            )
            xml = self._xml_capture()
            transport = FakeTransport(
                [
                    {"done": True, "response": {"rawData": base64.b64encode(xml.encode()).decode()}},
                    {"done": False},
                    {"done": False, "error": {"code": 13, "message": "failed"}},
                ]
            )

            result = poll_submitted(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:10:00+03:00",
                transport,
                pause_seconds=0,
            )

            self.assertTrue(hasattr(result, "completed_query_ids"))
            self.assertEqual(result.completed_query_ids, ("Q000001",))
            self.assertEqual(result.remaining_query_ids, ("Q000002", "Q000003"))
            self.assertEqual(result.errors, ("Q000003: failed",))
            self.assertEqual(len(result.written_paths), 1)

    def test_poll_refuses_invalid_collection_timestamp_before_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}]),
                pause_seconds=0,
            )
            transport = FakeTransport([{"done": False}])

            with self.assertRaisesRegex(ValueError, "ISO-8601|timezone"):
                poll_submitted(
                    build_collection_plan(queue, serp_dir),
                    credentials,
                    serp_dir,
                    manifest,
                    "not-a-timestamp",
                    transport,
                    pause_seconds=0,
                )

            self.assertEqual(transport.calls, [])
            self.assertFalse((serp_dir / "yandex-api-Q000001.jsonl").exists())

    def test_poll_reconciles_existing_raw_files_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}]),
                pause_seconds=0,
            )
            (serp_dir / "yandex-api-Q000001.xml").write_text(
                "<yandexsearch><response><results /></response></yandexsearch>",
                encoding="utf-8",
            )
            self._write_capture(serp_dir / "yandex-api-Q000001.jsonl", range(1, 2))
            transport = FakeTransport([])

            result = poll_submitted(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:10:00+03:00",
                transport,
                pause_seconds=0,
            )

            self.assertEqual(transport.calls, [])
            self.assertTrue(hasattr(result, "completed_query_ids"))
            self.assertEqual(result.completed_query_ids, ("Q000001",))
            entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
            self.assertEqual(
                {entry["path"] for entry in entries},
                {
                    "serp/yandex-api-Q000001-operation.json",
                    "serp/yandex-api-Q000001.jsonl",
                },
            )

    def test_verify_cli_requires_exact_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            serp_dir = Path(tmp) / "serp"
            serp_dir.mkdir()
            queue = self._write_queue(serp_dir, 1)

            try:
                missing_result = main(
                    ["serp-api-verify", "--queue", str(queue), "--serp-dir", str(serp_dir)]
                )
            except SystemExit as exc:
                missing_result = f"unexpected SystemExit {exc.code}"
            self.assertEqual(missing_result, 2)

            self._write_capture(serp_dir / "complete.jsonl", range(1, 2))
            complete_result = main(
                ["serp-api-verify", "--queue", str(queue), "--serp-dir", str(serp_dir)]
            )
            self.assertEqual(complete_result, 0)

    def test_manifest_registration_is_idempotent_but_rejects_rebaselining(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "raw" / "evidence.json"
            source.parent.mkdir()
            source.write_text("one", encoding="utf-8")
            manifest = root / "raw" / "source-manifest.json"
            first = register_source(source, "serp", "2026-08-20T12:00:00+03:00", manifest)
            original_manifest = manifest.read_bytes()

            recovered = register_source(source, "serp", "2026-08-20T13:00:00+03:00", manifest)

            self.assertEqual(recovered, first)
            self.assertEqual(manifest.read_bytes(), original_manifest)
            source.write_text("two", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "immutable manifest entry differs"):
                register_source(source, "serp", "2026-08-20T14:00:00+03:00", manifest)

    def test_failed_atomic_manifest_publish_preserves_the_previous_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            raw.mkdir()
            first = raw / "first.json"
            second = raw / "second.json"
            first.write_text("one", encoding="utf-8")
            second.write_text("two", encoding="utf-8")
            manifest = raw / "source-manifest.json"
            register_source(first, "serp", "2026-08-20T12:00:00+03:00", manifest)
            original_manifest = manifest.read_bytes()

            with patch("tools.seo_semantics.manifest.os.replace", side_effect=OSError("publish failed")):
                with self.assertRaisesRegex(OSError, "publish failed"):
                    register_source(second, "serp", "2026-08-20T12:01:00+03:00", manifest)

            self.assertEqual(manifest.read_bytes(), original_manifest)
            self.assertEqual(sorted(path.name for path in raw.iterdir()), [
                "first.json", "second.json", "source-manifest.json"
            ])

    def test_poll_persists_only_sanitized_organic_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}]),
                pause_seconds=0,
            )
            xml = self._xml_capture(include_passage=True)
            transport = FakeTransport(
                [{"done": True, "response": {"rawData": base64.b64encode(xml.encode()).decode()}}]
            )

            written = poll_submitted(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:10:00+03:00",
                transport,
            )

            self.assertEqual(len(written), 1)
            xml_path = serp_dir / "yandex-api-Q000001.xml"
            jsonl_path = serp_dir / "yandex-api-Q000001.jsonl"
            self.assertFalse(xml_path.exists())
            record = json.loads(jsonl_path.read_text(encoding="utf-8"))
            self.assertEqual(record["query_id"], "Q000001")
            self.assertEqual(len(record["results"]), 10)
            self.assertEqual(record["results"][0], {
                "rank": 1, "url": "https://result-1.example/page", "title": "Result 1",
            })
            self.assertNotIn("competitor passage", jsonl_path.read_text(encoding="utf-8"))
            self.assertTrue(assert_complete_coverage(queue, serp_dir))
            entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
            self.assertEqual({entry["path"] for entry in entries}, {
                "serp/yandex-api-Q000001-operation.json",
                "serp/yandex-api-Q000001.jsonl",
            })
            self.assertNotIn("key", "".join(path.read_text(encoding="utf-8") for path in written))

    def test_poll_ignores_untracked_xml_and_uses_the_operation_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            serp_dir = root / "raw" / "serp"
            serp_dir.mkdir(parents=True)
            queue = self._write_queue(serp_dir, 1)
            manifest = root / "raw" / "source-manifest.json"
            credentials = ApiCredentials(api_key="key", folder_id="folder", billing_active=True)
            submit_pending(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:00:00+03:00",
                FakeTransport([{"id": "operation-1"}]),
                pause_seconds=0,
            )
            stale_xml = self._xml_capture().replace(
                "https://result-",
                "https://stale-result-",
            )
            (serp_dir / "yandex-api-Q000001.xml").write_text(stale_xml, encoding="utf-8")
            current_xml = self._xml_capture()
            transport = FakeTransport(
                [{"done": True, "response": {"rawData": base64.b64encode(current_xml.encode()).decode()}}]
            )

            result = poll_submitted(
                build_collection_plan(queue, serp_dir),
                credentials,
                serp_dir,
                manifest,
                "2026-08-20T12:10:00+03:00",
                transport,
                pause_seconds=0,
            )

            record = json.loads(
                (serp_dir / "yandex-api-Q000001.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(result.completed_query_ids, ("Q000001",))
            self.assertEqual(record["results"][0]["url"], "https://result-1.example/page")

    @staticmethod
    def _write_queue(serp_dir: Path, count: int, start: int = 1) -> Path:
        path = serp_dir / "serp-queue.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=(
                    "query_id", "query", "service_id", "intent", "region",
                    "device", "reason", "status",
                ),
            )
            writer.writeheader()
            for index in range(start, start + count):
                writer.writerow(
                    {
                        "query_id": f"Q{index:06d}",
                        "query": f"query {index}",
                        "service_id": "S1",
                        "intent": "commercial_research",
                        "region": "Yaroslavl",
                        "device": "desktop",
                        "reason": "fixture",
                        "status": "pending",
                    }
                )
        return path

    @staticmethod
    def _write_capture(path: Path, indexes, query_prefix: str = "query") -> None:
        with path.open("w", encoding="utf-8") as handle:
            for index in indexes:
                handle.write(
                    json.dumps(
                        {
                            "query_id": f"Q{index:06d}",
                            "query": f"{query_prefix} {index}",
                            "region": "Yaroslavl",
                            "device": "desktop",
                            "checked_at": "2026-08-20T12:00:00+03:00",
                            "results": [
                                {
                                    "rank": rank,
                                    "url": f"https://result-{index}-{rank}.example/page",
                                    "title": f"Result {rank}",
                                }
                                for rank in range(1, 11)
                            ],
                        }
                    )
                    + "\n"
                )

    @staticmethod
    def _xml_capture(include_passage: bool = False) -> str:
        docs = []
        for rank in range(1, 11):
            passage = (
                "<passages><passage>competitor passage</passage></passages>"
                if include_passage
                else ""
            )
            docs.append(
                "<group><doc>"
                f"<url>https://result-{rank}.example/page</url>"
                f"<title>Result {rank}</title>{passage}"
                "</doc></group>"
            )
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            "<yandexsearch><response><results><grouping>"
            + "".join(docs)
            + "</grouping></results></response></yandexsearch>"
        )


if __name__ == "__main__":
    unittest.main()
