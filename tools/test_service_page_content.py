"""Behavior contracts for production child-service content payloads."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.seo_semantics.complete_service_architecture import (
    build_complete_service_rows,
)
from tools.service_page_content import (
    DEFAULT_ARCHITECTURE_PATH,
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_PAGES_DIR,
    build_import_item,
    build_import_items,
    build_import_payload,
    build_deployment_bundle,
    load_architecture,
    load_default_architecture,
    main,
    render_standalone_html,
    validate_collection,
    validate_page,
)


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_PATH = DEFAULT_ARCHITECTURE_PATH
PRESENTATION_IMAGE_MANIFEST = (
    ROOT / "seo-content" / "service-pages" / "presentation-images-manifest.json"
)
RELEASE_PAYLOAD = (
    ROOT / "seo-content" / "service-pages" / "import" / "service-pages-import.json"
)


def architecture_row(*, reuse: bool = False) -> dict[str, object]:
    if reuse:
        return {
            "destination_id": "S7-CHILD-HOLIDAY",
            "service_id": "S7",
            "title": "Новогоднее освещение загородного дома",
            "slug": (
                "novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-"
                "i-jaroslavskojj-oblasti"
            ),
            "query": "монтаж новогоднего освещения дома ярославль",
            "parent_hub": "S7-HUB",
            "parent_hub_url": "https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/",
            "current_url": (
                "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-"
                "v-rybinske-i-jaroslavskojj-oblasti/"
            ),
            "target_url": (
                "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-"
                "v-rybinske-i-jaroslavskojj-oblasti/"
            ),
            "url_action": "reuse",
            "current_wp_id": "10381",
            "current_post_type": "page",
            "target_template": "servicepost.php",
            "excluded_primary_intents": (
                "постоянное фасадное освещение|ландшафтное освещение"
            ),
            "business_evidence": "business_source:wp-rest/pages/10381#published-service",
            "semantic_evidence": "Q000272",
            "boundary": (
                "Сезонный монтаж праздничной подсветки; постоянное фасадное "
                "освещение рассчитывается отдельно."
            ),
            "publication_status": "ready",
        }
    return {
        "destination_id": "S1-CHILD-SKETCH",
        "service_id": "S1",
        "title": "Эскизный проект участка",
        "slug": "eskiznyj-proekt-uchastka",
        "query": "эскизный проект участка",
        "parent_hub": "S1-HUB",
        "parent_hub_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
        "current_url": "",
        "target_url": "https://exp76.ru/eskiznyj-proekt-uchastka/",
        "url_action": "create",
        "current_wp_id": "",
        "current_post_type": "",
        "target_template": "",
        "excluded_primary_intents": "полный рабочий проект|кадастровый план",
        "business_evidence": "business_source:wp-rest/pages/1",
        "semantic_evidence": "Q000002",
        "boundary": (
            "Услуга включает эскиз, зонирование и общую концепцию; полный комплект "
            "рабочих материалов рассчитывается отдельно."
        ),
        "publication_status": "ready",
    }


def evidence_entry(destination_id: str, *, attachment_id: int = 901) -> dict[str, object]:
    return {
        "destination_id": destination_id,
        "evidence_class": "A",
        "exact_case_ids": [501],
        "exact_case_urls": ["https://exp76.ru/case/example/"],
        "contextual_page_ids": [601],
        "media_pool": "M1",
        "media": [
            {
                "attachment_id": attachment_id,
                "url": f"https://exp76.ru/wp-content/uploads/2026/08/{attachment_id}.webp",
                "pool": "M1",
                "asset_kind": "case_photo",
                "source_page_id": 501,
            }
        ],
        "asset_kind": "case_photo",
        "safe_caption_rule": "Можно называть подтверждённым кейсом.",
        "caveat": "Кейс подтверждает тип работ, но не индивидуальную смету.",
        "needs_client_asset_or_generated_illustration": False,
    }


def valid_page(*, reuse: bool = False) -> dict[str, object]:
    row = architecture_row(reuse=reuse)
    destination_id = str(row["destination_id"])
    service_id = str(row["service_id"])
    current_wp_id = int(str(row["current_wp_id"])) if reuse else None
    return {
        "schema_version": 1,
        "destination_id": destination_id,
        "service_id": service_id,
        "deployment": {
            "action": str(row["url_action"]),
            "current_wp_id": current_wp_id,
            "current_post_type": "page" if reuse else None,
            "current_url": str(row["current_url"]) if reuse else None,
            "target_template": "servicepost.php" if reuse else None,
            "preserve_id": reuse,
            "preserve_permalink": reuse,
        },
        "slug": str(row["slug"]),
        "canonical": str(row["target_url"]),
        "post_title": str(row["title"]),
        "seo": {
            "title": f"{row['title']} в Ярославле — заказать услугу",
            "description": (
                f"{row['title']} для загородного участка в Ярославле и области: "
                "разбираем задачу, состав работ и факторы сметы."
            ),
        },
        "h1": f"{row['title']} в Ярославле",
        "lead": (
            f"Подготовим {str(row['title']).lower()} с учётом рельефа, существующих "
            "объектов и дальнейшего использования участка."
        ),
        "scope": {
            "heading": "Что входит в услугу и какой результат получает заказчик",
            "text": "Состав работ определяем после изучения участка и согласования задачи.",
            "results": [
                {
                    "title": "Понятное решение",
                    "text": "Фиксируем согласованный результат и границы работ до начала реализации.",
                },
                {
                    "title": "Основа для следующих работ",
                    "text": "Учитываем связанные этапы благоустройства и существующие элементы участка.",
                },
            ],
        },
        "audience": {
            "heading": "Кому и когда нужна эта услуга",
            "text": "Услуга подходит владельцам участков, которым нужен прогнозируемый результат.",
            "items": [
                {
                    "title": "До начала благоустройства",
                    "text": "Когда важно согласовать решение до закупки материалов и выхода техники.",
                },
                {
                    "title": "При изменении участка",
                    "text": "Когда существующая территория больше не соответствует сценарию использования.",
                },
                {
                    "title": "Перед связанными работами",
                    "text": "Когда результат должен учитывать будущие посадки, покрытия и инженерные системы.",
                },
            ],
        },
        "process": {
            "heading": "Как проходит работа",
            "steps": [
                {"title": "Заявка", "text": "Уточняем задачу и исходные данные участка."},
                {"title": "Осмотр", "text": "Проверяем условия, доступы и существующие объекты."},
                {"title": "Решение", "text": "Предлагаем состав работ в согласованных границах."},
                {"title": "Смета", "text": "Фиксируем материалы, операции и факторы стоимости."},
                {"title": "Выполнение", "text": "Проводим согласованные работы и проверяем результат."},
            ],
        },
        "pricing": {
            "heading": "От чего зависит стоимость",
            "text": "Точную смету готовим после уточнения исходных условий и состава работ.",
            "factors": [
                {"title": "Площадь и объём", "text": "Учитываем фактический фронт работ на участке."},
                {"title": "Условия участка", "text": "Оцениваем рельеф, грунт, доступы и ограничения."},
                {"title": "Состав решения", "text": "Считаем только согласованные операции и материалы."},
            ],
        },
        "proof": {
            "evidence_ref": destination_id,
            "case_ids": [501],
            "main_image_attachment_id": 901,
            "main_image_alt": f"{row['title']} — пример профильных работ",
            "caption": "Подтверждённый пример профильных работ компании на загородном участке.",
        },
        "geo": {
            "heading": "Работаем в Ярославле и области",
            "text": "Выезжаем на участки в Ярославле, Рыбинске и населённых пунктах Ярославской области.",
            "areas": ["Ярославль", "Рыбинск", "Ярославская область"],
        },
        "faq": {
            "heading": "Вопросы об услуге",
            "items": [
                {"question": "Что нужно для предварительной оценки?", "answer": "Пришлите план, фотографии и кратко опишите желаемый результат."},
                {"question": "Нужен ли выезд на участок?", "answer": "Выезд помогает проверить условия и подготовить точный состав работ."},
                {"question": "Можно выполнить работу поэтапно?", "answer": "Поэтапность согласуем, если она не нарушает техническую последовательность."},
                {"question": "Что влияет на смету?", "answer": "На смету влияют объём, условия участка, материалы и выбранный состав работ."},
                {"question": "Как согласуется результат?", "answer": "До начала работ фиксируем задачу, границы и критерии готовности результата."},
            ],
        },
        "links": {
            "parent": {
                "page_key": str(row["parent_hub"]),
                "url": str(row["parent_hub_url"]),
                "label": "Все услуги направления",
            },
            "related_services": [
                {
                    "page_key": f"{service_id}-CHILD-RELATED",
                    "url": "https://exp76.ru/related-service/",
                    "label": "Связанная услуга",
                }
            ],
        },
        "cta": {
            "heading": "Обсудить задачу по участку",
            "text": "Пришлите план или фотографии — уточним состав работ и подготовим расчёт.",
            "primary_label": "Получить расчёт",
            "primary_url": "#calc",
            "secondary_label": "Задать вопрос",
            "secondary_url": "#consultation",
        },
        "boundary": {
            "summary": str(row["boundary"]),
            "excluded_intents": (
                str(row["excluded_primary_intents"]).split("|")
                if str(row["excluded_primary_intents"])
                else ["работы за пределами согласованной услуги"]
            ),
        },
    }


class ServicePageValidationTests(unittest.TestCase):
    def test_presentation_images_accept_three_separate_non_proof_roles(self) -> None:
        row = architecture_row()
        page = valid_page()
        page["presentation_images"] = {
            "hero": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-hero.webp",
                "alt": "Ландшафтный архитектор обсуждает эскиз участка",
            },
            "context": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-context.webp",
                "alt": "Рабочий стол с эскизом благоустройства участка",
            },
            "card": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-card.webp",
                "alt": "Эскизный проект загородного участка",
            },
        }

        self.assertEqual(
            [],
            validate_page(page, row, evidence_entry(str(row["destination_id"]))),
        )

    def test_presentation_images_fail_closed_for_incomplete_or_unsafe_roles(self) -> None:
        row = architecture_row()
        evidence = evidence_entry(str(row["destination_id"]))
        base = valid_page()
        base["presentation_images"] = {
            "hero": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-hero.webp",
                "alt": "Ландшафтный архитектор обсуждает эскиз участка",
            },
            "context": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-context.webp",
                "alt": "Рабочий стол с эскизом благоустройства участка",
            },
            "card": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-card.webp",
                "alt": "Эскизный проект загородного участка",
            },
        }
        mutations = {
            "missing role": (
                lambda page: page["presentation_images"].pop("card"),
                "presentation_images.card is required",
            ),
            "external URL": (
                lambda page: page["presentation_images"]["hero"].update(
                    url="https://example.com/borrowed.webp"
                ),
                "presentation_images.hero.url must be a generated context URL",
            ),
            "empty alt": (
                lambda page: page["presentation_images"]["context"].update(alt=""),
                "presentation_images.context.alt must contain at least 12 characters",
            ),
            "unexpected field": (
                lambda page: page["presentation_images"]["card"].update(caption="extra"),
                "presentation_images.card.caption is not allowed",
            ),
        }

        for label, (mutate, expected) in mutations.items():
            with self.subTest(label=label):
                page = copy.deepcopy(base)
                mutate(page)
                self.assertIn(expected, validate_page(page, row, evidence))

    def test_valid_page_is_bound_to_architecture_and_evidence(self) -> None:
        row = architecture_row()
        page = valid_page()
        evidence = evidence_entry(str(row["destination_id"]))

        self.assertEqual([], validate_page(page, row, evidence))

    def test_reuse_contract_freezes_identity_permalink_and_template(self) -> None:
        row = architecture_row(reuse=True)
        page = valid_page(reuse=True)
        evidence = evidence_entry(str(row["destination_id"]))

        self.assertEqual([], validate_page(page, row, evidence))
        for field, bad_value in (
            ("current_wp_id", 9999),
            ("current_post_type", "post"),
            ("current_url", "https://exp76.ru/wrong/"),
            ("target_template", "wrong.php"),
            ("preserve_id", False),
            ("preserve_permalink", False),
        ):
            broken = copy.deepcopy(page)
            broken["deployment"][field] = bad_value
            with self.subTest(field=field):
                errors = validate_page(broken, row, evidence)
                self.assertTrue(any(f"deployment.{field}" in error for error in errors))

    def test_required_content_blocks_fail_closed_at_production_minima(self) -> None:
        row = architecture_row()
        evidence = evidence_entry(str(row["destination_id"]))
        mutations = (
            ("scope.results", lambda page: page["scope"].update(results=[])),
            ("audience.items", lambda page: page["audience"].update(items=[])),
            (
                "process.steps",
                lambda page: page["process"].update(
                    steps=page["process"]["steps"][:4]
                ),
            ),
            ("pricing.factors", lambda page: page["pricing"].update(factors=[])),
            ("geo.text", lambda page: page["geo"].update(text="")),
            (
                "faq.items",
                lambda page: page["faq"].update(items=page["faq"]["items"][:4]),
            ),
            (
                "links.related_services",
                lambda page: page["links"].update(related_services=[]),
            ),
            ("cta.text", lambda page: page["cta"].update(text="")),
            (
                "boundary.excluded_intents",
                lambda page: page["boundary"].update(excluded_intents=[]),
            ),
        )
        for expected_path, mutate in mutations:
            broken = valid_page()
            mutate(broken)
            with self.subTest(path=expected_path):
                errors = validate_page(broken, row, evidence)
                self.assertTrue(
                    any(expected_path in error for error in errors),
                    errors,
                )

    def test_placeholders_absolute_claims_and_fictional_prices_are_rejected(self) -> None:
        row = architecture_row()
        evidence = evidence_entry(str(row["destination_id"]))
        mutations = (
            (
                "placeholder",
                lambda page: page["scope"].update(
                    text="TODO: сюда позднее будет добавлен окончательный текст страницы."
                ),
            ),
            (
                "unsupported absolute claim",
                lambda page: page.update(
                    lead=(
                        "Гарантируем идеальный результат для любого участка независимо "
                        "от исходных условий."
                    )
                ),
            ),
            (
                "fictional price",
                lambda page: page["pricing"]["factors"][0].update(
                    text="Фиксированная стоимость составляет 25 000 ₽ для каждого участка."
                ),
            ),
            (
                "unsupported numeric claim",
                lambda page: page["process"]["steps"][4].update(
                    text="Гарантированно завершаем весь этап за 3 дня."
                ),
            ),
        )
        for expected_error, mutate in mutations:
            broken = valid_page()
            mutate(broken)
            with self.subTest(rule=expected_error):
                errors = validate_page(broken, row, evidence)
                self.assertTrue(
                    any(expected_error in error for error in errors),
                    errors,
                )

    def test_internal_seo_language_is_rejected_from_customer_facing_copy(self) -> None:
        row = architecture_row()
        evidence = evidence_entry(str(row["destination_id"]))
        mutations = (
            (
                "audience.text contains internal SEO language",
                lambda page: page["audience"].update(
                    text=(
                        "Разбираем задачу отдельно и не переносим на неё обещания "
                        "соседних услуг направления."
                    )
                ),
            ),
            (
                "faq.heading contains internal SEO language",
                lambda page: page["faq"].update(
                    heading="Вопросы про посадка растений на участке"
                ),
            ),
            (
                "boundary.summary contains internal SEO language",
                lambda page: page["boundary"].update(
                    summary="Земляные работы принадлежат S5, а этот интент остаётся здесь."
                ),
            ),
            (
                "faq.items[0].answer contains internal SEO language",
                lambda page: page["faq"]["items"][0].update(
                    answer=(
                        "Нет, эта задача относится к другому кластеру и отдельному "
                        "поисковому интенту."
                    )
                ),
            ),
        )
        for expected_error, mutate in mutations:
            broken = valid_page()
            mutate(broken)
            with self.subTest(rule=expected_error):
                errors = validate_page(broken, row, evidence)
                self.assertIn(expected_error, errors)

    def test_non_case_media_must_be_described_honestly(self) -> None:
        row = architecture_row()
        page = valid_page()
        page["proof"]["case_ids"] = []
        evidence = evidence_entry(str(row["destination_id"]))
        evidence["evidence_class"] = "B"
        evidence["exact_case_ids"] = []
        evidence["exact_case_urls"] = []
        evidence["asset_kind"] = "illustration"
        evidence["media"][0]["asset_kind"] = "illustration"
        evidence["media"][0]["source_page_id"] = 601

        errors = validate_page(page, row, evidence)
        self.assertTrue(any("Иллюстрация:" in error for error in errors), errors)

        page["proof"]["caption"] = (
            "Иллюстрация: схема показывает принцип организации работ на участке."
        )
        self.assertEqual([], validate_page(page, row, evidence))

        page["proof"]["caption"] = (
            "Иллюстрация: наш выполненный объект и реализованные работы компании."
        )
        errors = validate_page(page, row, evidence)
        self.assertTrue(any("non-case media" in error for error in errors), errors)

        page["proof"]["caption"] = (
            "Иллюстрация: фотография с нашего объекта после завершения работ."
        )
        errors = validate_page(page, row, evidence)
        self.assertTrue(any("non-case media" in error for error in errors), errors)

    def test_context_photo_with_recommendation_flag_is_still_production_usable(self) -> None:
        row = architecture_row()
        page = valid_page()
        page["proof"]["case_ids"] = []
        page["proof"]["caption"] = (
            "Контекстное фото показывает релевантный тип территории без привязки к кейсу."
        )
        evidence = evidence_entry(str(row["destination_id"]))
        evidence["evidence_class"] = "C"
        evidence["exact_case_ids"] = []
        evidence["exact_case_urls"] = []
        evidence["asset_kind"] = "context_photo"
        evidence["media"][0]["asset_kind"] = "context_photo"
        evidence["media"][0]["source_page_id"] = 601
        evidence["needs_client_asset_or_generated_illustration"] = True

        self.assertEqual([], validate_page(page, row, evidence))

    def test_nested_shape_registry_readiness_and_media_origin_fail_closed(self) -> None:
        base_row = architecture_row()
        base_evidence = evidence_entry(str(base_row["destination_id"]))
        mutations = (
            (
                "seo.unexpected is not allowed",
                lambda page, row, evidence: page["seo"].update(unexpected="value"),
            ),
            (
                "architecture publication_status must be ready",
                lambda page, row, evidence: row.update(publication_status="backlog"),
            ),
            (
                "proof main image source_page_id is not confirmed",
                lambda page, row, evidence: evidence["media"][0].update(
                    source_page_id=999999
                ),
            ),
            (
                "faq.items contains duplicate questions",
                lambda page, row, evidence: page["faq"]["items"][1].update(
                    question=page["faq"]["items"][0]["question"]
                ),
            ),
        )
        for expected_error, mutate in mutations:
            page = valid_page()
            row = copy.deepcopy(base_row)
            evidence = copy.deepcopy(base_evidence)
            mutate(page, row, evidence)
            with self.subTest(expected_error=expected_error):
                errors = validate_page(page, row, evidence)
                self.assertTrue(
                    any(expected_error in error for error in errors),
                    errors,
                )

    def test_collection_requires_unique_search_snippets_h1_and_lead(self) -> None:
        first_row = architecture_row()
        second_row = copy.deepcopy(first_row)
        second_row.update(
            destination_id="S1-CHILD-SECOND",
            title="Вторая услуга",
            slug="vtoraya-usluga",
            target_url="https://exp76.ru/vtoraya-usluga/",
            excluded_primary_intents="",
            boundary="Граница второй услуги отделяет её от соседних направлений.",
        )
        first = valid_page()
        second = copy.deepcopy(first)
        second.update(
            destination_id=second_row["destination_id"],
            slug=second_row["slug"],
            canonical=second_row["target_url"],
            post_title=second_row["title"],
        )
        second["proof"]["evidence_ref"] = second_row["destination_id"]
        second["proof"]["main_image_attachment_id"] = 902
        second["boundary"]["summary"] = second_row["boundary"]
        second["boundary"]["excluded_intents"] = ["соседние направления"]
        architecture = {
            str(first_row["destination_id"]): first_row,
            str(second_row["destination_id"]): second_row,
        }
        evidence = {
            str(first_row["destination_id"]): evidence_entry(
                str(first_row["destination_id"]), attachment_id=901
            ),
            str(second_row["destination_id"]): evidence_entry(
                str(second_row["destination_id"]), attachment_id=902
            ),
        }

        errors = validate_collection([first, second], architecture, evidence)

        for field in ("seo.title", "seo.description", "h1", "lead"):
            self.assertTrue(any(f"duplicate {field}" in error for error in errors), errors)


class DefaultServiceArchitectureTests(unittest.TestCase):
    def test_default_registry_is_the_authoritative_complete_65(self) -> None:
        architecture = load_default_architecture()
        expected_rows = build_complete_service_rows()
        expected_ids = [row["destination_id"] for row in expected_rows]

        self.assertEqual(expected_ids, list(architecture))
        self.assertEqual(65, len(architecture))
        self.assertEqual(
            {"S7-CHILD-HOLIDAY"},
            {
                destination_id
                for destination_id, row in architecture.items()
                if row["url_action"] == "reuse"
            },
        )
        self.assertNotIn("S5-CHILD-STUMPS", architecture)
        self.assertEqual(
            {f"S{number}" for number in range(9, 16)},
            {
                row["service_id"]
                for row in architecture.values()
                if int(row["service_id"][1:]) >= 9
            },
        )
        self.assertEqual(
            ROOT / "seo-content" / "service-pages" / "pages",
            DEFAULT_PAGES_DIR,
        )
        self.assertEqual(
            ROOT / "seo-content" / "service-pages" / "evidence.json",
            DEFAULT_EVIDENCE_PATH,
        )

    def test_default_loader_rejects_checked_in_csv_drift(self) -> None:
        rows = build_complete_service_rows()
        rows[0] = {**rows[0], "title": "Несогласованный заголовок"}

        with tempfile.TemporaryDirectory() as temporary:
            drifted_path = Path(temporary) / "complete_service_children.csv"
            with drifted_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with patch(
                "tools.service_page_content.DEFAULT_ARCHITECTURE_PATH",
                drifted_path,
            ):
                with self.assertRaisesRegex(ValueError, "drift"):
                    load_default_architecture()


class ServicePageRenderingTests(unittest.TestCase):
    def test_import_item_keeps_proof_main_image_and_uses_context_asset_for_acf(self) -> None:
        row = architecture_row()
        page = valid_page()
        page["presentation_images"] = {
            "hero": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-hero.webp",
                "alt": "Ландшафтный архитектор обсуждает эскиз участка",
            },
            "context": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-context.webp",
                "alt": "Рабочий стол с эскизом благоустройства участка",
            },
            "card": {
                "url": "https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-sketch-card.webp",
                "alt": "Эскизный проект загородного участка",
            },
        }
        evidence = evidence_entry(str(row["destination_id"]))

        item = build_import_item(page, row, evidence)

        self.assertEqual(
            {
                "url": "https://exp76.ru/wp-content/uploads/2026/08/901.webp",
                "alt": page["proof"]["main_image_alt"],
            },
            item["main_image"],
        )
        self.assertEqual(page["presentation_images"], item["presentation_images"])
        self.assertEqual(
            page["presentation_images"]["context"]["url"],
            item["acf"]["ns87_problem_items"][0]["image"],
        )

    def test_context_photo_manifest_has_21_ready_verified_theme_assets(self) -> None:
        manifest = json.loads(PRESENTATION_IMAGE_MANIFEST.read_text(encoding="utf-8"))
        assets = manifest["assets"]

        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual("ready", manifest["release_status"])
        self.assertEqual(21, manifest["asset_count"])
        self.assertEqual(21, len(assets))
        self.assertEqual(21, len({asset["asset_id"] for asset in assets}))
        self.assertTrue(all(asset["asset_kind"] == "context_photo" for asset in assets))
        self.assertTrue(all("attachment_id" not in asset["output"] for asset in assets))
        generated_prefix = (
            "https://exp76.ru/wp-content/themes/land76wp/generated/context/"
        )
        for asset in assets:
            output = asset["output"]
            filename = output["filename"]
            self.assertRegex(filename, r"^context-photo-[a-z0-9]+(?:-[a-z0-9]+)*\.webp$")
            self.assertEqual("ready", output["status"])
            self.assertEqual(generated_prefix + filename, output["url"])
            local_path = ROOT / output["local_path"]
            self.assertTrue(local_path.is_file(), local_path)
            self.assertEqual(output["bytes"], local_path.stat().st_size)
            self.assertRegex(output["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(1600, output["width"])
            self.assertEqual(1000, output["height"])
        targets = [target for asset in assets for target in asset["targets"]]
        self.assertEqual(163, len(targets))
        self.assertTrue(all(not target["field"].startswith("proof.") for target in targets))
        evidence = json.loads(DEFAULT_EVIDENCE_PATH.read_text(encoding="utf-8"))
        verified_case_urls = {
            media["url"]
            for service in evidence["services"]
            for media in service["media"]
            if media.get("asset_kind") == "case_photo"
        }
        for hub_path in (ROOT / "seo-content" / "service-hubs" / "hubs").glob("S*.json"):
            hub = json.loads(hub_path.read_text(encoding="utf-8"))
            verified_case_urls.update(
                case["image"]["url"] for case in hub["proof"]["cases"]
            )
        expected_child_roles: dict[str, dict[str, dict[str, str]]] = {}
        for asset in assets:
            expected_image = {
                "url": asset["output"]["url"],
                "alt": asset["alt"],
            }
            for target in asset["targets"]:
                if target["page_key"].endswith("-HUB"):
                    continue
                role_match = re.fullmatch(
                    r"presentation_images\.(hero|context|card)",
                    target["field"],
                )
                self.assertIsNotNone(role_match, target)
                assert role_match is not None
                expected_child_roles.setdefault(target["page_key"], {})[
                    role_match.group(1)
                ] = expected_image
        self.assertEqual(32, len(expected_child_roles))
        for page_key, expected_roles in expected_child_roles.items():
            page = json.loads(
                (DEFAULT_PAGES_DIR / f"{page_key}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(expected_roles, page["presentation_images"], page_key)

        for target in targets:
            if not target["page_key"].endswith("-HUB"):
                continue
            service_id = target["page_key"].removesuffix("-HUB")
            hub = json.loads(
                (
                    ROOT / "seo-content" / "service-hubs" / "hubs" / f"{service_id}.json"
                ).read_text(encoding="utf-8")
            )
            if target["field"] == "hero.image":
                current_image = hub["hero"]["image"]
            else:
                match = re.fullmatch(
                    r"(scope|services|articles)\.items\[(\d+)\]\.image",
                    target["field"],
                )
                self.assertIsNotNone(match, target)
                assert match is not None
                current_image = hub[match.group(1)]["items"][int(match.group(2))]["image"]
            asset = next(
                item for item in assets if target in item["targets"]
            )
            self.assertEqual(asset["output"]["url"], current_image["url"], target)
            self.assertEqual(asset["alt"], current_image["alt"], target)
            self.assertEqual("context_photo", current_image.get("asset_kind"), target)
            self.assertTrue(
                current_image.get("caption", "").startswith("Контекстная иллюстрация:"),
                target,
            )
            self.assertNotIn(current_image["url"], verified_case_urls, target)
        for role in ("hero", "context", "card"):
            self.assertIn(
                {"page_key": "S6-CHILD-STONE", "field": f"presentation_images.{role}"},
                next(
                    asset["targets"]
                    for asset in assets
                    if asset["asset_id"] == "stone-retaining-wall"
                ),
            )

    def test_import_item_uses_standard_schema_and_php_compatible_checksum(self) -> None:
        row = architecture_row()
        page = valid_page()
        evidence = evidence_entry(str(row["destination_id"]))

        item = build_import_item(page, row, evidence)

        self.assertEqual("child_service", item["role"])
        self.assertEqual("S1", item["topic_key"])
        self.assertEqual([501], item["case_ids"])
        self.assertEqual(
            ["S1-HUB", "S1-CHILD-RELATED"],
            item["related_service_page_keys"],
        )
        self.assertNotIn("deployment", item)
        self.assertNotIn("current_wp_id", item)
        self.assertEqual(5, len(item["acf"]["ns87_faq_items"]))
        self.assertNotIn("service-content--links", item["post_content"])
        self.assertEqual(
            page["pricing"]["factors"][0]["text"],
            item["acf"]["ns87_price_rows"][0]["term"],
        )
        canonical_item = {key: value for key, value in item.items() if key != "checksum"}
        encoded = json.dumps(
            canonical_item,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(encoded).hexdigest(), item["checksum"])

    def test_managed_payload_keeps_audit_caption_private_and_uses_factor_rows(self) -> None:
        row = architecture_row()
        page = valid_page()
        page["proof"]["caption"] = (
            "WP 8620 подтверждает источник; объект не приписан "
            "неподтверждённому этапу и публично не заявляется."
        )
        evidence = evidence_entry(str(row["destination_id"]))

        item = build_import_item(page, row, evidence)

        self.assertIn("WP 8620", page["proof"]["caption"])
        self.assertNotIn("service-media-caption", item["post_content"])
        for forbidden in (
            "WP 8620",
            "не приписан",
            "не заявляется",
            "не подтверждается",
            "Исключённые основные интенты",
        ):
            self.assertNotIn(forbidden, item["post_content"])
        self.assertIn("Не входит в услугу", item["post_content"])
        self.assertEqual(
            {
                "service": page["pricing"]["factors"][0]["title"],
                "price": "",
                "term": page["pricing"]["factors"][0]["text"],
            },
            item["acf"]["ns87_price_rows"][0],
        )
        self.assertNotIn(
            "по расчёту",
            json.dumps(item["acf"]["ns87_price_rows"], ensure_ascii=False).casefold(),
        )

    def test_checked_in_managed_release_contains_only_customer_facing_copy(self) -> None:
        pages = {
            payload["destination_id"]: payload
            for payload in (
                json.loads(path.read_text(encoding="utf-8"))
                for path in DEFAULT_PAGES_DIR.glob("*.json")
            )
        }
        payload = json.loads(RELEASE_PAYLOAD.read_text(encoding="utf-8"))
        children = {
            item["page_key"]: item
            for item in payload["items"]
            if item["role"] == "child_service"
        }
        self.assertEqual(65, len(pages))
        self.assertEqual(set(pages), set(children))

        internal_pattern = re.compile(
            r"(?:\bS\d+(?:-[A-Z0-9-]+)?\b|\b(?:SEO|SERP|overlap|интент|кластер)\b|"
            r"не переносим|обещания соседних|принадлежит|защищ[её]нн\w* владельц\w*|"
            r"неподтвержд[её]нн\w*|раздельн\w+ публикац\w+|\bхаб\w*\b|"
            r"URL-владел\w*|утвержд[её]нн\w* архитектур\w*|"
            r"(?:действующ\w*|стар\w*) страниц\w*|в этом контенте|"
            r"\bCMS\b|\bWP\s+\d+\b|опубликованн\w+ (?:текст\w*|материал\w*)|"
            r"не подтвержда\w*|не заявля\w*)",
            re.IGNORECASE,
        )
        forensic_pattern = re.compile(
            r"(?:service-media-caption|WP\s+\d+|не приписан|не заявляется|"
            r"не подтверждается|опубликованные материалы подтверждают|"
            r"фото со страницы услуги)",
            re.IGNORECASE,
        )
        for page_key, page in pages.items():
            with self.subTest(page_key=page_key):
                self.assertNotIn("не переносим", page["audience"]["text"].casefold())
                self.assertNotIn("обещания соседних", page["audience"]["text"].casefold())
                self.assertNotIn("вопросы про", page["faq"]["heading"].casefold())
                public_boundary = json.dumps(page["boundary"], ensure_ascii=False)
                public_faq = json.dumps(page["faq"], ensure_ascii=False)
                self.assertIsNone(internal_pattern.search(public_boundary), public_boundary)
                self.assertIsNone(internal_pattern.search(public_faq), public_faq)

                item = children[page_key]
                acf = item["acf"]
                self.assertEqual(page["audience"]["text"], acf["ns87_problem_text"])
                self.assertEqual(page["faq"]["heading"], acf["ns87_faq_title"])
                self.assertIsNone(forensic_pattern.search(item["post_content"]))
                self.assertIsNone(internal_pattern.search(item["post_content"]))
                public_acf = json.dumps(acf, ensure_ascii=False)
                self.assertIsNone(internal_pattern.search(public_acf), public_acf)
                price_rows = acf["ns87_price_rows"]
                self.assertGreaterEqual(len(price_rows), 3)
                self.assertEqual(len(price_rows), len({row["service"] for row in price_rows}))
                for row in price_rows:
                    self.assertEqual("", row["price"])
                    self.assertGreaterEqual(len(row["service"].strip()), 3)
                    self.assertGreaterEqual(len(row["term"].strip()), 20)
                self.assertNotIn(
                    "по расчёту",
                    json.dumps(acf, ensure_ascii=False).casefold(),
                )

    def test_import_payload_wrapper_matches_release_schema(self) -> None:
        row = architecture_row()
        page = valid_page()
        evidence = evidence_entry(str(row["destination_id"]))
        item = build_import_item(page, row, evidence)
        manifest_hash = "a" * 64

        payload = build_import_payload(
            [item],
            release_id="service-hubs-2026-08-28",
            manifest_sha256=manifest_hash,
        )

        self.assertEqual(
            {
                "schema_version": 1,
                "release_id": "service-hubs-2026-08-28",
                "release_status": "ready",
                "manifest_sha256": manifest_hash,
                "items": [item],
            },
            payload,
        )
        with self.assertRaisesRegex(ValueError, "manifest_sha256"):
            build_import_payload(
                [item],
                release_id="service-hubs-2026-08-28",
                manifest_sha256="0" * 64,
            )

    def test_deployment_bundle_binds_ready_payload_to_exact_inventory(self) -> None:
        row = architecture_row()
        item = build_import_item(valid_page(), row, evidence_entry(str(row["destination_id"])))
        source_hash = "b" * 64

        manifest, payload = build_deployment_bundle(
            [item],
            release_id="service-hubs-2026-08-28",
            source_manifest_sha256=source_hash,
        )

        self.assertEqual(
            [{"page_key": item["page_key"], "checksum": item["checksum"]}],
            manifest["items"],
        )
        self.assertEqual("ready", manifest["release_status"])
        self.assertEqual(source_hash, manifest["source_manifest_sha256"])
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(manifest_bytes).hexdigest(),
            payload["manifest_sha256"],
        )
        self.assertEqual([item], payload["items"])

    def test_standalone_renderer_escapes_text_and_never_emits_script_urls(self) -> None:
        page = valid_page(reuse=True)
        page["h1"] = '<script>alert("x")</script> Безопасный заголовок услуги'
        page["links"]["related_services"][0]["label"] = "<b>Связанная</b> услуга"
        page["cta"]["primary_url"] = "javascript:alert(1)"

        rendered = render_standalone_html(page)

        self.assertNotIn("<script", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;b&gt;Связанная&lt;/b&gt;", rendered)
        self.assertNotIn("javascript:", rendered)

    def test_reuse_item_keeps_nested_permalink_and_uses_managed_template_content(self) -> None:
        row = architecture_row(reuse=True)
        page = valid_page(reuse=True)
        evidence = evidence_entry(str(row["destination_id"]))

        item = build_import_item(page, row, evidence)

        self.assertEqual(row["target_url"], item["canonical"])
        self.assertNotIn("<h1>", item["post_content"])
        self.assertNotIn("<details>", item["post_content"])
        self.assertIn("service-content--scope", item["post_content"])
        self.assertEqual(5, len(item["acf"]["ns87_faq_items"]))
        self.assertNotIn("current_wp_id", item)
        self.assertNotIn("url_action", item)

    def test_current_registry_builds_65_standard_items_with_one_reuse(self) -> None:
        architecture = load_default_architecture()
        pages: list[dict[str, object]] = []
        evidence: dict[str, dict[str, object]] = {}
        service_rows: dict[str, list[dict[str, str]]] = {}
        for row in architecture.values():
            service_rows.setdefault(row["service_id"], []).append(row)

        for index, row in enumerate(architecture.values(), start=1):
            page = valid_page()
            destination_id = row["destination_id"]
            reuse = row["url_action"] == "reuse"
            page.update(
                destination_id=destination_id,
                service_id=row["service_id"],
                slug=row["slug"],
                canonical=row["target_url"],
                post_title=row["title"],
                h1=f"{row['title']} — вариант {index}",
                lead=(
                    f"{row['title']}: уникальное описание задачи, вариант {index}, для "
                    "владельцев участков в Ярославле и Ярославской области."
                ),
            )
            page["seo"] = {
                "title": f"{row['title']} в Ярославле — вариант {index}",
                "description": (
                    f"{row['title']} для участка: состав услуги, порядок работ и факторы "
                    f"сметы. Уникальный вариант {index}."
                ),
            }
            page["deployment"] = {
                "action": row["url_action"],
                "current_wp_id": int(row["current_wp_id"]) if reuse else None,
                "current_post_type": row["current_post_type"] or None,
                "current_url": row["current_url"] or None,
                "target_template": row["target_template"] or None,
                "preserve_id": reuse,
                "preserve_permalink": reuse,
            }
            page["proof"] = {
                "evidence_ref": destination_id,
                "case_ids": [],
                "main_image_attachment_id": 1000 + index,
                "main_image_alt": f"{row['title']} — контекстное изображение",
                "caption": (
                    "Контекстное фото показывает релевантные условия участка без "
                    "утверждения о выполненном кейсе."
                ),
            }
            page["boundary"] = {
                "summary": (
                    "Услуга имеет самостоятельный состав работ и понятный результат "
                    "для заказчика."
                ),
                "excluded_intents": ["работы вне согласованного состава услуги"],
            }
            siblings = [
                candidate
                for candidate in service_rows[row["service_id"]]
                if candidate["destination_id"] != destination_id
            ]
            page["links"] = {
                "parent": {
                    "page_key": row["parent_hub"],
                    "url": row["parent_hub_url"],
                    "label": "Все услуги направления",
                },
                "related_services": [
                    {
                        "page_key": siblings[0]["destination_id"],
                        "url": siblings[0]["target_url"],
                        "label": siblings[0]["title"],
                    }
                ],
            }
            pages.append(page)
            evidence[destination_id] = {
                **evidence_entry(destination_id, attachment_id=1000 + index),
                "evidence_class": "C",
                "exact_case_ids": [],
                "exact_case_urls": [],
                "asset_kind": "context_photo",
                "media": [
                    {
                        "attachment_id": 1000 + index,
                        "url": (
                            "https://exp76.ru/wp-content/uploads/2026/08/"
                            f"{1000 + index}.webp"
                        ),
                        "pool": "CONTEXT",
                        "asset_kind": "context_photo",
                        "source_page_id": 601,
                    }
                ],
                "needs_client_asset_or_generated_illustration": True,
            }

        items = build_import_items(pages, architecture, evidence)

        self.assertEqual(65, len(items))
        self.assertEqual(65, len({item["page_key"] for item in items}))
        self.assertNotIn("S5-CHILD-STUMPS", {item["page_key"] for item in items})
        self.assertEqual(
            {"S7-CHILD-HOLIDAY"},
            {
                destination_id
                for destination_id, row in architecture.items()
                if row["url_action"] == "reuse"
            },
        )
        self.assertTrue(all("<h1>" not in item["post_content"] for item in items))

    def test_cli_validates_and_renders_items_from_a_pages_directory(self) -> None:
        row = architecture_row()
        page = valid_page()
        evidence = evidence_entry(str(row["destination_id"]))
        related_row = copy.deepcopy(row)
        related_row.update(
            destination_id="S1-CHILD-RELATED",
            title="Связанная услуга",
            slug="related-service",
            target_url="https://exp76.ru/related-service/",
            excluded_primary_intents="",
            boundary="Связанная услуга имеет отдельную коммерческую границу.",
        )
        related_page = copy.deepcopy(page)
        related_page.update(
            destination_id=related_row["destination_id"],
            slug=related_row["slug"],
            canonical=related_row["target_url"],
            post_title=related_row["title"],
            h1="Связанная услуга для загородного участка",
            lead=(
                "Отдельная связанная услуга с самостоятельным результатом, составом "
                "работ и понятной границей ответственности."
            ),
        )
        related_page["seo"] = {
            "title": "Связанная услуга в Ярославле — заказать работы",
            "description": (
                "Связанная услуга для участка в Ярославле и области: состав работ, "
                "порядок выполнения и факторы сметы."
            ),
        }
        related_page["proof"]["evidence_ref"] = related_row["destination_id"]
        related_page["proof"]["main_image_attachment_id"] = 902
        related_page["boundary"] = {
            "summary": related_row["boundary"],
            "excluded_intents": ["другие коммерческие направления"],
        }
        related_page["links"]["related_services"] = [
            {
                "page_key": row["destination_id"],
                "url": row["target_url"],
                "label": row["title"],
            }
        ]
        related_evidence = evidence_entry(
            str(related_row["destination_id"]), attachment_id=902
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pages_dir = root / "pages"
            pages_dir.mkdir()
            (pages_dir / "S1-CHILD-SKETCH.json").write_text(
                json.dumps(page, ensure_ascii=False), encoding="utf-8"
            )
            (pages_dir / "S1-CHILD-RELATED.json").write_text(
                json.dumps(related_page, ensure_ascii=False), encoding="utf-8"
            )
            architecture_path = root / "architecture.csv"
            with architecture_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
                writer.writerow(related_row)
            evidence_path = root / "evidence.json"
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "services": [evidence, related_evidence],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            output_path = root / "items.json"
            source_manifest_path = root / "source-manifest.json"
            source_manifest_path.write_text('{"release_status":"draft"}\n', encoding="utf-8")
            deployment_manifest_path = root / "deployment-manifest.json"
            payload_path = root / "payload.json"
            stdout = StringIO()

            with redirect_stdout(stdout):
                validate_status = main(
                    [
                        "validate",
                        "--pages-dir",
                        str(pages_dir),
                        "--architecture",
                        str(architecture_path),
                        "--evidence",
                        str(evidence_path),
                    ]
                )
                render_status = main(
                    [
                        "render-items",
                        "--pages-dir",
                        str(pages_dir),
                        "--architecture",
                        str(architecture_path),
                        "--evidence",
                        str(evidence_path),
                        "--output",
                        str(output_path),
                    ]
                )
                bundle_status = main(
                    [
                        "render-bundle",
                        "--pages-dir",
                        str(pages_dir),
                        "--architecture",
                        str(architecture_path),
                        "--evidence",
                        str(evidence_path),
                        "--release-id",
                        "service-hubs-2026-08-28",
                        "--source-manifest",
                        str(source_manifest_path),
                        "--deployment-manifest-output",
                        str(deployment_manifest_path),
                        "--payload-output",
                        str(payload_path),
                    ]
                )

            self.assertEqual(0, validate_status)
            self.assertEqual(0, render_status)
            self.assertEqual(0, bundle_status)
            self.assertIn("validated 2 service pages", stdout.getvalue())
            rendered = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(2, len(rendered))
            self.assertEqual(
                {"S1-CHILD-SKETCH", "S1-CHILD-RELATED"},
                {item["page_key"] for item in rendered},
            )
            deployment_manifest = json.loads(
                deployment_manifest_path.read_text(encoding="utf-8")
            )
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(2, len(deployment_manifest["items"]))
            self.assertEqual(2, len(payload["items"]))
            self.assertEqual(
                hashlib.sha256(deployment_manifest_path.read_bytes()).hexdigest(),
                payload["manifest_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
