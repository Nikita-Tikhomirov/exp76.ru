"""Regression tests for reviewed semantic page decisions."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.seo_semantics.architecture import (
    ArchitectureBuild,
    ArchitectureError,
    PageDestination,
    PairReview,
    build_pair_review_queue,
    resolve_url_architecture,
    resolve_pair_action,
    validate_architecture,
)
from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE = load_scope(ROOT / "seo-data/2026-08-exp76-services/scope.json")


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

    def test_review_queue_preserves_reviewed_owner_boundaries(self):
        """The queue must not downgrade protected reviewed pair decisions."""
        queue = build_pair_review_queue(
            [
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

        self.assertEqual(queue[0]["review_status"], "reviewed")
        self.assertEqual(queue[0]["reviewer"], "policy_scope_owner")

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
