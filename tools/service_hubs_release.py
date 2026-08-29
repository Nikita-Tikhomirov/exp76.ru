"""Build the single transactional release for child services and ready articles."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.legacy_article_content import (
    DEFAULT_ARTICLE_DIR,
    load_and_validate_articles,
    validate_article,
)
from tools.seo_semantics.legacy_article_architecture import build_legacy_article_rows
from tools.service_page_content import (
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_PAGES_DIR,
    build_deployment_bundle,
    build_import_items,
    item_checksum,
    load_default_architecture,
    load_evidence,
    load_pages,
)


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "service-hubs-2026-08-28"
SOURCE_RELEASE_MANIFEST = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
SOURCE_PAYLOAD = ROOT / "seo-content" / "service-pages" / "import" / "service-pages-import.json"
SOURCE_DEPLOYMENT_MANIFEST = (
    ROOT / "seo-content" / "service-pages" / "import" / "service-pages-release-manifest.json"
)
THEME_IMPORT_DIR = (
    ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp" / "import"
)
THEME_PAYLOAD = THEME_IMPORT_DIR / "service-hubs-import.json"
THEME_DEPLOYMENT_MANIFEST = THEME_IMPORT_DIR / "service-hubs-release-manifest.json"


def _expected_article_rows() -> list[dict[str, str]]:
    rows = build_legacy_article_rows()
    if len(rows) != 11 or any(row["publication_status"] != "ready" for row in rows):
        raise ValueError("ready article architecture must contain exactly 11 destinations")
    return rows


def _article_relations(article: Mapping[str, Any]) -> list[str]:
    page_key = str(article["destination_id"])
    service_id = str(article["service_id"])
    relations = [
        str(link["page_key"])
        for link in article["internal_links"]
        if isinstance(link, dict) and isinstance(link.get("page_key"), str)
    ]
    hub_keys = [key for key in relations if key == f"{service_id}-HUB"]
    child_keys = [key for key in relations if key.startswith(f"{service_id}-CHILD-")]
    if len(hub_keys) != 1 or len(child_keys) != 1 or len(relations) != 2:
        raise ValueError(
            f"{page_key}: article must relate to exactly one owning hub and one child service"
        )
    if len(relations) != len(set(relations)):
        raise ValueError(f"{page_key}: duplicate article relation")
    return relations


def build_article_import_item(article: Mapping[str, Any]) -> dict[str, object]:
    """Convert one reviewed article source to the unified importer contract."""

    if not isinstance(article, dict):
        raise ValueError("article source must be an object")
    architecture = {row["destination_id"]: row for row in _expected_article_rows()}
    page_key = str(article.get("destination_id", ""))
    if page_key not in architecture:
        raise ValueError(f"unknown or non-ready article destination {page_key!r}")
    validate_article(article, expected=architecture[page_key])
    acf = article["acf"]
    importer_acf = copy.deepcopy(acf)
    # Typed page-key relations replace the obsolete unregistered slug field.
    importer_acf.pop("blogseo_related_service_slugs", None)
    item: dict[str, object] = {
        "page_key": page_key,
        "service_id": article["service_id"],
        "topic_key": article["service_id"],
        "role": "article",
        "slug": article["slug"],
        "canonical": article["canonical"],
        "post_title": article["post_title"],
        "post_content": article["post_content"],
        "post_excerpt": article["post_excerpt"],
        "seo": {
            "title": acf["blogseo_seo_title"],
            "description": acf["blogseo_seo_description"],
        },
        "main_image": {
            "url": article["featured_image_url"],
            "alt": acf["blogseo_main_image_alt"],
        },
        "related_service_page_keys": _article_relations(article),
        "acf": importer_acf,
    }
    item["checksum"] = item_checksum(item)
    return item


def _validate_child_inventory(child_items: Sequence[Mapping[str, object]]) -> None:
    expected_keys = set(load_default_architecture())
    actual_keys = [str(item.get("page_key", "")) for item in child_items]
    if len(child_items) != 65 or set(actual_keys) != expected_keys or len(actual_keys) != len(set(actual_keys)):
        raise ValueError("child service inventory must contain the exact 65 ready destinations")
    for item in child_items:
        if item.get("role") != "child_service":
            raise ValueError(f"{item.get('page_key', '')}: child inventory contains another role")
        if item.get("checksum") != item_checksum(item):
            raise ValueError(f"{item.get('page_key', '')}: invalid child checksum")


def build_unified_import_items(
    child_items: Sequence[Mapping[str, object]],
    articles: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    """Merge the exact 65+11 inventory and add deterministic article backlinks."""

    _validate_child_inventory(child_items)
    expected_rows = _expected_article_rows()
    expected_article_keys = [row["destination_id"] for row in expected_rows]
    articles_by_key: dict[str, Mapping[str, Any]] = {}
    for article in articles:
        page_key = str(article.get("destination_id", ""))
        if page_key in articles_by_key:
            raise ValueError(f"duplicate article destination {page_key}")
        articles_by_key[page_key] = article
    if set(articles_by_key) != set(expected_article_keys) or len(articles_by_key) != 11:
        missing = sorted(set(expected_article_keys) - set(articles_by_key))
        extra = sorted(set(articles_by_key) - set(expected_article_keys))
        raise ValueError(f"article inventory mismatch: missing={missing}; extra={extra}")

    normalized_children = [copy.deepcopy(dict(item)) for item in child_items]
    child_by_key = {str(item["page_key"]): item for item in normalized_children}
    article_items = [
        build_article_import_item(articles_by_key[page_key])
        for page_key in expected_article_keys
    ]
    article_order = {page_key: index for index, page_key in enumerate(expected_article_keys)}

    for child in normalized_children:
        existing = child.get("related_article_page_keys", [])
        if not isinstance(existing, list) or not all(isinstance(key, str) for key in existing):
            raise ValueError(f"{child['page_key']}: invalid related article list")
        unknown = set(existing) - set(expected_article_keys)
        if unknown:
            raise ValueError(f"{child['page_key']}: non-ready article backlink {sorted(unknown)}")

    for article in article_items:
        child_keys = [
            key for key in article["related_service_page_keys"] if "-CHILD-" in key
        ]
        child_key = child_keys[0]
        child = child_by_key.get(child_key)
        if child is None or child["service_id"] != article["service_id"]:
            raise ValueError(f"{article['page_key']}: unresolved owning child {child_key}")
        backlinks = list(child.get("related_article_page_keys", []))
        if article["page_key"] not in backlinks:
            backlinks.append(str(article["page_key"]))
        child["related_article_page_keys"] = sorted(
            backlinks,
            key=lambda page_key: article_order[page_key],
        )

    for child in normalized_children:
        if child.get("related_article_page_keys") == []:
            child.pop("related_article_page_keys", None)
        child["checksum"] = item_checksum(child)

    return normalized_children + article_items


def build_default_unified_import_items() -> list[dict[str, object]]:
    """Build the release inventory from checked source pages and article JSON."""

    architecture = load_default_architecture()
    children = build_import_items(
        load_pages(DEFAULT_PAGES_DIR),
        architecture,
        load_evidence(DEFAULT_EVIDENCE_PATH),
    )
    articles = load_and_validate_articles(DEFAULT_ARTICLE_DIR, require_complete=True)
    return build_unified_import_items(children, articles)


def _validate_source_release_manifest(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("source release manifest is not valid UTF-8 JSON") from error
    if not isinstance(manifest, dict):
        raise ValueError("source release manifest must be an object")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("release_id") != RELEASE_ID
        or manifest.get("release_status") != "ready"
    ):
        raise ValueError("source release manifest is not the ready release")
    managed_pages = manifest.get("managed_pages")
    if not isinstance(managed_pages, list):
        raise ValueError("source release manifest managed_pages must be a list")

    expected: dict[str, dict[str, str]] = {
        f"S{number}-HUB": {
            "service_id": f"S{number}",
            "page_role": "hub",
            "parent_page_key": "",
        }
        for number in range(1, 16)
    }
    for page_key, row in load_default_architecture().items():
        expected[page_key] = {
            "service_id": row["service_id"],
            "page_role": "child_service",
            "parent_page_key": row["parent_hub"],
            "canonical": row["target_url"],
        }
    for row in _expected_article_rows():
        expected[row["destination_id"]] = {
            "service_id": row["service_id"],
            "page_role": "article",
            "parent_page_key": row["parent_destination_id"],
            "canonical": row["canonical_url"],
        }

    actual: dict[str, Mapping[str, Any]] = {}
    for record in managed_pages:
        if not isinstance(record, dict) or not isinstance(record.get("page_key"), str):
            raise ValueError("source release manifest contains an invalid managed page")
        page_key = record["page_key"]
        if page_key in actual:
            raise ValueError(f"source release manifest duplicates {page_key}")
        actual[page_key] = record
    if len(actual) != 91 or set(actual) != set(expected):
        raise ValueError("source release manifest must contain exact 15+65+11 inventory")
    for page_key, expected_record in expected.items():
        record = actual[page_key]
        if any(record.get(key) != value for key, value in expected_record.items()):
            raise ValueError(f"source release manifest record differs: {page_key}")
        if (
            record.get("architecture_status") != "ready"
            or record.get("content_status") != "validated"
        ):
            raise ValueError(f"source release manifest record is not ready: {page_key}")
        canonical = record.get("canonical")
        if not isinstance(canonical, str) or not canonical.startswith("https://exp76.ru/"):
            raise ValueError(f"source release manifest canonical is invalid: {page_key}")
    return raw


def build_default_deployment_bundle(
    source_manifest_path: Path = SOURCE_RELEASE_MANIFEST,
) -> tuple[dict[str, object], dict[str, object]]:
    """Bind the unified inventory to the exact source release manifest bytes."""

    source_hash = hashlib.sha256(_validate_source_release_manifest(source_manifest_path)).hexdigest()
    return build_deployment_bundle(
        build_default_unified_import_items(),
        release_id=RELEASE_ID,
        source_manifest_sha256=source_hash,
    )


def _json_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_default_deployment_bundle() -> int:
    """Write byte-identical source and theme copies of the 76-item release."""

    manifest, payload = build_default_deployment_bundle()
    outputs = (
        (SOURCE_DEPLOYMENT_MANIFEST, _json_bytes(manifest)),
        (THEME_DEPLOYMENT_MANIFEST, _json_bytes(manifest)),
        (SOURCE_PAYLOAD, _json_bytes(payload)),
        (THEME_PAYLOAD, _json_bytes(payload)),
    )
    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return len(payload["items"])


def check_default_deployment_bundle() -> list[str]:
    """Return drifted checked artifacts without modifying the workspace."""

    manifest, payload = build_default_deployment_bundle()
    expected = {
        SOURCE_DEPLOYMENT_MANIFEST: _json_bytes(manifest),
        THEME_DEPLOYMENT_MANIFEST: _json_bytes(manifest),
        SOURCE_PAYLOAD: _json_bytes(payload),
        THEME_PAYLOAD: _json_bytes(payload),
    }
    return [str(path) for path, content in expected.items() if not path.is_file() or path.read_bytes() != content]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the unified 65+11 service release")
    parser.add_argument("command", choices=("render", "check"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "render":
        count = write_default_deployment_bundle()
        print(f"Rendered {count} unified import items.")
        return 0
    drifted = check_default_deployment_bundle()
    if drifted:
        print("Release artifacts differ:")
        for path in drifted:
            print(f"- {path}")
        return 1
    print("Unified release artifacts are current (76 items).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
