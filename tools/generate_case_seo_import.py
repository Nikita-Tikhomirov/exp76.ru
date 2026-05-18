from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "cases_by_category.json"
MAP_PATH = ROOT / "acf_selected_works_map.json"
OUT_PATH = ROOT / "seo-content" / "cases" / "import" / "cases-seo-import.json"
THEME_OUT_PATH = (
    ROOT
    / "ftp_dump_minimal"
    / "wp-content"
    / "themes"
    / "land76wp"
    / "import"
    / "cases-seo-import.json"
)


CATEGORIES = {
    "drenazh": {
        "cat_id": 87,
        "label": "Дренаж участка",
        "work_type": "Дренаж участка",
        "service_url": "/category/drenazh-uchastka/",
        "keywords": "дренаж участка, дренаж участка под ключ, дренаж грунтовых вод, дренаж вокруг дома",
        "problem": "На участке скапливалась вода, грунт долго оставался сырым, а рядом с домом требовался надежный отвод воды без случайных решений.",
        "technology": "Мы оцениваем рельеф, уровень воды, тип грунта и существующие дорожки, после чего подбираем схему: пристенный, кольцевой, глубинный или поверхностный дренаж. В работе учитываем уклоны, точки сброса, ревизионные колодцы и возможность обслуживания системы.",
        "result": "Готовая система отводит лишнюю воду от дома и функциональных зон участка. Это снижает риск подтопления, сырости у фундамента и разрушения дорожек после дождей и снеготаяния.",
        "faq": [
            ("Можно ли сделать такой дренаж на уже благоустроенном участке?", "Да, но схему подбираем аккуратно: учитываем дорожки, посадки, подъезд техники и места, где нельзя нарушать покрытие."),
            ("От чего зависит цена дренажа участка?", "На стоимость влияют длина трасс, глубина заложения, грунт, количество колодцев, точка сброса воды и необходимость совмещать дренаж с ливневкой."),
        ],
    },
    "otmostka": {
        "cat_id": 88,
        "label": "Отмостка вокруг дома",
        "work_type": "Отмостка вокруг дома",
        "service_url": "/category/otmostka-vokrug-doma/",
        "keywords": "отмостка вокруг дома, отмостка под ключ, бетонная отмостка, мягкая отмостка, отвод воды от фундамента",
        "problem": "Вода от кровли и осадков попадала к фундаменту, поэтому нужна была отмостка с правильным уклоном и подготовкой основания.",
        "technology": "Делаем разметку, выемку грунта, подушку, геотекстиль, щебень, уклон от дома и финишный слой под выбранный тип отмостки. При необходимости связываем отмостку с ливневкой или дренажом.",
        "result": "Отмостка защищает основание дома от воды, делает периметр аккуратным и готовит участок к дальнейшему благоустройству.",
        "faq": [
            ("Какая отмостка лучше: бетонная, мягкая или из плитки?", "Тип выбираем по дому, грунту, бюджету и будущему благоустройству. Иногда выгоднее мягкая отмостка, иногда нужна жесткая конструкция с плиткой или бетоном."),
            ("Можно ли совместить отмостку с водоотведением?", "Да. Если вода идет к фундаменту, сразу предусматриваем уклон, лотки, приемники или связку с дренажом."),
        ],
    },
    "plitka": {
        "cat_id": 89,
        "label": "Укладка тротуарной плитки",
        "work_type": "Укладка тротуарной плитки",
        "service_url": "/category/ukladka-trotuarnoy-plitki/",
        "keywords": "укладка тротуарной плитки, укладка плитки под ключ, мощение участка, тротуарная плитка цена",
        "problem": "Нужно было сделать удобные дорожки или площадки с правильной геометрией, основанием и водоотводом, чтобы покрытие не проседало.",
        "technology": "Готовим основание, задаем уклоны, уплотняем слои, выставляем бордюры и укладываем плитку по выбранному рисунку. На сложных участках заранее решаем вопрос водоотведения.",
        "result": "Покрытие получается ровным, удобным для ходьбы и обслуживания, а участок получает законченный вид без луж и хаотичных проходов.",
        "faq": [
            ("Почему плитка может просесть после укладки?", "Чаще всего причина в слабом основании, плохом уплотнении, отсутствии бордюров или неправильных уклонах."),
            ("Можно ли посчитать цену за м2 до выезда?", "Ориентир дать можно, но точная смета зависит от основания, объема работ, бордюров, рисунка и водоотведения."),
        ],
    },
    "osushenie": {
        "cat_id": 90,
        "label": "Осушение участка",
        "work_type": "Осушение участка",
        "service_url": "/category/osushenie-uchastka/",
        "keywords": "осушение участка, осушение участка под ключ, дренаж для осушения, вода на участке",
        "problem": "На участке держалась сырость, вода после дождя уходила медленно, а обычная планировка не решала проблему переувлажнения.",
        "technology": "Сначала определяем, откуда приходит вода: рельеф, глина, высокий уровень грунтовых вод, ливневые потоки. Затем выбираем дренаж, водоотвод, подсыпку, планировку или комбинированную систему.",
        "result": "Участок становится пригодным для дорожек, газона, посадок и дальнейшего благоустройства. Вода уходит организованно, без постоянных луж и сырого грунта.",
        "faq": [
            ("Осушение участка — это всегда дренаж?", "Не всегда. Иногда достаточно поверхностного водоотвода и планировки, но при высоких грунтовых водах нужен полноценный дренаж."),
            ("Когда лучше делать осушение?", "Лучше до мощения, газона и посадок, чтобы потом не вскрывать готовое благоустройство."),
        ],
    },
    "livnevka": {
        "cat_id": 91,
        "label": "Ливневая канализация",
        "work_type": "Ливневая канализация",
        "service_url": "/category/livnevaya-kanalizatsiya/",
        "keywords": "ливневая канализация, ливневка на участке, отвод дождевой воды, ливневые лотки",
        "problem": "Дождевая и талая вода попадала на дорожки, к дому или в низкие зоны участка, поэтому требовался организованный поверхностный водоотвод.",
        "technology": "Проектируем точки сбора воды, лотки, дождеприемники, трубы, колодцы и трассы отвода. Систему привязываем к уклонам участка, кровле, дорожкам и парковке.",
        "result": "Ливневка собирает воду с кровли и покрытий, защищает дорожки и основание дома, помогает сохранить благоустройство после сильных дождей.",
        "faq": [
            ("Чем ливневка отличается от дренажа?", "Ливневка собирает воду с поверхности и кровли, а дренаж работает с водой в грунте. На сложных участках системы совмещают."),
            ("Можно ли добавить ливневку к уже готовым дорожкам?", "Можно, но трассы и лотки подбираем так, чтобы минимально вскрывать покрытие и сохранить уклоны."),
        ],
    },
    "autopoliv": {
        "cat_id": 92,
        "label": "Автополив на участке",
        "work_type": "Автополив на участке",
        "service_url": "/category/avtopoliv-na-uchastke/",
        "keywords": "автополив на участке, автоматический полив газона, монтаж автополива, капельный полив",
        "problem": "Нужно было организовать регулярный полив газона, сада или посадок без ручного переноса шлангов и пересушенных зон.",
        "technology": "Делим участок на зоны, подбираем спринклеры, капельные линии, трубы, клапаны, контроллер и насосное оборудование. Систему настраиваем по давлению и расписанию.",
        "result": "Газон и посадки получают воду по расписанию, а владелец экономит время и снижает расход воды за счет правильного зонирования.",
        "faq": [
            ("Можно ли сделать автополив на готовом участке?", "Да. Трассы прокладываем с учетом газона, дорожек, посадок и мест, где нельзя повредить покрытие."),
            ("Что входит в монтаж автополива?", "Проект, трубы, спринклеры или капельные линии, клапаны, контроллер, подключение источника воды, настройка зон и запуск."),
        ],
    },
    "blagoustroystvo": {
        "cat_id": 85,
        "label": "Фотогалерея",
        "work_type": "Благоустройство участка",
        "service_url": "/fotogalereja/",
        "keywords": "благоустройство участка, ландшафтные работы, примеры работ",
        "problem": "Участку требовалось комплексное благоустройство: связать дорожки, покрытия, посадки, водоотведение и удобные зоны использования.",
        "technology": "Работы выполняем по логике участка: планировка, подготовка основания, водоотведение, мощение, посадки, газон и финишные элементы благоустройства.",
        "result": "Территория получает законченный вид и понятную структуру: дорожки, зоны отдыха, посадки и инженерные решения работают как единая система.",
        "faq": [
            ("Можно ли делать благоустройство поэтапно?", "Да. Главное заранее понимать общую схему, чтобы этапы не конфликтовали друг с другом."),
            ("С чего начинается комплексное благоустройство?", "С осмотра участка, понимания рельефа, воды, дорожек, посадок и задач владельца."),
        ],
    },
}


OSUSHENIE_CASE_URLS = {
    "https://exp76.ru/fotogalereja/rybinsk-shankhajj/",
    "https://exp76.ru/fotogalereja/kamenniki/",
    "https://exp76.ru/fotogalereja/poselok-iskra-oktjabrja/",
    "https://exp76.ru/fotogalereja/poselok-dubrava-g-jaroslavl/",
    "https://exp76.ru/fotogalereja/aksenovo/",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def norm_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path if parsed.path.endswith("/") else parsed.path + "/"
    return f"https://exp76.ru{path}"


def build_path(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.strip("/")


def city_from_title(title: str) -> str:
    value = title.strip()
    if "," in value:
        return value.split(",")[0].strip()
    return value


def title_for_case(item: dict, category: str) -> str:
    meta = CATEGORIES[category]
    location = city_from_title(item["title"])
    return f"{meta['work_type']}: кейс {location}"


def excerpt(item: dict, category: str) -> str:
    meta = CATEGORIES[category]
    location = city_from_title(item["title"])
    return (
        f"{meta['work_type']} в локации {location}: {item['description']}. "
        "Показываем задачу, ход работ, результат и детали, которые важны для расчета похожего проекта."
    )


def build_case_payload(item: dict, category: str, all_cases_by_url: dict) -> dict:
    meta = CATEGORIES[category]
    title = title_for_case(item, category)
    location = item["title"]
    work_type = meta["work_type"]
    details = item["description"].rstrip(".")
    related = [
        url for url, payload in all_cases_by_url.items()
        if payload["primary_category"] == category and url != norm_url(item["url"])
    ][:4]

    return {
        "url": norm_url(item["url"]),
        "path": build_path(item["url"]),
        "primary_category": category,
        "source_title": item["title"],
        "source_description": item["description"],
        "acf": {
            "cs87_hero_title": title,
            "cs87_hero_subtitle": excerpt(item, category),
            "cs87_hero_btn_primary_text": "Смотреть фото",
            "cs87_hero_btn_primary_url": "#gallery",
            "cs87_hero_btn_secondary_text": "Рассчитать похожий проект",
            "cs87_hero_btn_secondary_url": "#popup",
            "cs87_location": location,
            "cs87_work_type": work_type,
            "cs87_area": "",
            "cs87_timeline": "",
            "cs87_budget": "",
            "cs87_intro_title": f"{work_type} на объекте {location}",
            "cs87_intro_text": (
                f"Этот кейс показывает, как мы решали задачу по направлению «{work_type.lower()}» "
                f"на конкретном участке. По объекту: {details}. Для SEO-страницы важны не только фото, "
                "но и понятное описание работ: что было на участке, почему выбрали именно такую схему "
                "и какой результат получил заказчик."
            ),
            "cs87_challenge_title": "Задача на объекте",
            "cs87_challenge_text": meta["problem"],
            "cs87_solution_title": "Как выполнили работы",
            "cs87_solution_text": (
                f"{meta['technology']} На этом объекте учитывали исходные условия: {details}. "
                "Поэтому решение подбиралось не шаблонно, а под фактический рельеф, грунт, существующие строения и будущую эксплуатацию участка."
            ),
            "cs87_technology_title": "Технология и важные нюансы",
            "cs87_technology_text": meta["technology"],
            "cs87_result_title": "Результат для участка",
            "cs87_result_text": meta["result"],
            "cs87_scope_title": "Что важно при заказе похожих работ",
            "cs87_scope_items": [
                {"item": "Осмотреть участок и определить, откуда приходит вода или где будет основная нагрузка."},
                {"item": "Согласовать схему работ до начала благоустройства, чтобы не переделывать готовые покрытия."},
                {"item": "Подобрать материалы и конструкцию под грунт, рельеф, дом, дорожки и посадки."},
                {"item": "Сразу заложить обслуживание: ревизии, доступ к узлам, понятный отвод воды или удобную эксплуатацию."},
            ],
            "cs87_price_note": (
                "Точную стоимость похожего проекта считаем после осмотра: на цену влияют объем, доступ техники, "
                "материалы, грунт, уклоны, длина трасс и подготовка основания."
            ),
            "cs87_related_case_urls": related,
            "cs87_related_cases": [],
            "cs87_faq_title": f"Вопросы по проекту «{work_type.lower()}»",
            "cs87_faq_items": [
                {"question": question, "answer": answer}
                for question, answer in meta["faq"]
            ],
            "cs87_seo_title": f"{work_type}: пример работ {location} — фото и описание",
            "cs87_seo_description": (
                f"{work_type}: кейс {location}. {details}. Фото, описание работ, технология, "
                "результат и ориентиры для расчета похожего проекта."
            )[:240],
            "cs87_case_keywords": meta["keywords"],
            "cs87_service_url": meta["service_url"],
        },
    }


def main() -> None:
    cases_by_category = read_json(CASES_PATH)
    selected_map = read_json(MAP_PATH)

    for item in cases_by_category.get("drenazh", []):
        if norm_url(item["url"]) in OSUSHENIE_CASE_URLS:
            cases_by_category.setdefault("osushenie", []).append(
                {**item, "source_section": "ОСУШЕНИЕ УЧАСТКА (по смыслу из дренажа/водоотведения)"}
            )

    if "osushenie" in selected_map:
        selected_map["osushenie"]["cases"] = [
            {"title": item["title"], "url": norm_url(item["url"])}
            for item in cases_by_category.get("osushenie", [])
        ]

    primary_by_url = {}
    for category, items in cases_by_category.items():
        if category not in CATEGORIES:
            continue
        for item in items:
            url = norm_url(item["url"])
            if url not in primary_by_url:
                primary_by_url[url] = {"primary_category": category, "item": item}

    payloads = [
        build_case_payload(data["item"], data["primary_category"], primary_by_url)
        for data in primary_by_url.values()
    ]
    payloads.sort(key=lambda case: (case["primary_category"], case["path"]))

    result = {
        "source": "Кейсы семантика.docx + cases_by_category.json",
        "cases": payloads,
        "category_case_maps": selected_map,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    THEME_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    for path in (OUT_PATH, THEME_OUT_PATH, MAP_PATH):
        path.write_text(json.dumps(result if path != MAP_PATH else selected_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {THEME_OUT_PATH}")
    print(f"Cases: {len(payloads)}")


if __name__ == "__main__":
    main()
