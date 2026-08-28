import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.seo_semantics.architecture import PageDestination
from tools.site_content.cases import CaseEvidence, ImageAudit
from tools.site_content.contracts import (
    build_release_link_allowlist,
    ContractError,
    load_case_catalog,
    load_content_page,
    load_page_architecture,
    load_release_manifest,
    numeric_fact_claims,
    validate_content_collection,
    validate_content_page_dict,
    validate_release_manifest,
)


IMAGE_URL = "https://exp76.ru/wp-content/uploads/2026/08/verified.webp"
CASE_URL = "https://exp76.ru/verified-case/"
ROOT = Path(__file__).resolve().parents[1]
PAGE_ARCHITECTURE_PATH = (
    ROOT / "seo-data" / "2026-08-exp76-services" / "processed" / "page_architecture.csv"
)
CASE_CATALOG_PATH = ROOT / "seo-content" / "service-hubs" / "case-catalog.json"
RELEASE_MANIFEST_PATH = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
HUB_SOURCE_DIR = ROOT / "seo-content" / "service-hubs" / "hubs"
LEGACY_SHARED_RELATED_TEXT = (
    "Форма для предварительного обращения по работам на вашем участке."
)

ARCHITECTURE = {
    "S1-HUB": PageDestination(
        destination_id="S1-HUB",
        service_id="S1",
        page_role="hub",
        parent_destination_id="",
        canonical_url="https://exp76.ru/services/landshaftnoe-proektirovanie/",
        source_cluster_ids=("C-HUB",),
        publication_status="ready",
    ),
    "S1-CHILD": PageDestination(
        destination_id="S1-CHILD",
        service_id="S1",
        page_role="child_service",
        parent_destination_id="S1-HUB",
        canonical_url="https://exp76.ru/approved-child/",
        source_cluster_ids=("C-CHILD",),
        publication_status="ready",
    ),
    "S1-ARTICLE": PageDestination(
        destination_id="S1-ARTICLE",
        service_id="S1",
        page_role="article",
        parent_destination_id="S1-HUB",
        canonical_url="https://exp76.ru/approved-article/",
        source_cluster_ids=("C-ARTICLE",),
        publication_status="ready",
    ),
}

CASES = {
    101: CaseEvidence(
        page_id=101,
        url=CASE_URL,
        title="Подтверждённый объект",
        location="Ярославль",
        work_types=("Ландшафтное проектирование",),
        service_ids=("S1",),
        image_urls=(IMAGE_URL,),
        source_files=("fixture.json",),
        seo_ready=True,
        image_audits=(
            ImageAudit(
                url=IMAGE_URL,
                http_status=200,
                content_type="image/webp",
                checked_date="2026-08-28",
                method="HEAD",
                final_url=IMAGE_URL,
            ),
        ),
    )
}


def image_fixture() -> dict[str, object]:
    return {
        "url": IMAGE_URL,
        "alt": "Подтверждённая фотография выполненного объекта",
        "case_id": 101,
    }


def named_items(count: int) -> list[dict[str, str]]:
    return [
        {
            "title": f"Самостоятельный раздел {index}",
            "text": (
                "Содержательный текст описывает конкретную задачу, порядок работ "
                f"и проверяемый результат раздела {index} без шаблонных обещаний."
            ),
        }
        for index in range(1, count + 1)
    ]


def service_page_fixture() -> dict[str, object]:
    return {
        "schema_version": 1,
        "page_key": "S1-CHILD",
        "service_id": "S1",
        "page_type": "service",
        "slug": "approved-child",
        "canonical": "https://exp76.ru/approved-child/",
        "seo": {
            "title": "Самостоятельная услуга ландшафтного проектирования в Ярославле",
            "description": (
                "Подробное описание самостоятельной услуги, состава работ, этапов, "
                "факторов стоимости и подтверждённых результатов на участке."
            ),
        },
        "hero": {
            "title": "Самостоятельная услуга проектирования участка",
            "lead": "Объясняем задачу и ожидаемый результат до начала подготовки проекта.",
            "image": image_fixture(),
        },
        "problem": "Исходные данные и задачи участка нужно согласовать до проектирования.",
        "solution": "Фиксируем состав проекта, этапы и проверяемые результаты работ.",
        "sections": named_items(5),
        "price_factors": named_items(3),
        "process": named_items(4),
        "faq": [
            {
                "question": f"Как согласуется этап работ номер {index}?",
                "answer": (
                    "Этап согласуют после проверки исходных данных и фиксируют в составе "
                    "работ без неподтверждённых сроков или гарантий."
                ),
            }
            for index in range(1, 6)
        ],
        "proof": {
            "cases": [
                {
                    "page_id": 101,
                    "url": CASE_URL,
                    "title": "Подтверждённый объект",
                    "text": "Опубликованная карточка объекта подтверждает выполненный состав работ.",
                    "image": image_fixture(),
                }
            ]
        },
        "related_commercial_links": [
            {
                "page_key": "S1-HUB",
                "url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "role": "hub",
            }
        ],
        "related_article_links": [
            {
                "page_key": "S1-ARTICLE",
                "url": "https://exp76.ru/approved-article/",
                "role": "article",
            }
        ],
        "fact_evidence": [],
    }


def hub_page_fixture() -> dict[str, object]:
    return {
        "schema_version": 2,
        "page_key": "S1-HUB",
        "service_id": "S1",
        "page_type": "hub",
        "page_id": 673,
        "parent_id": 921,
        "wp_template": "servicepost.php",
        "slug": "landshaftnoe-proektirovanie",
        "canonical": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
        "seo": {
            "title": "Уникальный title хаба ландшафтного проектирования",
            "description": (
                "Уникальное описание широкого хаба с составом работ, этапами, "
                "факторами стоимости и подтверждёнными объектами."
            ),
            "primary_queries": ["ландшафтное проектирование участка"],
            "secondary_queries": [
                "проект участка",
                "ландшафтный проект",
                "проектирование сада",
            ],
        },
        "hero": {
            "eyebrow": "Проектирование участка",
            "title": "Уникальный H1 хаба ландшафтного проектирования",
            "lead": "Связываем задачи владельца, особенности территории и будущие работы.",
            "image": image_fixture(),
            "primary_cta": {"label": "Обсудить проект", "href": "#service-v2-form"},
            "secondary_cta": {"label": "Посмотреть работы", "href": "#service-v2-cases"},
        },
        "intro": {
            "heading": "Зачем нужен единый проект участка",
            "body": [
                "Проект фиксирует решения до начала строительных и посадочных работ на территории.",
                "Состав документации определяют по исходным данным и задачам конкретного владельца.",
            ],
            "highlights": named_items(4),
        },
        "scope": {
            "heading": "Что рассматриваем внутри широкого хаба",
            "lead": "Эти описательные карточки не создают самостоятельных владельцев запросов.",
            "items": [
                {
                    **named_items(1)[0],
                    "image": image_fixture(),
                }
            ],
        },
        "services": {
            "heading": "Самостоятельные коммерческие услуги",
            "lead": "Ссылки появляются только для подтверждённых архитектурой дочерних страниц.",
            "items": [
                {
                    "page_key": "S1-CHILD",
                    "url": "https://exp76.ru/approved-child/",
                    "title": "Утверждённая дочерняя услуга",
                    "text": "Описание отдельной коммерческой услуги с самостоятельным интентом.",
                    "image": image_fixture(),
                }
            ]
        },
        "articles": {
            "heading": "Материалы по теме",
            "lead": "Информационные страницы отвечают на отдельные вопросы и ведут к владельцу услуги.",
            "items": [
                {
                    "page_key": "S1-ARTICLE",
                    "url": "https://exp76.ru/approved-article/",
                    "title": "Утверждённая статья",
                    "text": "Информационный материал отвечает на отдельный вопрос пользователя.",
                    "image": image_fixture(),
                }
            ]
        },
        "process": {
            "heading": "Как строится работа",
            "lead": "Этапы согласуют последовательно по проверенным исходным данным.",
            "steps": named_items(4),
        },
        "pricing": {
            "heading": "Факторы стоимости",
            "lead": "Состав расчёта зависит от территории и выбранных проектных разделов.",
            "body": [
                "До расчёта определяют площадь, рельеф и необходимый состав документации.",
                "Итоговая смета опирается на согласованное техническое задание без универсальных обещаний.",
            ],
            "factors": named_items(5),
            "calculator": None,
        },
        "proof": service_page_fixture()["proof"],
        "geo": {
            "heading": "Работа с участками в Ярославской области",
            "body": [
                "Условия выезда и исходные данные уточняют для конкретной территории.",
                "Город сам по себе не заменяет сведения о рельефе, застройке и подъезде.",
            ],
        },
        "faq": {
            "heading": "Вопросы о проектировании",
            "items": [
                {
                    "question": f"Что уточняют на этапе проекта {index}?",
                    "answer": (
                        f"Для этапа {index} проверяют исходные данные и согласуют ожидаемый результат."
                    ),
                }
                for index in range(1, 6)
            ],
        },
        "related_links": {
            "heading": "Связанные страницы",
            "lead": "Переходы ведут только к утверждённым владельцам тем.",
            "items": [
                {
                    "page_key": "S1-CHILD",
                    "url": "https://exp76.ru/approved-child/",
                    "role": "child_service",
                    "label": "Утверждённая услуга",
                    "text": "Самостоятельная коммерческая страница внутри направления.",
                }
            ],
        },
        "cta": {
            "heading": "Обсудить исходные данные",
            "text": "Опишите участок и задачу, чтобы определить подходящий состав работ.",
            "button_label": "Отправить заявку",
        },
        "evidence_gaps": [],
        "fact_evidence": [],
    }


def article_page_fixture() -> dict[str, object]:
    return {
        "schema_version": 1,
        "page_key": "S1-ARTICLE",
        "service_id": "S1",
        "page_type": "article",
        "slug": "approved-article",
        "canonical": "https://exp76.ru/approved-article/",
        "intent": "informational",
        "primary_query": "как подготовить исходные данные для проекта участка",
        "seo": {
            "title": "Как подготовить исходные данные для проекта участка",
            "description": (
                "Разбираем исходные данные, ограничения территории и типовые ошибки "
                "до заказа самостоятельной услуги проектирования."
            ),
        },
        "hero": {
            "title": "Подготовка исходных данных для проекта",
            "lead": "Практический разбор без дублирования коммерческого предложения.",
            "image": image_fixture(),
        },
        "sections": named_items(4),
        "related_commercial_links": [
            {
                "page_key": "S1-HUB",
                "url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "role": "hub",
            }
        ],
        "fact_evidence": [],
    }


class ContentContractTest(unittest.TestCase):
    def test_complete_service_article_and_hub_fixtures_are_valid(self) -> None:
        self.assertEqual([], validate_content_page_dict(service_page_fixture(), ARCHITECTURE, CASES))
        self.assertEqual([], validate_content_page_dict(article_page_fixture(), ARCHITECTURE, CASES))
        self.assertEqual([], validate_content_page_dict(hub_page_fixture(), ARCHITECTURE, CASES))

    def test_service_page_requires_at_least_five_sections(self) -> None:
        page = service_page_fixture()
        page["sections"] = []

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("sections must contain at least 5 items", errors)

    def test_service_and_article_require_owner_seo_hero_and_main_image(self) -> None:
        for factory in (service_page_fixture, article_page_fixture):
            with self.subTest(page=factory.__name__):
                page = factory()
                page.pop("slug")
                page.pop("seo")
                page.pop("hero")

                errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

                self.assertIn("slug must be non-blank and match canonical", errors)
                self.assertIn("seo must contain title and description", errors)
                self.assertIn("hero must contain title, lead and a verified main image", errors)

    def test_hub_card_rejects_url_absent_from_page_architecture(self) -> None:
        hub = copy.deepcopy(hub_page_fixture())
        hub["services"]["items"][0]["url"] = "https://exp76.ru/not-approved/"

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn("service card URL is absent from page architecture", errors)

    def test_hub_linked_cards_require_complete_renderable_fields(self) -> None:
        hub = hub_page_fixture()
        for field in ("title", "text", "image"):
            hub["services"]["items"][0].pop(field)

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn(
            "child card must contain page_key, url, title, text and image",
            errors,
        )

    def test_article_requires_informational_query_and_four_sections(self) -> None:
        article = article_page_fixture()
        article["primary_query"] = ""
        article["sections"] = named_items(3)

        errors = validate_content_page_dict(article, ARCHITECTURE, CASES)

        self.assertIn("primary_query must be non-blank informational text", errors)
        self.assertIn("sections must contain at least 4 items", errors)

    def test_unknown_case_reference_is_rejected(self) -> None:
        page = service_page_fixture()
        page["proof"]["cases"][0]["page_id"] = 999

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("unknown case 999", errors)

    def test_service_requires_complete_commercial_contract(self) -> None:
        page = service_page_fixture()
        page["problem"] = ""
        page["price_factors"] = []
        page["process"] = []
        page["faq"] = page["faq"][:4]
        page["proof"]["cases"] = []
        page["related_commercial_links"] = []
        page["related_article_links"] = []

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("problem must contain substantive text", errors)
        self.assertIn("price_factors must contain at least 1 item", errors)
        self.assertIn("process must contain at least 1 item", errors)
        self.assertIn("faq must contain at least 5 items", errors)
        self.assertIn("service page requires a verified case or hub_case_fallback", errors)
        self.assertIn("related_commercial_links must contain at least 1 item", errors)
        self.assertIn("related_article_links must contain at least 1 item", errors)

    def test_sections_and_faq_items_require_typed_substantive_fields(self) -> None:
        page = service_page_fixture()
        page["sections"][0].pop("title")
        page["faq"] = [1, 2, 3, 4, 5]

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("sections[0].title must not be blank", errors)
        self.assertIn("faq[0] must be an object", errors)

        article = article_page_fixture()
        article["faq_supported_by_cluster"] = True
        article["faq"] = [{}]
        errors = validate_content_page_dict(article, ARCHITECTURE, CASES)
        self.assertIn("faq[0].question must not be blank", errors)
        self.assertIn("faq[0].answer must contain substantive text", errors)

    def test_child_case_fallback_must_be_explicit_and_catalog_verified(self) -> None:
        page = service_page_fixture()
        page["proof"]["cases"] = []
        page["proof"]["hub_case_fallback"] = {}

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("hub_case_fallback must reference a verified supporting case", errors)

        page["proof"]["hub_case_fallback"] = {
            "page_id": 101,
            "url": CASE_URL,
            "image": image_fixture(),
            "reason": "The verified hub case demonstrates the same supported service scope.",
            "source_ref": "case-catalog:101",
        }
        self.assertEqual([], validate_content_page_dict(page, ARCHITECTURE, CASES))

    def test_article_faq_requires_cluster_support(self) -> None:
        article = article_page_fixture()
        article["faq"] = [
            {
                "question": "Как проверить исходные данные?",
                "answer": "Сверить документы и фактические ограничения территории.",
            }
        ]

        errors = validate_content_page_dict(article, ARCHITECTURE, CASES)

        self.assertIn("article FAQ requires faq_supported_by_cluster=true", errors)

    def test_hub_requires_schema_two_and_preserved_v1_sections(self) -> None:
        hub = hub_page_fixture()
        hub["schema_version"] = 1
        del hub["pricing"]

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn("hub schema_version must be 2", errors)
        self.assertIn("hub must preserve v1 section pricing", errors)

    def test_draft_hub_requires_explicit_gaps_and_never_accepts_fallback_proof(self) -> None:
        architecture = dict(ARCHITECTURE)
        architecture["S1-ARTICLE"] = replace(
            architecture["S1-ARTICLE"], publication_status="backlog"
        )
        hub = hub_page_fixture()
        hub["proof"]["cases"] = []
        hub["evidence_gaps"] = [
            {
                "kind": "missing_verified_case",
                "page_key": "S1-HUB",
                "status": "missing",
            },
            {
                "kind": "nonready_destination",
                "page_key": "S1-ARTICLE",
                "status": "backlog",
            },
        ]

        self.assertEqual([], validate_content_page_dict(hub, architecture, CASES))

        hub["evidence_gaps"] = []
        hub["proof"]["hub_case_fallback"] = {"page_id": 101}
        errors = validate_content_page_dict(hub, architecture, CASES)
        self.assertIn("hub proof must not synthesize hub_case_fallback", errors)
        self.assertIn("evidence_gaps is missing unresolved content evidence", errors)

    def test_production_ready_hub_rejects_empty_cases_and_nonready_destinations(self) -> None:
        architecture = dict(ARCHITECTURE)
        architecture["S1-CHILD"] = replace(
            architecture["S1-CHILD"], publication_status="blocked_facts"
        )
        hub = hub_page_fixture()
        hub["proof"]["cases"] = []
        hub["evidence_gaps"] = [
            {
                "kind": "missing_verified_case",
                "page_key": "S1-HUB",
                "status": "missing",
            },
            {
                "kind": "nonready_destination",
                "page_key": "S1-CHILD",
                "status": "blocked_facts",
            },
        ]

        errors = validate_content_page_dict(
            hub,
            architecture,
            CASES,
            production_ready=True,
        )

        self.assertIn("production-ready hub requires a verified case", errors)
        self.assertIn("production-ready hub contains unresolved evidence_gaps", errors)
        self.assertIn("production-ready hub links a nonready destination", errors)

    def test_substantive_sections_reject_short_copy(self) -> None:
        page = service_page_fixture()
        page["sections"][0]["text"] = "Коротко."

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("sections[0].text must contain substantive text", errors)

    def test_case_must_support_the_page_service(self) -> None:
        page = service_page_fixture()
        cases = {101: replace(CASES[101], service_ids=("S2",))}

        errors = validate_content_page_dict(page, ARCHITECTURE, cases)

        self.assertIn("case 101 does not support service S1", errors)

    def test_image_must_be_owned_and_verified_by_its_case(self) -> None:
        page = service_page_fixture()
        page["hero"]["image"]["url"] = (
            "https://exp76.ru/wp-content/uploads/2026/08/not-owned.webp"
        )

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn(
            "image https://exp76.ru/wp-content/uploads/2026/08/not-owned.webp "
            "is not owned by case 101",
            errors,
        )

    def test_linked_card_image_must_resolve_through_the_case_catalog(self) -> None:
        hub = hub_page_fixture()
        hub["articles"]["items"][0]["image"] = {
            "url": "https://exp76.ru/wp-content/uploads/unverified.webp",
            "alt": "Неподтверждённое изображение карточки",
        }

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn(
            "articles.items[0].image.url is absent from verified catalog images for S1",
            errors,
        )

    def test_internal_link_outside_architecture_is_rejected(self) -> None:
        page = service_page_fixture()
        page["related_article_links"][0]["url"] = "https://exp76.ru/not-approved/"

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("internal link is outside the release allowlist", errors)

    def test_related_links_reject_nonobjects_unknown_keys_and_wrong_roles(self) -> None:
        page = service_page_fixture()
        page["related_commercial_links"] = [{}]
        page["related_article_links"] = [42]

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("related_commercial_links[0] must be a typed link object", errors)
        self.assertIn("related_article_links[0] must be a typed link object", errors)

        page = service_page_fixture()
        page["related_commercial_links"][0] = {
            "page_key": "S1-ARTICLE",
            "url": "https://exp76.ru/approved-article/",
            "role": "article",
        }
        page["related_article_links"][0] = {
            "page_key": "UNKNOWN",
            "url": CASE_URL,
            "role": "article",
        }
        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)
        self.assertIn("related_commercial_links[0] has a prohibited page role", errors)
        self.assertIn("related_article_links[0] does not match page architecture", errors)

    def test_article_must_link_its_own_architecture_parent(self) -> None:
        architecture = dict(ARCHITECTURE)
        architecture["S2-HUB"] = PageDestination(
            destination_id="S2-HUB",
            service_id="S2",
            page_role="hub",
            parent_destination_id="",
            canonical_url="https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
            source_cluster_ids=("C-S2-HUB",),
            publication_status="ready",
        )
        article = article_page_fixture()
        article["related_commercial_links"] = [
            {
                "page_key": "S2-HUB",
                "url": "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
                "role": "hub",
            }
        ]

        errors = validate_content_page_dict(article, architecture, CASES)

        self.assertIn(
            "related_commercial_links must include the page architecture parent",
            errors,
        )

    def test_hub_related_link_outside_release_allowlist_is_rejected(self) -> None:
        hub = hub_page_fixture()
        hub["related_links"]["items"][0]["url"] = "https://exp76.ru/not-approved/"

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn("internal link is outside the release allowlist", errors)

    def test_calculator_link_must_match_the_special_calculator_owner(self) -> None:
        architecture = dict(ARCHITECTURE)
        architecture["SPECIAL-CALCULATOR"] = PageDestination(
            destination_id="SPECIAL-CALCULATOR",
            service_id="S1",
            page_role="special",
            parent_destination_id="",
            canonical_url="https://exp76.ru/kalkuljator-uslug/",
            source_cluster_ids=("C-CALCULATOR",),
            publication_status="ready",
        )
        hub = hub_page_fixture()
        hub["pricing"]["calculator"] = {
            "url": CASE_URL,
            "label": "Открыть расчёт",
            "note": "Проверить исходные данные перед предварительным расчётом.",
        }

        errors = validate_content_page_dict(hub, architecture, CASES)

        self.assertIn("pricing.calculator.url must match SPECIAL-CALCULATOR", errors)

    def test_real_link_allowlist_keeps_release_and_case_urls_separate(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)

        allowlist = build_release_link_allowlist(architecture, cases)

        self.assertEqual(26, len(allowlist.managed_urls))
        self.assertEqual(9, len(allowlist.preserved_urls))
        self.assertEqual(35, len(allowlist.case_urls))
        self.assertNotIn("https://exp76.ru/not-approved/", allowlist.internal_urls)

    def test_numeric_guarantee_claim_requires_exact_fact_evidence(self) -> None:
        page = service_page_fixture()
        page["solution"] = "Предоставляем гарантию на результат сроком 5 лет."

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn(
            "solution numeric guarantee claim '5 лет' lacks fact_evidence",
            errors,
        )

    def test_mixed_numeric_claims_each_require_exact_typed_evidence(self) -> None:
        page = service_page_fixture()
        page["solution"] = "Цена 1000 руб., срок 5 дней, гарантия 2 года подтверждаются договором."
        page["fact_evidence"] = [
            {
                "path": "solution",
                "claim_type": "guarantee",
                "claim": "2",
                "source_ref": "client_fact:contract",
            }
        ]

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("solution numeric price claim '1000 руб.' lacks fact_evidence", errors)
        self.assertIn("solution numeric term claim '5 дней' lacks fact_evidence", errors)
        self.assertIn("solution numeric guarantee claim '2 года' lacks fact_evidence", errors)

        page["fact_evidence"] = [
            {
                "path": "solution",
                "claim_type": claim_type,
                "claim": claim,
                "source_ref": "client_fact:contract",
            }
            for claim_type, claim in (
                ("price", "1000 руб."),
                ("term", "5 дней"),
                ("guarantee", "2 года"),
            )
        ]
        self.assertEqual([], validate_content_page_dict(page, ARCHITECTURE, CASES))

    def test_hour_term_claim_requires_evidence(self) -> None:
        page = service_page_fixture()
        page["solution"] = (
            "Предварительное обследование выполняется за 24 часа после получения "
            "полного набора исходных данных от владельца участка."
        )

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("solution numeric term claim '24 часа' lacks fact_evidence", errors)

    def test_price_marker_without_currency_and_suffix_guarantee_require_evidence(self) -> None:
        page = service_page_fixture()
        page["solution"] = (
            "Стоимость обследования начинается от 5000 за объект, а согласованное "
            "покрытие получает 2 года гарантии по условиям договора."
        )

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("solution numeric price claim '5000' lacks fact_evidence", errors)
        self.assertIn("solution numeric guarantee claim '2 года' lacks fact_evidence", errors)

    def test_inherited_unit_ranges_require_exact_full_range_evidence(self) -> None:
        page = service_page_fixture()
        page["solution"] = (
            "Срок выполнения составляет от 2 до 5 дней, цена 1000–2000 руб., "
            "а гарантия действует 2–5 лет по условиям договора."
        )
        expected_claims = (
            ("term", "от 2 до 5 дней"),
            ("price", "1000–2000 руб."),
            ("guarantee", "2–5 лет"),
        )
        page["fact_evidence"] = [
            {
                "path": "solution",
                "claim_type": "term",
                "claim": "5 дней",
                "source_ref": "client_fact:contract",
            }
        ]

        self.assertEqual(expected_claims, numeric_fact_claims(page["solution"]))
        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)
        for claim_type, claim in expected_claims:
            self.assertIn(
                f"solution numeric {claim_type} claim {claim!r} lacks fact_evidence",
                errors,
            )

        page["fact_evidence"] = [
            {
                "path": "solution",
                "claim_type": claim_type,
                "claim": claim,
                "source_ref": "client_fact:contract",
            }
            for claim_type, claim in expected_claims
        ]
        self.assertEqual([], validate_content_page_dict(page, ARCHITECTURE, CASES))

    def test_replacement_character_and_placeholder_text_are_rejected(self) -> None:
        page = service_page_fixture()
        page["problem"] = "Повреждённый текст \ufffd"
        page["solution"] = "Здесь будет готовое решение"

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("problem contains Unicode replacement character", errors)
        self.assertIn("solution contains prohibited placeholder text: здесь будет", errors)

    def test_placeholder_detection_normalizes_case_and_whitespace(self) -> None:
        page = service_page_fixture()
        page["solution"] = (
            "Подробный состав услуги и итоговая стоимость предоставляются "
            "ПО   ЗАПРОСУ после получения исходных данных."
        )

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("solution contains prohibited placeholder text: по запросу", errors)

    def test_exact_fact_evidence_allows_numeric_guarantee_claim(self) -> None:
        page = service_page_fixture()
        page["solution"] = (
            "Подтверждённая договором гарантия действует 5 лет и относится к точному "
            "согласованному составу работ."
        )
        page["fact_evidence"] = [
            {
                "path": "solution",
                "claim_type": "guarantee",
                "claim": "5 лет",
                "source_ref": "client_fact:contract-2026-08-28",
            }
        ]

        self.assertEqual([], validate_content_page_dict(page, ARCHITECTURE, CASES))

    def test_page_ownership_must_match_architecture(self) -> None:
        page = service_page_fixture()
        page["canonical"] = "https://exp76.ru/wrong-owner/"

        errors = validate_content_page_dict(page, ARCHITECTURE, CASES)

        self.assertIn("canonical differs from page architecture", errors)

    def test_hub_must_link_every_architecture_child_and_article_once(self) -> None:
        hub = hub_page_fixture()
        hub["services"]["items"] = []
        hub["articles"]["items"] = []

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn("hub is missing child page S1-CHILD", errors)
        self.assertIn("hub is missing article page S1-ARTICLE", errors)

    def test_scope_items_must_not_claim_a_destination_url(self) -> None:
        hub = hub_page_fixture()
        hub["scope"]["items"][0]["url"] = "https://exp76.ru/approved-child/"

        errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)

        self.assertIn("scope item must remain descriptive and unlinked", errors)

    def test_load_content_page_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate.json"
            path.write_text('{"page_key":"A","page_key":"B"}', encoding="utf-8")

            with self.assertRaisesRegex(ContractError, "duplicate JSON key: page_key"):
                load_content_page(path)

    def test_load_content_page_returns_strict_utf8_object(self) -> None:
        page = service_page_fixture()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "service.json"
            path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")

            loaded = load_content_page(path)

        self.assertEqual(loaded.path, path)
        self.assertEqual(loaded.data["page_key"], "S1-CHILD")

    def test_real_architecture_and_case_catalog_load_without_network(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)

        self.assertEqual(35, len(architecture))
        self.assertEqual(35, len(cases))
        self.assertEqual(25, len(cases.verified_image_urls))
        self.assertEqual(
            {"S1": 4, "S2": 3, "S3": 2, "S4": 6, "S5": 6, "S6": 6, "S7": 3, "S8": 2},
            {
                service_id: len(urls)
                for service_id, urls in cases.verified_image_urls_by_service.items()
            },
        )
        self.assertEqual(
            "https://exp76.ru/services/planirovka-territorii/",
            architecture["S5-HUB"].canonical_url,
        )

    def test_audited_catalog_image_does_not_invent_case_ownership(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)
        destination = architecture["S4-ARTICLE-F668FF6F6190"]
        article = article_page_fixture()
        article.update(
            {
                "page_key": destination.destination_id,
                "service_id": destination.service_id,
                "slug": "shema-uhoda-za-sadom",
                "canonical": destination.canonical_url,
            }
        )
        article["hero"]["image"] = {
            "url": "https://exp76.ru/wp-content/uploads/2018/12/uhod1.webp",
            "alt": "Проверенная иллюстрация ухода за садом",
        }
        article["related_commercial_links"] = [
            {
                "page_key": "S4-HUB",
                "url": "https://exp76.ru/services/ukhod-za-sadom/",
                "role": "hub",
            }
        ]

        self.assertEqual([], validate_content_page_dict(article, architecture, cases))

    def test_collection_rejects_normalized_metadata_and_paragraph_duplicates(self) -> None:
        first = service_page_fixture()
        second = copy.deepcopy(first)
        second.update(
            {
                "page_key": "S1-CHILD-TWO",
                "slug": "approved-child-two",
                "canonical": "https://exp76.ru/approved-child-two/",
            }
        )
        second["seo"]["title"] = first["seo"]["title"].upper()
        second["hero"]["title"] = first["hero"]["title"].replace("е", "ё")
        architecture = dict(ARCHITECTURE)
        architecture["S1-CHILD-TWO"] = PageDestination(
            destination_id="S1-CHILD-TWO",
            service_id="S1",
            page_role="child_service",
            parent_destination_id="S1-HUB",
            canonical_url="https://exp76.ru/approved-child-two/",
            source_cluster_ids=("C-CHILD-TWO",),
            publication_status="ready",
        )

        errors = validate_content_collection(
            [
                load_memory_page("first.json", first),
                load_memory_page("second.json", second),
            ],
            architecture,
            CASES,
        )

        self.assertIn("duplicate normalized seo.title across content pages", errors)
        self.assertIn("repeated paragraph fingerprint across content pages", errors)

    def test_collection_rejects_normalized_seo_description_duplicates(self) -> None:
        first = service_page_fixture()
        second = article_page_fixture()
        second["seo"]["description"] = first["seo"]["description"].upper()

        errors = validate_content_collection(
            [load_memory_page("first.json", first), load_memory_page("second.json", second)],
            ARCHITECTURE,
            CASES,
        )

        self.assertIn("duplicate normalized seo.description across content pages", errors)

    def test_collection_accepts_only_the_exact_preserved_s4_s5_legacy_duplicate(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)
        pages = [
            load_content_page(path) for path in sorted(HUB_SOURCE_DIR.glob("*.json"))
        ]

        self.assertEqual([], validate_content_collection(pages, architecture, cases))

    def test_legacy_duplicate_policy_rejects_another_owner_or_path(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)
        by_key = {
            str(page.data["page_key"]): page
            for page in (
                load_content_page(path)
                for path in sorted(HUB_SOURCE_DIR.glob("*.json"))
            )
        }

        s1 = copy.deepcopy(by_key["S1-HUB"].data)
        s4 = copy.deepcopy(by_key["S4-HUB"].data)
        s1["related_links"]["items"][2]["text"] = LEGACY_SHARED_RELATED_TEXT
        owner_errors = validate_content_collection(
            [load_memory_page("S1.json", s1), load_memory_page("S4.json", s4)],
            architecture,
            cases,
        )
        self.assertIn("repeated paragraph fingerprint across content pages", owner_errors)

        s4 = copy.deepcopy(by_key["S4-HUB"].data)
        s5 = copy.deepcopy(by_key["S5-HUB"].data)
        s4["intro"]["body"][0] = LEGACY_SHARED_RELATED_TEXT
        s5["intro"]["body"][0] = LEGACY_SHARED_RELATED_TEXT
        path_errors = validate_content_collection(
            [load_memory_page("S4.json", s4), load_memory_page("S5.json", s5)],
            architecture,
            cases,
        )
        self.assertIn("repeated paragraph fingerprint across content pages", path_errors)

    def test_legacy_duplicate_policy_rejects_changed_copy(self) -> None:
        architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)
        cases = load_case_catalog(CASE_CATALOG_PATH)
        by_key = {
            str(page.data["page_key"]): page
            for page in (
                load_content_page(path)
                for path in sorted(HUB_SOURCE_DIR.glob("*.json"))
            )
        }
        changed = LEGACY_SHARED_RELATED_TEXT + " Изменённая версия."
        pages = []
        for page_key in ("S4-HUB", "S5-HUB"):
            data = copy.deepcopy(by_key[page_key].data)
            data["related_links"]["items"][2]["text"] = changed
            pages.append(load_memory_page(f"{page_key}.json", data))

        errors = validate_content_collection(pages, architecture, cases)

        self.assertIn("repeated paragraph fingerprint across content pages", errors)

    def test_collection_rejects_cluster_owned_by_two_destinations(self) -> None:
        architecture = dict(ARCHITECTURE)
        architecture["S1-CHILD-TWO"] = PageDestination(
            destination_id="S1-CHILD-TWO",
            service_id="S1",
            page_role="child_service",
            parent_destination_id="S1-HUB",
            canonical_url="https://exp76.ru/approved-child-two/",
            source_cluster_ids=("C-CHILD",),
            publication_status="ready",
        )

        errors = validate_content_collection([], architecture, CASES)

        self.assertIn("cluster C-CHILD has 2 page owners", errors)


def load_memory_page(name: str, data: dict[str, object]):
    from tools.site_content.contracts import ContentPage

    return ContentPage(Path(name), data)


class ReleaseManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.architecture = load_page_architecture(PAGE_ARCHITECTURE_PATH)

    def test_committed_draft_manifest_matches_architecture_bidirectionally(self) -> None:
        manifest = load_release_manifest(RELEASE_MANIFEST_PATH)

        self.assertEqual("draft", manifest["release_status"])
        self.assertEqual(26, len(manifest["managed_pages"]))
        self.assertEqual(9, len(manifest["preserved_pages"]))
        self.assertTrue(
            all(row["content_status"] == "content_pending" for row in manifest["managed_pages"])
        )
        self.assertEqual([], validate_release_manifest(manifest, self.architecture))

    def test_manifest_rejects_missing_and_unknown_architecture_pages(self) -> None:
        manifest = load_release_manifest(RELEASE_MANIFEST_PATH)
        manifest["managed_pages"].pop()
        manifest["managed_pages"].append(
            {
                "page_key": "UNKNOWN",
                "service_id": "S1",
                "page_role": "article",
                "parent_page_key": "S1-HUB",
                "canonical": "https://exp76.ru/unknown/",
                "architecture_status": "backlog",
                "content_status": "content_pending",
            }
        )

        errors = validate_release_manifest(manifest, self.architecture)

        self.assertIn("architecture page is absent from manifest", errors)
        self.assertIn("manifest page is absent from architecture", errors)

    def test_ready_manifest_rejects_pending_content_and_nonready_architecture(self) -> None:
        manifest = load_release_manifest(RELEASE_MANIFEST_PATH)
        manifest["release_status"] = "ready"

        errors = validate_release_manifest(manifest, self.architecture)

        self.assertIn("ready release contains content_pending pages", errors)
        self.assertIn("ready release contains blocked or backlog architecture pages", errors)


if __name__ == "__main__":
    unittest.main()
