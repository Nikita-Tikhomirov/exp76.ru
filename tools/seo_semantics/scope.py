"""Read-only manifest for the semantic-core working scope."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_EXPECTED_SERVICE_IDS = frozenset({"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"})
_EXPECTED_FROZEN_URLS = frozenset(
    {
        "https://exp76.ru/category/drenazh-uchastka/",
        "https://exp76.ru/category/otmostka-vokrug-doma/",
        "https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
        "https://exp76.ru/category/osushenie-uchastka/",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
        "https://exp76.ru/category/avtopoliv-na-uchastke/",
    }
)


@dataclass(frozen=True)
class ServiceScope:
    service_id: str
    name: str
    current_url: str


@dataclass(frozen=True)
class RegionScope:
    name: str
    wordstat_id: int | None
    priority: int


@dataclass(frozen=True)
class ScopeConfig:
    site: str
    services: tuple[ServiceScope, ...]
    frozen_urls: frozenset[str]
    regions: tuple[RegionScope, ...]


def _require_https_trailing_slash(url: Any, field: str) -> str:
    if not isinstance(url, str):
        raise ValueError(f"{field} must be a string")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or not url.endswith("/"):
        raise ValueError(f"{field} must be an HTTPS URL ending in '/': {url!r}")
    return url


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def load_scope(path: Path) -> ScopeConfig:
    """Load and validate a semantic scope manifest from JSON."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read scope manifest {path}: {exc}") from exc
    data = _require_mapping(raw, "scope")

    site = _require_https_trailing_slash(data.get("site"), "site")
    service_records = data.get("services")
    if not isinstance(service_records, list):
        raise ValueError("services must be an array")
    services: list[ServiceScope] = []
    seen_urls: set[str] = set()
    for index, record in enumerate(service_records):
        item = _require_mapping(record, f"services[{index}]")
        service_id = item.get("service_id")
        name = item.get("name")
        if not isinstance(service_id, str) or not isinstance(name, str) or not name:
            raise ValueError(f"services[{index}] requires service_id and name strings")
        current_url = _require_https_trailing_slash(item.get("current_url"), f"services[{index}].current_url")
        if current_url in seen_urls:
            raise ValueError(f"duplicate service URL: {current_url}")
        seen_urls.add(current_url)
        services.append(ServiceScope(service_id, name, current_url))
    if len(services) != len(_EXPECTED_SERVICE_IDS) or {item.service_id for item in services} != _EXPECTED_SERVICE_IDS:
        raise ValueError("services must contain exactly service IDs S1 through S8")

    frozen_records = data.get("frozen_urls")
    if not isinstance(frozen_records, list) or any(not isinstance(url, str) for url in frozen_records):
        raise ValueError("frozen_urls must be an array of strings")
    frozen_urls = frozenset(_require_https_trailing_slash(url, "frozen_urls entry") for url in frozen_records)
    if frozen_urls != _EXPECTED_FROZEN_URLS or len(frozen_records) != 6:
        raise ValueError("frozen_urls must contain exactly the six approved category URLs")

    region_records = data.get("regions")
    if not isinstance(region_records, list):
        raise ValueError("regions must be an array")
    regions: list[RegionScope] = []
    for index, record in enumerate(region_records):
        item = _require_mapping(record, f"regions[{index}]")
        name, wordstat_id, priority = item.get("name"), item.get("wordstat_id"), item.get("priority")
        if not isinstance(name, str) or not name or (wordstat_id is not None and not isinstance(wordstat_id, int)):
            raise ValueError(f"regions[{index}] has invalid name or wordstat_id")
        if not isinstance(priority, int):
            raise ValueError(f"regions[{index}].priority must be an integer")
        regions.append(RegionScope(name, wordstat_id, priority))
    return ScopeConfig(site, tuple(services), frozen_urls, tuple(regions))
