"""Reviewed semantic page architecture decisions.

SERP overlap is evidence only.  A destination is created only from a final
cluster-page review, so draft input cannot silently select an existing hub.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlsplit

from .scope import ScopeConfig


COMMERCIAL_ACTIONS = {"hub", "child", "merge", "exclude", "frozen", "unresolved"}
INFORMATIONAL_ACTIONS = {"article", "merge", "exclude", "frozen"}
FINAL_REVIEW_STATUSES = {"reviewed", "approved"}


class ArchitectureError(ValueError):
    """A review decision is not safe to turn into a destination."""


@dataclass(frozen=True, init=False)
class PairReview:
    pair_id: str
    decision: str
    review_status: str
    reviewer: str
    rationale: str
    evidence_note: str

    def __init__(
        self,
        pair_id: str,
        decision: str,
        review_status: str,
        reviewer: str,
        rationale: str,
        evidence_note: str = "",
        *,
        owner_action: str = "",
    ) -> None:
        object.__setattr__(self, "pair_id", pair_id)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "review_status", review_status)
        object.__setattr__(self, "reviewer", reviewer)
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(self, "evidence_note", evidence_note)
        object.__setattr__(self, "_owner_action", owner_action)

    @property
    def owner_action(self) -> str:
        """Compatibility value retained from the ambiguous-pair evidence CSV."""
        return self._owner_action


@dataclass(frozen=True)
class ClusterPageDecision:
    cluster_id: str
    service_id: str
    destination_id: str
    page_role: str
    parent_destination_id: str
    current_url: str
    proposed_url: str
    proposed_slug: str
    url_action: str
    publication_status: str
    business_offer_confirmed: str
    evidence_refs: str
    review_status: str
    reviewer: str
    rationale: str


@dataclass(frozen=True)
class PageDestination:
    destination_id: str
    service_id: str
    page_role: str
    parent_destination_id: str
    canonical_url: str
    source_cluster_ids: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureBuild:
    destinations: tuple[PageDestination, ...]
    commercial_cluster_ids: frozenset[str]
    informational_cluster_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


PAIR_REVIEW_COLUMNS = (
    "pair_id",
    "decision",
    "owner_action",
    "review_status",
    "reviewer",
    "rationale",
    "evidence_note",
)
CLUSTER_DECISION_COLUMNS = tuple(ClusterPageDecision.__dataclass_fields__)
URL_MAP_COLUMNS = (
    "cluster_id",
    "destination_id",
    "service_id",
    "page_role",
    "parent_destination_id",
    "canonical_url",
    "url_action",
)
PAGE_ARCHITECTURE_COLUMNS = (
    "destination_id",
    "service_id",
    "page_role",
    "parent_destination_id",
    "canonical_url",
    "source_cluster_ids",
)
CONTENT_BRIEF_COLUMNS = (
    "destination_id",
    "service_id",
    "page_role",
    "canonical_url",
    "source_cluster_ids",
    "cluster_names",
    "head_queries",
)


def resolve_pair_action(pair: PairReview) -> str:
    """Return a final pair action without inventing an owner from SERP data."""
    if pair.review_status == "pending":
        raise ArchitectureError(f"{pair.pair_id} remains pending")
    if pair.review_status not in FINAL_REVIEW_STATUSES:
        raise ArchitectureError(f"{pair.pair_id} has non-final review status {pair.review_status!r}")
    if not pair.reviewer:
        raise ArchitectureError(f"{pair.pair_id} has no reviewer")
    if not pair.rationale:
        raise ArchitectureError(f"{pair.pair_id} has no rationale")
    if pair.owner_action == "hold_current_url":
        raise ArchitectureError(f"{pair.pair_id} cannot use hold_current_url")
    return pair.decision


def build_pair_review_queue(ambiguous_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    """Create a draft review queue while retaining evidence from ambiguous pairs."""
    queue: list[dict[str, str]] = []
    for row in ambiguous_rows:
        pair_id = row.get("pair_id", "").strip()
        if not pair_id:
            raise ArchitectureError("ambiguous pair is missing pair_id")
        queue.append(
            {
                "pair_id": pair_id,
                "decision": row.get("decision", "manual_review").strip() or "manual_review",
                "owner_action": row.get("owner_action", "").strip(),
                "review_status": row.get("review_status", "").strip() or "pending",
                "reviewer": row.get("reviewer", "").strip(),
                "rationale": row.get("rationale", "").strip(),
                "evidence_note": row.get("shared_urls", "").strip(),
            }
        )
    return queue


def load_pair_reviews(path: Path) -> dict[str, PairReview]:
    rows = _read_csv(path, {"pair_id", "decision", "review_status", "reviewer", "rationale"})
    reviews: dict[str, PairReview] = {}
    for row in rows:
        pair = PairReview(
            pair_id=row["pair_id"].strip(),
            decision=row["decision"].strip(),
            review_status=row["review_status"].strip(),
            reviewer=row["reviewer"].strip(),
            rationale=row["rationale"].strip(),
            evidence_note=row.get("evidence_note", "").strip(),
            owner_action=row.get("owner_action", "").strip(),
        )
        if not pair.pair_id or pair.pair_id in reviews:
            raise ArchitectureError(f"duplicate or blank pair review id: {pair.pair_id!r}")
        reviews[pair.pair_id] = pair
    return reviews


def validate_pair_review_coverage(
    ambiguous_rows: Sequence[Mapping[str, str]], reviews: Mapping[str, PairReview]
) -> list[str]:
    pair_ids = {row.get("pair_id", "").strip() for row in ambiguous_rows}
    pair_ids.discard("")
    errors = [f"missing pair review: {pair_id}" for pair_id in sorted(pair_ids - set(reviews))]
    errors.extend(f"unknown pair review: {pair_id}" for pair_id in sorted(set(reviews) - pair_ids))
    for pair_id in sorted(pair_ids & set(reviews)):
        try:
            resolve_pair_action(reviews[pair_id])
        except ArchitectureError as exc:
            errors.append(str(exc))
    return errors


def load_cluster_page_decisions(path: Path) -> dict[str, ClusterPageDecision]:
    rows = _read_csv(path, set(CLUSTER_DECISION_COLUMNS))
    decisions: dict[str, ClusterPageDecision] = {}
    for row in rows:
        decision = ClusterPageDecision(**{field: row[field].strip() for field in CLUSTER_DECISION_COLUMNS})
        if not decision.cluster_id or decision.cluster_id in decisions:
            raise ArchitectureError(f"duplicate or blank cluster decision id: {decision.cluster_id!r}")
        decisions[decision.cluster_id] = decision
    return decisions


def resolve_url_architecture(
    scope: ScopeConfig,
    clusters: Sequence[Mapping[str, str]],
    candidates: Sequence[Mapping[str, str]],
    ambiguous_pairs: Sequence[Mapping[str, str]],
    pair_reviews: Mapping[str, PairReview],
    cluster_decisions: Mapping[str, ClusterPageDecision],
) -> ArchitectureBuild:
    """Build destinations exclusively from reviewed cluster decisions."""
    del candidates  # The candidate map remains an input contract and audit source for briefs.
    errors = validate_pair_review_coverage(ambiguous_pairs, pair_reviews)
    service_urls = {service.service_id: service.current_url for service in scope.services}
    hub_urls = set(service_urls.values())
    frozen_urls = set(scope.frozen_urls)
    cluster_by_id = {row.get("cluster_id", "").strip(): row for row in clusters}
    cluster_by_id.pop("", None)
    errors.extend(
        f"unknown cluster decision: {cluster_id}"
        for cluster_id in sorted(set(cluster_decisions) - set(cluster_by_id))
    )

    destinations: list[PageDestination] = []
    merge_sources: list[tuple[str, str]] = []
    commercial_ids: set[str] = set()
    informational_ids: list[str] = []
    for cluster_id, row in sorted(cluster_by_id.items()):
        intent = row.get("intent", "").strip()
        if intent not in {"transactional", "commercial_research", "informational"}:
            continue
        decision = cluster_decisions.get(cluster_id)
        if decision is None:
            errors.append(f"cluster {cluster_id} has no page decision")
            continue
        decision_errors = _decision_errors(decision, intent, scope, service_urls, hub_urls, frozen_urls)
        errors.extend(decision_errors)
        if decision_errors:
            continue
        if decision.url_action in {"exclude", "unresolved"}:
            continue
        if decision.url_action == "merge":
            merge_sources.append((cluster_id, decision.destination_id))
            if intent in {"transactional", "commercial_research"}:
                commercial_ids.add(cluster_id)
            else:
                informational_ids.append(cluster_id)
            continue
        destination = PageDestination(
            destination_id=decision.destination_id,
            service_id=decision.service_id,
            page_role=decision.page_role,
            parent_destination_id=decision.parent_destination_id,
            canonical_url=_decision_url(decision),
            source_cluster_ids=(cluster_id,),
        )
        destinations.append(destination)
        if intent in {"transactional", "commercial_research"}:
            commercial_ids.add(cluster_id)
        else:
            informational_ids.append(cluster_id)

    for cluster_id, destination_id in merge_sources:
        matches = [
            index for index, destination in enumerate(destinations) if destination.destination_id == destination_id
        ]
        if len(matches) != 1:
            errors.append(f"cluster {cluster_id} merges into missing destination {destination_id}")
            continue
        index = matches[0]
        destination = destinations[index]
        expanded = replace(destination, source_cluster_ids=destination.source_cluster_ids + (cluster_id,))
        destinations[index] = expanded
    return ArchitectureBuild(
        destinations=tuple(destinations),
        commercial_cluster_ids=frozenset(commercial_ids),
        informational_cluster_ids=tuple(sorted(informational_ids)),
        errors=tuple(sorted(set(errors))),
    )


def validate_architecture(build: ArchitectureBuild, *, release: bool = False) -> list[str]:
    """Validate ownership and URL uniqueness before an architecture is released."""
    errors = list(build.errors)
    owner_counts = {cluster_id: 0 for cluster_id in build.commercial_cluster_ids}
    destination_ids: set[str] = set()
    urls: set[str] = set()
    frozen_urls = {item.canonical_url for item in build.destinations if item.page_role == "frozen"}
    hub_urls = {item.canonical_url for item in build.destinations if item.page_role == "hub"}
    for destination in build.destinations:
        if not destination.destination_id or destination.destination_id in destination_ids:
            errors.append(f"duplicate or blank destination id: {destination.destination_id!r}")
        destination_ids.add(destination.destination_id)
        if not _is_https_url(destination.canonical_url):
            errors.append(f"destination {destination.destination_id} has invalid URL")
        if destination.canonical_url in urls:
            errors.append(f"duplicate destination URL: {destination.canonical_url}")
        urls.add(destination.canonical_url)
        if destination.page_role == "child_service" and destination.canonical_url in hub_urls | frozen_urls:
            errors.append(f"child destination {destination.destination_id} reuses a hub or frozen URL")
        for cluster_id in destination.source_cluster_ids:
            if cluster_id in owner_counts:
                owner_counts[cluster_id] += 1
    for cluster_id, count in sorted(owner_counts.items()):
        if count != 1:
            errors.append(f"cluster {cluster_id} has {count} owners")
    if release:
        errors.extend(error for error in build.errors if "pending" in error or "unresolved" in error)
    return sorted(set(errors))


def build_destination_briefs(
    architecture: ArchitectureBuild, candidates: Sequence[Mapping[str, str]]
) -> list[dict[str, str]]:
    """Create compact content briefs from the resolved destination ownership."""
    cluster_names: dict[str, str] = {}
    head_queries: dict[str, str] = {}
    for candidate in candidates:
        cluster_id = candidate.get("cluster_id", "").strip()
        if cluster_id and cluster_id not in head_queries:
            head_queries[cluster_id] = candidate.get("query", "").strip()
        if cluster_id and candidate.get("cluster_name", "").strip():
            cluster_names[cluster_id] = candidate["cluster_name"].strip()
    return [
        {
            "destination_id": destination.destination_id,
            "service_id": destination.service_id,
            "page_role": destination.page_role,
            "canonical_url": destination.canonical_url,
            "source_cluster_ids": "|".join(destination.source_cluster_ids),
            "cluster_names": " | ".join(cluster_names.get(cluster_id, "") for cluster_id in destination.source_cluster_ids).strip(),
            "head_queries": " | ".join(head_queries.get(cluster_id, "") for cluster_id in destination.source_cluster_ids).strip(),
        }
        for destination in architecture.destinations
    ]


def _decision_errors(
    decision: ClusterPageDecision,
    intent: str,
    scope: ScopeConfig,
    service_urls: Mapping[str, str],
    hub_urls: set[str],
    frozen_urls: set[str],
) -> list[str]:
    errors: list[str] = []
    prefix = f"cluster {decision.cluster_id}"
    actions = COMMERCIAL_ACTIONS if intent in {"transactional", "commercial_research"} else INFORMATIONAL_ACTIONS
    if decision.review_status not in FINAL_REVIEW_STATUSES:
        errors.append(f"{prefix} has non-final review status {decision.review_status!r}")
    if not decision.reviewer:
        errors.append(f"{prefix} has no reviewer")
    if not decision.rationale:
        errors.append(f"{prefix} has no rationale")
    if decision.url_action not in actions:
        errors.append(f"{prefix} has invalid {intent} action {decision.url_action!r}")
    if decision.url_action == "unresolved":
        if _decision_url(decision) or decision.destination_id:
            errors.append(f"{prefix} unresolved action must have blank target and destination")
        return errors
    if decision.url_action in {"exclude"}:
        return errors
    if not decision.destination_id:
        errors.append(f"{prefix} has no destination id")
    if decision.url_action == "merge":
        return errors
    url = _decision_url(decision)
    if not _is_https_url(url):
        errors.append(f"{prefix} has invalid proposed URL")
        return errors
    if decision.url_action == "hub":
        if decision.service_id not in service_urls or url != service_urls[decision.service_id] or url not in hub_urls:
            errors.append(f"{prefix} hub URL must be its existing S1-S8 URL")
    elif decision.url_action == "child":
        parsed = urlsplit(url)
        scope_host = urlsplit(scope.site).netloc
        if parsed.netloc != scope_host or url in hub_urls | frozen_urls:
            errors.append(f"{prefix} child URL must be a unique internal HTTPS URL")
        if not decision.parent_destination_id:
            errors.append(f"{prefix} child destination has no parent")
    elif decision.url_action == "frozen" and url not in frozen_urls:
        errors.append(f"{prefix} frozen URL is outside the protected categories")
    if decision.url_action in {"hub", "child"} and decision.business_offer_confirmed.casefold() not in {"true", "yes", "1"}:
        errors.append(f"{prefix} has no confirmed business offer")
    return errors


def _decision_url(decision: ClusterPageDecision) -> str:
    return decision.proposed_url or decision.current_url


def _is_https_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and value.endswith("/")


def _read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(required - set(reader.fieldnames or ()))
            if missing:
                raise ArchitectureError(f"{path.name}: missing columns: {', '.join(missing)}")
            return list(reader)
    except OSError as exc:
        raise ArchitectureError(f"unable to read {path}: {exc}") from exc
