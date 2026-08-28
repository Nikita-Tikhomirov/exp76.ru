"""Contracts for the final, publishable child-service architecture."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from tools.seo_semantics.expanded_architecture import EXPANDED_CHILDREN
from tools.seo_semantics.reviewed_service_architecture import (
    APPROVED_FINAL_IDS,
    BACKLOG_CHILDREN,
    CHILD_RULINGS,
    EXPECTED_CHILD_COUNTS,
    FINALIZATION_SERP_QUERIES,
    REUSE_DEPLOYMENT_REQUIREMENTS,
    REVIEWED_CHILDREN,
    SPARSE_HUB_JUSTIFICATIONS,
    URL_DECISIONS,
    all_reviewed_children,
    validate_child_rulings,
    validate_reviewed_child_architecture,
)


class ReviewedServiceArchitectureTests(unittest.TestCase):
    def test_hubs_have_five_children_except_three_evidence_based_floors(self) -> None:
        self.assertEqual(
            {service_id: len(pages) for service_id, pages in REVIEWED_CHILDREN.items()},
            {
                "S1": 5,
                "S2": 4,
                "S3": 5,
                "S4": 5,
                "S5": 6,
                "S6": 3,
                "S7": 5,
                "S8": 4,
            },
        )
        self.assertEqual(EXPECTED_CHILD_COUNTS, {
            service_id: len(pages)
            for service_id, pages in REVIEWED_CHILDREN.items()
        })
        self.assertEqual(37, len(all_reviewed_children()))
        self.assertEqual(APPROVED_FINAL_IDS, tuple(
            page.destination_id for page in all_reviewed_children()
        ))
        self.assertEqual({"S2", "S6", "S8"}, set(SPARSE_HUB_JUSTIFICATIONS))
        for service_id, justification in SPARSE_HUB_JUSTIFICATIONS.items():
            self.assertIn("Q", justification)
            self.assertGreaterEqual(len(justification), 80, service_id)

    def test_final_additions_are_real_offers_and_forced_candidates_are_absent(self) -> None:
        page_ids = {page.destination_id for page in all_reviewed_children()}
        self.assertTrue(
            {
                "S3-CHILD-HEDGE",
                "S4-CHILD-PEST",
                "S5-CHILD-CULTIVATION",
                "S5-CHILD-STUMPS",
                "S6-CHILD-WOOD",
                "S7-CHILD-HOLIDAY",
                "S8-CHILD-PARKING",
            }
            <= page_ids
        )
        self.assertTrue(
            {
                "S2-CHILD-INITIAL-CARE",
                "S3-CHILD-DECIDUOUS",
                "S4-CHILD-SEASONAL",
                "S4-CHILD-MAINTENANCE",
                "S5-CHILD-SOIL",
                "S5-CHILD-FOR-LAWN",
                "S5-CHILD-SOIL-REMOVAL",
                "S6-CHILD-SLOPE",
                "S6-CHILD-BLOCKS",
                "S6-CHILD-BRICK",
                "S7-CHILD-PATHS",
                "S7-CHILD-SECURITY",
                "S8-CHILD-BASE",
                "S8-CHILD-HEADWALLS",
                "S8-CHILD-SLABS",
            }.isdisjoint(page_ids)
        )

    def test_every_candidate_has_an_explicit_fail_closed_ruling(self) -> None:
        candidate_ids = {
            page.destination_id
            for pages in EXPANDED_CHILDREN.values()
            for page in pages
        }
        self.assertEqual(candidate_ids, set(CHILD_RULINGS))
        self.assertEqual([], validate_child_rulings(CHILD_RULINGS))

        incomplete = dict(CHILD_RULINGS)
        incomplete.pop("S1-CHILD-SKETCH")
        self.assertTrue(
            any("coverage" in error for error in validate_child_rulings(incomplete))
        )
        extra = dict(CHILD_RULINGS)
        extra["S9-CHILD-INVENTED"] = next(iter(CHILD_RULINGS.values()))
        self.assertTrue(any("unknown" in error for error in validate_child_rulings(extra)))

    def test_production_registry_contains_no_gated_or_pending_offer(self) -> None:
        self.assertEqual([], validate_reviewed_child_architecture())
        for page in all_reviewed_children():
            self.assertEqual("confirmed", page.offer_status, page.destination_id)
            self.assertTrue(page.business_evidence.startswith("business_source:"))
            self.assertNotIn("pending", page.semantic_evidence.casefold())
            self.assertNotIn("seed_gap:", page.semantic_evidence.casefold())

        masterplan = next(
            page
            for page in all_reviewed_children()
            if page.destination_id == "S1-CHILD-MASTERPLAN"
        )
        self.assertEqual(
            "генеральный план участка ландшафтный дизайн цена",
            masterplan.representative_query,
        )
        self.assertIn("Q000247", masterplan.semantic_evidence)
        self.assertIn("ГПЗУ", masterplan.boundary)
        self.assertIn("кадастров", masterplan.boundary.casefold())

        production_ids = {page.destination_id for page in all_reviewed_children()}
        self.assertTrue(set(BACKLOG_CHILDREN).isdisjoint(production_ids))
        self.assertTrue(
            {
                "S6-CHILD-GABIONS",
                "S8-CHILD-SLABS",
                "S8-CHILD-PIPE-PLASTIC",
                "S8-CHILD-PIPE-STEEL",
                "S8-CHILD-PIPE-RC",
            }
            <= set(BACKLOG_CHILDREN)
        )

    def test_protected_owner_detection_rejects_compound_queries_and_slugs(self) -> None:
        base = REVIEWED_CHILDREN["S1"][0]
        bad_slug = replace(base, slug="remont-livnevaya-kanalizatsiya")
        bad_query = replace(base, representative_query="ремонт ливневой канализации цена")
        bad_title = replace(base, title="Автоматический полив участка")
        bad_transliteration = replace(base, slug="ukladka-trotuarnoj-plitki")

        children = {key: tuple(value) for key, value in REVIEWED_CHILDREN.items()}
        children["S1"] = (bad_slug, *children["S1"][1:])
        self.assertTrue(
            any("protected" in error for error in validate_reviewed_child_architecture(children))
        )
        children["S1"] = (bad_query, *REVIEWED_CHILDREN["S1"][1:])
        self.assertTrue(
            any("protected" in error for error in validate_reviewed_child_architecture(children))
        )
        children["S1"] = (bad_title, *REVIEWED_CHILDREN["S1"][1:])
        self.assertTrue(
            any("protected" in error for error in validate_reviewed_child_architecture(children))
        )
        children["S1"] = (bad_transliteration, *REVIEWED_CHILDREN["S1"][1:])
        self.assertTrue(
            any("protected" in error for error in validate_reviewed_child_architecture(children))
        )

    def test_approved_inventory_and_page_records_are_immutable(self) -> None:
        children = {key: tuple(value) for key, value in REVIEWED_CHILDREN.items()}
        children["S1"] = children["S1"][1:]
        errors = validate_reviewed_child_architecture(children)
        self.assertTrue(any("approved child ids" in error for error in errors))
        self.assertTrue(any("approved child count" in error for error in errors))

        invented_source = replace(
            REVIEWED_CHILDREN["S1"][0],
            business_evidence="business_source:wp-rest/pages/999999#invented",
        )
        children = {key: tuple(value) for key, value in REVIEWED_CHILDREN.items()}
        children["S1"] = (invented_source, *children["S1"][1:])
        self.assertTrue(any(
            "approved page record" in error
            for error in validate_reviewed_child_architecture(children)
        ))
    def test_every_production_child_has_an_explicit_unique_url_decision(self) -> None:
        children = all_reviewed_children()
        self.assertEqual({page.destination_id for page in children}, set(URL_DECISIONS))
        self.assertEqual(
            len(children),
            len({decision.target_url for decision in URL_DECISIONS.values()}),
        )
        holiday = URL_DECISIONS["S7-CHILD-HOLIDAY"]
        self.assertEqual("reuse", holiday.url_action)
        self.assertEqual(10381, holiday.current_wp_id)
        self.assertEqual(holiday.current_url, holiday.target_url)
        self.assertTrue(
            holiday.target_url.endswith(
                "/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/"
            )
        )
        stumps = URL_DECISIONS["S5-CHILD-STUMPS"]
        self.assertEqual("reuse", stumps.url_action)
        self.assertEqual(6870, stumps.current_wp_id)
        self.assertEqual(stumps.current_url, stumps.target_url)
        self.assertEqual(
            "https://exp76.ru/services/vykorchevyvanie-pnejj-spil-derevev/",
            stumps.target_url,
        )
        self.assertEqual(
            {
                "current_post_type": "page",
                "target_template": "servicepost.php",
                "preserve_post_id": "6870",
                "preserve_permalink": stumps.target_url,
                "excluded_primary_intents": "обрезка|спил деревьев|фрезеровка пней",
            },
            REUSE_DEPLOYMENT_REQUIREMENTS["S5-CHILD-STUMPS"],
        )
        for destination_id, decision in URL_DECISIONS.items():
            if destination_id in {"S5-CHILD-STUMPS", "S7-CHILD-HOLIDAY"}:
                continue
            self.assertEqual("create", decision.url_action)
            self.assertEqual("", decision.current_url)
            self.assertIsNone(decision.current_wp_id)

        changed_holiday = dict(URL_DECISIONS)
        changed_holiday["S7-CHILD-HOLIDAY"] = replace(
            holiday,
            current_url="",
            target_url="https://exp76.ru/novogodnee-osveshhenie/",
            url_action="create",
            current_wp_id=None,
        )
        self.assertTrue(any(
            "frozen reuse owner" in error
            for error in validate_reviewed_child_architecture(
                url_decisions=changed_holiday
            )
        ))

    def test_stump_and_clearing_browser_serps_are_manifest_bound_and_commercial(self) -> None:
        raw_root = (
            Path(__file__).resolve().parents[1]
            / "seo-data"
            / "2026-08-exp76-services"
            / "raw"
        )
        corpora = (
            ("yandex-browser-serp", "yandex-browser-YB000001.json", "S5-CHILD-CLEARING", "расчист"),
            ("yandex-browser-serp-stump", "yandex-browser-YB000002.json", "S5-CHILD-STUMPS", "пн"),
        )
        for directory, filename, destination_id, intent_root in corpora:
            data_root = raw_root / directory
            manifest = json.loads(
                (data_root / "source-manifest.json").read_text(encoding="utf-8")
            )
            entries = {entry["path"]: entry for entry in manifest["files"]}
            self.assertEqual({"serp-queue.csv", filename}, set(entries))
            for relative, entry in entries.items():
                data = (data_root / relative).read_bytes()
                self.assertEqual(len(data), entry["byte_count"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

            payload = json.loads((data_root / filename).read_text(encoding="utf-8"))
            self.assertEqual(destination_id, payload["destination_id"])
            self.assertEqual("yandex_search_browser", payload["source"])
            self.assertEqual(list(range(1, 11)), [
                result["rank"] for result in payload["organic_results"]
            ])
            self.assertTrue(all(
                result["title"] and result["url"]
                for result in payload["organic_results"]
            ))
            self.assertTrue(all(
                intent_root in (result["title"] + result["snippet"]).casefold()
                for result in payload["organic_results"]
            ))

        foreign_owner = dict(URL_DECISIONS)
        first_id = next(key for key in foreign_owner if key != "S7-CHILD-HOLIDAY")
        foreign_owner[first_id] = replace(
            foreign_owner[first_id],
            current_url="https://exp76.ru/foreign/",
            target_url="https://exp76.ru/foreign/",
            url_action="reuse",
            current_wp_id=999999,
        )
        self.assertTrue(any(
            "frozen URL decision" in error
            for error in validate_reviewed_child_architecture(
                url_decisions=foreign_owner
            )
        ))

    def test_finalization_serp_queue_is_fully_resolved(self) -> None:
        self.assertEqual(
            [f"Q{number:06d}" for number in range(273, 281)],
            [probe.query_id for probe in FINALIZATION_SERP_QUERIES],
        )
        self.assertEqual(
            {
                "keep",
                "defer_business_confirmation",
                "keep_business_proven_low_frequency",
                "merge_to_generic_pipe",
            },
            {probe.decision for probe in FINALIZATION_SERP_QUERIES},
        )
        for probe in FINALIZATION_SERP_QUERIES:
            self.assertNotIn("pending", probe.rationale.casefold())
            self.assertTrue(
                probe.evidence_ref.endswith(
                    f"yandex-api-{probe.query_id}.jsonl|{probe.query_id}"
                )
            )


if __name__ == "__main__":
    unittest.main()
