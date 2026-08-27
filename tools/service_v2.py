from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


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

EXACT_SERVICE_OWNERS = {
    "S1": (673, "landshaftnoe-proektirovanie"),
    "S2": (6868, "gazon-posevnojj-i-gazon-rulonnyjj"),
    "S3": (6871, "posadka-derevev-i-kustarnikov"),
    "S4": (9357, "ukhod-za-sadom"),
    "S5": (667, "planirovka-territorii"),
    "S6": (676, "podpornye-stenki"),
    "S7": (6918, "ulichnoe-osveshhenie-uchastka"),
    "S8": (9282, "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch"),
}


class ContractError(ValueError):
    """Raised when production service content violates the publish contract."""


def _require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{path} must be an object")
    return value


def _require_list(value: Any, path: str, minimum: int = 0) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{path} must be an array")
    if len(value) < minimum:
        raise ContractError(f"{path} must contain at least {minimum} items")
    return value


def _require_text(value: Any, path: str, minimum: int = 1) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{path} must be a string")
    value = value.strip()
    if len(value) < minimum:
        raise ContractError(f"{path} must contain at least {minimum} characters")
    folded = value.casefold()
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in folded:
            raise ContractError(f"{path} contains prohibited placeholder text: {pattern}")
    return value


def _require_https_url(value: Any, path: str, *, internal: bool = False) -> str:
    value = _require_text(value, path)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ContractError(f"{path} must be an absolute HTTPS URL")
    if internal and parsed.netloc not in {"exp76.ru", "www.exp76.ru"}:
        raise ContractError(f"{path} must stay on exp76.ru")
    return value


def _validate_image(value: Any, path: str) -> None:
    image = _require_dict(value, path)
    _require_https_url(image.get("url"), f"{path}.url", internal=True)
    _require_text(image.get("alt"), f"{path}.alt", 12)


def _validate_named_text_items(value: Any, path: str, minimum: int) -> None:
    items = _require_list(value, path, minimum)
    for index, item_value in enumerate(items):
        item = _require_dict(item_value, f"{path}[{index}]")
        _require_text(item.get("title"), f"{path}[{index}].title", 3)
        _require_text(item.get("text"), f"{path}[{index}].text", 45)


def validate_service(service: dict[str, Any]) -> None:
    service_id = _require_text(service.get("service_id"), "service_id")
    if service_id not in EXACT_SERVICE_OWNERS:
        raise ContractError(f"unknown service_id: {service_id}")

    expected_page_id, expected_slug = EXACT_SERVICE_OWNERS[service_id]
    if service.get("schema_version") != 1:
        raise ContractError(f"{service_id}.schema_version must be 1")
    if service.get("page_id") != expected_page_id:
        raise ContractError(f"{service_id}.page_id must remain {expected_page_id}")
    if service.get("parent_id") != 921:
        raise ContractError(f"{service_id}.parent_id must remain 921")
    if service.get("wp_template") != "servicepost.php":
        raise ContractError(f"{service_id}.wp_template must remain servicepost.php")
    if service.get("slug") != expected_slug:
        raise ContractError(f"{service_id}.slug must remain {expected_slug}")
    expected_canonical = f"https://exp76.ru/services/{expected_slug}/"
    if service.get("canonical") != expected_canonical:
        raise ContractError(f"{service_id}.canonical must remain {expected_canonical}")

    seo = _require_dict(service.get("seo"), f"{service_id}.seo")
    title = _require_text(seo.get("title"), f"{service_id}.seo.title", 45)
    description = _require_text(seo.get("description"), f"{service_id}.seo.description", 110)
    if len(title) > 85:
        raise ContractError(f"{service_id}.seo.title exceeds 85 characters")
    if len(description) > 180:
        raise ContractError(f"{service_id}.seo.description exceeds 180 characters")
    for field in ("primary_queries", "secondary_queries"):
        queries = _require_list(seo.get(field), f"{service_id}.seo.{field}", 1 if field == "primary_queries" else 3)
        for index, query in enumerate(queries):
            _require_text(query, f"{service_id}.seo.{field}[{index}]", 3)

    hero = _require_dict(service.get("hero"), f"{service_id}.hero")
    _require_text(hero.get("eyebrow"), f"{service_id}.hero.eyebrow", 5)
    _require_text(hero.get("title"), f"{service_id}.hero.title", 20)
    _require_text(hero.get("lead"), f"{service_id}.hero.lead", 90)
    _validate_image(hero.get("image"), f"{service_id}.hero.image")
    for cta_name in ("primary_cta", "secondary_cta"):
        cta = _require_dict(hero.get(cta_name), f"{service_id}.hero.{cta_name}")
        _require_text(cta.get("label"), f"{service_id}.hero.{cta_name}.label", 4)
        href = _require_text(cta.get("href"), f"{service_id}.hero.{cta_name}.href", 2)
        if not href.startswith("#service-v2-"):
            raise ContractError(f"{service_id}.hero.{cta_name}.href must target a service-v2 section")

    intro = _require_dict(service.get("intro"), f"{service_id}.intro")
    _require_text(intro.get("heading"), f"{service_id}.intro.heading", 15)
    for index, paragraph in enumerate(_require_list(intro.get("body"), f"{service_id}.intro.body", 2)):
        _require_text(paragraph, f"{service_id}.intro.body[{index}]", 100)
    _validate_named_text_items(intro.get("highlights"), f"{service_id}.intro.highlights", 4)

    services = _require_dict(service.get("services"), f"{service_id}.services")
    _require_text(services.get("heading"), f"{service_id}.services.heading", 12)
    _require_text(services.get("lead"), f"{service_id}.services.lead", 70)
    service_items = _require_list(services.get("items"), f"{service_id}.services.items", 4)
    for index, item_value in enumerate(service_items):
        item = _require_dict(item_value, f"{service_id}.services.items[{index}]")
        _require_text(item.get("title"), f"{service_id}.services.items[{index}].title", 5)
        _require_text(item.get("text"), f"{service_id}.services.items[{index}].text", 100)
        _validate_image(item.get("image"), f"{service_id}.services.items[{index}].image")

    process = _require_dict(service.get("process"), f"{service_id}.process")
    _require_text(process.get("heading"), f"{service_id}.process.heading", 12)
    _require_text(process.get("lead"), f"{service_id}.process.lead", 70)
    _validate_named_text_items(process.get("steps"), f"{service_id}.process.steps", 4)

    pricing = _require_dict(service.get("pricing"), f"{service_id}.pricing")
    _require_text(pricing.get("heading"), f"{service_id}.pricing.heading", 12)
    _require_text(pricing.get("lead"), f"{service_id}.pricing.lead", 70)
    for index, paragraph in enumerate(_require_list(pricing.get("body"), f"{service_id}.pricing.body", 2)):
        _require_text(paragraph, f"{service_id}.pricing.body[{index}]", 90)
    _validate_named_text_items(pricing.get("factors"), f"{service_id}.pricing.factors", 5)
    calculator = pricing.get("calculator")
    if calculator is not None:
        calculator = _require_dict(calculator, f"{service_id}.pricing.calculator")
        _require_text(calculator.get("label"), f"{service_id}.pricing.calculator.label", 5)
        _require_https_url(calculator.get("url"), f"{service_id}.pricing.calculator.url", internal=True)
        _require_text(calculator.get("note"), f"{service_id}.pricing.calculator.note", 70)

    proof = _require_dict(service.get("proof"), f"{service_id}.proof")
    _require_text(proof.get("heading"), f"{service_id}.proof.heading", 10)
    _require_text(proof.get("lead"), f"{service_id}.proof.lead", 60)
    cases = _require_list(proof.get("cases"), f"{service_id}.proof.cases")
    for index, case_value in enumerate(cases):
        case = _require_dict(case_value, f"{service_id}.proof.cases[{index}]")
        if not isinstance(case.get("page_id"), int) or case["page_id"] <= 0:
            raise ContractError(f"{service_id}.proof.cases[{index}].page_id must be a positive integer")
        _require_https_url(case.get("url"), f"{service_id}.proof.cases[{index}].url", internal=True)
        _require_text(case.get("title"), f"{service_id}.proof.cases[{index}].title", 8)
        _require_text(case.get("text"), f"{service_id}.proof.cases[{index}].text", 80)
        _validate_image(case.get("image"), f"{service_id}.proof.cases[{index}].image")
    gallery = _require_list(proof.get("gallery"), f"{service_id}.proof.gallery")
    for index, image_value in enumerate(gallery):
        image = _require_dict(image_value, f"{service_id}.proof.gallery[{index}]")
        _validate_image(image, f"{service_id}.proof.gallery[{index}]")
        _require_text(image.get("caption"), f"{service_id}.proof.gallery[{index}].caption", 20)

    geo = _require_dict(service.get("geo"), f"{service_id}.geo")
    _require_text(geo.get("heading"), f"{service_id}.geo.heading", 15)
    for index, paragraph in enumerate(_require_list(geo.get("body"), f"{service_id}.geo.body", 2)):
        _require_text(paragraph, f"{service_id}.geo.body[{index}]", 90)

    faq = _require_dict(service.get("faq"), f"{service_id}.faq")
    _require_text(faq.get("heading"), f"{service_id}.faq.heading", 12)
    faq_items = _require_list(faq.get("items"), f"{service_id}.faq.items", 5)
    for index, item_value in enumerate(faq_items):
        item = _require_dict(item_value, f"{service_id}.faq.items[{index}]")
        _require_text(item.get("question"), f"{service_id}.faq.items[{index}].question", 12)
        _require_text(item.get("answer"), f"{service_id}.faq.items[{index}].answer", 70)

    related = _require_dict(service.get("related_links"), f"{service_id}.related_links")
    _require_text(related.get("heading"), f"{service_id}.related_links.heading", 12)
    _require_text(related.get("lead"), f"{service_id}.related_links.lead", 60)
    related_items = _require_list(related.get("items"), f"{service_id}.related_links.items", 3)
    seen_urls: set[str] = set()
    for index, item_value in enumerate(related_items):
        item = _require_dict(item_value, f"{service_id}.related_links.items[{index}]")
        url = _require_https_url(item.get("url"), f"{service_id}.related_links.items[{index}].url", internal=True)
        if url in seen_urls:
            raise ContractError(f"{service_id}.related_links contains duplicate URL: {url}")
        seen_urls.add(url)
        _require_text(item.get("label"), f"{service_id}.related_links.items[{index}].label", 5)
        _require_text(item.get("text"), f"{service_id}.related_links.items[{index}].text", 45)

    cta = _require_dict(service.get("cta"), f"{service_id}.cta")
    _require_text(cta.get("heading"), f"{service_id}.cta.heading", 12)
    _require_text(cta.get("text"), f"{service_id}.cta.text", 80)
    _require_text(cta.get("button_label"), f"{service_id}.cta.button_label", 5)


def load_services(data_dir: Path) -> list[dict[str, Any]]:
    if not data_dir.is_dir():
        raise ContractError(f"data directory does not exist: {data_dir}")
    files = sorted(data_dir.glob("*.json"))
    if len(files) != len(EXACT_SERVICE_OWNERS):
        raise ContractError(f"expected 8 JSON payloads, found {len(files)}")

    services: list[dict[str, Any]] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError(f"cannot read {path.name}: {exc}") from exc
        service = _require_dict(payload, path.name)
        validate_service(service)
        if path.stem != service["slug"]:
            raise ContractError(f"{path.name} must match its slug")
        services.append(service)

    service_ids = [str(service["service_id"]) for service in services]
    if set(service_ids) != set(EXACT_SERVICE_OWNERS):
        raise ContractError("payloads must contain every S1-S8 owner exactly once")
    if len(service_ids) != len(set(service_ids)):
        raise ContractError("duplicate service_id in production payloads")

    titles = [str(service["seo"]["title"]) for service in services]
    descriptions = [str(service["seo"]["description"]) for service in services]
    h1_values = [str(service["hero"]["title"]) for service in services]
    for values, label in ((titles, "SEO title"), (descriptions, "SEO description"), (h1_values, "H1")):
        if len(values) != len(set(values)):
            raise ContractError(f"duplicate {label} across production payloads")
    return services


def count_words(value: Any) -> int:
    if isinstance(value, dict):
        return sum(count_words(item) for item in value.values())
    if isinstance(value, list):
        return sum(count_words(item) for item in value)
    if isinstance(value, str):
        return len(re.findall(r"[0-9A-Za-zА-Яа-яЁё]+(?:[-–][0-9A-Za-zА-Яа-яЁё]+)*", value))
    return 0


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _paragraphs(items: list[str]) -> str:
    return "\n".join(f"<p>{_e(item)}</p>" for item in items)


def _image(image: dict[str, str], css_class: str, *, eager: bool = False) -> str:
    loading = ' fetchpriority="high"' if eager else ' loading="lazy"'
    return (
        f'<img class="{_e(css_class)}" src="{_e(image["url"])}" '
        f'alt="{_e(image["alt"])}"{loading} decoding="async">'
    )


def render_service(service: dict[str, Any]) -> str:
    service_id = _e(service["service_id"])
    hero = service["hero"]
    intro = service["intro"]
    services = service["services"]
    process = service["process"]
    pricing = service["pricing"]
    proof = service["proof"]
    geo = service["geo"]
    faq = service["faq"]
    related = service["related_links"]
    cta = service["cta"]

    output: list[str] = [f'<div class="service-v2" data-service-id="{service_id}">']
    output.extend(
        [
            '<section class="service-v2__hero">',
            '<div class="service-v2__hero-media" id="scene">',
            _image(hero["image"], "service-v2__hero-image", eager=True),
            '<div class="service-v2__hero-overlay"></div></div>',
            '<div class="service-v2__hero-content wrapper">',
            f'<p class="service-v2__eyebrow">{_e(hero["eyebrow"])}</p>',
            f'<h1>{_e(hero["title"])}</h1>',
            f'<p class="service-v2__hero-lead">{_e(hero["lead"])}</p>',
            '<div class="service-v2__hero-actions">',
            f'<a class="service-v2__button" href="{_e(hero["primary_cta"]["href"])}">{_e(hero["primary_cta"]["label"])}</a>',
            f'<a class="service-v2__button service-v2__button--light" href="{_e(hero["secondary_cta"]["href"])}">{_e(hero["secondary_cta"]["label"])}</a>',
            '</div>',
            '<nav class="service-v2__breadcrumbs" aria-label="Хлебные крошки">',
            '<a href="https://exp76.ru/">Главная</a><span aria-hidden="true">/</span>',
            '<a href="https://exp76.ru/services/">Услуги</a><span aria-hidden="true">/</span>',
            f'<span aria-current="page">{_e(hero["title"])}</span></nav>',
            '</div></section>',
        ]
    )

    output.extend(
        [
            '<section class="service-v2__section service-v2__intro wrapper">',
            f'<div class="service-v2__section-copy"><h2>{_e(intro["heading"])}</h2>{_paragraphs(intro["body"])}</div>',
            '<div class="service-v2__highlights">',
        ]
    )
    for item in intro["highlights"]:
        output.append(f'<article><h3>{_e(item["title"])}</h3><p>{_e(item["text"])}</p></article>')
    output.append('</div></section>')

    output.extend(
        [
            '<section class="service-v2__section service-v2__section--soft">',
            '<div class="wrapper">',
            f'<div class="service-v2__section-heading"><h2>{_e(services["heading"])}</h2><p>{_e(services["lead"])}</p></div>',
            '<div class="service-v2__cards">',
        ]
    )
    for item in services["items"]:
        output.extend(
            [
                '<article class="service-v2__card">',
                _image(item["image"], "service-v2__card-image"),
                '<div class="service-v2__card-body">',
                f'<h3>{_e(item["title"])}</h3><p>{_e(item["text"])}</p>',
                '</div></article>',
            ]
        )
    output.append('</div></div></section>')

    output.extend(
        [
            '<section class="service-v2__section wrapper">',
            f'<div class="service-v2__section-heading"><h2>{_e(process["heading"])}</h2><p>{_e(process["lead"])}</p></div>',
            '<ol class="service-v2__steps">',
        ]
    )
    for index, step in enumerate(process["steps"], start=1):
        output.append(
            f'<li><span>{index}</span><div><h3>{_e(step["title"])}</h3><p>{_e(step["text"])}</p></div></li>'
        )
    output.append('</ol></section>')

    output.extend(
        [
            '<section class="service-v2__section service-v2__section--dark" id="service-v2-pricing">',
            '<div class="wrapper service-v2__pricing">',
            '<div class="service-v2__pricing-copy">',
            f'<h2>{_e(pricing["heading"])}</h2><p class="service-v2__pricing-lead">{_e(pricing["lead"])}</p>',
            _paragraphs(pricing["body"]),
            '</div><div class="service-v2__factors">',
        ]
    )
    for factor in pricing["factors"]:
        output.append(f'<article><h3>{_e(factor["title"])}</h3><p>{_e(factor["text"])}</p></article>')
    output.append('</div>')
    if pricing["calculator"] is not None:
        calculator = pricing["calculator"]
        output.extend(
            [
                '<aside class="service-v2__calculator">',
                f'<p>{_e(calculator["note"])}</p>',
                f'<a class="service-v2__button" href="{_e(calculator["url"])}">{_e(calculator["label"])}</a>',
                '</aside>',
            ]
        )
    output.append('</div></section>')

    if proof["cases"] or proof["gallery"]:
        output.extend(
            [
                '<section class="service-v2__section wrapper" id="service-v2-cases">',
                f'<div class="service-v2__section-heading"><h2>{_e(proof["heading"])}</h2><p>{_e(proof["lead"])}</p></div>',
                '<div class="service-v2__proof-grid">',
            ]
        )
        for case in proof["cases"]:
            output.extend(
                [
                    '<article class="service-v2__case">',
                    f'<a href="{_e(case["url"])}">{_image(case["image"], "service-v2__case-image")}</a>',
                    '<div class="service-v2__case-body">',
                    f'<h3><a href="{_e(case["url"])}">{_e(case["title"])}</a></h3>',
                    f'<p>{_e(case["text"])}</p>',
                    f'<a class="service-v2__text-link" href="{_e(case["url"])}">Посмотреть объект</a>',
                    '</div></article>',
                ]
            )
        for image in proof["gallery"]:
            output.extend(
                [
                    '<figure class="service-v2__case">',
                    _image(image, "service-v2__case-image"),
                    f'<figcaption>{_e(image["caption"])}</figcaption>',
                    '</figure>',
                ]
            )
        output.append('</div></section>')

    output.extend(
        [
            '<section class="service-v2__section service-v2__geo">',
            '<div class="wrapper service-v2__geo-inner">',
            f'<h2>{_e(geo["heading"])}</h2>{_paragraphs(geo["body"])}',
            '</div></section>',
            '<section class="service-v2__section wrapper">',
            f'<div class="service-v2__section-heading"><h2>{_e(related["heading"])}</h2><p>{_e(related["lead"])}</p></div>',
            '<div class="service-v2__related">',
        ]
    )
    for item in related["items"]:
        output.append(
            f'<a href="{_e(item["url"])}"><strong>{_e(item["label"])}</strong><span>{_e(item["text"])}</span></a>'
        )
    output.append('</div></section>')

    output.extend(
        [
            '<section class="service-v2__section service-v2__section--soft">',
            '<div class="wrapper service-v2__faq">',
            f'<h2>{_e(faq["heading"])}</h2>',
        ]
    )
    for item in faq["items"]:
        output.append(
            '<details class="service-v2__faq-item">'
            f'<summary>{_e(item["question"])}</summary><p>{_e(item["answer"])}</p>'
            '</details>'
        )
    output.append('</div></section>')

    output.extend(
        [
            '<section class="service-v2__section service-v2__cta" id="service-v2-form">',
            '<div class="wrapper service-v2__cta-inner">',
            f'<div><h2>{_e(cta["heading"])}</h2><p>{_e(cta["text"])}</p></div>',
            '<div class="formWrapper service-v2__form-wrapper">',
            '<form class="form service-v2__form" method="post" action="/server.php">',
            '<label class="form__label"><span>Ваше имя</span><input class="form__input" type="text" name="name" autocomplete="name" required></label>',
            '<label class="form__label"><span>Телефон</span><input class="form__input" type="tel" name="phone" autocomplete="tel" inputmode="tel" required></label>',
            '<input type="hidden" name="form_version" value="service-v2">',
            f'<input type="hidden" name="source" value="{_e(service["canonical"])}">',
            '<label class="service-v2__consent"><input type="checkbox" name="consent" value="1" required><span>Соглашаюсь с <a href="/privacy/">политикой конфиденциальности</a> и <a href="/consent/">обработкой персональных данных</a>.</span></label>',
            f'<button class="service-v2__button form__btn" type="submit">{_e(cta["button_label"])}</button>',
            '</form>',
            '<div class="ajaxMessage"><div class="ajaxMessage__success"><div class="ajaxMessage__title"><p>Спасибо!</p><p>Заявка отправлена</p></div><div class="ajaxMessage__text">Свяжемся с вами, чтобы уточнить задачу и договориться о следующем шаге.</div></div><div class="ajaxMessage__error"><div class="ajaxMessage__title">Не удалось отправить заявку</div><div class="ajaxMessage__text">Позвоните нам по номеру 8 (915) 978-88-09.</div></div><button class="ajaxMessage__btn btn closeModal" type="button">Закрыть</button></div>',
            '</div></div></section>',
        ]
    )

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq["items"]
        ],
    }
    schema_json = json.dumps(faq_schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output.append(f'<script type="application/ld+json" class="service-v2__schema">{schema_json}</script>')
    output.append('</div>')
    return "\n".join(output) + "\n"


def build_services(data_dir: Path, output_dir: Path) -> dict[str, int]:
    services = load_services(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*.html"):
        stale.unlink()
    for service in services:
        output_path = output_dir / f'{service["slug"]}.html'
        output_path.write_text(render_service(service), encoding="utf-8", newline="\n")
    return {"services": len(services), "errors": 0, "words": sum(count_words(service) for service in services)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and render exp76 service-v2 content")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate all service JSON payloads")
    validate.add_argument("data_dir", type=Path)

    build = subparsers.add_parser("build", help="validate and build static WordPress fragments")
    build.add_argument("data_dir", type=Path)
    build.add_argument("output_dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            services = load_services(args.data_dir)
            summary = {
                "services": len(services),
                "errors": 0,
                "words": sum(count_words(service) for service in services),
            }
        else:
            summary = build_services(args.data_dir, args.output_dir)
    except ContractError as exc:
        print(json.dumps({"services": 0, "errors": 1, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
