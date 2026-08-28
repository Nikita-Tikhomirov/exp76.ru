"""Fail-closed production child architecture for the eight service hubs.

The expanded registry is an immutable candidate ledger tied to paid SERP QIDs.
This module is the later human-reviewed publication decision.  It deliberately
keeps fewer pages when the SERP or the company's public offer cannot support a
separate landing page; deferred candidates never leak into production.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping, Sequence

from .expanded_architecture import EXPANDED_CHILDREN, ExpandedPage


SERVICE_ORDER = tuple(f"S{index}" for index in range(1, 9))
SITE_ROOT = "https://exp76.ru"
EXPECTED_CHILD_COUNTS: Mapping[str, int] = {
    "S1": 5,
    "S2": 4,
    "S3": 5,
    "S4": 5,
    "S5": 6,
    "S6": 3,
    "S7": 5,
    "S8": 4,
}


@dataclass(frozen=True)
class ChildRuling:
    action: str
    target_destination_id: str
    rationale: str


@dataclass(frozen=True)
class UrlDecision:
    current_url: str
    target_url: str
    url_action: str
    current_wp_id: int | None = None


@dataclass(frozen=True)
class FinalizationSerpProbe:
    query_id: str
    destination_id: str
    query: str
    decision: str
    rationale: str
    evidence_ref: str


def _candidate_by_id() -> dict[str, ExpandedPage]:
    return {
        page.destination_id: page
        for pages in EXPANDED_CHILDREN.values()
        for page in pages
    }


_CANDIDATES = _candidate_by_id()


def _new_child(
    service_id: str,
    key: str,
    title: str,
    slug: str,
    query: str,
    business_evidence: str,
    semantic_evidence: str,
    boundary: str,
) -> ExpandedPage:
    return ExpandedPage(
        destination_id=f"{service_id}-CHILD-{key}",
        service_id=service_id,
        page_role="child_service",
        title=title,
        slug=slug,
        representative_query=query,
        offer_status="confirmed",
        business_evidence=business_evidence,
        semantic_evidence=semantic_evidence,
        boundary=boundary,
    )


# Candidate IDs are enumerated explicitly.  A new candidate cannot silently get
# a default keep ruling: validate_child_rulings() fails until it is reviewed.
_KEEP_CANDIDATE_IDS = (
    "S1-CHILD-SKETCH",
    "S1-CHILD-MASTERPLAN",
    "S1-CHILD-DENDROPLAN",
    "S1-CHILD-3D",
    "S1-CHILD-RELIEF",
    "S2-CHILD-ROLL",
    "S2-CHILD-SEED",
    "S2-CHILD-SOIL",
    "S2-CHILD-RESTORE",
    "S3-CHILD-FRUIT",
    "S3-CHILD-CONIFERS",
    "S3-CHILD-SHRUBS",
    "S3-CHILD-LARGE",
    "S4-CHILD-TREE-PRUNING",
    "S4-CHILD-SHRUB-PRUNING",
    "S4-CHILD-LAWN-CARE",
    "S4-CHILD-FLOWERBEDS",
    "S5-CHILD-LEVEL",
    "S5-CHILD-VERTICAL",
    "S5-CHILD-MACHINERY",
    "S5-CHILD-FILL",
    "S6-CHILD-CONCRETE",
    "S6-CHILD-STONE",
    "S7-CHILD-DESIGN",
    "S7-CHILD-INSTALL",
    "S7-CHILD-LANDSCAPE",
    "S7-CHILD-ARCHITECTURAL",
    "S8-CHILD-PIPE",
    "S8-CHILD-GRAVEL",
    "S8-CHILD-CONCRETE",
)


_NON_KEEP_RULINGS: Mapping[str, ChildRuling] = {
    "S2-CHILD-INITIAL-CARE": ChildRuling(
        "merge",
        "S2-HUB",
        "Первичный уход является этапом рулонного или посевного газона; Q000253 ушёл в нерелевантную автомобильную выдачу.",
    ),
    "S3-CHILD-DECIDUOUS": ChildRuling(
        "replace",
        "S3-CHILD-HEDGE",
        "Общий запрос декоративных деревьев не отделился от посадочного хаба; живая изгородь имеет отдельный объект и результат.",
    ),
    "S4-CHILD-MAINTENANCE": ChildRuling(
        "merge",
        "S4-HUB",
        "Комплексное обслуживание сада дублирует сам хаб «Уход за садом»; сохранение двух владельцев создаёт каннибализацию.",
    ),
    "S4-CHILD-SEASONAL": ChildRuling(
        "merge",
        "S4-HUB",
        "Весенние и осенние работы остаются сезонными блоками основного хаба, а не отдельным результатом услуги.",
    ),
    "S5-CHILD-SOIL": ChildRuling(
        "merge",
        "S5-CHILD-LEVEL",
        "Планировка и уплотнение грунта входят в физическое выравнивание; отдельная выдача пересекается с соседними страницами.",
    ),
    "S5-CHILD-FOR-LAWN": ChildRuling(
        "merge",
        "S2-CHILD-SOIL",
        "Подготовка грунта именно под газон принадлежит S2; второй URL в S5 создавал бы cross-service каннибализацию.",
    ),
    "S6-CHILD-SLOPE": ChildRuling(
        "merge",
        "S6-HUB",
        "Уклон является условием основной услуги; Q000213/Q000254 сильно пересекаются с материалами и хабом.",
    ),
    "S6-CHILD-BRICK": ChildRuling(
        "merge",
        "S6-CHILD-STONE",
        "Кирпичная и каменная кладка объединяются в одну masonry-страницу: отдельная кирпичная выдача слишком общая.",
    ),
    "S6-CHILD-BLOCKS": ChildRuling(
        "merge",
        "S6-CHILD-CONCRETE",
        "D007/Q000216/Q000257: выдача ЖБ-блоков пересекается с бетонными стенками до 7/10; сборную технологию раскрываем внутри бетонной страницы.",
    ),
    "S7-CHILD-PATHS": ChildRuling(
        "merge",
        "S7-CHILD-LANDSCAPE",
        "Подсветка дорожек является сценарием ландшафтного света и пересеклась с ним на пяти URL.",
    ),
    "S7-CHILD-SECURITY": ChildRuling(
        "merge",
        "S7-CHILD-INSTALL",
        "Запрос уходит в сигнализацию и общий электромонтаж; функциональный свет остаётся сценарием монтажной страницы.",
    ),
    "S8-CHILD-BASE": ChildRuling(
        "merge",
        "S8-HUB",
        "Основание — обязательный этап любого въезда, а не отдельный покупательский результат.",
    ),
    "S8-CHILD-HEADWALLS": ChildRuling(
        "merge",
        "S8-HUB",
        "Оголовки являются частью конструкции, сильно пересекаются с бетонным въездом и не подтверждены отдельным оффером.",
    ),
    "S8-CHILD-SLABS": ChildRuling(
        "defer",
        "S8-HUB",
        "Дорожные плиты не подтверждены как услуга компании и рискуют забрать интент защищённого владельца мощения.",
    ),
}


CHILD_RULINGS: Mapping[str, ChildRuling] = {
    **{
        destination_id: ChildRuling(
            "keep",
            destination_id,
            "Явно сохранено после проверки оффера, SERP-намерения и редакционной границы.",
        )
        for destination_id in _KEEP_CANDIDATE_IDS
    },
    **_NON_KEEP_RULINGS,
}


def validate_child_rulings(
    rulings: Mapping[str, ChildRuling],
) -> list[str]:
    """Require an explicit decision for every immutable candidate and no others."""

    candidate_ids = set(_CANDIDATES)
    ruling_ids = set(rulings)
    errors: list[str] = []
    missing = sorted(candidate_ids - ruling_ids)
    unknown = sorted(ruling_ids - candidate_ids)
    if missing:
        errors.append(f"child ruling coverage is incomplete: {','.join(missing)}")
    if unknown:
        errors.append(f"child rulings contain unknown ids: {','.join(unknown)}")
    for destination_id, ruling in rulings.items():
        if ruling.action not in {"keep", "merge", "replace", "defer"}:
            errors.append(f"unsupported child ruling: {destination_id}")
        if not ruling.rationale.strip():
            errors.append(f"child ruling has no rationale: {destination_id}")
        if ruling.action == "keep" and ruling.target_destination_id != destination_id:
            errors.append(f"keep ruling must target itself: {destination_id}")
        if ruling.action != "keep" and not ruling.target_destination_id:
            errors.append(f"non-keep ruling has no target: {destination_id}")
    return sorted(set(errors))


_OVERRIDES: Mapping[str, ExpandedPage] = {
    "S1-CHILD-SKETCH": replace(
        _CANDIDATES["S1-CHILD-SKETCH"],
        semantic_evidence="raw/expanded-serp/yandex-api-Q000155.jsonl|Q000155",
    ),
    "S1-CHILD-MASTERPLAN": replace(
        _CANDIDATES["S1-CHILD-MASTERPLAN"],
        representative_query="генеральный план участка ландшафтный дизайн цена",
        semantic_evidence=(
            "raw/expanded-serp/yandex-api-Q000156.jsonl|Q000156|"
            "raw/expanded-serp-targeted/yandex-api-Q000247.jsonl|Q000247|"
            "raw/reviewed-suggest-v6/yandex-suggest-YS000507.jsonl|YS000507"
        ),
        boundary=(
            "Генеральный план как часть ландшафтного проекта: зонирование, дорожки, "
            "озеленение и инженерные решения участка. ГПЗУ, кадастровый и строительный "
            "генплан исключаются; физическая планировка и выравнивание принадлежат S5."
        ),
    ),
    "S1-CHILD-DENDROPLAN": replace(
        _CANDIDATES["S1-CHILD-DENDROPLAN"],
        semantic_evidence="raw/expanded-serp/yandex-api-Q000157.jsonl|Q000157",
    ),
    "S1-CHILD-RELIEF": replace(
        _CANDIDATES["S1-CHILD-RELIEF"],
        semantic_evidence=(
            "raw/expanded-serp/yandex-api-Q000159.jsonl|Q000159|"
            "raw/expanded-serp-targeted/yandex-api-Q000248.jsonl|Q000248"
        ),
    ),
    "S4-CHILD-FLOWERBEDS": replace(
        _CANDIDATES["S4-CHILD-FLOWERBEDS"],
        semantic_evidence="raw/expanded-serp/yandex-api-Q000195.jsonl|Q000195",
    ),
    "S4-CHILD-LAWN-CARE": replace(
        _CANDIDATES["S4-CHILD-LAWN-CARE"],
        semantic_evidence=(
            "raw/expanded-serp/yandex-api-Q000194.jsonl|Q000194|"
            "webmaster_query:стрижка и уход за газоном"
        ),
    ),
    "S7-CHILD-ARCHITECTURAL": replace(
        _CANDIDATES["S7-CHILD-ARCHITECTURAL"],
        semantic_evidence=(
            "raw/expanded-serp/yandex-api-Q000227.jsonl|Q000227|"
            "raw/expanded-serp-targeted/yandex-api-Q000262.jsonl|Q000262"
        ),
    ),
    "S2-CHILD-RESTORE": _new_child(
        "S2",
        "RESTORE",
        "Восстановление и ремонт газона",
        "vosstanovlenie-i-remont-gazona",
        "восстановление газона услуги цена ярославль",
        "business_source:wp-rest/pages/9357#content[пожелтевший-газон+полный-комплекс-работ]",
        "raw/expanded-serp/yandex-api-Q000170.jsonl|Q000170|raw/expanded-serp-targeted/yandex-api-Q000252.jsonl|Q000252",
        "Разовое восстановление повреждённого покрытия; регулярная стрижка, полив и подкормка принадлежат S4-LAWN-CARE.",
    ),
    "S5-CHILD-MACHINERY": _new_child(
        "S5",
        "MACHINERY",
        "Планировка участка спецтехникой",
        "planirovka-uchastka-spectehnikoj",
        "планировка участка трактором цена ярославль",
        "business_source:wp-rest/pages/10345+9533+9415+8640+8613#completed-planning|media:planirovka_territorii2.webp+planirovka_territorii6.webp",
        "raw/expanded-serp/yandex-api-Q000204.jsonl|Q000204|wordstat:Yaroslavl_oblast[планировка участка трактором]=6",
        "Работы техникой с оператором и измеримым результатом; аренда техники без работ исключается.",
    ),
    "S6-CHILD-STONE": _new_child(
        "S6",
        "STONE",
        "Подпорные стенки из камня и кирпича",
        "podpornaya-stenka-iz-kamnya-i-kirpicha",
        "строительство подпорной стенки из камня или кирпича ярославль",
        "business_source:wp-rest/pages/676#content[камень+кирпич]",
        "raw/expanded-serp/yandex-api-Q000215.jsonl|Q000215|raw/expanded-serp-targeted/yandex-api-Q000256.jsonl|Q000256|raw/expanded-serp/yandex-api-Q000217.jsonl|Q000217|raw/expanded-serp-targeted/yandex-api-Q000258.jsonl|Q000258",
        "Каменная и кирпичная кладка объединены; монолитный бетон и сборные ЖБ-блоки остаются отдельными технологиями.",
    ),
}


_ADDITIONS: Mapping[str, ExpandedPage] = {
    "S3-CHILD-HEDGE": _new_child(
        "S3",
        "HEDGE",
        "Посадка живой изгороди",
        "posadka-zhivoj-izgorodi",
        "посадка живой изгороди под ключ ярославль",
        "business_source:wp-rest/pages/6871#content[посадка-кустарника-как-живая-изгородь]",
        "raw/expanded-serp-alternatives/yandex-api-Q000270.jsonl|Q000270",
        "Создание линейной посадки; последующая стрижка и обслуживание принадлежат S4-SHRUB-PRUNING.",
    ),
    "S4-CHILD-PEST": _new_child(
        "S4",
        "PEST",
        "Обработка сада от болезней и вредителей",
        "obrabotka-sada-ot-boleznej-i-vreditelej",
        "обработка сада от болезней и вредителей цена ярославль",
        "business_source:wp-rest/pages/9357#content[обработки-от-вредителей-и-возбудителей-болезней]",
        "raw/expanded-serp-finalization/yandex-api-Q000273.jsonl|Q000273",
        "Только диагностика и обработка растений; клещи, комары и санитарная обработка территории исключаются.",
    ),
    "S5-CHILD-CULTIVATION": _new_child(
        "S5",
        "CULTIVATION",
        "Культивация участка",
        "kultivaciya-uchastka",
        "культивация участка цена за сотку ярославль",
        "business_source:wp-rest/pages/8636#content[культивирование-земли+планировка]",
        "raw/expanded-serp-finalization/yandex-api-Q000274.jsonl|Q000274",
        "Отдельная механическая обработка земли; планировка рельефа, посев и устройство газона не входят.",
    ),
    "S5-CHILD-STUMPS": _new_child(
        "S5",
        "STUMPS",
        "Корчевание пней на участке",
        "vykorchevyvanie-pnejj-spil-derevev",
        "корчевание пней цена ярославль",
        "business_source:wp-rest/pages/6870#content[отдельная-услуга-викорчевывание-пней]+wp-rest/pages/8613#content[корчевание-пней-и-планировка]",
        "raw/yandex-browser-serp-stump/yandex-browser-YB000002.json|YB000002|raw/reviewed-suggest-v6/yandex-suggest-YS000553.jsonl|YS000553|raw/yandex-browser-serp/yandex-browser-YB000001.json|YB000001",
        "Корчевание и удаление пней с расчисткой места под дальнейшие работы. Формирующая и санитарная обрезка принадлежит S4; вывоз строительного мусора не входит.",
    ),
    "S6-CHILD-WOOD": _new_child(
        "S6",
        "WOOD",
        "Деревянные подпорные стенки",
        "podpornaya-stenka-iz-dereva",
        "деревянная подпорная стенка цена работы ярославль",
        "business_source:wp-rest/pages/676#content[услуги-из-любых-материалов+дерево]",
        "raw/expanded-serp-finalization/yandex-api-Q000276.jsonl|Q000276|raw/reviewed-suggest-v6/yandex-suggest-YS000559.jsonl|YS000559",
        "Только невысокие деревянные или бревенчатые конструкции после оценки применимости; заборы и декоративные ограждения исключаются.",
    ),
    "S7-CHILD-HOLIDAY": _new_child(
        "S7",
        "HOLIDAY",
        "Новогоднее освещение загородного дома",
        "novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti",
        "монтаж новогоднего освещения дома ярославль",
        "business_source:wp-rest/pages/10381#published-service",
        "raw/expanded-serp-alternatives/yandex-api-Q000272.jsonl|Q000272",
        "Сезонный монтаж праздничной подсветки; постоянное фасадное освещение принадлежит S7-ARCHITECTURAL.",
    ),
    "S8-CHILD-PARKING": _new_child(
        "S8",
        "PARKING",
        "Въезд через канаву с парковочной площадкой",
        "vezd-cherez-kanavu-s-parkovochnoj-ploshchadkoj",
        "въезд на участок с парковочной площадкой под ключ ярославль",
        "business_source:wp-rest/pages/9282#content[въездная-площадка+площадка-для-автомобиля]",
        "raw/expanded-serp-finalization/yandex-api-Q000280.jsonl|Q000280|raw/serp/yandex-api-Q000129.jsonl|Q000129|raw/serp/yandex-api-Q000131.jsonl|Q000131",
        "Только переход через канаву с площадкой непосредственно за ним; отдельная парковка, плитка и мощение принадлежат защищённому владельцу.",
    ),
}


def _reviewed_candidate(destination_id: str) -> ExpandedPage:
    return _OVERRIDES.get(destination_id, _CANDIDATES[destination_id])


def _kept(service_id: str) -> tuple[ExpandedPage, ...]:
    return tuple(
        _reviewed_candidate(page.destination_id)
        for page in EXPANDED_CHILDREN[service_id]
        if CHILD_RULINGS[page.destination_id].action == "keep"
    )


REVIEWED_CHILDREN: Mapping[str, tuple[ExpandedPage, ...]] = {
    "S1": _kept("S1"),
    "S2": _kept("S2"),
    "S3": (*_kept("S3"), _ADDITIONS["S3-CHILD-HEDGE"]),
    "S4": (*_kept("S4"), _ADDITIONS["S4-CHILD-PEST"]),
    "S5": (
        *_kept("S5"),
        _ADDITIONS["S5-CHILD-CULTIVATION"],
        _ADDITIONS["S5-CHILD-STUMPS"],
    ),
    "S6": (*_kept("S6"), _ADDITIONS["S6-CHILD-WOOD"]),
    "S7": (*_kept("S7"), _ADDITIONS["S7-CHILD-HOLIDAY"]),
    "S8": (*_kept("S8"), _ADDITIONS["S8-CHILD-PARKING"]),
}


SPARSE_HUB_JUSTIFICATIONS: Mapping[str, str] = {
    "S2": (
        "Q000253 rejected первичный уход; Q000042/Q000048 показывают спрос на гидропосев, "
        "но публичная страница 6868 подтверждает только посевной и рулонный способы. "
        "Пятая страница запрещена до подтверждения нового оборудования и выполненных объектов."
    ),
    "S6": (
        "D007/Q000216/Q000257 объединяют ЖБ-блоки с бетоном из-за overlap до 7/10. Q000276 не дал "
        "wood-specific результатов, но публичный оффер и Yandex Suggest прямо подтверждают деревянные "
        "стенки. Кирпич объединён с камнем; четвёртую страницу без отдельного интента не создаём."
    ),
    "S8": (
        "Q000277/Q000278/Q000279 показали один общий интент трубы: exact overlap 7/10, 6/10 и 5/10. "
        "Основание и оголовки являются этапами, а дорожные плиты не подтверждены и пересекаются с "
        "защищённым мощением. Четыре страницы — доказанный максимум."
    ),
}


BACKLOG_CHILDREN: Mapping[str, str] = {
    "S2-CHILD-HYDROSEED": "Есть спрос, но компания публично подтверждает только посевной и рулонный газон.",
    "S2-CHILD-ARTIFICIAL": "Монтаж искусственного газона не подтверждён бизнесом и локальной сервисной выдачей.",
    "S5-CHILD-SOIL-REMOVAL": "Q000275 подтверждает спрос, но действующая страница 667 не подтверждает отдельную услугу вывоза грунта.",
    "S6-CHILD-GABIONS": "Q000271 подтверждает интент, но строительство габионов требует подтверждения клиента.",
    "S8-CHILD-SLABS": "Нет подтверждённого оффера, есть риск пересечения с защищённой категорией мощения.",
    "S8-CHILD-PIPE-PLASTIC": "Q000277 объединён с общим владельцем S8-CHILD-PIPE.",
    "S8-CHILD-PIPE-STEEL": "Q000278 объединён с общим владельцем S8-CHILD-PIPE.",
    "S8-CHILD-PIPE-RC": "Q000279 объединён с общим владельцем S8-CHILD-PIPE.",
}


FINALIZATION_SERP_QUERIES: tuple[FinalizationSerpProbe, ...] = (
    FinalizationSerpProbe("Q000273", "S4-CHILD-PEST", "обработка сада от болезней и вредителей цена ярославль", "keep", "Пять заголовков явно содержат модификаторы болезней или вредителей; остальные результаты относятся к общей обработке сада. Оффер подтверждён страницей 9357.", "raw/expanded-serp-finalization/yandex-api-Q000273.jsonl|Q000273"),
    FinalizationSerpProbe("Q000274", "S5-CHILD-CULTIVATION", "культивация участка цена за сотку ярославль", "keep", "Все десять результатов предлагают культивацию или вспашку как услугу в регионе.", "raw/expanded-serp-finalization/yandex-api-Q000274.jsonl|Q000274"),
    FinalizationSerpProbe("Q000275", "S5-CHILD-SOIL-REMOVAL", "вывоз грунта с участка с погрузкой цена ярославль", "defer_business_confirmation", "Коммерческий интент силён: 10/10 результатов содержат грунт. Но действующая страница 667 не подтверждает отдельный оффер, поэтому URL остаётся в backlog.", "raw/expanded-serp-finalization/yandex-api-Q000275.jsonl|Q000275"),
    FinalizationSerpProbe("Q000276", "S6-CHILD-WOOD", "деревянная подпорная стенка цена работы ярославль", "keep_business_proven_low_frequency", "В платной выдаче 0 wood-specific заголовков, однако страница 676 прямо продаёт деревянные и бревенчатые стенки, а Yandex Suggest подтверждает точную формулировку. Оставляем узкую низкочастотную страницу.", "raw/expanded-serp-finalization/yandex-api-Q000276.jsonl|Q000276"),
    FinalizationSerpProbe("Q000277", "S8-CHILD-PIPE-PLASTIC", "пластиковая труба в канаву для заезда монтаж ярославль", "merge_to_generic_pipe", "Материал не отделился; exact overlap с steel 7/10 и RC 6/10.", "raw/expanded-serp-finalization/yandex-api-Q000277.jsonl|Q000277"),
    FinalizationSerpProbe("Q000278", "S8-CHILD-PIPE-STEEL", "стальная труба в канаву для заезда установка ярославль", "merge_to_generic_pipe", "Материал не отделился; exact overlap с plastic 7/10 и RC 5/10.", "raw/expanded-serp-finalization/yandex-api-Q000278.jsonl|Q000278"),
    FinalizationSerpProbe("Q000279", "S8-CHILD-PIPE-RC", "железобетонная труба в канаву для заезда монтаж ярославль", "merge_to_generic_pipe", "Запрос ведёт к общей услуге въезда с трубой; отдельная material-page каннибализировала бы владельца.", "raw/expanded-serp-finalization/yandex-api-Q000279.jsonl|Q000279"),
    FinalizationSerpProbe("Q000280", "S8-CHILD-PARKING", "въезд на участок с парковочной площадкой под ключ ярославль", "keep", "Только 4/10 заголовков содержат площадку или парковку и один результат явно объединяет её с въездом. Страница допустима лишь для связки «канава + площадка сразу за въездом»; отдельное мощение исключено.", "raw/expanded-serp-finalization/yandex-api-Q000280.jsonl|Q000280"),
)


def all_reviewed_children() -> tuple[ExpandedPage, ...]:
    """Return the stable production child sequence."""

    return tuple(
        page
        for service_id in SERVICE_ORDER
        for page in REVIEWED_CHILDREN[service_id]
    )


APPROVED_FINAL_IDS = (
    "S1-CHILD-SKETCH", "S1-CHILD-MASTERPLAN", "S1-CHILD-DENDROPLAN", "S1-CHILD-3D", "S1-CHILD-RELIEF",
    "S2-CHILD-ROLL", "S2-CHILD-SEED", "S2-CHILD-SOIL", "S2-CHILD-RESTORE",
    "S3-CHILD-FRUIT", "S3-CHILD-CONIFERS", "S3-CHILD-SHRUBS", "S3-CHILD-LARGE", "S3-CHILD-HEDGE",
    "S4-CHILD-TREE-PRUNING", "S4-CHILD-SHRUB-PRUNING", "S4-CHILD-LAWN-CARE", "S4-CHILD-FLOWERBEDS", "S4-CHILD-PEST",
    "S5-CHILD-LEVEL", "S5-CHILD-VERTICAL", "S5-CHILD-MACHINERY", "S5-CHILD-FILL", "S5-CHILD-CULTIVATION", "S5-CHILD-STUMPS",
    "S6-CHILD-CONCRETE", "S6-CHILD-STONE", "S6-CHILD-WOOD",
    "S7-CHILD-DESIGN", "S7-CHILD-INSTALL", "S7-CHILD-LANDSCAPE", "S7-CHILD-ARCHITECTURAL",
    "S7-CHILD-HOLIDAY",
    "S8-CHILD-PIPE", "S8-CHILD-GRAVEL", "S8-CHILD-CONCRETE", "S8-CHILD-PARKING",
)
_CREATE_URL_IDS = tuple(
    destination_id
    for destination_id in APPROVED_FINAL_IDS
    if destination_id not in {"S5-CHILD-STUMPS", "S7-CHILD-HOLIDAY"}
)
_APPROVED_PAGE_BY_ID = {
    page.destination_id: page
    for page in all_reviewed_children()
}


_FINAL_BY_ID = {page.destination_id: page for page in all_reviewed_children()}
URL_DECISIONS: Mapping[str, UrlDecision] = {
    **{
        destination_id: UrlDecision(
            current_url="",
            target_url=f"{SITE_ROOT}/{_FINAL_BY_ID[destination_id].slug}/",
            url_action="create",
        )
        for destination_id in _CREATE_URL_IDS
    },
    "S5-CHILD-STUMPS": UrlDecision(
        current_url=f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
        target_url=f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
        url_action="reuse",
        current_wp_id=6870,
    ),
    "S7-CHILD-HOLIDAY": UrlDecision(
        current_url=f"{SITE_ROOT}/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
        target_url=f"{SITE_ROOT}/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
        url_action="reuse",
        current_wp_id=10381,
    ),
}
_FROZEN_URL_DECISIONS = dict(URL_DECISIONS)
_FROZEN_REUSE_OWNERS = {
    "S5-CHILD-STUMPS": UrlDecision(
        current_url=f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
        target_url=f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
        url_action="reuse",
        current_wp_id=6870,
    ),
    "S7-CHILD-HOLIDAY": UrlDecision(
        current_url=f"{SITE_ROOT}/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
        target_url=f"{SITE_ROOT}/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
        url_action="reuse",
        current_wp_id=10381,
    ),
}

# Reused WordPress pages are never recreated or silently converted.  This
# contract is consumed by the release builder/importer so the exact page ID and
# permalink survive while the rendering template and intent boundary are fixed.
REUSE_DEPLOYMENT_REQUIREMENTS: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "S5-CHILD-STUMPS": MappingProxyType({
        "current_post_type": "page",
        "target_template": "servicepost.php",
        "preserve_post_id": "6870",
        "preserve_permalink": f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
        "excluded_primary_intents": "обрезка|спил деревьев|фрезеровка пней",
    }),
    "S7-CHILD-HOLIDAY": MappingProxyType({
        "current_post_type": "page",
        "target_template": "servicepost.php",
        "preserve_post_id": "10381",
        "preserve_permalink": f"{SITE_ROOT}/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
        "excluded_primary_intents": "постоянное фасадное освещение|ландшафтное освещение",
    }),
})


_PROTECTED_TEXT_PATTERNS = (
    ("автополив",),
    ("автомат", "полив"),
    ("дренаж",),
    ("ливнев",),
    ("осушен",),
    ("отмост",),
    ("тротуарн", "плит"),
)
_PROTECTED_SLUG_PATTERNS = (
    ("avtopoliv",),
    ("avtomatich", "poliv"),
    ("drenazh",),
    ("livnev",),
    ("osush",),
    ("otmost",),
    ("trotuar", "plitk"),
)


def _claims_protected_owner(page: ExpandedPage) -> bool:
    slug = page.slug.casefold()
    if any(
        all(root in slug for root in pattern)
        for pattern in _PROTECTED_SLUG_PATTERNS
    ):
        return True
    for value in (page.title, page.representative_query):
        tokens = re.findall(r"[а-яёa-z0-9]+", value.casefold())
        if any(
            all(any(token.startswith(root) for token in tokens) for root in pattern)
            for pattern in _PROTECTED_TEXT_PATTERNS
        ):
            return True
    return False


def validate_reviewed_child_architecture(
    children: Mapping[str, Sequence[ExpandedPage]] = REVIEWED_CHILDREN,
    *,
    rulings: Mapping[str, ChildRuling] = CHILD_RULINGS,
    url_decisions: Mapping[str, UrlDecision] = URL_DECISIONS,
) -> list[str]:
    """Fail closed on sparse, duplicate, protected, gated or unowned pages."""

    errors = validate_child_rulings(rulings)
    services = set(SERVICE_ORDER)
    if set(children) != services:
        errors.append("reviewed children must define exactly S1-S8")
    final_pages = [page for service_id in SERVICE_ORDER for page in children.get(service_id, ())]
    final_id_sequence = tuple(page.destination_id for page in final_pages)
    final_ids = {page.destination_id for page in final_pages}
    if len(final_ids) != len(final_pages):
        errors.append("reviewed children contain duplicate destination ids")
    if final_id_sequence != APPROVED_FINAL_IDS:
        errors.append("reviewed children differ from approved child ids or order")

    for service_id in SERVICE_ORDER:
        count = len(children.get(service_id, ()))
        if count != EXPECTED_CHILD_COUNTS[service_id]:
            errors.append(
                f"{service_id} differs from approved child count: "
                f"{count} != {EXPECTED_CHILD_COUNTS[service_id]}"
            )

    slugs: set[str] = set()
    queries: set[str] = set()
    for page in final_pages:
        query = " ".join(page.representative_query.casefold().split())
        if page.service_id not in services or page not in children.get(page.service_id, ()):
            errors.append(f"reviewed child has invalid service owner: {page.destination_id}")
        if _APPROVED_PAGE_BY_ID.get(page.destination_id) != page:
            errors.append(f"reviewed child differs from approved page record: {page.destination_id}")
        if page.page_role != "child_service":
            errors.append(f"reviewed child has invalid role: {page.destination_id}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", page.slug):
            errors.append(f"reviewed child has invalid slug: {page.destination_id}")
        if page.slug in slugs:
            errors.append(f"reviewed children contain duplicate slug: {page.slug}")
        slugs.add(page.slug)
        if not query or query in queries:
            errors.append(f"reviewed children contain duplicate or blank query: {query}")
        queries.add(query)
        if _claims_protected_owner(page):
            errors.append(f"reviewed child claims a protected owner: {page.destination_id}")
        if page.offer_status != "confirmed":
            errors.append(f"production child is not confirmed: {page.destination_id}")
        if not page.business_evidence.startswith("business_source:"):
            errors.append(f"confirmed reviewed child has no business source: {page.destination_id}")
        if "pending" in page.semantic_evidence.casefold():
            errors.append(f"production child has pending semantic evidence: {page.destination_id}")
        if "seed_gap:" in page.semantic_evidence.casefold():
            errors.append(
                f"production child has unverified semantic evidence: {page.destination_id}"
            )
        if not all((page.title, page.semantic_evidence, page.boundary)):
            errors.append(f"reviewed child is incomplete: {page.destination_id}")

    if set(url_decisions) != final_ids:
        errors.append("URL decision coverage differs from production children")
    for destination_id in APPROVED_FINAL_IDS:
        if url_decisions.get(destination_id) != _FROZEN_URL_DECISIONS[destination_id]:
            errors.append(f"frozen URL decision differs: {destination_id}")
    for destination_id, expected_owner in _FROZEN_REUSE_OWNERS.items():
        if url_decisions.get(destination_id) != expected_owner:
            errors.append(f"frozen reuse owner differs: {destination_id}")
    target_urls: set[str] = set()
    for destination_id, decision in url_decisions.items():
        page = next((item for item in final_pages if item.destination_id == destination_id), None)
        if page is None:
            continue
        expected_target = _FROZEN_URL_DECISIONS[destination_id].target_url
        if decision.target_url != expected_target:
            errors.append(f"URL target differs from reviewed slug: {destination_id}")
        if decision.target_url in target_urls:
            errors.append(f"duplicate production target URL: {decision.target_url}")
        target_urls.add(decision.target_url)
        if decision.url_action == "create":
            if decision.current_url or decision.current_wp_id is not None:
                errors.append(f"create URL has an existing owner: {destination_id}")
        elif decision.url_action == "reuse":
            if not decision.current_url or decision.current_wp_id is None:
                errors.append(f"reuse URL has no existing owner: {destination_id}")
        else:
            errors.append(f"unsupported URL action: {destination_id}")

    kept_candidates = {
        destination_id
        for destination_id, ruling in rulings.items()
        if ruling.action == "keep"
    }
    if kept_candidates != final_ids & set(_CANDIDATES):
        errors.append("keep rulings differ from reviewed candidate children")
    allowed_targets = final_ids | {f"S{index}-HUB" for index in range(1, 9)}
    for destination_id, ruling in rulings.items():
        if ruling.action != "keep" and ruling.target_destination_id not in allowed_targets:
            errors.append(f"child ruling has invalid target: {destination_id}")
    if set(BACKLOG_CHILDREN) & final_ids:
        errors.append("deferred child leaked into production")
    return sorted(set(errors))


_MODULE_ERRORS = validate_reviewed_child_architecture()
if _MODULE_ERRORS:
    raise RuntimeError("; ".join(_MODULE_ERRORS))
