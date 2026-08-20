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

from .ingest import load_source_csv, merge_records
from .manifest import register_source
from .models import KeywordRecord
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
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _ingest(scope_path: Path, manifest_path: Path, output_path: Path) -> int:
    load_scope(scope_path)
    entries = _load_manifest_entries(manifest_path)
    wordstat_context = _load_wordstat_context(manifest_path.parent / "wordstat" / "coverage.csv")
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
        elif source == "wordstat" and path.name.startswith("top-"):
            context = wordstat_context.get(path.name)
            if context is None:
                raise ValueError(f"{path.name}: missing Wordstat coverage entry")
            metric = _wordstat_metric(context["kind"])
            loaded = load_source_csv(
                path,
                source,
                {"query": "Запросы со словами", metric: "Число запросов"},
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


def _load_csv_by_key(path: Path, key: str) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row[key]: row for row in rows if row.get(key)}


def _load_wordstat_context(path: Path) -> dict[str, dict[str, str]]:
    return _load_csv_by_key(path, "raw_file")


def _load_wordcraft_context(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        f"{row['run_type']}:{row['service_id']}:{row['device']}": row
        for row in rows
    }


def _wordstat_metric(kind: str) -> str:
    if kind == "phrase":
        return "phrase_frequency"
    if kind == "exact":
        return "exact_frequency"
    return "broad_frequency"


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
