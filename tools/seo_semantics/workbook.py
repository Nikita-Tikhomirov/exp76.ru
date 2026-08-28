"""Build and validate the semantic-core workbook with the bundled artifact runtime."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit

from .serp import canonicalize_serp_url


SHEET_NAMES = (
    "scope_urls",
    "keywords_raw",
    "keywords_clean",
    "minus_words",
    "frozen_collisions",
    "serp_results",
    "clusters",
    "url_map",
    "content_briefs",
    "launch_monitoring",
    "qa_log",
)

_RUNTIME_NODE_ROOT = Path(
    os.environ.get(
        "CODEX_ARTIFACT_NODE_ROOT",
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node",
    )
).expanduser()
_BUNDLED_NODE = Path(
    os.environ.get("CODEX_ARTIFACT_NODE", _RUNTIME_NODE_ROOT / "bin" / "node.exe")
).expanduser()
_BUNDLED_NODE_MODULES = Path(
    os.environ.get("CODEX_ARTIFACT_NODE_MODULES", _RUNTIME_NODE_ROOT / "node_modules")
).expanduser()
_POWERSHELL = Path(
    os.environ.get("SystemRoot", r"C:\Windows")
) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
_NODE_SCRIPT = Path(__file__).with_suffix(".mjs")

_PROCESSED_QA_FILES = {
    "serp_results.csv": {
        "query_id",
        "query",
        "service_id",
        "intent",
        "device",
        "rank",
        "url",
        "canonical_url",
        "title",
    },
    "clusters.csv": {
        "cluster_id",
        "service_id",
        "candidate_count",
        "target_url",
        "url_action",
        "validation_status",
        "review_status",
        "confidence",
    },
    "url_map.csv": {
        "cluster_id",
        "service_id",
        "target_url",
        "url_action",
        "validation_status",
        "review_status",
        "confidence",
    },
    "candidate_cluster_map.csv": {
        "candidate_key",
        "service_id",
        "query",
        "intent",
        "cluster_id",
        "target_url",
        "url_action",
        "assignment_method",
        "validation_status",
        "review_status",
    },
    "content_briefs.csv": {
        "service_id",
        "target_url",
        "page_type",
        "source_cluster_ids",
        "primary_query",
        "secondary_queries",
        "required_sections",
        "price_factors",
        "case_ids",
        "photo_ids",
        "internal_links",
        "frozen_links",
        "missing_facts",
        "status",
    },
    "serp_ambiguous_pairs.csv": {
        "pair_id",
        "left_query_id",
        "right_query_id",
        "left_query",
        "right_query",
        "left_service_id",
        "right_service_id",
        "left_intent",
        "right_intent",
        "overlap",
        "shared_urls",
        "decision",
        "owner_action",
        "validation_status",
        "review_status",
        "reviewer",
        "rationale",
    },
}
_ALLOWED_URL_ACTIONS = {
    "article_candidate",
    "article",
    "child",
    "exclude",
    "frozen",
    "frozen_owner",
    "hub",
    "keep_enhance",
    "keep_special_owner",
    "merge",
    "special",
    "unresolved",
}
_SERP_GRAPH_INTENTS = {
    "commercial_research",
    "informational",
    "product_only",
    "transactional",
}


def _require_runtime() -> None:
    missing = [
        str(path)
        for path in (_BUNDLED_NODE, _BUNDLED_NODE_MODULES, _NODE_SCRIPT)
        if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"bundled workbook runtime is unavailable: {', '.join(missing)}")


def _create_module_junction(link: Path) -> None:
    """Expose the loader-provided packages without modifying their directory."""
    try:
        os.symlink(_BUNDLED_NODE_MODULES, link, target_is_directory=True)
        return
    except OSError:
        pass
    result = subprocess.run(
        [
            str(_POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "New-Item -ItemType Junction -Path $args[0] -Target $args[1] | Out-Null",
            str(link),
            str(_BUNDLED_NODE_MODULES),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"failed to create bundled node_modules junction: {detail}")


def _run_node(*arguments: str) -> str:
    _require_runtime()
    with tempfile.TemporaryDirectory(prefix="exp76-workbook-") as tmp:
        runtime_dir = Path(tmp)
        runtime_script = runtime_dir / "workbook.mjs"
        shutil.copy2(_NODE_SCRIPT, runtime_script)
        _create_module_junction(runtime_dir / "node_modules")
        for attempt in range(3):
            try:
                result = subprocess.run(
                    [str(_BUNDLED_NODE), str(runtime_script), *arguments],
                    cwd=runtime_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.1 * (attempt + 1))
                continue

            if result.returncode == 0:
                return result.stdout

            detail = result.stderr.strip() or result.stdout.strip()
            # The bundled Windows runtime can occasionally terminate before
            # JavaScript starts and return neither stdout nor stderr. Retrying
            # that specific no-diagnostic failure is safe for build/validate/
            # render because each command writes to explicit caller-owned paths.
            if not detail and attempt < 2:
                time.sleep(0.1 * (attempt + 1))
                continue
            diagnostic = detail or "no stdout/stderr"
            raise RuntimeError(
                f"artifact workbook command failed (exit {result.returncode}): {diagnostic}"
            )
    raise RuntimeError("artifact workbook command failed after retries")


def _read_processed_csv(
    data_dir: Path,
    filename: str,
    required_columns: set[str],
    errors: list[str],
) -> list[dict[str, str]] | None:
    path = data_dir / filename
    if not path.is_file():
        errors.append(f"missing_processed_file:{filename}")
        return None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            missing = sorted(required_columns - columns)
            if missing:
                errors.append(f"missing_processed_columns:{filename}:{','.join(missing)}")
                return None
            return list(reader)
    except (OSError, csv.Error) as exc:
        errors.append(f"invalid_processed_csv:{filename}:{exc}")
        return None


def _text(value: object) -> str:
    return str(value or "").strip()


def _row_identifier(filename: str, row: dict[str, str], row_number: int) -> str:
    key = "candidate_key" if filename == "candidate_cluster_map.csv" else "cluster_id"
    return _text(row.get(key)) or f"row-{row_number}"


def _url_action_errors(
    filename: str,
    rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        identifier = _row_identifier(filename, row, row_number)
        action = _text(row.get("url_action"))
        if action not in _ALLOWED_URL_ACTIONS:
            errors.append(f"forbidden_url_action:{filename}:{identifier}:{action or '<blank>'}")
        if any("owner_conflict" in _text(value).casefold() for value in row.values()):
            errors.append(f"owner_conflict:{filename}:{identifier}")
    return errors


def _unique_cluster_ids(
    filename: str,
    rows: list[dict[str, str]],
) -> tuple[set[str], list[str]]:
    identifiers = [_text(row.get("cluster_id")) for row in rows]
    counts = Counter(identifier for identifier in identifiers if identifier)
    errors = [
        f"duplicate_cluster_id:{filename}:{identifier}"
        for identifier, count in sorted(counts.items())
        if count > 1
    ]
    for row_number, identifier in enumerate(identifiers, start=2):
        if not identifier:
            errors.append(f"blank_cluster_id:{filename}:row-{row_number}")
    return set(counts), errors


def _cluster_url_map_errors(
    cluster_rows: list[dict[str, str]],
    url_rows: list[dict[str, str]],
) -> list[str]:
    fields = (
        "service_id",
        "target_url",
        "url_action",
        "validation_status",
        "review_status",
        "confidence",
    )
    clusters = {
        _text(row.get("cluster_id")): row
        for row in cluster_rows
        if _text(row.get("cluster_id"))
    }
    url_map = {
        _text(row.get("cluster_id")): row
        for row in url_rows
        if _text(row.get("cluster_id"))
    }
    return [
        f"cluster_url_map_mismatch:{cluster_id}:{field}"
        for cluster_id in sorted(set(clusters) & set(url_map))
        for field in fields
        if _text(clusters[cluster_id].get(field)) != _text(url_map[cluster_id].get(field))
    ]


def _cluster_review_errors(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        cluster_id = _text(row.get("cluster_id")) or f"row-{row_number}"
        statuses = set(_text(row.get("validation_status")).split("|"))
        if "serp_pair_pending_review" not in statuses:
            continue
        if (
            _text(row.get("url_action")) != "keep_enhance"
            or _text(row.get("review_status")) != "pending"
        ):
            errors.append(f"invalid_pending_serp_cluster:{cluster_id}")
    return errors


def _serp_state(
    rows: list[dict[str, str]],
) -> tuple[dict[str, tuple[str, str, str, str]], dict[str, set[str]], list[str]]:
    ranks_by_query: dict[str, list[int]] = defaultdict(list)
    metadata: dict[str, tuple[str, str, str, str]] = {}
    urls: dict[str, set[str]] = defaultdict(set)
    errors: list[str] = []
    invalid_rank_queries: set[str] = set()
    expected_query_ids = {f"Q{index:06d}" for index in range(1, 142)}
    if len(rows) != 1410:
        errors.append(f"serp_row_count:expected=1410:actual={len(rows)}")
    for row_number, row in enumerate(rows, start=2):
        query_id = _text(row.get("query_id"))
        query_label = query_id or f"row-{row_number}"
        if not query_id:
            errors.append(f"blank_serp_query_id:row-{row_number}")
            continue
        try:
            rank = int(_text(row.get("rank")))
        except ValueError:
            invalid_rank_queries.add(query_id)
        else:
            ranks_by_query[query_id].append(rank)
        current_metadata = (
            _text(row.get("query")),
            _text(row.get("service_id")),
            _text(row.get("intent")),
            _text(row.get("device")),
        )
        previous_metadata = metadata.setdefault(query_id, current_metadata)
        if previous_metadata != current_metadata:
            errors.append(f"serp_metadata_conflict:{query_id}")
        rank_label = _text(row.get("rank")) or f"row-{row_number}"
        if not _text(row.get("title")):
            errors.append(f"serp_missing_title:{query_label}:{rank_label}")
        raw_url = _text(row.get("url"))
        try:
            parsed = urlsplit(raw_url)
            hostname = (parsed.hostname or "").casefold().removeprefix("www.")
            canonical_url = canonicalize_serp_url(raw_url)
        except ValueError:
            errors.append(f"serp_invalid_url:{query_label}:{rank_label}")
            continue
        if hostname == "yandex.ru" and parsed.path.startswith("/an/count/"):
            errors.append(f"serp_ad_tracking_url:{query_label}:{rank_label}")
        if _text(row.get("canonical_url")) != canonical_url:
            errors.append(f"serp_canonical_mismatch:{query_label}:{rank_label}")
        first_segment = parsed.path.strip("/").split("/", 1)[0].casefold()
        excluded_yandex_vertical = (
            hostname in {"yandex.ru", "ya.ru"}
            and first_segment in {"images", "maps", "video"}
        ) or hostname.startswith("maps.yandex.")
        if not excluded_yandex_vertical:
            urls[query_id].add(canonical_url)

    actual_query_ids = set(metadata)
    if actual_query_ids != expected_query_ids:
        missing = ",".join(sorted(expected_query_ids - actual_query_ids)) or "none"
        extra = ",".join(sorted(actual_query_ids - expected_query_ids)) or "none"
        errors.append(f"serp_query_id_coverage:missing={missing}:extra={extra}")
    for query_id in sorted(expected_query_ids | set(ranks_by_query) | invalid_rank_queries):
        if query_id in invalid_rank_queries or sorted(ranks_by_query[query_id]) != list(range(1, 11)):
            errors.append(f"serp_rank_contract:{query_id}")
    return metadata, urls, errors


def _candidate_map_errors(
    rows: list[dict[str, str]],
    cluster_rows: list[dict[str, str]],
    cluster_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    keys = [_text(row.get("candidate_key")) for row in rows]
    key_counts = Counter(key for key in keys if key)
    for key, count in sorted(key_counts.items()):
        if count > 1:
            errors.append(f"duplicate_candidate_key:{key}")
    for row_number, row in enumerate(rows, start=2):
        key = _text(row.get("candidate_key"))
        cluster_id = _text(row.get("cluster_id"))
        if not key:
            errors.append(f"blank_candidate_key:row-{row_number}")
        if not cluster_id or cluster_id not in cluster_ids:
            errors.append(
                f"candidate_cluster_missing:{key or f'row-{row_number}'}:{cluster_id or '<blank>'}"
            )

    actual_counts = Counter(_text(row.get("cluster_id")) for row in rows)
    for row_number, cluster in enumerate(cluster_rows, start=2):
        cluster_id = _text(cluster.get("cluster_id"))
        if not cluster_id or _text(cluster.get("url_action")) in {"frozen", "frozen_owner"}:
            continue
        try:
            expected = int(_text(cluster.get("candidate_count")))
        except ValueError:
            errors.append(f"invalid_candidate_count:{cluster_id or f'row-{row_number}'}")
            continue
        actual = actual_counts[cluster_id]
        if expected != actual:
            errors.append(
                f"candidate_count_mismatch:{cluster_id}:expected={expected}:actual={actual}"
            )
    return errors


def _pipe_values(value: object) -> list[str]:
    return [item for part in _text(value).split("|") if (item := _text(part))]


def _content_brief_errors(
    rows: list[dict[str, str]],
    cluster_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
) -> list[str]:
    """Keep editorial briefs traceable to accepted service-query assignments."""
    if rows and all("destination_id" in row for row in rows):
        return _destination_content_brief_errors(rows, cluster_rows, candidate_rows)
    errors: list[str] = []
    clusters = {
        _text(row.get("cluster_id")): row
        for row in cluster_rows
        if _text(row.get("cluster_id"))
    }
    candidates_by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidate_rows:
        candidates_by_query[_text(candidate.get("query"))].append(candidate)

    service_ids = [_text(row.get("service_id")) for row in rows]
    for service_id, count in sorted(Counter(item for item in service_ids if item).items()):
        if count > 1:
            errors.append(f"duplicate_content_brief_service:{service_id}")

    for row_number, row in enumerate(rows, start=2):
        service_id = _text(row.get("service_id"))
        brief_id = service_id or f"row-{row_number}"
        target_url = _text(row.get("target_url"))
        source_ids = _pipe_values(row.get("source_cluster_ids"))

        if not service_id:
            errors.append(f"blank_content_brief_service:row-{row_number}")
        if not target_url:
            errors.append(f"blank_content_brief_target:{brief_id}")
        if not source_ids:
            errors.append(f"blank_content_brief_sources:{brief_id}")
        for source_id, count in sorted(Counter(source_ids).items()):
            if count > 1:
                errors.append(f"duplicate_content_brief_source:{brief_id}:{source_id}")

        for source_id in source_ids:
            cluster = clusters.get(source_id)
            if cluster is None:
                errors.append(f"content_brief_source_missing:{brief_id}:{source_id}")
                continue
            action = _text(cluster.get("url_action"))
            source_service = _text(cluster.get("service_id"))
            source_target = _text(cluster.get("target_url"))
            if action != "keep_enhance":
                errors.append(f"content_brief_source_action:{brief_id}:{source_id}:{action}")
            if source_service != service_id:
                errors.append(
                    f"content_brief_source_service_mismatch:"
                    f"{brief_id}:{source_id}:{source_service or '<blank>'}"
                )
            if source_target != target_url:
                errors.append(f"content_brief_source_target_mismatch:{brief_id}:{source_id}")

        primary_query = _text(row.get("primary_query"))
        if not primary_query:
            errors.append(f"blank_content_brief_primary_query:{brief_id}")
        query_fields = (
            ("primary_query", [primary_query] if primary_query else []),
            ("secondary_queries", _pipe_values(row.get("secondary_queries"))),
        )
        seen_queries: set[str] = set()
        for field, queries in query_fields:
            for query in queries:
                if query in seen_queries:
                    errors.append(f"duplicate_content_brief_query:{brief_id}:{query}")
                    continue
                seen_queries.add(query)
                candidates = candidates_by_query.get(query, [])
                if not candidates:
                    errors.append(f"content_brief_query_missing:{brief_id}:{field}:{query}")
                    continue
                traceable = any(
                    _text(candidate.get("service_id")) == service_id
                    and _text(candidate.get("cluster_id")) in source_ids
                    and _text(candidate.get("target_url")) == target_url
                    and _text(candidate.get("url_action")) == "keep_enhance"
                    and _text(candidate.get("assignment_method"))
                    == "direct_serp_representative"
                    and _text(candidate.get("validation_status"))
                    == "serp_direct_reviewed"
                    and _text(candidate.get("review_status")) == "reviewed"
                    for candidate in candidates
                )
                if not traceable:
                    errors.append(
                        f"content_brief_query_outside_sources:{brief_id}:{field}:{query}"
                    )
    return errors


def _destination_content_brief_errors(
    rows: list[dict[str, str]],
    cluster_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
) -> list[str]:
    """Validate the Task 2 destination-level brief contract."""
    errors: list[str] = []
    clusters = {
        _text(row.get("cluster_id")): row
        for row in cluster_rows
        if _text(row.get("cluster_id"))
    }
    candidate_queries: dict[str, set[str]] = defaultdict(set)
    for candidate in candidate_rows:
        candidate_queries[_text(candidate.get("cluster_id"))].add(
            _text(candidate.get("query"))
        )
    destination_ids = [_text(row.get("destination_id")) for row in rows]
    for destination_id, count in Counter(item for item in destination_ids if item).items():
        if count > 1:
            errors.append(f"duplicate_content_brief_destination:{destination_id}")

    required_fields = (
        "destination_id",
        "target_url",
        "page_type",
        "source_cluster_ids",
        "primary_query",
        "secondary_queries",
        "intent",
        "required_sections",
        "price_factors",
        "internal_links",
        "evidence_refs",
        "evidence_state",
        "missing_facts",
        "status",
    )
    for row_number, row in enumerate(rows, start=2):
        destination_id = _text(row.get("destination_id")) or f"row-{row_number}"
        for field in required_fields:
            if not _text(row.get(field)):
                errors.append(f"blank_content_brief_field:{destination_id}:{field}")
        source_ids = _pipe_values(row.get("source_cluster_ids"))
        for source_id, count in Counter(source_ids).items():
            if count > 1:
                errors.append(f"duplicate_content_brief_source:{destination_id}:{source_id}")
        target_url = _text(row.get("target_url"))
        service_id = _text(row.get("service_id"))
        for source_id in source_ids:
            cluster = clusters.get(source_id)
            if cluster is None:
                errors.append(f"content_brief_source_missing:{destination_id}:{source_id}")
                continue
            source_target = _text(cluster.get("target_url"))
            if source_target != target_url:
                errors.append(
                    f"content_brief_source_target_mismatch:{destination_id}:{source_id}"
                )
            source_service = _text(cluster.get("service_id"))
            if service_id and source_service != service_id:
                errors.append(
                    f"content_brief_source_service_mismatch:"
                    f"{destination_id}:{source_id}:{source_service or '<blank>'}"
                )
        page_type = _text(row.get("page_type"))
        if page_type not in {"frozen", "special"}:
            traceable_queries = set().union(
                *(candidate_queries.get(source_id, set()) for source_id in source_ids)
            )
            for field in ("primary_query", "secondary_queries"):
                queries = (
                    [_text(row.get(field))]
                    if field == "primary_query"
                    else _pipe_values(row.get(field))
                )
                for query in queries:
                    if query not in traceable_queries:
                        errors.append(
                            f"content_brief_query_outside_sources:"
                            f"{destination_id}:{field}:{query}"
                        )
        if (not _text(row.get("case_ids")) or not _text(row.get("photo_ids"))) and _text(
            row.get("status")
        ) != "needs_case_mapping":
            errors.append(f"content_brief_missing_case_mapping_status:{destination_id}")
    return errors


def _ambiguous_pair_errors(
    rows: list[dict[str, str]],
    metadata: dict[str, tuple[str, str, str, str]],
    urls: dict[str, set[str]],
    candidate_rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    assignments = {
        (
            _text(row.get("service_id")),
            _text(row.get("query")),
            _text(row.get("intent")),
        ): row
        for row in candidate_rows
    }
    policy_fields = {
        "manual_review": (
            "hold_current_url",
            "serp_pair_pending_review",
            "pending",
            "",
        ),
        "owner_boundary_split": (
            "hold_distinct_service_owners",
            "cross_service_owner_boundary_reviewed",
            "reviewed",
            "policy_scope_owner",
        ),
        "shared_special_owner": (
            "hold_shared_special_owner",
            "shared_special_owner_reviewed",
            "reviewed",
            "policy_special_owner",
        ),
        "policy_exclusion_split": (
            "retain_exclusion_and_service_assignment",
            "policy_exclusion_split_reviewed",
            "reviewed",
            "policy_exclusion",
        ),
        "shared_policy_exclusion": (
            "retain_shared_exclusion",
            "shared_policy_exclusion_reviewed",
            "reviewed",
            "policy_exclusion",
        ),
    }
    primary_ids = sorted(
        query_id
        for query_id, (_, _, intent, device) in metadata.items()
        if device == "desktop" and intent in _SERP_GRAPH_INTENTS
    )
    expected_pairs: set[tuple[str, str]] = set()
    for left_id, right_id in combinations(primary_ids, 2):
        overlap = len(urls[left_id] & urls[right_id])
        left_service = metadata[left_id][1]
        right_service = metadata[right_id][1]
        same_service = left_service == right_service
        same_intent = metadata[left_id][2] == metadata[right_id][2]
        if overlap <= 1:
            continue
        if same_service and same_intent and overlap >= 4:
            continue
        expected_pairs.add((left_id, right_id))

    pair_ids: set[str] = set()
    actual_pairs: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        pair_id = _text(row.get("pair_id")) or f"row-{row_number}"
        if pair_id in pair_ids:
            errors.append(f"duplicate_serp_ambiguous_pair_id:{pair_id}")
        pair_ids.add(pair_id)
        left_id = _text(row.get("left_query_id"))
        right_id = _text(row.get("right_query_id"))
        pair = (left_id, right_id)
        if pair in actual_pairs:
            errors.append(f"duplicate_serp_ambiguous_pair:{left_id}:{right_id}")
        actual_pairs.add(pair)
        if (
            not left_id
            or not right_id
            or left_id >= right_id
            or left_id not in metadata
            or right_id not in metadata
        ):
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:query_ids")
            continue

        left_query, left_service, left_intent, _ = metadata[left_id]
        right_query, right_service, right_intent, _ = metadata[right_id]
        expected_metadata = (
            left_query,
            right_query,
            left_service,
            right_service,
            left_intent,
            right_intent,
        )
        actual_metadata = tuple(
            _text(row.get(field))
            for field in (
                "left_query",
                "right_query",
                "left_service_id",
                "right_service_id",
                "left_intent",
                "right_intent",
            )
        )
        if actual_metadata != expected_metadata:
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:metadata")

        shared_urls = {_text(item) for item in _text(row.get("shared_urls")).split("|") if _text(item)}
        expected_shared_urls = urls[left_id] & urls[right_id]
        try:
            overlap = int(_text(row.get("overlap")))
        except ValueError:
            overlap = -1
        if overlap != len(expected_shared_urls) or shared_urls != expected_shared_urls:
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:overlap")

        left_assignment = assignments.get((left_service, left_query, left_intent))
        right_assignment = assignments.get((right_service, right_query, right_intent))
        expected_decision = ""
        if left_assignment is None or right_assignment is None:
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:candidate_assignment")
        else:
            left_assignment_key = (
                _text(left_assignment.get("cluster_id")),
                _text(left_assignment.get("url_action")),
                _text(left_assignment.get("target_url")),
            )
            right_assignment_key = (
                _text(right_assignment.get("cluster_id")),
                _text(right_assignment.get("url_action")),
                _text(right_assignment.get("target_url")),
            )
            left_cluster, left_action, left_target = left_assignment_key
            right_cluster, right_action, right_target = right_assignment_key
            shared_special_owner = (
                left_action == right_action == "keep_special_owner"
                and left_cluster == right_cluster
                and left_cluster.startswith("SPECIAL-")
                and bool(left_target)
                and left_target == right_target
            )
            shared_policy_exclusion = (
                left_action == right_action == "exclude"
                and left_cluster == right_cluster
            )
            has_exclusion = "exclude" in {left_action, right_action}
            if shared_special_owner:
                expected_decision = "shared_special_owner"
            elif shared_policy_exclusion:
                expected_decision = "shared_policy_exclusion"
            elif has_exclusion and left_assignment_key != right_assignment_key:
                expected_decision = "policy_exclusion_split"
            elif (
                left_service == right_service
                and left_action not in {"exclude", "keep_special_owner"}
                and right_action not in {"exclude", "keep_special_owner"}
            ):
                expected_decision = "manual_review"
            elif left_service != right_service:
                expected_decision = "owner_boundary_split"
            if _text(row.get("decision")) != expected_decision:
                errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:assignment_policy")

        actual_policy_fields = (
            _text(row.get("owner_action")),
            _text(row.get("validation_status")),
            _text(row.get("review_status")),
            _text(row.get("reviewer")),
        )
        expected_policy_fields = policy_fields.get(_text(row.get("decision")))
        if expected_policy_fields is None or actual_policy_fields != expected_policy_fields:
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:policy_fields")
        if not _text(row.get("rationale")):
            errors.append(f"invalid_serp_ambiguous_pair:{pair_id}:rationale")

    for left_id, right_id in sorted(expected_pairs - actual_pairs):
        errors.append(f"missing_serp_ambiguous_pair:{left_id}:{right_id}")
    for left_id, right_id in sorted(actual_pairs - expected_pairs):
        errors.append(f"unexpected_serp_ambiguous_pair:{left_id}:{right_id}")
    return errors


def validate_processed_data(data_dir: Path) -> list[str]:
    """Return deterministic integrity errors for the non-destructive SEO outputs."""
    data_dir = Path(data_dir).resolve()
    errors: list[str] = []
    tables = {
        filename: _read_processed_csv(data_dir, filename, columns, errors)
        for filename, columns in _PROCESSED_QA_FILES.items()
    }

    serp_rows = tables["serp_results.csv"]
    cluster_rows = tables["clusters.csv"]
    url_rows = tables["url_map.csv"]
    candidate_rows = tables["candidate_cluster_map.csv"]
    content_brief_rows = tables["content_briefs.csv"]
    ambiguous_rows = tables["serp_ambiguous_pairs.csv"]

    metadata: dict[str, tuple[str, str, str, str]] = {}
    urls: dict[str, set[str]] = {}
    if serp_rows is not None:
        metadata, urls, serp_errors = _serp_state(serp_rows)
        errors.extend(serp_errors)

    cluster_ids: set[str] = set()
    url_cluster_ids: set[str] = set()
    if cluster_rows is not None:
        cluster_ids, cluster_id_errors = _unique_cluster_ids("clusters.csv", cluster_rows)
        errors.extend(cluster_id_errors)
        errors.extend(_url_action_errors("clusters.csv", cluster_rows))
        errors.extend(_cluster_review_errors(cluster_rows))
    if url_rows is not None:
        url_cluster_ids, url_id_errors = _unique_cluster_ids("url_map.csv", url_rows)
        errors.extend(url_id_errors)
        errors.extend(_url_action_errors("url_map.csv", url_rows))
    if cluster_rows is not None and url_rows is not None:
        errors.extend(
            f"cluster_id_missing_from_url_map:{cluster_id}"
            for cluster_id in sorted(cluster_ids - url_cluster_ids)
        )
        errors.extend(
            f"cluster_id_missing_from_clusters:{cluster_id}"
            for cluster_id in sorted(url_cluster_ids - cluster_ids)
        )
        errors.extend(_cluster_url_map_errors(cluster_rows, url_rows))

    if candidate_rows is not None:
        errors.extend(_url_action_errors("candidate_cluster_map.csv", candidate_rows))
        if cluster_rows is not None:
            errors.extend(_candidate_map_errors(candidate_rows, cluster_rows, cluster_ids))

    if (
        content_brief_rows is not None
        and cluster_rows is not None
        and candidate_rows is not None
    ):
        errors.extend(
            _content_brief_errors(content_brief_rows, cluster_rows, candidate_rows)
        )

    if ambiguous_rows is not None and serp_rows is not None and candidate_rows is not None:
        errors.extend(_ambiguous_pair_errors(ambiguous_rows, metadata, urls, candidate_rows))
    return sorted(set(errors))


def build_workbook(data_dir: Path, output_path: Path) -> None:
    """Create the exact eleven-sheet XLSX from processed CSV files."""
    data_dir = Path(data_dir).resolve()
    output_path = Path(output_path).resolve()
    missing = [f"{name}.csv" for name in SHEET_NAMES if not (data_dir / f"{name}.csv").is_file()]
    if missing:
        raise ValueError(f"missing CSV files: {', '.join(missing)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_node(
        "build",
        "--data-dir",
        str(data_dir),
        "--output",
        str(output_path),
    )


def validate_workbook(path: Path, data_dir: Path | None = None) -> list[str]:
    """Return deterministic semantic QA errors from the exported workbook."""
    path = Path(path).resolve()
    if not path.is_file():
        return [f"missing_workbook:{path}"]
    arguments = ["validate", "--input", str(path)]
    if data_dir is not None:
        arguments.extend(("--data-dir", str(Path(data_dir).resolve())))
    stdout = _run_node(*arguments)
    prefix = "VALIDATION_JSON:"
    for line in reversed(stdout.splitlines()):
        if line.startswith(prefix):
            payload = json.loads(line.removeprefix(prefix))
            if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
                raise RuntimeError("artifact validator returned an invalid payload")
            return sorted(set(payload))
    raise RuntimeError("artifact validator did not return a validation payload")


def render_workbook(path: Path, output_dir: Path) -> list[Path]:
    """Render every contractual sheet to a PNG preview for visual QA."""
    path = Path(path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout = _run_node(
        "render",
        "--input",
        str(path),
        "--output-dir",
        str(output_dir),
    )
    prefix = "RENDER_JSON:"
    for line in reversed(stdout.splitlines()):
        if line.startswith(prefix):
            payload = json.loads(line.removeprefix(prefix))
            return [Path(item) for item in payload]
    raise RuntimeError("artifact renderer did not return preview paths")
