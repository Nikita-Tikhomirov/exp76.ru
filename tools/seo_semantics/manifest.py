"""Registration of immutable raw semantic-data sources."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


_SECRET_LIKE_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "cookie",
    "credential",
    "пароль",
    "токен",
)


@dataclass(frozen=True)
class SourceManifestEntry:
    path: str
    source: str
    collected_at: str
    sha256: str
    byte_count: int


def validate_collected_at(value: str) -> str:
    """Validate and return an offset-aware ISO-8601 collection timestamp."""
    if not isinstance(value, str):
        raise ValueError("collected_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("collected_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("collected_at must include a timezone offset")
    return value


def _contains_secret_like_name(path: Path) -> bool:
    name = path.name.casefold()
    return any(part in name for part in _SECRET_LIKE_PARTS)


def _load_entries(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read source manifest: {exc}") from exc
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError("source manifest must contain a files array")

    seen_paths: set[str] = set()
    for index, item in enumerate(files):
        for field in ("path", "source", "collected_at", "sha256"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"source manifest entry {index} requires a non-empty string: {field}"
                )
        try:
            validate_collected_at(item["collected_at"])
        except ValueError as exc:
            raise ValueError(
                f"source manifest entry {index} has invalid collected_at"
            ) from exc
        sha256 = item["sha256"]
        if len(sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in sha256
        ):
            raise ValueError(f"source manifest entry {index} has invalid sha256")
        byte_count = item.get("byte_count")
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
            raise ValueError(f"source manifest entry {index} has invalid byte_count")
        path = item["path"]
        if path in seen_paths:
            raise ValueError(f"duplicate manifest entry path: {path}")
        seen_paths.add(path)
    return files


def validate_manifest(manifest_path: Path) -> None:
    """Load and validate the manifest structure without changing it."""

    _load_entries(manifest_path.resolve())


def register_source(path: Path, source: str, collected_at: str, manifest_path: Path) -> SourceManifestEntry:
    """Hash and register a raw source file without modifying the source itself."""
    source_path = path.resolve()
    target_manifest = manifest_path.resolve()
    if source_path == target_manifest:
        raise ValueError("source file and manifest path must differ")
    if _contains_secret_like_name(source_path):
        raise ValueError("secret-like filename cannot be registered")
    if not source_path.is_file():
        raise ValueError(f"source file does not exist: {path}")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")

    timestamp = validate_collected_at(collected_at)
    data = source_path.read_bytes()
    relative_path = Path(os.path.relpath(source_path, target_manifest.parent)).as_posix()
    entry = SourceManifestEntry(
        path=relative_path,
        source=source.strip(),
        collected_at=timestamp,
        sha256=hashlib.sha256(data).hexdigest(),
        byte_count=len(data),
    )

    entries = _load_entries(target_manifest)
    existing = next((item for item in entries if item.get("path") == entry.path), None)
    if existing is not None:
        immutable_fields = {
            "path": entry.path,
            "source": entry.source,
            "sha256": entry.sha256,
            "byte_count": entry.byte_count,
        }
        if any(existing.get(key) != value for key, value in immutable_fields.items()):
            raise ValueError(f"immutable manifest entry differs for {entry.path}")
        return SourceManifestEntry(
            path=str(existing["path"]),
            source=str(existing["source"]),
            collected_at=str(existing["collected_at"]),
            sha256=str(existing["sha256"]),
            byte_count=int(existing["byte_count"]),
        )

    entries.append(asdict(entry))
    entries.sort(key=lambda item: str(item["path"]))
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    _write_manifest_atomic(target_manifest, entries)
    return entry


def _write_manifest_atomic(manifest_path: Path, entries: list[dict[str, Any]]) -> None:
    value = json.dumps({"files": entries}, ensure_ascii=False, indent=2) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            delete=False,
            dir=manifest_path.parent,
            prefix=f".{manifest_path.name}.",
            suffix=".tmp",
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, manifest_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
