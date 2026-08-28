"""Validate and summarize the final paid Yandex SERP evidence bundle."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .reviewed_service_architecture import FINALIZATION_SERP_QUERIES


AUDIT_COLUMNS = (
    "query_id",
    "destination_id",
    "query",
    "decision",
    "result_count",
    "modifier_specific_results",
    "pipe_overlap",
    "evidence_ref",
    "rationale",
)


@dataclass(frozen=True)
class FinalizationAuditRow:
    query_id: str
    destination_id: str
    query: str
    decision: str
    result_count: int
    modifier_specific_results: int
    pipe_overlap: int
    evidence_ref: str
    rationale: str


def _evidence_dir(data_root: Path) -> Path:
    return data_root / "raw" / "expanded-serp-finalization"


def _expected_manifest_paths() -> set[str]:
    paths = {"serp-queue.csv"}
    for probe in FINALIZATION_SERP_QUERIES:
        paths.add(f"yandex-api-{probe.query_id}-operation.json")
        paths.add(f"yandex-api-{probe.query_id}.jsonl")
    return paths


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_queue(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_result(path: Path) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"SERP result must contain exactly one JSONL record: {path.name}")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise ValueError(f"SERP result must be an object: {path.name}")
    return payload


def validate_finalization_serp_evidence(data_root: Path) -> list[str]:
    """Check manifest hashes, exact queue identity and ten-result coverage."""

    base = _evidence_dir(data_root)
    manifest_path = base / "source-manifest.json"
    errors: list[str] = []
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"unable to read finalization manifest: {exc}"]
    entries = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        return ["finalization manifest must contain a files array"]
    by_path: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append("finalization manifest contains an invalid entry")
            continue
        path = entry["path"]
        if path in by_path:
            errors.append(f"duplicate finalization manifest path: {path}")
        by_path[path] = entry
    expected = _expected_manifest_paths()
    if set(by_path) != expected:
        missing = sorted(expected - set(by_path))
        extra = sorted(set(by_path) - expected)
        errors.append(f"finalization manifest inventory mismatch: missing={missing}, extra={extra}")
    for relative_path, entry in by_path.items():
        target = (base / relative_path).resolve()
        if base.resolve() not in target.parents:
            errors.append(f"finalization manifest path escapes evidence root: {relative_path}")
            continue
        if not target.is_file():
            errors.append(f"finalization evidence file is missing: {relative_path}")
            continue
        data = target.read_bytes()
        if entry.get("byte_count") != len(data):
            errors.append(f"byte count mismatch: {relative_path}")
        if entry.get("sha256") != hashlib.sha256(data).hexdigest():
            errors.append(f"hash mismatch: {relative_path}")
        expected_source = (
            "serp_api_queue"
            if relative_path == "serp-queue.csv"
            else "serp_api_operation"
            if relative_path.endswith("-operation.json")
            else "serp"
        )
        if entry.get("source") != expected_source:
            errors.append(f"unexpected source type for {relative_path}")

    queue_path = base / "serp-queue.csv"
    try:
        queue = _load_queue(queue_path)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"unable to read finalization queue: {exc}")
        queue = []
    expected_probes = list(FINALIZATION_SERP_QUERIES)
    if len(queue) != len(expected_probes):
        errors.append("finalization queue must contain exactly eight probes")
    for index, probe in enumerate(expected_probes):
        if index >= len(queue):
            break
        row = queue[index]
        expected_values = {
            "query_id": probe.query_id,
            "destination_id": probe.destination_id,
            "query": probe.query,
        }
        for field, expected_value in expected_values.items():
            if row.get(field) != expected_value:
                errors.append(f"finalization queue mismatch at {probe.query_id}: {field}")

        result_path = base / f"yandex-api-{probe.query_id}.jsonl"
        try:
            payload = _load_result(result_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"unable to read {probe.query_id} result: {exc}")
            continue
        if payload.get("query_id") != probe.query_id or payload.get("query") != probe.query:
            errors.append(f"SERP result identity mismatch: {probe.query_id}")
        results = payload.get("results")
        if not isinstance(results, list) or len(results) != 10:
            errors.append(f"SERP result must have ten entries: {probe.query_id}")
            continue
        ranks = [item.get("rank") for item in results if isinstance(item, dict)]
        if ranks != list(range(1, 11)):
            errors.append(f"SERP ranks are invalid: {probe.query_id}")
        if any(
            not isinstance(item, dict)
            or not isinstance(item.get("url"), str)
            or not item["url"].strip()
            or not isinstance(item.get("title"), str)
            for item in results
        ):
            errors.append(f"SERP result contains an incomplete entry: {probe.query_id}")
    return sorted(set(errors))


_MODIFIER_ROOTS: dict[str, tuple[str, ...]] = {
    "Q000273": ("вредител", "болезн"),
    "Q000274": ("культив", "вспаш"),
    "Q000275": ("грунт",),
    "Q000276": ("деревян", "бревн"),
    "Q000277": ("пластик",),
    "Q000278": ("сталь", "стальн", "металл"),
    "Q000279": ("железобет", "жб"),
    "Q000280": ("парков", "площадк"),
}


def _specific_count(query_id: str, results: list[dict[str, Any]]) -> int:
    roots = _MODIFIER_ROOTS[query_id]
    return sum(
        any(root in str(item.get("title", "")).casefold() for root in roots)
        for item in results
    )


def build_finalization_serp_audit(data_root: Path) -> list[FinalizationAuditRow]:
    """Build the deterministic eight-row review after evidence validation."""

    errors = validate_finalization_serp_evidence(data_root)
    if errors:
        raise ValueError("; ".join(errors))
    base = _evidence_dir(data_root)
    result_sets: dict[str, set[str]] = {}
    result_payloads: dict[str, list[dict[str, Any]]] = {}
    for probe in FINALIZATION_SERP_QUERIES:
        payload = _load_result(base / f"yandex-api-{probe.query_id}.jsonl")
        results = payload["results"]
        result_payloads[probe.query_id] = results
        result_sets[probe.query_id] = {str(item["url"]).split("#", 1)[0] for item in results}

    pipe_ids = ("Q000277", "Q000278", "Q000279")
    rows: list[FinalizationAuditRow] = []
    for probe in FINALIZATION_SERP_QUERIES:
        overlaps = [
            len(result_sets[probe.query_id] & result_sets[other])
            for other in pipe_ids
            if probe.query_id in pipe_ids and other != probe.query_id
        ]
        results = result_payloads[probe.query_id]
        rows.append(
            FinalizationAuditRow(
                query_id=probe.query_id,
                destination_id=probe.destination_id,
                query=probe.query,
                decision=probe.decision,
                result_count=len(results),
                modifier_specific_results=_specific_count(probe.query_id, results),
                pipe_overlap=max(overlaps, default=0),
                evidence_ref=probe.evidence_ref,
                rationale=probe.rationale,
            )
        )
    return rows


def write_finalization_serp_audit(data_root: Path, output: Path) -> int:
    """Write the reviewed evidence ledger as deterministic UTF-8 CSV."""

    rows = build_finalization_serp_audit(data_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    return len(rows)
