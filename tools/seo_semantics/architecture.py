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


COMMERCIAL_ACTIONS = {"hub", "child", "merge", "exclude", "frozen", "special", "unresolved"}
INFORMATIONAL_ACTIONS = {"article", "merge", "exclude", "frozen"}
FINAL_REVIEW_STATUSES = {"reviewed", "approved"}
PAIR_DECISIONS = {"same_destination", "separate_destinations"}
PUBLICATION_STATUSES = {"ready", "blocked_facts", "backlog"}


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
    current_url: str = ""
    proposed_url: str = ""
    primary_cluster_id: str = ""
    url_action: str = ""
    publication_status: str = ""
    evidence_refs: str = ""
    review_status: str = ""
    reviewer: str = ""
    rationale: str = ""


@dataclass(frozen=True)
class ArchitectureBuild:
    destinations: tuple[PageDestination, ...]
    commercial_cluster_ids: frozenset[str]
    informational_cluster_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    cluster_decisions: tuple[ClusterPageDecision, ...] = ()


PAIR_REVIEW_COLUMNS = (
    "pair_id",
    "decision",
    "review_status",
    "reviewer",
    "rationale",
    "evidence_note",
)
CLUSTER_DECISION_COLUMNS = tuple(ClusterPageDecision.__dataclass_fields__)
URL_MAP_COLUMNS = (
    "map_id",
    "cluster_id",
    "service_id",
    "cluster_name",
    "intent",
    "current_url",
    "target_url",
    "url_action",
    "method",
    "evidence",
    "validation_status",
    "confidence",
    "review_status",
    "reviewer",
    "rationale",
    "destination_id",
    "page_role",
    "parent_destination_id",
    "publication_status",
)
PAGE_ARCHITECTURE_COLUMNS = (
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
)
CONTENT_BRIEF_COLUMNS = (
    "destination_id",
    "service_id",
    "target_url",
    "page_type",
    "source_cluster_ids",
    "primary_query",
    "secondary_queries",
    "intent",
    "title_intent",
    "h1_intent",
    "required_sections",
    "price_factors",
    "case_ids",
    "photo_ids",
    "internal_links",
    "frozen_links",
    "evidence_refs",
    "evidence_state",
    "missing_facts",
    "status",
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
    if pair.decision not in PAIR_DECISIONS:
        raise ArchitectureError(f"{pair.pair_id} has invalid decision {pair.decision!r}")
    return pair.decision


def build_pair_review_queue(ambiguous_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    """Create a draft overlay for manual rows without copying policy evidence."""
    queue: list[dict[str, str]] = []
    for row in ambiguous_rows:
        if row.get("decision", "").strip() != "manual_review":
            continue
        pair_id = row.get("pair_id", "").strip()
        if not pair_id:
            raise ArchitectureError("ambiguous pair is missing pair_id")
        queue.append(
            {
                "pair_id": pair_id,
                "decision": "manual_review",
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
    pair_ids = {
        row.get("pair_id", "").strip()
        for row in ambiguous_rows
        if row.get("decision", "").strip() == "manual_review"
    }
    pair_ids.discard("")
    errors = [f"missing pair review: {pair_id}" for pair_id in sorted(pair_ids - set(reviews))]
    errors.extend(f"unknown pair review: {pair_id}" for pair_id in sorted(set(reviews) - pair_ids))
    for pair_id in sorted(pair_ids & set(reviews)):
        try:
            resolve_pair_action(reviews[pair_id])
        except ArchitectureError as exc:
            errors.append(str(exc))
    errors.extend(validate_pair_review_consistency(ambiguous_rows, reviews))
    return errors


def validate_pair_review_consistency(
    ambiguous_rows: Sequence[Mapping[str, str]], reviews: Mapping[str, PairReview]
) -> list[str]:
    """Reject a separate edge inside a same-destination transitive component."""
    manual_rows = {
        row.get("pair_id", "").strip(): row
        for row in ambiguous_rows
        if row.get("decision", "").strip() == "manual_review"
    }
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for pair_id, review in reviews.items():
        row = manual_rows.get(pair_id)
        if row is None or review.decision != "same_destination":
            continue
        union(row.get("left_query_id", "").strip(), row.get("right_query_id", "").strip())

    errors: list[str] = []
    for pair_id, review in sorted(reviews.items()):
        row = manual_rows.get(pair_id)
        if row is None or review.decision != "separate_destinations":
            continue
        left_id = row.get("left_query_id", "").strip()
        right_id = row.get("right_query_id", "").strip()
        if left_id and right_id and find(left_id) == find(right_id):
            errors.append(f"{pair_id} separates one same-destination component")
    return errors


def validate_pair_architecture_alignment(
    ambiguous_rows: Sequence[Mapping[str, str]],
    candidates: Sequence[Mapping[str, str]],
    reviews: Mapping[str, PairReview],
    cluster_decisions: Mapping[str, ClusterPageDecision],
) -> list[str]:
    """Ensure reviewed pair outcomes resolve to the final destination IDs."""
    assignments = {
        (
            row.get("service_id", "").strip(),
            row.get("query", "").strip(),
            row.get("intent", "").strip(),
        ): row.get("cluster_id", "").strip()
        for row in candidates
    }
    errors: list[str] = []
    for row in ambiguous_rows:
        pair_id = row.get("pair_id", "").strip()
        review = reviews.get(pair_id)
        if row.get("decision", "").strip() != "manual_review" or review is None:
            continue
        left_cluster = assignments.get(
            (
                row.get("left_service_id", "").strip(),
                row.get("left_query", "").strip(),
                row.get("left_intent", "").strip(),
            ),
            "",
        )
        right_cluster = assignments.get(
            (
                row.get("right_service_id", "").strip(),
                row.get("right_query", "").strip(),
                row.get("right_intent", "").strip(),
            ),
            "",
        )
        if not left_cluster or not right_cluster:
            errors.append(f"{pair_id} has no candidate cluster assignment")
            continue
        left_decision = cluster_decisions.get(left_cluster)
        right_decision = cluster_decisions.get(right_cluster)
        if left_decision is None or right_decision is None:
            errors.append(f"{pair_id} has no final cluster page decision")
            continue
        left_destination = left_decision.destination_id
        right_destination = right_decision.destination_id
        left_excluded = left_decision.url_action == "exclude"
        right_excluded = right_decision.url_action == "exclude"
        if (
            review.decision == "same_destination"
            and not (left_excluded and right_excluded)
            and left_destination != right_destination
        ):
            errors.append(
                f"{pair_id} requires one destination but resolves to "
                f"{left_destination or '<blank>'} and {right_destination or '<blank>'}"
            )
        if (
            review.decision == "separate_destinations"
            and not (left_excluded or right_excluded)
            and left_destination == right_destination
        ):
            errors.append(
                f"{pair_id} requires separate destinations but resolves to "
                f"{left_destination or '<blank>'}"
            )
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
    errors = validate_pair_review_coverage(ambiguous_pairs, pair_reviews)
    errors.extend(
        validate_pair_architecture_alignment(
            ambiguous_pairs,
            candidates,
            pair_reviews,
            cluster_decisions,
        )
    )
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
    merge_sources: list[tuple[str, str, str]] = []
    commercial_ids: set[str] = set()
    informational_ids: list[str] = []
    for cluster_id, row in sorted(cluster_by_id.items()):
        intent = row.get("intent", "").strip()
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
            merge_sources.append((cluster_id, decision.destination_id, intent))
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
            current_url=decision.current_url,
            proposed_url=decision.proposed_url,
            primary_cluster_id=cluster_id,
            url_action=decision.url_action,
            publication_status=decision.publication_status,
            evidence_refs=decision.evidence_refs,
            review_status=decision.review_status,
            reviewer=decision.reviewer,
            rationale=decision.rationale,
        )
        destinations.append(destination)
        if intent in {"transactional", "commercial_research"}:
            commercial_ids.add(cluster_id)
        else:
            informational_ids.append(cluster_id)

    for cluster_id, destination_id, source_intent in merge_sources:
        matches = [
            index for index, destination in enumerate(destinations) if destination.destination_id == destination_id
        ]
        if len(matches) != 1:
            errors.append(f"cluster {cluster_id} merges into missing destination {destination_id}")
            continue
        index = matches[0]
        destination = destinations[index]
        destination_intent = cluster_by_id[destination.source_cluster_ids[0]].get("intent", "").strip()
        source_decision = cluster_decisions[cluster_id]
        protected_owner_merge = (
            destination.page_role == "frozen"
            and source_intent in {"transactional", "commercial_research"}
            and source_decision.page_role == "frozen"
            and "protected_owner:" in source_decision.evidence_refs
        )
        if (
            _intent_family(source_intent) != _intent_family(destination_intent)
            and not protected_owner_merge
        ):
            errors.append(f"cluster {cluster_id} cannot merge into commercial destination {destination_id}")
            continue
        expanded = replace(destination, source_cluster_ids=destination.source_cluster_ids + (cluster_id,))
        destinations[index] = expanded
    return ArchitectureBuild(
        destinations=tuple(destinations),
        commercial_cluster_ids=frozenset(commercial_ids),
        informational_cluster_ids=tuple(sorted(informational_ids)),
        errors=tuple(sorted(set(errors))),
        cluster_decisions=tuple(
            cluster_decisions[cluster_id]
            for cluster_id in sorted(set(cluster_by_id) & set(cluster_decisions))
        ),
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


_PRICE_FACTORS = {
    "S1": "площадь|состав проектных разделов|исходные данные|визуализация|авторское сопровождение",
    "S2": "площадь|подготовка грунта|тип газона|доставка|полив|удаленность объекта",
    "S3": "вид и размер растений|подготовка посадочных мест|грунт|доставка|уход после посадки",
    "S4": "площадь сада|состав работ|состояние растений|сезонность|вывоз растительных остатков",
    "S5": "площадь|перепад высот|объем перемещения грунта|техника|условия подъезда",
    "S6": "длина и высота|материал|основание|рельеф|условия отвода воды",
    "S7": "площадь|количество зон|схема прокладки|оборудование|условия подключения",
    "S8": "ширина въезда|глубина канавы|нагрузка|материалы|условия подъезда",
}
_FROZEN_LINKS = {
    "S1": "https://exp76.ru/category/drenazh-uchastka/|https://exp76.ru/category/livnevaya-kanalizatsiya/|https://exp76.ru/category/avtopoliv-na-uchastke/|https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
    "S2": "https://exp76.ru/category/avtopoliv-na-uchastke/",
    "S3": "https://exp76.ru/category/avtopoliv-na-uchastke/",
    "S5": "https://exp76.ru/category/drenazh-uchastka/|https://exp76.ru/category/osushenie-uchastka/|https://exp76.ru/category/livnevaya-kanalizatsiya/",
    "S6": "https://exp76.ru/category/drenazh-uchastka/",
    "S8": "https://exp76.ru/category/drenazh-uchastka/|https://exp76.ru/category/livnevaya-kanalizatsiya/",
}


def build_destination_briefs(
    architecture: ArchitectureBuild,
    candidates: Sequence[Mapping[str, str]],
    clusters: Sequence[Mapping[str, str]] = (),
) -> list[dict[str, str]]:
    """Create destination-driven briefs without pretending case/photo readiness."""
    cluster_by_id = {
        row.get("cluster_id", "").strip(): row
        for row in clusters
        if row.get("cluster_id", "").strip()
    }
    queries_by_cluster: dict[str, list[str]] = {}
    for candidate in candidates:
        cluster_id = candidate.get("cluster_id", "").strip()
        query = candidate.get("query", "").strip()
        if cluster_id and query and query not in queries_by_cluster.setdefault(cluster_id, []):
            queries_by_cluster[cluster_id].append(query)
    destination_by_id = {item.destination_id: item for item in architecture.destinations}
    rows: list[dict[str, str]] = []
    for destination in architecture.destinations:
        primary_cluster = cluster_by_id.get(destination.primary_cluster_id, {})
        primary_query = primary_cluster.get("head_query", "").strip()
        if not primary_query:
            primary_query = next(
                (
                    query
                    for cluster_id in destination.source_cluster_ids
                    for query in queries_by_cluster.get(cluster_id, [])
                ),
                destination.destination_id,
            )
        secondary = [
            query
            for cluster_id in destination.source_cluster_ids
            for query in queries_by_cluster.get(cluster_id, [])
            if query != primary_query
        ]
        secondary = list(dict.fromkeys(secondary))[:20]
        intents = list(
            dict.fromkeys(
                cluster_by_id.get(cluster_id, {}).get("intent", "").strip()
                for cluster_id in destination.source_cluster_ids
                if cluster_by_id.get(cluster_id, {}).get("intent", "").strip()
            )
        )
        if destination.page_role == "article":
            sections = "Краткий ответ|условия и ограничения|пошаговый разбор|типовые ошибки|когда нужен подрядчик|связанная услуга"
            missing_facts = "успешная representative-query SERP|проверенные иллюстрации|редакторская проверка"
        else:
            sections = "Состав работ|когда подходит|этапы|факторы цены|примеры работ|FAQ|связанные услуги"
            missing_facts = "карта реальных кейсов|карта фотографий|подтвержденные цены и сроки"
        related = [
            item.canonical_url
            for item in architecture.destinations
            if item.service_id == destination.service_id
            and item.destination_id != destination.destination_id
            and item.page_role in {"hub", "child_service", "article"}
        ]
        parent = destination_by_id.get(destination.parent_destination_id)
        if parent is not None:
            related.insert(0, parent.canonical_url)
        internal_links = "|".join(dict.fromkeys(related)) or "https://exp76.ru/services/"
        rows.append(
            {
                "destination_id": destination.destination_id,
                "service_id": destination.service_id,
                "target_url": destination.canonical_url,
                "page_type": destination.page_role,
                "source_cluster_ids": "|".join(destination.source_cluster_ids),
                "primary_query": primary_query,
                "secondary_queries": "|".join(secondary) or primary_query,
                "intent": "|".join(intents) or destination.page_role,
                "title_intent": f"{primary_query} — Эксперты",
                "h1_intent": primary_query[:1].upper() + primary_query[1:],
                "required_sections": sections,
                "price_factors": _PRICE_FACTORS.get(
                    destination.service_id,
                    "не применяется к сохраненному владельцу|контекст перехода",
                ),
                "case_ids": "",
                "photo_ids": "",
                "internal_links": internal_links,
                "frozen_links": _FROZEN_LINKS.get(destination.service_id, ""),
                "evidence_refs": destination.evidence_refs,
                "evidence_state": (
                    f"publication={destination.publication_status};"
                    "cases=needs_mapping;photos=needs_mapping"
                ),
                "missing_facts": missing_facts,
                "status": "needs_case_mapping",
            }
        )
    return rows


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
    if intent in {"transactional", "commercial_research"}:
        actions = COMMERCIAL_ACTIONS
    elif intent == "informational":
        actions = INFORMATIONAL_ACTIONS
    elif intent == "frozen_collision":
        actions = {"frozen"}
    elif intent in {"product_only", "external_noise"}:
        actions = {"exclude"}
    elif intent in {"brand_navigation", "calculator_intent"}:
        actions = {"special"}
    else:
        actions = {"exclude"}
    if decision.review_status not in FINAL_REVIEW_STATUSES:
        errors.append(f"{prefix} has non-final review status {decision.review_status!r}")
    if not decision.reviewer:
        errors.append(f"{prefix} has no reviewer")
    if not decision.rationale:
        errors.append(f"{prefix} has no rationale")
    if not decision.evidence_refs:
        errors.append(f"{prefix} has no evidence references")
    if decision.publication_status not in PUBLICATION_STATUSES:
        errors.append(f"{prefix} has invalid publication status {decision.publication_status!r}")
    if decision.url_action not in actions:
        errors.append(f"{prefix} has invalid {intent} action {decision.url_action!r}")
    if decision.url_action == "unresolved":
        if _decision_url(decision) or decision.destination_id:
            errors.append(f"{prefix} unresolved action must have blank target and destination")
        if intent in {"transactional", "commercial_research"}:
            errors.append(f"{prefix} remains unresolved")
        return errors
    if decision.url_action in {"exclude"}:
        if decision.destination_id or _decision_url(decision):
            errors.append(f"{prefix} excluded action must have blank target and destination")
        return errors
    expected_role = {
        "hub": "hub",
        "child": "child_service",
        "frozen": "frozen",
        "article": "article",
        "special": "special",
    }.get(decision.url_action)
    if expected_role and decision.page_role != expected_role:
        errors.append(f"{prefix} action {decision.url_action} requires page role {expected_role}")
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
        if not decision.evidence_refs:
            errors.append(f"{prefix} child destination has no evidence references")
        if not decision.publication_status:
            errors.append(f"{prefix} child destination has no publication readiness")
        if not decision.proposed_slug:
            errors.append(f"{prefix} child destination has no proposed slug")
        if (
            decision.business_offer_confirmed.casefold() in {"true", "yes", "1"}
            and "business_source:" not in decision.evidence_refs
        ):
            errors.append(f"{prefix} confirmed child offer has no business evidence reference")
        if decision.publication_status == "ready":
            if decision.business_offer_confirmed.casefold() not in {"true", "yes", "1"}:
                errors.append(f"{prefix} ready child has no confirmed business offer")
            if not _has_successful_serp_reference(decision.evidence_refs):
                errors.append(f"{prefix} ready child has no successful SERP evidence")
    elif decision.url_action == "article":
        parsed = urlsplit(url)
        scope_host = urlsplit(scope.site).netloc
        if parsed.netloc != scope_host or url in hub_urls | frozen_urls:
            errors.append(f"{prefix} article URL must be a unique internal HTTPS URL")
        if not decision.parent_destination_id:
            errors.append(f"{prefix} article destination has no parent")
        if not decision.proposed_slug:
            errors.append(f"{prefix} article destination has no proposed slug")
        if decision.publication_status == "ready" and not _has_successful_serp_reference(
            decision.evidence_refs
        ):
            errors.append(f"{prefix} ready article has no successful SERP evidence")
    elif decision.url_action == "frozen" and url not in frozen_urls:
        errors.append(f"{prefix} frozen URL is outside the protected categories")
    elif decision.url_action == "special":
        if urlsplit(url).netloc != urlsplit(scope.site).netloc:
            errors.append(f"{prefix} special URL must be internal")
    if decision.url_action == "hub" and decision.business_offer_confirmed.casefold() not in {"true", "yes", "1"}:
        errors.append(f"{prefix} has no confirmed business offer")
    return errors


def _has_successful_serp_reference(value: str) -> bool:
    return any(part.strip().startswith("Q") for part in value.split("|"))


def _decision_url(decision: ClusterPageDecision) -> str:
    return decision.proposed_url or decision.current_url


def _is_https_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and value.endswith("/")


def _intent_family(intent: str) -> str:
    if intent in {"transactional", "commercial_research"}:
        return "commercial"
    if intent == "informational":
        return "informational"
    return "other"


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
