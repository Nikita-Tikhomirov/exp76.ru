import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.classify import (
    classify_query,
    infer_primary_service_id,
    infer_service_id,
    load_seed_owners,
)
from tools.seo_semantics.cli import main
from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "seo-data/2026-08-exp76-services/scope.json"
SEEDS_PATH = ROOT / "seo-data/2026-08-exp76-services/seeds.json"
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

    def test_bare_work_token_is_not_employment_or_minus_evidence(self):
        queries = (
            ("благоустройство участка плиткой стоимость работа плюс материалы", "S1"),
            ("планировка участки цена работа", "S5"),
            ("рыбинск сколько стоит работа выложить тротуарную плитку", ""),
            ("сколько стоит работа по монтажу дренажной и ливневой системы", ""),
        )

        for query, service_hint in queries:
            with self.subTest(query=query):
                result = classify_query(query, service_hint, SCOPE)
                self.assertNotEqual(result.exclusion_reason, "jobs")

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

    def test_routes_observed_frozen_inflections_as_complete_tokens(self):
        examples = (
            ("организация занимается дренажными работами", "drenazh-uchastka"),
            ("водоотводы ливневые вокруг дома", "livnevaya-kanalizatsiya"),
            ("на новой отмостке появились трещины", "otmostka-vokrug-doma"),
            ("организация занимается ливневкой", "livnevaya-kanalizatsiya"),
            ("сделать ливневку вокруг дома", "livnevaya-kanalizatsiya"),
            ("схема ливневых колодцев", "livnevaya-kanalizatsiya"),
            ("осушение заболоченных территорий", "osushenie-uchastka"),
        )

        for query, owner_slug in examples:
            with self.subTest(query=query):
                result = classify_query(query, "", SCOPE)
                self.assertTrue(result.frozen_collision)
                self.assertIn(f"/category/{owner_slug}/", result.owner_url)

    def test_routes_morphological_frozen_collision_with_seeded_service(self):
        s8 = classify_query("заезд на участок где есть канава с ливневкой", "S8", SCOPE)
        s3 = classify_query("посадка деревьев на заболоченных почвах", "S3", SCOPE)

        self.assertEqual((s8.service_id, s8.relevance), ("S8", "manual_review"))
        self.assertTrue(s8.owner_url.endswith("/category/livnevaya-kanalizatsiya/"))
        self.assertEqual((s3.service_id, s3.relevance), ("S3", "manual_review"))
        self.assertTrue(s3.owner_url.endswith("/category/osushenie-uchastka/"))

    def test_routes_observed_water_ditch_forms_to_drainage_owner(self):
        examples = (
            "обустройство водоотводной канавы и въезда на участок ярославль",
            "ремонт водоотводной канавы",
            "устройство водоотводной канавы",
            "прочистка водоотводных канав",
        )

        for query in examples:
            with self.subTest(query=query):
                result = classify_query(query, "S8" if "въезда" in query else "", SCOPE)
                self.assertTrue(result.frozen_collision)
                self.assertTrue(result.owner_url.endswith("/category/drenazh-uchastka/"))
        mixed = classify_query(examples[0], "S8", SCOPE)
        self.assertEqual((mixed.service_id, mixed.relevance), ("S8", "manual_review"))

    def test_infers_reviewed_service_phrases(self):
        self.assertEqual(infer_service_id("благоустройство в рыбинске"), "S1")
        self.assertEqual(infer_service_id("найти садовника на участок"), "S4")
        self.assertEqual(infer_service_id("сделать въезд в канаву"), "S8")

    def test_infers_owner_from_earliest_explicit_service_phrase(self):
        self.assertEqual(infer_primary_service_id("ландшафтный дизайн планировка участка"), "S1")

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

    def test_loads_every_approved_seed_owner_from_configuration(self):
        payload = json.loads(SEEDS_PATH.read_text(encoding="utf-8"))
        owners = load_seed_owners(SEEDS_PATH)

        self.assertEqual(sum(len(seeds) for seeds in payload.values()), len(owners))
        for service_id, seeds in payload.items():
            for seed in seeds:
                with self.subTest(seed=seed):
                    self.assertEqual(owners[seed], service_id)
                    result = classify_query(seed, owners[seed], SCOPE)
                    self.assertEqual(result.service_id, service_id)
                    self.assertEqual(result.relevance, "relevant")

    def test_source_hint_requires_query_evidence_and_excludes_wrong_senses(self):
        legal = classify_query("градостроительный кодекс планировка территории", "S5", SCOPE)
        municipal = classify_query("1 проект планировки территории", "S5", SCOPE)
        arbitrary = classify_query("купить трактор", "S5", SCOPE)
        generic_project = classify_query("проектные работы арефино", "S1", SCOPE)
        grading = classify_query("планировка участка с уклоном", "S5", SCOPE)
        grading_inflected = classify_query("аренда трактора для планировки участка", "S5", SCOPE)
        site_zoning = classify_query("планировка участка зонирование", "S5", SCOPE)
        municipal_zoning = classify_query(
            "территориальное планирование зонирование планировка территории", "S5", SCOPE
        )
        disputed = classify_query("корчевание деревьев ярославль", "S4", SCOPE)

        legal_forms = (
            "планировка территории градостроительные планы земельного участка",
            "планировка территории градостроительства",
            "сбцп планировка территории",
            "планировка участка по кадастровому номеру",
        )

        self.assertEqual((legal.relevance, legal.exclusion_reason), ("excluded", "legal_municipal_planning"))
        self.assertEqual((municipal.relevance, municipal.exclusion_reason), ("excluded", "legal_municipal_planning"))
        self.assertEqual((arbitrary.relevance, arbitrary.exclusion_reason), ("excluded", "out_of_scope"))
        self.assertEqual(
            (generic_project.relevance, generic_project.exclusion_reason),
            ("excluded", "out_of_scope"),
        )
        self.assertEqual(grading.relevance, "relevant")
        self.assertEqual(grading_inflected.relevance, "relevant")
        self.assertEqual(site_zoning.relevance, "relevant")
        self.assertEqual(
            (municipal_zoning.relevance, municipal_zoning.exclusion_reason),
            ("excluded", "legal_municipal_planning"),
        )
        self.assertEqual((disputed.relevance, disputed.exclusion_reason), ("excluded", "out_of_scope"))
        for query in legal_forms:
            with self.subTest(query=query):
                result = classify_query(query, "S5", SCOPE)
                self.assertEqual(
                    (result.relevance, result.exclusion_reason),
                    ("excluded", "legal_municipal_planning"),
                )

    def test_generated_output_closes_round_two_and_has_single_eligible_owner(self):
        clean = self._read_csv(
            ROOT / "seo-data/2026-08-exp76-services/processed/keywords_clean.csv"
        )
        frozen = self._read_csv(
            ROOT / "seo-data/2026-08-exp76-services/processed/frozen_collisions.csv"
        )
        rows = clean + frozen
        by_id = {row["keyword_id"]: row for row in rows}

        mixed = by_id["K003172"]
        self.assertEqual((mixed["service_id"], mixed["relevance"]), ("S8", "manual_review"))
        self.assertTrue(mixed["owner_url"].endswith("/category/drenazh-uchastka/"))
        self.assertEqual((mixed["review_status"], mixed["final_decision"]), ("reviewed", "frozen_owner"))

        for keyword_id in ("K003929", "K003930", "K003931", "K003932", "K003933", "K004546", "K006385"):
            with self.subTest(keyword_id=keyword_id):
                row = by_id[keyword_id]
                self.assertEqual(
                    (row["relevance"], row["exclusion_reason"]),
                    ("excluded", "legal_municipal_planning"),
                )

        canonical_rows = [by_id[keyword_id] for keyword_id in ("K002235", "K002236", "K002237")]
        self.assertEqual({row["service_id"] for row in canonical_rows}, {"S1"})
        self.assertEqual({row["review_status"] for row in canonical_rows}, {"reviewed"})
        self.assertEqual({row["final_decision"] for row in canonical_rows}, {"canonical_service_owner"})
        self.assertEqual({row["review_reason"] for row in canonical_rows}, {"earliest_service_phrase:S1"})

        eligible = [
            row
            for row in clean
            if row["relevance"] == "relevant"
            and row["intent"] in {"transactional", "commercial_research", "informational", "product_only"}
        ]
        owners_by_query: dict[str, set[str]] = {}
        for row in eligible:
            owners_by_query.setdefault(row["query_normalized"], set()).add(row["service_id"])
        conflicts = {query: owners for query, owners in owners_by_query.items() if len(owners) > 1}
        self.assertEqual(conflicts, {})

    def test_excludes_reviewed_noisy_frozen_token_contexts(self):
        queries = (
            "грузоперевозки капельный полив углич",
            "автополив он ярославль автосалон",
            "отвод дренажной воды от действующих градирен в систему канализации ярославль",
            "цены на заболоченный участок в ярославле",
        )

        for query in queries:
            with self.subTest(query=query):
                result = classify_query(query, "", SCOPE)
                self.assertFalse(result.frozen_collision)
                self.assertEqual((result.relevance, result.exclusion_reason), ("excluded", "out_of_scope"))

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
                self._raw_row("K000006", "авито навес арочный", "", clicks="1"),
                self._raw_row("K000007", "градостроительный кодекс планировка территории", "планировка территории"),
                self._raw_row("K000008", "монтаж освещения участка рыбинск", "монтаж освещения участка"),
                self._raw_row("K000009", "обустройство въезда на участок углич", "обустройство въезда на участок"),
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
            self.assertEqual(sorted(all_ids), [f"K{index:06d}" for index in range(1, 10)])
            self.assertEqual(len(all_ids), len(set(all_ids)))
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000001")["service_id"], "S8")
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000002")["exclusion_reason"], "jobs")
            mixed = next(row for row in frozen if row["keyword_id"] == "K000004")
            self.assertEqual(mixed["relevance"], "manual_review")
            self.assertTrue(mixed["owner_url"].endswith("/category/drenazh-uchastka/"))
            clicked_exclusion = next(row for row in clean if row["keyword_id"] == "K000006")
            self.assertEqual(clicked_exclusion["service_id"], "")
            self.assertEqual(clicked_exclusion["review_status"], "reviewed")
            self.assertEqual(clicked_exclusion["final_decision"], "exclude")
            self.assertEqual(clicked_exclusion["review_reason"], "clicked_out_of_scope")
            legal = next(row for row in clean if row["keyword_id"] == "K000007")
            self.assertEqual((legal["relevance"], legal["exclusion_reason"]), ("excluded", "legal_municipal_planning"))
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000008")["service_id"], "S7")
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000009")["service_id"], "S8")
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000008")["relevance"], "relevant")
            self.assertEqual(next(row for row in clean if row["keyword_id"] == "K000009")["relevance"], "relevant")
            self.assertEqual(clicked_exclusion["seed"], "")
            self.assertEqual(clicked_exclusion["ctr"], "25.0")
            self.assertEqual(clicked_exclusion["collected_at"], "2026-08-20T12:00:00+03:00")
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
            "ctr": "25.0",
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
