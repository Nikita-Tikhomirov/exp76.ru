from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "seo-data" / "2026-08-exp76-services"
RAW_ROOT = DATA_ROOT / "raw" / "article-serp"
QUEUE_PATH = RAW_ROOT / "serp-queue.csv"
MANIFEST_PATH = RAW_ROOT / "source-manifest.json"
REVIEW_PATH = DATA_ROOT / "reviews" / "article_destination_serp_reviews.csv"

EXPECTED_DESTINATIONS = {
    "Q000001": "S4-ARTICLE-PRUNING-GUIDE",
    "Q000002": "S2-ARTICLE-15A8258BC551",
    "Q000003": "S2-ARTICLE-182825428CBD",
    "Q000004": "S1-ARTICLE-505521C7EF8C",
    "Q000005": "S6-ARTICLE-DIY-RETAINING-WALL",
    "Q000006": "S1-ARTICLE-72FBB49E67C8",
    "Q000007": "S5-ARTICLE-74B3B2B18DA4",
    "Q000008": "S1-ARTICLE-DIY-DESIGN",
    "Q000009": "S3-ARTICLE-PLANTING-SCHEMES",
    "Q000010": "S8-ARTICLE-DIY-ENTRANCE",
    "Q000011": "S7-ARTICLE-DIY-LIGHTING",
    "Q000012": "S4-ARTICLE-F668FF6F6190",
    "Q000013": "S5-ARTICLE-FF3B04A53D72",
}

EXPECTED_OVERLAPS = {
    ("Q000002", "Q000003"): 1,
    ("Q000004", "Q000006"): 3,
    ("Q000008", "Q000013"): 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_result(query_id: str) -> dict[str, object]:
    path = RAW_ROOT / f"yandex-api-{query_id}.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(lines) != 1:
        raise AssertionError(f"{path.name} must contain one immutable record")
    return json.loads(lines[0])


class ArticleSerpEvidenceTest(unittest.TestCase):
    def test_queue_covers_exact_thirteen_article_destinations(self) -> None:
        rows = read_csv(QUEUE_PATH)
        self.assertEqual(list(EXPECTED_DESTINATIONS), [row["query_id"] for row in rows])
        self.assertEqual(13, len(rows))
        self.assertEqual(13, len({row["query"] for row in rows}))
        for row in rows:
            self.assertEqual("informational", row["intent"])
            self.assertEqual("Yaroslavl", row["region"])
            self.assertEqual("desktop", row["device"])
            self.assertEqual(
                f"article_representative[{EXPECTED_DESTINATIONS[row['query_id']]}]",
                row["reason"],
            )

    def test_every_result_is_sanitized_exact_top_ten(self) -> None:
        queue = {row["query_id"]: row for row in read_csv(QUEUE_PATH)}
        for query_id, row in queue.items():
            operation = json.loads(
                (RAW_ROOT / f"yandex-api-{query_id}-operation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(query_id, operation["query_id"])
            self.assertEqual(row["query"], operation["query"])
            self.assertNotIn("api_key", json.dumps(operation).casefold())
            self.assertNotIn("authorization", json.dumps(operation).casefold())

            result = read_result(query_id)
            self.assertEqual(
                {"query_id", "query", "region", "device", "checked_at", "results"},
                set(result),
            )
            self.assertEqual(row["query"], result["query"])
            items = result["results"]
            self.assertIsInstance(items, list)
            self.assertEqual(list(range(1, 11)), [item["rank"] for item in items])
            for item in items:
                self.assertEqual({"rank", "url", "title"}, set(item))

    def test_source_manifest_hashes_every_immutable_file(self) -> None:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        entries = payload["files"]
        self.assertEqual(27, len(entries))
        self.assertEqual(27, len({entry["path"] for entry in entries}))
        for entry in entries:
            path = RAW_ROOT / entry["path"]
            data = path.read_bytes()
            self.assertEqual(len(data), entry["byte_count"], entry["path"])
            self.assertEqual(
                hashlib.sha256(data).hexdigest(), entry["sha256"], entry["path"]
            )

    def test_review_is_complete_and_keeps_no_unsupported_extra_page(self) -> None:
        rows = read_csv(REVIEW_PATH)
        by_query = {row["query_id"]: row for row in rows}
        self.assertEqual(set(EXPECTED_DESTINATIONS), set(by_query))
        self.assertEqual(13, len(rows))
        for query_id, destination_id in EXPECTED_DESTINATIONS.items():
            row = by_query[query_id]
            self.assertEqual(destination_id, row["destination_id"])
            self.assertEqual("reviewed", row["review_status"])
            self.assertTrue(row["rationale"].strip())
            self.assertIn(query_id, row["evidence_refs"])

        merged = [row for row in rows if row["decision"] == "merge"]
        kept = [row for row in rows if row["decision"] == "keep_article"]
        self.assertEqual(12, len(kept))
        self.assertEqual(1, len(merged))
        self.assertEqual("Q000006", merged[0]["query_id"])
        self.assertEqual("S1-ARTICLE-505521C7EF8C", merged[0]["merge_target"])

    def test_exact_url_overlap_oracle_is_stable(self) -> None:
        result_sets = {
            query_id: {item["url"] for item in read_result(query_id)["results"]}
            for query_id in EXPECTED_DESTINATIONS
        }
        overlaps: dict[tuple[str, str], int] = {}
        query_ids = list(EXPECTED_DESTINATIONS)
        for index, left in enumerate(query_ids):
            for right in query_ids[index + 1 :]:
                count = len(result_sets[left] & result_sets[right])
                if count:
                    overlaps[(left, right)] = count
        self.assertEqual(EXPECTED_OVERLAPS, overlaps)


if __name__ == "__main__":
    unittest.main()
