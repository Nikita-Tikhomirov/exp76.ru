"""Regression tests for reviewed semantic page decisions."""

from __future__ import annotations

import unittest

from tools.seo_semantics.architecture import (
    ArchitectureBuild,
    ArchitectureError,
    PageDestination,
    PairReview,
    build_pair_review_queue,
    resolve_pair_action,
    validate_architecture,
)


class SemanticArchitectureTests(unittest.TestCase):
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
