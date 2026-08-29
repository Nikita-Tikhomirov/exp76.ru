"""Supporting informational architecture for the audited S9-S15 hubs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence


_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _REPOSITORY_ROOT / "seo-data" / "2026-08-exp76-services"
DEFAULT_CSV_PATH = _DATA_ROOT / "processed" / "legacy_article_architecture.csv"
DEFAULT_REVIEW_PATH = _DATA_ROOT / "reviews" / "legacy_article_structure.md"

ARTICLE_COLUMNS = (
    "destination_id",
    "service_id",
    "page_role",
    "parent_destination_id",
    "title",
    "primary_query",
    "regional_monthly_frequency",
    "current_url",
    "proposed_url",
    "canonical_url",
    "primary_cluster_id",
    "source_cluster_ids",
    "url_action",
    "publication_status",
    "evidence_refs",
    "review_status",
    "reviewer",
    "rationale",
    "serp_top_titles",
)


@dataclass(frozen=True)
class LegacyArticle:
    destination_id: str
    service_id: str
    title: str
    query: str
    slug: str
    regional_monthly_frequency: int
    top_titles: tuple[str, ...]
    boundary: str


LEGACY_ARTICLES = (
    LegacyArticle(
        "S9-ARTICLE-STUMP-DIY",
        "S9",
        "Как избавиться от пня на участке: способы и ограничения",
        "корчевание пней своими руками",
        "kak-izbavitsja-ot-pnja-na-uchastke",
        14,
        (
            "Как избавиться от пня на участке: лучшие способы...",
            "Как избавиться от пня на участке: 5 способов",
            "ЧАСТЬ 3. Корчевание — DRIVE2",
        ),
        "сравнить самостоятельные способы и риски; заказ корчевания и расчёт оставить дочерней услуге",
    ),
    LegacyArticle(
        "S9-ARTICLE-OVERGROWN-SITE",
        "S9",
        "С чего начать расчистку заросшего участка",
        "как расчистить заросший участок от кустарника и деревьев",
        "kak-raschistit-zarosshij-uchastok",
        0,
        (
            "Как разработать заросший участок - с чего начать работы...",
            "Как я расчистил свой участок от деревьев для... | DRIVE2",
            "Как правильно расчистить запущенный участок",
        ),
        "дать порядок обследования и подготовки; коммерческую расчистку оставить дочерней услуге",
    ),
    LegacyArticle(
        "S10-ARTICLE-POND-DIY",
        "S10",
        "Как сделать декоративный пруд на участке",
        "как сделать декоративный пруд на участке",
        "kak-sdelat-dekorativnyj-prud-na-uchastke",
        0,
        (
            "Пруд своими руками на даче: как сделать правильно",
            "Планирование",
            "Выбор материала",
        ),
        "раскрыть этапы и типовые ошибки без обещания универсальной конструкции; проектирование и создание оставить услуге",
    ),
    LegacyArticle(
        "S10-ARTICLE-POND-CARE",
        "S10",
        "Уход за декоративным прудом по сезонам",
        "уход за декоративным прудом на участке",
        "uhod-za-dekorativnym-prudom",
        0,
        (
            "Как создать декоративный пруд и ухаживать за ним...",
            "Летний уход за декоративным прудом на даче",
            "Искусственный пруд на участке: как обустроить...",
        ),
        "описать эксплуатационный уход; не выдавать очистку запущенных водоёмов за подтверждённую услугу компании",
    ),
    LegacyArticle(
        "S11-ARTICLE-PRESSURE",
        "S11",
        "Туманообразование высокого и низкого давления: в чём разница",
        "система туманообразования высокого и низкого давления отличия",
        "sistemy-tumanoobrazovanija-vysokogo-i-nizkogo-davlenija",
        0,
        (
            "Разница между системами туманообразования...",
            "В чем разница туманообразующих систем низкого...",
            "Системы туманообразования высокого и низкого...",
        ),
        "сравнить принципы и сценарии без неподтверждённых характеристик оборудования; подбор и монтаж оставить хабу",
    ),
    LegacyArticle(
        "S12-ARTICLE-PILE-PROS-CONS",
        "S12",
        "Фундамент на бетонных сваях: плюсы, минусы и ограничения",
        "фундамент на бетонных сваях плюсы и минусы",
        "fundament-na-betonnyh-svajah-pljusy-i-minusy",
        0,
        (
            "Плюсы и минусы фундамента из бетонных свай | Дзен",
            "Дом на бетонных сваях: особенности, плюсы и минусы",
            "В чем минус фундамента из забивных ж/б свай",
        ),
        "дать критерии обсуждения без расчёта несущей способности и неподтверждённых технических обещаний; монтаж оставить услуге",
    ),
    LegacyArticle(
        "S13-ARTICLE-CARPORT-DIY",
        "S13",
        "Навес для автомобиля своими руками: что учесть до строительства",
        "навес для автомобиля своими руками из металла чертежи",
        "naves-dlja-avtomobilja-svoimi-rukami",
        5,
        (
            "Как сделать навес для машины из профильной трубы...",
            "Навес для машины своими руками: как сделать, виды...",
            "Навес для машины из профильной трубы: Инструкция по...",
        ),
        "объяснить исходные данные и риски самостроя без публикации универсального расчёта; изготовление оставить услуге",
    ),
    LegacyArticle(
        "S13-ARTICLE-POLYCARBONATE-DIY",
        "S13",
        "Навес из поликарбоната, примыкающий к дому: планирование",
        "навес к дому из поликарбоната своими руками",
        "naves-iz-polikarbonata-k-domu-svoimi-rukami",
        0,
        (
            "Делаем навес из поликарбоната, пристроенный к дому",
            "Навес к дому из поликарбоната своими руками",
            "Как сделать навес к дому своими руками: бюджетные...",
        ),
        "раскрыть примыкание, водоотвод и исходные размеры без расчётных обещаний; проектирование и монтаж оставить услуге",
    ),
    LegacyArticle(
        "S14-ARTICLE-BRICK-GRILL-DIY",
        "S14",
        "Кирпичный мангал своими руками: подготовка, схема и ошибки",
        "кирпичный мангал своими руками чертежи и фото пошаговая инструкция",
        "kirpichnyj-mangal-svoimi-rukami",
        1,
        (
            "Печь барбекю из кирпича: 7 проектов с чертежами... | Дзен",
            "Мангал из кирпича: 44 чертежа, 18 проектов + фото",
            "Мангал из кирпича своими руками - пошаговая...",
        ),
        "дать учебную последовательность и требования безопасности; профессиональную кладку оставить дочерней услуге",
    ),
    LegacyArticle(
        "S14-ARTICLE-HEATING-STOVE-DIY",
        "S14",
        "Кладка отопительной печи: что проверить до начала работ",
        "кладка отопительной печи своими руками",
        "kladka-otopitelnoj-pechi-svoimi-rukami",
        0,
        (
            "Как сложить печь из кирпича своими руками: пошаговая...",
            "Кладка простой печи из кирпича своими руками",
            "Как сложить печь своими руками: порядовка...",
        ),
        "объяснить подготовку и риски без универсальной порядовки для любого дома; кладку оставить дочерней услуге",
    ),
    LegacyArticle(
        "S15-ARTICLE-DEMOLITION-PERMIT",
        "S15",
        "Нужно ли разрешение на снос частного дома",
        "нужно ли разрешение на снос частного дома",
        "nuzhno-li-razreshenie-na-snos-chastnogo-doma",
        1,
        (
            "Как снести старый дом на своем участке? – Инструкции...",
            "Как правильно снести загородный дом | РБК Недвижимость",
            "Как снести дом и снять его с кадастрового учёта",
        ),
        "перед публикацией проверить актуальные официальные нормы и описать порядок документов; сами работы оставить услуге",
    ),
)

LEGACY_ARTICLE_COUNTS: Mapping[str, int] = MappingProxyType(
    dict(Counter(article.service_id for article in LEGACY_ARTICLES))
)


def _article_row(article: LegacyArticle) -> dict[str, str]:
    canonical = f"https://exp76.ru/{article.slug}/"
    evidence = (
        "yandex_serp:manual:2026-08-29:lr=16; "
        f"wordstat:region=10841:2026-07-28..2026-08-28:frequency={article.regional_monthly_frequency}; "
        "yandex_suggest:legacy-suggest-v2"
    )
    return {
        "destination_id": article.destination_id,
        "service_id": article.service_id,
        "page_role": "article",
        "parent_destination_id": f"{article.service_id}-HUB",
        "title": article.title,
        "primary_query": article.query,
        "regional_monthly_frequency": str(article.regional_monthly_frequency),
        "current_url": "",
        "proposed_url": canonical,
        "canonical_url": canonical,
        "primary_cluster_id": article.destination_id,
        "source_cluster_ids": article.destination_id,
        "url_action": "article",
        "publication_status": "ready",
        "evidence_refs": evidence,
        "review_status": "reviewed",
        "reviewer": "codex-2026-08-29",
        "rationale": (
            "Яндекс показывает отдельную информационную выдачу. "
            f"Информационная граница: {article.boundary}."
        ),
        "serp_top_titles": " | ".join(article.top_titles),
    }


def build_legacy_article_rows() -> list[dict[str, str]]:
    """Return the 11 reviewed informational destinations in hub order."""

    rows = [_article_row(article) for article in LEGACY_ARTICLES]
    if len(rows) != 11:
        raise ValueError("legacy article count differs")
    if len({row["destination_id"] for row in rows}) != len(rows):
        raise ValueError("legacy article ids must be unique")
    if len({row["canonical_url"] for row in rows}) != len(rows):
        raise ValueError("legacy article URLs must be unique")
    if set(LEGACY_ARTICLE_COUNTS) != {f"S{number}" for number in range(9, 16)}:
        raise ValueError("every legacy hub needs an informational destination")
    return rows


def render_legacy_article_review() -> str:
    """Render the reviewed queries and publication boundaries."""

    lines = [
        "# Статьи для поддержки хабов S9–S15",
        "",
        "Проверка выполнена 29 августа 2026 года в Яндексе (регион Ярославль, lr=16) и Вордстате (Ярославская область, 10841). Частотность — широкая региональная частота конкретной фразы за 28.07–28.08.2026, а не прогноз трафика.",
        "",
        "Все URL на момент проверки отвечали 404 и не конфликтовали с опубликованными владельцами. Статус `ready` означает: кластер, URL и полный текст подготовлены; публикация всё равно проходит только через отдельные preview, stage и publish-проверки импортера.",
        "",
    ]
    for row in build_legacy_article_rows():
        lines.extend(
            [
                f"## {row['destination_id']} — {row['title']}",
                "",
                f"- Хаб: `{row['service_id']}`",
                f"- Запрос: «{row['primary_query']}»",
                f"- Вордстат 10841: **{row['regional_monthly_frequency']}**",
                f"- URL: {row['canonical_url']}",
                f"- Верх выдачи: {row['serp_top_titles']}",
                f"- Решение: {row['rationale']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Правило выпуска",
            "",
            "Статьи не заменяют коммерческие страницы и не дублируют их Title/H1. Каждая ведёт на один основной хаб и одну релевантную подуслугу. Для материала о разрешении на снос обязательна повторная проверка официальных правовых источников непосредственно перед публикацией.",
            "",
        ]
    )
    return "\n".join(lines)


def write_legacy_article_artifacts(
    csv_path: Path = DEFAULT_CSV_PATH,
    review_path: Path = DEFAULT_REVIEW_PATH,
) -> int:
    """Write deterministic UTF-8 CSV and human review."""

    rows = build_legacy_article_rows()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ARTICLE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(render_legacy_article_review(), encoding="utf-8", newline="\n")
    return len(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export reviewed S9-S15 article architecture.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW_PATH)
    args = parser.parse_args(argv)
    count = write_legacy_article_artifacts(args.csv, args.review)
    print(f"Exported {count} legacy article destinations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
