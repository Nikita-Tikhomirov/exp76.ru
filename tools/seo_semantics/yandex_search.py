"""Guarded deferred Yandex Search API collection with immutable raw evidence."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .manifest import register_source, validate_collected_at, validate_manifest
from .serp import validate_organic_result


SEARCH_ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/web/searchAsync"
OPERATION_ENDPOINT = "https://operation.api.cloud.yandex.net/operations"
DAY_DEFERRED_COST_RUB = Decimal("0.0305")
MAX_ASYNC_REQUESTS = 115
MAX_COST_RUB = Decimal("10")
QUEUE_COLUMNS = frozenset(
    {"query_id", "query", "service_id", "intent", "region", "device"}
)


@dataclass(frozen=True)
class ApiCredentials:
    api_key: str
    folder_id: str
    billing_active: bool


@dataclass(frozen=True)
class ApiCollectionPlan:
    queue_rows: tuple[dict[str, str], ...]
    completed_query_ids: tuple[str, ...]
    submitted_query_ids: tuple[str, ...]
    pending_query_ids: tuple[str, ...]
    estimated_cost_rub: Decimal
    queue_sha256: str
    max_requests: int = MAX_ASYNC_REQUESTS
    max_cost_rub: Decimal = MAX_COST_RUB

    @property
    def queue_by_id(self) -> dict[str, dict[str, str]]:
        return {row["query_id"]: row for row in self.queue_rows}


@dataclass(frozen=True)
class ApiPollResult:
    written_paths: tuple[Path, ...]
    completed_query_ids: tuple[str, ...]
    remaining_query_ids: tuple[str, ...]
    errors: tuple[str, ...]

    def __len__(self) -> int:
        return len(self.written_paths)

    def __iter__(self):
        return iter(self.written_paths)


class JsonTransport(Protocol):
    def request_json(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | None = None,
    ) -> dict[str, object]: ...


class UrllibJsonTransport:
    """Small standard-library JSON transport that never logs credentials."""

    def request_json(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = Request(url, data=payload, headers=dict(headers), method=method)
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ValueError(f"Yandex Search API returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise ValueError("Yandex Search API request failed") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("Yandex Search API returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise ValueError("Yandex Search API response must be a JSON object")
        return result


def load_api_credentials(environ: Mapping[str, str] | None = None) -> ApiCredentials:
    """Load credentials only from process environment after an explicit billing gate."""

    values = os.environ if environ is None else environ
    api_key = values.get("YANDEX_SEARCH_API_KEY", "").strip()
    folder_id = values.get("YANDEX_CLOUD_FOLDER_ID", "").strip()
    if not api_key:
        raise ValueError("Yandex Search API credential is missing from YANDEX_SEARCH_API_KEY")
    if not folder_id:
        raise ValueError("Yandex Cloud folder is missing from YANDEX_CLOUD_FOLDER_ID")
    if values.get("YANDEX_SEARCH_API_BILLING_ACTIVE", "").strip().casefold() != "true":
        raise ValueError("active billing must be explicitly confirmed in YANDEX_SEARCH_API_BILLING_ACTIVE")
    return ApiCredentials(api_key=api_key, folder_id=folder_id, billing_active=True)


def build_collection_plan(queue_path: Path, serp_dir: Path) -> ApiCollectionPlan:
    """Build an exact resumable QID partition before any billable API request."""

    queue_rows = _read_queue(queue_path)
    queue_ids = tuple(row["query_id"] for row in queue_rows)
    queue_set = set(queue_ids)
    queue_by_id = {row["query_id"]: row for row in queue_rows}
    completed = _completed_query_ids(serp_dir, queue_by_id)
    submitted = _submitted_operations(serp_dir)
    unknown = (completed | set(submitted)) - queue_set
    if unknown:
        raise ValueError(f"raw SERP evidence has QIDs absent from queue: {','.join(sorted(unknown))}")

    completed_ordered = tuple(query_id for query_id in queue_ids if query_id in completed)
    submitted_ordered = tuple(
        query_id for query_id in queue_ids if query_id in submitted and query_id not in completed
    )
    pending = tuple(
        query_id
        for query_id in queue_ids
        if query_id not in completed and query_id not in submitted
    )
    billable_scope = len(submitted) + len(pending)
    estimated_cost = DAY_DEFERRED_COST_RUB * billable_scope
    if billable_scope > MAX_ASYNC_REQUESTS:
        raise ValueError(
            f"115-request budget guard exceeded: {billable_scope} uncaptured queue rows"
        )
    if estimated_cost > MAX_COST_RUB:
        raise ValueError(
            f"10-ruble budget guard exceeded: estimated {estimated_cost} RUB"
        )
    if len(completed_ordered) + len(submitted_ordered) + len(pending) != len(queue_ids):
        raise ValueError("QID coverage partition is incomplete")
    return ApiCollectionPlan(
        queue_rows=tuple(queue_rows),
        completed_query_ids=completed_ordered,
        submitted_query_ids=submitted_ordered,
        pending_query_ids=pending,
        estimated_cost_rub=estimated_cost,
        queue_sha256=_canonical_sha256(queue_rows),
    )


def submit_pending(
    plan: ApiCollectionPlan,
    credentials: ApiCredentials,
    serp_dir: Path,
    manifest_path: Path,
    collected_at: str,
    transport: JsonTransport | None = None,
    pause_seconds: float = 0.15,
) -> tuple[Path, ...]:
    """Submit only never-submitted QIDs and persist sanitized immutable operation records."""

    _require_active_credentials(credentials)
    # Fail before the first billable request. The same validated value is later
    # written to the immutable operation record and source manifest.
    validate_collected_at(collected_at)
    client = transport or UrllibJsonTransport()
    queue_by_id = plan.queue_by_id
    _reconcile_and_validate_operations(
        plan,
        credentials.folder_id,
        serp_dir,
        manifest_path,
    )
    batch_sha256 = _batch_sha256(plan.queue_rows, credentials.folder_id)
    written: list[Path] = []
    for index, query_id in enumerate(plan.pending_query_ids):
        row = queue_by_id[query_id]
        request_body = _request_body(row, credentials.folder_id)
        response = client.request_json(
            "POST",
            SEARCH_ENDPOINT,
            _authorization_headers(credentials.api_key),
            request_body,
        )
        operation_id = str(response.get("id", "")).strip()
        if not operation_id:
            raise ValueError(f"Yandex Search API submission for {query_id} returned no operation id")
        operation_record = {
            "query_id": query_id,
            "query": row["query"],
            "service_id": row["service_id"],
            "intent": row["intent"],
            "region": row["region"],
            "device": row["device"],
            "operation_id": operation_id,
            "submitted_at": collected_at,
            "endpoint": SEARCH_ENDPOINT,
            "response_format": "FORMAT_XML",
            "queue_sha256": plan.queue_sha256,
            "request_sha256": _canonical_sha256(request_body),
            "batch_sha256": batch_sha256,
        }
        path = serp_dir / f"yandex-api-{query_id}-operation.json"
        _write_exclusive(path, json.dumps(operation_record, ensure_ascii=False, indent=2) + "\n")
        register_source(path, "serp_api_operation", collected_at, manifest_path)
        written.append(path)
        if index + 1 < len(plan.pending_query_ids) and pause_seconds:
            time.sleep(pause_seconds)
    return tuple(written)


def poll_submitted(
    plan: ApiCollectionPlan,
    credentials: ApiCredentials,
    serp_dir: Path,
    manifest_path: Path,
    collected_at: str,
    transport: JsonTransport | None = None,
    pause_seconds: float = 0.15,
) -> ApiPollResult:
    """Poll each submitted operation once; callers rerun later for unfinished jobs."""

    _require_active_credentials(credentials)
    validate_collected_at(collected_at)
    client = transport or UrllibJsonTransport()
    queue_by_id = plan.queue_by_id
    operations = _reconcile_and_validate_operations(
        plan,
        credentials.folder_id,
        serp_dir,
        manifest_path,
    )
    _reconcile_existing_results(plan, serp_dir, manifest_path, collected_at)
    written: list[Path] = []
    errors: list[str] = []
    for index, query_id in enumerate(plan.submitted_query_ids):
        operation = operations[query_id]
        jsonl_path = serp_dir / f"yandex-api-{query_id}.jsonl"
        try:
            response = client.request_json(
                "GET",
                f"{OPERATION_ENDPOINT}/{operation['operation_id']}",
                _authorization_headers(credentials.api_key),
            )
        except ValueError as exc:
            errors.append(f"{query_id}: {exc}")
            continue
        if response.get("error"):
            error = response["error"]
            message = error.get("message") if isinstance(error, dict) else ""
            errors.append(f"{query_id}: {message or 'operation failed'}")
            continue
        if not response.get("done"):
            continue
        response_body = response.get("response")
        if not isinstance(response_body, dict) or not response_body.get("rawData"):
            errors.append(f"{query_id}: completed operation has no rawData")
            continue
        try:
            xml_bytes = base64.b64decode(str(response_body["rawData"]), validate=True)
            xml_text = xml_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            errors.append(f"{query_id}: rawData is not valid UTF-8 XML")
            continue
        try:
            _validate_xml(xml_text, query_id)
        except ValueError as exc:
            errors.append(f"{query_id}: {exc}")
            continue
        if not jsonl_path.is_file():
            record = _organic_record(queue_by_id[query_id], xml_text, collected_at)
            _validate_completed_record(record, queue_by_id[query_id], query_id)
            _write_exclusive(
                jsonl_path,
                json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n",
            )
            register_source(jsonl_path, "serp", collected_at, manifest_path)
            written.append(jsonl_path)
        if index + 1 < len(plan.submitted_query_ids) and pause_seconds:
            time.sleep(pause_seconds)
    completed = _completed_query_ids(serp_dir, plan.queue_by_id)
    completed_ordered = tuple(
        row["query_id"] for row in plan.queue_rows if row["query_id"] in completed
    )
    remaining = tuple(
        row["query_id"] for row in plan.queue_rows if row["query_id"] not in completed
    )
    return ApiPollResult(
        written_paths=tuple(written),
        completed_query_ids=completed_ordered,
        remaining_query_ids=remaining,
        errors=tuple(errors),
    )


def assert_complete_coverage(queue_path: Path, serp_dir: Path) -> bool:
    """Require exactly one completed organic record for every queue QID."""

    queue_rows = _read_queue(queue_path)
    queue_ids = {row["query_id"] for row in queue_rows}
    queue_by_id = {row["query_id"]: row for row in queue_rows}
    completed = _completed_query_ids(serp_dir, queue_by_id)
    if completed != queue_ids:
        missing = sorted(queue_ids - completed)
        extra = sorted(completed - queue_ids)
        raise ValueError(
            f"SERP QID coverage mismatch: missing={','.join(missing) or 'none'};"
            f"extra={','.join(extra) or 'none'}"
        )
    return True


def _read_queue(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(QUEUE_COLUMNS - set(reader.fieldnames or ()))
            if missing:
                raise ValueError(f"SERP queue is missing columns: {', '.join(missing)}")
            rows = list(reader)
    except OSError as exc:
        raise ValueError(f"unable to read SERP queue: {exc}") from exc
    query_ids = [row["query_id"] for row in rows]
    if len(query_ids) != len(set(query_ids)) or any(not value for value in query_ids):
        raise ValueError("SERP queue requires unique non-empty query_id values")
    expected = [f"Q{index:06d}" for index in range(1, len(rows) + 1)]
    if query_ids != expected:
        raise ValueError("SERP queue query_ids must be the exact consecutive ordered range")
    return rows


def _completed_query_ids(
    serp_dir: Path,
    queue_by_id: Mapping[str, Mapping[str, str]],
) -> set[str]:
    completed: set[str] = set()
    for path in sorted(serp_dir.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_number}: invalid JSONL") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path.name}:{line_number}: SERP record must be an object")
            query_id = str(record.get("query_id", ""))
            if not query_id or query_id in completed:
                raise ValueError(f"duplicate or empty completed SERP QID: {query_id!r}")
            queue_row = queue_by_id.get(query_id)
            if queue_row is not None:
                _validate_completed_record(record, queue_row, f"{path.name}:{line_number}")
            completed.add(query_id)
    return completed


def _validate_completed_record(
    record: Mapping[str, object],
    queue_row: Mapping[str, str],
    source: str,
) -> None:
    query_id = queue_row["query_id"]
    for field in ("query_id", "query", "region", "device"):
        if str(record.get(field, "")) != queue_row[field]:
            raise ValueError(f"SERP record {source} differs from queue for {query_id}: {field}")
    results = record.get("results")
    if not isinstance(results, list) or len(results) != 10:
        raise ValueError(f"SERP record {source} requires exact ranks 1-10")
    try:
        ranks = sorted(int(item.get("rank", 0)) for item in results if isinstance(item, dict))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"SERP record {source} requires exact ranks 1-10") from exc
    if ranks != list(range(1, 11)):
        raise ValueError(f"SERP record {source} requires exact ranks 1-10")
    for item in results:
        if not isinstance(item, dict):
            raise ValueError(f"SERP record {source} requires exact ranks 1-10")
        validate_organic_result(item, source)


def _submitted_operations(serp_dir: Path) -> dict[str, dict[str, str]]:
    operations: dict[str, dict[str, str]] = {}
    for path in sorted(serp_dir.glob("yandex-api-Q*-operation.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"unable to read operation record {path.name}") from exc
        query_id = str(record.get("query_id", ""))
        operation_id = str(record.get("operation_id", ""))
        expected_name = f"yandex-api-{query_id}-operation.json"
        if (
            not query_id
            or not operation_id
            or query_id in operations
            or path.name != expected_name
        ):
            raise ValueError(f"invalid or duplicate operation record: {path.name}")
        operations[query_id] = {key: str(value) for key, value in record.items()}
    return operations


def _reconcile_and_validate_operations(
    plan: ApiCollectionPlan,
    folder_id: str,
    serp_dir: Path,
    manifest_path: Path,
) -> dict[str, dict[str, str]]:
    validate_manifest(manifest_path)
    operations = _submitted_operations(serp_dir)
    queue_by_id = plan.queue_by_id
    expected_batch_sha256 = _batch_sha256(plan.queue_rows, folder_id)
    for query_id, record in operations.items():
        row = queue_by_id.get(query_id)
        if row is None:
            raise ValueError(f"operation record QID is absent from queue: {query_id}")
        for field in ("query", "service_id", "intent", "region", "device"):
            if record.get(field) != row[field]:
                raise ValueError(f"operation record differs from queue for {query_id}: {field}")
        if record.get("endpoint") not in (None, "", SEARCH_ENDPOINT):
            raise ValueError(f"operation record has an unexpected endpoint for {query_id}")
        if record.get("response_format") not in (None, "", "FORMAT_XML"):
            raise ValueError(f"operation record has an unexpected response format for {query_id}")

        binding_fields = ("queue_sha256", "request_sha256", "batch_sha256")
        present_bindings = tuple(bool(record.get(field)) for field in binding_fields)
        if any(present_bindings) and not all(present_bindings):
            raise ValueError(f"operation record has incomplete snapshot binding for {query_id}")
        if all(present_bindings):
            if record["queue_sha256"] != plan.queue_sha256:
                raise ValueError(f"operation queue snapshot differs for {query_id}")
            expected_request_sha256 = _canonical_sha256(_request_body(row, folder_id))
            if record["request_sha256"] != expected_request_sha256:
                raise ValueError(f"operation request snapshot differs for {query_id}")
            if record["batch_sha256"] != expected_batch_sha256:
                raise ValueError(f"operation batch snapshot differs for {query_id}")

        operation_path = serp_dir / f"yandex-api-{query_id}-operation.json"
        register_source(
            operation_path,
            "serp_api_operation",
            record.get("submitted_at", ""),
            manifest_path,
        )
    return operations


def _reconcile_existing_results(
    plan: ApiCollectionPlan,
    serp_dir: Path,
    manifest_path: Path,
    collected_at: str,
) -> None:
    queue_by_id = plan.queue_by_id
    for query_id, row in queue_by_id.items():
        jsonl_path = serp_dir / f"yandex-api-{query_id}.jsonl"
        if not jsonl_path.is_file():
            continue
        lines = [line for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError(f"API SERP result must contain one JSONL record: {jsonl_path.name}")
        try:
            record = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid API SERP JSONL: {jsonl_path.name}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"invalid API SERP JSONL: {jsonl_path.name}")
        _validate_completed_record(record, row, jsonl_path.name)
        register_source(jsonl_path, "serp", collected_at, manifest_path)


def _authorization_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _require_active_credentials(credentials: ApiCredentials) -> None:
    if not credentials.api_key.strip() or not credentials.folder_id.strip():
        raise ValueError("Yandex Search API credential and folder must be non-empty")
    if not credentials.billing_active:
        raise ValueError("active billing must be confirmed before Yandex Search API calls")


def _request_body(row: Mapping[str, str], folder_id: str) -> dict[str, object]:
    user_agent = (
        "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36"
        if row["device"] == "mobile"
        else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    return {
        "query": {
            "searchType": "SEARCH_TYPE_RU",
            "queryText": row["query"],
            "familyMode": "FAMILY_MODE_MODERATE",
            "page": "0",
            "fixTypoMode": "FIX_TYPO_MODE_ON",
        },
        "sortSpec": {"sortMode": "SORT_MODE_BY_RELEVANCE"},
        "groupSpec": {
            "groupMode": "GROUP_MODE_FLAT",
            "groupsOnPage": "10",
            "docsInGroup": "1",
        },
        "region": "16",
        "l10N": "LOCALIZATION_RU",
        "folderId": folder_id,
        "responseFormat": "FORMAT_XML",
        "userAgent": user_agent,
    }


def _batch_sha256(queue_rows: Sequence[Mapping[str, str]], folder_id: str) -> str:
    snapshot = {
        "queue": list(queue_rows),
        "requests": [
            {
                "query_id": row["query_id"],
                "body": _request_body(row, folder_id),
            }
            for row in queue_rows
        ],
    }
    return _canonical_sha256(snapshot)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _organic_record(row: Mapping[str, str], xml_text: str, checked_at: str) -> dict[str, object]:
    root = _validate_xml(xml_text, row["query_id"])
    results: list[dict[str, object]] = []
    for element in root.iter():
        if _local_name(element.tag) != "doc":
            continue
        url_element = next(
            (child for child in element if _local_name(child.tag) == "url"),
            None,
        )
        title_element = next(
            (child for child in element if _local_name(child.tag) == "title"),
            None,
        )
        url = "" if url_element is None else "".join(url_element.itertext()).strip()
        title = "" if title_element is None else "".join(title_element.itertext()).strip()
        if not url or not title:
            continue
        result = {"rank": len(results) + 1, "url": url, "title": title}
        validate_organic_result(result, row["query_id"])
        results.append(result)
        if len(results) == 10:
            break
    return {
        "query_id": row["query_id"],
        "query": row["query"],
        "region": row["region"],
        "device": row["device"],
        "checked_at": checked_at,
        "results": results,
    }


def _validate_xml(xml_text: str, query_id: str) -> ET.Element:
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Yandex Search API returned invalid XML for {query_id}") from exc


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _write_exclusive(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="") as handle:
            handle.write(value)
    except FileExistsError as exc:
        raise ValueError(f"immutable raw file already exists: {path.name}") from exc
