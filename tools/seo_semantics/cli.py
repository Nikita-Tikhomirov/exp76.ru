"""Command-line entry points for the read-only semantic-core pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from .classify import QueryClassification, classify_query, exclusion_evidence, infer_service_id
from .ingest import load_source_csv, merge_records
from .manifest import register_source
from .models import KeywordRecord
from .normalize import normalize_query
from .scope import load_scope


_OUTPUT_COLUMNS = (
    "keyword_id",
    "query_raw",
    "query_normalized",
    "sources",
    "seed",
    "region",
    "device",
    "broad_frequency",
    "phrase_frequency",
    "exact_frequency",
    "impressions",
    "clicks",
    "ctr",
    "avg_position",
    "current_url",
    "collected_at",
)

_CLASSIFIED_OUTPUT_COLUMNS = (
    "keyword_id",
    "query_raw",
    "query_normalized",
    "service_id",
    "intent",
    "relevance",
    "exclusion_reason",
    "geo",
    "entities",
    "frozen_collision",
    "owner_url",
    "sources",
    "region",
    "device",
    "broad_frequency",
    "phrase_frequency",
    "exact_frequency",
    "impressions",
    "clicks",
    "avg_position",
    "current_url",
)

_MINUS_OUTPUT_COLUMNS = (
    "scope",
    "service_id",
    "word",
    "reason",
    "source_query_ids",
    "status",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.seo_semantics.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    validate_scope = commands.add_parser("validate-scope")
    validate_scope.add_argument("--scope", required=True, type=Path)

    register = commands.add_parser("register-source")
    register.add_argument("--file", required=True, type=Path)
    register.add_argument("--source", required=True)
    register.add_argument("--collected-at", required=True)
    register.add_argument("--manifest", required=True, type=Path)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("--scope", required=True, type=Path)
    ingest.add_argument("--manifest", required=True, type=Path)
    ingest.add_argument("--output", required=True, type=Path)

    classify = commands.add_parser("classify")
    classify.add_argument("--scope", required=True, type=Path)
    classify.add_argument("--input", required=True, type=Path)
    classify.add_argument("--output", required=True, type=Path)
    classify.add_argument("--frozen-output", required=True, type=Path)
    classify.add_argument("--minus-output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "validate-scope":
            scope = load_scope(args.scope)
            print(f"scope valid: {len(scope.services)} services, {len(scope.frozen_urls)} frozen URLs")
        elif args.command == "register-source":
            entry = register_source(args.file, args.source, args.collected_at, args.manifest)
            print(json.dumps(entry.__dict__, ensure_ascii=False, sort_keys=True))
        elif args.command == "ingest":
            count = _ingest(args.scope, args.manifest, args.output)
            print(f"ingested {count} keyword rows")
        elif args.command == "classify":
            clean_count, frozen_count, minus_count = _classify(
                args.scope,
                args.input,
                args.output,
                args.frozen_output,
                args.minus_output,
            )
            print(
                f"classified {clean_count + frozen_count} keyword rows: "
                f"clean={clean_count}, frozen={frozen_count}, minus={minus_count}"
            )
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _ingest(scope_path: Path, manifest_path: Path, output_path: Path) -> int:
    load_scope(scope_path)
    entries = _load_manifest_entries(manifest_path)
    wordstat_coverage_path = (manifest_path.parent / "wordstat" / "coverage.csv").resolve()
    wordstat_routes = _load_wordstat_routes(wordstat_coverage_path)
    wordstat_context = {
        row["raw_file"]: row
        for row in wordstat_routes
        if row.get("raw_file")
    }
    wordcraft_context = _load_wordcraft_context(manifest_path.parent / "wordcraft" / "coverage.csv")
    records: list[KeywordRecord] = []

    for entry in entries:
        path = (manifest_path.parent / entry["path"]).resolve()
        _verify_registered_file(path, entry)
        source = entry["source"]
        if source == "webmaster" and path.suffix.casefold() == ".csv":
            loaded = load_source_csv(
                path,
                source,
                {
                    "query": "Query",
                    "impressions": "Impressions",
                    "clicks": "Clicks",
                    "ctr": "CTR %",
                    "avg_position": "Avg. position",
                },
            )
            records.extend(replace(record, collected_at=entry["collected_at"]) for record in loaded)
        elif source == "wordstat" and path == wordstat_coverage_path:
            records.extend(_wordstat_head_records(wordstat_routes, path))
        elif source == "wordstat" and path.name.startswith("top-"):
            context = wordstat_context.get(path.name)
            if context is None:
                raise ValueError(f"{path.name}: missing Wordstat coverage entry")
            loaded = load_source_csv(
                path,
                source,
                {"query": "Запросы со словами", "broad_frequency": "Число запросов"},
            )
            records.extend(
                replace(
                    record,
                    seed=context["seed"],
                    region=context["region"],
                    device="all",
                    collected_at=entry["collected_at"],
                )
                for record in loaded
            )
        elif source == "wordcraft" and path.name.endswith("-dom.csv"):
            context = wordcraft_context.get(_wordcraft_key(path.name))
            if context is None:
                raise ValueError(f"{path.name}: missing Wordcraft coverage entry")
            loaded = load_source_csv(
                path,
                source,
                {
                    "query": "query",
                    "broad_frequency": "demand",
                    "region": "region",
                    "device": "device",
                    "collected_at": "collected_at",
                },
            )
            records.extend(
                replace(
                    record,
                    seed=context["seed"],
                    current_url=context["target_url"],
                    collected_at=record.collected_at or entry["collected_at"],
                )
                for record in loaded
            )

    merged = merge_records(records)
    _write_keyword_csv(output_path, merged)
    return len(merged)


def _classify(
    scope_path: Path,
    input_path: Path,
    output_path: Path,
    frozen_output_path: Path,
    minus_output_path: Path,
) -> tuple[int, int, int]:
    scope = load_scope(scope_path)
    rows = _read_keyword_rows(input_path)
    service_urls = {service.current_url: service.service_id for service in scope.services}
    clean_rows: list[dict[str, str]] = []
    frozen_rows: list[dict[str, str]] = []
    minus_evidence: dict[tuple[str, str, str, str], set[str]] = {}

    for row in rows:
        service_hint = (
            service_urls.get(row.get("current_url", ""), "")
            or infer_service_id(row.get("seed", ""))
            or infer_service_id(row["query_normalized"])
        )
        decision = classify_query(row["query_raw"], service_hint, scope)
        if _positive_integer(row.get("clicks", "")) and not decision.service_id and not decision.owner_url:
            decision = replace(decision, service_id="S1")
        classified_row = _classified_row(row, decision)
        target = frozen_rows if decision.frozen_collision else clean_rows
        target.append(classified_row)
        for word in exclusion_evidence(row["query_raw"], decision.exclusion_reason):
            key = ("global", "", word, decision.exclusion_reason)
            minus_evidence.setdefault(key, set()).add(row["keyword_id"])

    _validate_partition(rows, clean_rows, frozen_rows)
    minus_rows = [
        {
            "scope": scope_name,
            "service_id": service_id,
            "word": word,
            "reason": reason,
            "source_query_ids": "|".join(sorted(query_ids)),
            "status": "accepted_repeated_evidence",
        }
        for (scope_name, service_id, word, reason), query_ids in sorted(minus_evidence.items())
        if len(query_ids) >= 2
    ]
    _write_dict_rows(output_path, _CLASSIFIED_OUTPUT_COLUMNS, clean_rows)
    _write_dict_rows(frozen_output_path, _CLASSIFIED_OUTPUT_COLUMNS, frozen_rows)
    _write_dict_rows(minus_output_path, _MINUS_OUTPUT_COLUMNS, minus_rows)
    return len(clean_rows), len(frozen_rows), len(minus_rows)


def _read_keyword_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            required = {"keyword_id", "query_raw", "query_normalized", "sources"}
            missing = sorted(required - set(headers))
            if missing:
                raise ValueError(f"{path.name}: missing columns: {', '.join(missing)}")
            rows = list(reader)
    except OSError as exc:
        raise ValueError(f"unable to read keyword input {path}: {exc}") from exc
    keyword_ids = [row["keyword_id"] for row in rows]
    if any(not keyword_id for keyword_id in keyword_ids):
        raise ValueError(f"{path.name}: keyword_id must not be empty")
    if len(keyword_ids) != len(set(keyword_ids)):
        raise ValueError(f"{path.name}: duplicate keyword_id")
    return rows


def _classified_row(row: dict[str, str], decision: QueryClassification) -> dict[str, str]:
    return {
        "keyword_id": row["keyword_id"],
        "query_raw": row["query_raw"],
        "query_normalized": row["query_normalized"],
        "service_id": decision.service_id,
        "intent": decision.intent,
        "relevance": decision.relevance,
        "exclusion_reason": decision.exclusion_reason,
        "geo": decision.geo,
        "entities": "|".join(decision.entities),
        "frozen_collision": str(decision.frozen_collision).lower(),
        "owner_url": decision.owner_url,
        "sources": row.get("sources", ""),
        "region": row.get("region", ""),
        "device": row.get("device", ""),
        "broad_frequency": row.get("broad_frequency", ""),
        "phrase_frequency": row.get("phrase_frequency", ""),
        "exact_frequency": row.get("exact_frequency", ""),
        "impressions": row.get("impressions", ""),
        "clicks": row.get("clicks", ""),
        "avg_position": row.get("avg_position", ""),
        "current_url": row.get("current_url", ""),
    }


def _validate_partition(
    source_rows: list[dict[str, str]],
    clean_rows: list[dict[str, str]],
    frozen_rows: list[dict[str, str]],
) -> None:
    source_ids = [row["keyword_id"] for row in source_rows]
    output_ids = [row["keyword_id"] for row in clean_rows + frozen_rows]
    if len(output_ids) != len(set(output_ids)):
        raise ValueError("classification outputs contain duplicate keyword IDs")
    if set(output_ids) != set(source_ids) or len(output_ids) != len(source_ids):
        raise ValueError("classification outputs do not partition input exactly once")
    if any(row["relevance"] == "excluded" and not row["exclusion_reason"] for row in clean_rows):
        raise ValueError("excluded classification requires an explicit reason")


def _write_dict_rows(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _positive_integer(value: str) -> bool:
    if not value.strip():
        return False
    try:
        return int(float(value.replace(",", "."))) > 0
    except ValueError as exc:
        raise ValueError(f"clicks must be a non-negative number: {value!r}") from exc


def _load_manifest_entries(manifest_path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read source manifest: {exc}") from exc
    entries = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise ValueError("source manifest must contain a files array")
    return sorted(entries, key=lambda entry: str(entry.get("path", "")))


def _verify_registered_file(path: Path, entry: dict[str, object]) -> None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"unable to read registered source {path}: {exc}") from exc
    if len(data) != entry.get("byte_count"):
        raise ValueError(f"{path.name}: byte count differs from source manifest")
    if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
        raise ValueError(f"{path.name}: SHA-256 differs from source manifest")


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_wordstat_routes(path: Path) -> list[dict[str, str]]:
    return _load_csv_rows(path)


def _load_wordcraft_context(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        f"{row['run_type']}:{row['service_id']}:{row['device']}": row
        for row in rows
    }


def _wordstat_head_metric(kind: str) -> str | None:
    if kind == "phrase":
        return "phrase_frequency"
    if kind == "exact":
        return "exact_frequency"
    if kind.startswith("geo_"):
        return "broad_frequency"
    return None


def _wordstat_head_records(
    routes: list[dict[str, str]],
    coverage_path: Path,
) -> list[KeywordRecord]:
    records: list[KeywordRecord] = []
    for row_number, route in enumerate(routes, start=2):
        metric = _wordstat_head_metric(route.get("kind", ""))
        if metric is None:
            continue
        query_expr = route.get("query_expr", "").strip()
        if not query_expr:
            raise ValueError(f"{coverage_path.name}:{row_number}: query_expr must not be empty")
        row_hint = _parse_wordstat_row_hint(coverage_path, row_number, route.get("row_hint", ""))
        records.append(
            KeywordRecord(
                query_raw=query_expr,
                query_normalized=normalize_query(query_expr),
                source="wordstat",
                seed=route.get("seed", ""),
                region=route.get("region", ""),
                device="all",
                collected_at=route.get("collected_at", ""),
                **{metric: row_hint},
            )
        )
    return records


def _parse_wordstat_row_hint(path: Path, row_number: int, value: str) -> int:
    normalized = value.strip().replace(" ", "").replace("\u00a0", "")
    try:
        number = int(normalized)
    except ValueError as exc:
        raise ValueError(f"{path.name}:{row_number}: row_hint must be a non-negative integer") from exc
    if number < 0:
        raise ValueError(f"{path.name}:{row_number}: row_hint must be a non-negative integer")
    return number


def _wordcraft_key(filename: str) -> str:
    parts = filename.split("-")
    if filename.startswith("url-"):
        return f"url:{parts[1].upper()}:all"
    device = "mobile_and_tablet" if "-mobile-" in filename else "all"
    run_type = "seed_mobile" if device == "mobile_and_tablet" else "seed"
    return f"{run_type}:{parts[1].upper()}:{device}"


def _write_keyword_csv(path: Path, records: list[KeywordRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_OUTPUT_COLUMNS)
        writer.writeheader()
        for index, record in enumerate(records, start=1):
            writer.writerow(
                {
                    "keyword_id": f"K{index:06d}",
                    "query_raw": record.query_raw,
                    "query_normalized": record.query_normalized,
                    "sources": "|".join(record.sources or (record.source,)),
                    "seed": record.seed,
                    "region": record.region,
                    "device": record.device,
                    "broad_frequency": _csv_value(record.broad_frequency),
                    "phrase_frequency": _csv_value(record.phrase_frequency),
                    "exact_frequency": _csv_value(record.exact_frequency),
                    "impressions": _csv_value(record.impressions),
                    "clicks": _csv_value(record.clicks),
                    "ctr": _csv_value(record.ctr),
                    "avg_position": _csv_value(record.avg_position),
                    "current_url": record.current_url,
                    "collected_at": record.collected_at,
                }
            )


def _csv_value(value: int | float | None) -> int | float | str:
    return "" if value is None else value


if __name__ == "__main__":
    raise SystemExit(main())
