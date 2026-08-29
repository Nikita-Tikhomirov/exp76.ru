"""Create the content-validation ledger for all 15 service hubs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from tools.site_content.contracts import load_page_architecture

from .architecture import PAGE_ARCHITECTURE_COLUMNS, PageDestination
from .complete_service_architecture import (
    COMPLETE_SERVICE_ORDER,
    build_complete_service_rows,
)
from .legacy_service_architecture import LEGACY_HUB_OWNERS
from .legacy_article_architecture import build_legacy_article_rows


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _REPOSITORY_ROOT / "seo-data" / "2026-08-exp76-services"
BASE_PAGE_ARCHITECTURE_PATH = _DATA_ROOT / "processed" / "page_architecture.csv"
DEFAULT_PAGE_ARCHITECTURE_PATH = (
    _DATA_ROOT / "processed" / "complete_page_architecture.csv"
)
DEFAULT_RELEASE_MANIFEST_PATH = (
    _REPOSITORY_ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
)
_HUB_CONTENT_DIR = _REPOSITORY_ROOT / "seo-content" / "service-hubs" / "hubs"
_CHILD_CONTENT_DIR = _REPOSITORY_ROOT / "seo-content" / "service-pages" / "pages"
_ARTICLE_CONTENT_DIR = _REPOSITORY_ROOT / "seo-content" / "legacy-articles" / "articles"
_RELEASE_ID = "service-hubs-2026-08-28"
_REVIEWER = "codex-2026-08-29"
_MERGED_BASE_ARTICLE_ID = "S1-ARTICLE-72FBB49E67C8"
_COST_ARTICLE_ID = "S1-ARTICLE-505521C7EF8C"
_COST_ARTICLE_CANONICAL = (
    "https://exp76.ru/kak-rasschitat-stoimost-blagoustrojstva-za-sotku/"
)


def _legacy_hub_destination(service_id: str) -> PageDestination:
    owner = LEGACY_HUB_OWNERS[service_id]
    return PageDestination(
        destination_id=f"{service_id}-HUB",
        service_id=service_id,
        page_role="hub",
        parent_destination_id="",
        canonical_url=owner.current_url,
        source_cluster_ids=(f"{service_id}-HUB",),
        current_url=owner.current_url,
        proposed_url="",
        primary_cluster_id=f"{service_id}-HUB",
        url_action="reuse",
        publication_status="ready",
        evidence_refs=f"{owner.business_evidence}; {owner.boundary}",
        review_status="reviewed",
        reviewer=_REVIEWER,
        rationale=(
            f"Сохраняется опубликованный владелец WP {owner.current_wp_id}; "
            "страница переводится в service-v2 hub без смены URL."
        ),
    )


def _child_destination(row: dict[str, str]) -> PageDestination:
    canonical = row["target_url"]
    action = row["url_action"]
    return PageDestination(
        destination_id=row["destination_id"],
        service_id=row["service_id"],
        page_role="child_service",
        parent_destination_id=row["parent_hub"],
        canonical_url=canonical,
        source_cluster_ids=(row["destination_id"],),
        current_url=row["current_url"],
        proposed_url=canonical if action == "create" else "",
        primary_cluster_id=row["destination_id"],
        url_action=action,
        publication_status=row["publication_status"],
        evidence_refs=(
            f"business={row['business_evidence']}; semantic={row['semantic_evidence']}"
        ),
        review_status="reviewed",
        reviewer=_REVIEWER,
        rationale=row["boundary"],
    )


def _legacy_article_destination(row: dict[str, str]) -> PageDestination:
    """Map a reviewed S9-S15 information cluster into the page ledger."""

    return PageDestination(
        destination_id=row["destination_id"],
        service_id=row["service_id"],
        page_role="article",
        parent_destination_id=row["parent_destination_id"],
        canonical_url=row["canonical_url"],
        source_cluster_ids=(row["destination_id"],),
        current_url="",
        proposed_url=row["proposed_url"],
        primary_cluster_id=row["primary_cluster_id"],
        url_action="article",
        publication_status=row["publication_status"],
        evidence_refs=row["evidence_refs"],
        review_status=row["review_status"],
        reviewer=row["reviewer"],
        rationale=row["rationale"],
    )


def validate_complete_page_destinations(
    destinations: Sequence[PageDestination],
) -> list[str]:
    """Reject duplicate ownership or an incomplete S1-S15 hierarchy."""

    errors: list[str] = []
    if len(destinations) != 112:
        errors.append("complete page destination count differs")
    ids = [item.destination_id for item in destinations]
    urls = [item.canonical_url for item in destinations]
    if len(ids) != len(set(ids)):
        errors.append("duplicate destination id")
    if len(urls) != len(set(urls)):
        errors.append("duplicate canonical url")
    roles = Counter(item.page_role for item in destinations)
    if roles != Counter(
        {
            "frozen": 6,
            "article": 23,
            "special": 3,
            "hub": 15,
            "child_service": 65,
        }
    ):
        errors.append("complete destination roles differ")
    hubs = {
        item.service_id
        for item in destinations
        if item.page_role == "hub"
    }
    if hubs != set(COMPLETE_SERVICE_ORDER):
        errors.append("complete hub ownership differs")
    if "S5-CHILD-STUMPS" in ids:
        errors.append("obsolete S5 stump child remains")
    for item in destinations:
        if item.page_role == "child_service":
            if item.parent_destination_id != f"{item.service_id}-HUB":
                errors.append(f"child parent differs: {item.destination_id}")
            if item.publication_status != "ready":
                errors.append(f"child is not architecture-ready: {item.destination_id}")
    return errors


def build_complete_page_destinations(
    base_path: Path = BASE_PAGE_ARCHITECTURE_PATH,
) -> tuple[PageDestination, ...]:
    """Combine preserved pages, exact hub owners and all approved children."""

    base = load_page_architecture(base_path)
    preserved: list[PageDestination] = []
    for item in base.values():
        if item.page_role not in {"frozen", "article", "special"}:
            continue
        if item.destination_id == _MERGED_BASE_ARTICLE_ID:
            continue
        if item.destination_id == _COST_ARTICLE_ID:
            item = replace(
                item,
                canonical_url=_COST_ARTICLE_CANONICAL,
                proposed_url=_COST_ARTICLE_CANONICAL,
            )
        preserved.append(item)
    legacy_articles = [
        _legacy_article_destination(row)
        for row in build_legacy_article_rows()
    ]
    reviewed_hubs = {
        item.service_id: item
        for item in base.values()
        if item.page_role == "hub"
    }
    hubs = [
        reviewed_hubs[service_id]
        if service_id in reviewed_hubs
        else _legacy_hub_destination(service_id)
        for service_id in COMPLETE_SERVICE_ORDER
    ]
    children = [
        _child_destination(row)
        for row in build_complete_service_rows()
    ]
    destinations = tuple((*preserved, *legacy_articles, *hubs, *children))
    errors = validate_complete_page_destinations(destinations)
    if errors:
        raise ValueError("; ".join(errors))
    return destinations


def _row(destination: PageDestination) -> dict[str, str]:
    return {
        "destination_id": destination.destination_id,
        "service_id": destination.service_id,
        "page_role": destination.page_role,
        "parent_destination_id": destination.parent_destination_id,
        "current_url": destination.current_url,
        "proposed_url": destination.proposed_url,
        "canonical_url": destination.canonical_url,
        "primary_cluster_id": destination.primary_cluster_id,
        "source_cluster_ids": "|".join(destination.source_cluster_ids),
        "url_action": destination.url_action,
        "publication_status": destination.publication_status,
        "evidence_refs": destination.evidence_refs,
        "review_status": destination.review_status,
        "reviewer": destination.reviewer,
        "rationale": destination.rationale,
    }


def write_complete_page_architecture(
    output_path: Path = DEFAULT_PAGE_ARCHITECTURE_PATH,
) -> int:
    """Write a deterministic UTF-8 CSV accepted by content contracts."""

    destinations = build_complete_page_destinations()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PAGE_ARCHITECTURE_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(_row(destination) for destination in destinations)
    return len(destinations)


def _content_artifact_keys() -> set[str]:
    """Return page keys backed by a complete local production content source."""

    keys: set[str] = set()
    for directory, key_field in (
        (_HUB_CONTENT_DIR, "page_key"),
        (_CHILD_CONTENT_DIR, "destination_id"),
        (_ARTICLE_CONTENT_DIR, "destination_id"),
    ):
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            page_key = payload.get(key_field) if isinstance(payload, dict) else None
            if not isinstance(page_key, str) or not page_key:
                raise ValueError(f"content artifact has no {key_field}: {path}")
            if page_key in keys:
                raise ValueError(f"duplicate content artifact owner: {page_key}")
            keys.add(page_key)
    return keys


def build_release_manifest() -> dict[str, object]:
    """Build the reconciled draft release inventory for all 112 destinations."""

    destinations = build_complete_page_destinations()
    content_keys = _content_artifact_keys()
    ready_managed = {
        item.destination_id
        for item in destinations
        if item.page_role in {"hub", "child_service", "article"}
        and item.publication_status == "ready"
    }
    if content_keys != ready_managed:
        missing = sorted(ready_managed - content_keys)
        extra = sorted(content_keys - ready_managed)
        raise ValueError(f"content artifact inventory mismatch: missing={missing}; extra={extra}")

    managed_pages: list[dict[str, str]] = []
    preserved_pages: list[dict[str, str]] = []
    for item in destinations:
        row = {
            "page_key": item.destination_id,
            "service_id": item.service_id,
            "page_role": item.page_role,
            "parent_page_key": item.parent_destination_id,
            "canonical": item.canonical_url,
            "architecture_status": item.publication_status,
        }
        if item.page_role in {"hub", "child_service", "article"}:
            row["content_status"] = (
                "validated" if item.destination_id in content_keys else "content_pending"
            )
            managed_pages.append(row)
        else:
            preserved_pages.append(row)
    return {
        "schema_version": 1,
        "release_id": _RELEASE_ID,
        "release_status": "draft",
        "managed_pages": managed_pages,
        "preserved_pages": preserved_pages,
    }


def write_release_manifest(
    output_path: Path = DEFAULT_RELEASE_MANIFEST_PATH,
) -> int:
    """Write the deterministic release manifest used by local sync and import."""

    manifest = build_release_manifest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(manifest["managed_pages"]) + len(manifest["preserved_pages"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the complete content destination ledger."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_PAGE_ARCHITECTURE_PATH)
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=DEFAULT_RELEASE_MANIFEST_PATH,
    )
    args = parser.parse_args(argv)
    count = write_complete_page_architecture(args.output)
    write_release_manifest(args.manifest_output)
    print(f"Exported {count} complete page destinations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
