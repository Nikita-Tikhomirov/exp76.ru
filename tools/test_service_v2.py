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
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import service_v2 as service_v2_module
from tools.service_v2 import (
    ContractError,
    count_words,
    load_hub_services,
    load_services_auto,
    render_service,
    sync_services,
    validate_service_v2,
)
from tools.site_content.contracts import (
    load_case_catalog,
    load_page_architecture,
    numeric_fact_claims,
)


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
DATA_DIR = THEME / "content" / "service-v2"
HUB_SOURCE_DIR = ROOT / "seo-content" / "service-hubs" / "hubs"
ARCHITECTURE_PATH = (
    ROOT / "seo-data" / "2026-08-exp76-services" / "processed" / "page_architecture.csv"
)
CASE_CATALOG_PATH = ROOT / "seo-content" / "service-hubs" / "case-catalog.json"
RELEASE_MANIFEST_PATH = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
RELEASE_ID = "service-hubs-2026-08-28"

EXPECTED_SERVICES = {
    "S1": (673, "landshaftnoe-proektirovanie"),
    "S2": (6868, "gazon-posevnojj-i-gazon-rulonnyjj"),
    "S3": (6871, "posadka-derevev-i-kustarnikov"),
    "S4": (9357, "ukhod-za-sadom"),
    "S5": (667, "planirovka-territorii"),
    "S6": (676, "podpornye-stenki"),
    "S7": (6918, "ulichnoe-osveshhenie-uchastka"),
    "S8": (9282, "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch"),
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
}

EXPECTED_LEGACY_WORDS = {
    "S1": 1259,
    "S2": 1086,
    "S3": 1093,
    "S4": 1339,
    "S5": 1317,
    "S6": 1296,
    "S7": 1254,
    "S8": 1306,
}

EXPECTED_LEGACY_FINGERPRINTS = {
    "S1": "87e7b122301f1971d9b72ba1dd47f66c7bbe84b7154f57857fa16f7acb0b7a0f",
    "S2": "59fbf87336edc788beb0a3b2cb61134a63f840a05e78b71ceb60708bf4f53f4e",
    "S3": "4fddc3df0abd9469ab6d7e1ecbaf7234459b62cc0ac39194275641f53fb6ff3f",
    "S4": "3f78e81ede630e0fe24e4b0b19d268812a8bef1e8e021f6eb5548dbc55ddffcf",
    "S5": "53478d3a3492f2d86b21bb076bb07e3364978e833c0169a719f0db1edc19ae4c",
    "S6": "85126de28e06c94bfb2083d56fb3d9f5d857f62c99673faf708ef1f86db95df9",
    "S7": "5f75cbcfbcb89981934bedc0fc0459c36a47167106533cd41faae4da37b8b6d2",
    "S8": "f998456dd56c25e636d3160a772c4754073209e73d3c27ebf12c642015e2cad7",
}

EXPECTED_NAVIGATION = {
    "S1": {
        "services": {},
        "articles": {
            "S1-ARTICLE-505521C7EF8C": "https://exp76.ru/kak-rasschitat-stoimost-blagoustrojstva-sa-sotku/",
            "S1-ARTICLE-72FBB49E67C8": "https://exp76.ru/kak-rasschitat-inzhenernoe-blagoustrojstvo-uchastka/",
            "S1-ARTICLE-DIY-DESIGN": "https://exp76.ru/dizajn-proekt-uchastka-svoimi-rukami/",
        },
    },
    "S2": {
        "services": {
            "S2-CHILD-POSEVNOY-GAZON": "https://exp76.ru/posevnoj-gazon-pod-kljuch/",
            "S2-CHILD-RULONNY-GAZON": "https://exp76.ru/rulonnyj-gazon-pod-kljuch/",
        },
        "articles": {
            "S2-ARTICLE-15A8258BC551": "https://exp76.ru/ustrojstvo-gazona-shema/",
            "S2-ARTICLE-182825428CBD": "https://exp76.ru/kak-ukladyvat-rulonnyj-gazon/",
        },
    },
    "S3": {
        "services": {
            "S3-CHILD-KRUPNOMERY": "https://exp76.ru/posadka-krupnomerov/",
        },
        "articles": {
            "S3-ARTICLE-PLANTING-SCHEMES": "https://exp76.ru/normy-posadki-derevev/",
        },
    },
    "S4": {
        "services": {
            "S4-CHILD-OBREZKA": "https://exp76.ru/obrezka-derevev-i-kustarnikov/",
        },
        "articles": {
            "S4-ARTICLE-F668FF6F6190": "https://exp76.ru/shema-uhoda-za-sadom/",
            "S4-ARTICLE-PRUNING-GUIDE": "https://exp76.ru/obrezka-derevev-shema/",
        },
    },
    "S5": {
        "services": {
            "S5-CHILD-VYRAVNIVANIE": "https://exp76.ru/vyravnivanie-uchastka/",
        },
        "articles": {
            "S5-ARTICLE-74B3B2B18DA4": "https://exp76.ru/vyravnivanie-uchastka-svoimi-rukami/",
            "S5-ARTICLE-FF3B04A53D72": "https://exp76.ru/shema-planirovki-uchastka/",
        },
    },
    "S6": {
        "services": {},
        "articles": {
            "S6-ARTICLE-DIY-RETAINING-WALL": "https://exp76.ru/podpornaya-stenka-na-uchastke-svoimi-rukami/",
        },
    },
    "S7": {
        "services": {},
        "articles": {
            "S7-ARTICLE-DIY-LIGHTING": "https://exp76.ru/kak-sdelat-osveschenie-na-uchastke/",
        },
    },
    "S8": {
        "services": {},
        "articles": {
            "S8-ARTICLE-DIY-ENTRANCE": "https://exp76.ru/kak-sdelat-vezd-na-uchastok-cherez-kanavu/",
        },
    },
}

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
}

UPLOADS = "https://exp76.ru/wp-content/uploads/"
EXPECTED_IMAGE_POOLS = {
    "S1": {
        UPLOADS + "2015/07/lanshaftnoe-proektirovanie.webp",
        UPLOADS + "2019/02/IMG_20181015_110705_HDR.webp",
        UPLOADS + "2020/10/Ila-CrwKkL4.webp",
        UPLOADS + "2023/12/20230817_084022-1-scaled.webp",
    },
    "S2": {
        UPLOADS + "2017/01/gazoni-rulonniy-posevnoy.webp",
        UPLOADS + "2019/02/NEwk9KFYTXY.webp",
        UPLOADS + "2020/10/20200514_085626.webp",
    },
    "S3": {
        UPLOADS + "2017/01/ozelenenie.webp",
        UPLOADS + "2020/10/20200514_085626.webp",
    },
    "S4": {
        UPLOADS + "2015/07/lanshaftnoe-proektirovanie.webp",
        UPLOADS + "2017/01/gazoni-rulonniy-posevnoy.webp",
        UPLOADS + "2017/01/landshaftnoe-osveshenie.webp",
        UPLOADS + "2017/01/ozelenenie.webp",
        UPLOADS + "2018/12/uhod1.webp",
        UPLOADS + "2018/12/uhod2.webp",
    },
    "S5": {
        UPLOADS + "2015/07/lanshaftnoe-proektirovanie.webp",
        UPLOADS + "2015/07/planirovka-territorii.webp",
        UPLOADS + "2017/01/ozelenenie.webp",
        UPLOADS + "2017/01/planirovka_territorii10.webp",
        UPLOADS + "2017/01/planirovka_territorii2.webp",
        UPLOADS + "2017/01/planirovka_territorii6.webp",
    },
    "S6": {
        UPLOADS + "2015/07/Подпорные-стенки.webp",
        *(UPLOADS + f"2015/07/podporki{index}.webp" for index in range(1, 6)),
    },
    "S7": {
        UPLOADS + "2017/01/landshaftnoe-osveshenie.webp",
        UPLOADS + "2017/01/naruzhnoe-osveshhenie_752.webp",
        UPLOADS + "2017/01/osvescheniezdaniya.webp",
    },
    "S8": {
        UPLOADS + "2018/12/vjezd.webp",
        UPLOADS + "2018/12/vjezd2.webp",
    },
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


def _payload_fingerprint(payload: dict[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _embedded_image_urls(value: object) -> set[str]:
    urls: set[str] = set()
    if isinstance(value, dict):
        url = value.get("url")
        alt = value.get("alt")
        if isinstance(url, str) and url.startswith(UPLOADS) and isinstance(alt, str):
            urls.add(url)
        for item in value.values():
            urls.update(_embedded_image_urls(item))
    elif isinstance(value, list):
        for item in value:
            urls.update(_embedded_image_urls(item))
    return urls


def schema_two_fixture(service: dict[str, object]) -> dict[str, object]:
    """Return a valid v2 fixture, promoting preserved v1 input when necessary."""
    payload = copy.deepcopy(service)
    if payload.get("schema_version") == 2:
        payload["rendered_sha256"] = hashlib.sha256(
            render_service(payload).encode("utf-8")
        ).hexdigest()
        return payload

    service_id = str(payload["service_id"])
    architecture = load_page_architecture(ARCHITECTURE_PATH)
    payload["schema_version"] = 2
    payload["release_id"] = RELEASE_ID
    payload["release_status"] = "draft"
    payload["page_key"] = f"{service_id}-HUB"
    payload["page_type"] = "hub"
    payload["scope"] = payload.pop("services")
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
    if service_id == "S5":
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
    if not payload["proof"]["cases"]:
        payload["evidence_gaps"].append(
            {
                "kind": "missing_verified_case",
                "page_key": payload["page_key"],
                "status": "missing",
            }
        )
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
        for path in sorted(DATA_DIR.glob("*.json"))
    ]
    for service in services:
        path = source_dir / f'{service["service_id"]}.json'
        path.write_text(
            json.dumps(service, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return services


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
        self.assertEqual(len(files), 8, "exactly eight approved service payloads must ship")
        return [json.loads(path.read_text(encoding="utf-8")) for path in files]

    def test_real_payloads_pass_the_production_contract(self) -> None:
        """Catches incomplete copy, placeholders, unsafe owners and missing SEO fields."""
        result = self.run_cli("validate", str(DATA_DIR))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["services"], 8)
        self.assertEqual(summary["errors"], 0)
        self.assertGreaterEqual(summary["words"], 7000)

    def test_payloads_keep_the_eight_existing_url_owners(self) -> None:
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
        """Catches duplicate snippets or generic H1 values across the eight owners."""
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
            self.assertEqual(len(rendered), 8)
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
        self.assertEqual(len(list(rendered_dir.glob("*.html"))), 8)

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
        self.assertIn("http_response_code(405)", handler_source)
        self.assertIn("http_response_code(422)", handler_source)
        self.assertIn("http_response_code(500)", handler_source)
        self.assertIn("$_POST['consent'] ??", handler_source)
        self.assertIn("land76_clean_post_value('source'", handler_source)
        self.assertIn("$mail_sent = @mail(", handler_source)
        self.assertIn("if (!$mail_sent)", handler_source)


class SchemaTwoProductionDataTest(unittest.TestCase):
    def load_sources(self) -> list[dict[str, object]]:
        files = sorted(HUB_SOURCE_DIR.glob("*.json"))
        self.assertEqual(8, len(files), "canonical hub source must contain S1-S8")
        return [json.loads(path.read_text(encoding="utf-8")) for path in files]

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
            self.assertEqual("draft", service["release_status"])
            scope_items = service["scope"]["items"]
            self.assertEqual(EXPECTED_SCOPE_COUNTS[service_id], len(scope_items))
            self.assertTrue(
                all("url" not in item and "page_key" not in item for item in scope_items)
            )
            legacy = _legacy_projection(service)
            words = count_words(legacy)
            self.assertEqual(EXPECTED_LEGACY_WORDS[service_id], words)
            self.assertEqual(
                EXPECTED_LEGACY_FINGERPRINTS[service_id],
                _payload_fingerprint(legacy),
            )
            total_words += words
            total_scope_cards += len(scope_items)
        self.assertEqual(9950, total_words)
        self.assertEqual(39, total_scope_cards)

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
        self.assertEqual(5, sum(len(item["services"]) for item in EXPECTED_NAVIGATION.values()))
        self.assertEqual(13, sum(len(item["articles"]) for item in EXPECTED_NAVIGATION.values()))
        self.assertEqual(18, navigation_count)

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
            self.assertEqual(EXPECTED_IMAGE_POOLS[service_id], _embedded_image_urls(service))
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
            }
            if not EXPECTED_CASES[service_id]:
                expected_gaps.add(("missing_verified_case", f"{service_id}-HUB", "missing"))
            actual_gaps = {
                (str(gap["kind"]), str(gap["page_key"]), str(gap["status"]))
                for gap in service["evidence_gaps"]
            }
            self.assertEqual(expected_gaps, actual_gaps)

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
        self.assertEqual(8, len(installed_files))
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
            if EXPECTED_CASES[service_id]:
                self.assertIn('id="service-v2-cases"', rendered)
                self.assertIn('href="#service-v2-cases"', rendered)
            else:
                self.assertNotIn('id="service-v2-cases"', rendered)
                self.assertNotIn('href="#service-v2-cases"', rendered)
        self.assertEqual(39, scope_cards)
        self.assertEqual(18, linked_cards)

        css = (THEME / "css" / "service-v2.css").read_text(encoding="utf-8")
        self.assertIn(".service-v2__card--linked:focus-visible", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertRegex(css, r"@media\s*\(max-width:")

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
        self.assertIn(
            "673 => array('slug' => 'landshaftnoe-proektirovanie', 'service_id' => 'S1')",
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
        cls.v1_services = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(DATA_DIR.glob("*.json"))
        ]

    def test_schema_two_preserves_descriptive_scope_and_renders_linked_cards(self) -> None:
        service = schema_two_fixture(self.v1_services[0])

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
            self.assertEqual(8, json.loads(result.stdout)["services"])

    def test_schema_two_rejects_owner_and_architecture_drift(self) -> None:
        service = schema_two_fixture(self.v1_services[0])
        service["canonical"] = "https://exp76.ru/services/not-the-owner/"

        with self.assertRaisesRegex(ContractError, "canonical"):
            validate_service_v2(service, self.architecture, self.cases)

        service = schema_two_fixture(self.v1_services[0])
        service["services"]["items"][0]["url"] = "https://exp76.ru/not-approved/"
        with self.assertRaisesRegex(ContractError, "architecture"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_schema_two_requires_renderable_navigation_sections_even_when_empty(self) -> None:
        s6 = next(payload for payload in self.v1_services if payload["service_id"] == "S6")
        service = schema_two_fixture(s6)
        service["services"] = {}

        with self.assertRaisesRegex(ContractError, "services must contain heading, lead and items"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_draft_gaps_are_explicit_and_production_ready_validation_fails_closed(self) -> None:
        service = next(
            schema_two_fixture(payload)
            for payload in self.v1_services
            if payload["service_id"] == "S4"
        )

        validate_service_v2(service, self.architecture, self.cases)
        kinds = {gap["kind"] for gap in service["evidence_gaps"]}
        self.assertIn("missing_verified_case", kinds)
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

    def test_schema_two_rejects_another_services_audited_illustration(self) -> None:
        s1 = next(payload for payload in self.v1_services if payload["service_id"] == "S1")
        s8 = next(payload for payload in self.v1_services if payload["service_id"] == "S8")
        service = schema_two_fixture(s8)
        service["hero"]["image"] = copy.deepcopy(s1["hero"]["image"])

        with self.assertRaisesRegex(ContractError, "verified catalog images for S8"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_schema_two_rejects_stale_rendered_fragment_hash(self) -> None:
        service = schema_two_fixture(self.v1_services[0])
        service["hero"]["lead"] += " Изменение после генерации фрагмента."

        with self.assertRaisesRegex(ContractError, "rendered_sha256 does not match"):
            validate_service_v2(service, self.architecture, self.cases)

    def test_sync_writes_only_eight_slug_json_and_html_outputs(self) -> None:
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

            summary = sync_services(source, target, allow_draft=True)

            self.assertEqual(8, summary["services"])
            self.assertEqual(16, summary["outputs"])
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
                sync_services(source, target)
            self.assertEqual(before, directory_snapshot(target))

            services[0]["release_id"] = "different-release"
            (source / f'{services[0]["service_id"]}.json').write_text(
                json.dumps(services[0], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "release manifest"):
                sync_services(source, target, allow_draft=True)
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
                    sync_services(source, target, allow_draft=True)

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
                sync_services(
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
                sync_services(
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
                sync_services(
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
                sync_services(source, target, allow_draft=True)

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
                sync_services(source, target, allow_draft=True)

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
                    sync_services(source, target, allow_draft=True)

                self.assertEqual({}, directory_snapshot(outside))


if __name__ == "__main__":
    unittest.main()
