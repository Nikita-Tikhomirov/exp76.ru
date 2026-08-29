"""Build and validate traceable case and selected-image evidence.

Local files remain the authority for work, location, service and image
ownership facts. Public WordPress REST and HTTP reads resolve identifiers and
verify availability; they never mutate the live site.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


CASE_HOST = "exp76.ru"
UPLOAD_PREFIX = "https://exp76.ru/wp-content/uploads/"
USER_AGENT = "Exp76EvidenceAudit/1.0 (+https://exp76.ru/)"
HTTP_TIMEOUT_SECONDS = 20
SERVICE_CANONICALS = {
    "S1": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
    "S2": "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
    "S3": "https://exp76.ru/services/posadka-derevev-i-kustarnikov/",
    "S4": "https://exp76.ru/services/ukhod-za-sadom/",
    "S5": "https://exp76.ru/services/planirovka-territorii/",
    "S6": "https://exp76.ru/services/podpornye-stenki/",
    "S7": "https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/",
    "S8": "https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/",
}
SUPPORTED_PROOF_SERVICES = frozenset({"S1", "S2", "S3"})
SUPPLEMENTAL_PROOF_SERVICES = frozenset({"S9", "S10"})
BASELINE_SELECTED_IMAGE_URLS = frozenset(
    {
        "https://exp76.ru/wp-content/uploads/2015/07/lanshaftnoe-proektirovanie.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki1.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki2.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki3.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki4.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki5.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/gazoni-rulonniy-posevnoy.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/landshaftnoe-osveshenie.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/naruzhnoe-osveshhenie_752.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/osvescheniezdaniya.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/ozelenenie.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii10.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii2.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii6.webp",
        "https://exp76.ru/wp-content/uploads/2018/12/uhod1.webp",
        "https://exp76.ru/wp-content/uploads/2019/02/IMG_20181015_110705_HDR.webp",
        "https://exp76.ru/wp-content/uploads/2019/02/NEwk9KFYTXY.webp",
        "https://exp76.ru/wp-content/uploads/2020/10/20200514_085626.webp",
        "https://exp76.ru/wp-content/uploads/2020/10/Ila-CrwKkL4.webp",
        "https://exp76.ru/wp-content/uploads/2023/12/20230817_084022-1-scaled.webp",
    }
)
EXPECTED_SOURCE_COUNTS = {
    "cases_by_category.json": {"occurrences": 51, "unique_cases": 35},
    "acf_selected_works_map.json": {"occurrences": 50, "unique_cases": 29},
    "seo-content/cases/import/cases-seo-import.json": {
        "occurrences": 35,
        "unique_cases": 35,
    },
    "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json": {
        "occurrences": 6,
        "unique_cases": 5,
    },
}
EXPECTED_PAGE_IDS = {
    "https://exp76.ru/d-rjabukhino/": 10079,
    "https://exp76.ru/d-volkovo/": 10066,
    "https://exp76.ru/derevnja-selekhovo/": 10303,
    "https://exp76.ru/fotogalereja/aksenovo/": 8512,
    "https://exp76.ru/fotogalereja/c-glebovo-rybinskijj-r-on/": 9415,
    "https://exp76.ru/fotogalereja/d-gorokhovo/": 9494,
    "https://exp76.ru/fotogalereja/d-kuzino/": 9520,
    "https://exp76.ru/fotogalereja/d-malye-vysoka/": 9533,
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": 9554,
    "https://exp76.ru/fotogalereja/d-timoshkino/": 9567,
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": 9445,
    "https://exp76.ru/fotogalereja/g-rybinsk/": 9431,
    "https://exp76.ru/fotogalereja/jaroslavskoe-vzmore/": 9716,
    "https://exp76.ru/fotogalereja/kamenniki/": 8604,
    "https://exp76.ru/fotogalereja/miljushino/": 9594,
    "https://exp76.ru/fotogalereja/poselok-dubrava-g-jaroslavl/": 9615,
    "https://exp76.ru/fotogalereja/poselok-iskra-oktjabrja/": 9630,
    "https://exp76.ru/fotogalereja/poselok-svingino/": 9650,
    "https://exp76.ru/fotogalereja/poshekhonskijj-rajjon/": 9673,
    "https://exp76.ru/fotogalereja/rybinsk-marievka/": 9684,
    "https://exp76.ru/fotogalereja/rybinsk-shankhajj/": 8620,
    "https://exp76.ru/fotogalereja/rybinsk-slip/": 9699,
    "https://exp76.ru/fotogalereja/rybinskijj-r-on-d-djagtericy/": 8630,
    "https://exp76.ru/fotogalereja/rybinskijj-r-on-pos-svigino/": 8628,
    "https://exp76.ru/fotogalereja/rybinskijj-r-on-pos-svingino/": 8632,
    "https://exp76.ru/fotogalereja/rybinskijj-rajjon-sudoverf/": 8626,
    "https://exp76.ru/fotogalereja/s-spass/": 8634,
    "https://exp76.ru/fotogalereja/timoshkino/": 8638,
    "https://exp76.ru/kottedzhnyjj-poselok-koprino/": 10322,
    "https://exp76.ru/pos-kamenniki/": 10084,
    "https://exp76.ru/pos-slip/": 10096,
    "https://exp76.ru/poshekhone/": 10107,
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": 10136,
    "https://exp76.ru/rybinsk-ul-veretevskaja/": 10125,
    "https://exp76.ru/slip-ul-bugorok/": 10345,
}
EXPECTED_FEATURED_MEDIA = {
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": 9559,
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": 9467,
    "https://exp76.ru/pos-slip/": 10101,
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": 10141,
    "https://exp76.ru/slip-ul-bugorok/": 10354,
}
EXPECTED_SELECTED_IMAGE_URLS = frozenset(
    {
        "https://exp76.ru/wp-content/uploads/2015/07/lanshaftnoe-proektirovanie.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki1.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki2.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki3.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki4.webp",
        "https://exp76.ru/wp-content/uploads/2015/07/podporki5.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/gazoni-rulonniy-posevnoy.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/landshaftnoe-osveshenie.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/naruzhnoe-osveshhenie_752.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/osvescheniezdaniya.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/ozelenenie.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii10.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii2.webp",
        "https://exp76.ru/wp-content/uploads/2017/01/planirovka_territorii6.webp",
        "https://exp76.ru/wp-content/uploads/2018/12/uhod1.webp",
        "https://exp76.ru/wp-content/uploads/2019/02/IMG_20181015_110705_HDR.webp",
        "https://exp76.ru/wp-content/uploads/2019/02/NEwk9KFYTXY.webp",
        "https://exp76.ru/wp-content/uploads/2020/10/20200514_085626.webp",
        "https://exp76.ru/wp-content/uploads/2020/10/Ila-CrwKkL4.webp",
        "https://exp76.ru/wp-content/uploads/2023/12/20230817_084022-1-scaled.webp",
    }
)
EXPECTED_OWNED_IMAGES = {
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": (
        "https://exp76.ru/wp-content/uploads/2019/02/NEwk9KFYTXY.webp",
    ),
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": (
        "https://exp76.ru/wp-content/uploads/2019/02/IMG_20181015_110705_HDR.webp",
    ),
    "https://exp76.ru/pos-slip/": (
        "https://exp76.ru/wp-content/uploads/2020/10/20200514_085626.webp",
    ),
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": (
        "https://exp76.ru/wp-content/uploads/2020/10/Ila-CrwKkL4.webp",
    ),
    "https://exp76.ru/slip-ul-bugorok/": (
        "https://exp76.ru/wp-content/uploads/2023/12/20230817_084022-1-scaled.webp",
    ),
}
EXPECTED_SERVICE_SUPPORT = {
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": (
        (
            "S2",
            "explicit_work",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "gazon-posevnojj-i-gazon-rulonnyjj.json#proof.cases[1]",
        ),
    ),
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": (
        (
            "S1",
            "hub_proof_only",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "landshaftnoe-proektirovanie.json#proof.cases[2]",
        ),
    ),
    "https://exp76.ru/pos-slip/": (
        (
            "S2",
            "explicit_work",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "gazon-posevnojj-i-gazon-rulonnyjj.json#proof.cases[0]",
        ),
        (
            "S3",
            "explicit_work",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "posadka-derevev-i-kustarnikov.json#proof.cases[0]",
        ),
    ),
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": (
        (
            "S1",
            "hub_proof_only",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "landshaftnoe-proektirovanie.json#proof.cases[1]",
        ),
    ),
    "https://exp76.ru/slip-ul-bugorok/": (
        (
            "S1",
            "hub_proof_only",
            "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "landshaftnoe-proektirovanie.json#proof.cases[0]",
        ),
    ),
}
MANAGED_CASE_SEO_FIELDS = frozenset(
    {
        "cs87_hero_title",
        "cs87_location",
        "cs87_work_type",
        "cs87_related_case_urls",
        "cs87_seo_title",
        "cs87_seo_description",
        "cs87_case_keywords",
        "cs87_service_url",
    }
)


class CatalogError(ValueError):
    """Raised when evidence cannot be resolved without guessing."""


class _RejectRedirects(HTTPRedirectHandler):
    """Reject redirects before urllib can contact an unaudited destination."""

    def redirect_request(
        self,
        request: Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> None:
        del file_pointer
        raise HTTPError(
            request.full_url,
            code,
            f"redirect blocked before contacting {new_url}: {message}",
            headers,
            None,
        )


_NO_REDIRECT_OPENER = build_opener(_RejectRedirects())


def _open_url(request: Request, *, timeout: int) -> Any:
    return _NO_REDIRECT_OPENER.open(request, timeout=timeout)


@dataclass(frozen=True)
class FactSource:
    """One literal fact and the JSON location that states it."""

    value: str
    source_ref: str


@dataclass(frozen=True)
class ServiceSupport:
    """One S1-S8 mapping and the exact proof record that permits it."""

    service_id: str
    basis: str
    source_ref: str


@dataclass(frozen=True)
class ImageAudit:
    """Read-only HTTP evidence for one selected image URL."""

    url: str
    http_status: int
    content_type: str
    checked_date: str
    method: str
    final_url: str = ""
    error: str = ""

    @property
    def is_valid(self) -> bool:
        return (
            200 <= self.http_status < 300
            and self.content_type.startswith("image/")
            and self.final_url == self.url
        )


@dataclass(frozen=True)
class PageAudit:
    """Public REST/HTTP evidence tying a canonical case URL to a page ID."""

    page_id: int
    canonical_url: str
    post_status: str
    http_status: int
    content_type: str
    checked_date: str
    rest_url: str
    method: str = "HEAD"
    final_url: str = ""
    post_type: str = "page"
    featured_media_id: int = 0

    @property
    def is_valid(self) -> bool:
        return (
            self.page_id > 0
            and self.post_type == "page"
            and self.post_status == "publish"
            and 200 <= self.http_status < 300
            and self.content_type.startswith("text/html")
            and self.final_url == self.canonical_url
        )


@dataclass(frozen=True)
class CaseEvidence:
    """Normalized evidence for one canonical, already existing case page."""

    page_id: int
    url: str
    title: str
    location: str
    work_types: tuple[str, ...]
    service_ids: tuple[str, ...]
    image_urls: tuple[str, ...]
    source_files: tuple[str, ...]
    seo_ready: bool
    source_refs: tuple[str, ...] = ()
    location_sources: tuple[str, ...] = ()
    work_type_sources: tuple[FactSource, ...] = ()
    service_support: tuple[ServiceSupport, ...] = ()
    image_sources: tuple[FactSource, ...] = ()
    page_audit: PageAudit | None = None
    image_audits: tuple[ImageAudit, ...] = ()
    blocking_gaps: tuple[str, ...] = ()


@dataclass
class _CaseAccumulator:
    url: str
    title: str = ""
    location: str = ""
    work_types: list[str] = field(default_factory=list)
    source_files: set[str] = field(default_factory=set)
    source_refs: set[str] = field(default_factory=set)
    location_sources: set[str] = field(default_factory=set)
    work_type_sources: list[FactSource] = field(default_factory=list)
    service_support: list[ServiceSupport] = field(default_factory=list)
    image_sources: list[FactSource] = field(default_factory=list)
    proof_page_ids: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class _BuildResult:
    cases: tuple[CaseEvidence, ...]
    selected_image_audits: tuple[ImageAudit, ...]
    selected_image_sources: Mapping[str, tuple[str, ...]]
    source_occurrences: int
    source_counts: Mapping[str, Mapping[str, int]]


PageResolver = Callable[[str, str], PageAudit]
ImageAuditor = Callable[[str, str], ImageAudit]


def canonicalize_case_url(value: str) -> str:
    """Return the single internal HTTPS canonical used for case dedupe."""
    raw = str(value or "").strip()
    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"}:
        raise CatalogError(f"case URL must use HTTP(S): {raw}")
    if parts.username or parts.password or parts.port:
        raise CatalogError(f"case URL contains forbidden authority data: {raw}")
    host = (parts.hostname or "").lower()
    if host == f"www.{CASE_HOST}":
        host = CASE_HOST
    if host != CASE_HOST:
        raise CatalogError(f"case URL must belong to {CASE_HOST}: {raw}")
    path = re.sub(r"/{2,}", "/", unquote(parts.path or "/"))
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/":
        path = f"{path.rstrip('/')}/"
    return urlunsplit(("https", CASE_HOST, path, "", ""))


def _canonical_upload_url(value: str) -> str:
    raw = str(value or "").strip()
    parts = urlsplit(raw)
    if (
        parts.scheme != "https"
        or (parts.hostname or "").lower() != CASE_HOST
        or parts.username
        or parts.password
        or parts.port
        or parts.query
        or parts.fragment
        or not parts.path.startswith("/wp-content/uploads/")
    ):
        raise CatalogError(f"selected image is not an internal upload: {raw}")
    return urlunsplit(("https", CASE_HOST, unquote(parts.path), "", ""))


def _transport_url(value: str) -> str:
    parts = urlsplit(value)
    encoded_path = quote(parts.path, safe="/%:@-._~")
    return urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, ""))


def _public_page_rest_url(canonical: str) -> str:
    slug = canonical.rstrip("/").rsplit("/", 1)[-1]
    query = urlencode(
        {
            "slug": slug,
            "per_page": 100,
            "_fields": "id,link,status,type,featured_media",
        }
    )
    return f"https://exp76.ru/wp-json/wp/v2/pages?{query}"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read JSON {path}: {exc}") from exc


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _request(url: str, method: str, *, byte_range: bool = False) -> Request:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if byte_range:
        headers["Range"] = "bytes=0-0"
    return Request(_transport_url(url), method=method, headers=headers)


def _response_status(response: Any) -> int:
    return int(getattr(response, "status", response.getcode()))


def _response_content_type(response: Any) -> str:
    header = str(response.headers.get("Content-Type", ""))
    return header.split(";", 1)[0].strip().lower()


def _probe_headers(url: str, *, require_prefix: str) -> tuple[int, str, str, str, str]:
    """Probe headers with HEAD, then a one-byte GET request when HEAD is unusable."""
    head_error = ""
    try:
        with _open_url(_request(url, "HEAD"), timeout=HTTP_TIMEOUT_SECONDS) as response:
            status = _response_status(response)
            content_type = _response_content_type(response)
            final_url = str(response.geturl() or url)
            if 200 <= status < 300 and content_type.startswith(require_prefix):
                return status, content_type, "HEAD", "", final_url
            head_error = f"HEAD returned {status} {content_type or 'without content type'}"
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        head_error = f"HEAD failed: {exc}"

    try:
        with _open_url(
            _request(url, "GET", byte_range=True),
            timeout=HTTP_TIMEOUT_SECONDS,
        ) as response:
            return (
                _response_status(response),
                _response_content_type(response),
                "GET_RANGE",
                head_error,
                str(response.geturl() or url),
            )
    except HTTPError as exc:
        content_type = str(exc.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
        return (
            int(exc.code),
            content_type,
            "GET_RANGE",
            f"{head_error}; GET failed: {exc}",
            str(exc.geturl() or url),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return 0, "", "GET_RANGE", f"{head_error}; GET failed: {exc}", url


def audit_image_url(url: str, checked_date: str) -> ImageAudit:
    """Verify one internal upload without reading or replacing its body."""
    canonical = _canonical_upload_url(url)
    status, content_type, method, error, final_url = _probe_headers(
        canonical,
        require_prefix="image/",
    )
    try:
        final_canonical = _canonical_upload_url(final_url)
    except CatalogError:
        final_canonical = final_url
    return ImageAudit(
        url=canonical,
        http_status=status,
        content_type=content_type,
        checked_date=checked_date,
        method=method,
        final_url=final_canonical,
        error=error,
    )


def resolve_public_page(url: str, checked_date: str) -> PageAudit:
    """Resolve one published page by slug and exact public canonical URL."""
    canonical = canonicalize_case_url(url)
    rest_url = _public_page_rest_url(canonical)
    try:
        with _open_url(_request(rest_url, "GET"), timeout=HTTP_TIMEOUT_SECONDS) as response:
            final_rest_url = str(response.geturl() or rest_url)
            if final_rest_url != rest_url:
                raise CatalogError(
                    f"public page REST endpoint redirected from {rest_url} to {final_rest_url}"
                )
            if _response_status(response) != 200 or not _response_content_type(
                response
            ).startswith("application/json"):
                raise CatalogError(f"invalid public page REST response for {canonical}")
            raw = response.read(1_000_001)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise CatalogError(f"cannot resolve public page {canonical}: {exc}") from exc
    if len(raw) > 1_000_000:
        raise CatalogError(f"public page response is unexpectedly large for {canonical}")
    try:
        rows = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"invalid public page response for {canonical}: {exc}") from exc
    if not isinstance(rows, list):
        raise CatalogError(f"public page response is not a list for {canonical}")

    for row in rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("id"), int)
            or isinstance(row.get("id"), bool)
            or int(row.get("id", 0)) <= 0
            or not isinstance(row.get("link"), str)
            or not isinstance(row.get("status"), str)
            or not isinstance(row.get("type"), str)
            or not isinstance(row.get("featured_media"), int)
            or isinstance(row.get("featured_media"), bool)
            or int(row.get("featured_media", -1)) < 0
        ):
            raise CatalogError(f"invalid public page record for {canonical}: {row!r}")

    exact = [row for row in rows if row.get("link") == canonical]
    if len(exact) != 1:
        raise CatalogError(f"public page {canonical} resolved to {len(exact)} exact records")
    row = exact[0]
    if row.get("type") != "page" or row.get("status") != "publish":
        raise CatalogError(f"public page {canonical} is not a published page")

    status, content_type, method, error, final_url = _probe_headers(
        canonical,
        require_prefix="text/html",
    )
    if error and not (200 <= status < 300 and content_type.startswith("text/html")):
        raise CatalogError(f"public page HTTP check failed for {canonical}: {error}")
    if final_url != canonical:
        raise CatalogError(f"public page {canonical} redirected away to {final_url}")
    return PageAudit(
        page_id=row["id"],
        canonical_url=canonical,
        post_status=str(row.get("status", "")),
        http_status=status,
        content_type=content_type,
        checked_date=checked_date,
        rest_url=rest_url,
        method=method,
        final_url=final_url,
        post_type=row["type"],
        featured_media_id=row["featured_media"],
    )


def _iter_upload_urls(value: Any, pointer: str = "") -> Sequence[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_pointer = f"{pointer}.{key}" if pointer else str(key)
            if key == "url" and isinstance(child, str) and child.startswith(UPLOAD_PREFIX):
                rows.append((_canonical_upload_url(child), child_pointer))
            else:
                rows.extend(_iter_upload_urls(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_iter_upload_urls(child, f"{pointer}[{index}]"))
    return rows


def _get_accumulator(cases: dict[str, _CaseAccumulator], url: str) -> _CaseAccumulator:
    canonical = canonicalize_case_url(url)
    if canonical not in cases:
        cases[canonical] = _CaseAccumulator(url=canonical)
    return cases[canonical]


def _add_work_fact(acc: _CaseAccumulator, value: str, source_ref: str) -> None:
    fact = str(value or "").strip()
    if not fact:
        return
    if fact not in acc.work_types:
        acc.work_types.append(fact)
    candidate = FactSource(value=fact, source_ref=source_ref)
    if candidate not in acc.work_type_sources:
        acc.work_type_sources.append(candidate)


def _load_local_evidence(root: Path) -> tuple[
    dict[str, _CaseAccumulator],
    int,
    dict[str, set[str]],
    dict[str, dict[str, int]],
]:
    cases: dict[str, _CaseAccumulator] = {}
    occurrences = 0
    selected_image_sources: dict[str, set[str]] = {}
    source_occurrences: Counter[str] = Counter()
    source_case_urls = {source: set() for source in EXPECTED_SOURCE_COUNTS}

    def record_occurrence(source: str, canonical: str) -> None:
        source_occurrences[source] += 1
        source_case_urls[source].add(canonical)

    fact_path = root / "cases_by_category.json"
    fact_data = _read_json(fact_path)
    if not isinstance(fact_data, Mapping):
        raise CatalogError("cases_by_category.json must be an object")
    fact_file = _relative_path(root, fact_path)
    for category, records in fact_data.items():
        if not isinstance(records, list):
            raise CatalogError(f"cases_by_category.json#{category} must be a list")
        for index, record in enumerate(records):
            occurrences += 1
            acc = _get_accumulator(cases, record.get("url", ""))
            record_occurrence("cases_by_category.json", acc.url)
            base_ref = f"{fact_file}#{category}[{index}]"
            title = str(record.get("title", "")).strip()
            if title and not acc.title:
                acc.title = title
                acc.location = title
            if title and acc.location == title:
                acc.location_sources.add(f"{base_ref}.title")
            elif title and title != acc.location:
                raise CatalogError(f"conflicting locations for {acc.url}: {acc.location!r} vs {title!r}")
            _add_work_fact(acc, str(record.get("description", "")), f"{base_ref}.description")
            acc.source_files.add(fact_file)
            acc.source_refs.add(base_ref)

    import_path = root / "seo-content" / "cases" / "import" / "cases-seo-import.json"
    import_data = _read_json(import_path)
    import_file = _relative_path(root, import_path)
    records = import_data.get("cases", []) if isinstance(import_data, Mapping) else []
    if not isinstance(records, list):
        raise CatalogError("cases-seo-import.json#cases must be a list")
    for index, record in enumerate(records):
        occurrences += 1
        acc = _get_accumulator(cases, record.get("url", ""))
        record_occurrence("seo-content/cases/import/cases-seo-import.json", acc.url)
        acc.source_files.add(import_file)
        acc.source_refs.add(f"{import_file}#cases[{index}]")

    acf_path = root / "acf_selected_works_map.json"
    acf_data = _read_json(acf_path)
    if not isinstance(acf_data, Mapping):
        raise CatalogError("acf_selected_works_map.json must be an object")
    acf_file = _relative_path(root, acf_path)
    for category, category_data in acf_data.items():
        records = category_data.get("cases", []) if isinstance(category_data, Mapping) else []
        if not isinstance(records, list):
            raise CatalogError(f"acf_selected_works_map.json#{category}.cases must be a list")
        for index, record in enumerate(records):
            occurrences += 1
            acc = _get_accumulator(cases, record.get("url", ""))
            record_occurrence("acf_selected_works_map.json", acc.url)
            acc.source_files.add(acf_file)
            acc.source_refs.add(f"{acf_file}#{category}.cases[{index}]")

    v2_dir = root / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp" / "content" / "service-v2"
    for path in sorted(v2_dir.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, Mapping):
            raise CatalogError(f"{path} must contain an object")
        source_file = _relative_path(root, path)
        service_id = str(payload.get("service_id", ""))
        for image_url, pointer in _iter_upload_urls(payload):
            if image_url in BASELINE_SELECTED_IMAGE_URLS:
                selected_image_sources.setdefault(image_url, set()).add(
                    f"{source_file}#{pointer}"
                )

        proof = payload.get("proof", {})
        proof_cases = proof.get("cases", []) if isinstance(proof, Mapping) else []
        if not isinstance(proof_cases, list):
            raise CatalogError(f"{source_file}#proof.cases must be a list")
        if proof_cases and service_id in SUPPLEMENTAL_PROOF_SERVICES:
            # S9/S10 are independently audited and merged by contracts.py from
            # hub-evidence-supplement.json. Keep this frozen S1-S8 catalog stable.
            continue
        if proof_cases and service_id not in SUPPORTED_PROOF_SERVICES:
            raise CatalogError(f"unsupported {service_id} proof cases appeared in {source_file}")
        for index, record in enumerate(proof_cases):
            occurrences += 1
            acc = _get_accumulator(cases, record.get("url", ""))
            record_occurrence(
                "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json",
                acc.url,
            )
            base_ref = f"{source_file}#proof.cases[{index}]"
            page_id = int(record.get("page_id", 0) or 0)
            if page_id <= 0:
                raise CatalogError(f"{base_ref} has no positive page_id")
            acc.proof_page_ids.add(page_id)
            basis = "hub_proof_only" if service_id == "S1" else "explicit_work"
            support = ServiceSupport(service_id=service_id, basis=basis, source_ref=base_ref)
            if support not in acc.service_support:
                acc.service_support.append(support)
            image = record.get("image", {})
            image_url = _canonical_upload_url(image.get("url", "")) if isinstance(image, Mapping) else ""
            if not image_url:
                raise CatalogError(f"{base_ref} has no owned image URL")
            image_source = FactSource(value=image_url, source_ref=f"{base_ref}.image.url")
            if image_source not in acc.image_sources:
                acc.image_sources.append(image_source)
            acc.source_files.add(source_file)
            acc.source_refs.add(base_ref)

    source_counts = {
        source: {
            "occurrences": int(source_occurrences[source]),
            "unique_cases": len(source_case_urls[source]),
        }
        for source in EXPECTED_SOURCE_COUNTS
    }
    return cases, occurrences, selected_image_sources, source_counts


def _valid_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise CatalogError(f"checked date must be ISO YYYY-MM-DD: {value}") from exc


def _build(
    root: Path,
    *,
    page_resolver: PageResolver | None,
    image_auditor: ImageAuditor | None,
    checked_date: str | None,
) -> _BuildResult:
    root = root.resolve()
    checked = _valid_date(checked_date or date.today().isoformat())
    resolve_page = page_resolver or resolve_public_page
    audit_image = image_auditor or audit_image_url
    accumulators, occurrences, selected_image_sources, source_counts = _load_local_evidence(root)

    selected_audits: dict[str, ImageAudit] = {}
    for image_url in sorted(selected_image_sources):
        audit = audit_image(image_url, checked)
        if audit.url != image_url:
            raise CatalogError(f"image auditor changed canonical URL {image_url} to {audit.url}")
        selected_audits[image_url] = audit

    cases: list[CaseEvidence] = []
    for canonical in sorted(accumulators):
        acc = accumulators[canonical]
        if not acc.title or not acc.location or not acc.work_types:
            raise CatalogError(f"case lacks primary location/work facts: {canonical}")
        page_audit = resolve_page(canonical, checked)
        if page_audit.canonical_url != canonical:
            raise CatalogError(f"page resolver changed canonical URL {canonical}")
        if acc.proof_page_ids and page_audit.page_id not in acc.proof_page_ids:
            raise CatalogError(
                f"public page ID {page_audit.page_id} disagrees with local proof IDs "
                f"{sorted(acc.proof_page_ids)} for {canonical}"
            )

        support = tuple(sorted(acc.service_support, key=lambda item: item.service_id))
        service_ids = tuple(item.service_id for item in support)
        image_sources = tuple(sorted(acc.image_sources, key=lambda item: (item.value, item.source_ref)))
        image_urls = tuple(dict.fromkeys(item.value for item in image_sources))
        image_audits = tuple(selected_audits[url] for url in image_urls)
        gaps: list[str] = []
        if not service_ids:
            gaps.append("no S1-S8 support in service-v2 proof")
        if not image_urls:
            gaps.append("no case-owned selected image in service-v2 proof")
        if not page_audit.is_valid:
            gaps.append("public page ID/status/HTTP evidence is invalid")
        if any(not audit.is_valid for audit in image_audits):
            gaps.append("case-owned selected image failed HTTP validation")

        cases.append(
            CaseEvidence(
                page_id=page_audit.page_id,
                url=canonical,
                title=acc.title,
                location=acc.location,
                work_types=tuple(acc.work_types),
                service_ids=service_ids,
                image_urls=image_urls,
                source_files=tuple(sorted(acc.source_files)),
                seo_ready=not gaps,
                source_refs=tuple(sorted(acc.source_refs)),
                location_sources=tuple(sorted(acc.location_sources)),
                work_type_sources=tuple(acc.work_type_sources),
                service_support=support,
                image_sources=image_sources,
                page_audit=page_audit,
                image_audits=image_audits,
                blocking_gaps=tuple(gaps),
            )
        )

    normalized_sources = {
        url: tuple(sorted(refs)) for url, refs in sorted(selected_image_sources.items())
    }
    return _BuildResult(
        cases=tuple(cases),
        selected_image_audits=tuple(selected_audits[url] for url in sorted(selected_audits)),
        selected_image_sources=normalized_sources,
        source_occurrences=occurrences,
        source_counts=source_counts,
    )


def build_case_catalog(
    root: Path,
    *,
    page_resolver: PageResolver | None = None,
    image_auditor: ImageAuditor | None = None,
    checked_date: str | None = None,
) -> tuple[CaseEvidence, ...]:
    """Build the canonical case tuple from local facts plus public read-only checks."""
    return _build(
        root,
        page_resolver=page_resolver,
        image_auditor=image_auditor,
        checked_date=checked_date,
    ).cases


def _counts(values: Sequence[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _json_compatible(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


def build_catalog_document(
    root: Path,
    *,
    page_resolver: PageResolver | None = None,
    image_auditor: ImageAuditor | None = None,
    checked_date: str | None = None,
) -> dict[str, Any]:
    """Build the complete serializable catalog and its audit summary."""
    built = _build(
        root,
        page_resolver=page_resolver,
        image_auditor=image_auditor,
        checked_date=checked_date,
    )
    catalog_cases = len(built.cases)
    ready_cases = sum(case.seo_ready for case in built.cases)
    support_counts = Counter(
        service_id for case in built.cases for service_id in case.service_ids
    )
    image_statuses = _counts([audit.http_status for audit in built.selected_image_audits])
    image_content_types = _counts([audit.content_type for audit in built.selected_image_audits])
    selected_images = []
    for audit in built.selected_image_audits:
        row = asdict(audit)
        row["source_refs"] = list(built.selected_image_sources[audit.url])
        selected_images.append(row)

    return {
        "schema_version": 1,
        "checked_date": built.cases[0].page_audit.checked_date if built.cases else (checked_date or ""),
        "sources": [
            {"path": "cases_by_category.json", "role": "primary_location_and_work_facts"},
            {"path": "acf_selected_works_map.json", "role": "relationship_corroboration_only"},
            {
                "path": "seo-content/cases/import/cases-seo-import.json",
                "role": "existing_import_state_not_fact_authority",
            },
            {
                "path": "ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json",
                "role": "S1-S3_case_mapping_and_selected_image_authority",
            },
            {
                "url": "https://exp76.ru/wp-json/wp/v2/pages",
                "role": "public_page_id_and_publish_status",
            },
        ],
        "summary": {
            "source_occurrences": built.source_occurrences,
            "source_counts": built.source_counts,
            "canonical_merges": built.source_occurrences - catalog_cases,
            "catalog_cases": catalog_cases,
            "resolved_page_ids": sum(case.page_id > 0 for case in built.cases),
            "service_support_mappings": sum(len(case.service_ids) for case in built.cases),
            "support_by_service": {
                service_id: int(support_counts.get(service_id, 0)) for service_id in SERVICE_CANONICALS
            },
            "services_without_supported_cases": [
                service_id for service_id in SERVICE_CANONICALS if not support_counts.get(service_id)
            ],
            "unmapped_cases": sum(not case.service_ids for case in built.cases),
            "selected_image_urls": len(built.selected_image_audits),
            "selected_image_statuses": image_statuses,
            "selected_image_content_types": image_content_types,
            "case_owned_image_urls": sum(len(case.image_urls) for case in built.cases),
            "seo_ready_cases": ready_cases,
            "blocked_cases": catalog_cases - ready_cases,
        },
        "selected_image_audits": selected_images,
        "cases": [_json_compatible(asdict(case)) for case in built.cases],
    }


def _is_valid_image_audit(row: Mapping[str, Any]) -> bool:
    return (
        isinstance(row.get("http_status"), int)
        and 200 <= int(row["http_status"]) < 300
        and str(row.get("content_type", "")).startswith("image/")
        and bool(row.get("checked_date"))
        and row.get("final_url") == row.get("url")
    )


def validate_catalog_document(document: Mapping[str, Any]) -> list[str]:
    """Validate a checked-in catalog without repeating network requests."""
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    cases = document.get("cases", [])
    if not isinstance(cases, list):
        return errors + ["cases must be a list"]
    if len(cases) != 35:
        errors.append(f"catalog must contain 35 cases, found {len(cases)}")

    urls: set[str] = set()
    page_ids: set[int] = set()
    page_id_map: dict[str, int] = {}
    ready_cases = 0
    support_counts: Counter[str] = Counter()
    owned_image_urls: list[str] = []
    owned_images_by_case: dict[str, tuple[str, ...]] = {}
    support_by_case: dict[str, tuple[tuple[str, str, str], ...]] = {}
    nested_image_audits: list[tuple[str, Mapping[str, Any]]] = []
    for row in cases:
        if not isinstance(row, Mapping):
            errors.append("catalog case must be an object")
            continue
        try:
            canonical = canonicalize_case_url(str(row.get("url", "")))
        except CatalogError as exc:
            errors.append(str(exc))
            continue
        if canonical != row.get("url"):
            errors.append(f"case URL is not canonical: {row.get('url', '')}")
        if canonical in urls:
            errors.append(f"duplicate canonical case URL: {canonical}")
        urls.add(canonical)
        page_id = row.get("page_id")
        if not isinstance(page_id, int) or page_id <= 0:
            errors.append(f"case has invalid page_id: {canonical}")
        elif page_id in page_ids:
            errors.append(f"duplicate page_id {page_id}")
        else:
            page_ids.add(page_id)
            page_id_map[canonical] = page_id
        expected_page_id = EXPECTED_PAGE_IDS.get(canonical)
        if page_id != expected_page_id:
            errors.append(
                f"case {canonical} expected page_id {expected_page_id}, found {page_id!r}"
            )
        if not row.get("location") or not row.get("work_types"):
            errors.append(f"case lacks location/work facts: {canonical}")
        if not row.get("source_files") or not row.get("source_refs"):
            errors.append(f"case lacks source provenance: {canonical}")
        location_sources = row.get("location_sources") or []
        work_type_sources = row.get("work_type_sources") or []
        if not location_sources or not work_type_sources:
            errors.append(f"case lacks location/work provenance: {canonical}")
        elif not all(
            str(ref).startswith("cases_by_category.json#") for ref in location_sources
        ) or not all(
            isinstance(item, Mapping)
            and str(item.get("source_ref", "")).startswith("cases_by_category.json#")
            for item in work_type_sources
        ):
            errors.append(f"case uses non-primary location/work provenance: {canonical}")
        page = row.get("page_audit") or {}
        if (
            not isinstance(page, Mapping)
            or page.get("page_id") != page_id
            or page.get("canonical_url") != canonical
            or page.get("final_url") != canonical
            or page.get("post_type") != "page"
            or page.get("post_status") != "publish"
            or not isinstance(page.get("http_status"), int)
            or isinstance(page.get("http_status"), bool)
            or not 200 <= int(page.get("http_status", 0)) < 300
            or not str(page.get("content_type", "")).startswith("text/html")
            or not page.get("checked_date")
            or page.get("rest_url") != _public_page_rest_url(canonical)
        ):
            errors.append(f"case has invalid public page audit: {canonical}")
        expected_media_id = EXPECTED_FEATURED_MEDIA.get(canonical)
        if expected_media_id is not None and page.get("featured_media_id") != expected_media_id:
            errors.append(
                f"case {canonical} expected featured_media_id {expected_media_id}, "
                f"found {page.get('featured_media_id')!r}"
            )
        service_ids = tuple(row.get("service_ids") or ())
        if any(service_id not in SUPPORTED_PROOF_SERVICES for service_id in service_ids):
            errors.append(f"case has unsupported S4-S8 mapping: {canonical}")
        support_rows = row.get("service_support") or []
        details: list[tuple[str, str, str]] = []
        if not isinstance(support_rows, (list, tuple)):
            errors.append(f"case has invalid service support: {canonical}")
        else:
            for support in support_rows:
                if not isinstance(support, Mapping):
                    errors.append(f"case has invalid service support: {canonical}")
                    continue
                detail = (
                    str(support.get("service_id", "")),
                    str(support.get("basis", "")),
                    str(support.get("source_ref", "")),
                )
                details.append(detail)
                if detail[2] not in (row.get("source_refs") or []):
                    errors.append(f"case support lacks matching source provenance: {canonical}")
        if tuple(item[0] for item in details) != service_ids:
            errors.append(f"case service IDs disagree with support records: {canonical}")
        if details:
            support_by_case[canonical] = tuple(details)
        support_counts.update(service_ids)
        if row.get("seo_ready"):
            ready_cases += 1
            if not service_ids or not row.get("image_urls") or row.get("blocking_gaps"):
                errors.append(f"seo_ready case lacks complete support: {canonical}")
        elif not row.get("blocking_gaps"):
            errors.append(f"blocked case does not name its evidence gap: {canonical}")
        case_image_urls = tuple(row.get("image_urls") or ())
        if case_image_urls:
            owned_images_by_case[canonical] = case_image_urls
        owned_image_urls.extend(case_image_urls)
        case_audits = row.get("image_audits") or []
        if not isinstance(case_audits, (list, tuple)):
            errors.append(f"case image audits must be a list: {canonical}")
        else:
            for audit in case_audits:
                if isinstance(audit, Mapping):
                    nested_image_audits.append((canonical, audit))
                else:
                    errors.append(f"case has invalid image audit: {canonical}")

    if page_id_map != EXPECTED_PAGE_IDS:
        errors.append("catalog URL map does not match expected page_id evidence")
    if support_by_case != EXPECTED_SERVICE_SUPPORT:
        errors.append("catalog does not match exact service support evidence")
    if owned_images_by_case != EXPECTED_OWNED_IMAGES:
        errors.append("catalog does not match exact case-owned images")

    selected = document.get("selected_image_audits", [])
    if not isinstance(selected, list):
        errors.append("selected_image_audits must be a list")
        selected = []
    expected_selected_count = len(EXPECTED_SELECTED_IMAGE_URLS)
    if len(selected) != expected_selected_count:
        errors.append(
            "selected_image_audits must contain "
            f"{expected_selected_count} URLs, found {len(selected)}"
        )
    selected_urls: set[str] = set()
    selected_by_url: dict[str, Mapping[str, Any]] = {}
    for row in selected:
        if not isinstance(row, Mapping):
            errors.append("selected image audit must be an object")
            continue
        raw_url = str(row.get("url", ""))
        try:
            canonical = _canonical_upload_url(raw_url)
        except CatalogError as exc:
            errors.append(str(exc))
            continue
        if canonical != raw_url:
            errors.append(f"selected image URL is not canonical: {raw_url}")
        if canonical in selected_urls:
            errors.append(f"duplicate selected image URL: {canonical}")
        selected_urls.add(canonical)
        selected_by_url[canonical] = row
        if not _is_valid_image_audit(row):
            errors.append(f"selected image failed HTTP/content validation: {canonical}")
        if not row.get("source_refs"):
            errors.append(f"selected image lacks source provenance: {canonical}")
    if selected_urls != EXPECTED_SELECTED_IMAGE_URLS:
        errors.append("selected image audits do not match the exact service-v2 URL set")
    for image_url in owned_image_urls:
        if image_url not in selected_urls:
            errors.append(f"case-owned image is absent from selected audit: {image_url}")
    for canonical, nested in nested_image_audits:
        image_url = str(nested.get("url", ""))
        global_audit = selected_by_url.get(image_url)
        if global_audit is None:
            continue
        expected_nested = {
            key: value for key, value in global_audit.items() if key != "source_refs"
        }
        if dict(nested) != expected_nested:
            errors.append(
                f"case-owned image audit differs from global selected audit: "
                f"{canonical} {image_url}"
            )

    summary = document.get("summary", {})
    expected_summary = {
        "source_occurrences": 142,
        "canonical_merges": 107,
        "catalog_cases": len(cases),
        "resolved_page_ids": len(page_ids),
        "service_support_mappings": sum(support_counts.values()),
        "unmapped_cases": sum(not (row.get("service_ids") or []) for row in cases),
        "selected_image_urls": len(selected),
        "case_owned_image_urls": len(owned_image_urls),
        "seo_ready_cases": ready_cases,
        "blocked_cases": len(cases) - ready_cases,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            errors.append(f"summary {key} must be {expected}, found {summary.get(key)!r}")
    expected_support = {service_id: int(support_counts.get(service_id, 0)) for service_id in SERVICE_CANONICALS}
    if summary.get("support_by_service") != expected_support:
        errors.append("summary support_by_service does not match case mappings")
    if summary.get("source_counts") != EXPECTED_SOURCE_COUNTS:
        errors.append("summary source_counts does not match exact local-source counts")
    expected_empty_services = [
        service_id for service_id in SERVICE_CANONICALS if not support_counts.get(service_id)
    ]
    if summary.get("services_without_supported_cases") != expected_empty_services:
        errors.append("summary services_without_supported_cases does not match case mappings")
    expected_image_statuses = _counts(
        [row.get("http_status") for row in selected if isinstance(row, Mapping)]
    )
    if summary.get("selected_image_statuses") != expected_image_statuses:
        errors.append("summary selected_image_statuses does not match selected audits")
    expected_image_content_types = _counts(
        [row.get("content_type") for row in selected if isinstance(row, Mapping)]
    )
    if summary.get("selected_image_content_types") != expected_image_content_types:
        errors.append("summary selected_image_content_types does not match selected audits")
    return errors


def validate_case_reference(
    case_id: int,
    image_url: str,
    catalog: Sequence[CaseEvidence],
) -> list[str]:
    """Validate that an existing case owns a verified selected image."""
    matches = [item for item in catalog if item.page_id == case_id]
    if not matches:
        return [f"unknown case {case_id}"]
    if len(matches) > 1:
        return [f"case {case_id} appears {len(matches)} times"]
    case = matches[0]
    try:
        canonical_image = _canonical_upload_url(image_url)
    except CatalogError as exc:
        return [str(exc)]
    errors: list[str] = []
    if canonical_image not in case.image_urls:
        errors.append(f"image {canonical_image} is not owned by case {case_id}")
        return errors
    audit = next((item for item in case.image_audits if item.url == canonical_image), None)
    if audit is None or not audit.is_valid:
        errors.append(f"image {canonical_image} is not verified for case {case_id}")
    if not case.seo_ready:
        errors.append(f"case {case_id} is blocked: {', '.join(case.blocking_gaps)}")
    return errors


def catalog_from_document(document: Mapping[str, Any]) -> tuple[CaseEvidence, ...]:
    """Restore immutable case records from an already validated JSON document."""
    rows = document.get("cases")
    if not isinstance(rows, list):
        raise CatalogError("catalog document cases must be a list")
    catalog: list[CaseEvidence] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise CatalogError("catalog case must be an object")
        page_row = row.get("page_audit")
        page_audit = PageAudit(**page_row) if isinstance(page_row, Mapping) else None
        catalog.append(
            CaseEvidence(
                page_id=int(row.get("page_id", 0)),
                url=str(row.get("url", "")),
                title=str(row.get("title", "")),
                location=str(row.get("location", "")),
                work_types=tuple(row.get("work_types") or ()),
                service_ids=tuple(row.get("service_ids") or ()),
                image_urls=tuple(row.get("image_urls") or ()),
                source_files=tuple(row.get("source_files") or ()),
                seo_ready=bool(row.get("seo_ready")),
                source_refs=tuple(row.get("source_refs") or ()),
                location_sources=tuple(row.get("location_sources") or ()),
                work_type_sources=tuple(
                    FactSource(**item) for item in (row.get("work_type_sources") or ())
                ),
                service_support=tuple(
                    ServiceSupport(**item) for item in (row.get("service_support") or ())
                ),
                image_sources=tuple(
                    FactSource(**item) for item in (row.get("image_sources") or ())
                ),
                page_audit=page_audit,
                image_audits=tuple(
                    ImageAudit(**item) for item in (row.get("image_audits") or ())
                ),
                blocking_gaps=tuple(row.get("blocking_gaps") or ()),
            )
        )
    return tuple(catalog)


def _display_work_type(value: str) -> str:
    value = str(value or "").strip()
    return value[:1].upper() + value[1:] if value else value


def _work_tokens(case: CaseEvidence) -> set[str]:
    text = " ".join(case.work_types).lower().replace("ё", "е")
    tokens = set(re.findall(r"[0-9a-zа-я]+", text))
    return tokens - {"и", "на", "по", "в", "с", "участка", "участке", "комплекс"}


def _related_case_urls(case: CaseEvidence, catalog: Sequence[CaseEvidence]) -> list[str]:
    related: list[str] = []
    service_ids = set(case.service_ids)
    work_tokens = _work_tokens(case)
    location_tokens = set(re.findall(r"[0-9a-zа-я]+", case.location.lower().replace("ё", "е")))
    for candidate in catalog:
        if candidate.url == case.url or not candidate.seo_ready:
            continue
        same_service = bool(service_ids.intersection(candidate.service_ids))
        same_work = bool(work_tokens.intersection(_work_tokens(candidate)))
        candidate_location = set(
            re.findall(r"[0-9a-zа-я]+", candidate.location.lower().replace("ё", "е"))
        )
        same_location = bool(location_tokens.intersection(candidate_location) - {"г", "д", "пос", "ул", "р", "он"})
        if same_service and (same_work or same_location):
            related.append(candidate.url)
    return sorted(related)


def _case_seo_fields(case: CaseEvidence, catalog: Sequence[CaseEvidence]) -> dict[str, Any]:
    if not case.seo_ready or not case.service_ids:
        return {}
    work_type = _display_work_type(case.work_types[0])
    service_id = next(
        service_id for service_id in ("S1", "S2", "S3") if service_id in case.service_ids
    )
    description = "; ".join(case.work_types)
    return {
        "cs87_hero_title": f"{work_type}: {case.location}",
        "cs87_location": case.location,
        "cs87_work_type": work_type,
        "cs87_related_case_urls": _related_case_urls(case, catalog),
        "cs87_seo_title": f"{work_type}: {case.location} — фото выполненных работ",
        "cs87_seo_description": (
            f"{case.location}: {description}. Фото опубликованного объекта и ссылка "
            "на соответствующую услугу."
        ),
        "cs87_case_keywords": ", ".join(case.work_types),
        "cs87_service_url": SERVICE_CANONICALS[service_id],
    }


def update_case_seo_document(
    document: Mapping[str, Any],
    catalog: Sequence[CaseEvidence],
) -> dict[str, Any]:
    """Apply only evidence-backed S1-S3 fields, preserving every other value."""
    updated = copy.deepcopy(document)
    records = updated.get("cases")
    if not isinstance(records, list):
        raise CatalogError("cases-seo-import.json#cases must be a list")
    catalog_by_url = {case.url: case for case in catalog}
    ready_urls = {case.url for case in catalog if case.seo_ready}
    found_ready_urls: set[str] = set()
    imported_urls: set[str] = set()
    for record in records:
        canonical = canonicalize_case_url(str(record.get("url", "")))
        if canonical in imported_urls:
            raise CatalogError(f"duplicate case import URL: {canonical}")
        imported_urls.add(canonical)
        case = catalog_by_url.get(canonical)
        if case is None:
            raise CatalogError(f"case import URL is absent from catalog: {canonical}")
        fields = _case_seo_fields(case, catalog)
        if not fields:
            continue
        found_ready_urls.add(canonical)
        acf = record.get("acf")
        if not isinstance(acf, dict):
            raise CatalogError(f"case import ACF payload is invalid: {canonical}")
        for key, value in fields.items():
            if key not in MANAGED_CASE_SEO_FIELDS:
                raise CatalogError(f"attempted to update unmanaged case field {key}")
            acf[key] = value
    missing_ready_urls = sorted(ready_urls - found_ready_urls)
    if missing_ready_urls:
        raise CatalogError(
            f"missing {len(missing_ready_urls)} seo-ready cases from case import: "
            f"{', '.join(missing_ready_urls)}"
        )
    return updated


def _serialize_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _stage_bytes(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def _write_json_transaction(outputs: Sequence[tuple[Path, Mapping[str, Any]]]) -> None:
    """Replace all JSON outputs together, restoring exact prior bytes on failure."""
    normalized = [Path(path).resolve() for path, _ in outputs]
    path_keys = [os.path.normcase(str(path)) for path in normalized]
    if len(path_keys) != len(set(path_keys)):
        raise CatalogError("JSON transaction contains the same output path more than once")

    staged: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    replaced: list[Path] = []
    preserved_backups: set[Path] = set()
    try:
        for (_, payload), target in zip(outputs, normalized):
            staged[target] = _stage_bytes(target, _serialize_json(payload).encode("utf-8"))
        for target in normalized:
            backups[target] = _stage_bytes(target, target.read_bytes()) if target.exists() else None
        for target in normalized:
            replaced.append(target)
            os.replace(staged[target], target)
    except BaseException as exc:
        rollback_errors: list[str] = []
        for target in reversed(replaced):
            backup = backups.get(target)
            try:
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    os.replace(backup, target)
            except BaseException as rollback_exc:
                if backup is not None:
                    preserved_backups.add(backup)
                    recovery = f"; preserved backup {backup}"
                else:
                    recovery = "; no prior file existed to preserve"
                rollback_errors.append(f"{target}: {rollback_exc}{recovery}")
        if rollback_errors:
            raise OSError(
                f"cannot commit JSON output transaction: {exc}; rollback failed for "
                f"{'; '.join(rollback_errors)}"
            ) from exc
        if isinstance(exc, OSError):
            raise OSError(f"cannot commit JSON output transaction: {exc}") from exc
        raise
    finally:
        cleanup_paths = (
            *staged.values(),
            *(item for item in backups.values() if item and item not in preserved_backups),
        )
        for temp_path in cleanup_paths:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--output", type=Path, required=True, help="case catalog JSON output")
    parser.add_argument("--validate", action="store_true", help="fail unless the complete catalog is valid")
    parser.add_argument(
        "--update-seo-import",
        type=Path,
        help="surgically update the existing case SEO import after catalog validation",
    )
    parser.add_argument(
        "--checked-date",
        default=None,
        help="ISO audit date; defaults to the current local date",
    )
    return parser


def _configure_utf8_stdio() -> None:
    """Keep Cyrillic evidence paths readable in redirected Windows CLI logs."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        document = build_catalog_document(root, checked_date=args.checked_date)
        errors = validate_catalog_document(document)
        if errors and (args.validate or args.update_seo_import):
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            return 1
        outputs: list[tuple[Path, Mapping[str, Any]]] = [(output, document)]
        if args.update_seo_import:
            import_path = args.update_seo_import
            if not import_path.is_absolute():
                import_path = root / import_path
            source = _read_json(import_path)
            catalog = catalog_from_document(document)
            outputs.append((import_path, update_case_seo_document(source, catalog)))
        _write_json_transaction(outputs)
    except (CatalogError, OSError, KeyError, TypeError, StopIteration) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    summary = document["summary"]
    print(
        "catalog_cases={catalog_cases} canonical_merges={canonical_merges} "
        "selected_images={selected_image_urls} seo_ready={seo_ready_cases} blocked={blocked_cases}".format(
            **summary
        )
    )
    return 0


if __name__ == "__main__":
    _configure_utf8_stdio()
    raise SystemExit(main())
