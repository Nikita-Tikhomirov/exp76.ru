import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.classify import classify_query, infer_service_id
from tools.seo_semantics.cli import main
from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "seo-data/2026-08-exp76-services/scope.json"
SCOPE = load_scope(SCOPE_PATH)


class SemanticClassifyTest(unittest.TestCase):
    def test_assigns_commercial_service_query(self):
        result = classify_query("въезд через канаву под ключ ярославль", "S8", SCOPE)

        self.assertEqual(result.intent, "transactional")
        self.assertEqual(result.service_id, "S8")
        self.assertFalse(result.frozen_collision)

    def test_protects_existing_autopoliv_cluster(self):
        result = classify_query("монтаж автополива газона", "S2", SCOPE)

        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.owner_url, "https://exp76.ru/category/avtopoliv-na-uchastke/")

    def test_protects_existing_livnevka_cluster(self):
        result = classify_query("ливневка под въездом на участок", "S8", SCOPE)

        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.owner_url, "https://exp76.ru/category/livnevaya-kanalizatsiya/")

    def test_frozen_owner_is_not_mislabeled_irrelevant(self):
        result = classify_query("дренаж участка", "", SCOPE)

        self.assertEqual(result.intent, "commercial_research")
        self.assertEqual(result.relevance, "frozen_collision")

    def test_marks_jobs_as_irrelevant(self):
        result = classify_query("работа садовником вакансии", "S4", SCOPE)

        self.assertEqual(result.intent, "irrelevant")
        self.assertEqual(result.exclusion_reason, "jobs")

    def test_preserves_mixed_service_and_frozen_query_for_review(self):
        result = classify_query("планировка участка с уклоном и дренажом", "S5", SCOPE)

        self.assertEqual(result.service_id, "S5")
        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.relevance, "manual_review")
        self.assertEqual(result.owner_url, "https://exp76.ru/category/drenazh-uchastka/")

    def test_uses_tokens_instead_of_substring_matches(self):
        result = classify_query("подработка с автополивочной системой", "S2", SCOPE)

        self.assertNotEqual(result.exclusion_reason, "jobs")
        self.assertFalse(result.frozen_collision)

    def test_frozen_priority_is_explicit_for_multi_owner_query(self):
        result = classify_query("ливневая канализация и дренаж участка", "", SCOPE)

        self.assertEqual(result.owner_url, "https://exp76.ru/category/livnevaya-kanalizatsiya/")

    def test_first_explicit_frozen_phrase_wins_across_multiple_owners(self):
        result = classify_query("осушение участка с высоким уровнем грунтовых вод", "", SCOPE)

        self.assertEqual(result.owner_url, "https://exp76.ru/category/osushenie-uchastka/")

    def test_covers_reviewed_inflections_without_substring_matching(self):
        result = classify_query("калькуляция стоимости по дренажным работам", "", SCOPE)

        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.owner_url, "https://exp76.ru/category/drenazh-uchastka/")

    def test_infers_reviewed_service_phrases(self):
        self.assertEqual(infer_service_id("благоустройство в рыбинске"), "S1")
        self.assertEqual(infer_service_id("найти садовника на участок"), "S4")
        self.assertEqual(infer_service_id("сделать въезд в канаву"), "S8")

    def test_routes_contextual_outdoor_tile_but_not_indoor_tile(self):
        outdoor = classify_query("переложить старую плитку на дорожке", "", SCOPE)
        indoor = classify_query("керамическая плитка для ванной", "", SCOPE)

        self.assertTrue(outdoor.frozen_collision)
        self.assertEqual(outdoor.owner_url, "https://exp76.ru/category/ukladka-trotuarnoy-plitki/")
        self.assertFalse(indoor.frozen_collision)

    def test_infers_inflected_broad_landscaping_term(self):
        self.assertEqual(infer_service_id("стоимость работ по благоустройству"), "S1")

    def test_routes_reviewed_brand_and_garden_phrases(self):
        brand = classify_query("эксперты рыбинск", "", SCOPE)

        self.assertEqual(brand.service_id, "S1")
        self.assertEqual(brand.intent, "brand_navigation")
        self.assertEqual(infer_service_id("калькулятор работ садовых"), "S4")

    def test_cli_partitions_every_row_once_and_requires_repeat_minus_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "keywords_raw.csv"
            clean_path = root / "keywords_clean.csv"
            frozen_path = root / "frozen_collisions.csv"
            minus_path = root / "minus_words.csv"
            fieldnames = [
                "keyword_id", "query_raw", "query_normalized", "sources", "seed",
                "region", "device", "broad_frequency", "phrase_frequency",
                "exact_frequency", "impressions", "clicks", "ctr", "avg_position",
                "current_url", "collected_at",
            ]
            rows = [
                self._raw_row("K000001", "въезд через канаву под ключ", "въезд на участок", clicks="1"),
                self._raw_row("K000002", "работа садовником вакансии", "уход за садом"),
                self._raw_row("K000003", "вакансии садовника", "садовник на участок"),
                self._raw_row("K000004", "планировка участка с дренажом", "планировка участка"),
                self._raw_row("K000005", "курс по уходу за садом", "уход за садом"),
            ]
            with raw_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = main(
                [
                    "classify", "--scope", str(SCOPE_PATH), "--input", str(raw_path),
                    "--output", str(clean_path), "--frozen-output", str(frozen_path),
                    "--minus-output", str(minus_path),
                ]
            )

            self.assertEqual(result, 0)
            clean = self._read_csv(clean_path)
            frozen = self._read_csv(frozen_path)
            all_ids = [row["keyword_id"] for row in clean + frozen]
            self.assertEqual(sorted(all_ids), [f"K{index:06d}" for index in range(1, 6)])
            self.assertEqual(len(all_ids), len(set(all_ids)))
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000001")["service_id"], "S8")
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000002")["exclusion_reason"], "jobs")
            mixed = next(row for row in frozen if row["keyword_id"] == "K000004")
            self.assertEqual(mixed["relevance"], "manual_review")
            self.assertTrue(mixed["owner_url"].endswith("/category/drenazh-uchastka/"))
            minus = self._read_csv(minus_path)
            self.assertEqual(
                [(row["scope"], row["word"], row["reason"]) for row in minus],
                [("global", "вакансия", "jobs")],
            )
            self.assertEqual(minus[0]["source_query_ids"], "K000002|K000003")
            self.assertNotIn("курс", {row["word"] for row in minus})

    @staticmethod
    def _raw_row(keyword_id: str, query: str, seed: str, clicks: str = "") -> dict[str, str]:
        return {
            "keyword_id": keyword_id,
            "query_raw": query,
            "query_normalized": query,
            "sources": "fixture",
            "seed": seed,
            "region": "Ярославль",
            "device": "all",
            "broad_frequency": "",
            "phrase_frequency": "",
            "exact_frequency": "",
            "impressions": clicks,
            "clicks": clicks,
            "ctr": "",
            "avg_position": "",
            "current_url": "",
            "collected_at": "2026-08-20T12:00:00+03:00",
        }

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
