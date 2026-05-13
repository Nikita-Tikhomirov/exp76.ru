#!/usr/bin/env python3
"""
Распределяет страницы кейсов из portfolio-links-po-tipam-rabot.md
по новым категориям (дренаж, отмостка, ливнёвка, плитка, осушение, автополив)
на основе смысла описания и структуры md-файла.

Выходные данные:
  1. cases_by_category.json      — { "category_slug": [ { "title": "...", "url": "..." }, ... ] }
  2. cases_by_category_report.md — человекочитаемый отчёт
  3. acf_selected_works_map.json — маппинг для поля ACF selected_works_posts (нужны ID страниц)

Запуск:
  python tools/distribute_cases_to_categories.py
"""

import re
import json
import os
import sys
from pathlib import Path

# Фикс кодировки для Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Конфигурация категорий ──────────────────────────────────────────────
# slug:      системное имя (совпадает с названием папки в seo-content и термином WP)
# label:     русское название
# cat_id:    ID категории в WordPress (term_id)
# template:  файл шаблона
# keywords:  ключевые слова для определения категории по описанию кейса
CATEGORIES = {
    "drenazh": {
        "label": "Дренаж участка",
        "cat_id": 87,
        "template": "category-87.php",
        "region_template": "page-drenazh-region.php",
        "keywords": [
            "дренаж", "дренажн", "пристенный", "кольцевой", "глубинный",
            "поверхностный дренаж", "дренаж фундамента", "дренаж участка",
            "отвод воды", "осушени", "грунтовые воды", "вода на участке",
        ],
    },
    "otmostka": {
        "label": "Отмостка вокруг дома",
        "cat_id": 88,
        "template": "category-88.php",
        "region_template": "page-otmostka-region.php",
        "keywords": [
            "отмостк", "бетонная отмостка", "мягкая отмостка",
            "утеплённая отмостка", "утепленная отмостка",
            "отмостка из плитки", "ремонт отмостки", "заливка отмостки",
        ],
    },
    "plitka": {
        "label": "Укладка тротуарной плитки",
        "cat_id": 89,
        "template": "category-89.php",
        "region_template": "page-plitka-region.php",
        "keywords": [
            "тротуарная плитка", "укладка плитки", "мощение", "брусчатка",
            "плитк", "тротуар", "дорожки из плитки", "площадка под авто",
            "двор из плитки", "плитняк",
        ],
    },
    "osushenie": {
        "label": "Осушение участка",
        "cat_id": 90,
        "template": "category-90.php",
        "region_template": "page-osushenie-region.php",
        "keywords": [
            "осушение", "заболачивание", "мокрый грунт", "лужи",
            "отвод воды с участка", "вода после дождя",
            "осушени", "водоотвод",
        ],
    },
    "livnevka": {
        "label": "Ливневая канализация",
        "cat_id": 91,
        "template": "category-91.php",
        "region_template": "page-livnevka-region.php",
        "keywords": [
            "ливнев", "ливнёв", "ливневая канализация", "ливневка",
            "дождеприёмник", "дождеприемник", "лотки", "ливневые лотки",
            "линейный водоотвод", "отвод воды с крыши", "водосток",
        ],
    },
    "autopoliv": {
        "label": "Автополив на участке",
        "cat_id": 92,
        "template": "category-92.php",
        "region_template": "page-autopoliv-region.php",
        "keywords": [
            "автополив", "автоматический полив", "полив газона",
            "капельный полив", "спринклер", "дождеватель",
            "система полива", "контроллер полива",
        ],
    },
    "blagoustroystvo": {
        "label": "Благоустройство / Прочее",
        "cat_id": None,  # нет отдельной категории
        "template": None,
        "region_template": None,
        "keywords": [
            "благоустройство", "газон", "рулонный газон", "посадка",
            "хвойные", "пруд", "водоём", "водоем", "планировка",
            "комплексное благоустройство",
        ],
    },
}


def parse_md_file(filepath: str) -> dict:
    """
    Парсит portfolio-links-po-tipam-rabot.md.
    Возвращает: { "section_name": [ { "title": str, "url": str, "description": str }, ... ] }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем секции по заголовкам ##
    sections = {}
    current_section = None
    current_entries = []

    lines = content.split("\n")
    for line in lines:
        # Заголовок секции (## ...)
        if line.startswith("## ") and not line.startswith("### "):
            if current_section and current_entries:
                sections[current_section] = current_entries
            current_section = line[3:].strip()
            current_entries = []
            continue

        # Пропускаем ## ИТОГО и примечания
        if current_section and current_section.startswith("ИТОГО"):
            continue

        # Нумерованный элемент: "1. название — описание"
        match = re.match(r"^\d+\.\s+(.+?)\s*—\s*(.+)$", line)
        if match and current_section:
            title = match.group(1).strip()
            description = match.group(2).strip()
            current_entries.append({"title": title, "description": description, "url": ""})
            continue

        # URL: "   https://..."
        url_match = re.match(r"^\s+(https?://\S+)", line)
        if url_match and current_entries:
            current_entries[-1]["url"] = url_match.group(1).strip()

    # Последняя секция
    if current_section and current_entries:
        sections[current_section] = current_entries

    return sections


def classify_case(description: str, existing_category: str) -> list:
    """
    Определяет категорию(и) кейса по описанию.
    Возвращает список slug'ов категорий (может быть несколько, т.к. кейс может
    относиться к дренажу И ливнёвке одновременно).
    """
    desc_lower = description.lower()
    matched = []

    for slug, cat in CATEGORIES.items():
        if slug == "blagoustroystvo":
            continue  # обрабатывается отдельно
        for kw in cat["keywords"]:
            if kw.lower() in desc_lower:
                if slug not in matched:
                    matched.append(slug)
                break  # достаточно одного ключевого слова

    # Если ничего не найдено — прочее
    if not matched:
        # Попробуем "прочее" keywords
        for kw in CATEGORIES["blagoustroystvo"]["keywords"]:
            if kw.lower() in desc_lower:
                matched.append("blagoustroystvo")
                break
        if not matched:
            matched.append("blagoustroystvo")

    return matched


def normalize_section_to_slug(section_name: str) -> str:
    """Маппит название секции из md на slug категории."""
    mapping = {
        "ДРЕНАЖ": "drenazh",
        "ЛИВНЕВАЯ КАНАЛИЗАЦИЯ": "livnevka",
        "ЛИВНЕВАЯ КАНАЛИЗАЦИЯ (ЛИВНЕВКА)": "livnevka",
        "ОТМОСТКА": "otmostka",
        "ТРОТУАРНАЯ ПЛИТКА": "plitka",
        "ТРОТУАРНАЯ ПЛИТКА (ТП)": "plitka",
        "ПРОЧИЕ РАБОТЫ": "blagoustroystvo",
        "ПРОЧЕЕ": "blagoustroystvo",
    }
    # Нечёткое совпадение
    for key, val in mapping.items():
        if key in section_name.upper():
            return val
    return "blagoustroystvo"


def main():
    workspace = Path(__file__).resolve().parent.parent
    md_path = workspace / "portfolio-links-po-tipam-rabot.md"
    output_dir = workspace

    print(f"[READ] Parsing {md_path}...")
    sections = parse_md_file(str(md_path))

    # ── Распределение по категориям ──────────────────────────────────
    cases_by_category = {slug: [] for slug in CATEGORIES}

    stats = {"total_cases": 0, "matched_by_section": 0, "matched_by_keywords": 0, "multi_category": 0}

    for section_name, entries in sections.items():
        section_slug = normalize_section_to_slug(section_name)
        stats["total_cases"] += len(entries)

        for entry in entries:
            # Классификация по ключевым словам в описании
            keyword_cats = classify_case(entry["description"], section_slug)

            # Если keywords выдали категорию, совпадающую с секцией — отлично
            # Если нет — добавляем и из секции, и из keywords
            all_cats = set(keyword_cats)

            # Секция md — сильный сигнал, добавляем если не противоречит
            if section_slug != "blagoustroystvo":
                all_cats.add(section_slug)

            # Убираем "blagoustroystvo" если есть что-то конкретное
            if len(all_cats) > 1 and "blagoustroystvo" in all_cats:
                all_cats.discard("blagoustroystvo")

            if len(all_cats) > 1:
                stats["multi_category"] += 1

            if section_slug in all_cats:
                stats["matched_by_section"] += 1
            else:
                stats["matched_by_keywords"] += 1

            for cat_slug in all_cats:
                cases_by_category[cat_slug].append({
                    "title": entry["title"],
                    "description": entry["description"],
                    "url": entry["url"],
                    "source_section": section_name,
                })

    # ── Дедупликация URL'ов внутри категорий ────────────────────────
    for slug in cases_by_category:
        seen_urls = set()
        unique = []
        for case in cases_by_category[slug]:
            if case["url"] not in seen_urls:
                seen_urls.add(case["url"])
                unique.append(case)
        cases_by_category[slug] = unique

    # ── Запись cases_by_category.json ─────────────────────────────────
    json_path = output_dir / "cases_by_category.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cases_by_category, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON mapping: {json_path}")

    # ── Запись cases_by_category_report.md ────────────────────────────
    report_path = output_dir / "cases_by_category_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Распределение кейсов по категориям\n\n")
        f.write(f"> Автоматически сгенерировано скриптом `tools/distribute_cases_to_categories.py`\n\n")
        f.write(f"**Всего кейсов:** {stats['total_cases']}\n")
        f.write(f"**Мультикатегорийных:** {stats['multi_category']}\n\n")
        f.write("---\n\n")

        for slug, cat in CATEGORIES.items():
            cases = cases_by_category.get(slug, [])
            if not cases:
                continue
            f.write(f"## {cat['label'].upper()} ({len(cases)} проектов)\n\n")
            if cat["template"]:
                f.write(f"- **Шаблон:** `{cat['template']}`\n")
                f.write(f"- **Региональный:** `{cat['region_template']}`\n")
                f.write(f"- **ID категории:** `{cat['cat_id']}`\n\n")
            for i, case in enumerate(cases, 1):
                f.write(f"{i}. **{case['title']}** — {case['description']}\n")
                f.write(f"   {case['url']}\n")
                # Показываем переопределение только если секция md не совпадает с категорией
                section_slug = normalize_section_to_slug(case["source_section"])
                if section_slug != slug and section_slug != "blagoustroystvo":
                    f.write(f"   *(из секции «{case['source_section']}» — переопределено по смыслу)*\n")
                f.write("\n")
            f.write("\n")

    print(f"[OK] Report: {report_path}")

    # ── Запись acf_selected_works_map.json (для ручного импорта) ─────
    acf_map = {}
    for slug, cat in CATEGORIES.items():
        if cat["cat_id"] is None:
            continue
        cases = cases_by_category.get(slug, [])
        acf_map[slug] = {
            "cat_id": cat["cat_id"],
            "cat_label": cat["label"],
            "template": cat["template"],
            "acf_field": "selected_works_posts",
            "acf_context": f"category_{cat['cat_id']}",
            "cases": [{"title": c["title"], "url": c["url"]} for c in cases],
        }

    acf_path = output_dir / "acf_selected_works_map.json"
    with open(acf_path, "w", encoding="utf-8") as f:
        json.dump(acf_map, f, ensure_ascii=False, indent=2)
    print(f"[OK] ACF mapping: {acf_path}")

    # ── Статистика ────────────────────────────────────────────────────
    print(f"\n=== Statistics:")
    print(f"   Всего кейсов:            {stats['total_cases']}")
    print(f"   Совпало по секции md:     {stats['matched_by_section']}")
    print(f"   Переопределено keywords:  {stats['matched_by_keywords']}")
    print(f"   В нескольких категориях:  {stats['multi_category']}")
    for slug, cat in CATEGORIES.items():
        count = len(cases_by_category.get(slug, []))
        if count > 0:
            print(f"   {cat['label']:30s} {count:3d}")


if __name__ == "__main__":
    main()
