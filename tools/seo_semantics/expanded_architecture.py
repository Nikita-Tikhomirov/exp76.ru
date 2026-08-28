"""Expanded S1-S8 page candidates for the production SEO silo.

This registry is deliberately separate from the current release manifest.  It
describes the next architecture and provides the representative-query queue
used to prove or reject each destination before content is published.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


SERVICE_IDS = tuple(f"S{index}" for index in range(1, 9))
OFFER_STATUSES = {"confirmed", "needs_business_confirmation", "not_applicable"}
PROTECTED_SLUGS = {
    "avtopoliv-na-uchastke",
    "drenazh-uchastka",
    "livnevaya-kanalizatsiya",
    "osushenie-uchastka",
    "otmostka-vokrug-doma",
    "ukladka-trotuarnoy-plitki",
}
PROTECTED_QUERY_OWNERS = {
    "автополив на участке",
    "дренаж участка",
    "ливневая канализация",
    "осушение участка",
    "отмостка вокруг дома",
    "укладка тротуарной плитки",
}
QUEUE_COLUMNS = (
    "query_id",
    "query",
    "service_id",
    "intent",
    "region",
    "device",
    "destination_id",
    "reason",
)


@dataclass(frozen=True)
class ExpandedPage:
    destination_id: str
    service_id: str
    page_role: str
    title: str
    slug: str
    representative_query: str
    offer_status: str
    business_evidence: str
    semantic_evidence: str
    boundary: str


def _child(
    service_id: str,
    key: str,
    title: str,
    slug: str,
    query: str,
    business_evidence: str,
    semantic_evidence: str,
    boundary: str,
    *,
    offer_status: str = "confirmed",
) -> ExpandedPage:
    return ExpandedPage(
        destination_id=f"{service_id}-CHILD-{key}",
        service_id=service_id,
        page_role="child_service",
        title=title,
        slug=slug,
        representative_query=query,
        offer_status=offer_status,
        business_evidence=business_evidence,
        semantic_evidence=semantic_evidence,
        boundary=boundary,
    )


def _article(
    service_id: str,
    key: str,
    title: str,
    slug: str,
    query: str,
    semantic_evidence: str,
    boundary: str,
) -> ExpandedPage:
    return ExpandedPage(
        destination_id=f"{service_id}-ARTICLE-{key}",
        service_id=service_id,
        page_role="article",
        title=title,
        slug=slug,
        representative_query=query,
        offer_status="not_applicable",
        business_evidence="not_applicable:informational_destination",
        semantic_evidence=semantic_evidence,
        boundary=boundary,
    )


EXPANDED_CHILDREN: Mapping[str, tuple[ExpandedPage, ...]] = {
    "S1": (
        _child(
            "S1", "SKETCH", "Эскизный проект участка", "eskiznyj-proekt-uchastka",
            "заказать эскизный проект участка",
            "business_source:service-v2/landshaftnoe-proektirovanie.json#scope[Эскиз и зонирование]",
            "seed_gap:эскизный проект участка",
            "Эскиз, зонирование и концепция; полный комплект проекта остаётся хабу.",
        ),
        _child(
            "S1", "MASTERPLAN", "Генеральный план участка", "generalnyj-plan-uchastka",
            "заказать генеральный план участка",
            "business_source:service-v2/landshaftnoe-proektirovanie.json#scope[Генеральный план]",
            "seed_gap:генеральный план участка ландшафтный дизайн",
            "Проектный генплан; физическая планировка и выравнивание принадлежат S5.",
        ),
        _child(
            "S1", "DENDROPLAN", "Дендроплан участка", "dendroplan-uchastka",
            "заказать дендроплан участка",
            "business_source:service-v2/landshaftnoe-proektirovanie.json#scope[Дендроплан и озеленение]",
            "seed_gap:дендроплан участка",
            "Проект размещения и ведомость растений; физическая посадка принадлежит S3.",
        ),
        _child(
            "S1", "3D", "3D-визуализация ландшафтного дизайна",
            "3d-vizualizatsiya-landshaftnogo-dizajna",
            "заказать 3d визуализацию ландшафтного дизайна",
            "business_source:service-v2/landshaftnoe-proektirovanie.json#scope[3D-визуализация]",
            "wordstat:Yaroslavl_oblast[ландшафтный дизайн участка 3д]=1",
            "Коммерческая визуализация проекта; программы и ИИ относятся к статье.",
        ),
        _child(
            "S1", "RELIEF", "Проект вертикальной планировки участка",
            "proekt-vertikalnoj-planirovki-uchastka",
            "заказать проект вертикальной планировки участка",
            "business_source:service-v2/landshaftnoe-proektirovanie.json#pricing[план организации рельефа]",
            "seed_gap:проект вертикальной планировки участка",
            "Только проект отметок и уклонов; земляные работы принадлежат S5.",
        ),
    ),
    "S2": (
        _child(
            "S2", "ROLL", "Рулонный газон под ключ", "rulonnyj-gazon-pod-kljuch",
            "укладка рулонного газона под ключ",
            "business_source:service-v2/gazon-posevnojj-i-gazon-rulonnyjj.json#services[Рулонный газон]",
            "SERP-D405C455A674|SERP-0767F40D1ED4|wordstat:Yaroslavl_oblast=288",
            "Подготовка и укладка рулонов; товарный запрос без работ исключается.",
        ),
        _child(
            "S2", "SEED", "Посевной газон под ключ", "posevnoj-gazon-pod-kljuch",
            "устройство посевного газона под ключ",
            "business_source:service-v2/gazon-posevnojj-i-gazon-rulonnyjj.json#services[Посевной газон]",
            "SERP-6070ECC246E8|SERP-1E2A5B0176EC|wordstat:Yaroslavl_oblast=22",
            "Посев и формирование покрытия; рулонный вариант остаётся отдельной услугой.",
        ),
        _child(
            "S2", "SOIL", "Подготовка грунта под газон", "podgotovka-grunta-pod-gazon",
            "подготовка грунта под газон цена",
            "business_source:service-v2/gazon-posevnojj-i-gazon-rulonnyjj.json#scope[Подготовка почвы]",
            "wordstat:Yaroslavl_oblast[подготовка грунта под газон]=2",
            "Верхний слой и основание газона; изменение общего рельефа принадлежит S5.",
        ),
        _child(
            "S2", "RESTORE", "Восстановление и ремонт газона",
            "vosstanovlenie-i-remont-gazona", "восстановление газона услуги цена",
            "business_confirmation_required:восстановление газона как отдельная услуга",
            "SERP-63EDD3F67224|wordstat:Yaroslavl_oblast=8",
            "Капитальное восстановление покрытия; регулярный уход принадлежит S4.",
            offer_status="needs_business_confirmation",
        ),
        _child(
            "S2", "INITIAL-CARE", "Первичный уход за новым газоном",
            "pervichnyj-uhod-za-novym-gazonom", "услуга ухода за новым газоном",
            "business_confirmation_required:первичный уход после устройства",
            "seed_gap:уход за новым газоном",
            "Только стартовый период после посева или укладки; сезонное обслуживание принадлежит S4.",
            offer_status="needs_business_confirmation",
        ),
    ),
    "S3": (
        _child(
            "S3", "DECIDUOUS", "Посадка декоративных деревьев",
            "posadka-dekorativnyh-derevev", "услуги посадки декоративных деревьев",
            "business_source:service-v2/posadka-derevev-i-kustarnikov.json#intro[деревья любого размера]",
            "seed_gap:посадка декоративных деревьев",
            "Лиственные декоративные деревья; плодовые, хвойные и крупномеры разведены.",
        ),
        _child(
            "S3", "FRUIT", "Посадка плодовых деревьев", "posadka-plodovyh-derevev",
            "услуги посадки плодовых деревьев",
            "business_source:service-v2/posadka-derevev-i-kustarnikov.json#intro[деревья любого размера]",
            "SERP-B063D3C3AD98|wordstat:Yaroslavl_oblast=57",
            "Плодовый сад; декоративные деревья и общий подбор остаются соседним страницам.",
        ),
        _child(
            "S3", "CONIFERS", "Посадка хвойных деревьев", "posadka-hvojnyh-derevev",
            "услуги посадки хвойных деревьев",
            "business_source:service-v2/posadka-derevev-i-kustarnikov.json#scope[Хвойные посадки]",
            "SERP-785822A3ED71|wordstat:Yaroslavl_oblast=44",
            "Хвойные деревья и группы; постоянный уход принадлежит S4.",
        ),
        _child(
            "S3", "SHRUBS", "Посадка кустарников", "posadka-kustarnikov",
            "посадка кустарников под ключ",
            "business_source:service-v2/posadka-derevev-i-kustarnikov.json#scope[Кустарники и группы]",
            "SERP-3DA3A83AC9A8|wordstat:Yaroslavl_oblast=218",
            "Кустарниковые группы; обрезка и обслуживание принадлежат S4.",
        ),
        _child(
            "S3", "LARGE", "Посадка крупномеров", "posadka-krupnomerov",
            "посадка крупномеров цена",
            "business_source:service-v2/posadka-derevev-i-kustarnikov.json#scope[Деревья и крупные формы]",
            "SERP-09010110F02E|wordstat:Yaroslavl_oblast=4",
            "Крупные формы, доставка и механизация; молодые деревья разведены по видам.",
        ),
    ),
    "S4": (
        _child(
            "S4", "TREE-PRUNING", "Обрезка деревьев", "obrezka-derevev",
            "заказать обрезку деревьев цена",
            "business_source:service-v2/ukhod-za-sadom.json#scope[Обрезка деревьев и кустарников]",
            "SERP-B592CED7E831|SERP-0D0F2C22B0AB|wordstat:Yaroslavl_oblast=494",
            "Только деревья; кустарники и живая изгородь разведены.",
        ),
        _child(
            "S4", "SHRUB-PRUNING", "Обрезка кустарников и живой изгороди",
            "obrezka-kustarnikov-i-zhivoj-izgorodi", "стрижка кустарников и живой изгороди цена",
            "business_source:service-v2/ukhod-za-sadom.json#scope[Обрезка деревьев и кустарников]",
            "SERP-8F99DD3FB843|wordstat:Yaroslavl_oblast=58",
            "Кустарники и изгороди; деревья остаются отдельной услугой.",
        ),
        _child(
            "S4", "MAINTENANCE", "Комплексное обслуживание сада",
            "obsluzhivanie-sada", "комплексное обслуживание сада услуги",
            "business_source:service-v2/ukhod-za-sadom.json#intro+scope",
            "SERP-AA3B1ED86F1C|SERP-7DE3AAD9BA6E|SERP-7BD020023148",
            "Регулярные визиты и комплекс работ; разовые сезонные работы разведены.",
        ),
        _child(
            "S4", "LAWN-CARE", "Уход и обслуживание газона", "uhod-za-gazonom",
            "услуги по уходу за газоном цена",
            "business_source:service-v2/ukhod-za-sadom.json#scope[Уход за газоном]",
            "webmaster_query:услуги по уходу за газоном|seed_gap:уход за газоном",
            "Регулярный уход; устройство и капитальное восстановление принадлежат S2.",
        ),
        _child(
            "S4", "FLOWERBEDS", "Уход за цветниками и клумбами",
            "uhod-za-cvetnikami-i-klumbami", "услуги по уходу за цветниками и клумбами",
            "business_source:service-v2/ukhod-za-sadom.json#scope[Цветники, клумбы и декоративные зоны]",
            "seed_gap:уход за цветниками и клумбами",
            "Обслуживание существующих цветников; создание посадок принадлежит S3.",
        ),
        _child(
            "S4", "SEASONAL", "Сезонные работы в саду", "sezonnyj-uhod-za-sadom",
            "сезонный уход за садом услуги",
            "business_source:service-v2/ukhod-za-sadom.json#scope[Подготовка сада к смене сезона]",
            "SERP-651B7A994F7E",
            "Разовые весенние и осенние комплексы; абонентское обслуживание разведено.",
        ),
    ),
    "S5": (
        _child(
            "S5", "LEVEL", "Выравнивание участка", "vyravnivanie-uchastka",
            "выравнивание участка цена",
            "business_source:service-v2/planirovka-territorii.json#scope[Выравнивание и формирование поверхностей]",
            "SERP-13FD00FC92C7|SERP-3AF29E33EBAC|wordstat:Yaroslavl_oblast=251",
            "Результат — ровная поверхность; специальные технологии и назначения разведены.",
        ),
        _child(
            "S5", "VERTICAL", "Вертикальная планировка и формирование уклонов",
            "vertikalnaya-planirovka-uchastka", "вертикальная планировка участка цена",
            "business_source:service-v2/planirovka-territorii.json#intro[рельеф и направление воды]",
            "wordstat:Yaroslavl_oblast=4|Q000080",
            "Физическое формирование отметок; проект рельефа принадлежит S1.",
        ),
        _child(
            "S5", "MACHINERY", "Планировка участка спецтехникой",
            "planirovka-uchastka-spectehnikoj", "планировка участка трактором цена",
            "business_confirmation_required:механизированная планировка своей техникой",
            "wordstat:Yaroslavl_oblast[трактором]=21",
            "Работы с оператором и результатом; аренда техники без работ исключается.",
            offer_status="needs_business_confirmation",
        ),
        _child(
            "S5", "FILL", "Отсыпка и подъём участка грунтом",
            "otsypka-i-podem-uchastka", "отсыпка и подъем участка грунтом цена",
            "business_source:service-v2/planirovka-territorii.json#pricing[добавить или вывезти грунт]",
            "SERP-490CDCE58295|wordstat:Yaroslavl_oblast=7",
            "Добавление материала и изменение отметок; продажа грунта исключается.",
        ),
        _child(
            "S5", "SOIL", "Планировка и уплотнение грунта",
            "planirovka-i-uplotnenie-grunta", "планировка и уплотнение грунта цена",
            "business_source:service-v2/planirovka-territorii.json#scope[Работа с грунтом]",
            "SERP-AE4638D982DC|wordstat:Yaroslavl_oblast=21",
            "Финишное разравнивание и уплотнение слоя; общая планировка остаётся хабу.",
        ),
        _child(
            "S5", "FOR-LAWN", "Подготовка и выравнивание участка под газон",
            "podgotovka-uchastka-pod-gazon", "выравнивание участка под газон цена",
            "business_source:service-v2/planirovka-territorii.json#scope[Подготовка к озеленению]",
            "wordstat:Yaroslavl_oblast=27",
            "Рельеф и грунт до плодородного слоя; устройство газона принадлежит S2.",
        ),
    ),
    "S6": (
        _child(
            "S6", "SLOPE", "Подпорные стенки на участке с уклоном",
            "podpornaya-stenka-na-uchastke-s-uklonom",
            "строительство подпорной стенки на участке с уклоном",
            "business_source:service-v2/podpornye-stenki.json#intro[удержать грунт и организовать перепад]",
            "wordstat:Yaroslavl_oblast=3|SERP-69104D6AA308",
            "Комплексное решение перепада; материал раскрывается на соседних страницах.",
        ),
        _child(
            "S6", "CONCRETE", "Бетонные подпорные стенки",
            "betonnaya-podpornaya-stenka", "устройство бетонной подпорной стенки",
            "business_source:service-v2/podpornye-stenki.json#scope[Бетонные конструкции]",
            "SERP-3CDF6B2A903F|wordstat:Yaroslavl_oblast=6",
            "Монолитный бетон; блоки и декоративная кладка разведены.",
        ),
        _child(
            "S6", "STONE", "Подпорные стенки из натурального камня",
            "podpornaya-stenka-iz-kamnya", "устройство подпорной стенки из камня",
            "business_source:service-v2/podpornye-stenki.json#scope[Натуральный и декоративный камень]",
            "wordstat:Yaroslavl_oblast=1",
            "Каменная кладка; габионы и бетон не входят.",
        ),
        _child(
            "S6", "BLOCKS", "Подпорные стенки из железобетонных блоков",
            "podpornaya-stenka-iz-zhb-blokov",
            "устройство подпорной стенки из железобетонных блоков",
            "business_source:service-v2/podpornye-stenki.json#scope[Железобетонные блоки]",
            "wordstat:Yaroslavl_oblast=1|Q000102",
            "Конструкция из ЖБ-блоков; товарные каталоги исключаются.",
        ),
        _child(
            "S6", "BRICK", "Кирпичные подпорные стенки",
            "kirpichnaya-podpornaya-stenka", "строительство подпорной стенки из кирпича",
            "business_source:service-v2/podpornye-stenki.json#scope[Кирпич]",
            "wordstat:Yaroslavl_oblast=1",
            "Кирпичная конструкция или облицовка; общий запрос остаётся хабу.",
        ),
    ),
    "S7": (
        _child(
            "S7", "DESIGN", "Проект освещения участка", "proekt-osveshcheniya-uchastka",
            "проектирование освещения участка цена",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#process[проектирование]",
            "wordstat:Yaroslavl_oblast=2",
            "Схема и проект; физический монтаж остаётся соседней услуге.",
        ),
        _child(
            "S7", "INSTALL", "Монтаж уличного освещения участка",
            "montazh-osveshcheniya-uchastka", "монтаж уличного освещения участка цена",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#process[монтаж]",
            "SERP-6979557B24CA|wordstat:Yaroslavl_oblast[устройство]=8",
            "Комплексный монтаж; отдельные сценарии света разведены.",
        ),
        _child(
            "S7", "PATHS", "Подсветка садовых дорожек и ступеней",
            "podsvetka-sadovyh-dorozhek", "монтаж подсветки садовых дорожек",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#scope[дорожки и ступени]",
            "SERP-942863B727BD|wordstat:Yaroslavl_oblast=31",
            "Монтаж дорожечного света; товарные запросы светильников исключаются.",
        ),
        _child(
            "S7", "LANDSCAPE", "Ландшафтное и декоративное освещение сада",
            "landshaftnoe-osveshchenie-uchastka", "монтаж ландшафтного освещения участка",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#scope[Декоративный свет в саду]",
            "SERP-D0ED9EC8158D|wordstat:Yaroslavl_oblast=23",
            "Сад и композиция; архитектурная подсветка дома разведена.",
        ),
        _child(
            "S7", "ARCHITECTURAL", "Архитектурная подсветка частного дома",
            "arhitekturnaya-podsvetka-doma", "монтаж архитектурной подсветки частного дома",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#scope[Архитектурная подсветка]",
            "seed_gap:архитектурная подсветка частного дома",
            "Фасад и архитектура дома; садовое освещение остаётся S7-LANDSCAPE.",
        ),
        _child(
            "S7", "SECURITY", "Функциональное и охранное освещение участка",
            "ohrannoe-osveshchenie-uchastka", "монтаж охранного освещения участка",
            "business_source:service-v2/ulichnoe-osveshhenie-uchastka.json#scope[Охранное освещение]",
            "wordstat:Yaroslavl_oblast[освещение периметра]=1",
            "Частный участок и периметр; муниципальное освещение исключается.",
        ),
    ),
    "S8": (
        _child(
            "S8", "PIPE", "Укладка водопропускной трубы в канаву",
            "truba-v-kanavu-dlya-zaezda", "установка водопропускной трубы в канаву для въезда",
            "business_source:service-v2/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch.json#scope[Водопропускная часть]",
            "SERP-854ADA9B5F75|Q000140|wordstat:Yaroslavl_oblast=25",
            "Установка трубы с сохранением стока; продажа трубы исключается.",
        ),
        _child(
            "S8", "BASE", "Устройство основания въезда на участок",
            "osnovanie-vezda-na-uchastok", "устройство основания въезда на участок цена",
            "business_source:service-v2/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch.json#scope[Основание въезда]",
            "seed_gap:устройство основания въезда на участок",
            "Основание проезда; тип финишного покрытия раскрывается отдельно.",
        ),
        _child(
            "S8", "GRAVEL", "Щебёночный въезд на участок",
            "shchebenochnyy-vezd-na-uchastok", "отсыпка въезда на участок щебнем цена",
            "business_source:service-v2/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch.json#scope[Щебёночный вариант]",
            "wordstat:Yaroslavl_oblast[щебень для заезда]=5",
            "Щебёночное исполнение; бетонный вариант разведён.",
        ),
        _child(
            "S8", "CONCRETE", "Бетонный въезд через канаву",
            "betonnyy-vezd-cherez-kanavu", "устройство бетонного въезда через канаву",
            "business_source:service-v2/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch.json#scope[Бетонный вариант]",
            "wordstat:Yaroslavl_oblast=1",
            "Бетонная конструкция; мощение остаётся у защищённого владельца.",
        ),
        _child(
            "S8", "HEADWALLS", "Устройство оголовков въезда через канаву",
            "ogolovki-vezda-cherez-kanavu", "устройство оголовков на въезд через канаву",
            "business_confirmation_required:устройство и укрепление оголовков",
            "webmaster_query:сколько стоит сделать оголовки на заезд=3_impressions",
            "Оголовки и укрепление краёв; труба и основание остаются соседним услугам.",
            offer_status="needs_business_confirmation",
        ),
        _child(
            "S8", "SLABS", "Въезд через канаву из дорожных плит",
            "vezd-cherez-kanavu-iz-dorozhnyh-plit",
            "установка дорожных плит на въезд через канаву",
            "business_confirmation_required:устройство въезда из дорожных плит",
            "SERP-28E8746F1C7F|Q000137|wordstat:Yaroslavl_oblast=1",
            "Дорожные плиты как конструкция проезда; мощение плиткой остаётся защищённому владельцу.",
            offer_status="needs_business_confirmation",
        ),
    ),
}


EXPANDED_ARTICLES: Mapping[str, tuple[ExpandedPage, ...]] = {
    "S1": (
        _article("S1", "COST", "Как рассчитать стоимость благоустройства за сотку", "kak-rasschitat-stoimost-blagoustrojstva-za-sotku", "как рассчитать стоимость благоустройства за сотку", "HOLD-505521C7EF8C|HOLD-72FBB49E67C8|Q000142", "Расчёт и факторы цены; коммерческий заказ проекта остаётся хабу."),
        _article("S1", "DIY", "Дизайн-проект участка своими руками", "dizajn-proekt-uchastka-svoimi-rukami", "дизайн проект участка своими руками", "HOLD-9CF4ABC55090|HOLD-FD41CABAE854", "DIY-процесс; профессиональная услуга остаётся хабу."),
        _article("S1", "SIX-SOTOK", "Ландшафтный дизайн участка 6 соток", "landshaftnyj-dizajn-uchastka-6-sotok", "ландшафтный дизайн участка 6 соток", "wordstat:Yaroslavl_oblast=30", "Планировочные сценарии для площади, не отдельная услуга."),
        _article("S1", "TEN-FIFTEEN", "Ландшафтный дизайн участка 10–15 соток", "landshaftnyj-dizajn-uchastka-10-i-15-sotok", "ландшафтный дизайн участка 10 соток", "wordstat:Yaroslavl_oblast=17", "Площадные сценарии; не дублирует страницу 6 соток."),
        _article("S1", "WITH-HOUSE", "Дизайн участка с домом, баней и огородом", "landshaftnyj-dizajn-uchastka-s-domom-banej-i-ogorodom", "ландшафтный дизайн участка с домом и баней", "wordstat:Yaroslavl_oblast=22+4", "Сценарии размещения объектов; проект заказывают в хабе."),
        _article("S1", "SOFTWARE", "Программы и ИИ для планировки участка", "programmy-dlya-landshaftnogo-dizajna-uchastka", "программа для ландшафтного дизайна участка", "wordstat:Yaroslavl_oblast=4", "Инструменты и ограничения; 3D-услуга остаётся коммерческой странице."),
        _article("S1", "IDEAS", "Идеи и примеры ландшафтного дизайна участка", "idei-i-primery-landshaftnogo-dizajna-uchastka", "примеры ландшафтного дизайна участка фото", "wordstat:Yaroslavl_oblast=81", "Вдохновение и разбор решений; без фиктивных кейсов компании."),
    ),
    "S2": (
        _article("S2", "ROLL-DIY", "Как укладывать рулонный газон", "kak-ukladyvat-rulonnyj-gazon", "как укладывать рулонный газон", "HOLD-182825428CBD", "DIY; услуга укладки остаётся коммерческой странице."),
        _article("S2", "SCHEME", "Устройство газона: схема слоёв и этапов", "ustrojstvo-gazona-shema", "устройство газона схема", "HOLD-15A8258BC551", "Информационная схема; расчёт работ остаётся хабу."),
        _article("S2", "PREP-ERRORS", "Ошибки при подготовке участка под газон", "oshibki-pri-podgotovke-uchastka-pod-gazon", "ошибки при подготовке участка под газон", "seed_gap:ошибки подготовки под газон", "Ошибки и профилактика; подготовка как услуга разведена."),
        _article("S2", "COMPARE", "Рулонный или посевной газон: что выбрать", "rulonnyj-ili-posevnoj-gazon", "рулонный или посевной газон что лучше", "Q000047|seed_gap:сравнение газонов", "Сравнение; отдельные варианты имеют свои коммерческие страницы."),
        _article("S2", "RESTORE", "Как восстановить испорченный газон", "kak-vosstanovit-gazon", "как восстановить газон", "SERP-63EDD3F67224|Q000039", "DIY и диагностика; платное восстановление не заявляется как факт до подтверждения."),
        _article("S2", "AFTERCARE", "Уход за газоном после укладки и посева", "uhod-za-gazonom-posle-ukladki-i-poseva", "уход за газоном после укладки и посева", "business_scope:начальный уход|seed_gap", "Только стартовый период; сезонный уход принадлежит S4."),
        _article("S2", "SEASON", "Когда сеять и укладывать газон", "kogda-seyat-i-ukladyvat-gazon", "когда сеять и укладывать газон", "seed_gap:сезонность газона", "Сроки и условия; не отдельная услуга."),
    ),
    "S3": (
        _article("S3", "NORMS", "Нормы посадки деревьев на участке", "normy-posadki-derevev", "нормы посадки деревьев на участке", "HOLD-A31AAE5725CD", "Нормы и расстояния; услуги посадки разведены по типам растений."),
        _article("S3", "FRUIT-SCHEME", "Схема посадки плодового сада", "shema-posadki-plodovogo-sada", "схема посадки плодового сада", "HOLD-1D9AC2530460|wordstat:Yaroslavl_oblast=2", "Схема плодового сада; коммерческая посадка отдельно."),
        _article("S3", "WHEN", "Когда сажать деревья и кустарники", "kogda-sazhat-derevya-i-kustarniki", "когда сажать деревья и кустарники", "seed_gap:сроки посадки", "Сезонность; не забирает запросы услуг."),
        _article("S3", "PIT", "Как подготовить посадочную яму", "kak-podgotovit-posadochnuyu-yamu", "как подготовить посадочную яму для дерева", "wordstat:Yaroslavl_oblast=5", "DIY-подготовка; подрядная посадка отдельно."),
        _article("S3", "AFTERCARE", "Полив и подвязка деревьев после посадки", "poliv-i-podvyazka-derevev-posle-posadki", "уход за деревьями после посадки", "HOLD-D5EEA7CA5259", "Первичный уход; регулярное обслуживание принадлежит S4."),
        _article("S3", "SEEDLINGS", "Как выбрать и сохранить саженцы до посадки", "kak-vybrat-i-sohranit-sazhency-do-posadki", "как сохранить саженцы до посадки", "seed_gap:хранение саженцев", "Выбор и хранение; товарные каталоги не являются целью."),
        _article("S3", "CONIFER-ERRORS", "Посадка хвойных: сроки и ошибки", "posadka-hvojnyh-oshibki-i-sroki", "ошибки при посадке хвойных деревьев", "HOLD-AF75D8A25C90", "Информационный разбор; услуга хвойной посадки отдельно."),
    ),
    "S4": (
        _article("S4", "CALENDAR", "Календарь ухода за садом", "shema-uhoda-za-sadom", "календарь ухода за садом по месяцам", "HOLD-F668FF6F6190", "Годовой обзор; сезонная услуга имеет коммерческий интент."),
        _article("S4", "PRUNING", "Схема и сроки обрезки плодовых деревьев", "obrezka-plodovyh-derevev-shema-i-sroki", "схема обрезки плодовых деревьев", "HOLD-136ED0AAB28A", "DIY-схема; заказ обрезки отдельно."),
        _article("S4", "SPRING", "Весенний уход за садом после зимы", "vesennij-uhod-za-sadom", "весенний уход за садом после зимы", "HOLD-28627278866D", "Весенний период; не повторяет годовой календарь."),
        _article("S4", "AUTUMN", "Осенний уход и подготовка сада к зиме", "podgotovka-sada-k-zime", "подготовка сада к зиме осенью", "HOLD-28627278866D", "Осень и зимовка; коммерческий сезонный комплекс отдельно."),
        _article("S4", "HYDRANGEA", "Уход за гортензией в саду", "uhod-za-gortenziej-v-sadu", "уход за гортензией в саду", "HOLD-28627278866D|wordstat:Yaroslavl_oblast=21", "Уход за конкретным растением; не отдельная услуга."),
    ),
    "S5": (
        _article("S5", "SCHEME", "Схема планировки участка: зоны и уровни", "shema-planirovki-uchastka", "схема планировки участка", "HOLD-FF3B04A53D72", "Функциональная и высотная логика; дизайн-проект принадлежит S1."),
        _article("S5", "DIY", "Выравнивание участка своими руками", "vyravnivanie-uchastka-svoimi-rukami", "выравнивание участка своими руками", "HOLD-74B3B2B18DA4", "DIY и ограничения; подрядная услуга отдельно."),
        _article("S5", "FILL", "Чем отсыпать и поднять участок", "chem-otsypat-i-podnyat-uchastok", "чем отсыпать и поднять участок", "SERP-490CDCE58295|Q000090", "Выбор материала; услуга отсыпки отдельно."),
        _article("S5", "LEVELS", "Уклоны и отметки участка до земляных работ", "uklony-i-otmetki-uchastka", "как определить уклоны и отметки участка", "HOLD-37D2E790086A", "Принцип и подготовка; проект S1 и работы S5 разведены."),
        _article("S5", "FOR-LAWN", "Выравнивание участка под газон: с чего начать", "vyravnivanie-uchastka-pod-gazon-s-chego-nachat", "как выровнять участок под газон", "SERP-13FD00FC92C7", "Инструкция; коммерческая подготовка отдельно."),
    ),
    "S6": (
        _article("S6", "DIY", "Подпорная стенка на участке своими руками", "podpornaya-stenka-na-uchastke-svoimi-rukami", "подпорная стенка на участке своими руками", "HOLD-70212404217F|Q000146", "DIY с инженерными ограничениями; подрядные страницы отдельно."),
        _article("S6", "TYPES", "Виды и материалы подпорных стенок", "vidy-i-materialy-podpornyh-stenok", "виды подпорных стенок на участке", "wordstat:Russia_discovery[варианты]=17", "Обзор выбора; страницы материалов отвечают на заказ работ."),
        _article("S6", "WATER", "Водоотвод за подпорной стенкой", "vodootvod-za-podpornoj-stenkoj", "как отвести воду от подпорной стенки", "business_scope:вода за стеной|seed_gap", "Объяснение связи; отдельные дренажные работы принадлежат защищённому URL."),
        _article("S6", "HEIGHT", "Как выбрать высоту и конструкцию подпорной стенки", "kak-vybrat-vysotu-podpornoj-stenki", "как рассчитать высоту подпорной стенки", "seed_gap:расчет подпорной стенки", "Без универсальных расчётных обещаний; требуется специалист."),
        _article("S6", "FAILURES", "Почему подпорная стенка трескается или наклоняется", "pochemu-podpornaya-stenka-treskaetsya", "почему подпорная стенка наклоняется", "seed_gap:дефекты подпорной стенки", "Диагностика признаков; не заявляет ремонт как оказываемую услугу."),
    ),
    "S7": (
        _article("S7", "DIY", "Как сделать освещение на участке", "kak-sdelat-osveschenie-na-uchastke", "как сделать освещение на участке", "HOLD-EC53FCBA2C1F|Q000152", "DIY и безопасность; монтаж как услуга отдельно."),
        _article("S7", "TYPES", "Виды освещения участка", "vidy-osveshcheniya-uchastka", "виды освещения участка", "wordstat:Yaroslavl_oblast=5", "Обзор сценариев; коммерческие сценарии разведены по страницам."),
        _article("S7", "SCHEME", "Схема освещения участка", "shema-osveshcheniya-uchastka", "схема освещения участка", "HOLD-EC53FCBA2C1F|seed_gap", "Планирование зон; проектирование как услуга отдельно."),
        _article("S7", "CABLE", "Прокладка кабеля для освещения участка", "prokladka-kabelya-dlya-osveshcheniya-uchastka", "как проложить кабель для освещения участка", "seed_gap:кабель освещения участка", "Безопасность и нормы; профессиональный монтаж отдельно."),
        _article("S7", "FIXTURES", "Как выбрать светильники для дорожек и сада", "kak-vybrat-svetilniki-dlya-dorozhek-i-sada", "как выбрать светильники для садовых дорожек", "SERP-942863B727BD", "Информационный выбор; товарные запросы не входят в коммерческое ядро."),
        _article("S7", "AUTOMATION", "Автоматизация освещения участка", "avtomatizatsiya-osveshcheniya-uchastka", "автоматизация освещения участка датчики", "seed_gap:автоматизация освещения участка", "Сценарии управления; автополив и другие защищённые услуги не затрагиваются."),
    ),
    "S8": (
        _article("S8", "DIY", "Как сделать въезд на участок через канаву", "kak-sdelat-vezd-na-uchastok-cherez-kanavu", "как сделать въезд на участок через канаву", "HOLD-BE8C4D20F9A4|Q000151", "DIY и ограничения; устройство под ключ остаётся хабу."),
        _article("S8", "PIPE", "Какую трубу выбрать для въезда на участок", "kakuyu-trubu-vybrat-dlya-vezda-na-uchastok", "какую трубу выбрать для въезда через канаву", "wordstat:Yaroslavl_oblast=11", "Выбор по условиям; продажа трубы исключается."),
        _article("S8", "WIDTH", "Ширина въезда на участок", "shirina-vezda-na-uchastok", "какая должна быть ширина въезда на участок", "wordstat:Yaroslavl_oblast=6", "Параметр планирования; не отдельная услуга."),
        _article("S8", "DIAMETER", "Как подобрать диаметр трубы под въезд", "diametr-truby-pod-vezd-na-uchastok", "какой диаметр трубы нужен для въезда через канаву", "wordstat:Yaroslavl_oblast=5", "Информационный подбор после обследования; без универсального размера."),
        _article("S8", "COMPARE", "Щебень, бетон или плиты для въезда", "shcheben-beton-ili-plity-dlya-vezda", "щебень бетон или плиты для въезда на участок", "seed_gap:сравнение конструкции въезда", "Сравнение вариантов; защищённое мощение не присваивается."),
        _article("S8", "BANKS", "Как укрепить края канавы у въезда", "kak-ukrepit-kraya-kanavy-u-vezda", "как укрепить края канавы у въезда", "webmaster_query:оголовки на заезд", "Информационная задача; услуга оголовков требует подтверждения бизнеса."),
    ),
}


# Second probes are reserved for destinations whose first SERP was too broad,
# heavily overlapped the hub, or showed an informational/product-heavy format.
TARGETED_SERP_QUERIES: tuple[tuple[str, str], ...] = (
    ("S1-CHILD-MASTERPLAN", "генеральный план участка ландшафтный дизайн цена"),
    ("S1-CHILD-RELIEF", "проект вертикальной планировки участка ландшафтный цена"),
    ("S2-CHILD-ROLL", "рулонный газон с укладкой цена ярославль"),
    ("S2-CHILD-SEED", "устройство посевного газона цена ярославль"),
    ("S2-CHILD-SOIL", "подготовка грунта под газон цена ярославль"),
    ("S2-CHILD-RESTORE", "ремонт и восстановление газона цена ярославль"),
    ("S2-CHILD-INITIAL-CARE", "обслуживание нового газона ярославль"),
    ("S6-CHILD-SLOPE", "подпорная стенка на участке с уклоном цена работы"),
    ("S6-CHILD-CONCRETE", "бетонная подпорная стенка цена работы ярославль"),
    ("S6-CHILD-STONE", "подпорная стенка из камня цена работы ярославль"),
    ("S6-CHILD-BLOCKS", "подпорная стенка из блоков цена работы ярославль"),
    ("S6-CHILD-BRICK", "подпорная стенка из кирпича цена работы ярославль"),
    ("S7-CHILD-DESIGN", "проект освещения участка цена ярославль"),
    ("S7-CHILD-PATHS", "монтаж подсветки садовых дорожек цена ярославль"),
    ("S7-CHILD-LANDSCAPE", "монтаж ландшафтного освещения цена ярославль"),
    ("S7-CHILD-ARCHITECTURAL", "архитектурная подсветка дома монтаж ярославль"),
    ("S7-CHILD-SECURITY", "охранное освещение участка монтаж ярославль"),
    ("S8-CHILD-PIPE", "труба в канаву для въезда установка цена ярославль"),
    ("S8-CHILD-BASE", "основание въезда на участок устройство ярославль"),
    ("S8-CHILD-GRAVEL", "щебеночный въезд на участок под ключ ярославль"),
    ("S8-CHILD-CONCRETE", "бетонный въезд через канаву цена ярославль"),
    ("S8-CHILD-HEADWALLS", "оголовки въезда через канаву цена ярославль"),
    ("S8-CHILD-SLABS", "въезд через канаву из дорожных плит цена ярославль"),
)


def all_expanded_pages() -> tuple[ExpandedPage, ...]:
    """Return a stable service-id, role and declaration ordered page sequence."""
    return tuple(
        page
        for service_id in SERVICE_IDS
        for group in (EXPANDED_CHILDREN[service_id], EXPANDED_ARTICLES[service_id])
        for page in group
    )


def validate_expanded_registry(
    children: Mapping[str, Sequence[ExpandedPage]] = EXPANDED_CHILDREN,
    articles: Mapping[str, Sequence[ExpandedPage]] = EXPANDED_ARTICLES,
) -> list[str]:
    """Fail closed on sparse, ambiguous, unsafe or untraceable destinations."""
    errors: list[str] = []
    expected_services = set(SERVICE_IDS)
    if set(children) != expected_services:
        errors.append("children must define exactly S1-S8")
    if set(articles) != expected_services:
        errors.append("articles must define exactly S1-S8")
    pages = [page for group in (*children.values(), *articles.values()) for page in group]
    destination_ids: set[str] = set()
    slugs: set[str] = set()
    queries: set[str] = set()
    for service_id in SERVICE_IDS:
        child_count = len(children.get(service_id, ()))
        article_count = len(articles.get(service_id, ()))
        if not 5 <= child_count <= 6:
            errors.append(f"{service_id} must have 5-6 commercial children, found {child_count}")
        if not 5 <= article_count <= 7:
            errors.append(f"{service_id} must have 5-7 articles, found {article_count}")
    for page in pages:
        prefix = f"{page.service_id}-{'CHILD' if page.page_role == 'child_service' else 'ARTICLE'}-"
        if page.service_id not in expected_services or not page.destination_id.startswith(prefix):
            errors.append(f"invalid destination identity: {page.destination_id}")
        if page.page_role not in {"child_service", "article"}:
            errors.append(f"invalid page role: {page.destination_id}")
        if page.destination_id in destination_ids:
            errors.append(f"duplicate destination id: {page.destination_id}")
        destination_ids.add(page.destination_id)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", page.slug):
            errors.append(f"invalid slug: {page.destination_id}")
        if page.slug in slugs:
            errors.append(f"duplicate slug: {page.slug}")
        slugs.add(page.slug)
        normalized_query = " ".join(page.representative_query.casefold().split())
        if not normalized_query:
            errors.append(f"blank representative query: {page.destination_id}")
        elif normalized_query in queries:
            errors.append(f"duplicate representative query: {normalized_query}")
        queries.add(normalized_query)
        if not all((page.title, page.business_evidence, page.semantic_evidence, page.boundary)):
            errors.append(f"incomplete evidence or boundary: {page.destination_id}")
        if page.offer_status not in OFFER_STATUSES:
            errors.append(f"invalid offer status: {page.destination_id}")
        if page.page_role == "child_service":
            if page.offer_status == "not_applicable":
                errors.append(f"child has non-commercial offer status: {page.destination_id}")
            if page.offer_status == "confirmed" and not page.business_evidence.startswith(
                "business_source:"
            ):
                errors.append(f"confirmed child has no business source: {page.destination_id}")
            if page.offer_status == "needs_business_confirmation" and not page.business_evidence.startswith(
                "business_confirmation_required:"
            ):
                errors.append(f"unconfirmed child has no confirmation gate: {page.destination_id}")
            if page.slug in PROTECTED_SLUGS or normalized_query in PROTECTED_QUERY_OWNERS:
                errors.append(f"child claims a protected owner: {page.destination_id}")
        elif page.offer_status != "not_applicable":
            errors.append(f"article has commercial offer status: {page.destination_id}")
    return sorted(set(errors))


def build_expanded_serp_queue(
    *,
    start_query_number: int,
    region: str = "Yaroslavl",
    device: str = "desktop",
) -> list[dict[str, str]]:
    """Build one current representative SERP probe per proposed destination."""
    errors = validate_expanded_registry()
    if errors:
        raise ValueError("; ".join(errors))
    if start_query_number < 1:
        raise ValueError("start_query_number must be positive")
    rows: list[dict[str, str]] = []
    for offset, page in enumerate(all_expanded_pages()):
        rows.append(
            {
                "query_id": f"Q{start_query_number + offset:06d}",
                "query": page.representative_query,
                "service_id": page.service_id,
                "intent": "transactional" if page.page_role == "child_service" else "informational",
                "region": region,
                "device": device,
                "destination_id": page.destination_id,
                "reason": f"expanded_representative[{page.destination_id}]",
            }
        )
    return rows


def write_expanded_serp_queue(
    output: Path,
    *,
    start_query_number: int,
    region: str = "Yaroslavl",
    device: str = "desktop",
) -> int:
    """Write a UTF-8 queue accepted by the guarded Yandex Search collector."""
    rows = build_expanded_serp_queue(
        start_query_number=start_query_number,
        region=region,
        device=device,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_targeted_serp_queue(
    *,
    start_query_number: int,
    region: str = "Yaroslavl",
    device: str = "desktop",
) -> list[dict[str, str]]:
    """Build the bounded second-probe queue for ambiguous commercial pages."""
    errors = validate_expanded_registry()
    if errors:
        raise ValueError("; ".join(errors))
    if start_query_number < 1:
        raise ValueError("start_query_number must be positive")
    page_by_id = {page.destination_id: page for page in all_expanded_pages()}
    queries: set[str] = set()
    rows: list[dict[str, str]] = []
    for offset, (destination_id, query) in enumerate(TARGETED_SERP_QUERIES):
        page = page_by_id.get(destination_id)
        if page is None or page.page_role != "child_service":
            raise ValueError(f"targeted SERP destination is not a child: {destination_id}")
        normalized = " ".join(query.casefold().split())
        if not normalized or normalized in queries:
            raise ValueError(f"duplicate or blank targeted SERP query: {query!r}")
        queries.add(normalized)
        rows.append(
            {
                "query_id": f"Q{start_query_number + offset:06d}",
                "query": query,
                "service_id": page.service_id,
                "intent": "transactional",
                "region": region,
                "device": device,
                "destination_id": destination_id,
                "reason": f"expanded_second_probe[{destination_id}]",
            }
        )
    return rows


def write_targeted_serp_queue(
    output: Path,
    *,
    start_query_number: int,
    region: str = "Yaroslavl",
    device: str = "desktop",
) -> int:
    """Write the targeted second-probe queue as UTF-8 CSV."""
    rows = build_targeted_serp_queue(
        start_query_number=start_query_number,
        region=region,
        device=device,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
