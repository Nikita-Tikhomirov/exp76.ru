"""Deterministic SERP review for the 92-page expanded service architecture.

The review is deliberately evidence-first: immutable queues and source manifests
are verified before any ruling is produced.  Every queued candidate gets one
primary probe, an optional targeted second probe, exact legacy-hub, same-role
sibling, and cross-service overlaps.  Primary and targeted probes remain equal
inputs to fail-closed rulings; this candidate ledger is never production approval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import unquote, urlsplit

from .expanded_architecture import (
    all_expanded_pages,
)
from .serp import canonicalize_serp_url, validate_organic_result


HUB_QUERY_IDS: Mapping[str, str] = {
    "S1": "Q000019",
    "S2": "Q000040",
    "S3": "Q000063",
    "S4": "Q000078",
    "S5": "Q000098",
    "S6": "Q000104",
    "S7": "Q000109",
    "S8": "Q000117",
}

FORMAT_NAMES = (
    "article_guide",
    "local_directory",
    "marketplace_directory",
    "product_catalog",
    "service_landing",
    "topic_landing",
)
RELEVANCE_NAMES = ("irrelevant", "product", "relevant")

REVIEW_COLUMNS = (
    "destination_id",
    "service_id",
    "page_role",
    "title",
    "slug",
    "offer_status",
    "primary_query_id",
    "primary_query",
    "primary_format_counts",
    "primary_relevance_counts",
    "primary_role_support",
    "primary_legacy_hub_overlap",
    "targeted_query_id",
    "targeted_query",
    "targeted_format_counts",
    "targeted_relevance_counts",
    "targeted_role_support",
    "targeted_legacy_hub_overlap",
    "legacy_hub_query_id",
    "max_legacy_hub_query_id",
    "max_legacy_hub_overlap",
    "max_sibling_destination_id",
    "max_sibling_left_query_id",
    "max_sibling_right_query_id",
    "max_sibling_overlap",
    "max_cross_service_destination_id",
    "max_cross_service_service_id",
    "max_cross_service_left_query_id",
    "max_cross_service_right_query_id",
    "max_cross_service_overlap",
    "manual_ruling_ids",
    "manual_ruling",
    "manual_ruling_evidence_refs",
    "final_decision",
    "final_status",
    "ruling_id",
    "merge_target",
    "rationale",
    "boundary",
    "business_evidence",
    "semantic_evidence",
    "evidence_refs",
    "review_status",
    "reviewer",
)

QUEUE_COLUMNS = (
    "query_id",
    "query",
    "service_id",
    "intent",
    "region",
    "device",
    "destination_id",
    "reason",
)

COMMERCIAL_FORMATS = frozenset(
    {"local_directory", "marketplace_directory", "service_landing"}
)
INFORMATIONAL_FORMATS = frozenset({"article_guide", "topic_landing"})
MIN_FORMAT_SUPPORT = 5
HIGH_OVERLAP = 4


@dataclass(frozen=True)
class Probe:
    query_id: str
    query: str
    service_id: str
    destination_id: str
    relative_path: str
    record: Mapping[str, object]
    canonical_urls: frozenset[str]
    format_counts: Mapping[str, int]
    relevance_counts: Mapping[str, int]
    role_support: int


@dataclass(frozen=True)
class CandidateMetadata:
    destination_id: str
    service_id: str
    page_role: str
    title: str
    slug: str
    offer_status: str
    boundary: str
    business_evidence: str
    semantic_evidence: str


@dataclass(frozen=True)
class ManualPairRuling:
    ruling_id: str
    left_destination_id: str
    right_destination_id: str
    decision: str
    rationale: str
    evidence_query_ids: tuple[str, ...]


MANUAL_PAIR_RULINGS = (
    ManualPairRuling(
        "M001",
        "S1-CHILD-RELIEF",
        "S5-CHILD-VERTICAL",
        "separate_with_boundary",
        "S1 owns the vertical-planning design document; S5 owns physical grading and earthwork. "
        "The cross-service SERP overlap is acknowledged and the implementation boundary is mandatory.",
        ("Q000159", "Q000248", "Q000203"),
    ),
    ManualPairRuling(
        "M002",
        "S2-CHILD-INITIAL-CARE",
        "S4-CHILD-LAWN-CARE",
        "reject_left_keep_right",
        "The proposed S2 initial-care query is unstable and its targeted SERP is dominated by "
        "GAZon Next vehicle-service results. Ongoing lawn care remains with S4.",
        ("Q000171", "Q000253", "Q000194"),
    ),
    ManualPairRuling(
        "M003",
        "S2-CHILD-SOIL",
        "S5-CHILD-FOR-LAWN",
        "separate_with_boundary",
        "S2 is limited to agronomic soil preparation inside lawn construction; S5 owns physical "
        "grading and elevation preparation for a lawn. Copy and internal links must state that split.",
        ("Q000169", "Q000251", "Q000207"),
    ),
    ManualPairRuling(
        "M004",
        "S7-ARTICLE-SCHEME",
        "S7-ARTICLE-DIY",
        "merge_left_into_right",
        "The scheme and DIY-guide probes overlap on seven exact canonical URLs and answer one "
        "planning task; retain one article with the scheme as a section.",
        ("Q000231", "Q000229"),
    ),
    ManualPairRuling(
        "M005",
        "S8-ARTICLE-DIAMETER",
        "S8-ARTICLE-PIPE",
        "merge_left_into_right",
        "Pipe choice and pipe diameter overlap on seven exact canonical URLs; diameter is a section "
        "of the pipe-selection article, not a second destination.",
        ("Q000244", "Q000242"),
    ),
)

MANUAL_DISPOSITIONS: Mapping[str, tuple[str, str, str, str]] = {
    "S2-CHILD-INITIAL-CARE": (
        "reject",
        "rejected",
        "M002_REJECT_IRRELEVANT_SERP",
        "",
    ),
    "S7-ARTICLE-SCHEME": (
        "merge",
        "merged",
        "M004_MERGE_DUPLICATE_ARTICLE",
        "S7-ARTICLE-DIY",
    ),
    "S8-ARTICLE-DIAMETER": (
        "merge",
        "merged",
        "M005_MERGE_DUPLICATE_ARTICLE",
        "S8-ARTICLE-PIPE",
    ),
    "S3-CHILD-DECIDUOUS": ("reject", "rejected", "D002_DROP_DECIDUOUS", ""),
    "S4-CHILD-SEASONAL": ("reject", "rejected", "D003_DROP_SEASONAL", ""),
    "S5-CHILD-SOIL": ("reject", "rejected", "D004_DROP_IMPORTED_SOIL", ""),
    "S5-CHILD-FOR-LAWN": ("reject", "rejected", "D005_DROP_LAWN_GRADING", ""),
    "S6-CHILD-SLOPE": ("reject", "rejected", "D006_DROP_SLOPE", ""),
    "S6-CHILD-BLOCKS": ("reject", "rejected", "D007_DROP_BLOCKS", ""),
    "S7-CHILD-PATHS": ("reject", "rejected", "D008_DROP_PATH_LIGHTING", ""),
    "S7-CHILD-SECURITY": ("reject", "rejected", "D009_DROP_SECURITY_LIGHTING", ""),
    "S8-CHILD-BASE": ("reject", "rejected", "D010_DROP_ENTRANCE_BASE", ""),
    "S8-CHILD-HEADWALLS": ("reject", "rejected", "D011_DROP_HEADWALLS", ""),
}

MANUAL_DISPOSITION_DETAILS: Mapping[str, tuple[str, str, tuple[str, ...]]] = {
    "S2-CHILD-INITIAL-CARE": (
        "M002",
        "Reject the unstable S2 child; targeted evidence is dominated by the GAZon Next entity collision.",
        ("Q000171", "Q000253", "Q000194"),
    ),
    "S7-ARTICLE-SCHEME": (
        "M004",
        "Merge the lighting scheme into the DIY planning guide.",
        ("Q000231", "Q000229"),
    ),
    "S8-ARTICLE-DIAMETER": (
        "M005",
        "Merge pipe diameter into the pipe-selection guide.",
        ("Q000244", "Q000242"),
    ),
    "S3-CHILD-DECIDUOUS": (
        "D002",
        "Drop the generic deciduous-tree split; a hedge service is the evidence-backed replacement candidate and needs a new probe.",
        ("Q000179",),
    ),
    "S4-CHILD-SEASONAL": (
        "D003",
        "Drop the broad seasonal child; it does not establish a sufficiently narrow commercial owner.",
        ("Q000196",),
    ),
    "S5-CHILD-SOIL": (
        "D004",
        "Drop imported-soil supply from the production service silo.",
        ("Q000206",),
    ),
    "S5-CHILD-FOR-LAWN": (
        "D005",
        "Drop the lawn-specific grading child; its ownership collides with S2 soil preparation.",
        ("Q000207", "Q000169", "Q000251"),
    ),
    "S6-CHILD-SLOPE": (
        "D006",
        "Drop the condition-based slope split; replace capacity with the explicit gabion offer after a new probe.",
        ("Q000213", "Q000254"),
    ),
    "S6-CHILD-BLOCKS": (
        "D007",
        "Drop the blocks material split because its stored SERPs strongly overlap other wall materials.",
        ("Q000216", "Q000257"),
    ),
    "S7-CHILD-PATHS": (
        "D008",
        "Drop path lighting as a standalone child; retain it as scope inside installation or landscape lighting.",
        ("Q000225", "Q000260"),
    ),
    "S7-CHILD-SECURITY": (
        "D009",
        "Drop security lighting as a standalone child; use the already published holiday-lighting owner instead.",
        ("Q000228", "Q000263"),
    ),
    "S8-CHILD-BASE": (
        "D010",
        "Drop the generic base split; it is a construction stage rather than an independent service destination.",
        ("Q000236", "Q000265"),
    ),
    "S8-CHILD-HEADWALLS": (
        "D011",
        "Drop the headwalls split; the offer is unconfirmed and the query has product contamination.",
        ("Q000239", "Q000268"),
    ),
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"CSV has no header: {path}")
            return list(reader)
    except OSError as exc:
        raise ValueError(f"unable to read CSV {path}: {exc}") from exc


def _format_counts_json(counts: Mapping[str, int]) -> str:
    return json.dumps(
        {name: int(counts.get(name, 0)) for name in FORMAT_NAMES},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _relevance_counts_json(counts: Mapping[str, int]) -> str:
    return json.dumps(
        {name: int(counts.get(name, 0)) for name in RELEVANCE_NAMES},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def classify_result_format(url: str, title: str) -> str:
    """Classify one organic result with a fixed, inspectable rule order."""

    canonical = canonicalize_serp_url(url)
    parsed = urlsplit(canonical)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    lowered_title = title.casefold()
    if any(token in host for token in ("avito.", "profi.", "uslugi.yandex", "youdo.")):
        return "marketplace_directory"
    if any(token in host for token in ("2gis.", "zoon.", "yell.", "orgpage.")):
        return "local_directory"
    if any(token in host for token in ("ozon.", "market.yandex", "leroy", "vseinstrumenti")):
        return "product_catalog"
    if any(token in path for token in ("/blog", "/article", "/stati", "/wiki")) or any(
        token in lowered_title
        for token in ("как сделать", "своими руками", "инструкция", "схема", "советы")
    ):
        return "article_guide"
    if any(token in lowered_title for token in ("купить", "продажа", "товар")):
        return "product_catalog"
    if any(
        token in lowered_title
        for token in ("услуги", "под ключ", "монтаж", "устройство", "заказать", "работы")
    ):
        return "service_landing"
    return "topic_landing"


def classify_result_relevance(
    service_id: str,
    destination_id: str,
    url: str,
    title: str,
    result_format: str,
) -> str:
    """Reject known entity collisions before applying a page-format ruling."""

    haystack = f"{title.casefold()} {unquote(url).casefold()}"
    automotive_gazon_tokens = (
        "газон next",
        "газон некст",
        "gazon next",
        "gazon-next",
        "яргазонсервис",
        "yargazonservis",
        "автосервис",
        "автоцентр",
        "gaz.yarkamp",
        "ремонт-техники",
        "ремонт техники",
        "запчасти yamz",
    )
    if service_id == "S2" and any(token in haystack for token in automotive_gazon_tokens):
        return "irrelevant"
    if result_format == "product_catalog":
        return "product"
    return "relevant"


def _manifest_entries(manifest_path: Path) -> dict[str, Mapping[str, object]]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read source manifest {manifest_path}: {exc}") from exc
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        raise ValueError(f"source manifest has no files array: {manifest_path}")
    entries: dict[str, Mapping[str, object]] = {}
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"invalid source manifest entry: {manifest_path}")
        relative_path = str(entry["path"])
        if relative_path in entries:
            raise ValueError(f"duplicate source manifest path: {relative_path}")
        entries[relative_path] = entry
    return entries


def _validate_manifest(
    manifest_path: Path,
    required_paths: Sequence[str],
    *,
    exact_paths: bool,
) -> None:
    entries = _manifest_entries(manifest_path)
    required = set(required_paths)
    if exact_paths and set(entries) != required:
        missing = sorted(required - set(entries))
        extra = sorted(set(entries) - required)
        raise ValueError(f"manifest file-set mismatch: missing={missing}; extra={extra}")
    missing = sorted(required - set(entries))
    if missing:
        raise ValueError(f"manifest is missing required files: {missing}")
    root = manifest_path.parent.resolve()
    for relative_path in sorted(required if not exact_paths else entries):
        entry = entries[relative_path]
        target = (root / relative_path).resolve()
        if root != target and root not in target.parents:
            raise ValueError(f"manifest path escapes evidence root: {relative_path}")
        if not target.is_file():
            raise ValueError(f"manifest evidence file does not exist: {relative_path}")
        data = target.read_bytes()
        try:
            byte_count = int(entry.get("byte_count", -1))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"manifest byte count is invalid: {relative_path}") from exc
        if len(data) != byte_count:
            raise ValueError(f"manifest byte-count mismatch: {relative_path}")
        digest = hashlib.sha256(data).hexdigest()
        if digest != str(entry.get("sha256", "")).casefold():
            raise ValueError(f"manifest hash mismatch: {relative_path}")


def _expanded_manifest_paths(query_ids: Sequence[str]) -> tuple[str, ...]:
    paths = ["serp-queue.csv"]
    for query_id in query_ids:
        paths.extend(
            (
                f"yandex-api-{query_id}-operation.json",
                f"yandex-api-{query_id}.jsonl",
            )
        )
    return tuple(paths)


def _validate_stored_queue(
    rows: Sequence[Mapping[str, str]],
    *,
    label: str,
    start_query_number: int,
    expected_count: int,
    primary_destinations: frozenset[str] | None = None,
) -> None:
    expected_query_ids = [
        f"Q{number:06d}"
        for number in range(start_query_number, start_query_number + expected_count)
    ]
    if len(rows) != expected_count or [row.get("query_id", "") for row in rows] != expected_query_ids:
        raise ValueError(
            f"{label} queue mismatch: expected {expected_count} sequential rows from "
            f"Q{start_query_number:06d}"
        )
    destinations = [row.get("destination_id", "") for row in rows]
    if any(set(row) != set(QUEUE_COLUMNS) for row in rows):
        raise ValueError(f"{label} queue mismatch: unexpected columns")
    if any(not destination for destination in destinations) or len(set(destinations)) != len(destinations):
        raise ValueError(f"{label} queue mismatch: destination ids must be non-empty and unique")
    queries = [" ".join(row.get("query", "").casefold().split()) for row in rows]
    if any(not query for query in queries) or len(set(queries)) != len(queries):
        raise ValueError(f"{label} queue mismatch: queries must be non-empty and unique")
    expected_reason_prefix = "expanded_representative" if label == "primary" else "expanded_second_probe"
    for row in rows:
        destination_id = row["destination_id"]
        if row["service_id"] not in HUB_QUERY_IDS:
            raise ValueError(f"{label} queue mismatch: invalid service for {destination_id}")
        if row["region"] != "Yaroslavl" or row["device"] != "desktop":
            raise ValueError(f"{label} queue mismatch: unsupported locale/device for {destination_id}")
        if row["reason"] != f"{expected_reason_prefix}[{destination_id}]":
            raise ValueError(f"{label} queue mismatch: invalid reason for {destination_id}")
        if label == "targeted" and row["intent"] != "transactional":
            raise ValueError(f"{label} queue mismatch: targeted probe must be transactional")
        if label == "primary" and row["intent"] not in {"transactional", "informational"}:
            raise ValueError(f"{label} queue mismatch: invalid intent for {destination_id}")
    if primary_destinations is not None and not set(destinations) <= primary_destinations:
        raise ValueError(f"{label} queue mismatch: targeted destination has no primary probe")


def _candidate_metadata(primary_queue: Sequence[Mapping[str, str]]) -> tuple[CandidateMetadata, ...]:
    registry = {page.destination_id: page for page in all_expanded_pages()}
    metadata: list[CandidateMetadata] = []
    for row in primary_queue:
        destination_id = row["destination_id"]
        page = registry.get(destination_id)
        queue_role = "article" if row["intent"] == "informational" else "child_service"
        if page is not None:
            if page.service_id != row["service_id"] or page.page_role != queue_role:
                raise ValueError(f"registry/primary queue identity mismatch: {destination_id}")
            metadata.append(
                CandidateMetadata(
                    destination_id=page.destination_id,
                    service_id=page.service_id,
                    page_role=page.page_role,
                    title=page.title,
                    slug=page.slug,
                    offer_status=page.offer_status,
                    boundary=page.boundary,
                    business_evidence=page.business_evidence,
                    semantic_evidence=page.semantic_evidence,
                )
            )
            continue
        metadata.append(
            CandidateMetadata(
                destination_id=destination_id,
                service_id=row["service_id"],
                page_role=queue_role,
                title=destination_id,
                slug="",
                offer_status="removed_from_registry",
                boundary="Removed candidate: no standalone production URL may be published.",
                business_evidence="not_applicable:removed_candidate",
                semantic_evidence=f"raw_queue:{row['query_id']}",
            )
        )
    return tuple(metadata)


def _read_matching_jsonl(path: Path, query_id: str) -> Mapping[str, object]:
    matches: list[Mapping[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"unable to read SERP evidence {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL record {path}:{line_number}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"SERP JSONL record is not an object: {path}:{line_number}")
        if payload.get("query_id") == query_id:
            matches.append(payload)
    if len(matches) != 1:
        raise ValueError(f"SERP evidence must contain query {query_id} exactly once: {path}")
    return matches[0]


def _validate_record(
    record: Mapping[str, object],
    *,
    query_id: str,
    query: str,
    region: str,
    device: str,
    service_id: str,
    destination_id: str,
    intent: str,
    source: str,
) -> tuple[frozenset[str], Mapping[str, int], Mapping[str, int], int]:
    expected_keys = {"query_id", "query", "region", "device", "checked_at", "results"}
    if set(record) != expected_keys:
        raise ValueError(f"SERP record has unexpected fields: {source}")
    for field, expected in (
        ("query_id", query_id),
        ("query", query),
        ("region", region),
        ("device", device),
    ):
        if record.get(field) != expected:
            raise ValueError(f"SERP record/queue mismatch for {field}: {source}")
    results = record.get("results")
    if not isinstance(results, list) or len(results) != 10:
        raise ValueError(f"SERP record is not an exact top ten: {source}")
    ranks: list[int] = []
    canonical_urls: set[str] = set()
    formats: Counter[str] = Counter()
    relevance: Counter[str] = Counter()
    role_support = 0
    accepted_formats = COMMERCIAL_FORMATS if intent != "informational" else INFORMATIONAL_FORMATS
    for result in results:
        if not isinstance(result, dict) or set(result) != {"rank", "url", "title"}:
            raise ValueError(f"SERP result has unexpected fields: {source}")
        rank, url, title, canonical = validate_organic_result(result, source)
        ranks.append(rank)
        canonical_urls.add(canonical)
        result_format = classify_result_format(url, title)
        result_relevance = classify_result_relevance(
            service_id,
            destination_id,
            url,
            title,
            result_format,
        )
        formats[result_format] += 1
        relevance[result_relevance] += 1
        if result_relevance == "relevant" and result_format in accepted_formats:
            role_support += 1
    if ranks != list(range(1, 11)):
        raise ValueError(f"SERP ranks are not exactly 1..10: {source}")
    return (
        frozenset(canonical_urls),
        {name: formats[name] for name in FORMAT_NAMES},
        {name: relevance[name] for name in RELEVANCE_NAMES},
        role_support,
    )


def _load_probe(
    data_root: Path,
    queue_row: Mapping[str, str],
    directory_name: str,
) -> Probe:
    query_id = queue_row["query_id"]
    relative_path = f"raw/{directory_name}/yandex-api-{query_id}.jsonl"
    path = data_root / relative_path
    record = _read_matching_jsonl(path, query_id)
    canonical_urls, formats, relevance, role_support = _validate_record(
        record,
        query_id=query_id,
        query=queue_row["query"],
        region=queue_row["region"],
        device=queue_row["device"],
        service_id=queue_row["service_id"],
        destination_id=queue_row["destination_id"],
        intent=queue_row["intent"],
        source=relative_path,
    )
    return Probe(
        query_id=query_id,
        query=queue_row["query"],
        service_id=queue_row["service_id"],
        destination_id=queue_row["destination_id"],
        relative_path=relative_path,
        record=record,
        canonical_urls=canonical_urls,
        format_counts=formats,
        relevance_counts=relevance,
        role_support=role_support,
    )


def _load_legacy_probe(
    data_root: Path,
    queue_row: Mapping[str, str],
) -> Probe:
    query_id = queue_row["query_id"]
    serp_root = data_root / "raw" / "serp"
    direct = serp_root / f"yandex-api-{query_id}.jsonl"
    if direct.exists():
        path = direct
        record = _read_matching_jsonl(path, query_id)
    else:
        found: list[tuple[Path, Mapping[str, object]]] = []
        for candidate in sorted(serp_root.glob("yandex-organic-*.jsonl")):
            try:
                record = _read_matching_jsonl(candidate, query_id)
            except ValueError as exc:
                if "must contain query" not in str(exc):
                    raise
                continue
            found.append((candidate, record))
        if len(found) != 1:
            raise ValueError(f"legacy SERP query {query_id} must have exactly one raw source")
        path, record = found[0]
    relative_path = path.relative_to(data_root).as_posix()
    canonical_urls, formats, relevance, role_support = _validate_record(
        record,
        query_id=query_id,
        query=queue_row["query"],
        region=queue_row["region"],
        device=queue_row["device"],
        service_id=queue_row["service_id"],
        destination_id="",
        intent=queue_row["intent"],
        source=relative_path,
    )
    return Probe(
        query_id=query_id,
        query=queue_row["query"],
        service_id=queue_row["service_id"],
        destination_id="",
        relative_path=relative_path,
        record=record,
        canonical_urls=canonical_urls,
        format_counts=formats,
        relevance_counts=relevance,
        role_support=role_support,
    )


def _final_ruling(
    *,
    destination_id: str,
    page_role: str,
    offer_status: str,
    probes: Sequence[Probe],
    hub_overlap: int,
    sibling_overlap: int,
    cross_service_overlap: int,
    cross_service_destination_id: str,
    manual_rulings: Sequence[ManualPairRuling],
) -> tuple[str, str, str, str, str]:
    """Return decision, status, rule id and a short rule explanation."""

    keep_decision = "keep_child" if page_role == "child_service" else "keep_article"
    if destination_id in MANUAL_DISPOSITIONS:
        decision, status, ruling_id, merge_target = MANUAL_DISPOSITIONS[destination_id]
        return (
            decision,
            status,
            ruling_id,
            merge_target,
            "An explicit manual destination ruling overrides automatic promotion.",
        )
    if offer_status == "removed_from_registry":
        return (
            "reject",
            "rejected",
            "R0_REMOVED_FROM_REGISTRY",
            "",
            "The candidate is absent from the active registry and cannot be promoted from stale SERP evidence.",
        )
    if offer_status == "needs_business_confirmation":
        return (
            "needs_review",
            "blocked_business_confirmation",
            "R1_BUSINESS_CONFIRMATION_REQUIRED",
            "",
            "SERP demand cannot prove that the company sells this exact scoped service.",
        )
    if max(probe.relevance_counts["irrelevant"] for probe in probes) >= 3:
        return (
            "needs_review",
            "blocked_serp_relevance",
            "R2_IRRELEVANT_SERP_CONTAMINATION",
            "",
            "At least one stored probe contains three or more explicitly irrelevant results.",
        )
    if max(probe.relevance_counts["product"] for probe in probes) >= 3:
        return (
            "needs_review",
            "blocked_serp_relevance",
            "R3_PRODUCT_SERP_CONTAMINATION",
            "",
            "At least one stored probe contains three or more product results.",
        )
    support_passes = [probe.role_support >= MIN_FORMAT_SUPPORT for probe in probes]
    if not all(support_passes):
        disagreement = len(probes) == 2 and len(set(support_passes)) == 2
        return (
            "needs_review",
            "blocked_probe_disagreement" if disagreement else "blocked_serp_format",
            "R4_PRIMARY_TARGETED_DISAGREEMENT" if disagreement else "R4_ROLE_FORMAT_INSUFFICIENT",
            "",
            "Primary and targeted probes are both retained; every available probe must have at "
            "least five relevant results in the destination role format.",
        )
    if sibling_overlap >= HIGH_OVERLAP:
        return (
            "needs_review",
            "blocked_cannibalization",
            "R5_SIBLING_OVERLAP_REVIEW",
            "",
            "A four-URL same-role sibling overlap is a merge/rewrite gate, not automatic approval.",
        )
    if hub_overlap >= HIGH_OVERLAP:
        return (
            "needs_review",
            "blocked_cannibalization",
            "R6_LEGACY_HUB_OVERLAP_REVIEW",
            "",
            "A four-URL legacy-hub overlap requires a manual split or merge ruling.",
        )
    cross_pair_is_resolved = any(
        ruling.decision == "separate_with_boundary"
        and cross_service_destination_id
        in {ruling.left_destination_id, ruling.right_destination_id}
        for ruling in manual_rulings
    )
    if cross_service_overlap >= HIGH_OVERLAP and not cross_pair_is_resolved:
        return (
            "needs_review",
            "blocked_cannibalization",
            "R7_CROSS_SERVICE_OVERLAP_REVIEW",
            "",
            "A four-URL cross-service overlap has no explicit separate-owner ruling.",
        )
    boundary_rulings = [
        ruling for ruling in manual_rulings if ruling.decision == "separate_with_boundary"
    ]
    if cross_pair_is_resolved or boundary_rulings:
        return (
            keep_decision,
            "boundary_required",
            "R8_MANUAL_OWNER_BOUNDARY",
            "",
            "An explicit manual cross-service owner ruling permits separation only with its boundary.",
        )
    return (
        keep_decision,
        "reviewed",
        "R9_FAIL_CLOSED_RULES_PASSED",
        "",
        "All available probes pass relevance and role-format gates with no unresolved high overlap.",
    )


def _max_probe_overlap(
    left_probes: Sequence[Probe],
    right_probes: Sequence[Probe],
) -> tuple[int, Probe, Probe]:
    candidates = [
        (len(left.canonical_urls & right.canonical_urls), left, right)
        for left in left_probes
        for right in right_probes
    ]
    return min(candidates, key=lambda item: (-item[0], item[1].query_id, item[2].query_id))


def _manual_rulings_for(destination_id: str) -> tuple[ManualPairRuling, ...]:
    return tuple(
        ruling
        for ruling in MANUAL_PAIR_RULINGS
        if destination_id in {ruling.left_destination_id, ruling.right_destination_id}
    )


def _evidence_refs(*probes: Probe) -> str:
    pairs: list[tuple[str, str]] = []
    for probe in probes:
        pair = (probe.relative_path, probe.query_id)
        if pair not in pairs:
            pairs.append(pair)
    return "|".join(value for pair in pairs for value in pair)


def build_expanded_destination_reviews(data_root: Path) -> list[dict[str, str]]:
    """Validate immutable evidence and build exactly one review per destination."""

    data_root = data_root.resolve()
    raw_root = data_root / "raw"
    primary_root = raw_root / "expanded-serp"
    targeted_root = raw_root / "expanded-serp-targeted"
    primary_queue = _read_csv(primary_root / "serp-queue.csv")
    targeted_queue = _read_csv(targeted_root / "serp-queue.csv")
    _validate_stored_queue(
        primary_queue,
        label="primary",
        start_query_number=155,
        expected_count=92,
    )
    _validate_stored_queue(
        targeted_queue,
        label="targeted",
        start_query_number=247,
        expected_count=23,
        primary_destinations=frozenset(row["destination_id"] for row in primary_queue),
    )
    primary_ids = [row["query_id"] for row in primary_queue]
    targeted_ids = [row["query_id"] for row in targeted_queue]
    _validate_manifest(
        primary_root / "source-manifest.json",
        _expanded_manifest_paths(primary_ids),
        exact_paths=True,
    )
    _validate_manifest(
        targeted_root / "source-manifest.json",
        _expanded_manifest_paths(targeted_ids),
        exact_paths=True,
    )

    legacy_queue_rows = _read_csv(raw_root / "serp" / "serp-queue.csv")
    legacy_queue = {row["query_id"]: row for row in legacy_queue_rows}
    if any(query_id not in legacy_queue for query_id in HUB_QUERY_IDS.values()):
        raise ValueError("legacy SERP queue does not contain every immutable hub query")
    legacy_by_service = {
        service_id: _load_legacy_probe(data_root, legacy_queue[query_id])
        for service_id, query_id in HUB_QUERY_IDS.items()
    }
    for service_id, probe in legacy_by_service.items():
        if probe.service_id != service_id:
            raise ValueError(f"legacy hub query/service mismatch: {probe.query_id}")
    _validate_manifest(
        raw_root / "source-manifest.json",
        [probe.relative_path.removeprefix("raw/") for probe in legacy_by_service.values()],
        exact_paths=False,
    )

    primary_by_destination = {
        row["destination_id"]: _load_probe(data_root, row, "expanded-serp")
        for row in primary_queue
    }
    targeted_by_destination = {
        row["destination_id"]: _load_probe(data_root, row, "expanded-serp-targeted")
        for row in targeted_queue
    }
    pages = _candidate_metadata(primary_queue)
    probes_by_destination = {
        page.destination_id: tuple(
            probe
            for probe in (
                primary_by_destination[page.destination_id],
                targeted_by_destination.get(page.destination_id),
            )
            if probe is not None
        )
        for page in pages
    }
    probe_by_query_id = {
        probe.query_id: probe
        for probes in probes_by_destination.values()
        for probe in probes
    }
    rows: list[dict[str, str]] = []
    for page in pages:
        primary = primary_by_destination[page.destination_id]
        targeted = targeted_by_destination.get(page.destination_id)
        page_probes = probes_by_destination[page.destination_id]
        hub = legacy_by_service[page.service_id]
        primary_hub_overlap = len(primary.canonical_urls & hub.canonical_urls)
        targeted_hub_overlap = (
            len(targeted.canonical_urls & hub.canonical_urls) if targeted is not None else None
        )
        max_hub_overlap, max_hub_probe, _ = _max_probe_overlap(page_probes, (hub,))
        siblings = [
            sibling
            for sibling in pages
            if sibling.service_id == page.service_id
            and sibling.page_role == page.page_role
            and sibling.destination_id != page.destination_id
        ]
        sibling_candidates = []
        for sibling in siblings:
            overlap, left_probe, right_probe = _max_probe_overlap(
                page_probes,
                probes_by_destination[sibling.destination_id],
            )
            sibling_candidates.append(
                (overlap, sibling.destination_id, left_probe, right_probe)
            )
        sibling_overlap, sibling_destination_id, sibling_left_probe, sibling_right_probe = min(
            sibling_candidates,
            key=lambda item: (-item[0], item[1], item[2].query_id, item[3].query_id),
        )

        cross_service_pages = [
            candidate
            for candidate in pages
            if candidate.page_role == page.page_role and candidate.service_id != page.service_id
        ]
        cross_candidates = []
        for candidate in cross_service_pages:
            overlap, left_probe, right_probe = _max_probe_overlap(
                page_probes,
                probes_by_destination[candidate.destination_id],
            )
            cross_candidates.append(
                (overlap, candidate.destination_id, candidate.service_id, left_probe, right_probe)
            )
        (
            cross_overlap,
            cross_destination_id,
            cross_service_id,
            cross_left_probe,
            cross_right_probe,
        ) = min(
            cross_candidates,
            key=lambda item: (-item[0], item[1], item[3].query_id, item[4].query_id),
        )

        manual_rulings = _manual_rulings_for(page.destination_id)
        disposition_detail = MANUAL_DISPOSITION_DETAILS.get(page.destination_id)
        manual_evidence = [
            probe_by_query_id[query_id]
            for manual_ruling in manual_rulings
            for query_id in manual_ruling.evidence_query_ids
        ]
        if disposition_detail is not None:
            manual_evidence.extend(
                probe_by_query_id[query_id] for query_id in disposition_detail[2]
            )
        final_decision, final_status, ruling_id, merge_target, rule_explanation = _final_ruling(
            destination_id=page.destination_id,
            page_role=page.page_role,
            offer_status=page.offer_status,
            probes=page_probes,
            hub_overlap=max_hub_overlap,
            sibling_overlap=sibling_overlap,
            cross_service_overlap=cross_overlap,
            cross_service_destination_id=cross_destination_id,
            manual_rulings=manual_rulings,
        )
        probe_observations = ";".join(
            f"{probe.query_id}[role_support={probe.role_support}/10;"
            f"relevance={_relevance_counts_json(probe.relevance_counts)};"
            f"formats={_format_counts_json(probe.format_counts)}]"
            for probe in page_probes
        )
        manual_id_values = [ruling.ruling_id for ruling in manual_rulings]
        manual_text_values = [
            f"{ruling.ruling_id}:{ruling.decision}:{ruling.rationale}"
            for ruling in manual_rulings
        ]
        if disposition_detail is not None:
            detail_id, detail_rationale, _ = disposition_detail
            if detail_id not in manual_id_values:
                manual_id_values.append(detail_id)
            manual_text_values.append(f"{detail_id}:destination_disposition:{detail_rationale}")
        manual_ids = "|".join(manual_id_values)
        manual_text = " || ".join(manual_text_values)
        rationale = (
            f"probes={probe_observations}; max_legacy_hub_overlap={max_hub_overlap}/10 "
            f"via {max_hub_probe.query_id}~{hub.query_id}; "
            f"max_same_role_sibling_overlap={sibling_overlap}/10 with {sibling_destination_id} "
            f"via {sibling_left_probe.query_id}~{sibling_right_probe.query_id}; "
            f"max_cross_service_overlap={cross_overlap}/10 with {cross_destination_id} "
            f"via {cross_left_probe.query_id}~{cross_right_probe.query_id}; "
            f"manual_rulings={manual_ids or 'none'}. {rule_explanation}"
        )
        evidence = list(page_probes)
        evidence.extend((hub, sibling_right_probe, cross_right_probe, *manual_evidence))
        rows.append(
            {
                "destination_id": page.destination_id,
                "service_id": page.service_id,
                "page_role": page.page_role,
                "title": page.title,
                "slug": page.slug,
                "offer_status": page.offer_status,
                "primary_query_id": primary.query_id,
                "primary_query": primary.query,
                "primary_format_counts": _format_counts_json(primary.format_counts),
                "primary_relevance_counts": _relevance_counts_json(primary.relevance_counts),
                "primary_role_support": str(primary.role_support),
                "primary_legacy_hub_overlap": str(primary_hub_overlap),
                "targeted_query_id": targeted.query_id if targeted is not None else "",
                "targeted_query": targeted.query if targeted is not None else "",
                "targeted_format_counts": (
                    _format_counts_json(targeted.format_counts) if targeted is not None else ""
                ),
                "targeted_relevance_counts": (
                    _relevance_counts_json(targeted.relevance_counts) if targeted is not None else ""
                ),
                "targeted_role_support": str(targeted.role_support) if targeted is not None else "",
                "targeted_legacy_hub_overlap": (
                    str(targeted_hub_overlap) if targeted_hub_overlap is not None else ""
                ),
                "legacy_hub_query_id": hub.query_id,
                "max_legacy_hub_query_id": max_hub_probe.query_id,
                "max_legacy_hub_overlap": str(max_hub_overlap),
                "max_sibling_destination_id": sibling_destination_id,
                "max_sibling_left_query_id": sibling_left_probe.query_id,
                "max_sibling_right_query_id": sibling_right_probe.query_id,
                "max_sibling_overlap": str(sibling_overlap),
                "max_cross_service_destination_id": cross_destination_id,
                "max_cross_service_service_id": cross_service_id,
                "max_cross_service_left_query_id": cross_left_probe.query_id,
                "max_cross_service_right_query_id": cross_right_probe.query_id,
                "max_cross_service_overlap": str(cross_overlap),
                "manual_ruling_ids": manual_ids,
                "manual_ruling": manual_text,
                "manual_ruling_evidence_refs": _evidence_refs(*manual_evidence),
                "final_decision": final_decision,
                "final_status": final_status,
                "ruling_id": ruling_id,
                "merge_target": merge_target,
                "rationale": rationale,
                "boundary": page.boundary,
                "business_evidence": page.business_evidence,
                "semantic_evidence": page.semantic_evidence,
                "evidence_refs": _evidence_refs(*evidence),
                "review_status": "reviewed",
                "reviewer": "codex-2026-08-28",
            }
        )
    errors = validate_expanded_review_rows(rows, data_root)
    if errors:
        raise ValueError("; ".join(errors))
    return rows


def _parse_counts(value: str, names: Sequence[str]) -> Mapping[str, int] | None:
    try:
        counts = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(counts, dict) or set(counts) != set(names):
        return None
    if any(isinstance(count, bool) or not isinstance(count, int) or count < 0 for count in counts.values()):
        return None
    if sum(counts.values()) != 10:
        return None
    return counts


def _validate_evidence_refs(
    value: str,
    *,
    destination_id: str,
    field: str,
    data_root: Path,
    required: bool,
) -> list[str]:
    errors: list[str] = []
    references = value.split("|") if value else []
    if not references:
        if required:
            errors.append(f"{destination_id} {field} must contain path/query-id pairs")
        return errors
    if len(references) % 2:
        return [f"{destination_id} {field} must contain path/query-id pairs"]
    for index in range(0, len(references), 2):
        relative_path, query_id = references[index : index + 2]
        evidence_path = (data_root / relative_path).resolve()
        if data_root != evidence_path and data_root not in evidence_path.parents:
            errors.append(f"{destination_id} evidence path escapes data root: {relative_path}")
            continue
        if not evidence_path.is_file():
            errors.append(f"{destination_id} evidence path does not exist: {relative_path}")
            continue
        try:
            _read_matching_jsonl(evidence_path, query_id)
        except ValueError as exc:
            errors.append(f"{destination_id} invalid evidence ref {relative_path}|{query_id}: {exc}")
    return errors


def validate_expanded_review_rows(
    rows: Sequence[Mapping[str, str]],
    data_root: Path,
) -> list[str]:
    """Validate coverage, stored observations, rulings, and every evidence ref."""

    data_root = data_root.resolve()
    expected_ids = [
        row["destination_id"]
        for row in _read_csv(data_root / "raw" / "expanded-serp" / "serp-queue.csv")
    ]
    actual_ids = [str(row.get("destination_id", "")) for row in rows]
    errors: list[str] = []
    if actual_ids != expected_ids or len(set(actual_ids)) != len(expected_ids):
        errors.append("destination coverage mismatch: expected every expanded destination exactly once")
    for row in rows:
        destination_id = str(row.get("destination_id", "")) or "<blank>"
        missing_columns = [column for column in REVIEW_COLUMNS if column not in row]
        if missing_columns:
            errors.append(f"{destination_id} missing review columns: {missing_columns}")
            continue
        for field in ("primary_format_counts",):
            if _parse_counts(row[field], FORMAT_NAMES) is None:
                errors.append(f"{destination_id} invalid top-10 format counts: {field}")
        if _parse_counts(row["primary_relevance_counts"], RELEVANCE_NAMES) is None:
            errors.append(f"{destination_id} invalid top-10 relevance counts: primary_relevance_counts")
        if row["targeted_query_id"]:
            if _parse_counts(row["targeted_format_counts"], FORMAT_NAMES) is None:
                errors.append(f"{destination_id} invalid top-10 format counts: targeted_format_counts")
            if _parse_counts(row["targeted_relevance_counts"], RELEVANCE_NAMES) is None:
                errors.append(f"{destination_id} invalid top-10 relevance counts: targeted_relevance_counts")
        elif any(
            row[field]
            for field in (
                "targeted_format_counts",
                "targeted_relevance_counts",
                "targeted_role_support",
                "targeted_legacy_hub_overlap",
            )
        ):
            errors.append(f"{destination_id} has targeted evidence without a targeted query")
        for field in ("primary_role_support", "targeted_role_support"):
            if field == "targeted_role_support" and not row["targeted_query_id"]:
                continue
            try:
                support = int(row[field])
            except (TypeError, ValueError):
                errors.append(f"{destination_id} invalid role support: {field}")
                continue
            if support not in range(11):
                errors.append(f"{destination_id} role support outside 0..10: {field}")
        for field in (
            "primary_legacy_hub_overlap",
            "max_legacy_hub_overlap",
            "max_sibling_overlap",
            "max_cross_service_overlap",
        ):
            try:
                value = int(row[field])
            except (TypeError, ValueError):
                errors.append(f"{destination_id} invalid overlap: {field}")
                continue
            if value not in range(11):
                errors.append(f"{destination_id} overlap outside 0..10: {field}")
        errors.extend(
            _validate_evidence_refs(
                row["evidence_refs"],
                destination_id=destination_id,
                field="evidence_refs",
                data_root=data_root,
                required=True,
            )
        )
        errors.extend(
            _validate_evidence_refs(
                row["manual_ruling_evidence_refs"],
                destination_id=destination_id,
                field="manual_ruling_evidence_refs",
                data_root=data_root,
                required=bool(row["manual_ruling_ids"]),
            )
        )
        if row["final_decision"] not in {
            "keep_child",
            "keep_article",
            "merge",
            "reject",
            "needs_review",
        }:
            errors.append(f"{destination_id} has an invalid final decision")
        if row["final_decision"] == "merge" and not row["merge_target"]:
            errors.append(f"{destination_id} merge has no target")
        if row["final_decision"] != "merge" and row["merge_target"]:
            errors.append(f"{destination_id} non-merge has a merge target")
        if not all(row[field].strip() for field in ("final_decision", "final_status", "ruling_id", "rationale", "boundary")):
            errors.append(f"{destination_id} has an incomplete final ruling")
    return sorted(set(errors))


def write_expanded_destination_reviews(data_root: Path, output: Path | None = None) -> int:
    """Write the deterministic review ledger as UTF-8 CSV."""

    rows = build_expanded_destination_reviews(data_root)
    target = output or data_root / "reviews" / "expanded_destination_serp_reviews.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _default_data_root() -> Path:
    return Path(__file__).resolve().parents[2] / "seo-data" / "2026-08-exp76-services"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=_default_data_root())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    count = write_expanded_destination_reviews(args.data_root, args.output)
    print(f"expanded_destination_serp_reviews={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
