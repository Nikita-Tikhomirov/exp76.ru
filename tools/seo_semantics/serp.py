"""Deterministic SERP queue preparation and URL-overlap helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Iterable, Literal, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

from .normalize import normalize_query
from .scope import load_scope


ELIGIBLE_INTENTS = frozenset(
    {"transactional", "commercial_research", "informational", "product_only"}
)
COMMERCIAL_INTENTS = frozenset({"transactional", "commercial_research"})
MOBILE_HEAD_SERVICES = frozenset({"S2", "S5", "S8"})
QUEUE_COLUMNS = (
    "query_id",
    "query",
    "service_id",
    "intent",
    "region",
    "device",
    "reason",
    "status",
)

SERP_RESULT_COLUMNS = (
    "query_id", "query", "service_id", "intent", "region", "device", "checked_at",
    "rank", "url", "canonical_url", "title", "source_file", "method",
)
CLUSTER_COLUMNS = (
    "cluster_id", "service_id", "cluster_name", "head_query", "query_ids", "candidate_count",
    "intent", "geo_scope", "broad_frequency", "phrase_frequency", "exact_frequency",
    "seasonality", "webmaster_impressions", "webmaster_clicks", "serp_cohesion", "target_url",
    "url_action", "priority", "confidence", "rationale", "method", "evidence",
    "validation_status", "review_status", "reviewer", "review_rationale",
)
URL_MAP_COLUMNS = (
    "map_id", "cluster_id", "service_id", "cluster_name", "intent", "current_url",
    "target_url", "url_action", "method", "evidence", "validation_status", "confidence",
    "review_status", "reviewer", "rationale",
)
CANDIDATE_MAP_COLUMNS = (
    "candidate_key", "service_id", "query", "intent", "cluster_id",
    "representative_query_ids", "current_url", "target_url", "url_action",
    "assignment_method", "validation_status", "review_status", "reviewer", "rationale",
)
AMBIGUOUS_PAIR_COLUMNS = (
    "pair_id", "left_query_id", "right_query_id", "left_query", "right_query",
    "left_service_id", "right_service_id", "left_intent", "right_intent", "overlap",
    "shared_urls", "decision", "owner_action", "validation_status", "review_status",
    "reviewer", "rationale",
)

_PRICE_TOKENS = frozenset(
    {"цена", "цены", "цену", "ценой", "цене", "цен", "стоимость", "стоимости", "стоимостью"}
)
_ORDER_TOKENS = frozenset({"заказать", "закажите", "заказ", "заказа", "заказу", "заказом"})
_NEW_PAGE_DECISIONS = frozenset({"new_page_proposal", "new_child_candidate"})


@dataclass(frozen=True)
class SerpQueueRow:
    query_id: str
    query: str
    service_id: str
    intent: str
    region: str
    device: str
    reason: str
    status: str


@dataclass(frozen=True)
class SerpQueueBuild:
    rows: tuple[SerpQueueRow, ...]
    eligible_row_count: int
    distinct_candidate_count: int
    tentative_group_count: int


@dataclass(frozen=True)
class ClusterBuildSummary:
    eligible_row_count: int
    distinct_candidate_count: int
    cluster_count: int
    frozen_cluster_count: int
    serp_query_count: int
    serp_result_count: int
    ambiguous_pair_count: int


@dataclass(frozen=True)
class SpecialOwnerDecision:
    target_url: str
    url_action: str
    validation_status: str
    review_status: str
    reviewer: str
    rationale: str


@dataclass(frozen=True)
class SerpCorpusRoles:
    primary_query_ids: tuple[str, ...]
    mobile_query_ids: tuple[str, ...]
    brand_query_ids: tuple[str, ...]


@dataclass
class _Candidate:
    service_id: str
    query: str
    intent: str
    groups: set[tuple[str, str]] = field(default_factory=set)
    broad_frequency: float = 0.0
    phrase_frequency: float = 0.0
    exact_frequency: float = 0.0
    impressions: float = 0.0
    clicks: float = 0.0
    has_local_evidence: bool = False
    clicked: bool = False
    new_page_proposal: bool = False
    eligible: bool = False
    keyword_ids: set[str] = field(default_factory=set)
    seeds: set[str] = field(default_factory=set)
    regions: set[str] = field(default_factory=set)
    wordcraft_clusters: set[str] = field(default_factory=set)

    @property
    def key(self) -> tuple[str, str, str]:
        return self.service_id, self.query, self.intent


def canonicalize_serp_url(url: str) -> str:
    """Return a comparison-only HTTPS canonical form for an organic result URL."""

    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"invalid SERP URL: {url!r}") from exc
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"SERP URL must use HTTP(S): {url!r}")

    hostname = parsed.hostname.casefold()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    netloc = f"{hostname}:{port}" if port is not None else hostname
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if not path.startswith("/"):
        path = f"/{path}"
    path = f"{path.rstrip('/')}/"
    return urlunsplit(("https", netloc, path, "", ""))


def validate_organic_result(
    result: Mapping[str, object],
    source: str,
) -> tuple[int, str, str, str]:
    """Validate one organic result and return rank, URL, title, and canonical URL."""

    try:
        rank = int(result.get("rank", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"SERP record {source} has invalid rank/title") from exc
    url = str(result.get("url", ""))
    title = str(result.get("title", "")).strip()
    if rank <= 0 or not title:
        raise ValueError(f"SERP record {source} has invalid rank/title")
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").casefold().removeprefix("www.")
    if hostname == "yandex.ru" and parsed.path.startswith("/an/count/"):
        raise ValueError(f"SERP record {source} contains an ad tracking URL")
    canonical = canonicalize_serp_url(url)
    return rank, url, title, canonical


def overlap_count(left: Sequence[str], right: Sequence[str]) -> int:
    """Count unique canonical URL intersections between two organic result sets."""

    left_urls = {canonicalize_serp_url(url) for url in left}
    right_urls = {canonicalize_serp_url(url) for url in right}
    return len(left_urls & right_urls)


def decide_cluster(
    overlap: int,
    same_intent: bool,
) -> Literal["merge", "manual_review", "split"]:
    """Apply the frozen top-10 overlap thresholds from the semantic strategy."""

    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap <= 1:
        return "split"
    if overlap >= 4 and same_intent:
        return "merge"
    return "manual_review"


def complete_link_clusters(
    query_ids: Sequence[str],
    intents: Mapping[str, str],
    overlaps: Mapping[tuple[str, str], int],
) -> tuple[tuple[str, ...], ...]:
    """Return deterministic complete-link clusters at the four-URL threshold."""

    ordered_ids = tuple(sorted(query_ids))
    if len(set(ordered_ids)) != len(ordered_ids):
        raise ValueError("complete-link query_ids must be unique")
    if set(ordered_ids) != set(intents):
        raise ValueError("complete-link intents must cover every query_id")

    def pair_overlap(left: str, right: str) -> int:
        key = tuple(sorted((left, right)))
        if key not in overlaps:
            raise ValueError(f"missing overlap for pair {key[0]}~{key[1]}")
        return overlaps[key]

    clusters: list[tuple[str, ...]] = [(query_id,) for query_id in ordered_ids]
    while True:
        feasible: list[tuple[float, float, tuple[str, ...], int, int]] = []
        for left_index, right_index in combinations(range(len(clusters)), 2):
            left = clusters[left_index]
            right = clusters[right_index]
            cross_pairs = [(a, b) for a in left for b in right]
            if any(intents[a] != intents[b] for a, b in cross_pairs):
                continue
            scores = [pair_overlap(a, b) for a, b in cross_pairs]
            if min(scores) < 4:
                continue
            merged = tuple(sorted(left + right))
            feasible.append((float(min(scores)), sum(scores) / len(scores), merged, left_index, right_index))
        if not feasible:
            break
        _, _, merged, left_index, right_index = min(
            feasible,
            key=lambda item: (-item[0], -item[1], item[2]),
        )
        clusters = [
            cluster
            for index, cluster in enumerate(clusters)
            if index not in {left_index, right_index}
        ]
        clusters.append(merged)
        clusters.sort()
    return tuple(clusters)


def route_special_owner(
    query: str,
    intent: str,
    current_url: str,
    *,
    clicked: bool = False,
) -> SpecialOwnerDecision | None:
    """Apply explicit reviewed owners before service-level projection."""

    normalized = normalize_query(query)
    external_patterns = (
        r"(?:^| )авито(?: |$)",
        r"(?:^| )леруа(?: мерлен)?(?: |$)",
        r"(?:^| )(?:tehno|техно)\s*(?:niki|ники|ник)(?: |$)",
        r"(?:^| )(?:niki|ники|ник)(?:\s+ооо)?\s+(?:tehno|техно)(?: |$)",
        r"(?:^| )(?:mini|мини) погрузчики ru(?: |$)",
        r"(?:^| )(?:geo|гео) услуги(?: ru)?(?: |$)",
        r"(?:^| )in garden(?: |$)",
        r"(?:^| )(?:экскаваторы|ekskavatory) arenda(?: |$)",
        r"(?:^| )эден крафт(?: |$)",
        r"(?:^| )\d{7,}(?: |$)",
        r"(?:^| )(?:улица|переулок|ул)(?: [^ ]+)* (?:д|дом) \d+(?: |$)",
    )
    is_false_brand = normalized == "торговые центры эксперт 76 ru"
    if is_false_brand or any(re.search(pattern, normalized) for pattern in external_patterns):
        return SpecialOwnerDecision(
            "",
            "exclude",
            "explicit_external_noise",
            "reviewed",
            "policy_external_noise",
            "explicit external brand, marketplace, or domain-noise query excluded",
        )
    if "калькулятор" in normalized or "калькуляторы" in normalized:
        return SpecialOwnerDecision(
            "https://exp76.ru/kalkuljator-uslug/",
            "keep_special_owner",
            "existing_owner_evidence",
            "reviewed",
            "policy_calculator_owner",
            "existing calculator owner supported by Q000012,Q000026,Q000031,Q000070",
        )
    if intent == "brand_navigation":
        if clicked:
            return SpecialOwnerDecision(
                "https://exp76.ru/",
                "keep_special_owner",
                "existing_owner_evidence",
                "reviewed",
                "policy_brand_owner",
                "clicked exp76 brand-navigation query retained on the homepage",
            )
        return SpecialOwnerDecision(
            "",
            "exclude",
            "manual_brand_review",
            "pending",
            "",
            "unclicked brand-like query requires manual ownership review",
        )
    return None


def validate_serp_corpus(
    queue_rows: Sequence[Mapping[str, str]],
    records: Mapping[str, Mapping[str, object]],
) -> SerpCorpusRoles:
    """Validate the immutable 141-query corpus and classify queue row roles."""

    expected_ids = tuple(f"Q{index:06d}" for index in range(1, 142))
    queue_ids = tuple(row.get("query_id", "") for row in queue_rows)
    if tuple(sorted(queue_ids)) != expected_ids or len(set(queue_ids)) != 141:
        raise ValueError("SERP queue requires exact Q000001-Q000141 coverage")
    if set(records) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(records))
        extra = sorted(set(records) - set(expected_ids))
        raise ValueError(
            f"SERP QID coverage mismatch: missing={','.join(missing) or 'none'};"
            f" extra={','.join(extra) or 'none'}"
        )

    queue_by_id = {row["query_id"]: row for row in queue_rows}
    for query_id in expected_ids:
        queue_row = queue_by_id[query_id]
        record = records[query_id]
        for field_name in ("query", "region", "device"):
            if str(record.get(field_name, "")) != queue_row.get(field_name, ""):
                raise ValueError(f"SERP record {query_id} differs from queue field {field_name}")
        results = record.get("results")
        if not isinstance(results, list) or sorted(int(item.get("rank", 0)) for item in results) != list(range(1, 11)):
            raise ValueError(f"SERP record {query_id} requires exact ranks 1-10")
        for result in results:
            canonicalize_serp_url(str(result.get("url", "")))

    primary_rows = [
        row
        for row in queue_rows
        if row.get("device") == "desktop" and row.get("intent") in ELIGIBLE_INTENTS
    ]
    mobile_rows = [row for row in queue_rows if row.get("device") == "mobile"]
    brand_rows = [row for row in queue_rows if row.get("intent") == "brand_navigation"]
    primary_keys = {
        (row.get("service_id", ""), normalize_query(row.get("query", "")), row.get("intent", ""))
        for row in primary_rows
    }
    if len(primary_rows) != 131 or len(primary_keys) != 131:
        raise ValueError("SERP corpus requires 131 unique desktop eligible graph nodes")
    if len(mobile_rows) != 3:
        raise ValueError("SERP corpus requires exactly three mobile auxiliary rows")
    if any(
        (row.get("service_id", ""), normalize_query(row.get("query", "")), row.get("intent", ""))
        not in primary_keys
        for row in mobile_rows
    ):
        raise ValueError("mobile auxiliary rows must duplicate desktop graph nodes")
    if len(brand_rows) != 7 or any("clicked" not in row.get("reason", "").split("|") for row in brand_rows):
        raise ValueError("SERP corpus requires seven clicked brand auxiliary rows")
    return SerpCorpusRoles(
        tuple(sorted(row["query_id"] for row in primary_rows)),
        tuple(sorted(row["query_id"] for row in mobile_rows)),
        tuple(sorted(row["query_id"] for row in brand_rows)),
    )


def build_representative_queue(rows: Iterable[Mapping[str, str]]) -> SerpQueueBuild:
    """Build a stable queue from seed-based tentative service groups.

    Eligible candidates are deduplicated by ``service_id + normalized query +
    intent``. A tentative group is ``service_id + source seed``; rows without a
    seed use one service-level unseeded group. Multiple selector reasons are
    coalesced onto one query/device row, so the queue is representative rather
    than one row per candidate.
    """

    candidates: dict[tuple[str, str, str], _Candidate] = {}
    eligible_row_count = 0
    group_members: dict[tuple[str, str], set[tuple[str, str, str]]] = {}

    for row_number, row in enumerate(rows, start=2):
        relevance = row.get("relevance", "").strip()
        intent = row.get("intent", "").strip()
        is_eligible = relevance == "relevant" and intent in ELIGIBLE_INTENTS
        is_mandatory = relevance == "relevant" and (
            _positive_metric(row.get("clicks", ""), "clicks", row_number)
            or _is_new_page_proposal(row)
        )
        if not (is_eligible or is_mandatory):
            continue
        service_id = row.get("service_id", "").strip()
        query = normalize_query(row.get("query_normalized", ""))
        if not service_id or not query or not intent:
            raise ValueError(f"keyword row {row_number}: selected query requires service_id, query and intent")
        if is_eligible:
            eligible_row_count += 1

        key = (service_id, query, intent)
        candidate = candidates.setdefault(key, _Candidate(service_id, query, intent))
        candidate.eligible = candidate.eligible or is_eligible
        candidate.clicked = candidate.clicked or _positive_metric(
            row.get("clicks", ""), "clicks", row_number
        )
        candidate.new_page_proposal = candidate.new_page_proposal or _is_new_page_proposal(row)
        candidate.broad_frequency = max(
            candidate.broad_frequency,
            _metric(row.get("broad_frequency", ""), "broad_frequency", row_number),
        )
        candidate.phrase_frequency = max(
            candidate.phrase_frequency,
            _metric(row.get("phrase_frequency", ""), "phrase_frequency", row_number),
        )
        candidate.exact_frequency = max(
            candidate.exact_frequency,
            _metric(row.get("exact_frequency", ""), "exact_frequency", row_number),
        )
        candidate.impressions = max(
            candidate.impressions,
            _metric(row.get("impressions", ""), "impressions", row_number),
        )
        candidate.clicks = max(
            candidate.clicks,
            _metric(row.get("clicks", ""), "clicks", row_number),
        )
        candidate.has_local_evidence = candidate.has_local_evidence or (
            row.get("region", "").strip() != "Russia_discovery"
        )
        if is_eligible:
            seed = normalize_query(row.get("seed", "")) or "__unseeded__"
            group = (service_id, seed)
            candidate.groups.add(group)
            group_members.setdefault(group, set()).add(key)

    eligible_candidates = {key for key, candidate in candidates.items() if candidate.eligible}
    group_ids = _group_ids(group_members)
    selections: dict[tuple[tuple[str, str, str], str], set[str]] = {}
    service_heads: dict[str, set[tuple[str, str, str]]] = {}

    for group in sorted(group_members):
        group_candidates = [candidates[key] for key in group_members[group]]
        commercial = [candidate for candidate in group_candidates if candidate.intent in COMMERCIAL_INTENTS]
        if not commercial:
            continue
        group_id = group_ids[group]
        head = min(commercial, key=_rank_key)
        _select(selections, head.key, "desktop", f"commercial_head[{group_id}]")
        service_heads.setdefault(head.service_id, set()).add(head.key)

        price = [candidate for candidate in commercial if _is_price_query(candidate.query)]
        if price:
            _select(selections, min(price, key=_rank_key).key, "desktop", f"price[{group_id}]")
        order = [candidate for candidate in commercial if _is_turnkey_order_query(candidate.query)]
        if order:
            _select(
                selections,
                min(order, key=_rank_key).key,
                "desktop",
                f"turnkey_order[{group_id}]",
            )
        geo = [candidate for candidate in commercial if _is_yaroslavl_query(candidate.query)]
        if geo:
            strongest_geo = min(geo, key=lambda candidate: (_geo_rank(candidate.query), _rank_key(candidate)))
            _select(selections, strongest_geo.key, "desktop", f"yaroslavl_geo[{group_id}]")

    for candidate in candidates.values():
        if candidate.clicked:
            _select(selections, candidate.key, "desktop", "clicked")
        if candidate.new_page_proposal:
            _select(selections, candidate.key, "desktop", "new_page_proposal")

    for service_id in sorted(MOBILE_HEAD_SERVICES):
        heads = [candidates[key] for key in service_heads.get(service_id, set())]
        if heads:
            head = min(heads, key=_rank_key)
            _select(selections, head.key, "mobile", "mobile_head_check")

    ordered = sorted(
        selections,
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2],
            0 if item[1] == "desktop" else 1,
        ),
    )
    queue_rows = tuple(
        SerpQueueRow(
            query_id=f"Q{index:06d}",
            query=candidates[candidate_key].query,
            service_id=candidates[candidate_key].service_id,
            intent=candidates[candidate_key].intent,
            region="Yaroslavl",
            device=device,
            reason="|".join(sorted(selections[(candidate_key, device)], key=_reason_key)),
            status="pending",
        )
        for index, (candidate_key, device) in enumerate(ordered, start=1)
    )
    return SerpQueueBuild(
        rows=queue_rows,
        eligible_row_count=eligible_row_count,
        distinct_candidate_count=len(eligible_candidates),
        tentative_group_count=len(group_members),
    )


def write_representative_queue(input_path: Path, output_path: Path) -> SerpQueueBuild:
    """Read classified keywords and write the exact queue CSV contract."""

    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {
                "query_normalized",
                "service_id",
                "intent",
                "relevance",
                "seed",
                "region",
                "clicks",
            }
            missing = sorted(required - set(reader.fieldnames or ()))
            if missing:
                raise ValueError(f"{input_path.name}: missing columns: {', '.join(missing)}")
            result = build_representative_queue(reader)
    except OSError as exc:
        raise ValueError(f"unable to read classified keywords {input_path}: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row.__dict__ for row in result.rows)
    return result


def cluster_semantics(
    scope_path: Path,
    keywords_path: Path,
    serp_dir: Path,
    serp_output_path: Path,
    clusters_output_path: Path,
    url_map_output_path: Path,
    candidate_map_output_path: Path | None = None,
    ambiguous_pairs_output_path: Path | None = None,
) -> ClusterBuildSummary:
    """Build a deterministic SERP-led architecture and exact-once candidate map."""

    scope = load_scope(scope_path)
    keyword_rows = _load_csv(keywords_path, {"keyword_id", "query_normalized", "service_id", "intent", "relevance"})
    candidates, eligible_row_count = _build_cluster_candidates(keyword_rows)
    frozen_rows = _load_csv(keywords_path.with_name("frozen_collisions.csv"), set(), required_file=True)
    queue_rows = _load_csv(serp_dir / "serp-queue.csv", set(), required_file=False)
    queue_by_id = {row.get("query_id", ""): row for row in queue_rows if row.get("query_id")}
    if len(queue_by_id) != len([row for row in queue_rows if row.get("query_id")]):
        raise ValueError("SERP queue contains duplicate query_id values")
    serp_records, serp_result_rows = _load_serp_records(serp_dir, queue_by_id)
    roles = validate_serp_corpus(queue_rows, serp_records)
    _write_rows(serp_output_path, SERP_RESULT_COLUMNS, serp_result_rows)
    service_urls = {service.service_id: service.current_url for service in scope.services}
    primary_rows = [queue_by_id[query_id] for query_id in roles.primary_query_ids]
    primary_intents = {row["query_id"]: row["intent"] for row in primary_rows}
    primary_service_intents = {
        row["query_id"]: f"{row['service_id']}|{row['intent']}"
        for row in primary_rows
    }
    primary_keys = {
        row["query_id"]: (row["service_id"], normalize_query(row["query"]), row["intent"])
        for row in primary_rows
    }
    unknown_representatives = sorted(set(primary_keys.values()) - set(candidates))
    if unknown_representatives:
        raise ValueError("desktop SERP representatives are absent from the 4,236-candidate universe")

    overlaps: dict[tuple[str, str], int] = {}
    for left_id, right_id in combinations(roles.primary_query_ids, 2):
        left_urls = _organic_page_urls(serp_records[left_id])
        right_urls = _organic_page_urls(serp_records[right_id])
        overlaps[(left_id, right_id)] = overlap_count(left_urls, right_urls)
    ambiguous_pair_rows = _ambiguous_pair_rows(
        overlaps,
        queue_by_id,
        serp_records,
    )
    ambiguous_pairs_output_path = ambiguous_pairs_output_path or clusters_output_path.with_name(
        "serp_ambiguous_pairs.csv"
    )
    _write_rows(ambiguous_pairs_output_path, AMBIGUOUS_PAIR_COLUMNS, ambiguous_pair_rows)
    pending_pair_ids_by_query: dict[str, set[str]] = {}
    for row in ambiguous_pair_rows:
        if row["review_status"] != "pending":
            continue
        for query_id in (row["left_query_id"], row["right_query_id"]):
            pending_pair_ids_by_query.setdefault(query_id, set()).add(row["pair_id"])
    # A shared aggregator can make two different services look identical after
    # query-string removal. Keep the SERP overlap as evidence, but never merge
    # two approved service owners automatically.
    cross_service_overlap_ids: set[str] = set()
    for (left_id, right_id), overlap in overlaps.items():
        if (
            overlap >= 4
            and primary_intents[left_id] == primary_intents[right_id]
            and queue_by_id[left_id]["service_id"] != queue_by_id[right_id]["service_id"]
        ):
            cross_service_overlap_ids.update((left_id, right_id))
    components = complete_link_clusters(
        roles.primary_query_ids,
        primary_service_intents,
        overlaps,
    )
    component_id_by_query: dict[str, str] = {}
    for component in components:
        cluster_id = _stable_identifier("SERP", component)
        for query_id in component:
            component_id_by_query[query_id] = cluster_id

    configured_seeds = _load_configured_seeds(scope_path.with_name("seeds.json"))
    candidate_strata = {
        key: (candidate.service_id, _assign_seed(candidate, configured_seeds[candidate.service_id]), candidate.intent)
        for key, candidate in candidates.items()
    }
    representative_by_candidate = {key: query_id for query_id, key in primary_keys.items()}
    stratum_components: dict[tuple[str, str, str], set[str]] = {}
    for query_id, candidate_key in primary_keys.items():
        component_id = component_id_by_query[query_id]
        stratum_components.setdefault(candidate_strata[candidate_key], set()).add(component_id)

    candidate_rows: list[dict[str, str]] = []
    for candidate_key in sorted(candidates):
        candidate = candidates[candidate_key]
        current_url = service_urls[candidate.service_id]
        representative_ids = sorted(
            query_id
            for query_id, key in primary_keys.items()
            if candidate_strata[key] == candidate_strata[candidate_key]
        )
        if candidate_key in representative_by_candidate:
            query_id = representative_by_candidate[candidate_key]
            cluster_id = component_id_by_query[query_id]
            assignment_method = "direct_serp_representative"
            base_validation = "serp_direct_pending_review"
            base_rationale = "direct SERP representative is evidence only; no page owner is approved"
            base_reviewed = False
        else:
            possible_components = stratum_components.get(candidate_strata[candidate_key], set())
            if len(possible_components) == 1:
                cluster_id = next(iter(possible_components))
                assignment_method = "representative_stratum_projection"
                base_validation = "serp_projected_pending_review"
                base_rationale = (
                    "projected because every stratum representative has one service-bounded SERP component"
                )
                base_reviewed = False
            else:
                cluster_id = _stable_identifier("HOLD", candidate_strata[candidate_key])
                assignment_method = "current_owner_hold"
                base_validation = (
                    "manual_projection_pending" if possible_components else "unrepresented_hold_pending"
                )
                base_rationale = (
                    "current service boundary retained; no unsupported child page or lexical merge created"
                )
                base_reviewed = False
        direct_query_id = representative_by_candidate.get(candidate_key)
        unresolved_pair_ids = sorted(pending_pair_ids_by_query.get(direct_query_id, set()))
        manual_boundary = direct_query_id in cross_service_overlap_ids
        boundary_note = ""
        if manual_boundary:
            boundary_note = (
                "; cross-service aggregator overlap manually split by the approved S1-S8 owner boundary"
            )

        special = route_special_owner(
            candidate.query,
            candidate.intent,
            current_url,
            clicked=candidate.clicked,
        )
        if special is not None:
            cluster_id = (
                "SPECIAL-CALCULATOR"
                if special.target_url.endswith("/kalkuljator-uslug/")
                else "SPECIAL-EXTERNAL-EXCLUSION"
            )
            target_url = special.target_url
            url_action = special.url_action
            assignment_method = "explicit_special_owner"
            validation_status = special.validation_status
            review_status = special.review_status
            reviewer = special.reviewer
            rationale = special.rationale
        elif candidate.intent == "informational":
            target_url = ""
            url_action = "article_candidate"
            if candidate.clicked:
                validation_status = "clicked_informational_article_reviewed"
                review_status = "reviewed"
                reviewer = "codex_task6"
            else:
                validation_status = "article_backlog_pending"
                review_status = "pending"
                reviewer = ""
            rationale = (
                f"{base_rationale}{boundary_note}; informational intent is separated from the "
                "commercial service page and remains an unpublished article backlog candidate"
            )
        elif candidate.intent == "product_only":
            target_url = ""
            url_action = "exclude"
            validation_status = "product_only_excluded"
            review_status = "reviewed"
            reviewer = "codex_task6"
            rationale = (
                f"{base_rationale}{boundary_note}; purchase-only intent has no confirmed works "
                "offer and is excluded from the service URL map"
            )
        else:
            manually_reviewed = base_reviewed or candidate.clicked or manual_boundary
            if unresolved_pair_ids or not manually_reviewed:
                target_url = ""
                url_action = "unresolved"
                validation_status = "serp_pair_pending_review" if unresolved_pair_ids else base_validation
                review_status = "pending"
                reviewer = ""
                unresolved_note = ",".join(unresolved_pair_ids) or "no reviewed cluster page decision"
                rationale = (
                    f"{base_rationale}{boundary_note}; unresolved commercial architecture: "
                    f"{unresolved_note}"
                )
            elif manual_boundary and not base_reviewed:
                target_url = current_url
                url_action = "keep_enhance"
                validation_status = "cross_service_owner_boundary_reviewed"
                review_status = "reviewed"
                reviewer = "codex_task6"
                rationale = (
                    f"{base_rationale}{boundary_note}; existing URL retained and no new URL approved"
                )
            elif candidate.clicked and not base_reviewed:
                target_url = current_url
                url_action = "keep_enhance"
                validation_status = "clicked_current_owner_reviewed"
                review_status = "reviewed"
                reviewer = "codex_task6"
                rationale = (
                    f"{base_rationale}{boundary_note}; existing URL retained and no new URL approved"
                )
            else:
                target_url = current_url
                url_action = "keep_enhance"
                validation_status = base_validation
                review_status = "reviewed"
                reviewer = "codex_task6"
                rationale = (
                    f"{base_rationale}{boundary_note}; existing URL retained and no new URL approved"
                )
        candidate_rows.append(
            {
                "candidate_key": "|".join(candidate_key),
                "service_id": candidate.service_id,
                "query": candidate.query,
                "intent": candidate.intent,
                "cluster_id": cluster_id,
                "representative_query_ids": "|".join(representative_ids),
                "current_url": current_url,
                "target_url": target_url,
                "url_action": url_action,
                "assignment_method": assignment_method,
                "validation_status": validation_status,
                "review_status": review_status,
                "reviewer": reviewer,
                "rationale": rationale,
            }
        )
    if len(candidate_rows) != len(candidates) or len({row["candidate_key"] for row in candidate_rows}) != len(candidates):
        raise ValueError("candidate projection must cover every candidate exactly once")
    candidate_map_output_path = candidate_map_output_path or clusters_output_path.with_name("candidate_cluster_map.csv")
    _write_rows(candidate_map_output_path, CANDIDATE_MAP_COLUMNS, candidate_rows)

    cluster_rows = _cluster_rows_from_assignments(
        candidate_rows,
        candidates,
        primary_keys,
        component_id_by_query,
        overlaps,
        pending_pair_ids_by_query,
    )
    cluster_rows.append(_brand_owner_cluster(queue_by_id, roles.brand_query_ids))
    frozen_start = len(cluster_rows)
    cluster_rows.extend(_frozen_cluster_rows(frozen_rows, frozen_start + 1))
    cluster_rows.sort(key=lambda row: row["cluster_id"])
    _write_rows(clusters_output_path, CLUSTER_COLUMNS, cluster_rows)

    url_map_rows = [
        {
            "map_id": f"M{index:04d}",
            "cluster_id": row["cluster_id"],
            "service_id": row["service_id"],
            "cluster_name": row["cluster_name"],
            "intent": row["intent"],
            "current_url": (
                service_urls.get(row["service_id"], "")
                or (row["target_url"] if row["url_action"] in {"frozen_owner", "keep_special_owner"} else "")
            ),
            "target_url": row["target_url"],
            "url_action": row["url_action"],
            "method": row["method"],
            "evidence": row["evidence"],
            "validation_status": row["validation_status"],
            "confidence": row["confidence"],
            "review_status": row["review_status"],
            "reviewer": row["reviewer"],
            "rationale": row["review_rationale"],
        }
        for index, row in enumerate(cluster_rows, start=1)
    ]
    _write_rows(url_map_output_path, URL_MAP_COLUMNS, url_map_rows)
    return ClusterBuildSummary(
        eligible_row_count=eligible_row_count,
        distinct_candidate_count=len(candidates),
        cluster_count=len(cluster_rows),
        frozen_cluster_count=len(cluster_rows) - frozen_start,
        serp_query_count=len(serp_records),
        serp_result_count=len(serp_result_rows),
        ambiguous_pair_count=len(ambiguous_pair_rows),
    )


def _stable_identifier(prefix: str, parts: Iterable[object]) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:12].upper()}"


def _organic_page_urls(record: Mapping[str, object]) -> list[str]:
    urls: list[str] = []
    for result in record.get("results", []):
        url = str(result["url"])
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").casefold().removeprefix("www.")
        first_segment = parsed.path.strip("/").split("/", 1)[0].casefold()
        if hostname in {"yandex.ru", "ya.ru"} and first_segment in {"images", "maps", "video"}:
            continue
        if hostname.startswith("maps.yandex."):
            continue
        urls.append(url)
    return urls


def _ambiguous_pair_rows(
    overlaps: Mapping[tuple[str, str], int],
    queue_by_id: Mapping[str, Mapping[str, str]],
    records: Mapping[str, Mapping[str, object]],
) -> list[dict[str, str]]:
    """Export same-service manual pairs and all non-split cross-owner pairs."""

    rows: list[dict[str, str]] = []
    for left_id, right_id in sorted(overlaps):
        left = queue_by_id[left_id]
        right = queue_by_id[right_id]
        overlap = overlaps[(left_id, right_id)]
        threshold_decision = decide_cluster(overlap, left["intent"] == right["intent"])
        same_service = left["service_id"] == right["service_id"]
        if same_service and threshold_decision != "manual_review":
            continue
        if not same_service and threshold_decision == "split":
            continue
        left_special = route_special_owner(
            left["query"],
            left["intent"],
            "",
            clicked="clicked" in left["reason"].split("|"),
        )
        right_special = route_special_owner(
            right["query"],
            right["intent"],
            "",
            clicked="clicked" in right["reason"].split("|"),
        )
        shared_special_owner = bool(
            left_special
            and right_special
            and left_special.url_action == right_special.url_action == "keep_special_owner"
            and left_special.target_url == right_special.target_url
        )
        shared_special_exclusion = bool(
            left_special
            and right_special
            and left_special.url_action == right_special.url_action == "exclude"
        )
        left_excluded = left["intent"] == "product_only" or bool(
            left_special and left_special.url_action == "exclude"
        )
        right_excluded = right["intent"] == "product_only" or bool(
            right_special and right_special.url_action == "exclude"
        )
        if shared_special_owner:
            pair_decision = "shared_special_owner"
            owner_action = "hold_shared_special_owner"
            validation_status = "shared_special_owner_reviewed"
            review_status = "reviewed"
            reviewer = "policy_special_owner"
            rationale = (
                "both queries have the same explicit calculator owner; SERP overlap cannot "
                "reassign either query to an S1-S8 service page"
            )
        elif shared_special_exclusion:
            pair_decision = "shared_policy_exclusion"
            owner_action = "retain_shared_exclusion"
            validation_status = "shared_policy_exclusion_reviewed"
            review_status = "reviewed"
            reviewer = "policy_exclusion"
            rationale = (
                "both queries match the reviewed external-noise exclusion policy; no URL owner "
                "or pending service split is created"
            )
        elif left_excluded or right_excluded:
            pair_decision = "policy_exclusion_split"
            owner_action = "retain_exclusion_and_service_assignment"
            validation_status = "policy_exclusion_split_reviewed"
            review_status = "reviewed"
            reviewer = "policy_exclusion"
            rationale = (
                "at least one query has a reviewed exclusion action; the excluded intent remains "
                "separate from the retained service assignment"
            )
        elif same_service:
            pair_decision = threshold_decision
            owner_action = "hold_current_url"
            validation_status = "serp_pair_pending_review"
            review_status = "pending"
            reviewer = ""
            rationale = (
                "same-service SERP pair meets the explicit manual-review threshold; the existing "
                "owner is held and no split or new URL is approved"
            )
        else:
            pair_decision = "owner_boundary_split"
            owner_action = "hold_distinct_service_owners"
            validation_status = "cross_service_owner_boundary_reviewed"
            review_status = "reviewed"
            reviewer = "policy_scope_owner"
            rationale = (
                "cross-service SERP pair meets a merge or manual-review threshold; the approved "
                "S1-S8 service-owner boundary prevents an automatic merge or reassignment"
            )
        left_urls = {canonicalize_serp_url(url) for url in _organic_page_urls(records[left_id])}
        right_urls = {canonicalize_serp_url(url) for url in _organic_page_urls(records[right_id])}
        rows.append(
            {
                "pair_id": _stable_identifier("PAIR", (left_id, right_id)),
                "left_query_id": left_id,
                "right_query_id": right_id,
                "left_query": left["query"],
                "right_query": right["query"],
                "left_service_id": left["service_id"],
                "right_service_id": right["service_id"],
                "left_intent": left["intent"],
                "right_intent": right["intent"],
                "overlap": str(overlap),
                "shared_urls": "|".join(sorted(left_urls & right_urls)),
                "decision": pair_decision,
                "owner_action": owner_action,
                "validation_status": validation_status,
                "review_status": review_status,
                "reviewer": reviewer,
                "rationale": rationale,
            }
        )
    return rows


def _cluster_rows_from_assignments(
    assignments: Sequence[Mapping[str, str]],
    candidates: Mapping[tuple[str, str, str], _Candidate],
    primary_keys: Mapping[str, tuple[str, str, str]],
    component_id_by_query: Mapping[str, str],
    overlaps: Mapping[tuple[str, str], int],
    pending_pair_ids_by_query: Mapping[str, set[str]],
) -> list[dict[str, str]]:
    candidate_by_text_key = {"|".join(key): candidate for key, candidate in candidates.items()}
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for row in assignments:
        grouped.setdefault(row["cluster_id"], []).append(row)
    result: list[dict[str, str]] = []
    for cluster_id, rows in sorted(grouped.items()):
        members = [candidate_by_text_key[row["candidate_key"]] for row in rows]
        head = min(members, key=_rank_key)
        services = sorted({row["service_id"] for row in rows})
        intents = sorted({row["intent"] for row in rows})
        targets = sorted({row["target_url"] for row in rows})
        actions = sorted({row["url_action"] for row in rows})
        representative_ids = sorted(
            query_id
            for query_id, candidate_key in primary_keys.items()
            if component_id_by_query.get(query_id) == cluster_id
        )
        direct_query_ids = {
            query_id
            for query_id, candidate_key in primary_keys.items()
            if "|".join(candidate_key) in {row["candidate_key"] for row in rows}
        }
        pair_scores = [
            overlaps[tuple(sorted((left_id, right_id)))]
            for left_id, right_id in combinations(representative_ids, 2)
        ]
        if pair_scores:
            cohesion = (
                f"complete_link_pairs={len(pair_scores)};min={min(pair_scores)};"
                f"max={max(pair_scores)};mean={sum(pair_scores) / len(pair_scores):.2f}"
            )
        elif representative_ids:
            cohesion = "single_representative"
        else:
            cohesion = "not_represented"
        if cluster_id == "SPECIAL-CALCULATOR":
            intent = "calculator_intent"
            cluster_name = "existing calculator owner"
            cohesion = "auxiliary_owner_evidence"
            method = "explicit_special_owner"
            evidence = (
                "owner_evidence=Q000012,Q000026,Q000031,Q000070;"
                f"candidate_count={len(members)}"
            )
        elif cluster_id == "SPECIAL-EXTERNAL-EXCLUSION":
            intent = "external_noise"
            cluster_name = "reviewed external noise exclusion"
            cohesion = "policy_exclusion"
            method = "explicit_special_owner"
            evidence = f"policy=external_noise;candidate_count={len(members)}"
        else:
            intent = intents[0] if len(intents) == 1 else "mixed_manual"
            cluster_name = f"{head.query} — {intent}"
            method = "complete_link_serp_projection"
            evidence = (
                f"representatives={','.join(representative_ids) or 'none'};"
                f"assignment_methods={','.join(sorted({row['assignment_method'] for row in rows}))}"
            )
        unresolved_pair_ids = sorted(
            {
                pair_id
                for query_id in direct_query_ids
                for pair_id in pending_pair_ids_by_query.get(query_id, set())
            }
        )
        unresolved_serp_pair = bool(unresolved_pair_ids)
        review_status = (
            "reviewed"
            if not unresolved_serp_pair and all(row["review_status"] == "reviewed" for row in rows)
            else "pending"
        )
        reviewers = sorted({row["reviewer"] for row in rows if row["reviewer"]})
        validation_statuses = sorted({row["validation_status"] for row in rows})
        if unresolved_serp_pair:
            validation_statuses.append("serp_pair_pending_review")
            reviewers = []
        target_url = targets[0] if len(targets) == 1 else ""
        url_action = actions[0] if len(actions) == 1 else "owner_conflict"
        rationale = "; ".join(sorted({row["rationale"] for row in rows}))
        if unresolved_serp_pair and intent in COMMERCIAL_INTENTS:
            target_url = ""
            url_action = "unresolved"
            rationale = f"{rationale}; unresolved SERP pairs: {','.join(unresolved_pair_ids)}"
        result.append(
            {
                "cluster_id": cluster_id,
                "service_id": services[0] if len(services) == 1 else "|".join(services),
                "cluster_name": cluster_name,
                "head_query": head.query,
                "query_ids": "|".join(sorted({item for member in members for item in member.keyword_ids})),
                "candidate_count": str(len(members)),
                "intent": intent,
                "geo_scope": _geo_scope(members),
                "broad_frequency": _format_metric(sum(member.broad_frequency for member in members)),
                "phrase_frequency": _format_metric(sum(member.phrase_frequency for member in members)),
                "exact_frequency": _format_metric(sum(member.exact_frequency for member in members)),
                "seasonality": "service_head_24m_dynamics_available",
                "webmaster_impressions": _format_metric(sum(member.impressions for member in members)),
                "webmaster_clicks": _format_metric(sum(member.clicks for member in members)),
                "serp_cohesion": cohesion,
                "target_url": target_url,
                "url_action": url_action,
                "priority": _priority(services[0]) if len(services) == 1 else "manual",
                "confidence": "high" if review_status == "reviewed" else "medium",
                "rationale": rationale,
                "method": method,
                "evidence": evidence,
                "validation_status": "|".join(validation_statuses),
                "review_status": review_status,
                "reviewer": reviewers[0] if len(reviewers) == 1 else "",
                "review_rationale": "; ".join(sorted({row["rationale"] for row in rows})),
            }
        )
    return result


def _brand_owner_cluster(
    queue_by_id: Mapping[str, Mapping[str, str]],
    brand_query_ids: Sequence[str],
) -> dict[str, str]:
    rows = [queue_by_id[query_id] for query_id in brand_query_ids]
    decisions = [
        route_special_owner(row["query"], row["intent"], "", clicked="clicked" in row["reason"].split("|"))
        for row in rows
    ]
    if any(decision is None or decision.target_url != "https://exp76.ru/" for decision in decisions):
        raise ValueError("clicked brand-navigation corpus contains an unresolved homepage owner")
    return {
        "cluster_id": "SPECIAL-BRAND-HOMEPAGE",
        "service_id": "",
        "cluster_name": "clicked exp76 brand navigation",
        "head_query": rows[0]["query"],
        "query_ids": "|".join(brand_query_ids),
        "candidate_count": "0",
        "intent": "brand_navigation",
        "geo_scope": "brand",
        "broad_frequency": "",
        "phrase_frequency": "",
        "exact_frequency": "",
        "seasonality": "not_applicable",
        "webmaster_impressions": "",
        "webmaster_clicks": "",
        "serp_cohesion": "auxiliary_owner_evidence",
        "target_url": "https://exp76.ru/",
        "url_action": "keep_special_owner",
        "priority": "protected",
        "confidence": "high",
        "rationale": "seven clicked brand-navigation QIDs retain the homepage owner",
        "method": "explicit_brand_owner",
        "evidence": f"representatives={','.join(brand_query_ids)}",
        "validation_status": "existing_owner_evidence",
        "review_status": "reviewed",
        "reviewer": "policy_brand_owner",
        "review_rationale": "explicit clicked brand-owner rule",
    }


def _load_csv(
    path: Path,
    required: set[str],
    *,
    required_file: bool = True,
) -> list[dict[str, str]]:
    if not path.is_file():
        if required_file:
            raise ValueError(f"required CSV does not exist: {path}")
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(required - set(reader.fieldnames or ()))
            if missing:
                raise ValueError(f"{path.name}: missing columns: {', '.join(missing)}")
            return list(reader)
    except OSError as exc:
        raise ValueError(f"unable to read CSV {path}: {exc}") from exc


def _write_rows(path: Path, columns: Sequence[str], rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _build_cluster_candidates(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[tuple[str, str, str], _Candidate], int]:
    candidates: dict[tuple[str, str, str], _Candidate] = {}
    eligible_row_count = 0
    for row_number, row in enumerate(rows, start=2):
        intent = row.get("intent", "").strip()
        if row.get("relevance", "").strip() != "relevant" or intent not in ELIGIBLE_INTENTS:
            continue
        eligible_row_count += 1
        service_id = row.get("service_id", "").strip()
        query = normalize_query(row.get("query_normalized", ""))
        if service_id not in {f"S{index}" for index in range(1, 9)} or not query:
            raise ValueError(f"keyword row {row_number}: eligible candidate requires an S1-S8 owner and query")
        key = (service_id, query, intent)
        candidate = candidates.setdefault(key, _Candidate(service_id, query, intent, eligible=True))
        candidate.keyword_ids.add(row.get("keyword_id", "").strip())
        seed = normalize_query(row.get("seed", ""))
        if seed:
            candidate.seeds.add(seed)
        region = row.get("region", "").strip()
        candidate.regions.add(region)
        candidate.has_local_evidence = candidate.has_local_evidence or region != "Russia_discovery"
        candidate.broad_frequency = max(candidate.broad_frequency, _metric(row.get("broad_frequency", ""), "broad_frequency", row_number))
        candidate.phrase_frequency = max(candidate.phrase_frequency, _metric(row.get("phrase_frequency", ""), "phrase_frequency", row_number))
        candidate.exact_frequency = max(candidate.exact_frequency, _metric(row.get("exact_frequency", ""), "exact_frequency", row_number))
        candidate.impressions = max(candidate.impressions, _metric(row.get("impressions", ""), "impressions", row_number))
        candidate.clicks = max(candidate.clicks, _metric(row.get("clicks", ""), "clicks", row_number))
        candidate.clicked = candidate.clicked or candidate.clicks > 0
    if any(not candidate.keyword_ids or "" in candidate.keyword_ids for candidate in candidates.values()):
        raise ValueError("eligible candidates require non-empty keyword_id values")
    return candidates, eligible_row_count


def _load_configured_seeds(path: Path) -> dict[str, tuple[str, ...]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read seeds: {exc}") from exc
    expected = {f"S{index}" for index in range(1, 9)}
    if set(payload) != expected:
        raise ValueError("seeds must define exactly S1-S8")
    return {
        service_id: tuple(normalize_query(seed) for seed in seeds)
        for service_id, seeds in payload.items()
    }


def _load_wordcraft_clusters(directory: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*-dom.csv")):
        for row in _load_csv(path, {"query", "yandex_cluster"}):
            query = normalize_query(row.get("query", ""))
            cluster = normalize_query(row.get("yandex_cluster", ""))
            if query and cluster:
                result.setdefault(query, set()).add(cluster)
    return result


def _assign_seed(candidate: _Candidate, seeds: Sequence[str]) -> str:
    observed = [seed for seed in seeds if seed in candidate.seeds]
    pool = observed or list(seeds)
    return max(pool, key=lambda seed: _seed_score(candidate.query, seed, seeds.index(seed)))


def _seed_score(query: str, seed: str, index: int) -> tuple[float, ...]:
    query_tokens = set(query.split())
    seed_tokens = set(seed.split())
    overlap = len(query_tokens & seed_tokens)
    union = len(query_tokens | seed_tokens) or 1
    return (
        float(seed in query),
        float(overlap),
        overlap / union,
        -abs(len(query_tokens) - len(seed_tokens)),
        -float(index),
    )


def _load_serp_records(
    serp_dir: Path,
    queue_by_id: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, dict[str, object]], list[dict[str, str]]]:
    records: dict[str, dict[str, object]] = {}
    flattened: list[dict[str, str]] = []
    for path in sorted(serp_dir.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ValueError(f"unable to read SERP source {path}: {exc}") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_number}: invalid JSON") from exc
            query_id = str(record.get("query_id", ""))
            if not query_id or query_id in records:
                raise ValueError(f"duplicate or empty SERP query_id: {query_id!r}")
            queue_row = queue_by_id.get(query_id)
            if queue_row is None:
                raise ValueError(f"SERP record {query_id} is absent from the queue")
            for field_name in ("query", "region", "device"):
                if str(record.get(field_name, "")) != queue_row.get(field_name, ""):
                    raise ValueError(f"SERP record {query_id} differs from queue field {field_name}")
            results = record.get("results")
            if not isinstance(results, list):
                raise ValueError(f"SERP record {query_id} results must be an array")
            seen_ranks: set[int] = set()
            clean_results: list[dict[str, object]] = []
            for result in results:
                if not isinstance(result, Mapping):
                    raise ValueError(f"SERP record {query_id} has invalid rank/title")
                rank, url, title, canonical = validate_organic_result(result, query_id)
                if rank in seen_ranks:
                    raise ValueError(f"SERP record {query_id} has invalid rank/title")
                seen_ranks.add(rank)
                clean_results.append({"rank": rank, "url": url, "title": title, "canonical_url": canonical})
                flattened.append(
                    {
                        "query_id": query_id,
                        "query": queue_row["query"],
                        "service_id": queue_row["service_id"],
                        "intent": queue_row["intent"],
                        "region": queue_row["region"],
                        "device": queue_row["device"],
                        "checked_at": str(record.get("checked_at", "")),
                        "rank": str(rank),
                        "url": url,
                        "canonical_url": canonical,
                        "title": title,
                        "source_file": path.name,
                        "method": "live_yandex_organic",
                    }
                )
            record["results"] = clean_results
            records[query_id] = record
    flattened.sort(key=lambda row: (row["query_id"], int(row["rank"])))
    return records, flattened


def _queue_ids_by_candidate(
    queue_rows: Sequence[Mapping[str, str]],
    serp_records: Mapping[str, Mapping[str, object]],
) -> dict[tuple[str, str, str], set[str]]:
    result: dict[tuple[str, str, str], set[str]] = {}
    for row in queue_rows:
        query_id = row.get("query_id", "")
        if query_id not in serp_records:
            continue
        key = (row.get("service_id", ""), normalize_query(row.get("query", "")), row.get("intent", ""))
        result.setdefault(key, set()).add(query_id)
    return result


def _live_overlap_pairs(
    query_ids: Sequence[str],
    records: Mapping[str, Mapping[str, object]],
) -> list[tuple[str, str, int, str]]:
    pairs: list[tuple[str, str, int, str]] = []
    for left_id, right_id in combinations(query_ids, 2):
        left_urls = [str(item["url"]) for item in records[left_id]["results"]]
        right_urls = [str(item["url"]) for item in records[right_id]["results"]]
        overlap = overlap_count(left_urls, right_urls)
        pairs.append((left_id, right_id, overlap, decide_cluster(overlap, True)))
    return pairs


def _cluster_evidence(
    seed: str,
    members: Sequence[_Candidate],
    captured_ids: Sequence[str],
    live_pairs: Sequence[tuple[str, str, int, str]],
) -> str:
    wordcraft_labels = sorted({label for member in members for label in member.wordcraft_clusters})
    parts = [
        f"seed={seed}",
        f"candidate_count={len(members)}",
        f"clicked_candidates={sum(member.clicked for member in members)}",
        f"city_variant_candidates={sum(_has_city_variant(member.query) for member in members)}",
        f"wordcraft_cluster_count={len(wordcraft_labels)}",
        f"captured_queries={','.join(captured_ids) if captured_ids else 'none'}",
    ]
    if wordcraft_labels:
        parts.append(f"wordcraft_sample={' / '.join(wordcraft_labels[:3])}")
    parts.extend(
        f"{left}~{right}:overlap={overlap}:decision={decision}"
        for left, right, overlap, decision in live_pairs
    )
    return ";".join(parts)


def _provisional_url_decision(intent: str, current_url: str) -> tuple[str, str]:
    if intent in COMMERCIAL_INTENTS:
        return current_url, "keep_enhance"
    if intent == "informational":
        return "", "article_candidate"
    return "", "exclude"


def _cluster_rationale(url_action: str, validation_status: str) -> str:
    if url_action == "keep_enhance":
        return f"existing URL retained by default; architecture is provisional ({validation_status})"
    if url_action == "article_candidate":
        return "informational intent kept separate; article target remains provisional pending SERP"
    return "product-only intent excluded from the service URL map after manual review"


def _review_rationale(
    service_id: str,
    members: Sequence[_Candidate],
    live_pairs: Sequence[tuple[str, str, int, str]],
    validation_status: str,
) -> str:
    details = []
    clicked_count = sum(member.clicked for member in members)
    if clicked_count:
        details.append(f"clicked candidates reviewed={clicked_count}")
    if any(_has_city_variant(member.query) for member in members):
        details.append("city variants retained in the existing owner; no substitution-only city page")
    if live_pairs:
        decisions = ",".join(sorted({pair[3] for pair in live_pairs}))
        details.append(f"captured S1 pair decisions reviewed={decisions}")
        details.append("split/manual signals deferred pending representative SERP; no new URL")
    else:
        details.append(f"provisional {service_id} owner reviewed; no live overlap claimed")
    details.append(validation_status)
    return "; ".join(details)


def _has_city_variant(query: str) -> bool:
    city_stems = ("ярославл", "рыбинск", "тутаев", "углич", "переславл")
    return any(token.startswith(city_stems) for token in query.split())


def _geo_scope(members: Sequence[_Candidate]) -> str:
    regions = {region for member in members for region in member.regions if region}
    if any(region != "Russia_discovery" for region in regions) or any(member.has_local_evidence for member in members):
        return "Yaroslavl_and_oblast"
    return "Russia_discovery_only"


def _priority(service_id: str) -> str:
    if service_id in {"S5", "S8"}:
        return "P1"
    if service_id in {"S2", "S3", "S4"}:
        return "P2"
    return "P3"


def _format_metric(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.4f}".rstrip("0").rstrip(".")


def _frozen_cluster_rows(rows: Sequence[Mapping[str, str]], start_index: int) -> list[dict[str, str]]:
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for row in rows:
        owner = row.get("owner_url", "").strip()
        if owner:
            grouped.setdefault(owner, []).append(row)
    result: list[dict[str, str]] = []
    for offset, (owner, owner_rows) in enumerate(sorted(grouped.items()), start=0):
        related_services = sorted({row.get("service_id", "") for row in owner_rows if row.get("service_id")})
        query_ids = sorted({row.get("keyword_id", "") for row in owner_rows if row.get("keyword_id")})
        clicked = sum(_metric(row.get("clicks", ""), "clicks", index) for index, row in enumerate(owner_rows, start=2))
        impressions = sum(_metric(row.get("impressions", ""), "impressions", index) for index, row in enumerate(owner_rows, start=2))
        slug = urlsplit(owner).path.strip("/").split("/")[-1]
        result.append(
            {
                "cluster_id": _stable_identifier("FROZEN", (owner,)),
                "service_id": "",
                "cluster_name": f"frozen owner — {slug}",
                "head_query": normalize_query(owner_rows[0].get("query_normalized", "")),
                "query_ids": "|".join(query_ids),
                "candidate_count": str(len({normalize_query(row.get("query_normalized", "")) for row in owner_rows})),
                "intent": "frozen_collision",
                "geo_scope": "existing_frozen_scope",
                "broad_frequency": "",
                "phrase_frequency": "",
                "exact_frequency": "",
                "seasonality": "not_recomputed",
                "webmaster_impressions": _format_metric(impressions),
                "webmaster_clicks": _format_metric(clicked),
                "serp_cohesion": "not_applicable",
                "target_url": owner,
                "url_action": "frozen_owner",
                "priority": "protected",
                "confidence": "high",
                "rationale": "immutable owner retained; no new destination allowed",
                "method": "frozen_classification_owner",
                "evidence": f"rows={len(owner_rows)};related_services={','.join(related_services) or 'direct_frozen'}",
                "validation_status": "frozen_owner_locked",
                "review_status": "reviewed",
                "reviewer": "codex_task6",
                "review_rationale": "reviewed against the six immutable category owners",
            }
        )
    return result


def _group_ids(
    group_members: Mapping[tuple[str, str], set[tuple[str, str, str]]],
) -> dict[tuple[str, str], str]:
    counters: dict[str, int] = {}
    identifiers: dict[tuple[str, str], str] = {}
    for group in sorted(group_members):
        service_id = group[0]
        counters[service_id] = counters.get(service_id, 0) + 1
        identifiers[group] = f"{service_id}-G{counters[service_id]:02d}"
    return identifiers


def _select(
    selections: dict[tuple[tuple[str, str, str], str], set[str]],
    candidate_key: tuple[str, str, str],
    device: str,
    reason: str,
) -> None:
    selections.setdefault((candidate_key, device), set()).add(reason)


def _rank_key(candidate: _Candidate) -> tuple[object, ...]:
    return (
        -int(candidate.has_local_evidence),
        -candidate.broad_frequency,
        -candidate.phrase_frequency,
        -candidate.exact_frequency,
        -candidate.impressions,
        -candidate.clicks,
        len(candidate.query.split()),
        candidate.query,
        candidate.intent,
    )


def _metric(value: str | None, name: str, row_number: int) -> float:
    if value is None or not value.strip():
        return 0.0
    try:
        parsed = float(value.replace(" ", "").replace(",", "."))
    except ValueError as exc:
        raise ValueError(f"keyword row {row_number}: {name} must be numeric: {value!r}") from exc
    if parsed < 0:
        raise ValueError(f"keyword row {row_number}: {name} must be non-negative")
    return parsed


def _positive_metric(value: str | None, name: str, row_number: int) -> bool:
    return _metric(value, name, row_number) > 0


def _is_price_query(query: str) -> bool:
    return bool(set(query.split()) & _PRICE_TOKENS)


def _is_turnkey_order_query(query: str) -> bool:
    tokens = query.split()
    return "под ключ" in query or bool(set(tokens) & _ORDER_TOKENS)


def _is_yaroslavl_query(query: str) -> bool:
    return any(token.startswith("ярославл") for token in query.split())


def _geo_rank(query: str) -> int:
    return 0 if "ярославль" in query.split() else 1


def _is_new_page_proposal(row: Mapping[str, str]) -> bool:
    decision = row.get("final_decision", "").strip().casefold()
    if decision in _NEW_PAGE_DECISIONS:
        return True
    reason_tokens = {
        token.strip().casefold()
        for token in re.split(r"[|;,]", row.get("review_reason", ""))
        if token.strip()
    }
    return bool(reason_tokens & _NEW_PAGE_DECISIONS)


def _reason_key(reason: str) -> tuple[int, str]:
    prefix = reason.split("[", 1)[0]
    order = {
        "clicked": 0,
        "new_page_proposal": 1,
        "commercial_head": 2,
        "price": 3,
        "turnkey_order": 4,
        "yaroslavl_geo": 5,
        "mobile_head_check": 6,
    }
    return order.get(prefix, 99), reason
