"""Registration of immutable raw semantic-data sources."""

from __future__ import annotations

import hashlib
import json
import os
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


def _validate_collected_at(value: str) -> str:
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
    return files


def register_source(path: Path, source: str, collected_at: str, manifest_path: Path) -> SourceManifestEntry:
    """Hash and register a raw source file without modifying the source itself."""
    source_path = path.resolve()
    target_manifest = manifest_path.resolve()
    if _contains_secret_like_name(source_path):
        raise ValueError("secret-like filename cannot be registered")
    if not source_path.is_file():
        raise ValueError(f"source file does not exist: {path}")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")

    timestamp = _validate_collected_at(collected_at)
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
    entries = [item for item in entries if item.get("path") != entry.path]
    entries.append(asdict(entry))
    entries.sort(key=lambda item: str(item["path"]))
    target_manifest.parent.mkdir(parents=True, exist_ok=True)
    target_manifest.write_text(
        json.dumps({"files": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return entry
