"""Regression tests for reviewed semantic page decisions."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import replace
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.seo_semantics.architecture import (
    ArchitectureBuild,
    ArchitectureError,
    PageDestination,
    PairReview,
    build_pair_review_queue,
    resolve_url_architecture,
    resolve_pair_action,
    validate_architecture,
    validate_pair_architecture_alignment,
    validate_pair_review_coverage,
    validate_pair_review_consistency,
)
from tools.seo_semantics.scope import load_scope
from tools.seo_semantics import production_architecture


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "seo-data/2026-08-exp76-services"
PROCESSED = DATA / "processed"
REVIEWS = DATA / "reviews"
SCOPE = load_scope(DATA / "scope.json")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class SemanticArchitectureTests(unittest.TestCase):
    def _decision(self, cluster_id: str, *, action: str, **overrides: str):
        values = {
            "cluster_id": cluster_id,
            "service_id": "S1",
            "destination_id": "S1-HUB",
            "page_role": "hub",
            "parent_destination_id": "",
            "current_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
            "proposed_url": "",
            "proposed_slug": "landshaftnoe-proektirovanie",
            "url_action": action,
            "publication_status": "ready",
            "business_offer_confirmed": "true",
            "evidence_refs": "SERP-1",
            "review_status": "approved",
            "reviewer": "reviewer",
            "rationale": "approved page decision",
        }
        values.update(overrides)
        from tools.seo_semantics.architecture import ClusterPageDecision

        return ClusterPageDecision(**values)

    def _build(self, clusters, decisions):
        return resolve_url_architecture(SCOPE, clusters, (), (), {}, decisions)

    def test_pending_pair_cannot_become_keep_enhance(self):
        """A pending pair must not preserve a URL owner by default."""
        pair = PairReview(
            pair_id="PAIR-1",
            decision="manual_review",
            owner_action="hold_current_url",
            review_status="pending",
            reviewer="",
            rationale="",
        )

        with self.assertRaisesRegex(ArchitectureError, "PAIR-1 remains pending"):
            resolve_pair_action(pair)

    def test_review_queue_contains_only_manual_review_pairs(self):
        """Policy evidence stays immutable and outside the human-review overlay."""
        queue = build_pair_review_queue(
            [
                {
                    "pair_id": "PAIR-MANUAL",
                    "decision": "manual_review",
                    "owner_action": "hold_current_url",
                    "review_status": "pending",
                    "left_query": "one",
                    "right_query": "two",
                    "overlap": "2",
                    "shared_urls": "https://example.test/",
                },
                {
                    "pair_id": "PAIR-BOUNDARY",
                    "decision": "owner_boundary_split",
                    "owner_action": "hold_distinct_service_owners",
                    "review_status": "reviewed",
                    "reviewer": "policy_scope_owner",
                    "rationale": "approved service boundary",
                    "shared_urls": "https://example.test/",
                }
            ]
        )

        self.assertEqual([row["pair_id"] for row in queue], ["PAIR-MANUAL"])

    def test_pair_review_coverage_uses_only_manual_evidence_rows(self):
        """Reviewed policy rows must neither be copied nor reported as missing."""
        ambiguous = [
            {"pair_id": "PAIR-MANUAL", "decision": "manual_review"},
            {"pair_id": "PAIR-POLICY", "decision": "owner_boundary_split"},
        ]
        reviews = {
            "PAIR-MANUAL": PairReview(
                pair_id="PAIR-MANUAL",
                decision="same_destination",
                review_status="reviewed",
                reviewer="reviewer",
                rationale="overlap=2/10; observed formats are service pages",
                evidence_note="overlap=2/10; observed formats are service pages",
            )
        }

        self.assertEqual(validate_pair_review_coverage(ambiguous, reviews), [])

    def test_pair_decision_enum_is_fail_closed(self):
        """A final-looking row with an unknown decision cannot enter the overlay."""
        pair = PairReview(
            pair_id="PAIR-1",
            decision="probably_same",
            review_status="reviewed",
            reviewer="reviewer",
            rationale="overlap=3/10; formats=service_landing",
            evidence_note="overlap=3/10; formats=service_landing",
        )

        with self.assertRaisesRegex(ArchitectureError, "invalid decision"):
            resolve_pair_action(pair)

    def test_transitive_pair_contradiction_is_rejected(self):
        """A separate edge cannot split a same-destination connected component."""
        ambiguous = [
            {"pair_id": "PAIR-AB", "decision": "manual_review", "left_query_id": "A", "right_query_id": "B"},
            {"pair_id": "PAIR-BC", "decision": "manual_review", "left_query_id": "B", "right_query_id": "C"},
            {"pair_id": "PAIR-AC", "decision": "manual_review", "left_query_id": "A", "right_query_id": "C"},
        ]
        reviews = {
            pair_id: PairReview(pair_id, decision, "reviewed", "reviewer", "reviewed", "observed")
            for pair_id, decision in (
                ("PAIR-AB", "same_destination"),
                ("PAIR-BC", "same_destination"),
                ("PAIR-AC", "separate_destinations"),
            )
        }

        self.assertEqual(
            validate_pair_review_consistency(ambiguous, reviews),
            ["PAIR-AC separates one same-destination component"],
        )

    def test_pair_decisions_constrain_final_cluster_owners(self):
        """Pair review outcomes and cluster-page destination IDs cannot drift."""
        ambiguous = [
            {
                "pair_id": "PAIR-1",
                "decision": "manual_review",
                "left_query": "left",
                "right_query": "right",
                "left_service_id": "S1",
                "right_service_id": "S1",
                "left_intent": "transactional",
                "right_intent": "commercial_research",
            }
        ]
        candidates = [
            {"query": "left", "service_id": "S1", "intent": "transactional", "cluster_id": "C1"},
            {"query": "right", "service_id": "S1", "intent": "commercial_research", "cluster_id": "C2"},
        ]
        reviews = {
            "PAIR-1": PairReview("PAIR-1", "same_destination", "reviewed", "reviewer", "reviewed", "observed")
        }
        decisions = {
            "C1": self._decision("C1", action="hub"),
            "C2": self._decision("C2", action="merge", destination_id="S1-OTHER"),
        }

        self.assertEqual(
            validate_pair_architecture_alignment(ambiguous, candidates, reviews, decisions),
            ["PAIR-1 requires one destination but resolves to S1-HUB and S1-OTHER"],
        )

    def test_every_accepted_commercial_cluster_has_exactly_one_owner(self):
        """Duplicating a commercial cluster across pages must be rejected."""
        destinations = (
            PageDestination(
                "S5-HUB",
                "S5",
                "hub",
                "",
                "https://exp76.ru/services/planirovka-territorii/",
                ("C1",),
            ),
            PageDestination(
                "S5-CHILD-1",
                "S5",
                "child_service",
                "S5-HUB",
                "https://exp76.ru/vertikalnaya-planirovka-uchastka/",
                ("C1",),
            ),
        )
        build = ArchitectureBuild(destinations=destinations, commercial_cluster_ids=frozenset({"C1"}))

        self.assertIn("cluster C1 has 2 owners", validate_architecture(build))

    def test_release_rejects_final_unresolved_commercial_cluster(self):
        """A final review cannot mark a commercial cluster unresolved at release."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "transactional"}],
            {
                "C1": self._decision(
                    "C1",
                    action="unresolved",
                    destination_id="",
                    current_url="",
                    proposed_slug="",
                )
            },
        )

        self.assertIn("cluster C1 remains unresolved", validate_architecture(build, release=True))

    def test_child_action_requires_child_service_role(self):
        """A child decision cannot be exported as a hub role."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "transactional"}],
            {
                "C1": self._decision(
                    "C1",
                    action="child",
                    destination_id="S1-CHILD-1",
                    page_role="hub",
                    parent_destination_id="S1-HUB",
                    proposed_url="https://exp76.ru/child-service/",
                )
            },
        )

        self.assertIn("cluster C1 action child requires page role child_service", build.errors)

    def test_informational_merge_cannot_target_commercial_destination(self):
        """An article cluster must not become source material for a service page."""
        build = self._build(
            [
                {"cluster_id": "C1", "intent": "transactional"},
                {"cluster_id": "I1", "intent": "informational"},
            ],
            {
                "C1": self._decision("C1", action="hub"),
                "I1": self._decision(
                    "I1",
                    action="merge",
                    service_id="",
                    destination_id="S1-HUB",
                    page_role="",
                    current_url="",
                    proposed_slug="",
                    business_offer_confirmed="",
                ),
            },
        )

        self.assertIn("cluster I1 cannot merge into commercial destination S1-HUB", build.errors)

    def test_commercial_cluster_can_merge_into_explicit_protected_owner(self):
        """SERP evidence may correct a commercial projection into a frozen category."""
        frozen_url = "https://exp76.ru/category/avtopoliv-na-uchastke/"
        build = self._build(
            [
                {"cluster_id": "FROZEN", "intent": "frozen_collision"},
                {"cluster_id": "C1", "intent": "commercial_research"},
            ],
            {
                "FROZEN": self._decision(
                    "FROZEN",
                    action="frozen",
                    service_id="",
                    destination_id="FROZEN",
                    page_role="frozen",
                    current_url=frozen_url,
                    proposed_slug="category/avtopoliv-na-uchastke",
                    business_offer_confirmed="yes",
                    evidence_refs=f"protected_owner:{frozen_url}",
                ),
                "C1": self._decision(
                    "C1",
                    action="merge",
                    service_id="S2",
                    destination_id="FROZEN",
                    page_role="frozen",
                    current_url="",
                    proposed_slug="",
                    business_offer_confirmed="no",
                    evidence_refs=f"Q000046|protected_owner:{frozen_url}",
                ),
            },
        )

        self.assertEqual(build.errors, ())
        self.assertEqual(build.destinations[0].source_cluster_ids, ("FROZEN", "C1"))

    def test_child_requires_evidence_publication_readiness_and_slug(self):
        """A new child needs independent evidence and publishable content metadata."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "transactional"}],
            {
                "C1": self._decision(
                    "C1",
                    action="child",
                    destination_id="S1-CHILD-1",
                    page_role="child_service",
                    parent_destination_id="S1-HUB",
                    proposed_url="https://exp76.ru/child-service/",
                    proposed_slug="",
                    publication_status="",
                    evidence_refs="",
                )
            },
        )

        self.assertIn("cluster C1 child destination has no evidence references", build.errors)
        self.assertIn("cluster C1 child destination has no publication readiness", build.errors)
        self.assertIn("cluster C1 child destination has no proposed slug", build.errors)

    def test_blocked_child_is_retained_without_claiming_release_readiness(self):
        """A supported candidate may stay blocked until facts/cases are mapped."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "transactional"}],
            {
                "C1": self._decision(
                    "C1",
                    action="child",
                    destination_id="S1-CHILD-1",
                    page_role="child_service",
                    parent_destination_id="S1-HUB",
                    proposed_url="https://exp76.ru/child-service/",
                    publication_status="blocked_facts",
                    business_offer_confirmed="no",
                )
            },
        )

        self.assertEqual(build.errors, ())
        self.assertEqual(build.destinations[0].publication_status, "blocked_facts")

    def test_confirmed_child_offer_requires_traceable_business_source(self):
        """SERP evidence alone cannot prove that exp76 offers a child service."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "transactional"}],
            {
                "C1": self._decision(
                    "C1",
                    action="child",
                    destination_id="S1-CHILD-1",
                    page_role="child_service",
                    parent_destination_id="S1-HUB",
                    proposed_url="https://exp76.ru/child-service/",
                    publication_status="blocked_facts",
                    business_offer_confirmed="yes",
                    evidence_refs="Q000001",
                )
            },
        )

        self.assertIn(
            "cluster C1 confirmed child offer has no business evidence reference",
            build.errors,
        )

    def test_ready_article_requires_successful_serp_evidence(self):
        """An informational destination without a stored representative SERP stays backlog."""
        build = self._build(
            [{"cluster_id": "I1", "intent": "informational"}],
            {
                "I1": self._decision(
                    "I1",
                    action="article",
                    destination_id="S1-ARTICLE-1",
                    page_role="article",
                    parent_destination_id="S1-HUB",
                    current_url="",
                    proposed_url="https://exp76.ru/article-one/",
                    proposed_slug="article-one",
                    publication_status="ready",
                    business_offer_confirmed="no",
                    evidence_refs="missing_representative_serp:I1",
                )
            },
        )

        self.assertIn("cluster I1 ready article has no successful SERP evidence", build.errors)

    def test_legacy_broad_commercial_owner_can_be_special(self):
        """Broad landscaping demand may retain /services/ without becoming an S1 child."""
        build = self._build(
            [{"cluster_id": "C1", "intent": "commercial_research"}],
            {
                "C1": self._decision(
                    "C1",
                    action="special",
                    destination_id="SPECIAL-SERVICES-CATALOG",
                    page_role="special",
                    current_url="https://exp76.ru/services/",
                    proposed_slug="services",
                    publication_status="backlog",
                    business_offer_confirmed="no",
                )
            },
        )

        self.assertEqual(build.errors, ())
        self.assertEqual(build.destinations[0].canonical_url, "https://exp76.ru/services/")


class SemanticProductionDataTest(unittest.TestCase):
    def test_generator_treats_pair_reviews_as_manual_input(self):
        """Regeneration must validate, never synthesize, the manual review ledger."""
        with patch.object(production_architecture, "_write_csv") as write_csv:
            production_architecture.generate(DATA)

        written_names = {call.args[0].name for call in write_csv.call_args_list}
        self.assertEqual({"cluster_page_decisions.csv"}, written_names)

    def test_manual_pair_evidence_constrains_destination_assignment(self):
        """Changing an owner cannot silently rewrite a static evidence-led pair ruling."""
        ambiguous = read_csv(PROCESSED / "serp_ambiguous_pairs.csv")
        candidates = read_csv(PROCESSED / "candidate_cluster_map.csv")
        reviews = production_architecture.load_pair_reviews(
            REVIEWS / "serp_pair_reviews.csv"
        )
        decision_rows = production_architecture.build_cluster_decisions(
            DATA / "scope.json",
            read_csv(PROCESSED / "clusters.csv"),
            read_csv(PROCESSED / "serp_results.csv"),
        )
        decisions = {
            row["cluster_id"]: production_architecture.ClusterPageDecision(
                **{
                    field: row[field]
                    for field in production_architecture.CLUSTER_DECISION_COLUMNS
                }
            )
            for row in decision_rows
        }
        assignments = {
            (row["service_id"], row["query"], row["intent"]): row["cluster_id"]
            for row in candidates
        }
        target = next(
            row
            for row in ambiguous
            if row["decision"] == "manual_review"
            and reviews[row["pair_id"]].decision == "same_destination"
            and assignments[
                (row["left_service_id"], row["left_query"], row["left_intent"])
            ]
            != assignments[
                (row["right_service_id"], row["right_query"], row["right_intent"])
            ]
        )
        right_cluster = assignments[
            (target["right_service_id"], target["right_query"], target["right_intent"])
        ]
        decisions[right_cluster] = replace(
            decisions[right_cluster], destination_id="MUTATED-DESTINATION"
        )

        errors = validate_pair_architecture_alignment(
            ambiguous, candidates, reviews, decisions
        )
        self.assertTrue(any(target["pair_id"] in error for error in errors))

    def test_autopoliv_and_s7_stored_serps_override_lexical_cluster_projection(self):
        """Known mixed SERPs cannot be assigned to a ready lawn or lighting hub."""
        decisions = {
            row["cluster_id"]: row
            for row in production_architecture.build_cluster_decisions(
                DATA / "scope.json",
                read_csv(PROCESSED / "clusters.csv"),
                read_csv(PROCESSED / "serp_results.csv"),
            )
        }

        autopoliv = decisions["SERP-92449D7EF3C6"]
        self.assertEqual("FROZEN-F839FE6BFD56", autopoliv["destination_id"])
        self.assertEqual("merge", autopoliv["url_action"])
        self.assertEqual("frozen", autopoliv["page_role"])
        self.assertIn("Q000046", autopoliv["evidence_refs"])

        self.assertEqual("hub", decisions["SERP-6979557B24CA"]["url_action"])
        self.assertEqual("S7-HUB", decisions["SERP-6979557B24CA"]["destination_id"])
        self.assertEqual("exclude", decisions["HOLD-630573F85F65"]["url_action"])
        self.assertIn("product", decisions["HOLD-630573F85F65"]["rationale"].casefold())
        self.assertEqual("merge", decisions["HOLD-E9DA472745AE"]["url_action"])
        self.assertEqual("merge", decisions["HOLD-F28F0E53D909"]["url_action"])
        self.assertEqual("merge", decisions["SERP-2716C16CFFC8"]["url_action"])
        for cluster_id, query_id in {
            "SERP-5A0AE0E41D86": "Q000107",
            "SERP-4FFE505A1BD1": "Q000110",
            "SERP-942863B727BD": "Q000111",
            "SERP-10BA4FC77863": "Q000113",
        }.items():
            with self.subTest(cluster_id=cluster_id):
                self.assertEqual("exclude", decisions[cluster_id]["url_action"])
                self.assertEqual("none", decisions[cluster_id]["page_role"])
                self.assertIn(query_id, decisions[cluster_id]["evidence_refs"])

    def test_manual_pair_labels_separate_autopoliv_products_guides_and_municipal_noise(self):
        """Canonical needs encode the exact stored-SERP corrections from review."""
        evidence = {
            row["pair_id"]: row
            for row in read_csv(PROCESSED / "serp_ambiguous_pairs.csv")
        }
        reviews = {
            row["pair_id"]: row
            for row in read_csv(REVIEWS / "serp_pair_reviews.csv")
        }
        expected = {
            "PAIR-1D6EFA45BF39": "separate_destinations",
            "PAIR-2F6EED9972F7": "separate_destinations",
            "PAIR-0FE6AFF82088": "separate_destinations",
            "PAIR-10C67F31A394": "separate_destinations",
            "PAIR-B540D2B1CA9A": "separate_destinations",
            "PAIR-DE32C5050F9F": "separate_destinations",
            "PAIR-E9F145411C48": "separate_destinations",
            "PAIR-70CFDD6A2127": "same_destination",
            "PAIR-4CF4E01BB428": "separate_destinations",
        }
        for pair_id, decision in expected.items():
            with self.subTest(pair_id=pair_id):
                pair = evidence[pair_id]
                left_need = production_architecture.canonical_need_label(
                    pair["left_service_id"], pair["left_query"]
                )
                right_need = production_architecture.canonical_need_label(
                    pair["right_service_id"], pair["right_query"]
                )
                self.assertEqual(
                    decision,
                    "same_destination" if left_need == right_need else "separate_destinations",
                )
                self.assertEqual(decision, reviews[pair_id]["decision"])

    def test_production_semantic_files_have_no_pending_decisions(self):
        """The immutable evidence, review overlay and cluster ledger are complete."""
        evidence = read_csv(PROCESSED / "serp_ambiguous_pairs.csv")
        reviews = read_csv(REVIEWS / "serp_pair_reviews.csv")
        decisions = read_csv(REVIEWS / "cluster_page_decisions.csv")
        clusters = read_csv(PROCESSED / "clusters.csv")
        required = [row["pair_id"] for row in evidence if row["decision"] == "manual_review"]

        self.assertEqual(1044, len(evidence))
        self.assertEqual(263, len(required))
        self.assertEqual(263, len(set(required)))
        self.assertEqual(required, [row["pair_id"] for row in reviews])
        self.assertEqual(len(reviews), len({row["pair_id"] for row in reviews}))
        self.assertEqual({"same_destination", "separate_destinations"}, {row["decision"] for row in reviews})
        self.assertEqual(
            Counter(row["decision"] for row in reviews),
            Counter({"same_destination": 186, "separate_destinations": 77}),
        )
        self.assertTrue(all(row["review_status"] == "reviewed" for row in reviews))
        self.assertTrue(all(row["reviewer"] == "codex-2026-08-28" for row in reviews))

        evidence_by_id = {row["pair_id"]: row for row in evidence}
        for review in reviews:
            pair = evidence_by_id[review["pair_id"]]
            overlap_text = f"overlap={pair['overlap']}/10"
            for field in ("rationale", "evidence_note"):
                self.assertIn(overlap_text, review[field], f"{review['pair_id']}:{field}")
                self.assertIn("formats=", review[field], f"{review['pair_id']}:{field}")
            self.assertIn(pair["left_query"], review["rationale"])
            self.assertIn(pair["right_query"], review["rationale"])
            self.assertNotRegex(
                review["rationale"],
                r"(?i)owner|destination|support this ruling|S[1-8]-(?:HUB|CHILD|ARTICLE)|SPECIAL-",
            )
            left_need = production_architecture.canonical_need_label(
                pair["left_service_id"], pair["left_query"]
            )
            right_need = production_architecture.canonical_need_label(
                pair["right_service_id"], pair["right_query"]
            )
            self.assertEqual(
                "same_destination" if left_need == right_need else "separate_destinations",
                review["decision"],
                review["pair_id"],
            )

        cluster_ids = [row["cluster_id"] for row in clusters]
        decision_ids = [row["cluster_id"] for row in decisions]
        self.assertEqual(164, len(cluster_ids))
        self.assertEqual(set(cluster_ids), set(decision_ids))
        self.assertEqual(len(decision_ids), len(set(decision_ids)))
        self.assertTrue(all(row["review_status"] == "reviewed" for row in decisions))
        self.assertTrue(all(row["reviewer"] == "codex-2026-08-28" for row in decisions))
        commercial = [
            row for row in clusters if row["intent"] in {"transactional", "commercial_research"}
        ]
        self.assertEqual(115, len(commercial))
        self.assertEqual(
            Counter(row["intent"] for row in clusters),
            Counter(
                {
                    "commercial_research": 73,
                    "transactional": 42,
                    "informational": 23,
                    "product_only": 17,
                    "frozen_collision": 6,
                    "brand_navigation": 1,
                    "calculator_intent": 1,
                    "external_noise": 1,
                }
            ),
        )

    def test_page_tree_has_full_contract_and_exact_hubs(self):
        """Every exported destination carries its decision and evidence context."""
        path = PROCESSED / "page_architecture.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            self.assertEqual(
                [
                    "destination_id",
                    "service_id",
                    "page_role",
                    "parent_destination_id",
                    "current_url",
                    "proposed_url",
                    "canonical_url",
                    "primary_cluster_id",
                    "source_cluster_ids",
                    "url_action",
                    "publication_status",
                    "evidence_refs",
                    "review_status",
                    "reviewer",
                    "rationale",
                ],
                reader.fieldnames,
            )

        hubs = [row for row in rows if row["page_role"] == "hub"]
        self.assertEqual({f"S{i}" for i in range(1, 9)}, {row["service_id"] for row in hubs})
        self.assertEqual(8, len(hubs))
        self.assertEqual(len(rows), len({row["destination_id"] for row in rows}))
        self.assertEqual(len(rows), len({row["canonical_url"] for row in rows}))
        self.assertFalse(any(row["url_action"] == "unresolved" for row in rows))
        self.assertEqual(
            14,
            sum(
                row["publication_status"] == "ready"
                and row["page_role"] in {"hub", "frozen"}
                for row in rows
            ),
        )
        self.assertFalse(
            any(
                row["publication_status"] == "ready"
                and row["page_role"] in {"child_service", "article", "geo"}
                for row in rows
            )
        )
        for row in rows:
            self.assertTrue(row["evidence_refs"])
            self.assertEqual("reviewed", row["review_status"])
            if row["page_role"] == "child_service" and row["publication_status"] == "ready":
                decision = next(
                    item
                    for item in read_csv(REVIEWS / "cluster_page_decisions.csv")
                    if item["cluster_id"] == row["primary_cluster_id"]
                )
                self.assertEqual("yes", decision["business_offer_confirmed"])

        child_decisions = [
            row
            for row in read_csv(REVIEWS / "cluster_page_decisions.csv")
            if row["url_action"] == "child"
        ]
        self.assertEqual(5, len(child_decisions))
        self.assertEqual(
            Counter(row["business_offer_confirmed"] for row in child_decisions),
            Counter({"yes": 4, "no": 1}),
        )
        self.assertTrue(
            all(
                row["business_offer_confirmed"] != "yes"
                or "business_source:" in row["evidence_refs"]
                for row in child_decisions
            )
        )
        for row in child_decisions:
            if row["business_offer_confirmed"] != "yes":
                continue
            source_ref = next(
                part
                for part in row["evidence_refs"].split("|")
                if part.startswith("business_source:")
            )
            relative_path, section = source_ref.removeprefix("business_source:").split(
                "#", 1
            )
            source_path = ROOT / relative_path
            self.assertTrue(source_path.is_file(), source_ref)
            source_text = source_path.read_text(encoding="utf-8").casefold()
            quoted_need = section.rsplit("[", 1)[-1].rstrip("]").casefold()
            self.assertIn(quoted_need, source_text, source_ref)

    def test_url_map_and_briefs_are_destination_driven(self):
        """All clusters remain assigned and every public destination has a rich brief."""
        clusters = read_csv(PROCESSED / "clusters.csv")
        url_map = read_csv(PROCESSED / "url_map.csv")
        architecture = read_csv(PROCESSED / "page_architecture.csv")
        briefs = read_csv(PROCESSED / "content_briefs.csv")

        self.assertEqual({row["cluster_id"] for row in clusters}, {row["cluster_id"] for row in url_map})
        self.assertEqual(len(url_map), len({row["cluster_id"] for row in url_map}))
        self.assertEqual({row["destination_id"] for row in architecture}, {row["destination_id"] for row in briefs})
        self.assertEqual(len(briefs), len({row["destination_id"] for row in briefs}))
        self.assertFalse(any(row["review_status"] == "pending" for row in clusters + url_map))
        required = {
            "primary_query",
            "secondary_queries",
            "intent",
            "required_sections",
            "price_factors",
            "internal_links",
            "evidence_refs",
            "evidence_state",
            "status",
        }
        self.assertTrue(all(required <= row.keys() for row in briefs))
        self.assertTrue(all(all(row[field] for field in required) for row in briefs))
        self.assertTrue(
            all(row["case_ids"] or row["status"] == "needs_case_mapping" for row in briefs)
        )
        self.assertTrue(
            all(row["photo_ids"] or row["status"] == "needs_case_mapping" for row in briefs)
        )

        role_counts = Counter(row["page_role"] for row in architecture)
        self.assertEqual(
            role_counts,
            Counter({"article": 13, "hub": 8, "frozen": 6, "child_service": 5, "special": 3}),
        )
        self.assertEqual(
            Counter(row["publication_status"] for row in architecture),
            Counter({"ready": 17, "backlog": 13, "blocked_facts": 5}),
        )
