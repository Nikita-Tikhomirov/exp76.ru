import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import service_v2 as service_v2_module
from tools.service_v2 import (
    ContractError,
    count_words,
    load_hub_services,
    load_services_auto,
    prepare_service_for_release,
    render_service,
    sync_services,
    validate_service_v2,
)
from tools.site_content.contracts import (
    load_case_catalog,
    load_page_architecture,
    load_release_manifest,
    numeric_fact_claims,
    validate_release_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
DATA_DIR = THEME / "content" / "service-v2"
HUB_SOURCE_DIR = ROOT / "seo-content" / "service-hubs" / "hubs"
ARCHITECTURE_PATH = (
    ROOT
    / "seo-data"
    / "2026-08-exp76-services"
    / "processed"
    / "complete_page_architecture.csv"
)
CASE_CATALOG_PATH = ROOT / "seo-content" / "service-hubs" / "case-catalog.json"
RELEASE_MANIFEST_PATH = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
RELEASE_ID = "service-hubs-2026-08-28"
HUB_COUNT = 15
CHILD_SERVICE_COUNT = 65
ARTICLE_COUNT = 11

EXPECTED_SERVICES = {
    "S1": (673, "landshaftnoe-proektirovanie"),
    "S2": (6868, "gazon-posevnojj-i-gazon-rulonnyjj"),
    "S3": (6871, "posadka-derevev-i-kustarnikov"),
    "S4": (9357, "ukhod-za-sadom"),
    "S5": (667, "planirovka-territorii"),
    "S6": (676, "podpornye-stenki"),
    "S7": (6918, "ulichnoe-osveshhenie-uchastka"),
    "S8": (9282, "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch"),
    "S9": (6870, "vykorchevyvanie-pnejj-spil-derevev"),
    "S10": (
        6900,
        "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev",
    ),
    "S11": (6922, "sistemy-tumanoobrazovaniya"),
    "S12": (9138, "fundament-na-zhelezobetonnykh-svajakh"),
    "S13": (9312, "navesy-iz-metalla"),
    "S14": (9775, "kaminy-pechi-barbekju"),
    "S15": (9838, "snos-i-demontazh-zdanijj-domov"),
}

EXPECTED_CASES = {
    "S1": [10345, 10136, 9445],
    "S2": [10096, 9554],
    "S3": [10096],
    "S4": [],
    "S5": [],
    "S6": [],
    "S7": [],
    "S8": [],
    "S9": [8613],
    "S10": [8608],
    "S11": [],
    "S12": [],
    "S13": [],
    "S14": [],
    "S15": [],
}

EXPECTED_SCOPE_COUNTS = {
    "S1": 5,
    "S2": 4,
    "S3": 5,
    "S4": 5,
    "S5": 5,
    "S6": 5,
    "S7": 5,
    "S8": 5,
    "S9": 4,
    "S10": 5,
    "S11": 4,
    "S12": 4,
    "S13": 5,
    "S14": 5,
    "S15": 6,
}
SCOPE_CARD_COUNT = sum(EXPECTED_SCOPE_COUNTS.values())

EXPECTED_LEGACY_TEXT_WORDS = {
    "S1": 1115,
    "S2": 961,
    "S3": 975,
    "S4": 1247,
    "S5": 1231,
    "S6": 1207,
    "S7": 1143,
    "S8": 1186,
    "S9": 1170,
    "S10": 1219,
    "S11": 1147,
    "S12": 1154,
    "S13": 1179,
    "S14": 1188,
    "S15": 1236,
}

EXPECTED_LEGACY_TEXT_FINGERPRINTS = {
    "S1": "4a497f03c8834cb7532b4cba9d9a12cb18b4da135c0b6747ef94c88b854b634f",
    "S2": "56cd5e3b160190830b292d09b6a18f925b2e564016567526d3613918f269db71",
    "S3": "cc85c4133aa70c1d07f15f63367aca046eb2671a6a8374696fb57feefa8efc9b",
    "S4": "fae7e96c981e7e8826bb11bf9087e2840e515d37d66012949d051167a5084824",
    "S5": "d11f0f12014a9e63a433150434af062d38cf41e83bda613f505fa916accee612",
    "S6": "971c0615af4fba7dd82ff7c14c3bbd67b00bb1406332994877cb27e1b776751a",
    "S7": "377235f0c427c1d0b72c5b3b5d9f1eaef111ca35402a7db362313002c0d4c053",
    "S8": "43a422865cd8a5011f17f8e1fdb4b9a275d10468773dc74a11f91187a3c99dc0",
    "S9": "76f2ca09e0b7539e2ccb7860595dc9c4564f94f93e82000c7fa802ecd835e413",
    "S10": "555bf77ca4e24b9a293cd524855972c5222dbbf5284c40d0e3fbbc7a6c0a995e",
    "S11": "4eaa003f77cf9af68d535956ea7f59c0b98369a2620ba7b7276665faf53c620c",
    "S12": "17f1713ce7e0b4854a19f985ad6a5124341b0dde3c4c00a1f10203d89695520f",
    "S13": "061e21fcb5cf0a7e83ba292a22ec042bfa1db28263bf7ae9451470c8686ddd45",
    "S14": "eb87ae33f7f76ba9f22a6664e8edb3ea88afe2b66f10214fff721910e7ea4663",
    "S15": "58f6114b89ab8e21dc12e8c9c9e4edccd7573dcdfa02f4607231c3b7e38d8651",
}

def _expected_navigation() -> dict[str, dict[str, dict[str, str]]]:
    """Build the exact 15-hub navigation contract from the completed ledger."""
    architecture = load_page_architecture(ARCHITECTURE_PATH)
    navigation = {
        service_id: {"services": {}, "articles": {}}
        for service_id in EXPECTED_SERVICES
    }
    field_by_role = {"child_service": "services", "article": "articles"}
    for destination in architecture.values():
        field = field_by_role.get(destination.page_role)
        if field is None or destination.service_id not in navigation:
            continue
        if destination.publication_status != "ready":
            continue
        if destination.parent_destination_id != f"{destination.service_id}-HUB":
            continue
        navigation[destination.service_id][field][destination.destination_id] = (
            destination.canonical_url
        )
    return navigation


EXPECTED_NAVIGATION = _expected_navigation()

EXPECTED_FROZEN_LINKS = {
    "S1": {
        "https://exp76.ru/category/drenazh-uchastka/",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
        "https://exp76.ru/category/avtopoliv-na-uchastke/",
        "https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
    },
    "S2": {"https://exp76.ru/category/avtopoliv-na-uchastke/"},
    "S3": {"https://exp76.ru/category/avtopoliv-na-uchastke/"},
    "S4": set(),
    "S5": {
        "https://exp76.ru/category/drenazh-uchastka/",
        "https://exp76.ru/category/osushenie-uchastka/",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
    },
    "S6": {"https://exp76.ru/category/drenazh-uchastka/"},
    "S7": set(),
    "S8": {
        "https://exp76.ru/category/drenazh-uchastka/",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
    },
    "S9": set(),
    "S10": {
        "https://exp76.ru/category/drenazh-uchastka/",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
    },
    "S11": set(),
    "S12": set(),
    "S13": set(),
    "S14": set(),
    "S15": set(),
}

UPLOADS = "https://exp76.ru/wp-content/uploads/"
GENERATED_CONTEXT = "https://exp76.ru/wp-content/themes/land76wp/generated/context/"
EXPECTED_IMAGE_POOL_FINGERPRINTS = {
    "S1": "47ee90773667711dbb7c4ef0a85d114bcef4be7400c2320c944f6debc6c084b9",
    "S2": "5f06b1d2a1005928d5802433693d8f4b1f8899e67190aa9f1f5b2c7d66e92bc8",
    "S3": "8c313a9f9cd627751b7c9fac506d32afe4eb758781b04fe64242ef7aa0af95ef",
    "S4": "d3cea0ec8fb29ea52e763cd6aea806b1176415ef49f7ae32d0091ae18f187efe",
    "S5": "e44dbc6e3be546d8f3f3b728d1d57d7763759b9847d6571d0b3b757dfba87fa8",
    "S6": "d8a73ac4abe2b57a9f63c3c33c3511473e8c9721fb044be9a14c6ffbc346de11",
    "S7": "17693781459f84ee7530524dc6a94a624a9ef0eb125be0a9cbc9ab89d6ca38a5",
    "S8": "715fd2b42be3dfee6ebd6a452e51279cd763f7773f9a1bd0fa415751e23b6b68",
    "S9": "5c50032e75e97e27ac8dced82a83d7baaf88d63777b935041685d4ccd162c3cd",
    "S10": "9f43a08e23dcb29a0da4da698a8fc8f3f80cc481476374e1e1b3a01578d33287",
    "S11": "5780f9b1f405a876904275d59fd2db6211febfeed16b31f149219209155553ad",
    "S12": "50161a9049bb724f942315264d230027710fc777f384bb1a9331b4f92afe9f1e",
    "S13": "417db9dc780facaed8f4f09d9e6579e0e67109bf9c42f5c0d2748fd640e02e17",
    "S14": "34577e131260239e17d65109f5ab233de4951be3bf2cc6fa349c47cca279a018",
    "S15": "91df33e932db98a4ed2ddda7ac04137aaf5c3e5abac6b22e46ae3f0f2698b729",
}

EXPECTED_FACT_PATHS = {
    "S1": {"pricing.body[0]", "pricing.calculator.note", "faq.items[4].question"},
    "S2": {"pricing.body[0]", "pricing.factors[2].text", "faq.items[2].answer"},
    "S3": set(),
    "S4": set(),
    "S5": set(),
    "S6": set(),
    "S7": set(),
    "S8": set(),
    "S9": set(),
    "S10": set(),
    "S11": set(),
    "S12": set(),
    "S13": set(),
    "S14": set(),
    "S15": set(),
}

LEGACY_RELATED_COUNTS = {
    "S1": 4,
    "S2": 3,
    "S3": 3,
    "S4": 3,
    "S5": 3,
    "S6": 3,
    "S7": 3,
    "S8": 4,
    "S9": 4,
    "S10": 4,
    "S11": 4,
    "S12": 4,
    "S13": 3,
    "S14": 3,
    "S15": 3,
}


def _text_paths(value: object, path: str = "") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else str(key)
            result.extend(_text_paths(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.extend(_text_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        result.append((path, value))
    return result


def _legacy_projection(service: dict[str, object]) -> dict[str, object]:
    """Reconstruct the exact pre-hub payload while ignoring Task 6 additions."""
    payload = copy.deepcopy(service)
    service_id = str(payload["service_id"])
    payload["schema_version"] = 1
    payload["services"] = payload.pop("scope")
    payload["related_links"]["items"] = payload["related_links"]["items"][
        : LEGACY_RELATED_COUNTS[service_id]
    ]
    for field in (
        "page_key",
        "page_type",
        "articles",
        "fact_evidence",
        "evidence_gaps",
        "release_id",
        "release_status",
        "rendered_sha256",
    ):
        payload.pop(field, None)
    return payload


def _without_presentation_metadata(value: object) -> object:
    """Keep legacy copy baselines independent from intentionally replaceable media."""
    if isinstance(value, dict):
        return {
            key: _without_presentation_metadata(item)
            for key, item in value.items()
            if key not in {"image", "gallery"}
        }
    if isinstance(value, list):
        return [_without_presentation_metadata(item) for item in value]
    return value


def _legacy_text_projection(service: dict[str, object]) -> dict[str, object]:
    """Reconstruct frozen legacy copy without image URLs, alt text or captions."""
    projection = _without_presentation_metadata(_legacy_projection(service))
    if not isinstance(projection, dict):
        raise AssertionError("legacy text projection must remain an object")
    return projection


def _payload_fingerprint(payload: dict[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _url_set_fingerprint(urls: set[str]) -> str:
    """Keep the exact audited image pool contract compact but fail closed."""
    return hashlib.sha256("\n".join(sorted(urls)).encode("utf-8")).hexdigest()


def _embedded_image_urls(value: object) -> set[str]:
    urls: set[str] = set()
    if isinstance(value, dict):
        url = value.get("url")
        alt = value.get("alt")
        if (
            isinstance(url, str)
            and url.startswith((UPLOADS, GENERATED_CONTEXT))
            and isinstance(alt, str)
        ):
            urls.add(url)
        for item in value.values():
            urls.update(_embedded_image_urls(item))
    elif isinstance(value, list):
        for item in value:
            urls.update(_embedded_image_urls(item))
    return urls


def schema_two_fixture(service: dict[str, object]) -> dict[str, object]:
    """Return a complete 15-owner v2 fixture aligned with the current ledger."""
    payload = copy.deepcopy(service)
    service_id = str(payload["service_id"])
    architecture = load_page_architecture(ARCHITECTURE_PATH)
    if payload.get("schema_version") == 1:
        payload["scope"] = payload.pop("services")
    elif payload.get("schema_version") != 2:
        raise AssertionError(f"unsupported fixture schema for {service_id}")

    payload["schema_version"] = 2
    payload["release_id"] = RELEASE_ID
    payload["release_status"] = "draft"
    payload["page_key"] = f"{service_id}-HUB"
    payload["page_type"] = "hub"
    image = copy.deepcopy(payload["hero"]["image"])

    children = sorted(
        (
            destination
            for destination in architecture.values()
            if destination.service_id == service_id
            and destination.parent_destination_id == payload["page_key"]
            and destination.page_role == "child_service"
        ),
        key=lambda destination: destination.destination_id,
    )
    articles = sorted(
        (
            destination
            for destination in architecture.values()
            if destination.service_id == service_id
            and destination.parent_destination_id == payload["page_key"]
            and destination.page_role == "article"
        ),
        key=lambda destination: destination.destination_id,
    )
    payload["services"] = {
        "heading": f"Коммерческие направления {service_id}",
        "lead": f"Коммерческие страницы владельца {service_id} создаются только для направлений, закреплённых в архитектуре релиза.",
        "items": [
            {
                "page_key": destination.destination_id,
                "url": destination.canonical_url,
                "title": f"Направление {destination.destination_id}",
                "text": f"Карточка {destination.destination_id} ведёт на единственную коммерческую страницу, которой назначен этот поисковый кластер.",
                "image": copy.deepcopy(image),
            }
            for destination in children
        ],
    }
    payload["articles"] = {
        "heading": f"Материалы по теме {service_id}",
        "lead": f"Информационные материалы владельца {service_id} отделены от коммерческой страницы и следуют утверждённой архитектуре.",
        "items": [
            {
                "page_key": destination.destination_id,
                "url": destination.canonical_url,
                "title": f"Материал {destination.destination_id}",
                "text": f"Статья {destination.destination_id} отвечает на самостоятельный информационный запрос и возвращает читателя к основной услуге.",
                "image": copy.deepcopy(image),
            }
            for destination in articles
        ],
    }
    if service_id == "S5" and "Раздел относится к планировке территории." not in str(
        payload["related_links"]["items"][2]["text"]
    ):
        payload["related_links"]["items"][2]["text"] += " Раздел относится к планировке территории."
    payload["evidence_gaps"] = [
        {
            "kind": "nonready_destination",
            "page_key": destination.destination_id,
            "status": destination.publication_status,
        }
        for destination in children + articles
        if destination.publication_status != "ready"
    ]
    payload["fact_evidence"] = []
    payload["fact_evidence"] = [
        {
            "path": path,
            "claim_type": claim_type,
            "claim": claim,
            "source_ref": "fixture:preserved-v1-evidence",
        }
        for path, text in _text_paths(payload)
        for claim_type, claim in numeric_fact_claims(text)
    ]
    payload["rendered_sha256"] = hashlib.sha256(
        render_service(payload).encode("utf-8")
    ).hexdigest()
    return payload


def write_schema_two_sources(source_dir: Path) -> list[dict[str, object]]:
    source_dir.mkdir(parents=True, exist_ok=True)
    services = [
        schema_two_fixture(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(HUB_SOURCE_DIR.glob("*.json"))
    ]
    if len(services) != HUB_COUNT:
        raise AssertionError(
            f"fixture source must contain {HUB_COUNT} hubs, found {len(services)}"
        )
    for service in services:
        path = source_dir / f'{service["service_id"]}.json'
        path.write_text(
            json.dumps(service, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    write_fixture_release_manifest(source_dir.parent / "release-manifest.json")
    return services


def write_fixture_release_manifest(path: Path) -> None:
    """Write a strict draft manifest for sync mechanics tests only."""
    architecture = load_page_architecture(ARCHITECTURE_PATH)
    managed_roles = {"hub", "child_service", "article"}
    managed_pages: list[dict[str, object]] = []
    preserved_pages: list[dict[str, object]] = []
    for destination in sorted(
        architecture.values(), key=lambda item: item.destination_id
    ):
        row: dict[str, object] = {
            "page_key": destination.destination_id,
            "service_id": destination.service_id,
            "page_role": destination.page_role,
            "parent_page_key": destination.parent_destination_id,
            "canonical": destination.canonical_url,
            "architecture_status": destination.publication_status,
        }
        if destination.page_role in managed_roles:
            row["content_status"] = "content_pending"
            managed_pages.append(row)
        else:
            preserved_pages.append(row)
    payload = {
        "schema_version": 1,
        "release_id": RELEASE_ID,
        "release_status": "draft",
        "managed_pages": managed_pages,
        "preserved_pages": preserved_pages,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sync_fixture_services(
    source_dir: Path,
    target_dir: Path,
    *,
    allow_draft: bool = False,
    _replace: Callable[[os.PathLike[str], os.PathLike[str]], None] = os.replace,
) -> dict[str, int]:
    """Run sync against the complete fixture manifest, not repository state."""
    return sync_services(
        source_dir,
        target_dir,
        allow_draft=allow_draft,
        release_manifest_path=source_dir.parent / "release-manifest.json",
        _replace=_replace,
    )


def directory_snapshot(path: Path) -> dict[str, bytes]:
    return {
        file.relative_to(path).as_posix(): file.read_bytes()
        for file in path.rglob("*")
        if file.is_file()
    }


class ServiceV2Test(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "tools.service_v2", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def load_services(self) -> list[dict[str, object]]:
        self.assertTrue(DATA_DIR.is_dir(), "production service-v2 data directory is missing")
        files = sorted(DATA_DIR.glob("*.json"))
        self.assertTrue(files, "production service-v2 data directory is empty")
        return [json.loads(path.read_text(encoding="utf-8")) for path in files]

    def test_real_payloads_pass_the_production_contract(self) -> None:
        """Catches incomplete copy, placeholders, unsafe owners and missing SEO fields."""
        result = self.run_cli("validate", str(DATA_DIR))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["services"], HUB_COUNT)
        self.assertEqual(summary["errors"], 0)
        self.assertGreaterEqual(summary["words"], HUB_COUNT * 900)

    def test_payloads_keep_all_fifteen_existing_url_owners(self) -> None:
        """Catches accidental URL, ID or canonical changes that would lose page history."""
        services = self.load_services()
        actual = {
            str(service["service_id"]): (int(service["page_id"]), str(service["slug"]))
            for service in services
        }

        self.assertEqual(actual, EXPECTED_SERVICES)
        for service in services:
            slug = str(service["slug"])
            self.assertEqual(service["canonical"], f"https://exp76.ru/services/{slug}/")
            self.assertEqual(service["parent_id"], 921)
            self.assertEqual(service["wp_template"], "servicepost.php")

    def test_only_verified_cases_are_presented_as_completed_work(self) -> None:
        """Catches invented portfolio proof on services that have no confirmed case."""
        services = self.load_services()
        actual = {
            str(service["service_id"]): [int(case["page_id"]) for case in service["proof"]["cases"]]
            for service in services
        }

        self.assertEqual(actual, EXPECTED_CASES)

    def test_seo_titles_descriptions_and_h1_are_unique(self) -> None:
        """Catches duplicate snippets or generic H1 values across all 15 owners."""
        services = self.load_services()
        titles = [str(service["seo"]["title"]) for service in services]
        descriptions = [str(service["seo"]["description"]) for service in services]
        h1_values = [str(service["hero"]["title"]) for service in services]

        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertEqual(len(h1_values), len(set(h1_values)))
        for title in titles:
            self.assertGreaterEqual(len(title), 45)
            self.assertLessEqual(len(title), 85)
        for description in descriptions:
            self.assertGreaterEqual(len(description), 110)
            self.assertLessEqual(len(description), 180)
        for service in services:
            self.assertGreaterEqual(count_words(service), 900, str(service["service_id"]))

    def test_contract_rejects_hotlinked_production_images(self) -> None:
        """Catches third-party image dependencies and accidental stock-photo hotlinking."""
        service = copy.deepcopy(self.load_services()[0])
        service["hero"]["image"]["url"] = "https://example.com/unverified-image.webp"

        with self.assertRaisesRegex(ContractError, "must stay on exp76.ru"):
            validate_service_v2(
                service,
                load_page_architecture(ARCHITECTURE_PATH),
                load_case_catalog(CASE_CATALOG_PATH),
            )

    def test_build_outputs_complete_accessible_html_for_every_service(self) -> None:
        """Catches empty production sections, broken form fallback and image accessibility regressions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli("build", str(DATA_DIR), temp_dir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            rendered = sorted(Path(temp_dir).glob("*.html"))
            self.assertEqual(len(rendered), HUB_COUNT)
            for path in rendered:
                html = path.read_text(encoding="utf-8")
                self.assertEqual(html.count("<h1"), 1, path.name)
                self.assertGreaterEqual(html.count("<h2"), 7, path.name)
                self.assertGreaterEqual(html.count('class="service-v2__faq-item"'), 5, path.name)
                self.assertIn('<form class="form service-v2__form" method="post"', html)
                self.assertIn('action="/server.php"', html)
                self.assertIn('name="form_version" value="service-v2"', html)
                self.assertIn('name="source"', html)
                self.assertIn('name="consent" value="1"', html)
                self.assertNotIn('alt=""', html)
                self.assertNotIn('href="#"', html)
                self.assertNotIn("privacy.html", html)
                self.assertNotIn("consent.html", html)
                self.assertNotIn("Lorem", html)
                self.assertNotIn("TODO", html)
                self.assertNotIn("TBD", html)
                self.assertNotIn("{{", html)
                for target in set(re.findall(r'href="(#service-v2-[^"]+)"', html)):
                    self.assertIn(f'id="{target[1:]}"', html, f"broken anchor {target} in {path.name}")

    def test_committed_fragments_match_validated_payloads(self) -> None:
        """Catches stale production HTML after a content or renderer change."""
        rendered_dir = DATA_DIR / "rendered"
        self.assertEqual(len(list(rendered_dir.glob("*.html"))), HUB_COUNT)

        services = {str(item["slug"]): item for item in load_services_auto(DATA_DIR)}
        for json_path in sorted(DATA_DIR.glob("*.json")):
            service = services[json_path.stem]
            actual = (rendered_dir / f"{service['slug']}.html").read_text(encoding="utf-8")
            self.assertEqual(actual, render_service(service), json_path.name)

    def test_theme_routes_only_approved_pages_through_service_v2(self) -> None:
        """Catches a broad template switch that would alter unrelated legacy pages."""
        helper = THEME / "inc" / "service-v2.php"
        template = THEME / "inc" / "service-v2-template.php"
        servicepost = THEME / "servicepost.php"

        self.assertTrue(helper.is_file())
        self.assertTrue(template.is_file())
        helper_source = helper.read_text(encoding="utf-8")
        template_source = template.read_text(encoding="utf-8")
        router_source = servicepost.read_text(encoding="utf-8")
        self.assertIn("land76_service_v2_current", router_source)
        self.assertIn("service-v2-template.php", router_source)
        self.assertIn("page_id", helper_source)
        self.assertIn("slug", helper_source)
        self.assertNotIn("wp_delete_post", helper_source + template_source)
        self.assertNotIn("wp_update_post", helper_source + template_source)

    def test_form_legal_links_have_complete_theme_routes(self) -> None:
        """Catches production forms linking to the two legacy 404 responses."""
        helper = THEME / "inc" / "legal-pages.php"
        template = THEME / "inc" / "legal-page-template.php"

        self.assertTrue(helper.is_file())
        self.assertTrue(template.is_file())
        helper_source = helper.read_text(encoding="utf-8")
        template_source = template.read_text(encoding="utf-8")
        self.assertIn("'privacy'", helper_source)
        self.assertIn("'consent'", helper_source)
        self.assertIn("Политика конфиденциальности", template_source)
        self.assertIn("Согласие на обработку персональных данных", template_source)
        self.assertIn("info@exp76.ru", template_source)
        self.assertGreaterEqual(count_words(template_source), 500)
        for placeholder in ("Lorem", "TODO", "TBD", "{{", "здесь будет"):
            self.assertNotIn(placeholder, template_source)

    def test_legacy_legal_links_redirect_to_canonical_documents(self) -> None:
        """Catches old relative privacy.html links resolving to nested 404 pages."""
        helper_source = (THEME / "inc" / "legal-pages.php").read_text(encoding="utf-8")

        self.assertIn("privacy.html", helper_source)
        self.assertIn("consent.html", helper_source)
        self.assertIn("wp_safe_redirect", helper_source)
        self.assertIn("301", helper_source)

    def test_lead_handler_validates_requests_and_mail_delivery(self) -> None:
        """Catches false success responses and unrecorded consent/source data."""
        handler_source = (ROOT / "ftp_dump_minimal" / "server.php").read_text(encoding="utf-8")

        self.assertIn("REQUEST_METHOD", handler_source)
        for error_code, status in (
            ("method_not_allowed", 405),
            ("consent_required", 422),
            ("invalid_phone", 422),
        ):
            self.assertRegex(
                handler_source,
                rf"land76_contact_error\('{error_code}',[^;]+,\s*{status}\);",
            )
        self.assertIn("wp_verify_nonce", handler_source)
        self.assertIn("isset($_POST['consent'])", handler_source)
        self.assertIn("land76_contact_post_text('source', 512)", handler_source)
        self.assertIn("$mail_sent = wp_mail(", handler_source)
        self.assertIn("if (!$mail_sent)", handler_source)
        mail_failure = handler_source.index("if (!$mail_sent)")
        self.assertIn("'code' => 'mail_failed'", handler_source[mail_failure:])
        self.assertIn("), 500", handler_source[mail_failure:])


class SchemaTwoProductionDataTest(unittest.TestCase):
    def load_sources(self) -> list[dict[str, object]]:
        files = sorted(HUB_SOURCE_DIR.glob("*.json"))
        self.assertEqual(
            HUB_COUNT,
            len(files),
            "canonical hub source must contain every S1-S15 owner",
        )
        return [json.loads(path.read_text(encoding="utf-8")) for path in files]

    def test_release_manifest_matches_the_complete_architecture(self) -> None:
        architecture = load_page_architecture(ARCHITECTURE_PATH)
        manifest = load_release_manifest(RELEASE_MANIFEST_PATH)

        self.assertEqual([], validate_release_manifest(manifest, architecture))

    def test_canonical_hubs_bind_exact_legacy_owners_and_content(self) -> None:
        services = self.load_sources()
        actual_owners = {
            str(service["service_id"]): (
                int(service["page_id"]),
                int(service["parent_id"]),
                str(service["wp_template"]),
                str(service["slug"]),
                str(service["canonical"]),
            )
            for service in services
        }
        expected_owners = {
            service_id: (
                page_id,
                921,
                "servicepost.php",
                slug,
                f"https://exp76.ru/services/{slug}/",
            )
            for service_id, (page_id, slug) in EXPECTED_SERVICES.items()
        }
        self.assertEqual(expected_owners, actual_owners)

        total_words = 0
        total_scope_cards = 0
        for service in services:
            service_id = str(service["service_id"])
            self.assertEqual(2, service["schema_version"])
            self.assertEqual(f"{service_id}-HUB", service["page_key"])
            self.assertEqual("hub", service["page_type"])
            self.assertEqual(RELEASE_ID, service["release_id"])
            self.assertEqual("ready", service["release_status"])
            self.assertEqual([], service["evidence_gaps"])
            scope_items = service["scope"]["items"]
            self.assertEqual(EXPECTED_SCOPE_COUNTS[service_id], len(scope_items))
            self.assertTrue(
                all("url" not in item and "page_key" not in item for item in scope_items)
            )
            legacy_text = _legacy_text_projection(service)
            words = count_words(legacy_text)
            self.assertEqual(EXPECTED_LEGACY_TEXT_WORDS[service_id], words)
            self.assertEqual(
                EXPECTED_LEGACY_TEXT_FINGERPRINTS[service_id],
                _payload_fingerprint(legacy_text),
            )
            total_words += words
            total_scope_cards += len(scope_items)
        self.assertEqual(sum(EXPECTED_LEGACY_TEXT_WORDS.values()), total_words)
        self.assertEqual(SCOPE_CARD_COUNT, total_scope_cards)

    def test_every_hub_has_the_exact_child_and_article_destinations_once(self) -> None:
        services = self.load_sources()
        navigation_count = 0
        for service in services:
            service_id = str(service["service_id"])
            rendered = render_service(service)
            for field in ("services", "articles"):
                expected = EXPECTED_NAVIGATION[service_id][field]
                items = service[field]["items"]
                actual = {str(item["page_key"]): str(item["url"]) for item in items}
                self.assertEqual(expected, actual)
                self.assertEqual(len(actual), len(items), f"duplicate {field} in {service_id}")
                for item in items:
                    self.assertNotEqual(item["page_key"], item["title"])
                    self.assertGreaterEqual(len(str(item["text"]).strip()), 45)
                    self.assertEqual(1, rendered.count(f'href="{item["url"]}"'))
                navigation_count += len(items)
        self.assertEqual(
            CHILD_SERVICE_COUNT,
            sum(len(item["services"]) for item in EXPECTED_NAVIGATION.values()),
        )
        self.assertEqual(
            ARTICLE_COUNT,
            sum(len(item["articles"]) for item in EXPECTED_NAVIGATION.values()),
        )
        self.assertEqual(CHILD_SERVICE_COUNT + ARTICLE_COUNT, navigation_count)

    def test_cases_images_frozen_links_and_draft_gaps_are_exact(self) -> None:
        services = self.load_sources()
        frozen_universe = set().union(*EXPECTED_FROZEN_LINKS.values())
        architecture = load_page_architecture(ARCHITECTURE_PATH)
        for service in services:
            service_id = str(service["service_id"])
            self.assertEqual(
                EXPECTED_CASES[service_id],
                [int(case["page_id"]) for case in service["proof"]["cases"]],
            )
            self.assertEqual(
                EXPECTED_IMAGE_POOL_FINGERPRINTS[service_id],
                _url_set_fingerprint(_embedded_image_urls(service)),
            )
            related_urls = {
                str(item["url"]) for item in service["related_links"]["items"]
            }
            self.assertEqual(
                EXPECTED_FROZEN_LINKS[service_id],
                related_urls & frozen_universe,
            )

            expected_gaps = {
                (
                    "nonready_destination",
                    destination_id,
                    architecture[destination_id].publication_status,
                )
                for field in ("services", "articles")
                for destination_id in EXPECTED_NAVIGATION[service_id][field]
                if architecture[destination_id].publication_status != "ready"
            }
            actual_gaps = {
                (str(gap["kind"]), str(gap["page_key"]), str(gap["status"]))
                for gap in service["evidence_gaps"]
            }
            self.assertEqual(expected_gaps, actual_gaps)

    def test_visible_hub_never_repeats_an_image_across_sections(self) -> None:
        """Catches one photo being rendered more than once anywhere on a hub."""
        for service in self.load_sources():
            service_id = str(service["service_id"])
            images = [("hero", str(service["hero"]["image"]["url"]))]
            for section_name in ("scope", "services", "articles"):
                images.extend(
                    (f"{section_name}[{index}]", str(item["image"]["url"]))
                    for index, item in enumerate(service[section_name]["items"])
                )
            images.extend(
                (f"proof.cases[{index}]", str(item["image"]["url"]))
                for index, item in enumerate(service["proof"]["cases"])
            )
            images.extend(
                (f"proof.gallery[{index}]", str(item["url"]))
                for index, item in enumerate(service["proof"]["gallery"])
            )

            occurrences: dict[str, list[str]] = {}
            for location, url in images:
                identity = re.sub(
                    r"-\d+x\d+(?=\.[A-Za-z0-9]+(?:[?#]|$))",
                    "",
                    url,
                )
                occurrences.setdefault(identity, []).append(location)
            duplicates = {
                identity: locations
                for identity, locations in occurrences.items()
                if len(locations) > 1
            }
            self.assertEqual({}, duplicates, f"{service_id} repeats visible images")

    def test_generated_context_photo_is_not_reused_by_different_hubs(self) -> None:
        """Prevents catalog browsing from showing the same generated scene on services."""
        occurrences: dict[str, list[str]] = {}
        for service in self.load_sources():
            service_id = str(service["service_id"])
            images = [("hero", str(service["hero"]["image"]["url"]))]
            for section_name in ("scope", "services", "articles"):
                images.extend(
                    (f"{section_name}[{index}]", str(item["image"]["url"]))
                    for index, item in enumerate(service[section_name]["items"])
                )
            for location, url in images:
                if url.startswith(GENERATED_CONTEXT):
                    occurrences.setdefault(url, []).append(f"{service_id}.{location}")

        reused = {
            url: locations
            for url, locations in occurrences.items()
            if len({location.split(".", 1)[0] for location in locations}) > 1
        }
        self.assertEqual({}, reused)

    def test_numeric_claims_have_exact_main_js_evidence(self) -> None:
        source_refs = {
            "S1": "ftp_dump_minimal/wp-content/themes/land76wp/js/main.js#tab-project-total",
            "S2": "ftp_dump_minimal/wp-content/themes/land76wp/js/main.js#tab-grass-total",
        }
        for service in self.load_sources():
            service_id = str(service["service_id"])
            evidence = service["fact_evidence"]
            self.assertEqual(EXPECTED_FACT_PATHS[service_id], {item["path"] for item in evidence})
            if service_id in source_refs:
                self.assertEqual({source_refs[service_id]}, {item["source_ref"] for item in evidence})
            else:
                self.assertEqual([], evidence)

            expected_claims = {
                (path, claim_type, claim)
                for path, text in _text_paths(service)
                if not path.startswith("fact_evidence[")
                for claim_type, claim in numeric_fact_claims(text)
            }
            actual_claims = {
                (str(item["path"]), str(item["claim_type"]), str(item["claim"]))
                for item in evidence
            }
            self.assertEqual(expected_claims, actual_claims)

    def test_synced_json_html_and_bound_sha256_are_identical(self) -> None:
        source_services = {
            str(service["service_id"]): service for service in self.load_sources()
        }
        installed_files = sorted(DATA_DIR.glob("*.json"))
        self.assertEqual(HUB_COUNT, len(installed_files))
        for installed_path in installed_files:
            installed = json.loads(installed_path.read_text(encoding="utf-8"))
            service_id = str(installed["service_id"])
            self.assertEqual(source_services[service_id], installed)
            rendered_bytes = (DATA_DIR / "rendered" / f'{installed["slug"]}.html').read_bytes()
            self.assertEqual(render_service(installed).encode("utf-8"), rendered_bytes)
            self.assertRegex(str(installed["rendered_sha256"]), r"^[0-9a-f]{64}$")
            self.assertEqual(
                installed["rendered_sha256"], hashlib.sha256(rendered_bytes).hexdigest()
            )

    def test_generated_hub_sources_and_fragments_are_checkout_stable_lf(self) -> None:
        generated_paths = [
            *sorted(HUB_SOURCE_DIR.glob("*.json")),
            *sorted(DATA_DIR.glob("*.json")),
            *sorted((DATA_DIR / "rendered").glob("*.html")),
        ]
        relative_paths = [path.relative_to(ROOT).as_posix() for path in generated_paths]
        result = subprocess.run(
            ["git", "check-attr", "eol", "--", *relative_paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        attributes = {
            line.rsplit(": eol: ", 1)[0]: line.rsplit(": eol: ", 1)[1]
            for line in result.stdout.splitlines()
            if ": eol: " in line
        }
        self.assertEqual(set(relative_paths), set(attributes))
        self.assertEqual({"lf"}, set(attributes.values()))
        for path in generated_paths:
            self.assertNotIn(b"\r\n", path.read_bytes(), str(path))

    def test_renderer_uses_semantic_accessible_links_and_omits_empty_proof(self) -> None:
        linked_cards = 0
        scope_cards = 0
        for service in self.load_sources():
            service_id = str(service["service_id"])
            rendered = render_service(service)
            self.assertIn('data-schema-version="2"', rendered)
            self.assertNotIn("onclick=", rendered.casefold())
            scope_cards += rendered.count('<article class="service-v2__card">')
            linked_cards += rendered.count(
                '<a class="service-v2__card service-v2__card--linked"'
            )
            proof = service["proof"]
            if proof["cases"] or proof["gallery"]:
                self.assertIn('id="service-v2-cases"', rendered)
                for case in proof["cases"]:
                    self.assertIn(f'href="{case["url"]}"', rendered)
                for image in proof["gallery"]:
                    self.assertIn(str(image["caption"]), rendered)
            else:
                self.assertNotIn('id="service-v2-cases"', rendered)
                self.assertNotIn('href="#service-v2-cases"', rendered)
        self.assertEqual(SCOPE_CARD_COUNT, scope_cards)
        self.assertEqual(CHILD_SERVICE_COUNT + ARTICLE_COUNT, linked_cards)

        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")
        self.assertIn(".service-v2__card--linked:focus-visible", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertRegex(css, r"@media\s*\(max-width:")

    def test_service_v2_preserves_the_legacy_light_section_background_rhythm(self) -> None:
        """Catches dark or solid-green full-width bands returning to service hubs."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")

        def declarations(selector: str) -> str:
            match = re.search(
                rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}",
                css,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(match, selector)
            return str(match.group("body"))

        plain = declarations(".service-v2__section--plain")
        soft = declarations(".service-v2__section--soft")
        pricing = declarations(".service-v2__section--dark")
        cta = declarations(".service-v2__cta")
        cta_inner = declarations(".service-v2__cta-inner")
        self.assertRegex(plain, r"background:\s*#fff(?:fff)?\s*;")
        self.assertIn("url(../img/sb5.png)", soft)
        self.assertNotIn("#0b4f12", pricing.casefold())
        self.assertNotIn("#0a9215", cta.casefold())
        self.assertRegex(cta_inner, r"background:\s*transparent\s*;")
        self.assertRegex(plain, r"border-top:\s*0\s*;")
        self.assertRegex(soft, r"border-top:\s*0\s*;")
        form = declarations(".service-v2__form-wrapper")
        self.assertRegex(form, r"background:\s*#fff(?:fff)?\s*;")

    def test_service_v2_full_width_sections_alternate_plain_and_texture(self) -> None:
        """Prevents several identical section backgrounds being stacked together."""
        for service in self.load_sources():
            rendered = render_service(service)
            section_classes = re.findall(
                r'<section class="([^"]*\bservice-v2__section\b[^"]*)"',
                rendered,
            )
            variants: list[str] = []
            for class_names in section_classes:
                present = [
                    variant
                    for variant in ("service-v2__section--plain", "service-v2__section--soft")
                    if variant in class_names.split()
                ]
                self.assertEqual([present[0]] if present else [], present, class_names)
                self.assertEqual(1, len(present), class_names)
                variants.append(present[0])
            self.assertGreaterEqual(len(variants), 8)
            self.assertTrue(
                all(left != right for left, right in zip(variants, variants[1:])),
                f"{service['service_id']} repeats a section background: {variants}",
            )

    def test_service_v2_hero_breadcrumbs_stay_in_normal_flow(self) -> None:
        """Prevents breadcrumbs from overlapping hero actions on desktop."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")

        match = re.search(
            r"\.service-v2__breadcrumbs\s*\{(?P<body>[^}]+)\}",
            css,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(match)
        declarations = str(match.group("body"))
        self.assertNotRegex(declarations, r"position:\s*absolute")
        self.assertRegex(declarations, r"margin-top:\s*[1-9]")

    def test_service_v2_box_padding_never_overrides_the_global_wrapper_gutter(self) -> None:
        """Keeps GEO, FAQ and CTA boxes inside the same 1200px page grid."""
        for service in self.load_sources():
            rendered = render_service(service)
            for inner_class in (
                "service-v2__geo-inner",
                "service-v2__faq",
                "service-v2__cta-inner",
            ):
                self.assertNotIn(f'class="wrapper {inner_class}"', rendered)
                self.assertIn(
                    f'<div class="wrapper"><div class="{inner_class}">',
                    rendered,
                )

    def test_service_v2_primary_button_meets_text_contrast_on_light_sections(self) -> None:
        """Prevents a translucent orange CTA from making white labels unreadable."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")
        match = re.search(r"\.service-v2__button\s*\{(?P<body>[^}]+)\}", css)
        self.assertIsNotNone(match)
        body = str(match.group("body"))
        background_variable = re.search(
            r"--service-v2-orange:\s*(#[0-9a-fA-F]{6})\s*;",
            css,
        )
        foreground = re.search(r"color:\s*(#[0-9a-fA-F]{6})\s*;", body)
        self.assertIn("background: var(--service-v2-orange)", body)
        self.assertIsNotNone(background_variable, css[:300])
        self.assertIsNotNone(foreground, body)

        def luminance(value: str) -> float:
            channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        assert background_variable is not None and foreground is not None
        bright, dark = sorted(
            (
                luminance(background_variable.group(1)),
                luminance(foreground.group(1)),
            ),
            reverse=True,
        )
        self.assertGreaterEqual((bright + 0.05) / (dark + 0.05), 3.0)

    def test_service_v2_reuses_site_orange_and_anchor_buttons_stay_white(self) -> None:
        """Catches off-brand CTA colors and generic link styles darkening labels."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")
        shared = (THEME / "css" / "styles.css").read_text(encoding="utf-8")

        orange = re.search(r"--service-v2-orange:\s*(#[0-9a-fA-F]{6})", css)
        header_cta = re.search(
            r"\.header__cta\s*\{(?P<body>[^}]+)\}",
            shared,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(orange)
        self.assertIsNotNone(header_cta)
        assert orange is not None and header_cta is not None
        shared_orange = re.search(
            r"background:\s*(#[0-9a-fA-F]{6})\s*;",
            header_cta.group("body"),
        )
        self.assertIsNotNone(shared_orange)
        assert shared_orange is not None
        self.assertEqual(shared_orange.group(1).lower(), orange.group(1).lower())
        self.assertRegex(
            css,
            r"\.service-v2\s+a\.service-v2__button\s*\{[^}]*color:\s*#fff(?:fff)?\s*;",
        )
        self.assertRegex(
            css,
            r"\.service-v2__form\s+\.form__btn\s*\{[^}]*"
            r"background:\s*var\(--service-v2-green\)",
        )

    def test_service_v2_primary_copy_remains_readable_on_textured_sections(self) -> None:
        """Catches pale gray body copy being reused as primary reading text."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")
        muted = re.search(r"--service-v2-muted:\s*(#[0-9a-fA-F]{6})", css)
        self.assertIsNotNone(muted)
        assert muted is not None

        def luminance(value: str) -> float:
            channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        contrast = (1.0 + 0.05) / (luminance(muted.group(1)) + 0.05)
        self.assertGreaterEqual(contrast, 7.0)

    def test_service_v2_avoids_nested_surfaces_and_vertical_card_stripes(self) -> None:
        """Keeps hub sections flat and uses one accent edge per standalone card."""
        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")

        def declarations(selector: str) -> str:
            match = re.search(
                rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]+)\}}",
                css,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(match, selector)
            assert match is not None
            return str(match.group("body"))

        highlights = declarations(
            ".service-v2__highlights article,\n.service-v2__factors article"
        )
        related = declarations(".service-v2__related a")
        geo = declarations(".service-v2__geo-inner")
        cta = declarations(".service-v2__cta-inner")

        for selector, body in (
            ("highlights", highlights),
            ("related", related),
            ("geo", geo),
        ):
            self.assertRegex(body, r"border-left:\s*0\s*;", selector)
        self.assertRegex(cta, r"background:\s*transparent\s*;")
        self.assertRegex(cta, r"box-shadow:\s*none\s*;")

    def test_php_loader_fails_closed_and_templates_cached_verified_bytes(self) -> None:
        helper = (THEME / "inc" / "service-v2.php").read_text(encoding="utf-8")
        template = (THEME / "inc" / "service-v2-template.php").read_text(
            encoding="utf-8"
        )
        self.assertIn("is_readable($css_path)", helper)
        self.assertIn("file_get_contents($rendered_path)", helper)
        self.assertIn("hash('sha256', $rendered_html)", helper)
        self.assertIn("hash_equals(", helper)
        self.assertIn("data-schema-version=\"2\"", helper)
        self.assertIn("$schema_version === 1", helper)
        self.assertIn("strpos($rendered_html, 'data-schema-version=\"2\"')", helper)
        self.assertIn("$payload['release_status'] === 'ready'", helper)
        self.assertIn("$payload['_rendered_html']", helper)
        self.assertNotIn("readfile", template)
        self.assertIn("$service_v2['_rendered_html']", template)

    def test_php_loader_binds_v2_payload_and_root_to_the_exact_page_owner(self) -> None:
        attacker = copy.deepcopy(
            next(
                service
                for service in self.load_sources()
                if service["service_id"] == "S2"
            )
        )
        s1_page_id, s1_slug = EXPECTED_SERVICES["S1"]
        attacker.update(
            page_id=s1_page_id,
            slug=s1_slug,
            canonical=f"https://exp76.ru/services/{s1_slug}/",
            release_status="ready",
        )
        attacker_html = render_service(attacker)
        attacker["rendered_sha256"] = hashlib.sha256(
            attacker_html.encode("utf-8")
        ).hexdigest()

        self.assertEqual("S2-HUB", attacker["page_key"])
        self.assertIn('data-service-id="S2" data-schema-version="2"', attacker_html)
        self.assertEqual(
            attacker["rendered_sha256"],
            hashlib.sha256(attacker_html.encode("utf-8")).hexdigest(),
        )

        helper = (THEME / "inc" / "service-v2.php").read_text(encoding="utf-8")
        for service_id, (page_id, slug) in EXPECTED_SERVICES.items():
            self.assertIn(
                f"{page_id} => array('slug' => '{slug}', 'service_id' => '{service_id}')",
                helper,
            )
        self.assertIn("$payload['service_id'] === $expected_service_id", helper)
        self.assertIn("$payload['page_key'] === $expected_service_id . '-HUB'", helper)
        self.assertIn("strpos($rendered_html, $expected_root_marker) !== 0", helper)

    def test_php_loader_binds_legacy_service_id_in_the_common_owner_gate(self) -> None:
        s2 = next(
            service for service in self.load_sources() if service["service_id"] == "S2"
        )
        attacker = _legacy_projection(s2)
        s1_page_id, s1_slug = EXPECTED_SERVICES["S1"]
        attacker.update(
            page_id=s1_page_id,
            slug=s1_slug,
            canonical=f"https://exp76.ru/services/{s1_slug}/",
        )
        attacker_html = render_service(attacker).replace(
            'data-service-id="S2"', 'data-service-id="S1"', 1
        )

        self.assertEqual("S2", attacker["service_id"])
        self.assertTrue(attacker_html.startswith('<div class="service-v2" data-service-id="S1"'))
        helper = (THEME / "inc" / "service-v2.php").read_text(encoding="utf-8")
        common_owner_gate = helper.split("$schema_version =", 1)[0]
        self.assertIn("$payload['service_id']", common_owner_gate)
        self.assertIn(
            "$payload['service_id'] === $expected_service_id", common_owner_gate
        )


class SchemaTwoSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.architecture = load_page_architecture(ARCHITECTURE_PATH)
        cls.cases = load_case_catalog(CASE_CATALOG_PATH)
        cls.service_seeds = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(HUB_SOURCE_DIR.glob("*.json"))
        ]
        if len(cls.service_seeds) != HUB_COUNT:
            raise AssertionError(
                f"sync fixtures require {HUB_COUNT} hub seeds, found {len(cls.service_seeds)}"
            )

    def test_schema_two_preserves_descriptive_scope_and_renders_linked_cards(self) -> None:
        service = schema_two_fixture(self.service_seeds[0])

        validate_service_v2(service, self.architecture, self.cases)
        rendered = render_service(service)

        scope_title = service["scope"]["items"][0]["title"]
        child = service["services"]["items"][0]
        article = service["articles"]["items"][0]
        self.assertIn(f'<article class="service-v2__card">', rendered)
        self.assertIn(f"<h3>{scope_title}</h3>", rendered)
        self.assertIn(
            f'<a class="service-v2__card service-v2__card--linked" href="{child["url"]}">',
            rendered,
        )
        self.assertIn(
            f'<a class="service-v2__card service-v2__card--linked" href="{article["url"]}">',
            rendered,
        )

    def test_schema_two_omits_inline_json_ld_because_theme_emits_shared_graph(self) -> None:
        """Catches a hub body adding a second FAQ graph beside the wp_head graph."""
        service = schema_two_fixture(self.service_seeds[0])

        rendered = render_service(service)

        self.assertIn('service-v2__faq', rendered)
        self.assertNotIn('type="application/ld+json"', rendered)
        self.assertNotIn('service-v2__schema', rendered)

    def test_prepare_release_removes_backlog_navigation_without_inventing_cases(self) -> None:
        service = next(
            schema_two_fixture(payload)
            for payload in self.service_seeds
            if payload["service_id"] == "S4"
        )

        prepared = prepare_service_for_release(
            service,
            self.architecture,
            self.cases,
        )

        self.assertEqual("ready", prepared["release_status"])
        self.assertEqual([], prepared["articles"]["items"])
        self.assertEqual([], prepared["evidence_gaps"])
        self.assertEqual([], prepared["proof"]["cases"])
        validate_service_v2(
            prepared,
            self.architecture,
            self.cases,
            production_ready=True,
        )

    def test_direct_cli_auto_validates_schema_two_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sources"
            write_schema_two_sources(source)

            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "service_v2.py"), "validate", str(source)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(HUB_COUNT, json.loads(result.stdout)["services"])

    def test_schema_two_rejects_owner_and_architecture_drift(self) -> None:
        service = schema_two_fixture(self.service_seeds[0])
        service["canonical"] = "https://exp76.ru/services/not-the-owner/"

        with self.assertRaisesRegex(ContractError, "canonical"):
            validate_service_v2(service, self.architecture, self.cases)

        service = schema_two_fixture(self.service_seeds[0])
        service["services"]["items"][0]["url"] = "https://exp76.ru/not-approved/"
        with self.assertRaisesRegex(ContractError, "architecture"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_schema_two_requires_renderable_navigation_sections_even_when_empty(self) -> None:
        s6 = next(
            payload for payload in self.service_seeds if payload["service_id"] == "S6"
        )
        service = schema_two_fixture(s6)
        service["services"] = {}

        with self.assertRaisesRegex(ContractError, "services must contain heading, lead and items"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_nonready_navigation_gaps_are_explicit_and_ready_validation_fails_closed(self) -> None:
        service = next(
            schema_two_fixture(payload)
            for payload in self.service_seeds
            if payload["service_id"] == "S4"
        )

        validate_service_v2(service, self.architecture, self.cases)
        kinds = {gap["kind"] for gap in service["evidence_gaps"]}
        self.assertIn("nonready_destination", kinds)

        with self.assertRaisesRegex(ContractError, "production-ready"):
            validate_service_v2(
                service,
                self.architecture,
                self.cases,
                production_ready=True,
            )

        service["release_status"] = "ready"
        with self.assertRaisesRegex(ContractError, "production-ready"):
            validate_service_v2(service, self.architecture, self.cases)
        service["release_status"] = "draft"

        service["evidence_gaps"] = []
        with self.assertRaisesRegex(ContractError, "evidence_gaps"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_ready_hub_may_truthfully_omit_cases_when_no_verified_case_exists(self) -> None:
        service = next(
            schema_two_fixture(payload)
            for payload in self.service_seeds
            if payload["service_id"] == "S11"
        )
        service["release_status"] = "ready"
        service["rendered_sha256"] = hashlib.sha256(
            render_service(service).encode("utf-8")
        ).hexdigest()

        validate_service_v2(
            service,
            self.architecture,
            self.cases,
            production_ready=True,
        )
        self.assertEqual([], service["proof"]["cases"])

    def test_schema_two_rejects_another_services_audited_illustration(self) -> None:
        s10 = next(
            payload for payload in self.service_seeds if payload["service_id"] == "S10"
        )
        s8 = next(
            payload for payload in self.service_seeds if payload["service_id"] == "S8"
        )
        service = schema_two_fixture(s8)
        service["hero"]["image"] = copy.deepcopy(s10["hero"]["image"])
        service["rendered_sha256"] = hashlib.sha256(
            render_service(service).encode("utf-8")
        ).hexdigest()

        with self.assertRaisesRegex(ContractError, "verified catalog images for S8"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_schema_two_rejects_stale_rendered_fragment_hash(self) -> None:
        service = schema_two_fixture(self.service_seeds[0])
        service["hero"]["lead"] += " Изменение после генерации фрагмента."

        with self.assertRaisesRegex(ContractError, "rendered_sha256 does not match"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_sync_writes_all_fifteen_slug_json_and_html_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            (target / "unrelated.txt").write_text("preserve me", encoding="utf-8")
            (target / "rendered").mkdir()
            (target / "rendered" / "unrelated.html").write_text(
                "preserve rendered", encoding="utf-8"
            )
            fixtures = write_schema_two_sources(source)

            summary = sync_fixture_services(source, target, allow_draft=True)

            self.assertEqual(HUB_COUNT, summary["services"])
            self.assertEqual(HUB_COUNT * 2, summary["outputs"])
            self.assertEqual("preserve me", (target / "unrelated.txt").read_text())
            self.assertEqual(
                "preserve rendered",
                (target / "rendered" / "unrelated.html").read_text(),
            )
            self.assertEqual(
                sorted(f'{service["slug"]}.json' for service in fixtures),
                sorted(path.name for path in target.glob("*.json")),
            )
            self.assertEqual(
                sorted(f'{service["slug"]}.html' for service in fixtures),
                sorted(path.name for path in (target / "rendered").glob("*.html") if path.name != "unrelated.html"),
            )
            for service in fixtures:
                installed = json.loads(
                    (target / f'{service["slug"]}.json').read_text(encoding="utf-8")
                )
                self.assertEqual(service, installed)

    def test_sync_rejects_draft_by_default_and_release_metadata_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            (target / "unrelated.txt").write_bytes(b"untouched")
            services = write_schema_two_sources(source)
            before = directory_snapshot(target)

            with self.assertRaisesRegex(ContractError, "allow_draft"):
                sync_fixture_services(source, target)
            self.assertEqual(before, directory_snapshot(target))

            services[0]["release_id"] = "different-release"
            (source / f'{services[0]["service_id"]}.json').write_text(
                json.dumps(services[0], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "release manifest"):
                sync_fixture_services(source, target, allow_draft=True)
            self.assertEqual(before, directory_snapshot(target))

    def test_sync_rejects_incomplete_or_invalid_set_before_target_write(self) -> None:
        for mutation in ("missing", "invalid"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "sources"
                target = root / "theme" / "service-v2"
                target.mkdir(parents=True)
                (target / "owner.json").write_bytes(b"existing-json")
                (target / "rendered").mkdir()
                (target / "rendered" / "owner.html").write_bytes(b"existing-html")
                services = write_schema_two_sources(source)
                if mutation == "missing":
                    (source / "S8.json").unlink()
                else:
                    services[0]["services"]["items"][0]["url"] = (
                        "https://exp76.ru/not-approved/"
                    )
                    (source / "S1.json").write_text(
                        json.dumps(services[0], ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                before = directory_snapshot(target)

                with self.assertRaises(ContractError):
                    sync_fixture_services(source, target, allow_draft=True)

                self.assertEqual(before, directory_snapshot(target))

    def test_sync_rolls_back_every_managed_output_after_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            fixtures = write_schema_two_sources(source)
            (target / "rendered").mkdir()
            for service in fixtures:
                (target / f'{service["slug"]}.json').write_bytes(
                    f'old-json-{service["service_id"]}'.encode()
                )
                (target / "rendered" / f'{service["slug"]}.html').write_bytes(
                    f'old-html-{service["service_id"]}'.encode()
                )
            (target / "unrelated.txt").write_bytes(b"untouched")
            before = directory_snapshot(target)
            replacements = 0

            def fail_fifth_replace(source_path: os.PathLike[str], target_path: os.PathLike[str]) -> None:
                nonlocal replacements
                replacements += 1
                if replacements == 5:
                    os.replace(source_path, target_path)
                    raise OSError("injected replacement failure")
                os.replace(source_path, target_path)

            with self.assertRaisesRegex(ContractError, "injected replacement failure"):
                sync_fixture_services(
                    source,
                    target,
                    allow_draft=True,
                    _replace=fail_fifth_replace,
                )

            self.assertEqual(before, directory_snapshot(target))

    def test_sync_rolls_back_and_reraises_keyboard_interrupt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            fixtures = write_schema_two_sources(source)
            (target / "rendered").mkdir()
            for service in fixtures:
                (target / f'{service["slug"]}.json').write_bytes(
                    f'old-json-{service["service_id"]}'.encode()
                )
                (target / "rendered" / f'{service["slug"]}.html').write_bytes(
                    f'old-html-{service["service_id"]}'.encode()
                )
            before = directory_snapshot(target)
            replacements = 0

            def interrupt_fifth_replace(
                source_path: os.PathLike[str], target_path: os.PathLike[str]
            ) -> None:
                nonlocal replacements
                replacements += 1
                if replacements == 5:
                    os.replace(source_path, target_path)
                    raise KeyboardInterrupt
                os.replace(source_path, target_path)

            with self.assertRaises(KeyboardInterrupt):
                sync_fixture_services(
                    source,
                    target,
                    allow_draft=True,
                    _replace=interrupt_fifth_replace,
                )

            self.assertEqual(before, directory_snapshot(target))

    def test_sync_preserves_recovery_bytes_when_rollback_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            fixtures = write_schema_two_sources(source)
            (target / "rendered").mkdir()
            prior_bytes: set[bytes] = set()
            for service in fixtures:
                json_before = f'old-json-{service["service_id"]}'.encode()
                html_before = f'old-html-{service["service_id"]}'.encode()
                prior_bytes.update((json_before, html_before))
                (target / f'{service["slug"]}.json').write_bytes(json_before)
                (target / "rendered" / f'{service["slug"]}.html').write_bytes(html_before)
            replacements = 0

            def fail_commit_and_rollback(
                source_path: os.PathLike[str], target_path: os.PathLike[str]
            ) -> None:
                nonlocal replacements
                replacements += 1
                if replacements == 2:
                    os.replace(source_path, target_path)
                    raise OSError("injected commit failure")
                if replacements == 3:
                    raise OSError("injected rollback failure")
                os.replace(source_path, target_path)

            with self.assertRaisesRegex(ContractError, "preserved backup") as raised:
                sync_fixture_services(
                    source,
                    target,
                    allow_draft=True,
                    _replace=fail_commit_and_rollback,
                )

            backups = list(target.rglob("*.service-v2-recovery"))
            self.assertEqual(1, len(backups), str(raised.exception))
            self.assertIn(backups[0].read_bytes(), prior_bytes)
            self.assertIn(str(backups[0]), str(raised.exception))

    def test_sync_rejects_managed_output_symlink_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            fixtures = write_schema_two_sources(source)
            (target / "rendered").mkdir()
            outside = root / "outside.json"
            outside.write_bytes(b"outside-owner")
            managed = target / f'{fixtures[0]["slug"]}.json'
            try:
                managed.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            before = directory_snapshot(target)

            with self.assertRaisesRegex(ContractError, "symbolic link"):
                sync_fixture_services(source, target, allow_draft=True)

            self.assertTrue(managed.is_symlink())
            self.assertEqual(b"outside-owner", outside.read_bytes())
            self.assertEqual(before, directory_snapshot(target))

    def test_sync_rejects_schema_source_symlink_before_target_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            target.mkdir(parents=True)
            write_schema_two_sources(source)
            outside = root / "outside-source.json"
            source_path = source / "S1.json"
            source_path.replace(outside)
            try:
                source_path.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            before = directory_snapshot(target)

            with self.assertRaisesRegex(ContractError, "source is a symbolic link"):
                sync_fixture_services(source, target, allow_draft=True)

            self.assertEqual(before, directory_snapshot(target))

    def test_loader_rejects_symlinked_source_directory_or_parent(self) -> None:
        for mode in ("directory", "parent"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                real_parent = root / "real-parent"
                real_source = real_parent / "sources"
                write_schema_two_sources(real_source)
                try:
                    if mode == "directory":
                        source = root / "linked-sources"
                        source.symlink_to(real_source, target_is_directory=True)
                    else:
                        linked_parent = root / "linked-parent"
                        linked_parent.symlink_to(real_parent, target_is_directory=True)
                        source = linked_parent / "sources"
                except OSError as exc:
                    self.skipTest(f"symbolic links are unavailable: {exc}")

                with self.assertRaisesRegex(ContractError, "source directory.*symbolic link"):
                    load_hub_services(source)

    def test_windows_reparse_fallback_rejects_source_and_target_trees(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sources"
            target = root / "theme" / "service-v2"
            write_schema_two_sources(source)
            target.mkdir(parents=True)
            original_lstat = Path.lstat

            def reparse_lstat(protected: Path):
                def fake_lstat(path: Path) -> object:
                    result = original_lstat(path)
                    if path == protected:
                        return SimpleNamespace(
                            st_file_attributes=(
                                getattr(result, "st_file_attributes", 0)
                                | stat.FILE_ATTRIBUTE_REPARSE_POINT
                            )
                        )
                    return result

                return fake_lstat

            with patch.object(Path, "is_symlink", return_value=False), patch.object(
                Path,
                "lstat",
                reparse_lstat(Path(os.path.abspath(source))),
            ):
                with self.assertRaisesRegex(ContractError, "source directory.*symbolic link"):
                    load_hub_services(source)

            protected_parent = target.parent
            with patch.object(Path, "is_symlink", return_value=False), patch.object(
                Path,
                "lstat",
                reparse_lstat(protected_parent),
            ):
                with self.assertRaisesRegex(ContractError, "managed target parent.*symbolic link"):
                    service_v2_module._reject_managed_symlinks(target, ["managed"])

    def test_sync_rejects_symlinked_target_directories(self) -> None:
        for mode in ("theme", "rendered", "parent"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source = root / "sources"
                write_schema_two_sources(source)
                outside = root / "outside-target"
                outside.mkdir()
                theme_parent = root / "theme"
                theme_parent.mkdir()
                target = theme_parent / "service-v2"
                try:
                    if mode == "theme":
                        target.symlink_to(outside, target_is_directory=True)
                    elif mode == "rendered":
                        target.mkdir()
                        (target / "rendered").symlink_to(
                            outside,
                            target_is_directory=True,
                        )
                    else:
                        linked_parent = root / "linked-parent"
                        linked_parent.symlink_to(outside, target_is_directory=True)
                        target = linked_parent / "service-v2"
                except OSError as exc:
                    self.skipTest(f"symbolic links are unavailable: {exc}")

                with self.assertRaisesRegex(ContractError, "symbolic link"):
                    sync_fixture_services(source, target, allow_draft=True)

                self.assertEqual({}, directory_snapshot(outside))


if __name__ == "__main__":
    unittest.main()
