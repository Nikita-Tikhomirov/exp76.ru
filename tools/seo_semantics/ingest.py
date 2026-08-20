"""Read source CSV exports without mutating their original evidence."""

from __future__ import annotations

import csv
from dataclasses import fields, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from .models import KeywordRecord
from .normalize import normalize_query


_INTEGER_FIELDS = frozenset(
    {
        "broad_frequency",
        "phrase_frequency",
        "exact_frequency",
        "impressions",
        "clicks",
    }
)
_FLOAT_FIELDS = frozenset({"ctr", "avg_position"})
_STRING_FIELDS = frozenset(
    {field.name for field in fields(KeywordRecord)} - _INTEGER_FIELDS - _FLOAT_FIELDS - {"source", "sources"}
)
_SUPPORTED_FIELDS = _INTEGER_FIELDS | _FLOAT_FIELDS | _STRING_FIELDS


def load_source_csv(path: Path, source: str, column_map: dict[str, str]) -> list[KeywordRecord]:
    """Load a UTF-8 CSV export into immutable records from one named source."""
    query_column = column_map.get("query")
    if not query_column:
        raise ValueError("column_map requires a query column")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(8192)
            handle.seek(0)
            delimiter = _detect_delimiter(sample, query_column)
            reader = csv.DictReader(handle, delimiter=delimiter)
            headers = reader.fieldnames or []
            if query_column not in headers:
                raise ValueError(f"{path.name}: missing expected query column {query_column!r}")
            _validate_column_map(path, column_map, headers)
            return [
                _record_from_row(path, row_number, row, source, column_map)
                for row_number, row in enumerate(reader, start=2)
            ]
    except OSError as exc:
        raise ValueError(f"Unable to read source CSV {path}: {exc}") from exc


def merge_records(records: Iterable[KeywordRecord]) -> list[KeywordRecord]:
    """Group exact normalized duplicates without combining incompatible metrics."""
    grouped: dict[tuple[str, str, str, str], list[KeywordRecord]] = {}
    for record in records:
        key = (
            record.query_normalized,
            record.region,
            record.device,
            record.current_url,
        )
        grouped.setdefault(key, []).append(record)

    merged: list[KeywordRecord] = []
    for key in sorted(grouped):
        group = grouped[key]
        first = group[0]
        sources = tuple(sorted({source for record in group for source in _record_sources(record)}))
        metrics = {
            field_name: _merge_metric(group, field_name)
            for field_name in sorted(_INTEGER_FIELDS | _FLOAT_FIELDS)
        }
        seed = next((record.seed for record in group if record.seed), "")
        collected_at = next((record.collected_at for record in group if record.collected_at), "")
        merged.append(
            replace(
                first,
                **metrics,
                seed=seed,
                collected_at=collected_at,
                sources=sources,
            )
        )
    return merged


def _validate_column_map(path: Path, column_map: dict[str, str], headers: list[str]) -> None:
    unsupported = sorted(set(column_map) - _SUPPORTED_FIELDS - {"query"})
    if unsupported:
        raise ValueError(f"{path.name}: unsupported mapped fields: {', '.join(unsupported)}")
    missing = sorted(column for column in column_map.values() if column not in headers)
    if missing:
        raise ValueError(f"{path.name}: missing expected columns: {', '.join(missing)}")


def _detect_delimiter(sample: str, query_column: str) -> str:
    for delimiter in (",", ";", "\t"):
        reader = csv.reader(sample.splitlines(), delimiter=delimiter)
        headers = next(reader, [])
        if query_column in headers:
            return delimiter
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ","


def _record_from_row(
    path: Path,
    row_number: int,
    row: dict[str, str | None],
    source: str,
    column_map: dict[str, str],
) -> KeywordRecord:
    query_raw = row[column_map["query"]] or ""
    if not query_raw.strip():
        raise ValueError(f"{path.name}:{row_number}: query must not be empty")

    values: dict[str, str | int | float | None] = {
        "query_raw": query_raw,
        "query_normalized": normalize_query(query_raw),
        "source": source,
    }
    for field_name, column_name in column_map.items():
        if field_name == "query":
            continue
        raw_value = row[column_name]
        values[field_name] = _parse_value(path, row_number, field_name, raw_value)
    return KeywordRecord(**values)


def _parse_value(
    path: Path,
    row_number: int,
    field_name: str,
    raw_value: str | None,
) -> str | int | float | None:
    if raw_value is None or not raw_value.strip():
        return None if field_name in _INTEGER_FIELDS | _FLOAT_FIELDS else ""
    value = raw_value.strip()
    if field_name in _INTEGER_FIELDS:
        normalized_number = value.replace(" ", "").replace("\u00a0", "")
        try:
            decimal_number = Decimal(normalized_number.replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(f"{path.name}:{row_number}: {field_name} must be an integer") from exc
        if decimal_number != decimal_number.to_integral_value():
            raise ValueError(f"{path.name}:{row_number}: {field_name} must be an integer")
        number = int(decimal_number)
        if number < 0:
            raise ValueError(f"{path.name}:{row_number}: {field_name} must not be negative")
        return number
    if field_name in _FLOAT_FIELDS:
        try:
            return float(value.replace(" ", "").replace("\u00a0", "").replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{path.name}:{row_number}: {field_name} must be a number") from exc
    return value


def _record_sources(record: KeywordRecord) -> tuple[str, ...]:
    return record.sources or (record.source,)


def _merge_metric(group: list[KeywordRecord], field_name: str) -> int | float | None:
    observations = [
        (record.source, getattr(record, field_name))
        for record in group
        if getattr(record, field_name) is not None
    ]
    if not observations:
        return None
    if len({source for source, _ in observations}) > 1:
        return None
    return observations[0][1]
