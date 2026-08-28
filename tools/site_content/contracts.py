"""Fail-closed content contracts for the service-hub release."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping
import unicodedata

from tools.seo_semantics.architecture import PageDestination
from tools.site_content.cases import (
    CaseEvidence,
    catalog_from_document,
    validate_case_reference,
    validate_catalog_document,
)


PLACEHOLDER_PATTERNS = (
    "lorem",
    "todo",
    "tbd",
    "{{",
    "}}",
    "здесь будет",
    "вставить текст",
    "текст-заглушка",
    "по запросу",
)

LEGACY_SHARED_RELATED_TEXT = (
    "Форма для предварительного обращения по работам на вашем участке."
)
LEGACY_SHARED_RELATED_FINGERPRINT = (
    "форма для предварительного обращения по работам на вашем участке"
)
LEGACY_SHARED_RELATED_LOCATIONS = frozenset(
    {
        ("S4-HUB", "related_links.items[2].text"),
        ("S5-HUB", "related_links.items[2].text"),
    }
)

SERVICE_SOURCE_SLUGS = {
    "S1": "landshaftnoe-proektirovanie",
    "S2": "gazon-posevnojj-i-gazon-rulonnyjj",
    "S3": "posadka-derevev-i-kustarnikov",
    "S4": "ukhod-za-sadom",
    "S5": "planirovka-territorii",
    "S6": "podpornye-stenki",
    "S7": "ulichnoe-osveshhenie-uchastka",
    "S8": "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch",
}

_NUMBER_PATTERN = r"\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?"
_MONEY_UNIT_PATTERN = r"(?:₽|руб(?:\.|лей|ля)?)"
_TIME_UNIT_PATTERN = (
    r"(?:час(?:а|ов)?|день|дня|дней|недел(?:я|и|ь)|"
    r"месяц(?:а|ев)?|года|год|лет)"
)
_RANGE_SEPARATOR_PATTERN = r"(?:-|–|—|до)"
_PRICE_RANGE_RE = re.compile(
    rf"(?P<claim>(?:от\s+)?{_NUMBER_PATTERN}\s*{_RANGE_SEPARATOR_PATTERN}\s*"
    rf"{_NUMBER_PATTERN}\s*{_MONEY_UNIT_PATTERN})",
    re.IGNORECASE,
)
_PRICE_SERIES_RE = re.compile(
    rf"(?P<series>{_NUMBER_PATTERN}(?:\s*(?:,|или|/)\s*{_NUMBER_PATTERN})+)"
    rf"\s*(?P<unit>{_MONEY_UNIT_PATTERN})",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(
    rf"(?P<number>{_NUMBER_PATTERN})\s*(?P<unit>{_MONEY_UNIT_PATTERN})",
    re.IGNORECASE,
)
_PRICE_MARKER_RE = re.compile(
    rf"(?:цена|стоимост\w*)[^\d.!?;]{{0,60}}(?P<number>{_NUMBER_PATTERN})",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    rf"(?P<number>{_NUMBER_PATTERN})\s*(?P<unit>{_TIME_UNIT_PATTERN})",
    re.IGNORECASE,
)
_TIME_RANGE_RE = re.compile(
    rf"(?P<claim>(?:от\s+)?{_NUMBER_PATTERN}\s*{_RANGE_SEPARATOR_PATTERN}\s*"
    rf"{_NUMBER_PATTERN}\s*{_TIME_UNIT_PATTERN})",
    re.IGNORECASE,
)


class ContractError(ValueError):
    """Raised when content cannot be loaded without ambiguity."""


@dataclass(frozen=True)
class ContentPage:
    """One JSON content page together with its source path."""

    path: Path
    data: Mapping[str, Any]


class CaseCatalogIndex(dict[int, CaseEvidence]):
    """Case mapping plus every separately audited internal image URL."""

    def __init__(
        self,
        cases: Iterable[CaseEvidence],
        *,
        verified_image_urls: Iterable[str] = (),
        verified_image_urls_by_service: Mapping[str, Iterable[str]] | None = None,
    ) -> None:
        super().__init__((case.page_id, case) for case in cases)
        self.verified_image_urls = frozenset(verified_image_urls)
        self.verified_image_urls_by_service = {
            service_id: frozenset(urls)
            for service_id, urls in (verified_image_urls_by_service or {}).items()
        }


@dataclass(frozen=True)
class ReleaseLinkAllowlist:
    """Separate architecture destinations from cataloged case evidence URLs."""

    managed_urls: frozenset[str]
    preserved_urls: frozenset[str]
    case_urls: frozenset[str]

    @property
    def internal_urls(self) -> frozenset[str]:
        return self.managed_urls | self.preserved_urls | self.case_urls


def build_release_link_allowlist(
    architecture: Mapping[str, PageDestination],
    cases: Mapping[int, CaseEvidence],
) -> ReleaseLinkAllowlist:
    """Build the fail-closed URL sets used by content link validation."""
    managed_roles = {"hub", "child_service", "article"}
    preserved_roles = {"frozen", "special"}
    return ReleaseLinkAllowlist(
        managed_urls=frozenset(
            destination.canonical_url
            for destination in architecture.values()
            if destination.page_role in managed_roles
        ),
        preserved_urls=frozenset(
            destination.canonical_url
            for destination in architecture.values()
            if destination.page_role in preserved_roles
        ),
        case_urls=frozenset(case.url for case in cases.values()),
    )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_content_page(path: Path) -> ContentPage:
    """Load one strict UTF-8 JSON object without accepting duplicate keys."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw, object_pairs_hook=_strict_object)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load content page {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ContractError(f"content page {path} must contain a JSON object")
    return ContentPage(path=path, data=data)


def load_page_architecture(path: Path) -> dict[str, PageDestination]:
    """Load the reviewed destination ledger without changing its decisions."""
    required = set(PageDestination.__dataclass_fields__)
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                missing = sorted(required - set(reader.fieldnames or ()))
                raise ContractError(f"page architecture is missing columns: {', '.join(missing)}")
            rows = list(reader)
    except ContractError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractError(f"cannot load page architecture {path}: {exc}") from exc

    architecture: dict[str, PageDestination] = {}
    canonicals: set[str] = set()
    for row in rows:
        destination_id = row["destination_id"].strip()
        canonical = row["canonical_url"].strip()
        if not destination_id or destination_id in architecture:
            raise ContractError(f"duplicate or blank architecture page_key: {destination_id!r}")
        if not canonical or canonical in canonicals:
            raise ContractError(f"duplicate or blank architecture canonical: {canonical!r}")
        architecture[destination_id] = PageDestination(
            destination_id=destination_id,
            service_id=row["service_id"].strip(),
            page_role=row["page_role"].strip(),
            parent_destination_id=row["parent_destination_id"].strip(),
            canonical_url=canonical,
            source_cluster_ids=tuple(
                item for item in row["source_cluster_ids"].split("|") if item
            ),
            current_url=row["current_url"].strip(),
            proposed_url=row["proposed_url"].strip(),
            primary_cluster_id=row["primary_cluster_id"].strip(),
            url_action=row["url_action"].strip(),
            publication_status=row["publication_status"].strip(),
            evidence_refs=row["evidence_refs"].strip(),
            review_status=row["review_status"].strip(),
            reviewer=row["reviewer"].strip(),
            rationale=row["rationale"].strip(),
        )
        canonicals.add(canonical)
    return architecture


def load_case_catalog(path: Path) -> CaseCatalogIndex:
    """Load and validate the committed Task 3 catalog without network access."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load case catalog {path}: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ContractError("case catalog must contain a JSON object")
    errors = validate_catalog_document(document)
    if errors:
        raise ContractError("invalid case catalog: " + "; ".join(errors))
    cases = catalog_from_document(document)
    if len({case.page_id for case in cases}) != len(cases):
        raise ContractError("case catalog contains duplicate page_id values")
    verified_images: list[str] = []
    verified_by_service: dict[str, set[str]] = {
        service_id: set() for service_id in SERVICE_SOURCE_SLUGS
    }
    selected = document.get("selected_image_audits")
    if isinstance(selected, list):
        for row in selected:
            if (
                isinstance(row, Mapping)
                and isinstance(row.get("url"), str)
                and isinstance(row.get("http_status"), int)
                and 200 <= row["http_status"] < 300
                and str(row.get("content_type", "")).startswith("image/")
                and row.get("final_url") == row.get("url")
            ):
                verified_images.append(row["url"])
                source_refs = row.get("source_refs")
                if isinstance(source_refs, list):
                    normalized_refs = [str(ref).replace("\\", "/") for ref in source_refs]
                    for service_id, slug in SERVICE_SOURCE_SLUGS.items():
                        if any(f"/{slug}.json#" in ref for ref in normalized_refs):
                            verified_by_service[service_id].add(row["url"])
    return CaseCatalogIndex(
        cases,
        verified_image_urls=verified_images,
        verified_image_urls_by_service=verified_by_service,
    )


def load_release_manifest(path: Path) -> dict[str, Any]:
    """Load the release ledger as strict UTF-8 JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load release manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError("release manifest must contain a JSON object")
    return data


def _text_leaves(value: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _text_leaves(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _text_leaves(item, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _time_claim_type(text: str, start: int, end: int) -> str:
    clause_start = max(text.rfind(mark, 0, start) for mark in (",", ";", ".", "!", "?"))
    prefix = text[clause_start + 1 : start].casefold()
    suffix = re.split(r"[,;.!?]", text[end:], maxsplit=1)[0][:60].casefold()
    return "guarantee" if "гарант" in prefix or "гарант" in suffix else "term"


def numeric_fact_claims(text: str) -> tuple[tuple[str, str], ...]:
    """Extract each exact numeric price, term or guarantee claim in source order."""
    claims: list[tuple[int, str, str]] = []
    price_range_matches = list(_PRICE_RANGE_RE.finditer(text))
    price_range_spans = [match.span() for match in price_range_matches]
    for match in price_range_matches:
        claims.append((match.start(), "price", match.group("claim").strip()))
    for match in _PRICE_SERIES_RE.finditer(text):
        unit = match.group("unit")
        for number in re.findall(_NUMBER_PATTERN, match.group("series")):
            claims.append((match.start(), "price", f"{number.strip()} {unit}"))
    direct_price_matches = list(_PRICE_RE.finditer(text))
    for match in direct_price_matches:
        if any(start <= match.start() < end for start, end in price_range_spans):
            continue
        claims.append((match.start(), "price", match.group(0).strip()))
    for match in _PRICE_MARKER_RE.finditer(text):
        number_start, _ = match.span("number")
        if any(start <= number_start < end for start, end in price_range_spans):
            continue
        if any(start <= number_start < end for start, end in (item.span() for item in direct_price_matches)):
            continue
        claims.append((number_start, "price", match.group("number").strip()))
    time_range_matches = list(_TIME_RANGE_RE.finditer(text))
    time_range_spans = [match.span() for match in time_range_matches]
    for match in time_range_matches:
        claim_type = _time_claim_type(text, match.start(), match.end())
        claims.append((match.start(), claim_type, match.group("claim").strip()))
    for match in _TIME_RE.finditer(text):
        if any(start <= match.start() < end for start, end in time_range_spans):
            continue
        claim_type = _time_claim_type(text, match.start(), match.end())
        claims.append((match.start(), claim_type, match.group(0).strip()))
    result: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for _, claim_type, claim in sorted(claims, key=lambda item: item[0]):
        key = (claim_type, claim)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return tuple(result)


def _has_fact_evidence(
    data: Mapping[str, Any],
    path: str,
    claim_type: str,
    claim: str,
) -> bool:
    evidence = data.get("fact_evidence")
    if not isinstance(evidence, list):
        return False
    for item in evidence:
        if not isinstance(item, Mapping):
            continue
        if (
            item.get("path") == path
            and item.get("claim_type") == claim_type
            and item.get("claim") == claim
            and isinstance(item.get("source_ref"), str)
            and bool(item["source_ref"].strip())
        ):
            return True
    return False


def _validate_text(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, text in _text_leaves(data):
        if not text.strip():
            errors.append(f"{path} must not be blank")
            continue
        folded = " ".join(text.casefold().split())
        if "\ufffd" in text:
            errors.append(f"{path} contains Unicode replacement character")
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in folded:
                errors.append(f"{path} contains prohibited placeholder text: {pattern}")
                break
        if not path.startswith("fact_evidence["):
            for claim_type, claim in numeric_fact_claims(text):
                if not _has_fact_evidence(data, path, claim_type, claim):
                    errors.append(
                        f"{path} numeric {claim_type} claim {claim!r} lacks fact_evidence"
                    )
    return errors


def _case_by_id(
    case_id: int,
    cases: Mapping[int, CaseEvidence],
) -> CaseEvidence | None:
    case = cases.get(case_id)
    return case if isinstance(case, CaseEvidence) else None


def _validate_image(
    image: Any,
    path: str,
    service_id: str,
    cases: Mapping[int, CaseEvidence],
    *,
    expected_case_id: int | None = None,
) -> list[str]:
    if not isinstance(image, Mapping):
        return [f"{path} must be an object"]
    errors: list[str] = []
    alt = image.get("alt")
    if not isinstance(alt, str) or not alt.strip():
        errors.append(f"{path}.alt must not be blank")
    case_id = expected_case_id if expected_case_id is not None else image.get("case_id")
    image_url = image.get("url")
    if expected_case_id is None and case_id is None:
        verified_by_service = getattr(cases, "verified_image_urls_by_service", {})
        verified_images = verified_by_service.get(service_id, frozenset())
        if not isinstance(image_url, str) or image_url not in verified_images:
            errors.append(
                f"{path}.url is absent from verified catalog images for {service_id}"
            )
        return errors
    if not isinstance(case_id, int) or case_id <= 0:
        errors.append(f"{path}.case_id must identify a verified case")
        return errors
    case = _case_by_id(case_id, cases)
    if case is None:
        errors.append(f"unknown case {case_id}")
        return errors
    if service_id not in case.service_ids:
        errors.append(f"case {case_id} does not support service {service_id}")
    if not isinstance(image_url, str):
        errors.append(f"{path}.url must be a string")
    else:
        errors.extend(validate_case_reference(case_id, image_url, tuple(cases.values())))
    return errors


def _validate_embedded_images(
    value: Any,
    path: str,
    service_id: str,
    cases: Mapping[int, CaseEvidence],
) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if key == "image":
                errors.extend(_validate_image(item, child_path, service_id, cases))
            else:
                errors.extend(_validate_embedded_images(item, child_path, service_id, cases))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(
                _validate_embedded_images(item, f"{path}[{index}]", service_id, cases)
            )
    return errors


def _validate_gallery_images(
    data: Mapping[str, Any],
    service_id: str,
    cases: Mapping[int, CaseEvidence],
) -> list[str]:
    proof = data.get("proof")
    gallery = proof.get("gallery") if isinstance(proof, Mapping) else None
    if not isinstance(gallery, list):
        return []
    errors: list[str] = []
    for index, image in enumerate(gallery):
        errors.extend(
            _validate_image(image, f"proof.gallery[{index}]", service_id, cases)
        )
    return errors


def _validate_cases(
    data: Mapping[str, Any],
    cases: Mapping[int, CaseEvidence],
) -> list[str]:
    proof = data.get("proof")
    if not isinstance(proof, Mapping):
        return []
    rows = proof.get("cases")
    if not isinstance(rows, list):
        return []
    service_id = str(data.get("service_id", ""))
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"proof.cases[{index}] must be an object")
            continue
        case_id = row.get("page_id")
        if not isinstance(case_id, int) or case_id <= 0:
            errors.append(f"proof.cases[{index}].page_id must be a positive integer")
            continue
        case = _case_by_id(case_id, cases)
        if case is None:
            errors.append(f"unknown case {case_id}")
            continue
        if row.get("url") != case.url:
            errors.append(f"case {case_id} URL does not match the case catalog")
        errors.extend(
            _validate_image(
                row.get("image"),
                f"proof.cases[{index}].image",
                service_id,
                cases,
                expected_case_id=case_id,
            )
        )
    return errors


def _validate_service_fallback(
    data: Mapping[str, Any],
    cases: Mapping[int, CaseEvidence],
) -> list[str]:
    proof = data.get("proof")
    fallback = proof.get("hub_case_fallback") if isinstance(proof, Mapping) else None
    if fallback is None:
        return []
    error = "hub_case_fallback must reference a verified supporting case"
    if not isinstance(fallback, Mapping):
        return [error]
    case_id = fallback.get("page_id")
    reason = fallback.get("reason")
    source_ref = fallback.get("source_ref")
    if not (
        isinstance(case_id, int)
        and case_id > 0
        and isinstance(reason, str)
        and bool(reason.strip())
        and isinstance(source_ref, str)
        and bool(source_ref.strip())
    ):
        return [error]
    case = _case_by_id(case_id, cases)
    service_id = str(data.get("service_id", ""))
    if (
        case is None
        or service_id not in case.service_ids
        or fallback.get("url") != case.url
    ):
        return [error]
    image_errors = _validate_image(
        fallback.get("image"),
        "proof.hub_case_fallback.image",
        service_id,
        cases,
        expected_case_id=case_id,
    )
    return [error] if image_errors else []


def _validate_link_items(
    value: Any,
    allowed_urls: set[str],
) -> list[str]:
    if not isinstance(value, list):
        return []
    errors: list[str] = []
    for item in value:
        url = item.get("url") if isinstance(item, Mapping) else item
        if not isinstance(url, str) or not url:
            errors.append("internal link must be a non-blank URL")
        elif url not in allowed_urls:
            errors.append("internal link is outside the release allowlist")
    return errors


def _validate_typed_relation_items(
    value: Any,
    path: str,
    allowed_roles: set[str],
    architecture: Mapping[str, PageDestination],
    cases: Mapping[int, CaseEvidence],
    *,
    allow_cases: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        return []
    errors: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, Mapping):
            errors.append(f"{item_path} must be a typed link object")
            continue
        role = item.get("role")
        url = item.get("url")
        if role == "case" and allow_cases:
            case_id = item.get("case_id")
            case = _case_by_id(case_id, cases) if isinstance(case_id, int) else None
            if case is None or url != case.url:
                errors.append(f"{item_path} does not match the case catalog")
            continue
        page_key = item.get("page_key")
        if not (
            isinstance(page_key, str)
            and page_key
            and isinstance(role, str)
            and role
            and isinstance(url, str)
            and url
        ):
            errors.append(f"{item_path} must be a typed link object")
            continue
        destination = architecture.get(page_key)
        if destination is None or destination.canonical_url != url or destination.page_role != role:
            errors.append(f"{item_path} does not match page architecture")
            continue
        if role not in allowed_roles:
            errors.append(f"{item_path} has a prohibited page role")
    return errors


def _has_substantive_text(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) >= 45


def _validate_named_items(value: Any, path: str, minimum: int) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        suffix = "item" if minimum == 1 else "items"
        return [f"{path} must contain at least {minimum} {suffix}"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"{path}[{index}] must be an object")
            continue
        if not isinstance(item.get("title"), str) or not item["title"].strip():
            errors.append(f"{path}[{index}].title must not be blank")
        if not _has_substantive_text(item.get("text")):
            errors.append(f"{path}[{index}].text must contain substantive text")
    return errors


def _validate_faq_items(value: Any, minimum: int) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        return [f"faq must contain at least {minimum} items"]
    errors: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            errors.append(f"faq[{index}] must be an object")
            continue
        if not isinstance(item.get("question"), str) or not item["question"].strip():
            errors.append(f"faq[{index}].question must not be blank")
        if not _has_substantive_text(item.get("answer")):
            errors.append(f"faq[{index}].answer must contain substantive text")
    return errors


def _validate_relation_minimum(data: Mapping[str, Any], field: str) -> list[str]:
    value = data.get(field)
    if not isinstance(value, list) or not value:
        return [f"{field} must contain at least 1 item"]
    return []


def _validate_common_page_shape(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    canonical = data.get("canonical")
    expected_slug = ""
    if isinstance(canonical, str) and canonical.strip():
        expected_slug = canonical.rstrip("/").rsplit("/", 1)[-1]
    if not expected_slug or data.get("slug") != expected_slug:
        errors.append("slug must be non-blank and match canonical")
    seo = data.get("seo")
    if not (
        isinstance(seo, Mapping)
        and isinstance(seo.get("title"), str)
        and bool(seo["title"].strip())
        and isinstance(seo.get("description"), str)
        and bool(seo["description"].strip())
    ):
        errors.append("seo must contain title and description")
    hero = data.get("hero")
    image = hero.get("image") if isinstance(hero, Mapping) else None
    if not (
        isinstance(hero, Mapping)
        and isinstance(hero.get("title"), str)
        and bool(hero["title"].strip())
        and isinstance(hero.get("lead"), str)
        and bool(hero["lead"].strip())
        and isinstance(image, Mapping)
        and isinstance(image.get("url"), str)
        and bool(image["url"].strip())
        and isinstance(image.get("alt"), str)
        and bool(image["alt"].strip())
    ):
        errors.append("hero must contain title, lead and a verified main image")
    return errors


def _validate_service_contract(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("problem", "solution"):
        if not _has_substantive_text(data.get(field)):
            errors.append(f"{field} must contain substantive text")
    errors.extend(_validate_named_items(data.get("sections"), "sections", 5))
    errors.extend(_validate_named_items(data.get("price_factors"), "price_factors", 1))
    errors.extend(_validate_named_items(data.get("process"), "process", 1))
    errors.extend(_validate_faq_items(data.get("faq"), 5))
    proof = data.get("proof")
    cases = proof.get("cases") if isinstance(proof, Mapping) else None
    fallback = proof.get("hub_case_fallback") if isinstance(proof, Mapping) else None
    if not isinstance(cases, list) or (not cases and not isinstance(fallback, Mapping)):
        errors.append("service page requires a verified case or hub_case_fallback")
    for field in ("related_commercial_links", "related_article_links"):
        errors.extend(_validate_relation_minimum(data, field))
    return errors


def _validate_article_contract(data: Mapping[str, Any]) -> list[str]:
    errors = _validate_named_items(data.get("sections"), "sections", 4)
    faq = data.get("faq")
    if isinstance(faq, list) and faq and data.get("faq_supported_by_cluster") is not True:
        errors.append("article FAQ requires faq_supported_by_cluster=true")
    if faq is not None:
        errors.extend(_validate_faq_items(faq, 0))
    errors.extend(_validate_relation_minimum(data, "related_commercial_links"))
    return errors


def _validate_hub_shape(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 2:
        errors.append("hub schema_version must be 2")
    for field in (
        "seo",
        "hero",
        "intro",
        "scope",
        "services",
        "articles",
        "process",
        "pricing",
        "proof",
        "geo",
        "faq",
        "related_links",
        "cta",
    ):
        if not isinstance(data.get(field), Mapping):
            errors.append(f"hub must preserve v1 section {field}")
    return errors


def _normalized_fingerprint(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(re.findall(r"[0-9a-zа-я]+", folded))


def _paragraph_candidates(data: Mapping[str, Any]) -> Iterable[tuple[str, str]]:
    for path, text in _text_leaves(data):
        if len(_normalized_fingerprint(text)) < 45:
            continue
        if path.startswith("fact_evidence[") or path.endswith((".url", ".href", ".alt")):
            continue
        if path in {"canonical", "slug", "page_key", "service_id", "page_type"}:
            continue
        if path.startswith("seo.") or path.endswith(
            (".title", ".heading", ".label", ".question", ".button_label")
        ):
            continue
        yield path, text


def _is_allowed_legacy_paragraph_duplicate(
    fingerprint: str,
    occurrences: list[tuple[str, str, str]],
) -> bool:
    """Allow only the exact S4/S5 copy already shared before schema v2."""
    return (
        len(occurrences) == 2
        and fingerprint == LEGACY_SHARED_RELATED_FINGERPRINT
        and all(text == LEGACY_SHARED_RELATED_TEXT for _, _, text in occurrences)
        and frozenset(
            (page_key, path) for page_key, path, _ in occurrences
        )
        == LEGACY_SHARED_RELATED_LOCATIONS
    )


def validate_content_collection(
    pages: Iterable[ContentPage],
    architecture: Mapping[str, PageDestination],
    cases: Mapping[int, CaseEvidence],
) -> list[str]:
    """Validate cross-page uniqueness and architecture ownership."""
    page_list = list(pages)
    errors: list[str] = []
    for page in page_list:
        errors.extend(validate_content_page(page, architecture, cases))

    fields: dict[str, list[str]] = {
        "canonical": [],
        "seo.title": [],
        "seo.description": [],
        "hero.title": [],
    }
    paragraphs: dict[str, list[tuple[str, str, str]]] = {}
    for page in page_list:
        fields["canonical"].append(str(page.data.get("canonical", "")))
        seo = page.data.get("seo")
        hero = page.data.get("hero")
        fields["seo.title"].append(str(seo.get("title", "")) if isinstance(seo, Mapping) else "")
        fields["seo.description"].append(
            str(seo.get("description", "")) if isinstance(seo, Mapping) else ""
        )
        fields["hero.title"].append(
            str(hero.get("title", "")) if isinstance(hero, Mapping) else ""
        )
        page_key = str(page.data.get("page_key", ""))
        for path, text in _paragraph_candidates(page.data):
            fingerprint = _normalized_fingerprint(text)
            paragraphs.setdefault(fingerprint, []).append((page_key, path, text))
    for field, values in fields.items():
        fingerprints = [_normalized_fingerprint(value) for value in values if value]
        if len(fingerprints) != len(set(fingerprints)):
            label = "H1" if field == "hero.title" else field
            errors.append(f"duplicate normalized {label} across content pages")
    if any(
        len(occurrences) > 1
        and not _is_allowed_legacy_paragraph_duplicate(fingerprint, occurrences)
        for fingerprint, occurrences in paragraphs.items()
    ):
        errors.append("repeated paragraph fingerprint across content pages")

    cluster_counts: dict[str, int] = {}
    for destination in architecture.values():
        for cluster_id in destination.source_cluster_ids:
            cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
    for cluster_id, count in sorted(cluster_counts.items()):
        if count != 1:
            errors.append(f"cluster {cluster_id} has {count} page owners")
    return sorted(set(errors))


def validate_release_manifest(
    manifest: Mapping[str, Any],
    architecture: Mapping[str, PageDestination],
) -> list[str]:
    """Reconcile managed and preserved pages with the reviewed architecture."""
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("release manifest schema_version must be 1")
    if not isinstance(manifest.get("release_id"), str) or not manifest["release_id"].strip():
        errors.append("release_id must be non-blank")
    release_status = manifest.get("release_status")
    if release_status not in {"draft", "ready"}:
        errors.append("release_status must be draft or ready")

    expected_managed = {
        key: destination
        for key, destination in architecture.items()
        if destination.page_role in {"hub", "child_service", "article"}
    }
    expected_preserved = {
        key: destination
        for key, destination in architecture.items()
        if destination.page_role in {"frozen", "special"}
    }
    collections = (
        ("managed_pages", expected_managed, True),
        ("preserved_pages", expected_preserved, False),
    )
    all_manifest_keys: set[str] = set()
    all_manifest_urls: set[str] = set()
    has_pending = False
    has_nonready_architecture = False
    for field, expected, managed in collections:
        rows = manifest.get(field)
        if not isinstance(rows, list):
            errors.append(f"{field} must be an array")
            continue
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, Mapping):
                errors.append(f"{field} entry must be an object")
                continue
            page_key = str(row.get("page_key", ""))
            canonical = str(row.get("canonical", ""))
            if not page_key or page_key in all_manifest_keys:
                errors.append("manifest contains duplicate or blank page_key")
            all_manifest_keys.add(page_key)
            seen.add(page_key)
            if not canonical or canonical in all_manifest_urls:
                errors.append("manifest contains duplicate or blank canonical")
            all_manifest_urls.add(canonical)
            destination = expected.get(page_key)
            if destination is None:
                errors.append("manifest page is absent from architecture")
                continue
            expected_parent = destination.parent_destination_id
            if (
                row.get("service_id") != destination.service_id
                or row.get("page_role") != destination.page_role
                or row.get("parent_page_key", "") != expected_parent
                or row.get("canonical") != destination.canonical_url
                or row.get("architecture_status") != destination.publication_status
            ):
                errors.append(f"manifest page {page_key} drifts from architecture")
            if managed:
                content_status = row.get("content_status")
                if content_status not in {"content_pending", "validated"}:
                    errors.append(f"manifest page {page_key} has invalid content_status")
                has_pending = has_pending or content_status == "content_pending"
                has_nonready_architecture = (
                    has_nonready_architecture or destination.publication_status != "ready"
                )
        if set(expected) - seen:
            errors.append("architecture page is absent from manifest")
    if release_status == "ready" and has_pending:
        errors.append("ready release contains content_pending pages")
    if release_status == "ready" and has_nonready_architecture:
        errors.append("ready release contains blocked or backlog architecture pages")
    return sorted(set(errors))


def _validate_architecture_owner(
    data: Mapping[str, Any],
    architecture: Mapping[str, PageDestination],
) -> list[str]:
    page_key = data.get("page_key")
    if not isinstance(page_key, str) or page_key not in architecture:
        return ["page_key is absent from page architecture"]
    destination = architecture[page_key]
    errors: list[str] = []
    expected_role = {
        "hub": "hub",
        "service": "child_service",
        "article": "article",
    }.get(str(data.get("page_type")))
    if data.get("service_id") != destination.service_id:
        errors.append("service_id differs from page architecture")
    if expected_role != destination.page_role:
        errors.append("page_type differs from page architecture")
    if data.get("canonical") != destination.canonical_url:
        errors.append("canonical differs from page architecture")
    return errors


def _validate_hub_navigation(
    data: Mapping[str, Any],
    architecture: Mapping[str, PageDestination],
) -> list[str]:
    page_key = str(data.get("page_key", ""))
    service_id = str(data.get("service_id", ""))
    errors: list[str] = []
    scope = data.get("scope")
    scope_items = scope.get("items") if isinstance(scope, Mapping) else None
    if isinstance(scope_items, list):
        for item in scope_items:
            if isinstance(item, Mapping) and ("url" in item or "page_key" in item):
                errors.append("scope item must remain descriptive and unlinked")

    expected_by_field = {
        "services": {
            destination.destination_id: destination
            for destination in architecture.values()
            if destination.page_role == "child_service"
            and destination.parent_destination_id == page_key
            and destination.service_id == service_id
        },
        "articles": {
            destination.destination_id: destination
            for destination in architecture.values()
            if destination.page_role == "article"
            and destination.parent_destination_id == page_key
            and destination.service_id == service_id
        },
    }
    labels = {"services": "child", "articles": "article"}
    for field, expected in expected_by_field.items():
        section = data.get(field)
        items = section.get("items") if isinstance(section, Mapping) else None
        if not (
            isinstance(section, Mapping)
            and isinstance(section.get("heading"), str)
            and bool(section["heading"].strip())
            and isinstance(section.get("lead"), str)
            and bool(section["lead"].strip())
            and isinstance(items, list)
        ):
            errors.append(f"{field} must contain heading, lead and items array")
        seen: list[str] = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, Mapping):
                    errors.append(f"{labels[field]} card must be an object")
                    continue
                image = item.get("image")
                if not (
                    isinstance(item.get("page_key"), str)
                    and bool(item["page_key"].strip())
                    and isinstance(item.get("url"), str)
                    and bool(item["url"].strip())
                    and isinstance(item.get("title"), str)
                    and bool(item["title"].strip())
                    and _has_substantive_text(item.get("text"))
                    and isinstance(image, Mapping)
                    and isinstance(image.get("url"), str)
                    and bool(image["url"].strip())
                    and isinstance(image.get("alt"), str)
                    and bool(image["alt"].strip())
                ):
                    errors.append(
                        f"{labels[field]} card must contain page_key, url, title, text and image"
                    )
                item_key = item.get("page_key")
                if isinstance(item_key, str):
                    seen.append(item_key)
                destination = expected.get(str(item_key))
                if destination is None or item.get("url") != destination.canonical_url:
                    errors.append(f"{labels[field]} card does not match page architecture")
        for destination_id in sorted(expected):
            count = seen.count(destination_id)
            if count == 0:
                errors.append(f"hub is missing {labels[field]} page {destination_id}")
            elif count > 1:
                errors.append(f"hub repeats {labels[field]} page {destination_id}")
    return errors


def _validate_hub_evidence_state(
    data: Mapping[str, Any],
    architecture: Mapping[str, PageDestination],
    *,
    production_ready: bool,
) -> list[str]:
    """Make draft gaps explicit and prevent those gaps from crossing a ready gate."""
    errors: list[str] = []
    page_key = str(data.get("page_key", ""))
    proof = data.get("proof")
    cases = proof.get("cases") if isinstance(proof, Mapping) else None
    if isinstance(proof, Mapping) and "hub_case_fallback" in proof:
        errors.append("hub proof must not synthesize hub_case_fallback")

    expected_gaps: set[tuple[str, str, str]] = set()
    if not isinstance(cases, list) or not cases:
        expected_gaps.add(("missing_verified_case", page_key, "missing"))
    for field in ("services", "articles"):
        section = data.get(field)
        items = section.get("items") if isinstance(section, Mapping) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, Mapping):
                continue
            destination = architecture.get(str(item.get("page_key", "")))
            if destination is not None and destination.publication_status != "ready":
                expected_gaps.add(
                    (
                        "nonready_destination",
                        destination.destination_id,
                        destination.publication_status,
                    )
                )

    gaps = data.get("evidence_gaps")
    actual_gaps: set[tuple[str, str, str]] = set()
    if not isinstance(gaps, list):
        errors.append("evidence_gaps must be an array")
    else:
        for item in gaps:
            if not isinstance(item, Mapping):
                errors.append("evidence_gaps entry must be an object")
                continue
            gap = (
                str(item.get("kind", "")),
                str(item.get("page_key", "")),
                str(item.get("status", "")),
            )
            if not all(gap) or gap in actual_gaps:
                errors.append("evidence_gaps contains a blank or duplicate entry")
            actual_gaps.add(gap)
    if actual_gaps != expected_gaps:
        errors.append("evidence_gaps is missing unresolved content evidence")

    if production_ready:
        if not isinstance(cases, list) or not cases:
            errors.append("production-ready hub requires a verified case")
        if actual_gaps:
            errors.append("production-ready hub contains unresolved evidence_gaps")
        if any(kind == "nonready_destination" for kind, _, _ in expected_gaps):
            errors.append("production-ready hub links a nonready destination")
    return errors


def validate_content_page(
    page: ContentPage,
    architecture: Mapping[str, PageDestination],
    cases: Mapping[int, CaseEvidence],
    *,
    production_ready: bool = False,
) -> list[str]:
    """Return deterministic contract violations for one page."""
    errors = _validate_text(page.data)
    errors.extend(_validate_architecture_owner(page.data, architecture))
    page_type = page.data.get("page_type")
    if page_type in {"service", "article", "hub"}:
        errors.extend(_validate_common_page_shape(page.data))
    if page_type == "service":
        sections = page.data.get("sections")
        if not isinstance(sections, list) or len(sections) < 5:
            errors.append("sections must contain at least 5 items")
        errors.extend(_validate_service_contract(page.data))
    if page_type == "article":
        primary_query = page.data.get("primary_query")
        if (
            page.data.get("intent") != "informational"
            or not isinstance(primary_query, str)
            or not primary_query.strip()
        ):
            errors.append("primary_query must be non-blank informational text")
        sections = page.data.get("sections")
        if not isinstance(sections, list) or len(sections) < 4:
            errors.append("sections must contain at least 4 items")
        errors.extend(_validate_article_contract(page.data))
    if page_type == "hub":
        errors.extend(_validate_hub_shape(page.data))
        services = page.data.get("services")
        items = services.get("items") if isinstance(services, Mapping) else None
        if isinstance(items, list):
            approved_urls = {
                destination.canonical_url
                for destination in architecture.values()
                if destination.page_role == "child_service"
            }
            for item in items:
                if isinstance(item, Mapping) and item.get("url") not in approved_urls:
                    errors.append("service card URL is absent from page architecture")
        errors.extend(_validate_hub_navigation(page.data, architecture))
        errors.extend(
            _validate_hub_evidence_state(
                page.data,
                architecture,
                production_ready=production_ready,
            )
        )
    service_id = str(page.data.get("service_id", ""))
    errors.extend(_validate_embedded_images(page.data, "", service_id, cases))
    errors.extend(_validate_gallery_images(page.data, service_id, cases))
    errors.extend(_validate_cases(page.data, cases))
    if page_type == "service":
        errors.extend(_validate_service_fallback(page.data, cases))
    allowlist = build_release_link_allowlist(architecture, cases)
    allowed_urls = set(allowlist.internal_urls)
    related_roles = {
        "related_commercial_links": {"hub", "child_service"},
        "related_article_links": {"article"},
    }
    for field, roles in related_roles.items():
        errors.extend(_validate_link_items(page.data.get(field), allowed_urls))
        errors.extend(
            _validate_typed_relation_items(
                page.data.get(field),
                field,
                roles,
                architecture,
                cases,
            )
        )
    if page_type in {"service", "article"}:
        destination = architecture.get(str(page.data.get("page_key", "")))
        parent_key = destination.parent_destination_id if destination is not None else ""
        parent = architecture.get(parent_key)
        commercial_links = page.data.get("related_commercial_links")
        has_parent = isinstance(commercial_links, list) and any(
            isinstance(item, Mapping) and item.get("page_key") == parent_key
            for item in commercial_links
        )
        if (
            not parent_key
            or parent is None
            or parent.service_id != page.data.get("service_id")
            or not has_parent
        ):
            errors.append(
                "related_commercial_links must include the page architecture parent"
            )
    related = page.data.get("related_links")
    if isinstance(related, Mapping):
        release_urls = set(allowlist.managed_urls | allowlist.preserved_urls)
        errors.extend(_validate_link_items(related.get("items"), release_urls))
    pricing = page.data.get("pricing")
    calculator = pricing.get("calculator") if isinstance(pricing, Mapping) else None
    if isinstance(calculator, Mapping):
        calculator_owner = architecture.get("SPECIAL-CALCULATOR")
        if (
            calculator_owner is None
            or calculator.get("url") != calculator_owner.canonical_url
        ):
            errors.append("pricing.calculator.url must match SPECIAL-CALCULATOR")
    return sorted(set(errors))


def validate_content_page_dict(
    data: Mapping[str, Any],
    architecture: Mapping[str, PageDestination],
    cases: Mapping[int, CaseEvidence],
    *,
    production_ready: bool = False,
) -> list[str]:
    """Validate an in-memory page fixture without writing a temporary file."""
    return validate_content_page(
        ContentPage(Path("<memory>"), data),
        architecture,
        cases,
        production_ready=production_ready,
    )
