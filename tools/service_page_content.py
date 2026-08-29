"""Validate and render production child-service content for the WP importer.

The source JSON is deliberately richer than the importer item.  Deployment
identity is validated here, while the PHP importer owns create/reuse mechanics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence

if __package__:
    from tools.seo_semantics.complete_service_architecture import (
        build_complete_service_rows,
    )
else:  # Direct execution: ``python tools/service_page_content.py``.
    from seo_semantics.complete_service_architecture import (  # type: ignore[no-redef]
        build_complete_service_rows,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGES_DIR = ROOT / "seo-content" / "service-pages" / "pages"
DEFAULT_ARCHITECTURE_PATH = (
    ROOT
    / "seo-data"
    / "2026-08-exp76-services"
    / "processed"
    / "complete_service_children.csv"
)
DEFAULT_EVIDENCE_PATH = ROOT / "seo-content" / "service-pages" / "evidence.json"

PAGE_FIELDS = {
    "schema_version",
    "destination_id",
    "service_id",
    "deployment",
    "slug",
    "canonical",
    "post_title",
    "seo",
    "h1",
    "lead",
    "scope",
    "audience",
    "process",
    "pricing",
    "proof",
    "geo",
    "faq",
    "links",
    "cta",
    "boundary",
}
DEPLOYMENT_FIELDS = {
    "action",
    "current_wp_id",
    "current_post_type",
    "current_url",
    "target_template",
    "preserve_id",
    "preserve_permalink",
}
PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:todo|tbd|lorem|ipsum|n/a)\b", re.IGNORECASE),
    re.compile(r"\b(?:заглушк\w*|текст\s+будет|пример\s+текста)\b", re.IGNORECASE),
    re.compile(r"\b(?:подставить|вставить)\s+(?:сюда|позже|позднее)\b", re.IGNORECASE),
    re.compile(r"уточнить\s+у\s+клиента", re.IGNORECASE),
    re.compile(r"\?{3,}|\[\s*(?:вставить|заполнить)", re.IGNORECASE),
)
ABSOLUTE_CLAIM_PATTERNS = (
    re.compile(r"\bгарантиру(?:ем|ется|ют)\b|\bгарантированн\w*\b", re.IGNORECASE),
    re.compile(r"\b(?:лучший|лучшая|лучшие|самый|самая|самые)\b", re.IGNORECASE),
    re.compile(r"\b(?:идеальн\w*|безупречн\w*|навсегда)\b", re.IGNORECASE),
    re.compile(r"\b(?:всегда|никогда)\b", re.IGNORECASE),
    re.compile(r"\b(?:любой|любая|любые|любого)\s+(?:участок|объект|случай|условия)", re.IGNORECASE),
    re.compile(r"(?:100\s*%|№\s*1|номер\s+один)", re.IGNORECASE),
)
FICTIONAL_PRICE_PATTERNS = (
    re.compile(r"\b\d[\d\s.,]*(?:₽|руб(?:\.|ля|лей)?|р\.)", re.IGNORECASE),
    re.compile(r"\b(?:от|до|цена|стоимость)\s+\d[\d\s.,]*\b", re.IGNORECASE),
)
UNSUPPORTED_NUMERIC_PATTERNS = (
    re.compile(r"\b\d[\d\s.,]*\s*%\b", re.IGNORECASE),
    re.compile(
        r"\b(?:за|срок\s*[-—:]?|в\s+течение)\s*\d+\s*"
        r"(?:час\w*|дн\w*|недел\w*|месяц\w*|лет|год\w*)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bгаранти\w*\s+(?:на\s+)?\d+\s*(?:месяц\w*|лет|год\w*)\b", re.IGNORECASE),
)
NON_CASE_CLAIM_PATTERNS = (
    re.compile(
        r"\bнаш(?:его|ем|и|а)?\s+(?:выполненн\w+\s+)?объект\w*\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bвыполненн\w+\s+работ\w*\s+компани\w*\b", re.IGNORECASE),
    re.compile(r"\bреализованн\w+\s+(?:объект\w*|работ\w*)\b", re.IGNORECASE),
    re.compile(r"\bподтвержд[её]нн\w+\s+кейс\w*\b", re.IGNORECASE),
    re.compile(r"\bпример\s+наш(?:их|ей)\s+работ\w*\b", re.IGNORECASE),
    re.compile(r"\bдо\s+и\s+после\b|\bадрес\s+объект\w*\b", re.IGNORECASE),
)


def load_architecture(path: Path) -> dict[str, dict[str, str]]:
    """Load an explicitly selected approved architecture registry."""

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        destination_id = str(row.get("destination_id", "")).strip()
        if not destination_id:
            raise ValueError("architecture row has no destination_id")
        if destination_id in indexed:
            raise ValueError(f"duplicate architecture destination_id: {destination_id}")
        indexed[destination_id] = {key: str(value or "") for key, value in row.items()}
    return indexed


def load_default_architecture() -> dict[str, dict[str, str]]:
    """Load the release CSV and fail if it drifted from its executable source."""

    actual = load_architecture(DEFAULT_ARCHITECTURE_PATH)
    expected_rows = build_complete_service_rows()
    expected: dict[str, dict[str, str]] = {}
    for row in expected_rows:
        destination_id = str(row.get("destination_id", "")).strip()
        expected[destination_id] = {
            key: str(value or "") for key, value in row.items()
        }
    if list(actual) != list(expected) or actual != expected:
        actual_ids = set(actual)
        expected_ids = set(expected)
        changed = sorted(
            destination_id
            for destination_id in actual_ids & expected_ids
            if actual[destination_id] != expected[destination_id]
        )
        raise ValueError(
            "default architecture CSV drifted from "
            "tools.seo_semantics.complete_service_architecture: "
            f"missing={sorted(expected_ids - actual_ids)}; "
            f"extra={sorted(actual_ids - expected_ids)}; changed={changed}"
        )
    return actual


def load_evidence(path: Path) -> dict[str, dict[str, object]]:
    """Load the evidence registry keyed by the frozen destination id."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("evidence registry must use schema_version 1")
    services = payload.get("services")
    if not isinstance(services, list):
        raise ValueError("evidence registry services must be a list")
    indexed: dict[str, dict[str, object]] = {}
    for entry in services:
        if not isinstance(entry, dict):
            raise ValueError("evidence registry entry must be an object")
        destination_id = entry.get("destination_id")
        if not isinstance(destination_id, str) or not destination_id:
            raise ValueError("evidence registry entry has no destination_id")
        if destination_id in indexed:
            raise ValueError(f"duplicate evidence destination_id: {destination_id}")
        indexed[destination_id] = entry
    return indexed


def _object(value: object, path: str, errors: list[str]) -> Mapping[str, object]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _list(value: object, path: str, errors: list[str]) -> list[object]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def _text(
    value: object,
    path: str,
    errors: list[str],
    *,
    minimum: int = 1,
) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        errors.append(f"{path} must contain at least {minimum} characters")
        return ""
    return value.strip()


def _expected_optional(row: Mapping[str, object], key: str) -> object:
    value = str(row.get(key, "")).strip()
    if key == "current_wp_id":
        return int(value) if value.isdigit() else None
    return value or None


def _validate_deployment(
    value: object,
    row: Mapping[str, object],
    errors: list[str],
) -> None:
    deployment = _object(value, "deployment", errors)
    if not deployment:
        return
    missing = DEPLOYMENT_FIELDS - set(deployment)
    unknown = set(deployment) - DEPLOYMENT_FIELDS
    for field in sorted(missing):
        errors.append(f"deployment.{field} is required")
    for field in sorted(unknown):
        errors.append(f"deployment.{field} is not allowed")

    action = str(row.get("url_action", ""))
    expected = {
        "action": action,
        "current_wp_id": _expected_optional(row, "current_wp_id"),
        "current_post_type": _expected_optional(row, "current_post_type"),
        "current_url": _expected_optional(row, "current_url"),
        "target_template": _expected_optional(row, "target_template"),
        "preserve_id": action == "reuse",
        "preserve_permalink": action == "reuse",
    }
    for field, expected_value in expected.items():
        if deployment.get(field) != expected_value:
            errors.append(
                f"deployment.{field} must equal frozen architecture value "
                f"{expected_value!r}"
            )


def _validate_exact_keys(
    value: Mapping[str, object],
    required: set[str],
    path: str,
    errors: list[str],
) -> None:
    for field in sorted(required - set(value)):
        errors.append(f"{path}.{field} is required")
    for field in sorted(set(value) - required):
        errors.append(f"{path}.{field} is not allowed")


def _validate_titled_items(
    value: object,
    path: str,
    errors: list[str],
    *,
    minimum_count: int,
) -> list[Mapping[str, object]]:
    items = _list(value, path, errors)
    if len(items) < minimum_count:
        errors.append(f"{path} must contain at least {minimum_count} items")
    valid: list[Mapping[str, object]] = []
    for index, item in enumerate(items):
        current = _object(item, f"{path}[{index}]", errors)
        if not current:
            continue
        _validate_exact_keys(current, {"title", "text"}, f"{path}[{index}]", errors)
        _text(current.get("title"), f"{path}[{index}].title", errors, minimum=3)
        _text(current.get("text"), f"{path}[{index}].text", errors, minimum=20)
        valid.append(current)
    return valid


def _walk_text(value: object, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_text(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_text(child, f"{path}[{index}]")


def _validate_copy_quality(page: Mapping[str, object], errors: list[str]) -> None:
    for path, text in _walk_text(page):
        if path.endswith((".url", ".canonical", ".slug", ".page_key")) or path in {
            "$.canonical",
            "$.slug",
            "$.destination_id",
            "$.service_id",
        }:
            continue
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path} contains placeholder copy")
                break
        # Boundary text is a frozen exclusion contract. It may name a forbidden
        # promise (for example, a guaranteed result) precisely to rule it out.
        if path.startswith("$.boundary."):
            continue
        for pattern in ABSOLUTE_CLAIM_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path} contains unsupported absolute claim")
                break
        for pattern in FICTIONAL_PRICE_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path} contains fictional price")
                break
        for pattern in UNSUPPORTED_NUMERIC_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path} contains unsupported numeric claim")
                break


def _is_internal_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if re.fullmatch(r"#[A-Za-z][A-Za-z0-9_-]*", value):
        return True
    return bool(re.fullmatch(r"https://exp76\.ru/(?:[^?#]*/)?", value))


def _validate_link(value: object, path: str, errors: list[str]) -> Mapping[str, object]:
    link = _object(value, path, errors)
    if not link:
        return {}
    _validate_exact_keys(link, {"page_key", "url", "label"}, path, errors)
    _text(link.get("page_key"), f"{path}.page_key", errors, minimum=4)
    _text(link.get("label"), f"{path}.label", errors, minimum=5)
    if not _is_internal_url(link.get("url")) or str(link.get("url", "")).startswith("#"):
        errors.append(f"{path}.url must be an absolute exp76.ru URL")
    return link


def _validate_content_blocks(page: Mapping[str, object], errors: list[str]) -> None:
    scope = _object(page.get("scope"), "scope", errors)
    if scope:
        _validate_exact_keys(scope, {"heading", "text", "results"}, "scope", errors)
        _text(scope.get("heading"), "scope.heading", errors, minimum=12)
        _text(scope.get("text"), "scope.text", errors, minimum=40)
        _validate_titled_items(
            scope.get("results"), "scope.results", errors, minimum_count=2
        )

    audience = _object(page.get("audience"), "audience", errors)
    if audience:
        _validate_exact_keys(audience, {"heading", "text", "items"}, "audience", errors)
        _text(audience.get("heading"), "audience.heading", errors, minimum=12)
        _text(audience.get("text"), "audience.text", errors, minimum=40)
        _validate_titled_items(
            audience.get("items"), "audience.items", errors, minimum_count=3
        )

    process = _object(page.get("process"), "process", errors)
    if process:
        _validate_exact_keys(process, {"heading", "steps"}, "process", errors)
        _text(process.get("heading"), "process.heading", errors, minimum=10)
        _validate_titled_items(
            process.get("steps"), "process.steps", errors, minimum_count=5
        )

    pricing = _object(page.get("pricing"), "pricing", errors)
    if pricing:
        _validate_exact_keys(pricing, {"heading", "text", "factors"}, "pricing", errors)
        _text(pricing.get("heading"), "pricing.heading", errors, minimum=10)
        _text(pricing.get("text"), "pricing.text", errors, minimum=40)
        _validate_titled_items(
            pricing.get("factors"), "pricing.factors", errors, minimum_count=3
        )

    geo = _object(page.get("geo"), "geo", errors)
    if geo:
        _validate_exact_keys(geo, {"heading", "text", "areas"}, "geo", errors)
        _text(geo.get("heading"), "geo.heading", errors, minimum=10)
        _text(geo.get("text"), "geo.text", errors, minimum=50)
        areas = _list(geo.get("areas"), "geo.areas", errors)
        if len(areas) < 2:
            errors.append("geo.areas must contain at least 2 service areas")
        for index, area in enumerate(areas):
            _text(area, f"geo.areas[{index}]", errors, minimum=3)

    faq = _object(page.get("faq"), "faq", errors)
    if faq:
        _validate_exact_keys(faq, {"heading", "items"}, "faq", errors)
        _text(faq.get("heading"), "faq.heading", errors, minimum=10)
        items = _list(faq.get("items"), "faq.items", errors)
        if len(items) < 5:
            errors.append("faq.items must contain at least 5 items")
        seen_questions: set[str] = set()
        for index, item in enumerate(items):
            current = _object(item, f"faq.items[{index}]", errors)
            if not current:
                continue
            _validate_exact_keys(
                current, {"question", "answer"}, f"faq.items[{index}]", errors
            )
            _text(
                current.get("question"),
                f"faq.items[{index}].question",
                errors,
                minimum=12,
            )
            _text(
                current.get("answer"),
                f"faq.items[{index}].answer",
                errors,
                minimum=30,
            )
            question = current.get("question")
            normalized_question = (
                re.sub(r"\s+", " ", question).strip().casefold()
                if isinstance(question, str)
                else ""
            )
            if normalized_question in seen_questions:
                errors.append("faq.items contains duplicate questions")
            elif normalized_question:
                seen_questions.add(normalized_question)

    cta = _object(page.get("cta"), "cta", errors)
    if cta:
        fields = {
            "heading",
            "text",
            "primary_label",
            "primary_url",
            "secondary_label",
            "secondary_url",
        }
        _validate_exact_keys(cta, fields, "cta", errors)
        _text(cta.get("heading"), "cta.heading", errors, minimum=10)
        _text(cta.get("text"), "cta.text", errors, minimum=40)
        _text(cta.get("primary_label"), "cta.primary_label", errors, minimum=5)
        _text(cta.get("secondary_label"), "cta.secondary_label", errors, minimum=5)
        for field in ("primary_url", "secondary_url"):
            if not _is_internal_url(cta.get(field)):
                errors.append(f"cta.{field} must be an internal URL or fragment")


def _selected_media(
    proof: Mapping[str, object],
    evidence: Mapping[str, object],
    errors: list[str],
) -> Mapping[str, object] | None:
    attachment_id = proof.get("main_image_attachment_id")
    if not isinstance(attachment_id, int) or attachment_id <= 0:
        errors.append("proof.main_image_attachment_id must be a positive integer")
        return None
    media = evidence.get("media")
    if not isinstance(media, list):
        errors.append("evidence.media must be a list")
        return None
    matches = [
        item
        for item in media
        if isinstance(item, dict) and item.get("attachment_id") == attachment_id
    ]
    if len(matches) != 1:
        errors.append(
            "proof.main_image_attachment_id must select exactly one confirmed evidence media"
        )
        return None
    selected = matches[0]
    if selected.get("asset_kind") not in {
        "case_photo",
        "service_photo",
        "context_photo",
        "illustration",
    }:
        errors.append("proof main image has an unsupported evidence asset_kind")
    source_page_id = selected.get("source_page_id")
    exact_sources = evidence.get("exact_case_ids")
    contextual_sources = evidence.get("contextual_page_ids")
    exact_source_ids = set(exact_sources if isinstance(exact_sources, list) else [])
    allowed_source_ids = set(exact_source_ids)
    allowed_source_ids.update(
        contextual_sources if isinstance(contextual_sources, list) else []
    )
    if not isinstance(source_page_id, int) or source_page_id not in allowed_source_ids:
        errors.append("proof main image source_page_id is not confirmed")
    if selected.get("asset_kind") == "case_photo" and source_page_id not in exact_source_ids:
        errors.append("proof case photo source_page_id is not an exact case")
    url = selected.get("url")
    if not isinstance(url, str) or not re.fullmatch(
        r"https://exp76\.ru/wp-content/uploads/.+", url
    ):
        errors.append("proof main image must use confirmed exp76.ru WP media")
    return selected


def validate_page(
    page: Mapping[str, object],
    row: Mapping[str, object],
    evidence: Mapping[str, object],
) -> list[str]:
    """Return fail-closed page errors without mutating the supplied objects."""

    errors: list[str] = []
    missing = PAGE_FIELDS - set(page)
    unknown = set(page) - PAGE_FIELDS
    for field in sorted(missing):
        errors.append(f"{field} is required")
    for field in sorted(unknown):
        errors.append(f"{field} is not allowed")
    if page.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if row.get("publication_status") != "ready":
        errors.append("architecture publication_status must be ready")

    identity_fields = {
        "destination_id": "destination_id",
        "service_id": "service_id",
        "slug": "slug",
        "canonical": "target_url",
        "post_title": "title",
    }
    for page_field, row_field in identity_fields.items():
        expected = str(row.get(row_field, ""))
        if page.get(page_field) != expected:
            errors.append(f"{page_field} must equal frozen architecture value {expected!r}")
    _validate_deployment(page.get("deployment"), row, errors)

    seo = _object(page.get("seo"), "seo", errors)
    if seo:
        _validate_exact_keys(seo, {"title", "description"}, "seo", errors)
    _text(seo.get("title"), "seo.title", errors, minimum=20)
    _text(seo.get("description"), "seo.description", errors, minimum=60)
    _text(page.get("h1"), "h1", errors, minimum=12)
    _text(page.get("lead"), "lead", errors, minimum=60)
    _validate_content_blocks(page, errors)

    proof = _object(page.get("proof"), "proof", errors)
    if proof:
        _validate_exact_keys(
            proof,
            {
                "evidence_ref",
                "case_ids",
                "main_image_attachment_id",
                "main_image_alt",
                "caption",
            },
            "proof",
            errors,
        )
        if proof.get("evidence_ref") != page.get("destination_id"):
            errors.append("proof.evidence_ref must equal destination_id")
        if evidence.get("destination_id") != page.get("destination_id"):
            errors.append("evidence destination_id does not match page")
        case_ids = _list(proof.get("case_ids"), "proof.case_ids", errors)
        exact_case_ids = evidence.get("exact_case_ids")
        confirmed_cases = set(exact_case_ids if isinstance(exact_case_ids, list) else [])
        for case_id in case_ids:
            if not isinstance(case_id, int) or case_id not in confirmed_cases:
                errors.append(f"proof.case_ids contains unconfirmed case {case_id!r}")
        if len(case_ids) != len(set(case_ids)):
            errors.append("proof.case_ids contains duplicates")
        if confirmed_cases and not case_ids:
            errors.append("proof.case_ids must use an available exact case")
        _text(proof.get("main_image_alt"), "proof.main_image_alt", errors, minimum=12)
        caption = _text(proof.get("caption"), "proof.caption", errors, minimum=20)
        selected = _selected_media(proof, evidence, errors)
        if selected is not None and selected.get("asset_kind") != "case_photo":
            if selected.get("asset_kind") == "illustration" and not caption.startswith(
                "Иллюстрация:"
            ):
                errors.append("proof.caption for illustration must start with 'Иллюстрация:'")
            searchable = " ".join(
                (
                    caption.casefold(),
                    str(proof.get("main_image_alt", "")).casefold(),
                )
            )
            if any(pattern.search(searchable) for pattern in NON_CASE_CLAIM_PATTERNS):
                errors.append("proof non-case media is described as a completed case")

    boundary = _object(page.get("boundary"), "boundary", errors)
    if boundary:
        _validate_exact_keys(
            boundary, {"summary", "excluded_intents"}, "boundary", errors
        )
        expected_boundary = str(row.get("boundary", ""))
        if boundary.get("summary") != expected_boundary:
            errors.append("boundary.summary must equal frozen architecture boundary")
        excluded = _list(
            boundary.get("excluded_intents"), "boundary.excluded_intents", errors
        )
        if not excluded:
            errors.append("boundary.excluded_intents must not be empty")
        explicit_excluded = {
            item.strip()
            for item in str(row.get("excluded_primary_intents", "")).split("|")
            if item.strip()
        }
        supplied_excluded = {
            item.strip() for item in excluded if isinstance(item, str) and item.strip()
        }
        if not explicit_excluded.issubset(supplied_excluded):
            errors.append("boundary.excluded_intents loses frozen excluded intents")

    links = _object(page.get("links"), "links", errors)
    if links:
        _validate_exact_keys(
            links, {"parent", "related_services"}, "links", errors
        )
        parent = _validate_link(links.get("parent"), "links.parent", errors)
        if parent.get("page_key") != row.get("parent_hub"):
            errors.append("links.parent.page_key must equal frozen parent hub")
        if parent.get("url") != row.get("parent_hub_url"):
            errors.append("links.parent.url must equal frozen parent hub URL")
        _text(parent.get("label"), "links.parent.label", errors, minimum=5)
        related = _list(
            links.get("related_services"), "links.related_services", errors
        )
        if not related:
            errors.append("links.related_services must not be empty")
        seen_page_keys: set[str] = set()
        for index, value in enumerate(related):
            current = _validate_link(
                value, f"links.related_services[{index}]", errors
            )
            page_key = current.get("page_key")
            if page_key == page.get("destination_id"):
                errors.append("links.related_services cannot link to the current page")
            if isinstance(page_key, str):
                if page_key in seen_page_keys:
                    errors.append("links.related_services contains duplicate page_key")
                seen_page_keys.add(page_key)

    _validate_copy_quality(page, errors)

    return errors


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _safe_href(value: object) -> str:
    return _escape(value) if _is_internal_url(value) else "#"


def _cards(items: Sequence[Mapping[str, object]], css_class: str) -> str:
    rendered = []
    for item in items:
        rendered.append(
            f'<li class="{css_class}"><strong>{_escape(item["title"])}</strong>'
            f'<p>{_escape(item["text"])}</p></li>'
        )
    return "<ul>" + "".join(rendered) + "</ul>"


def _section(heading: object, body: str, css_suffix: str) -> str:
    return (
        f'<section class="service-content service-content--{css_suffix}">'
        f"<h2>{_escape(heading)}</h2>{body}</section>"
    )


def _render_scope(page: Mapping[str, object]) -> str:
    scope = page["scope"]
    assert isinstance(scope, dict)
    results = scope["results"]
    assert isinstance(results, list)
    return _section(
        scope["heading"],
        f"<p>{_escape(scope['text'])}</p>"
        + _cards([item for item in results if isinstance(item, dict)], "service-result"),
        "scope",
    )


def _render_audience(page: Mapping[str, object]) -> str:
    audience = page["audience"]
    assert isinstance(audience, dict)
    items = audience["items"]
    assert isinstance(items, list)
    return _section(
        audience["heading"],
        f"<p>{_escape(audience['text'])}</p>"
        + _cards([item for item in items if isinstance(item, dict)], "service-audience"),
        "audience",
    )


def _render_process(page: Mapping[str, object]) -> str:
    process = page["process"]
    assert isinstance(process, dict)
    steps = process["steps"]
    assert isinstance(steps, list)
    rows = []
    for index, step in enumerate(steps, start=1):
        assert isinstance(step, dict)
        rows.append(
            f'<li><strong>{index}. {_escape(step["title"])}</strong>'
            f'<p>{_escape(step["text"])}</p></li>'
        )
    return _section(process["heading"], "<ol>" + "".join(rows) + "</ol>", "process")


def _render_pricing(page: Mapping[str, object]) -> str:
    pricing = page["pricing"]
    assert isinstance(pricing, dict)
    factors = pricing["factors"]
    assert isinstance(factors, list)
    return _section(
        pricing["heading"],
        f"<p>{_escape(pricing['text'])}</p>"
        + _cards([item for item in factors if isinstance(item, dict)], "price-factor"),
        "pricing",
    )


def _render_geo(page: Mapping[str, object]) -> str:
    geo = page["geo"]
    assert isinstance(geo, dict)
    areas = geo["areas"]
    assert isinstance(areas, list)
    areas_html = "<ul>" + "".join(f"<li>{_escape(area)}</li>" for area in areas) + "</ul>"
    return _section(
        geo["heading"], f"<p>{_escape(geo['text'])}</p>{areas_html}", "geo"
    )


def _render_faq(page: Mapping[str, object]) -> str:
    faq = page["faq"]
    assert isinstance(faq, dict)
    items = faq["items"]
    assert isinstance(items, list)
    rows = []
    for item in items:
        assert isinstance(item, dict)
        rows.append(
            f'<details><summary>{_escape(item["question"])}</summary>'
            f'<p>{_escape(item["answer"])}</p></details>'
        )
    return _section(faq["heading"], "".join(rows), "faq")


def _render_links(page: Mapping[str, object]) -> str:
    links = page["links"]
    assert isinstance(links, dict)
    parent = links["parent"]
    related = links["related_services"]
    assert isinstance(parent, dict) and isinstance(related, list)
    rows = [parent, *[item for item in related if isinstance(item, dict)]]
    body = "<ul>" + "".join(
        f'<li><a href="{_safe_href(item["url"])}">{_escape(item["label"])}</a></li>'
        for item in rows
    ) + "</ul>"
    return _section("Связанные услуги", body, "links")


def _render_boundary(page: Mapping[str, object]) -> str:
    boundary = page["boundary"]
    assert isinstance(boundary, dict)
    excluded = boundary["excluded_intents"]
    assert isinstance(excluded, list)
    body = f"<p>{_escape(boundary['summary'])}</p><h3>Что не относится к услуге</h3>"
    body += "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in excluded) + "</ul>"
    return _section("Границы услуги", body, "boundary")


def _render_cta(page: Mapping[str, object]) -> str:
    cta = page["cta"]
    assert isinstance(cta, dict)
    body = (
        f"<p>{_escape(cta['text'])}</p>"
        f'<p><a class="service-cta__primary" href="{_safe_href(cta["primary_url"])}">'
        f'{_escape(cta["primary_label"])}</a> '
        f'<a class="service-cta__secondary" href="{_safe_href(cta["secondary_url"])}">'
        f'{_escape(cta["secondary_label"])}</a></p>'
    )
    return _section(cta["heading"], body, "cta")


def render_standalone_html(
    page: Mapping[str, object],
    *,
    main_image_url: str | None = None,
) -> str:
    """Render a complete safe body for a legacy page template or preview."""

    proof = page["proof"]
    assert isinstance(proof, dict)
    lead = f'<p class="service-lead">{_escape(page["lead"])}</p>'
    if main_image_url and re.fullmatch(
        r"https://exp76\.ru/wp-content/uploads/[^?#]+", main_image_url
    ):
        media_caption = (
            '<figure class="service-main-image">'
            f'<img src="{_escape(main_image_url)}" alt="{_escape(proof["main_image_alt"])}">'
            f'<figcaption>{_escape(proof["caption"])}</figcaption></figure>'
        )
    else:
        media_caption = (
            f'<p class="service-media-caption">{_escape(proof["caption"])}</p>'
        )
    return "".join(
        (
            f"<h1>{_escape(page['h1'])}</h1>",
            lead,
            media_caption,
            _render_scope(page),
            _render_audience(page),
            _render_process(page),
            _render_pricing(page),
            _render_geo(page),
            _render_boundary(page),
            _render_faq(page),
            _render_links(page),
            _render_cta(page),
        )
    )


def _render_managed_post_content(page: Mapping[str, object]) -> str:
    """Render blocks not already rendered by ``newservicepost.php`` from ACF."""

    proof = page["proof"]
    assert isinstance(proof, dict)
    return "".join(
        (
            f'<p class="service-media-caption">{_escape(proof["caption"])}</p>',
            _render_scope(page),
            _render_geo(page),
            _render_boundary(page),
            _render_cta(page),
        )
    )


def _acf_payload(page: Mapping[str, object], image_url: str) -> dict[str, object]:
    audience = page["audience"]
    process = page["process"]
    pricing = page["pricing"]
    faq = page["faq"]
    cta = page["cta"]
    assert all(isinstance(value, dict) for value in (audience, process, pricing, faq, cta))
    audience = dict(audience)
    process = dict(process)
    pricing = dict(pricing)
    faq = dict(faq)
    cta = dict(cta)
    return {
        "ns87_hero_title": page["h1"],
        "ns87_hero_subtitle": page["lead"],
        "ns87_hero_btn_primary_text": cta["primary_label"],
        "ns87_hero_btn_primary_url": cta["primary_url"],
        "ns87_hero_btn_secondary_text": cta["secondary_label"],
        "ns87_hero_btn_secondary_url": cta["secondary_url"],
        "ns87_problem_title": audience["heading"],
        "ns87_problem_text": audience["text"],
        "ns87_problem_items": [
            {"title": item["title"], "text": item["text"], "image": image_url}
            for item in audience["items"]
            if isinstance(item, dict)
        ],
        "ns87_solution_title": process["heading"],
        "ns87_solution_text": "Последовательность работ: "
        + "; ".join(
            str(item["title"]).strip().lower()
            for item in process["steps"]
            if isinstance(item, dict)
        )
        + ".",
        "ns87_solution_points": [
            {"title": item["title"], "text": item["text"]}
            for item in process["steps"]
            if isinstance(item, dict)
        ],
        "ns87_prices_title": pricing["heading"],
        "ns87_price_rows": [
            {
                "service": item["title"],
                "price": "по расчёту",
                "term": item["text"],
            }
            for item in pricing["factors"]
            if isinstance(item, dict)
        ],
        "ns87_estimate_title": "Что учитываем при расчёте",
        "ns87_estimate_items": [
            {"item": f"{item['title']}: {item['text']}"}
            for item in pricing["factors"]
            if isinstance(item, dict)
        ],
        "ns87_estimate_total": pricing["text"],
        "ns87_faq_title": faq["heading"],
        "ns87_faq_items": [
            {"question": item["question"], "answer": item["answer"]}
            for item in faq["items"]
            if isinstance(item, dict)
        ],
    }


def item_checksum(item: Mapping[str, object]) -> str:
    """Match PHP's recursive key sort and unescaped UTF-8/slashes checksum."""

    canonical = {key: value for key, value in item.items() if key != "checksum"}
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_import_item(
    page: Mapping[str, object],
    row: Mapping[str, object],
    evidence: Mapping[str, object],
) -> dict[str, object]:
    """Build one importer-schema item for either create or frozen reuse."""

    errors = validate_page(page, row, evidence)
    if errors:
        raise ValueError("invalid service page:\n- " + "\n- ".join(errors))
    proof = page["proof"]
    links = page["links"]
    assert isinstance(proof, dict) and isinstance(links, dict)
    selected = _selected_media(proof, evidence, [])
    if selected is None:
        raise ValueError("invalid service page: confirmed main image is unavailable")
    related = links["related_services"]
    parent = links["parent"]
    assert isinstance(related, list) and isinstance(parent, dict)
    relation_keys = [parent["page_key"]] + [
        item["page_key"] for item in related if isinstance(item, dict)
    ]
    item: dict[str, object] = {
        "page_key": page["destination_id"],
        "service_id": page["service_id"],
        "topic_key": page["service_id"],
        "role": "child_service",
        "slug": page["slug"],
        "canonical": page["canonical"],
        "post_title": page["post_title"],
        "post_content": _render_managed_post_content(page),
        "post_excerpt": page["lead"],
        "seo": dict(page["seo"]),
        "main_image": {
            "url": selected["url"],
            "alt": proof["main_image_alt"],
        },
        "case_ids": list(proof["case_ids"]),
        "related_service_page_keys": relation_keys,
        "acf": _acf_payload(page, str(selected["url"])),
    }
    item["checksum"] = item_checksum(item)
    return item


def validate_collection(
    pages: Sequence[Mapping[str, object]],
    architecture: Mapping[str, Mapping[str, object]],
    evidence: Mapping[str, Mapping[str, object]],
) -> list[str]:
    """Validate exact collection coverage and page-level contracts."""

    errors: list[str] = []
    page_ids = [str(page.get("destination_id", "")) for page in pages]
    if len(page_ids) != len(set(page_ids)):
        errors.append("collection contains duplicate destination_id")
    if set(page_ids) != set(architecture):
        missing = sorted(set(architecture) - set(page_ids))
        extra = sorted(set(page_ids) - set(architecture))
        errors.append(f"collection coverage mismatch: missing={missing}; extra={extra}")
    if set(evidence) != set(architecture):
        errors.append("evidence coverage differs from frozen architecture")
    for page in pages:
        destination_id = str(page.get("destination_id", ""))
        row = architecture.get(destination_id)
        entry = evidence.get(destination_id)
        if row is None or entry is None:
            continue
        errors.extend(
            f"{destination_id}: {error}"
            for error in validate_page(page, row, entry)
        )
    unique_fields = {
        "seo.title": lambda page: (
            page.get("seo", {}).get("title", "")
            if isinstance(page.get("seo"), dict)
            else ""
        ),
        "seo.description": lambda page: (
            page.get("seo", {}).get("description", "")
            if isinstance(page.get("seo"), dict)
            else ""
        ),
        "h1": lambda page: page.get("h1", ""),
        "lead": lambda page: page.get("lead", ""),
    }
    for field, extractor in unique_fields.items():
        seen: dict[str, str] = {}
        for page in pages:
            destination_id = str(page.get("destination_id", ""))
            value = extractor(page)
            normalized = re.sub(r"\s+", " ", str(value)).strip().casefold()
            if not normalized:
                continue
            if normalized in seen:
                errors.append(
                    f"duplicate {field}: {seen[normalized]} and {destination_id}"
                )
            else:
                seen[normalized] = destination_id

    for page in pages:
        destination_id = str(page.get("destination_id", ""))
        row = architecture.get(destination_id)
        links = page.get("links")
        if row is None or not isinstance(links, dict):
            continue
        related = links.get("related_services")
        if not isinstance(related, list):
            continue
        for link in related:
            if not isinstance(link, dict):
                continue
            page_key = str(link.get("page_key", ""))
            related_row = architecture.get(page_key)
            if related_row is None:
                errors.append(
                    f"{destination_id}: unresolved related service {page_key!r}"
                )
                continue
            if related_row.get("service_id") != row.get("service_id"):
                errors.append(
                    f"{destination_id}: related service {page_key} belongs to another hub"
                )
            if link.get("url") != related_row.get("target_url"):
                errors.append(
                    f"{destination_id}: related service {page_key} URL differs from architecture"
                )
    return errors


def build_import_items(
    pages: Sequence[Mapping[str, object]],
    architecture: Mapping[str, Mapping[str, object]],
    evidence: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    """Build all items only after exact-coverage validation succeeds."""

    errors = validate_collection(pages, architecture, evidence)
    if errors:
        raise ValueError("invalid service page collection:\n- " + "\n- ".join(errors))
    by_id = {str(page["destination_id"]): page for page in pages}
    return [
        build_import_item(by_id[destination_id], row, evidence[destination_id])
        for destination_id, row in architecture.items()
    ]


def build_import_payload(
    items: Sequence[Mapping[str, object]],
    *,
    release_id: str,
    manifest_sha256: str,
) -> dict[str, object]:
    """Wrap rendered items in the exact ready-release importer payload shape."""

    if not isinstance(release_id, str) or not release_id.strip():
        raise ValueError("release_id must not be empty")
    if (
        not isinstance(manifest_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", manifest_sha256)
        or manifest_sha256 == "0" * 64
    ):
        raise ValueError("manifest_sha256 must be a non-zero lowercase sha256")
    normalized_items: list[dict[str, object]] = []
    for index, source in enumerate(items):
        if not isinstance(source, dict):
            raise ValueError(f"items[{index}] must be an object")
        item = dict(source)
        if item.get("checksum") != item_checksum(item):
            raise ValueError(f"items[{index}] has an invalid checksum")
        normalized_items.append(item)
    if not normalized_items:
        raise ValueError("ready payload items must not be empty")
    return {
        "schema_version": 1,
        "release_id": release_id.strip(),
        "release_status": "ready",
        "manifest_sha256": manifest_sha256,
        "items": normalized_items,
    }


def build_deployment_bundle(
    items: Sequence[Mapping[str, object]],
    *,
    release_id: str,
    source_manifest_sha256: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Bind a ready importer payload to its exact immutable item inventory."""

    if (
        not isinstance(source_manifest_sha256, str)
        or not re.fullmatch(r"[a-f0-9]{64}", source_manifest_sha256)
        or source_manifest_sha256 == "0" * 64
    ):
        raise ValueError("source_manifest_sha256 must be a non-zero lowercase sha256")
    normalized_items: list[dict[str, object]] = []
    for index, source in enumerate(items):
        if not isinstance(source, dict):
            raise ValueError(f"items[{index}] must be an object")
        item = dict(source)
        if item.get("checksum") != item_checksum(item):
            raise ValueError(f"items[{index}] has an invalid checksum")
        normalized_items.append(item)
    if not normalized_items:
        raise ValueError("ready payload items must not be empty")
    inventory = sorted(
        (
            {
                "page_key": str(item["page_key"]),
                "checksum": str(item["checksum"]),
            }
            for item in normalized_items
        ),
        key=lambda row: (row["page_key"], row["checksum"]),
    )
    if len({row["page_key"] for row in inventory}) != len(inventory):
        raise ValueError("deployment inventory contains duplicate page_key")
    manifest: dict[str, object] = {
        "schema_version": 1,
        "release_id": release_id.strip(),
        "release_status": "ready",
        "source_manifest_sha256": source_manifest_sha256,
        "items": inventory,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    payload = build_import_payload(
        normalized_items,
        release_id=release_id,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
    )
    return manifest, payload


def load_pages(directory: Path) -> list[dict[str, object]]:
    """Load sorted ``*.json`` page sources from one directory."""

    pages: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name.casefold()):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"page source must be an object: {path}")
        pages.append(payload)
    if not pages:
        raise ValueError(f"pages directory has no JSON sources: {directory}")
    return pages


def _add_source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pages-dir",
        type=Path,
        default=DEFAULT_PAGES_DIR,
        help=f"page source directory (default: {DEFAULT_PAGES_DIR})",
    )
    parser.add_argument(
        "--architecture",
        type=Path,
        default=None,
        help=(
            "approved architecture CSV; omission uses and verifies "
            f"{DEFAULT_ARCHITECTURE_PATH}"
        ),
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=DEFAULT_EVIDENCE_PATH,
        help=f"evidence registry (default: {DEFAULT_EVIDENCE_PATH})",
    )


def _load_inputs(args: argparse.Namespace) -> tuple[
    list[dict[str, object]],
    dict[str, dict[str, str]],
    dict[str, dict[str, object]],
]:
    pages = load_pages(args.pages_dir)
    architecture = (
        load_default_architecture()
        if args.architecture is None
        else load_architecture(args.architecture)
    )
    evidence = load_evidence(args.evidence)
    return pages, architecture, evidence


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for validation, item rendering and final payload wrapping."""

    parser = argparse.ArgumentParser(
        description="Validate and render production child-service page sources"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate", help="validate all page sources")
    _add_source_arguments(validate_parser)

    render_items_parser = commands.add_parser(
        "render-items", help="render importer items as a JSON list"
    )
    _add_source_arguments(render_items_parser)
    render_items_parser.add_argument("--output", type=Path, required=True)

    render_payload_parser = commands.add_parser(
        "render-payload", help="render a complete ready importer payload"
    )
    _add_source_arguments(render_payload_parser)
    render_payload_parser.add_argument("--release-id", required=True)
    render_payload_parser.add_argument("--manifest-sha256", required=True)
    render_payload_parser.add_argument("--output", type=Path, required=True)

    render_bundle_parser = commands.add_parser(
        "render-bundle",
        help="render a ready payload and its exact deployment manifest",
    )
    _add_source_arguments(render_bundle_parser)
    render_bundle_parser.add_argument("--release-id", required=True)
    render_bundle_parser.add_argument("--source-manifest", type=Path, required=True)
    render_bundle_parser.add_argument(
        "--deployment-manifest-output", type=Path, required=True
    )
    render_bundle_parser.add_argument("--payload-output", type=Path, required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)
    pages, architecture, evidence = _load_inputs(args)
    errors = validate_collection(pages, architecture, evidence)
    if errors:
        raise ValueError("invalid service page collection:\n- " + "\n- ".join(errors))
    if args.command == "validate":
        print(f"validated {len(pages)} service pages")
        return 0

    items = build_import_items(pages, architecture, evidence)
    if args.command == "render-bundle":
        source_manifest_sha256 = hashlib.sha256(
            args.source_manifest.read_bytes()
        ).hexdigest()
        deployment_manifest, payload = build_deployment_bundle(
            items,
            release_id=args.release_id,
            source_manifest_sha256=source_manifest_sha256,
        )
        for output_path, output in (
            (args.deployment_manifest_output, deployment_manifest),
            (args.payload_output, payload),
        ):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print(
            f"rendered {len(items)} service page items to "
            f"{args.payload_output} with manifest {args.deployment_manifest_output}"
        )
        return 0

    output: object = items
    if args.command == "render-payload":
        output = build_import_payload(
            items,
            release_id=args.release_id,
            manifest_sha256=args.manifest_sha256,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"rendered {len(items)} service page items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
