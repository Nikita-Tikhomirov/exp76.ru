import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.ingest import load_source_csv, merge_records


class SemanticIngestTest(unittest.TestCase):
    def test_preserves_raw_query_and_source_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "webmaster.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["query", "shows", "clicks", "url"])
                writer.writeheader()
                writer.writerow(
                    {
                        "query": "Въезд через канаву",
                        "shows": "60",
                        "clicks": "12",
                        "url": "https://exp76.ru/services/x/",
                    }
                )

            records = load_source_csv(
                path,
                source="webmaster",
                column_map={
                    "query": "query",
                    "impressions": "shows",
                    "clicks": "clicks",
                    "current_url": "url",
                },
            )

            self.assertEqual(records[0].query_raw, "Въезд через канаву")
            self.assertEqual(records[0].impressions, 60)
            self.assertEqual(records[0].clicks, 12)
            self.assertEqual(records[0].source, "webmaster")

    def test_merge_keeps_one_normalized_row_and_all_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = []
            for index, (source, query) in enumerate(
                (("webmaster", "Газон под ключ"), ("wordstat", "газон  под ключ")),
                start=1,
            ):
                path = Path(tmp) / f"source-{index}.csv"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["query"])
                    writer.writeheader()
                    writer.writerow({"query": query})
                records.extend(load_source_csv(path, source=source, column_map={"query": "query"}))

            merged = merge_records(records)

            self.assertEqual(len(merged), 1)
            self.assertEqual(merged[0].sources, ("webmaster", "wordstat"))

    def test_rejects_negative_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wordstat.csv"
            path.write_text("query,frequency\nгазон,-1\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "wordstat.csv.*broad_frequency"):
                load_source_csv(
                    path,
                    source="wordstat",
                    column_map={"query": "query", "broad_frequency": "frequency"},
                )

    def test_missing_query_column_names_file_and_expected_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.csv"
            path.write_text("phrase\nгазон\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "source.csv.*query"):
                load_source_csv(path, source="wordstat", column_map={"query": "query"})

    def test_merge_does_not_sum_metrics_from_different_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = []
            for source, frequency in (("wordstat", "50"), ("planner", "70")):
                path = Path(tmp) / f"{source}.csv"
                path.write_text(f"query,frequency\nгазон,{frequency}\n", encoding="utf-8")
                records.extend(
                    load_source_csv(
                        path,
                        source=source,
                        column_map={"query": "query", "broad_frequency": "frequency"},
                    )
                )

            merged = merge_records(records)

            self.assertEqual(len(merged), 1)
            self.assertIsNone(merged[0].broad_frequency)
