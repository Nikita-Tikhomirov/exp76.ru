"""Tests for the traceable case and selected-image catalog."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request

import tools.site_content.cases as cases_module

from tools.site_content.cases import (
    CatalogError,
    CaseEvidence,
    ImageAudit,
    PageAudit,
    audit_image_url,
    build_case_catalog,
    build_catalog_document,
    catalog_from_document,
    canonicalize_case_url,
    main as cases_main,
    resolve_public_page,
    update_case_seo_document,
    validate_case_reference,
    validate_catalog_document,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "seo-content" / "service-hubs" / "case-catalog.json"
CASE_IMPORT_PATH = ROOT / "seo-content" / "cases" / "import" / "cases-seo-import.json"

EXPECTED_SUPPORT = {
    "https://exp76.ru/slip-ul-bugorok/": ("S1",),
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": ("S1",),
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": ("S1",),
    "https://exp76.ru/pos-slip/": ("S2", "S3"),
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": ("S2",),
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

EXPECTED_SELECTED_IMAGES = frozenset(
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

EXPECTED_OWNED_IMAGES = frozenset(
    {
        (
            "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/",
            "https://exp76.ru/wp-content/uploads/2019/02/NEwk9KFYTXY.webp",
        ),
        (
            "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/",
            "https://exp76.ru/wp-content/uploads/2019/02/IMG_20181015_110705_HDR.webp",
        ),
        (
            "https://exp76.ru/pos-slip/",
            "https://exp76.ru/wp-content/uploads/2020/10/20200514_085626.webp",
        ),
        (
            "https://exp76.ru/rybinsk-ul-grazhdanskaja/",
            "https://exp76.ru/wp-content/uploads/2020/10/Ila-CrwKkL4.webp",
        ),
        (
            "https://exp76.ru/slip-ul-bugorok/",
            "https://exp76.ru/wp-content/uploads/2023/12/20230817_084022-1-scaled.webp",
        ),
    }
)

EXPECTED_SUPPORT_DETAILS = {
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

PROOF_PAGE_IDS = {
    "https://exp76.ru/slip-ul-bugorok/": 10345,
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": 10136,
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": 9445,
    "https://exp76.ru/pos-slip/": 10096,
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": 9554,
}

BASELINE_SUBTREE_HASHES = {
    "source": "429d18887a3455c6e2aed98eb82eff719dfc10756593a5733e1bc7bd2746e1b8",
    "category_case_maps": "b4f6d15aa508b8f8d633ac82796dd800b750106902ecb3142a05888132a66da9",
    "service_case_maps": "9460cc9bdc4387e98519562aebc3322726b9fffdb6b53f50951c2fffb6eda97e",
}
BASELINE_FROZEN_TAIL_HASH = "56edb932c21e1154a848a256f771e0772f9273eda8539495a58ba7a5ae7ec364"

MANAGED_IMPORT_FIELDS = {
    "cs87_hero_title",
    "cs87_location",
    "cs87_work_type",
    "cs87_related_case_urls",
    "cs87_seo_title",
    "cs87_seo_description",
    "cs87_case_keywords",
    "cs87_service_url",
}

PRE_UPDATE_MANAGED_FIELDS = {
    "https://exp76.ru/slip-ul-bugorok/": {
        "cs87_hero_title": "Благоустройство участка: Слип ул. Бугорок",
        "cs87_location": "Слип ул. Бугорок",
        "cs87_work_type": "Благоустройство участка",
        "cs87_related_case_urls": [
            "https://exp76.ru/derevnja-selekhovo/",
            "https://exp76.ru/rybinsk-ul-grazhdanskaja/",
            "https://exp76.ru/pos-slip/",
            "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/",
        ],
        "cs87_seo_title": "Благоустройство участка: пример работ Слип ул. Бугорок — фото и описание",
        "cs87_seo_description": (
            "Благоустройство участка: кейс Слип ул. Бугорок. комплексное благоустройство. "
            "Фото, описание работ, технология, результат и ориентиры для расчета похожего проекта."
        ),
        "cs87_case_keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "cs87_service_url": "/fotogalereja/",
    },
    "https://exp76.ru/rybinsk-ul-grazhdanskaja/": {
        "cs87_hero_title": "Благоустройство участка: Рыбинск ул. Гражданская",
        "cs87_location": "Рыбинск ул. Гражданская",
        "cs87_work_type": "Благоустройство участка",
        "cs87_related_case_urls": [
            "https://exp76.ru/slip-ul-bugorok/",
            "https://exp76.ru/derevnja-selekhovo/",
            "https://exp76.ru/pos-slip/",
            "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/",
        ],
        "cs87_seo_title": (
            "Благоустройство участка: пример работ Рыбинск ул. Гражданская — фото и описание"
        ),
        "cs87_seo_description": (
            "Благоустройство участка: кейс Рыбинск ул. Гражданская. комплексное благоустройство. "
            "Фото, описание работ, технология, результат и ориентиры для расчета похожего проекта."
        ),
        "cs87_case_keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "cs87_service_url": "/fotogalereja/",
    },
    "https://exp76.ru/fotogalereja/g-rybinsk-r-on-verete/": {
        "cs87_hero_title": "Благоустройство участка: г. Рыбинск",
        "cs87_location": "г. Рыбинск, р-он Веретье",
        "cs87_work_type": "Благоустройство участка",
        "cs87_related_case_urls": [
            "https://exp76.ru/slip-ul-bugorok/",
            "https://exp76.ru/derevnja-selekhovo/",
            "https://exp76.ru/rybinsk-ul-grazhdanskaja/",
            "https://exp76.ru/pos-slip/",
        ],
        "cs87_seo_title": (
            "Благоустройство участка: пример работ г. Рыбинск, р-он Веретье — фото и описание"
        ),
        "cs87_seo_description": (
            "Благоустройство участка: кейс г. Рыбинск, р-он Веретье. благоустройство участка. "
            "Фото, описание работ, технология, результат и ориентиры для расчета похожего проекта."
        ),
        "cs87_case_keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "cs87_service_url": "/fotogalereja/",
    },
    "https://exp76.ru/pos-slip/": {
        "cs87_hero_title": "Благоустройство участка: пос. Слип",
        "cs87_location": "пос. Слип",
        "cs87_work_type": "Благоустройство участка",
        "cs87_related_case_urls": [
            "https://exp76.ru/slip-ul-bugorok/",
            "https://exp76.ru/derevnja-selekhovo/",
            "https://exp76.ru/rybinsk-ul-grazhdanskaja/",
            "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/",
        ],
        "cs87_seo_title": "Благоустройство участка: пример работ пос. Слип — фото и описание",
        "cs87_seo_description": (
            "Благоустройство участка: кейс пос. Слип. газон + посадка хвойных. "
            "Фото, описание работ, технология, результат и ориентиры для расчета похожего проекта."
        ),
        "cs87_case_keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "cs87_service_url": "/fotogalereja/",
    },
    "https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/": {
        "cs87_hero_title": "Благоустройство участка: д. Нестерово",
        "cs87_location": "д. Нестерово, Угличский р-он",
        "cs87_work_type": "Благоустройство участка",
        "cs87_related_case_urls": [
            "https://exp76.ru/slip-ul-bugorok/",
            "https://exp76.ru/derevnja-selekhovo/",
            "https://exp76.ru/rybinsk-ul-grazhdanskaja/",
            "https://exp76.ru/pos-slip/",
        ],
        "cs87_seo_title": (
            "Благоустройство участка: пример работ д. Нестерово, Угличский р-он — фото и описание"
        ),
        "cs87_seo_description": (
            "Благоустройство участка: кейс д. Нестерово, Угличский р-он. рулонный газон. "
            "Фото, описание работ, технология, результат и ориентиры для расчета похожего проекта."
        ),
        "cs87_case_keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "cs87_service_url": "/fotogalereja/",
    },
}


class _FakeResponse:
    def __init__(
        self,
        payload: bytes = b"",
        *,
        status: int = 200,
        content_type: str = "application/json",
        final_url: str = "",
    ) -> None:
        self.payload = payload
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.final_url = final_url

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self.payload if size < 0 else self.payload[:size]

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self.final_url


def _stable_hash(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _rest_url(canonical: str) -> str:
    slug = canonical.rstrip("/").rsplit("/", 1)[-1]
    return "https://exp76.ru/wp-json/wp/v2/pages?" + urlencode(
        {
            "slug": slug,
            "per_page": 100,
            "_fields": "id,link,status,type,featured_media",
        }
    )


def _source_urls() -> list[str]:
    payload = json.loads(CASE_IMPORT_PATH.read_text(encoding="utf-8"))
    return [canonicalize_case_url(item["url"]) for item in payload["cases"]]


def _fake_page_resolver(url: str, checked_date: str) -> PageAudit:
    canonical = canonicalize_case_url(url)
    return PageAudit(
        page_id=EXPECTED_PAGE_IDS[canonical],
        canonical_url=canonical,
        post_status="publish",
        http_status=200,
        content_type="text/html; charset=UTF-8",
        checked_date=checked_date,
        rest_url=_rest_url(canonical),
        final_url=canonical,
        post_type="page",
        featured_media_id=EXPECTED_FEATURED_MEDIA.get(canonical, 0),
    )


def _fake_image_auditor(url: str, checked_date: str) -> ImageAudit:
    return ImageAudit(
        url=url,
        http_status=200,
        content_type="image/webp",
        checked_date=checked_date,
        method="HEAD",
        final_url=url,
    )


class CaseCatalogTest(unittest.TestCase):
    """Catch invented mappings, lost provenance and unsafe case references."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = build_catalog_document(
            ROOT,
            page_resolver=_fake_page_resolver,
            image_auditor=_fake_image_auditor,
            checked_date="2026-08-28",
        )
        cls.catalog = build_case_catalog(
            ROOT,
            page_resolver=_fake_page_resolver,
            image_auditor=_fake_image_auditor,
            checked_date="2026-08-28",
        )

    def test_catalog_normalizes_35_cases_and_reports_canonical_merges(self) -> None:
        """Changing canonical dedupe or dropping a source occurrence must fail."""
        self.assertEqual(35, len(self.catalog))
        self.assertEqual(35, len({item.url for item in self.catalog}))
        self.assertEqual(142, self.document["summary"]["source_occurrences"])
        self.assertEqual(107, self.document["summary"]["canonical_merges"])
        self.assertTrue(all(item.location and item.work_types for item in self.catalog))
        self.assertTrue(all(item.page_id > 0 for item in self.catalog))
        self.assertEqual(35, len({item.page_id for item in self.catalog}))
        self.assertEqual(EXPECTED_PAGE_IDS, {item.url: item.page_id for item in self.catalog})
        self.assertEqual(
            {
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
            },
            self.document["summary"]["source_counts"],
        )

    def test_only_service_v2_proof_creates_s1_s3_support(self) -> None:
        """A category or generated import label must not invent S1-S8 support."""
        actual = {item.url: item.service_ids for item in self.catalog if item.service_ids}
        self.assertEqual(EXPECTED_SUPPORT, actual)
        self.assertEqual(6, sum(len(value) for value in actual.values()))
        self.assertEqual(30, sum(not item.service_ids for item in self.catalog))

        by_url = {item.url: item for item in self.catalog}
        s1 = by_url["https://exp76.ru/slip-ul-bugorok/"]
        self.assertEqual("hub_proof_only", s1.service_support[0].basis)
        self.assertIn("service-v2", s1.service_support[0].source_ref)

        rolled = by_url["https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/"]
        self.assertEqual(("S2",), rolled.service_ids)
        self.assertNotIn("посев", " ".join(rolled.work_types).lower())
        details = {
            item.url: tuple(
                (support.service_id, support.basis, support.source_ref)
                for support in item.service_support
            )
            for item in self.catalog
            if item.service_support
        }
        self.assertEqual(EXPECTED_SUPPORT_DETAILS, details)

    def test_acf_osushenie_selection_never_becomes_work_or_service_evidence(self) -> None:
        """The five ACF osushenie relationships are corroboration, not work facts."""
        acf = json.loads((ROOT / "acf_selected_works_map.json").read_text(encoding="utf-8"))
        selected_urls = {
            canonicalize_case_url(row["url"]) for row in acf["osushenie"]["cases"]
        }
        self.assertEqual(5, len(selected_urls))
        by_url = {item.url: item for item in self.catalog}
        for url in selected_urls:
            case = by_url[url]
            self.assertFalse(any("осуш" in value.lower() for value in case.work_types))
            self.assertFalse(case.service_ids)
            self.assertTrue(
                any(ref.startswith("acf_selected_works_map.json#osushenie.cases[") for ref in case.source_refs)
            )

    def test_location_and_work_provenance_comes_from_primary_case_source(self) -> None:
        """Generated SEO copy must not become a factual authority."""
        for item in self.catalog:
            self.assertTrue(item.location_sources)
            self.assertTrue(all(ref.startswith("cases_by_category.json#") for ref in item.location_sources))
            self.assertTrue(item.work_type_sources)
            self.assertTrue(
                all(fact.source_ref.startswith("cases_by_category.json#") for fact in item.work_type_sources)
            )
            self.assertIn("seo-content/cases/import/cases-seo-import.json", item.source_files)

    def test_every_input_occurrence_has_an_exact_case_source_reference(self) -> None:
        """Per-source counts cannot be spoofed while individual evidence rows disappear."""
        by_url = {item.url: item for item in self.catalog}
        cases_by_category = json.loads((ROOT / "cases_by_category.json").read_text(encoding="utf-8"))
        for category, records in cases_by_category.items():
            for index, record in enumerate(records):
                ref = f"cases_by_category.json#{category}[{index}]"
                self.assertIn(ref, by_url[canonicalize_case_url(record["url"])].source_refs)

        acf = json.loads((ROOT / "acf_selected_works_map.json").read_text(encoding="utf-8"))
        for category, payload in acf.items():
            for index, record in enumerate(payload["cases"]):
                ref = f"acf_selected_works_map.json#{category}.cases[{index}]"
                self.assertIn(ref, by_url[canonicalize_case_url(record["url"])].source_refs)

        case_import = json.loads(CASE_IMPORT_PATH.read_text(encoding="utf-8"))
        for index, record in enumerate(case_import["cases"]):
            ref = f"seo-content/cases/import/cases-seo-import.json#cases[{index}]"
            self.assertIn(ref, by_url[canonicalize_case_url(record["url"])].source_refs)

        for url, details in EXPECTED_SUPPORT_DETAILS.items():
            for _, _, source_ref in details:
                base_ref = source_ref.split("#", 1)[0] + "#" + source_ref.split("#", 1)[1]
                self.assertIn(base_ref, by_url[url].source_refs)

    def test_selected_images_are_internal_verified_and_case_owned_conservatively(self) -> None:
        """Adding an external/unverified asset or assigning illustrations to a case must fail."""
        audits = self.document["selected_image_audits"]
        self.assertEqual(len(EXPECTED_SELECTED_IMAGES), len(audits))
        self.assertEqual(EXPECTED_SELECTED_IMAGES, {item["url"] for item in audits})
        self.assertTrue(
            all(item["url"].startswith("https://exp76.ru/wp-content/uploads/") for item in audits)
        )
        self.assertTrue(all(item["http_status"] == 200 for item in audits))
        self.assertTrue(all(item["content_type"] == "image/webp" for item in audits))
        self.assertTrue(all(item["checked_date"] == "2026-08-28" for item in audits))

        owned = {(item.url, image) for item in self.catalog for image in item.image_urls}
        self.assertEqual(EXPECTED_OWNED_IMAGES, owned)
        global_audits = {item["url"]: item for item in audits}
        for case in self.catalog:
            for audit in case.image_audits:
                global_row = global_audits[audit.url]
                for key, value in asdict(audit).items():
                    self.assertEqual(value, global_row[key])
        for url, media_id in EXPECTED_FEATURED_MEDIA.items():
            self.assertEqual(media_id, next(item for item in self.catalog if item.url == url).page_audit.featured_media_id)
        verified = next(item for item in self.catalog if item.url == "https://exp76.ru/pos-slip/")
        self.assertEqual(
            [],
            validate_case_reference(verified.page_id, verified.image_urls[0], self.catalog),
        )

    def test_catalog_rejects_unknown_case_and_unowned_photo(self) -> None:
        """A wrong ID or a photo borrowed from another case must fail validation."""
        catalog = (
            CaseEvidence(
                page_id=101,
                url="https://exp76.ru/portfolio/real/",
                title="Реальный объект",
                location="Ярославль",
                work_types=("планировка",),
                service_ids=("S5",),
                image_urls=("https://exp76.ru/wp-content/uploads/real.webp",),
                source_files=("fixture.json",),
                seo_ready=True,
                image_audits=(
                    ImageAudit(
                        url="https://exp76.ru/wp-content/uploads/real.webp",
                        http_status=200,
                        content_type="image/webp",
                        checked_date="2026-08-28",
                        method="HEAD",
                    ),
                ),
            ),
        )
        errors = validate_case_reference(
            999,
            "https://exp76.ru/wp-content/uploads/fake.webp",
            catalog,
        )
        self.assertIn("unknown case 999", errors)

        errors = validate_case_reference(
            101,
            "https://exp76.ru/wp-content/uploads/fake.webp",
            catalog,
        )
        self.assertIn(
            "image https://exp76.ru/wp-content/uploads/fake.webp is not owned by case 101",
            errors,
        )

    def test_external_image_is_rejected_before_network_access(self) -> None:
        """A non-exp76 upload URL can never enter selected-image evidence."""
        document = copy.deepcopy(self.document)
        document["selected_image_audits"][0]["url"] = "https://example.com/fake.webp"
        self.assertIn(
            "selected image is not an internal upload: https://example.com/fake.webp",
            validate_catalog_document(document),
        )

    def test_case_seo_update_is_surgical_and_changes_exactly_five_records(self) -> None:
        """New hub links must preserve root maps, record order and unrelated ACF values."""
        final_document = json.loads(CASE_IMPORT_PATH.read_text(encoding="utf-8"))
        baseline = copy.deepcopy(final_document)
        for record in baseline["cases"]:
            fields = PRE_UPDATE_MANAGED_FIELDS.get(record["url"])
            if fields:
                record["acf"].update(copy.deepcopy(fields))
        before = copy.deepcopy(baseline)
        updated = update_case_seo_document(baseline, self.catalog)

        self.assertEqual(before["source"], updated["source"])
        self.assertEqual(before["category_case_maps"], updated["category_case_maps"])
        self.assertEqual(before["service_case_maps"], updated["service_case_maps"])
        self.assertEqual(
            [item["url"] for item in before["cases"]],
            [item["url"] for item in updated["cases"]],
        )

        changed_urls: list[str] = []
        for old_case, new_case in zip(before["cases"], updated["cases"]):
            if old_case == new_case:
                continue
            changed_urls.append(old_case["url"])
            self.assertEqual(
                {key: value for key, value in old_case.items() if key != "acf"},
                {key: value for key, value in new_case.items() if key != "acf"},
            )
            self.assertEqual(
                {key: value for key, value in old_case["acf"].items() if key not in MANAGED_IMPORT_FIELDS},
                {key: value for key, value in new_case["acf"].items() if key not in MANAGED_IMPORT_FIELDS},
            )

        self.assertEqual(set(EXPECTED_SUPPORT), set(changed_urls))
        self.assertEqual(5, len(changed_urls))
        self.assertEqual(final_document, updated)
        self.assertEqual(before, baseline)
        by_url = {item["url"]: item for item in updated["cases"]}
        self.assertEqual(
            "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
            by_url["https://exp76.ru/pos-slip/"]["acf"]["cs87_service_url"],
        )
        self.assertEqual(
            ["https://exp76.ru/fotogalereja/d-nesterovo-uglichskijj-r-on/"],
            by_url["https://exp76.ru/pos-slip/"]["acf"]["cs87_related_case_urls"],
        )

    def test_checked_in_case_seo_import_is_idempotent_and_preserves_frozen_hashes(self) -> None:
        """A second Task 3 run must change zero records and no frozen payload subtree."""
        document = json.loads(CASE_IMPORT_PATH.read_text(encoding="utf-8"))
        updated = update_case_seo_document(document, self.catalog)
        self.assertEqual(document, updated)
        self.assertEqual(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        )
        for key, expected_hash in BASELINE_SUBTREE_HASHES.items():
            self.assertEqual(expected_hash, _stable_hash(document[key]))
        raw = CASE_IMPORT_PATH.read_bytes()
        marker = b'"category_case_maps"'
        frozen_tail = raw[raw.index(marker) :].replace(b"\r\n", b"\n")
        self.assertEqual(BASELINE_FROZEN_TAIL_HASH, hashlib.sha256(frozen_tail).hexdigest())

    def test_catalog_document_round_trip_preserves_nested_evidence(self) -> None:
        """CLI import updates must reuse the audited document without rechecking the network."""
        restored = catalog_from_document(self.document)
        self.assertEqual(self.catalog, restored)

    def test_checked_in_catalog_is_valid_live_evidence(self) -> None:
        """The shipped artifact must contain the audited production evidence, not fixtures."""
        document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual([], validate_catalog_document(document))
        self.assertEqual(35, document["summary"]["catalog_cases"])
        self.assertEqual(107, document["summary"]["canonical_merges"])
        self.assertEqual(
            len(EXPECTED_SELECTED_IMAGES),
            document["summary"]["selected_image_urls"],
        )
        self.assertEqual(5, document["summary"]["seo_ready_cases"])
        self.assertEqual(30, document["summary"]["blocked_cases"])
        self.assertEqual(EXPECTED_PAGE_IDS, {item["url"]: item["page_id"] for item in document["cases"]})
        self.assertTrue(all(item["page_audit"]["checked_date"] == "2026-08-28" for item in document["cases"]))
        self.assertTrue(all(item["page_audit"]["post_type"] == "page" for item in document["cases"]))
        self.assertTrue(all(item["page_audit"]["http_status"] == 200 for item in document["cases"]))
        self.assertTrue(all(item["page_audit"]["method"] == "HEAD" for item in document["cases"]))
        self.assertTrue(all("slug=fixture" not in item["page_audit"]["rest_url"] for item in document["cases"]))
        self.assertTrue(all(item["page_audit"]["final_url"] == item["url"] for item in document["cases"]))

    def test_checked_catalog_reconciles_exactly_with_local_sources_and_stored_audits(self) -> None:
        """A self-consistent edited artifact must still match the four source layers."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        pages = {
            row["url"]: PageAudit(**row["page_audit"])
            for row in checked["cases"]
        }
        images = {
            row["url"]: ImageAudit(
                **{key: value for key, value in row.items() if key != "source_refs"}
            )
            for row in checked["selected_image_audits"]
        }
        rebuilt = build_catalog_document(
            ROOT,
            page_resolver=lambda url, _: pages[url],
            image_auditor=lambda url, _: images[url],
            checked_date=checked["checked_date"],
        )
        self.assertEqual(checked, rebuilt)

    def test_fixed_evidence_rebuild_is_byte_deterministic(self) -> None:
        """Stable source order and fixed audits must produce identical checked-in bytes."""
        first = build_catalog_document(
            ROOT,
            page_resolver=_fake_page_resolver,
            image_auditor=_fake_image_auditor,
            checked_date="2026-08-28",
        )
        second = build_catalog_document(
            ROOT,
            page_resolver=_fake_page_resolver,
            image_auditor=_fake_image_auditor,
            checked_date="2026-08-28",
        )
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, indent=2) + "\n",
            json.dumps(second, ensure_ascii=False, indent=2) + "\n",
        )

    def test_checked_validator_pins_exact_ids_support_and_image_ownership(self) -> None:
        """A fabricated but internally consistent S1-S3 mapping must still be rejected."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(checked)
        mutated["cases"][0]["page_id"] = 999999
        mutated["cases"][0]["page_audit"]["page_id"] = 999999
        self.assertTrue(any("expected page_id" in error for error in validate_catalog_document(mutated)))

        mutated = copy.deepcopy(checked)
        unsupported = next(row for row in mutated["cases"] if not row["service_ids"])
        unsupported["service_ids"] = ["S1"]
        unsupported["service_support"] = [
            {"service_id": "S1", "basis": "hub_proof_only", "source_ref": "fabricated"}
        ]
        self.assertTrue(any("exact service support" in error for error in validate_catalog_document(mutated)))

        mutated = copy.deepcopy(checked)
        owner = next(row for row in mutated["cases"] if row["image_urls"])
        owner["image_urls"] = [next(iter(EXPECTED_SELECTED_IMAGES - set(owner["image_urls"])))]
        self.assertTrue(any("exact case-owned images" in error for error in validate_catalog_document(mutated)))

    def test_checked_validator_accepts_a_valid_ranged_get_audit(self) -> None:
        """A HEAD 405 followed by 206 image headers remains valid replay evidence."""
        document = copy.deepcopy(self.document)
        owned = {image for case in document["cases"] for image in case["image_urls"]}
        audit = next(
            row for row in document["selected_image_audits"] if row["url"] not in owned
        )
        audit["http_status"] = 206
        audit["method"] = "GET_RANGE"
        audit["error"] = "HEAD failed: HTTP Error 405"
        document["summary"]["selected_image_statuses"] = {
            "200": len(EXPECTED_SELECTED_IMAGES) - 1,
            "206": 1,
        }
        self.assertEqual([], validate_catalog_document(document))

    def test_checked_validator_accepts_a_valid_ranged_get_page_audit(self) -> None:
        """The shared HEAD fallback contract also applies to public case pages."""
        document = copy.deepcopy(self.document)
        page_audit = document["cases"][0]["page_audit"]
        page_audit["http_status"] = 206
        page_audit["method"] = "GET_RANGE"
        self.assertEqual([], validate_catalog_document(document))

    def test_case_url_canonicalization_collapses_source_variants(self) -> None:
        """Protocol, host case, query and trailing-slash variants must share one owner."""
        self.assertEqual(
            "https://exp76.ru/fotogalereja/real/",
            canonicalize_case_url("HTTP://WWW.EXP76.RU//fotogalereja/real?x=1#gallery"),
        )
        with self.assertRaises(CatalogError):
            canonicalize_case_url("https://example.com/real/")

    def test_case_seo_update_rejects_missing_ready_case_records(self) -> None:
        """A partial import cannot silently omit a case selected by the new hubs."""
        payload = {
            "source": "fixture",
            "cases": [],
            "category_case_maps": {},
            "service_case_maps": [],
        }
        with self.assertRaisesRegex(CatalogError, "missing 5 seo-ready cases"):
            update_case_seo_document(payload, self.catalog)


class PublicEvidenceAuditTest(unittest.TestCase):
    """Exercise the real REST/HTTP boundary while replacing only network I/O."""

    URL = "https://exp76.ru/pos-slip/"

    @staticmethod
    def _row(
        url: str,
        *,
        page_id: int = 10096,
        post_type: str = "page",
        status: str = "publish",
    ) -> dict[str, object]:
        return {
            "id": page_id,
            "link": url,
            "status": status,
            "type": post_type,
            "featured_media": 10101,
        }

    @staticmethod
    def _json_response(rows: object) -> _FakeResponse:
        return _FakeResponse(json.dumps(rows).encode("utf-8"))

    def test_resolver_selects_one_exact_canonical_among_same_slug_results(self) -> None:
        """A same-slug page under another parent cannot steal the requested case ID."""
        rows = [
            self._row("https://exp76.ru/other/pos-slip/", page_id=999),
            self._row(self.URL),
        ]
        responses = [
            self._json_response(rows),
            _FakeResponse(content_type="text/html; charset=UTF-8", final_url=self.URL),
        ]
        with patch("tools.site_content.cases._open_url", side_effect=responses):
            audit = resolve_public_page(self.URL, "2026-08-28")
        self.assertEqual(10096, audit.page_id)
        self.assertEqual("page", audit.post_type)
        self.assertEqual(self.URL, audit.canonical_url)
        self.assertEqual(self.URL, audit.final_url)
        self.assertTrue(audit.is_valid)

    def test_resolver_rejects_canonicalized_but_non_exact_rest_links(self) -> None:
        """REST evidence cannot launder HTTP, www, query or fragment variants."""
        variants = (
            "http://www.exp76.ru/pos-slip/",
            "https://exp76.ru/pos-slip/?tracking=1",
            "https://exp76.ru/pos-slip/#gallery",
        )
        for variant in variants:
            responses = [
                self._json_response([self._row(variant)]),
                _FakeResponse(content_type="text/html", final_url=self.URL),
            ]
            with self.subTest(variant=variant), patch(
                "tools.site_content.cases._open_url",
                side_effect=responses,
            ):
                with self.assertRaisesRegex(CatalogError, "resolved to 0 exact records"):
                    resolve_public_page(self.URL, "2026-08-28")

    def test_resolver_rejects_redirected_rest_response(self) -> None:
        """The public REST request itself must remain on its exact requested endpoint."""
        responses = [
            _FakeResponse(
                json.dumps([self._row(self.URL)]).encode("utf-8"),
                final_url="https://example.com/wp-json/wp/v2/pages?slug=pos-slip",
            ),
            _FakeResponse(content_type="text/html", final_url=self.URL),
        ]
        with patch("tools.site_content.cases._open_url", side_effect=responses):
            with self.assertRaisesRegex(CatalogError, "REST endpoint redirected"):
                resolve_public_page(self.URL, "2026-08-28")

    def test_transport_redirect_policy_blocks_before_following(self) -> None:
        """urllib must never contact a redirect destination outside the audited URL."""
        handler_type = getattr(cases_module, "_RejectRedirects", None)
        self.assertIsNotNone(handler_type)
        if handler_type is None:
            return
        request = Request(self.URL)
        for destination in ("https://example.com/other/", "http://exp76.ru/pos-slip/"):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(HTTPError, "redirect blocked"):
                    handler_type().redirect_request(
                        request,
                        None,
                        302,
                        "Found",
                        {},
                        destination,
                    )

    def test_resolver_rejects_zero_or_multiple_exact_canonicals(self) -> None:
        """A public slug query must resolve to exactly one canonical link."""
        fixtures = {
            "zero": [self._row("https://exp76.ru/other/pos-slip/")],
            "multiple": [self._row(self.URL), self._row(self.URL, page_id=10097)],
        }
        for label, rows in fixtures.items():
            with self.subTest(label=label), patch(
                "tools.site_content.cases._open_url",
                return_value=self._json_response(rows),
            ):
                with self.assertRaisesRegex(CatalogError, "resolved to"):
                    resolve_public_page(self.URL, "2026-08-28")

    def test_resolver_rejects_wrong_type_or_status(self) -> None:
        """Only a published WordPress page is valid case evidence."""
        fixtures = {
            "post": self._row(self.URL, post_type="post"),
            "draft": self._row(self.URL, status="draft"),
        }
        for label, row in fixtures.items():
            with self.subTest(label=label), patch(
                "tools.site_content.cases._open_url",
                return_value=self._json_response([row]),
            ):
                with self.assertRaisesRegex(CatalogError, "not a published page"):
                    resolve_public_page(self.URL, "2026-08-28")

    def test_resolver_fails_closed_for_rest_and_http_errors(self) -> None:
        """Timeouts, malformed JSON, REST 404 and non-HTML pages cannot be cataloged."""
        rest_404 = HTTPError(_rest_url(self.URL), 404, "not found", {}, io.BytesIO())
        rest_failures = {
            "timeout": TimeoutError("timeout"),
            "404": rest_404,
        }
        for label, failure in rest_failures.items():
            with self.subTest(label=label), patch(
                "tools.site_content.cases._open_url",
                side_effect=failure,
            ):
                with self.assertRaisesRegex(CatalogError, "cannot resolve public page"):
                    resolve_public_page(self.URL, "2026-08-28")

        with patch(
            "tools.site_content.cases._open_url",
            return_value=_FakeResponse(b"not-json"),
        ):
            with self.assertRaisesRegex(CatalogError, "invalid public page response"):
                resolve_public_page(self.URL, "2026-08-28")

        responses = [
            self._json_response([self._row(self.URL)]),
            _FakeResponse(content_type="image/webp", final_url=self.URL),
            _FakeResponse(content_type="image/webp", final_url=self.URL),
        ]
        with patch("tools.site_content.cases._open_url", side_effect=responses):
            with self.assertRaisesRegex(CatalogError, "HTTP check failed"):
                resolve_public_page(self.URL, "2026-08-28")

    def test_resolver_wraps_malformed_rest_row_schema(self) -> None:
        """Malformed page rows fail with a diagnostic CatalogError, never raw exceptions."""
        fixtures = {
            "non_object": [None],
            "bad_id": [self._row(self.URL, page_id="not-an-id")],
            "zero_id": [self._row(self.URL, page_id=0)],
        }
        for label, rows in fixtures.items():
            responses = [
                self._json_response(rows),
                _FakeResponse(content_type="text/html", final_url=self.URL),
            ]
            with self.subTest(label=label), patch(
                "tools.site_content.cases._open_url",
                side_effect=responses,
            ):
                with self.assertRaisesRegex(CatalogError, "invalid public page record"):
                    resolve_public_page(self.URL, "2026-08-28")

    def test_resolver_rejects_redirect_away_from_exact_case_url(self) -> None:
        """The final HTTP target is part of canonical case evidence."""
        responses = [
            self._json_response([self._row(self.URL)]),
            _FakeResponse(content_type="text/html", final_url="https://exp76.ru/other/"),
        ]
        with patch("tools.site_content.cases._open_url", side_effect=responses):
            with self.assertRaisesRegex(CatalogError, "redirected away"):
                resolve_public_page(self.URL, "2026-08-28")

    def test_image_audit_uses_ranged_get_only_after_head_failure(self) -> None:
        """HEAD fallback may inspect headers but must not read an image body."""
        image_url = "https://exp76.ru/wp-content/uploads/real.webp"
        requests = []

        def fake_open(request: object, **_: object) -> _FakeResponse:
            requests.append(request)
            if len(requests) == 1:
                raise HTTPError(image_url, 405, "method not allowed", {}, io.BytesIO())
            return _FakeResponse(
                status=206,
                content_type="image/webp",
                final_url=image_url,
            )

        with patch("tools.site_content.cases._open_url", side_effect=fake_open):
            audit = audit_image_url(image_url, "2026-08-28")
        self.assertTrue(audit.is_valid)
        self.assertEqual("GET_RANGE", audit.method)
        self.assertEqual("HEAD", requests[0].get_method())
        self.assertEqual("GET", requests[1].get_method())
        self.assertEqual("bytes=0-0", requests[1].get_header("Range"))

    def test_image_audit_fails_closed_when_both_probes_fail_or_redirect(self) -> None:
        """An unavailable or redirected selected image never becomes valid evidence."""
        image_url = "https://exp76.ru/wp-content/uploads/real.webp"
        failures = [
            HTTPError(image_url, 405, "method not allowed", {}, io.BytesIO()),
            HTTPError(image_url, 404, "not found", {}, io.BytesIO()),
        ]
        with patch("tools.site_content.cases._open_url", side_effect=failures):
            audit = audit_image_url(image_url, "2026-08-28")
        self.assertFalse(audit.is_valid)
        self.assertEqual(404, audit.http_status)

        with patch(
            "tools.site_content.cases._open_url",
            return_value=_FakeResponse(
                content_type="image/webp",
                final_url="https://exp76.ru/wp-content/uploads/other.webp",
            ),
        ):
            redirected = audit_image_url(image_url, "2026-08-28")
        self.assertFalse(redirected.is_valid)

    def test_external_image_is_rejected_without_network_access(self) -> None:
        """Host/path validation happens before any public HTTP request."""
        with patch("tools.site_content.cases._open_url") as mocked_open:
            with self.assertRaises(CatalogError):
                audit_image_url("https://example.com/fake.webp", "2026-08-28")
        mocked_open.assert_not_called()


class CatalogCliTransactionTest(unittest.TestCase):
    """Invalid evidence must leave both local output files byte-identical."""

    def test_catalog_validation_failure_leaves_both_outputs_unchanged(self) -> None:
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        invalid = copy.deepcopy(checked)
        invalid["selected_image_audits"][0]["url"] = "https://example.com/fake.webp"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_path.write_bytes(b"catalog-before\n")
            import_path.write_bytes(b"import-before\n")
            with patch("tools.site_content.cases.build_catalog_document", return_value=invalid):
                with redirect_stderr(io.StringIO()):
                    result = cases_main(
                        [
                            "--root",
                            str(root),
                            "--output",
                            str(catalog_path),
                            "--update-seo-import",
                            str(import_path),
                            "--validate",
                        ]
                    )
            self.assertEqual(1, result)
            self.assertEqual(b"catalog-before\n", catalog_path.read_bytes())
            self.assertEqual(b"import-before\n", import_path.read_bytes())

    def test_import_validation_failure_happens_before_catalog_write(self) -> None:
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        bad_import = {
            "source": "fixture",
            "cases": [{"url": "https://exp76.ru/not-in-catalog/", "acf": {}}],
            "category_case_maps": {},
            "service_case_maps": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_path.write_bytes(b"catalog-before\n")
            import_before = json.dumps(bad_import).encode("utf-8")
            import_path.write_bytes(import_before)
            with patch("tools.site_content.cases.build_catalog_document", return_value=checked):
                with redirect_stderr(io.StringIO()):
                    result = cases_main(
                        [
                            "--root",
                            str(root),
                            "--output",
                            str(catalog_path),
                            "--update-seo-import",
                            str(import_path),
                            "--validate",
                        ]
                    )
            self.assertEqual(1, result)
            self.assertEqual(b"catalog-before\n", catalog_path.read_bytes())
            self.assertEqual(import_before, import_path.read_bytes())

    def test_import_update_requires_validation_even_without_validate_flag(self) -> None:
        """Mutation mode cannot opt out of the catalog evidence gate."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        invalid = copy.deepcopy(checked)
        invalid["selected_image_audits"][0]["url"] = "https://example.com/fake.webp"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_before = b"catalog-before\n"
            import_before = CASE_IMPORT_PATH.read_bytes()
            catalog_path.write_bytes(catalog_before)
            import_path.write_bytes(import_before)
            with patch("tools.site_content.cases.build_catalog_document", return_value=invalid):
                with redirect_stderr(io.StringIO()):
                    result = cases_main(
                        [
                            "--root",
                            str(root),
                            "--output",
                            str(catalog_path),
                            "--update-seo-import",
                            str(import_path),
                        ]
                    )

            self.assertEqual(1, result)
            self.assertEqual(catalog_before, catalog_path.read_bytes())
            self.assertEqual(import_before, import_path.read_bytes())

    def test_second_replace_failure_rolls_back_both_outputs(self) -> None:
        """A filesystem failure cannot leave the catalog newer than its import."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_before = b"catalog-before\n"
            import_before = CASE_IMPORT_PATH.read_bytes()
            catalog_path.write_bytes(catalog_before)
            import_path.write_bytes(import_before)
            real_replace = os.replace
            failed = False

            def fail_import_replace(source: object, destination: object) -> None:
                nonlocal failed
                if Path(destination).resolve() == import_path.resolve() and not failed:
                    failed = True
                    raise OSError("simulated second replacement failure")
                real_replace(source, destination)

            with patch("tools.site_content.cases.build_catalog_document", return_value=checked):
                with patch("tools.site_content.cases.os.replace", side_effect=fail_import_replace):
                    with redirect_stderr(io.StringIO()):
                        result = cases_main(
                            [
                                "--root",
                                str(root),
                                "--output",
                                str(catalog_path),
                                "--update-seo-import",
                                str(import_path),
                                "--validate",
                            ]
                        )

            self.assertEqual(1, result)
            self.assertEqual(catalog_before, catalog_path.read_bytes())
            self.assertEqual(import_before, import_path.read_bytes())
            self.assertEqual([], list(root.glob(".*.tmp")))

    def test_keyboard_interrupt_on_second_replace_rolls_back_both_outputs(self) -> None:
        """A catchable interruption cannot leave a split catalog/import generation."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_before = b"catalog-before\n"
            import_before = b" \n" + CASE_IMPORT_PATH.read_bytes()
            catalog_path.write_bytes(catalog_before)
            import_path.write_bytes(import_before)
            real_replace = os.replace
            interrupted = False

            def interrupt_import_replace(source: object, destination: object) -> None:
                nonlocal interrupted
                if Path(destination).resolve() == import_path.resolve() and not interrupted:
                    interrupted = True
                    real_replace(source, destination)
                    raise KeyboardInterrupt
                real_replace(source, destination)

            with patch("tools.site_content.cases.build_catalog_document", return_value=checked):
                with patch(
                    "tools.site_content.cases.os.replace",
                    side_effect=interrupt_import_replace,
                ):
                    with self.assertRaises(KeyboardInterrupt):
                        cases_main(
                            [
                                "--root",
                                str(root),
                                "--output",
                                str(catalog_path),
                                "--update-seo-import",
                                str(import_path),
                                "--validate",
                            ]
                        )

            self.assertEqual(catalog_before, catalog_path.read_bytes())
            self.assertEqual(import_before, import_path.read_bytes())
            self.assertEqual([], list(root.glob(".*.tmp")))

    def test_failed_rollback_preserves_and_reports_recovery_backup(self) -> None:
        """If rollback itself fails, exact old bytes remain available to an operator."""
        checked = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            import_path = root / "import.json"
            catalog_before = b"catalog-before\n"
            import_before = CASE_IMPORT_PATH.read_bytes()
            catalog_path.write_bytes(catalog_before)
            import_path.write_bytes(import_before)
            real_replace = os.replace
            replace_count = 0

            def fail_import_and_rollback(source: object, destination: object) -> None:
                nonlocal replace_count
                replace_count += 1
                if replace_count in {2, 3}:
                    raise OSError(f"simulated replace failure {replace_count}")
                real_replace(source, destination)

            errors = io.StringIO()
            with patch("tools.site_content.cases.build_catalog_document", return_value=checked):
                with patch(
                    "tools.site_content.cases.os.replace",
                    side_effect=fail_import_and_rollback,
                ):
                    with redirect_stderr(errors):
                        result = cases_main(
                            [
                                "--root",
                                str(root),
                                "--output",
                                str(catalog_path),
                                "--update-seo-import",
                                str(import_path),
                                "--validate",
                            ]
                        )

            backups = list(root.glob(".import.json.*.tmp"))
            self.assertEqual(1, result)
            self.assertIn("preserved backup", errors.getvalue())
            self.assertEqual(1, len(backups))
            self.assertEqual(import_before, backups[0].read_bytes())
            self.assertEqual(catalog_before, catalog_path.read_bytes())
            self.assertEqual(import_before, import_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
