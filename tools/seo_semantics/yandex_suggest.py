"""Bounded, resumable Yandex Suggest expansion for the reviewed SEO silo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .expanded_architecture import ExpandedPage, all_expanded_pages
from .manifest import register_source, validate_collected_at, validate_manifest
from .reviewed_service_architecture import all_reviewed_children


SUGGEST_ENDPOINT = "https://suggest.yandex.ru/suggest-ya.cgi"
MAX_REQUESTS = 150
QUEUE_COLUMNS = (
    "query_id",
    "seed",
    "service_id",
    "destination_id",
    "page_role",
    "region_id",
    "reason",
)
ASSIGNMENT_COLUMNS = (
    "query_normalized",
    "query",
    "service_id",
    "destination_id",
    "page_role",
    "assignment_status",
    "conflicting_destination_ids",
    "source_query_ids",
    "source_seeds",
)


class SuggestTransport(Protocol):
    def fetch(self, seed: str, region_id: int) -> object: ...


class UrllibSuggestTransport:
    """Small public-suggestion transport with no credential or cookie handling."""

    def fetch(self, seed: str, region_id: int) -> object:
        url = f"{SUGGEST_ENDPOINT}?{urlencode({'v': '4', 'part': seed, 'lr': region_id})}"
        request = Request(url, headers={"User-Agent": "exp76-semantic-audit/1.0"})
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ValueError(f"Yandex Suggest returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise ValueError("Yandex Suggest request failed") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Yandex Suggest returned invalid UTF-8 JSON") from exc


def _normalized(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _root_seed(title: str) -> str:
    value = title.casefold().replace("–", " ").replace("—", " ")
    return " ".join(value.split())


def build_expanded_suggest_queue(
    *,
    start_query_number: int,
    region_id: int = 10841,
) -> list[dict[str, str]]:
    """Build one discovery probe per page plus one commercial probe per child."""

    return _build_suggest_queue(
        all_expanded_pages(),
        start_query_number=start_query_number,
        region_id=region_id,
        reason_prefix="expanded_suggest",
    )


def build_reviewed_suggest_queue(
    *,
    start_query_number: int,
    region_id: int = 10841,
) -> list[dict[str, str]]:
    """Build two free Suggest probes for every final publishable child."""

    return _build_suggest_queue(
        all_reviewed_children(),
        start_query_number=start_query_number,
        region_id=region_id,
        reason_prefix="reviewed_suggest",
    )


def _build_suggest_queue(
    pages: Sequence[ExpandedPage],
    *,
    start_query_number: int,
    region_id: int,
    reason_prefix: str,
) -> list[dict[str, str]]:
    """Build a bounded queue from an explicit immutable page sequence."""

    if start_query_number < 1:
        raise ValueError("start_query_number must be positive")
    if region_id <= 0:
        raise ValueError("region_id must be positive")
    rows: list[dict[str, str]] = []
    query_number = start_query_number
    for page in pages:
        probes = [
            (
                _root_seed(page.title)
                if page.page_role == "child_service"
                else page.representative_query,
                "root",
            )
        ]
        if page.page_role == "child_service":
            transactional = page.representative_query
            if _normalized(transactional) == _normalized(probes[0][0]):
                transactional = f"{transactional} цена"
            probes.append((transactional, "transactional"))
        for seed, kind in probes:
            rows.append(
                {
                    "query_id": f"YS{query_number:06d}",
                    "seed": seed,
                    "service_id": page.service_id,
                    "destination_id": page.destination_id,
                    "page_role": page.page_role,
                    "region_id": str(region_id),
                    "reason": f"{reason_prefix}_{kind}[{page.destination_id}]",
                }
            )
            query_number += 1
    _validate_queue(rows)
    return rows


def write_expanded_suggest_queue(
    output: Path,
    *,
    start_query_number: int,
    region_id: int = 10841,
) -> int:
    """Write the exact UTF-8 collection queue."""

    rows = build_expanded_suggest_queue(
        start_query_number=start_query_number,
        region_id=region_id,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_reviewed_suggest_queue(
    output: Path,
    *,
    start_query_number: int,
    region_id: int = 10841,
) -> int:
    """Write the exact production-child Suggest queue as UTF-8 CSV."""

    rows = build_reviewed_suggest_queue(
        start_query_number=start_query_number,
        region_id=region_id,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def read_suggest_queue(path: Path) -> list[dict[str, str]]:
    """Read and validate a previously committed suggest queue."""

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != QUEUE_COLUMNS:
                raise ValueError("suggest queue columns differ")
            rows = [dict(row) for row in reader]
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"unable to read suggest queue: {exc}") from exc
    _validate_queue(rows)
    return rows


def collect_suggestions(
    queue_rows: Sequence[Mapping[str, str]],
    raw_dir: Path,
    manifest_path: Path,
    collected_at: str,
    *,
    transport: SuggestTransport | None = None,
    pause_seconds: float = 0.25,
) -> tuple[Path, ...]:
    """Collect only missing queue rows and persist immutable JSONL evidence."""

    rows = [dict(row) for row in queue_rows]
    _validate_queue(rows)
    validate_collected_at(collected_at)
    raw_dir.mkdir(parents=True, exist_ok=True)
    client = transport or UrllibSuggestTransport()
    written: list[Path] = []
    for index, row in enumerate(rows):
        path = raw_dir / f"yandex-suggest-{row['query_id']}.jsonl"
        if path.exists():
            _load_record(path, row, manifest_path)
            continue
        payload = client.fetch(row["seed"], int(row["region_id"]))
        suggestions = _suggestions_from_payload(payload, row["seed"])
        record: dict[str, object] = {
            **row,
            "checked_at": collected_at,
            "suggestions": suggestions,
        }
        _write_exclusive(
            path,
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n",
        )
        register_source(path, "yandex_suggest", collected_at, manifest_path)
        written.append(path)
        if index + 1 < len(rows) and pause_seconds:
            time.sleep(pause_seconds)
    return tuple(written)


def load_suggestion_evidence(
    queue_rows: Sequence[Mapping[str, str]],
    raw_dir: Path,
    manifest_path: Path,
) -> dict[str, dict[str, object]]:
    """Require exact queue coverage and manifest-bound raw payloads."""

    rows = [dict(row) for row in queue_rows]
    _validate_queue(rows)
    validate_manifest(manifest_path)
    expected_files = {
        f"yandex-suggest-{row['query_id']}.jsonl": row for row in rows
    }
    actual_files = {path.name: path for path in raw_dir.glob("yandex-suggest-*.jsonl")}
    if set(actual_files) != set(expected_files):
        missing = sorted(set(expected_files) - set(actual_files))
        extra = sorted(set(actual_files) - set(expected_files))
        raise ValueError(
            "suggest evidence coverage differs: "
            f"missing={','.join(missing)} extra={','.join(extra)}"
        )
    evidence: dict[str, dict[str, object]] = {}
    for filename, row in expected_files.items():
        record = _load_record(actual_files[filename], row, manifest_path)
        evidence[row["query_id"]] = record
    return evidence


def suggestion_assignments(
    queue_rows: Sequence[Mapping[str, str]],
    evidence: Mapping[str, Mapping[str, object]],
) -> list[dict[str, str]]:
    """Deduplicate suggestions while surfacing sibling ownership conflicts."""

    rows = [dict(row) for row in queue_rows]
    _validate_queue(rows)
    queue_by_id = {row["query_id"]: row for row in rows}
    if set(evidence) != set(queue_by_id):
        raise ValueError("suggest assignment evidence coverage differs from queue")
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    owners: dict[str, set[str]] = {}
    for query_id, queue_row in queue_by_id.items():
        record = evidence[query_id]
        suggestions = record.get("suggestions")
        if not isinstance(suggestions, list):
            raise ValueError(f"suggestions must be an array: {query_id}")
        for suggestion in suggestions:
            if not isinstance(suggestion, str) or not suggestion.strip():
                raise ValueError(f"blank suggestion: {query_id}")
            normalized = _normalized(suggestion)
            owners.setdefault(normalized, set()).add(queue_row["destination_id"])
            key = (queue_row["destination_id"], queue_row["service_id"], normalized)
            aggregate = grouped.setdefault(
                key,
                {
                    "query": suggestion.strip(),
                    "page_role": queue_row["page_role"],
                    "query_ids": [],
                    "seeds": [],
                },
            )
            aggregate["query_ids"].append(query_id)  # type: ignore[union-attr]
            aggregate["seeds"].append(queue_row["seed"])  # type: ignore[union-attr]
    result: list[dict[str, str]] = []
    for (destination_id, service_id, normalized), aggregate in sorted(grouped.items()):
        conflicts = sorted(owners[normalized])
        result.append(
            {
                "query_normalized": normalized,
                "query": str(aggregate["query"]),
                "service_id": service_id,
                "destination_id": destination_id,
                "page_role": str(aggregate["page_role"]),
                "assignment_status": (
                    "needs_destination_review" if len(conflicts) > 1 else "candidate"
                ),
                "conflicting_destination_ids": "|".join(conflicts) if len(conflicts) > 1 else "",
                "source_query_ids": "|".join(dict.fromkeys(aggregate["query_ids"])),  # type: ignore[arg-type]
                "source_seeds": "|".join(dict.fromkeys(aggregate["seeds"])),  # type: ignore[arg-type]
            }
        )
    return result


def write_suggestion_assignments(output: Path, rows: Sequence[Mapping[str, str]]) -> int:
    """Write processed suggestion candidates without changing their ownership status."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ASSIGNMENT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _validate_queue(rows: Sequence[Mapping[str, str]]) -> None:
    if not rows or len(rows) > MAX_REQUESTS:
        raise ValueError(f"suggest queue must contain 1-{MAX_REQUESTS} rows")
    seen_ids: set[str] = set()
    for row in rows:
        if set(row) != set(QUEUE_COLUMNS):
            raise ValueError("suggest queue row columns differ")
        query_id = row["query_id"].strip()
        if not re.fullmatch(r"YS\d{6}", query_id) or query_id in seen_ids:
            raise ValueError(f"invalid or duplicate suggest query id: {query_id!r}")
        seen_ids.add(query_id)
        if not all(row[field].strip() for field in QUEUE_COLUMNS):
            raise ValueError(f"suggest queue row contains a blank field: {query_id}")
        if row["service_id"] not in {f"S{index}" for index in range(1, 9)}:
            raise ValueError(f"invalid suggest service id: {query_id}")
        if row["page_role"] not in {"hub", "child_service", "article"}:
            raise ValueError(f"invalid suggest page role: {query_id}")
        try:
            region_id = int(row["region_id"])
        except ValueError as exc:
            raise ValueError(f"invalid suggest region id: {query_id}") from exc
        if region_id <= 0:
            raise ValueError(f"invalid suggest region id: {query_id}")


def _suggestions_from_payload(payload: object, seed: str) -> list[str]:
    if (
        not isinstance(payload, list)
        or len(payload) < 2
        or not isinstance(payload[0], str)
        or _normalized(payload[0]) != _normalized(seed)
        or not isinstance(payload[1], list)
    ):
        raise ValueError("Yandex Suggest response differs from requested seed")
    suggestions: list[str] = []
    seen: set[str] = set()
    for value in payload[1]:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Yandex Suggest returned a blank suggestion")
        normalized = _normalized(value)
        if normalized not in seen:
            seen.add(normalized)
            suggestions.append(value.strip())
    return suggestions


def _manifest_entries(manifest_path: Path) -> dict[str, Mapping[str, object]]:
    validate_manifest(manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {str(item["path"]): item for item in payload["files"]}


def _load_record(
    path: Path,
    expected: Mapping[str, str],
    manifest_path: Path,
) -> dict[str, object]:
    entries = _manifest_entries(manifest_path)
    relative = path.resolve().relative_to(manifest_path.resolve().parent).as_posix()
    manifest = entries.get(relative)
    data = path.read_bytes()
    if (
        manifest is None
        or manifest.get("source") != "yandex_suggest"
        or manifest.get("byte_count") != len(data)
        or manifest.get("sha256") != hashlib.sha256(data).hexdigest()
    ):
        raise ValueError(f"suggest manifest hash differs: {path.name}")
    try:
        text = data.decode("utf-8")
        lines = [line for line in text.splitlines() if line]
        if len(lines) != 1:
            raise ValueError("expected one JSONL record")
        record = json.loads(lines[0])
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid suggest evidence {path.name}: {exc}") from exc
    if not isinstance(record, dict):
        raise ValueError(f"invalid suggest evidence object: {path.name}")
    expected_keys = set(QUEUE_COLUMNS) | {"checked_at", "suggestions"}
    if set(record) != expected_keys:
        raise ValueError(f"invalid suggest evidence shape: {path.name}")
    for field in QUEUE_COLUMNS:
        if record.get(field) != expected[field]:
            raise ValueError(f"suggest evidence differs from queue: {path.name}")
    validate_collected_at(record.get("checked_at"))  # type: ignore[arg-type]
    suggestions = record.get("suggestions")
    if not isinstance(suggestions, list):
        raise ValueError(f"suggestions must be an array: {path.name}")
    for suggestion in suggestions:
        if not isinstance(suggestion, str) or not suggestion.strip():
            raise ValueError(f"blank suggestion: {path.name}")
    return record


def _write_exclusive(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="") as handle:
            handle.write(value)
    except FileExistsError as exc:
        raise ValueError(f"suggest evidence already exists: {path.name}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    """Run guarded queue, collection, verification and processing commands."""

    parser = argparse.ArgumentParser(description="Collect Yandex Suggest semantic evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    queue_parser = subparsers.add_parser("queue")
    queue_parser.add_argument("--output", type=Path, required=True)
    queue_parser.add_argument("--manifest", type=Path, required=True)
    queue_parser.add_argument("--collected-at", required=True)
    queue_parser.add_argument("--start", type=int, default=1)
    queue_parser.add_argument("--region-id", type=int, default=10841)

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--queue", type=Path, required=True)
    collect_parser.add_argument("--raw-dir", type=Path, required=True)
    collect_parser.add_argument("--manifest", type=Path, required=True)
    collect_parser.add_argument("--collected-at", required=True)
    collect_parser.add_argument("--pause", type=float, default=0.25)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--queue", type=Path, required=True)
    verify_parser.add_argument("--raw-dir", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)

    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("--queue", type=Path, required=True)
    process_parser.add_argument("--raw-dir", type=Path, required=True)
    process_parser.add_argument("--manifest", type=Path, required=True)
    process_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "queue":
        count = write_expanded_suggest_queue(
            args.output,
            start_query_number=args.start,
            region_id=args.region_id,
        )
        register_source(args.output, "suggest_queue", args.collected_at, args.manifest)
        print(f"wrote {count} suggest queue rows")
        return 0
    rows = read_suggest_queue(args.queue)
    if args.command == "collect":
        if args.pause < 0:
            raise ValueError("pause must not be negative")
        written = collect_suggestions(
            rows,
            args.raw_dir,
            args.manifest,
            args.collected_at,
            pause_seconds=args.pause,
        )
        print(f"wrote {len(written)} suggest evidence files")
        return 0
    evidence = load_suggestion_evidence(rows, args.raw_dir, args.manifest)
    if args.command == "verify":
        print(f"verified {len(evidence)} suggest evidence files")
        return 0
    assignments = suggestion_assignments(rows, evidence)
    count = write_suggestion_assignments(args.output, assignments)
    print(f"wrote {count} suggestion assignment candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
