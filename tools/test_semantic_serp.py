import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.cli import main
from tools.seo_semantics.serp import (
    build_representative_queue,
    canonicalize_serp_url,
    cluster_semantics,
    complete_link_clusters,
    decide_cluster,
    overlap_count,
    route_special_owner,
    validate_serp_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = ROOT / "seo-data/2026-08-exp76-services/processed/keywords_clean.csv"
SCOPE = ROOT / "seo-data/2026-08-exp76-services/scope.json"
SERP_DIR = ROOT / "seo-data/2026-08-exp76-services/raw/serp"


class SemanticSerpTest(unittest.TestCase):
    def test_complete_link_does_not_chain_merge_incompatible_endpoints(self):
        clusters = complete_link_clusters(
            ("Q000003", "Q000001", "Q000002"),
            {
                "Q000001": "commercial_research",
                "Q000002": "commercial_research",
                "Q000003": "commercial_research",
            },
            {
                ("Q000001", "Q000002"): 5,
                ("Q000001", "Q000003"): 1,
                ("Q000002", "Q000003"): 4,
            },
        )

        self.assertEqual(clusters, (("Q000001", "Q000002"), ("Q000003",)))

    def test_complete_link_is_stable_and_never_merges_different_intents(self):
        overlaps = {
            ("Q000001", "Q000002"): 6,
            ("Q000001", "Q000003"): 6,
            ("Q000002", "Q000003"): 6,
        }
        intents = {
            "Q000001": "commercial_research",
            "Q000002": "commercial_research",
            "Q000003": "transactional",
        }

        forward = complete_link_clusters(("Q000001", "Q000002", "Q000003"), intents, overlaps)
        reverse = complete_link_clusters(("Q000003", "Q000002", "Q000001"), intents, overlaps)

        self.assertEqual(forward, (("Q000001", "Q000002"), ("Q000003",)))
        self.assertEqual(reverse, forward)

    def test_special_owner_routes_calculator_and_clicked_brand_navigation(self):
        calculator = route_special_owner(
            "калькулятор стоимости благоустройства участка",
            "transactional",
            "https://exp76.ru/services/landshaftnoe-proektirovanie/",
        )
        brand = route_special_owner(
            "эксперты рыбинск",
            "brand_navigation",
            "",
            clicked=True,
        )

        self.assertEqual(calculator.target_url, "https://exp76.ru/kalkuljator-uslug/")
        self.assertEqual(calculator.review_status, "reviewed")
        self.assertEqual(brand.target_url, "https://exp76.ru/")
        self.assertEqual(brand.review_status, "reviewed")

    def test_special_owner_excludes_only_reliable_external_noise_before_calculator(self):
        external = route_special_owner(
            "выровнять участок калькулятор стоимости tehno ники ru",
            "transactional",
            "https://exp76.ru/services/planirovka-territorii/",
        )
        false_brand = route_special_owner(
            "торговые центры эксперт 76 ru",
            "brand_navigation",
            "",
            clicked=True,
        )
        domain_noise = route_special_owner(
            "планировка участка ярославль подать заявку мини погрузчики ru",
            "commercial_research",
            "https://exp76.ru/services/planirovka-territorii/",
        )
        generic_method = route_special_owner(
            "планировка участка мини погрузчиком",
            "commercial_research",
            "https://exp76.ru/services/planirovka-territorii/",
        )
        techno_variants = (
            "выравнивание участка под заказ tehno niki",
            "выравнивание участка техноniki ru",
            "выравнивание участка ник ооо техно",
        )
        calculator_contaminants = (
            "калькулятор благоустройства geo услуги ru",
            "калькулятор благоустройства гео услуги",
            "калькулятор стоимости in garden",
            "планировка участка калькулятор ekskavatory arenda he",
            "стоимость благоустройства калькулятор эден крафт",
            "калькулятор благоустройства 84953246060",
            "калькулятор благоустройства новолесной переулок д 5",
        )

        self.assertEqual(external.url_action, "exclude")
        self.assertEqual(external.review_status, "reviewed")
        self.assertEqual(false_brand.url_action, "exclude")
        self.assertEqual(domain_noise.url_action, "exclude")
        self.assertTrue(
            all(
                route_special_owner(query, "commercial_research", "").url_action == "exclude"
                for query in techno_variants + calculator_contaminants
            )
        )
        self.assertIsNone(generic_method)

    def test_complete_corpus_accepts_ranked_duplicates_and_verticals_but_keeps_role_contract(self):
        queue, records = self._complete_corpus_fixture()
        records["Q000001"]["results"][1]["url"] = (
            records["Q000001"]["results"][0]["url"] + "?duplicate=1"
        )
        records["Q000001"]["results"][2]["url"] = "https://yandex.ru/images/search?text=test"

        roles = validate_serp_corpus(queue, records)

        self.assertEqual(len(roles.primary_query_ids), 131)
        self.assertEqual(len(roles.mobile_query_ids), 3)
        self.assertEqual(len(roles.brand_query_ids), 7)

    def test_complete_corpus_rejects_missing_qid_and_non_top_ten(self):
        queue, records = self._complete_corpus_fixture()
        del records["Q000141"]
        with self.assertRaisesRegex(ValueError, "QID coverage mismatch"):
            validate_serp_corpus(queue, records)

        _, records = self._complete_corpus_fixture()
        records["Q000001"]["results"].pop()
        with self.assertRaisesRegex(ValueError, "exact ranks 1-10"):
            validate_serp_corpus(queue, records)

    def test_real_complete_corpus_projects_every_candidate_once_with_safe_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            candidate_map_path = output / "candidate_cluster_map.csv"
            ambiguous_pairs_path = output / "serp_ambiguous_pairs.csv"

            summary = cluster_semantics(
                SCOPE,
                KEYWORDS,
                SERP_DIR,
                output / "serp_results.csv",
                output / "clusters.csv",
                output / "url_map.csv",
                candidate_map_path,
                ambiguous_pairs_path,
            )

            assignments = self._read_csv(candidate_map_path)
            ambiguous_pairs = self._read_csv(ambiguous_pairs_path)
            url_map = self._read_csv(output / "url_map.csv")
            self.assertEqual(summary.distinct_candidate_count, 4236)
            self.assertEqual(len(assignments), 4236)
            self.assertEqual(len({row["candidate_key"] for row in assignments}), 4236)
            same_service_pairs = [
                row for row in ambiguous_pairs if row["left_service_id"] == row["right_service_id"]
            ]
            cross_service_pairs = [
                row for row in ambiguous_pairs if row["left_service_id"] != row["right_service_id"]
            ]
            pending_manual_pairs = [
                row for row in ambiguous_pairs if row["decision"] == "manual_review"
            ]
            boundary_pairs = [
                row for row in ambiguous_pairs if row["decision"] == "owner_boundary_split"
            ]
            shared_special_pairs = [
                row for row in ambiguous_pairs if row["decision"] == "shared_special_owner"
            ]
            shared_exclusion_pairs = [
                row for row in ambiguous_pairs if row["decision"] == "shared_policy_exclusion"
            ]
            exclusion_split_pairs = [
                row for row in ambiguous_pairs if row["decision"] == "policy_exclusion_split"
            ]
            self.assertEqual(len(ambiguous_pairs), 1044)
            self.assertEqual(len(same_service_pairs), 290)
            self.assertEqual(len(cross_service_pairs), 754)
            self.assertEqual(len(pending_manual_pairs), 263)
            self.assertEqual(len(boundary_pairs), 747)
            self.assertEqual(len(shared_special_pairs), 5)
            self.assertEqual(len(shared_exclusion_pairs), 5)
            self.assertEqual(len(exclusion_split_pairs), 24)
            self.assertEqual({row["review_status"] for row in pending_manual_pairs}, {"pending"})
            self.assertEqual({row["review_status"] for row in boundary_pairs}, {"reviewed"})
            self.assertEqual({row["review_status"] for row in shared_special_pairs}, {"reviewed"})
            self.assertEqual({row["review_status"] for row in shared_exclusion_pairs}, {"reviewed"})
            self.assertEqual({row["review_status"] for row in exclusion_split_pairs}, {"reviewed"})
            self.assertEqual(
                {row["validation_status"] for row in boundary_pairs},
                {"cross_service_owner_boundary_reviewed"},
            )
            self.assertEqual(
                {row["validation_status"] for row in shared_special_pairs},
                {"shared_special_owner_reviewed"},
            )
            self.assertEqual(
                {row["validation_status"] for row in shared_exclusion_pairs},
                {"shared_policy_exclusion_reviewed"},
            )
            self.assertEqual(
                {row["validation_status"] for row in exclusion_split_pairs},
                {"policy_exclusion_split_reviewed"},
            )
            shared_pair_ids = {
                (row["left_query_id"], row["right_query_id"])
                for row in shared_special_pairs
            }
            self.assertEqual(
                shared_pair_ids,
                {
                    ("Q000012", "Q000026"),
                    ("Q000012", "Q000031"),
                    ("Q000012", "Q000070"),
                    ("Q000026", "Q000070"),
                    ("Q000031", "Q000070"),
                },
            )
            with (SERP_DIR / "serp-queue.csv").open("r", encoding="utf-8-sig", newline="") as handle:
                queue_by_id = {row["query_id"]: row for row in csv.DictReader(handle)}
            assignments_by_query = {
                (row["service_id"], row["query"], row["intent"]): row
                for row in assignments
            }
            for query_id in {item for pair in shared_pair_ids for item in pair}:
                queue_row = queue_by_id[query_id]
                assignment = assignments_by_query[
                    (queue_row["service_id"], queue_row["query"], queue_row["intent"])
                ]
                self.assertEqual(assignment["cluster_id"], "SPECIAL-CALCULATOR")
                self.assertEqual(assignment["target_url"], "https://exp76.ru/kalkuljator-uslug/")
            ambiguous_cluster_rows = [
                row for row in url_map if "serp_pair_pending_review" in row["validation_status"]
            ]
            self.assertEqual(len(ambiguous_cluster_rows), 67)
            self.assertEqual({row["review_status"] for row in ambiguous_cluster_rows}, {"pending"})
            self.assertNotIn("high", {row["confidence"] for row in ambiguous_cluster_rows})
            self.assertEqual({row["url_action"] for row in ambiguous_cluster_rows}, {"unresolved"})
            self.assertEqual({row["target_url"] for row in ambiguous_cluster_rows}, {""})
            self.assertTrue(
                all("serp_pair_pending_review" in row["validation_status"] for row in ambiguous_cluster_rows)
            )
            self.assertFalse(
                {"new_child_candidate", "redirect", "index", "city_page"}
                & {row["url_action"] for row in assignments}
            )
            calculators = [row for row in assignments if "калькулятор" in row["query"]]
            clean_calculators = [row for row in calculators if row["url_action"] != "exclude"]
            self.assertEqual(len(calculators), 34)
            self.assertEqual(len(clean_calculators), 23)
            self.assertEqual(
                {row["target_url"] for row in clean_calculators},
                {"https://exp76.ru/kalkuljator-uslug/"},
            )
            external = next(row for row in assignments if "tehno ники" in row["query"])
            self.assertEqual((external["url_action"], external["review_status"]), ("exclude", "reviewed"))
            generic_mini = next(
                row for row in assignments if row["query"] == "планировка участка мини погрузчиком"
            )
            self.assertEqual(generic_mini["target_url"], "")
            self.assertEqual(generic_mini["url_action"], "unresolved")
            direct_commercial = [
                row
                for row in assignments
                if row["assignment_method"] == "direct_serp_representative"
                and row["intent"] in {"transactional", "commercial_research"}
                and row["validation_status"] != "cross_service_owner_boundary_reviewed"
                and row["validation_status"] != "clicked_current_owner_reviewed"
            ]
            self.assertTrue(direct_commercial)
            self.assertEqual({row["url_action"] for row in direct_commercial}, {"unresolved"})
            self.assertEqual({row["target_url"] for row in direct_commercial}, {""})
            informational = [row for row in assignments if row["intent"] == "informational"]
            product_only = [row for row in assignments if row["intent"] == "product_only"]
            self.assertTrue(informational)
            self.assertTrue(product_only)
            self.assertEqual({row["url_action"] for row in informational}, {"article_candidate"})
            self.assertEqual({row["target_url"] for row in informational}, {""})
            self.assertEqual({row["review_status"] for row in informational}, {"pending"})
            self.assertEqual({row["url_action"] for row in product_only}, {"exclude"})
            self.assertEqual({row["target_url"] for row in product_only}, {""})
            self.assertEqual({row["review_status"] for row in product_only}, {"reviewed"})
            self.assertNotIn("owner_conflict", {row["url_action"] for row in assignments})

            with KEYWORDS.open("r", encoding="utf-8-sig", newline="") as handle:
                keyword_rows = list(csv.DictReader(handle))
            clicked_keys = {
                "|".join((row["service_id"], row["query_normalized"], row["intent"]))
                for row in keyword_rows
                if row["relevance"] == "relevant"
                and row["intent"] in {"transactional", "commercial_research", "informational", "product_only"}
                and float(row["clicks"] or 0) > 0
            }
            assignments_by_key = {row["candidate_key"]: row for row in assignments}
            self.assertTrue(clicked_keys)
            self.assertTrue(
                all(
                    assignments_by_key[key]["review_status"] == "reviewed"
                    or (
                        assignments_by_key[key]["url_action"] == "unresolved"
                        and assignments_by_key[key]["target_url"] == ""
                    )
                    for key in clicked_keys
                )
            )
            self.assertTrue(
                all(row["review_status"] != "reviewed" for row in assignments if "pending" in row["validation_status"])
            )
            inherited_boundary_reviews = [
                row
                for row in assignments
                if row["validation_status"] == "cross_service_owner_boundary_reviewed"
                and row["assignment_method"] != "direct_serp_representative"
            ]
            self.assertEqual(inherited_boundary_reviews, [])
            self.assertGreater(
                sum(row["review_status"] == "pending" for row in assignments),
                3000,
            )
            accepted_commercial = [
                row for row in url_map
                if row["intent"] in {"transactional", "commercial_research"}
                and row["url_action"] == "keep_enhance"
            ]
            self.assertTrue(accepted_commercial)
            self.assertTrue(all(row["target_url"] for row in accepted_commercial))
            self.assertTrue(all("|" not in row["service_id"] for row in accepted_commercial))
            calculator_owner = next(
                row for row in url_map if row["cluster_id"] == "SPECIAL-CALCULATOR"
            )
            self.assertEqual(calculator_owner["method"], "explicit_special_owner")
            self.assertIn("Q000012", calculator_owner["evidence"])
            frozen = [row for row in url_map if row["url_action"] == "frozen_owner"]
            self.assertEqual(len(frozen), 6)
            self.assertTrue(all(row["review_status"] == "reviewed" for row in frozen))

    def test_clustering_requires_the_frozen_collision_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed = root / "processed"
            processed.mkdir()
            copied_keywords = processed / "keywords_clean.csv"
            copied_keywords.write_bytes(KEYWORDS.read_bytes())
            candidate_map = processed / "candidate_cluster_map.csv"

            with self.assertRaisesRegex(ValueError, "frozen_collisions.csv"):
                cluster_semantics(
                    SCOPE,
                    copied_keywords,
                    SERP_DIR,
                    processed / "serp_results.csv",
                    processed / "clusters.csv",
                    processed / "url_map.csv",
                    candidate_map,
                )
            self.assertFalse(candidate_map.exists())

    def test_canonicalizes_protocol_www_query_and_fragment(self):
        self.assertEqual(
            canonicalize_serp_url("http://www.example.ru/path/?utm_source=x#part"),
            "https://example.ru/path/",
        )

    def test_canonicalization_collapses_slashes_and_rejects_non_http_urls(self):
        self.assertEqual(
            canonicalize_serp_url("HTTPS://WWW.Example.RU//a///b"),
            "https://example.ru/a/b/",
        )
        self.assertEqual(canonicalize_serp_url("https://example.ru"), "https://example.ru/")
        with self.assertRaisesRegex(ValueError, "HTTP"):
            canonicalize_serp_url("ftp://example.ru/file")

    def test_overlap_uses_unique_canonical_urls(self):
        left = [
            "https://a.ru/x",
            "https://a.ru/x?duplicate=1",
            "https://b.ru/y",
            "https://c.ru/z",
            "https://d.ru/q",
        ]
        right = [
            "http://www.a.ru/x/",
            "https://b.ru/y?x=1",
            "https://c.ru/z",
            "https://d.ru/q#x",
        ]
        self.assertEqual(overlap_count(left, right), 4)

    def test_cluster_thresholds_follow_the_spec(self):
        self.assertEqual(decide_cluster(4, True), "merge")
        self.assertEqual(decide_cluster(3, True), "manual_review")
        self.assertEqual(decide_cluster(1, True), "split")
        self.assertEqual(decide_cluster(5, False), "manual_review")
        with self.assertRaisesRegex(ValueError, "non-negative"):
            decide_cluster(-1, True)

    def test_queue_selects_group_representatives_and_retains_all_explicit_reasons(self):
        rows = [
            self._row("K000001", "ландшафтный дизайн участка", "S1", "seed a", broad="100"),
            self._row(
                "K000002",
                "ландшафтный дизайн участка",
                "S1",
                "seed a",
                broad="120",
                region="Ярославская область",
            ),
            self._row("K000003", "ландшафтный дизайн участка цена", "S1", "seed a", broad="30"),
            self._row("K000004", "ландшафтный дизайн участка под ключ", "S1", "seed a", broad="20"),
            self._row("K000005", "ландшафтный дизайн участка ярославль", "S1", "seed a", broad="10"),
            self._row("K000006", "ландшафтный проект для коттеджа", "S1", "seed a", clicks="2"),
            self._row(
                "K000007",
                "проект участка с водоемом",
                "S1",
                "seed a",
                final_decision="new_child_candidate",
            ),
            self._row("K000008", "невыбранный хвост seed a", "S1", "seed a", broad="1"),
            self._row("K000009", "проект благоустройства участка", "S1", "seed b", broad="90"),
        ]

        result = build_representative_queue(rows)

        self.assertEqual(result.eligible_row_count, 9)
        self.assertEqual(result.distinct_candidate_count, 8)
        self.assertEqual(result.tentative_group_count, 2)
        desktop = [row for row in result.rows if row.device == "desktop"]
        self.assertEqual(len(desktop), 7)
        self.assertNotIn("невыбранный хвост seed a", {row.query for row in desktop})
        self.assertEqual(len({(row.query, row.device) for row in result.rows}), len(result.rows))
        clicked = next(row for row in desktop if row.query == "ландшафтный проект для коттеджа")
        proposal = next(row for row in desktop if row.query == "проект участка с водоемом")
        self.assertIn("clicked", clicked.reason.split("|"))
        self.assertIn("new_page_proposal", proposal.reason.split("|"))

    def test_queue_coalesces_head_and_clicked_reasons_on_one_query(self):
        result = build_representative_queue(
            [self._row("K000001", "газон под ключ", "S2", "газон под ключ", broad="100", clicks="3")]
        )

        desktop = next(row for row in result.rows if row.device == "desktop")
        reasons = desktop.reason.split("|")
        self.assertIn("clicked", reasons)
        self.assertTrue(any(reason.startswith("commercial_head[") for reason in reasons))
        self.assertTrue(any(reason.startswith("turnkey_order[") for reason in reasons))

    def test_queue_adds_only_three_required_mobile_head_checks(self):
        rows = [
            self._row(f"K{index:06d}", f"head {service}", service, f"seed {service}", broad="10")
            for index, service in enumerate(("S1", "S2", "S5", "S8"), start=1)
        ]

        result = build_representative_queue(rows)

        mobile = [row for row in result.rows if row.device == "mobile"]
        self.assertEqual({row.service_id for row in mobile}, {"S2", "S5", "S8"})
        self.assertEqual({row.reason for row in mobile}, {"mobile_head_check"})

    def test_real_cleaned_input_has_frozen_candidate_gate_count(self):
        with KEYWORDS.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))

        result = build_representative_queue(rows)

        self.assertEqual(result.eligible_row_count, 6085)
        self.assertEqual(result.distinct_candidate_count, 4236)
        self.assertLess(len(result.rows), result.distinct_candidate_count)
        self.assertTrue(any("clicked" in row.reason.split("|") for row in result.rows))

    def test_serp_queue_cli_writes_exact_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "keywords.csv"
            output_path = root / "serp-queue.csv"
            rows = [self._row("K000001", "въезд через канаву", "S8", "въезд через канаву", broad="20")]
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            result = main(
                ["serp-queue", "--keywords", str(input_path), "--output", str(output_path)]
            )

            self.assertEqual(result, 0)
            with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                output_rows = list(reader)
            self.assertEqual(
                reader.fieldnames,
                ["query_id", "query", "service_id", "intent", "region", "device", "reason", "status"],
            )
            self.assertEqual({row["region"] for row in output_rows}, {"Yaroslavl"})
            self.assertEqual({row["status"] for row in output_rows}, {"pending"})
            self.assertNotIn(b"\r\n", output_path.read_bytes())

    def test_cluster_refuses_a_partial_serp_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed = root / "processed"
            serp_dir = root / "raw" / "serp"
            processed.mkdir(parents=True)
            serp_dir.mkdir(parents=True)
            keywords = processed / "keywords_clean.csv"
            rows = [
                self._row(
                    "K000001",
                    "ландшафтное проектирование участка",
                    "S1",
                    "ландшафтное проектирование участка",
                    broad="100",
                    clicks="2",
                ),
                self._row(
                    "K000002",
                    "ландшафтное проектирование участка ярославль",
                    "S1",
                    "ландшафтное проектирование участка",
                    broad="40",
                ),
                self._row("K000003", "газон под ключ", "S2", "газон под ключ", broad="80"),
            ]
            self._write_csv(keywords, rows)
            (processed / "frozen_collisions.csv").write_text("owner_url\n", encoding="utf-8")
            queue_rows = [
                {
                    "query_id": "Q000001", "query": rows[0]["query_normalized"],
                    "service_id": "S1", "intent": "commercial_research",
                    "region": "Yaroslavl", "device": "desktop", "reason": "commercial_head[S1-G01]",
                    "status": "pending",
                },
                {
                    "query_id": "Q000002", "query": rows[1]["query_normalized"],
                    "service_id": "S1", "intent": "commercial_research",
                    "region": "Yaroslavl", "device": "desktop", "reason": "yaroslavl_geo[S1-G01]",
                    "status": "pending",
                },
            ]
            self._write_csv(serp_dir / "serp-queue.csv", queue_rows)
            urls = [f"https://example{index}.ru/page" for index in range(1, 5)]
            records = [
                {
                    "query_id": queue_rows[index]["query_id"],
                    "query": queue_rows[index]["query"],
                    "region": "Yaroslavl", "device": "desktop",
                    "checked_at": "2026-08-20T12:00:00+03:00",
                    "results": [
                        {"rank": rank, "url": url, "title": f"Result {rank}"}
                        for rank, url in enumerate(urls, start=1)
                    ],
                }
                for index in range(2)
            ]
            (serp_dir / "sample.jsonl").write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Q000001-Q000141"):
                cluster_semantics(
                    ROOT / "seo-data/2026-08-exp76-services/scope.json",
                    keywords,
                    serp_dir,
                    processed / "serp_results.csv",
                    processed / "clusters.csv",
                    processed / "url_map.csv",
                )

    def test_cluster_cli_refuses_partial_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed = root / "processed"
            serp_dir = root / "raw" / "serp"
            processed.mkdir(parents=True)
            serp_dir.mkdir(parents=True)
            keywords = processed / "keywords_clean.csv"
            self._write_csv(
                keywords,
                [self._row("K000001", "въезд через канаву", "S8", "въезд через канаву", broad="20")],
            )
            (processed / "frozen_collisions.csv").write_text("owner_url\n", encoding="utf-8")
            self._write_csv(
                serp_dir / "serp-queue.csv",
                [{
                    "query_id": "Q000001", "query": "въезд через канаву", "service_id": "S8",
                    "intent": "commercial_research", "region": "Yaroslavl", "device": "desktop",
                    "reason": "commercial_head[S8-G01]", "status": "pending",
                }],
            )

            result = main(
                [
                    "cluster", "--scope", str(ROOT / "seo-data/2026-08-exp76-services/scope.json"),
                    "--keywords", str(keywords), "--serp-dir", str(serp_dir),
                    "--serp-output", str(processed / "serp_results.csv"),
                    "--clusters-output", str(processed / "clusters.csv"),
                    "--url-map-output", str(processed / "url_map.csv"),
                ]
            )

            self.assertEqual(result, 2)
            self.assertFalse((processed / "clusters.csv").exists())

    def test_cluster_cli_writes_the_explicit_candidate_map_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            candidate_map = output / "candidate_cluster_map.csv"

            result = main(
                [
                    "cluster", "--scope", str(SCOPE), "--keywords", str(KEYWORDS),
                    "--serp-dir", str(SERP_DIR),
                    "--serp-output", str(output / "serp_results.csv"),
                    "--clusters-output", str(output / "clusters.csv"),
                    "--url-map-output", str(output / "url_map.csv"),
                    "--candidate-map-output", str(candidate_map),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(len(self._read_csv(candidate_map)), 4236)

    @staticmethod
    def _complete_corpus_fixture():
        queue = []
        for index in range(1, 132):
            queue.append(
                {
                    "query_id": f"Q{index:06d}",
                    "query": f"primary query {index}",
                    "service_id": "S1",
                    "intent": "commercial_research",
                    "region": "Yaroslavl",
                    "device": "desktop",
                    "reason": "commercial_head[S1-G01]",
                    "status": "pending",
                }
            )
        for offset in range(3):
            queue.append(
                {
                    "query_id": f"Q{132 + offset:06d}",
                    "query": f"primary query {offset + 1}",
                    "service_id": "S1",
                    "intent": "commercial_research",
                    "region": "Yaroslavl",
                    "device": "mobile",
                    "reason": "mobile_head_check",
                    "status": "pending",
                }
            )
        for index in range(135, 142):
            queue.append(
                {
                    "query_id": f"Q{index:06d}",
                    "query": f"clicked brand {index}",
                    "service_id": "S1",
                    "intent": "brand_navigation",
                    "region": "Yaroslavl",
                    "device": "desktop",
                    "reason": "clicked",
                    "status": "pending",
                }
            )
        records = {
            row["query_id"]: {
                "query_id": row["query_id"],
                "query": row["query"],
                "region": row["region"],
                "device": row["device"],
                "results": [
                    {
                        "rank": rank,
                        "url": f"https://result-{row['query_id'].lower()}-{rank}.example/page",
                        "title": f"Result {rank}",
                    }
                    for rank in range(1, 11)
                ],
            }
            for row in queue
        }
        return queue, records

    @staticmethod
    def _row(
        keyword_id: str,
        query: str,
        service_id: str,
        seed: str,
        *,
        intent: str = "commercial_research",
        relevance: str = "relevant",
        broad: str = "",
        phrase: str = "",
        exact: str = "",
        impressions: str = "",
        clicks: str = "",
        region: str = "Ярославль",
        final_decision: str = "",
        review_reason: str = "",
    ) -> dict[str, str]:
        return {
            "keyword_id": keyword_id,
            "query_raw": query,
            "query_normalized": query,
            "service_id": service_id,
            "intent": intent,
            "relevance": relevance,
            "exclusion_reason": "",
            "geo": "",
            "entities": "",
            "frozen_collision": "false",
            "owner_url": "",
            "sources": "fixture",
            "seed": seed,
            "region": region,
            "device": "all",
            "broad_frequency": broad,
            "phrase_frequency": phrase,
            "exact_frequency": exact,
            "impressions": impressions,
            "clicks": clicks,
            "ctr": "",
            "avg_position": "",
            "current_url": "",
            "collected_at": "2026-08-20T12:00:00+03:00",
            "review_status": "reviewed" if clicks or final_decision else "",
            "final_decision": final_decision,
            "review_reason": review_reason,
        }

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
