import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.cli import main
from tools.seo_semantics.ingest import load_source_csv, merge_records
from tools.seo_semantics.manifest import register_source


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "seo-data/2026-08-exp76-services/scope.json"


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

    def test_reads_semicolon_delimited_wordstat_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wordstat.csv"
            path.write_text(
                "Запросы со словами;Число запросов;Топ запросов, период, регион\n"
                + "".join(f"газон, цена, вариант {index};1 234;\n" for index in range(20)),
                encoding="utf-8-sig",
            )

            records = load_source_csv(
                path,
                source="wordstat",
                column_map={"query": "Запросы со словами", "broad_frequency": "Число запросов"},
            )

            self.assertEqual(records[0].broad_frequency, 1234)

    def test_merge_preserves_region_device_and_url_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.csv"
            path.write_text(
                "query,region,device,url\n"
                "газон,Ярославль,all,https://exp76.ru/services/a/\n"
                "газон,Рыбинск,mobile,https://exp76.ru/services/b/\n",
                encoding="utf-8",
            )
            records = load_source_csv(
                path,
                source="wordstat",
                column_map={
                    "query": "query",
                    "region": "region",
                    "device": "device",
                    "current_url": "url",
                },
            )

            merged = merge_records(records)

            self.assertEqual(len(merged), 2)

    def test_merge_preserves_disjoint_metrics_from_different_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wordstat = root / "wordstat.csv"
            webmaster = root / "webmaster.csv"
            wordstat.write_text("query,frequency\nгазон,40\n", encoding="utf-8")
            webmaster.write_text("query,shows\nгазон,12\n", encoding="utf-8")
            records = load_source_csv(
                wordstat,
                "wordstat",
                {"query": "query", "broad_frequency": "frequency"},
            )
            records.extend(
                load_source_csv(
                    webmaster,
                    "webmaster",
                    {"query": "query", "impressions": "shows"},
                )
            )

            merged = merge_records(records)

            self.assertEqual(merged[0].broad_frequency, 40)
            self.assertEqual(merged[0].impressions, 12)

    def test_cli_ingest_reads_registered_sources_and_writes_stable_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            wordstat_dir = raw / "wordstat"
            webmaster_dir = raw / "webmaster"
            wordstat_dir.mkdir(parents=True)
            webmaster_dir.mkdir(parents=True)

            wordstat_file = wordstat_dir / "top-001.csv"
            wordstat_file.write_text(
                "Запросы со словами;Число запросов;Описание\n"
                "газон под ключ;15;\n",
                encoding="utf-8-sig",
            )
            coverage = wordstat_dir / "coverage.csv"
            with coverage.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "service_id", "seed", "query_expr", "region", "kind", "status",
                        "row_hint", "download_seq", "raw_file", "source_url",
                        "collected_at", "error",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "service_id": "S2",
                        "seed": "газон под ключ",
                        "query_expr": "газон под ключ",
                        "region": "Ярославль",
                        "kind": "broad",
                        "status": "exported",
                        "raw_file": "top-001.csv",
                        "source_url": "https://wordstat.yandex.ru/?region=16",
                        "collected_at": "2026-08-20T12:00:00+03:00",
                    }
                )
            webmaster_file = webmaster_dir / "site.csv"
            webmaster_file.write_text(
                '"Query","Dates range","Impressions","Clicks","CTR %","Avg. position"\n'
                '"планировка участка","2026-07-20 - 2026-08-18","20.00","2.00","10.00","4.50"\n',
                encoding="utf-8",
            )

            manifest = raw / "source-manifest.json"
            for path, source in (
                (wordstat_file, "wordstat"),
                (coverage, "wordstat"),
                (webmaster_file, "webmaster"),
            ):
                register_source(path, source, "2026-08-20T12:00:00+03:00", manifest)
            output = root / "processed" / "keywords_raw.csv"

            result = main(
                [
                    "ingest",
                    "--scope", str(SCOPE),
                    "--manifest", str(manifest),
                    "--output", str(output),
                ]
            )

            self.assertEqual(result, 0)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                list(rows[0]),
                [
                    "keyword_id", "query_raw", "query_normalized", "sources", "seed",
                    "region", "device", "broad_frequency", "phrase_frequency",
                    "exact_frequency", "impressions", "clicks", "ctr", "avg_position",
                    "current_url", "collected_at",
                ],
            )
            self.assertEqual([row["keyword_id"] for row in rows], ["K000001", "K000002"])
            wordstat_row = next(row for row in rows if row["query_normalized"] == "газон под ключ")
            self.assertEqual(wordstat_row["region"], "Ярославль")
            self.assertEqual(wordstat_row["broad_frequency"], "15")
            self.assertEqual(wordstat_row["seed"], "газон под ключ")
