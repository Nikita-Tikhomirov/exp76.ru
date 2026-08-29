"""Offline, fail-closed S9-S15 architecture for all remaining legacy services.

The registry preserves the seven live WordPress owners and limits children to
the 29 capabilities proven in ``legacy_service_scope_audit.md``.  Suggest rows
are collection instructions, not collected Wordstat or SERP evidence.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

from .yandex_suggest import MAX_REQUESTS, QUEUE_COLUMNS as SUGGEST_QUEUE_COLUMNS


SITE_ROOT = "https://exp76.ru"
LEGACY_SERVICE_ORDER = tuple(f"S{number}" for number in range(9, 16))
SUGGEST_REGION_ID = 10841
SUGGEST_FIRST_QUERY_NUMBER = 1001
PROTECTED_PRIMARY_INTENTS = (
    "автополив",
    "дренаж участка",
    "ливневая канализация",
    "осушение участка",
    "отмостка",
    "тротуарная плитка",
    "мощение участка",
)


@dataclass(frozen=True)
class LegacyDestination:
    destination_id: str
    service_id: str
    page_role: str
    title: str
    slug: str
    representative_query: str
    parent_destination_id: str
    owner_wp_id: int
    owner_current_url: str
    current_wp_id: int | None
    current_url: str
    target_url: str
    url_action: str
    current_post_type: str
    target_template: str
    business_evidence: str
    included_intent: str
    excluded_primary_intents: tuple[str, ...]

    @property
    def boundary(self) -> str:
        return (
            f"Включено: {self.included_intent}. Исключённые основные интенты: "
            f"{', '.join(self.excluded_primary_intents)}."
        )


@dataclass(frozen=True)
class _OwnerSpec:
    wp_id: int
    current_url: str
    title: str
    query: str
    evidence_fragment: str
    included_intent: str
    excluded_intents: tuple[str, ...]

    @property
    def slug(self) -> str:
        return self.current_url.rstrip("/").rsplit("/", 1)[-1]


@dataclass(frozen=True)
class _ChildSpec:
    key: str
    title: str
    slug: str
    query: str
    evidence_fragment: str
    included_intent: str


S9_EXCLUDED = (
    "обрезка деревьев",
    "обрезка кустарников",
    "выравнивание и планировка участка",
    "неподтверждённые вывоз и утилизация",
    "аренда спецтехники без работ",
)
S10_EXCLUDED = (
    "дренаж участка",
    "ливневая канализация",
    "автополив",
    "очистка существующих запущенных прудов",
    "строительство капитальных бассейнов",
    "инженерные городские фонтаны",
)
S11_EXCLUDED = (
    "автополив",
    "внутреннее промышленное увлажнение",
    "гарантированный агрономический результат",
    "гарантированное снижение температуры на 15 градусов",
)
S12_EXCLUDED = (
    "винтовые сваи",
    "буронабивные сваи",
    "неподтверждённые ростверк и геология",
    "раздельная публикация object-variants без SERP overlap-check",
)
S13_EXCLUDED = (
    "гараж и парковочная площадка",
    "капитальная пристройка",
    "печной комплекс",
    "неподтверждённые сроки, бренды и гарантии",
)
S14_EXCLUDED = (
    "продажа готового печного оборудования",
    "котлы и отопительное оборудование",
    "продажа переносных мангалов",
    "металлический навес",
    "неподтверждённые технические и гарантийные обещания",
)
S15_EXCLUDED = (
    "промышленный и высотный снос",
    "исторические объекты",
    "общий вывоз бытового мусора",
    "неподтверждённые разрешения, режим 24/7 и любой масштаб",
)


_OWNER_SPECS: Mapping[str, _OwnerSpec] = MappingProxyType(
    {
        "S9": _OwnerSpec(
            6870,
            f"{SITE_ROOT}/services/vykorchevyvanie-pnejj-spil-derevev/",
            "Расчистка участка, спил и корчевание",
            "спил деревьев и корчевание пней ярославль",
            "obrezka-i-spil-derevev-i-kustarnikov+vykorchevyvanie-pnej",
            "удаление деревьев, корчевание пней и расчистка древесно-кустарниковой растительности",
            S9_EXCLUDED,
        ),
        "S10": _OwnerSpec(
            6900,
            f"{SITE_ROOT}/services/sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev/",
            "Пруды, водоёмы и водные объекты",
            "пруд и водные объекты на участке ярославль",
            "bassejny+prudy-i-ozera+fontany+ruchji+vodopady",
            "создание перечисленных live-страницей частных ландшафтных водных объектов",
            S10_EXCLUDED,
        ),
        "S11": _OwnerSpec(
            6922,
            f"{SITE_ROOT}/services/sistemy-tumanoobrazovaniya/",
            "Системы туманообразования",
            "система туманообразования монтаж ярославль",
            "chastnye-uchastki+otkrytye-ploshhadki+restorany+oranzherei-i-teplicy",
            "монтаж систем высокого давления для подтверждённых частных, коммерческих и тепличных сценариев",
            S11_EXCLUDED,
        ),
        "S12": _OwnerSpec(
            9138,
            f"{SITE_ROOT}/services/fundament-na-zhelezobetonnykh-svajakh/",
            "Фундамент на железобетонных сваях",
            "фундамент на железобетонных сваях ярославль",
            "zabivnye-zhb-svai+betonnye-sterzhni-kvadratnogo-sechenija",
            "устройство фундамента на заявленных забивных железобетонных сваях без неподтверждённых конструктивных обещаний",
            S12_EXCLUDED,
        ),
        "S13": _OwnerSpec(
            9312,
            f"{SITE_ROOT}/services/navesy-iz-metalla/",
            "Навесы из металла",
            "изготовление и монтаж навесов из металла ярославль",
            "proektirovanie+izgotovlenie+montazh-legkih-metallokonstrukcij",
            "проектирование, изготовление и монтаж перечисленных live-страницей лёгких металлических навесов",
            S13_EXCLUDED,
        ),
        "S14": _OwnerSpec(
            9775,
            f"{SITE_ROOT}/services/kaminy-pechi-barbekju/",
            "Камины, печи и барбекю",
            "строительство каминов печей и барбекю ярославль",
            "kaminy+otopitelnye-pechi+barbekju-kompleksy+mangaly",
            "кладка заявленных каминов, отопительных печей и стационарных уличных печных комплексов",
            S14_EXCLUDED,
        ),
        "S15": _OwnerSpec(
            9838,
            f"{SITE_ROOT}/services/snos-i-demontazh-zdanijj-domov/",
            "Снос и демонтаж",
            "снос и демонтаж зданий ярославль",
            "ruchnoj-i-mehanizirovannyj-razbor+pogruzka-i-vyvoz",
            "ручной и механизированный демонтаж в подтверждённом масштабе с относящимся к нему вывозом",
            S15_EXCLUDED,
        ),
    }
)


_CHILD_SPECS: Mapping[str, tuple[_ChildSpec, ...]] = MappingProxyType(
    {
        "S9": (
            _ChildSpec(
                "TREE-REMOVAL",
                "Спил и удаление деревьев",
                "spil-i-udalenie-derevev",
                "спил деревьев ярославль",
                "spil-derevev",
                "спил и удаление дерева целиком или по частям",
            ),
            _ChildSpec(
                "STUMPS",
                "Корчевание пней",
                "korchevanie-pnej",
                "корчевание пней ярославль",
                "vykorchevyvanie-pnej",
                "корчевание и удаление пней",
            ),
            _ChildSpec(
                "CLEARING",
                "Расчистка участка от деревьев и кустарников",
                "raschistka-uchastka-ot-derevev-i-kustarnikov",
                "расчистка участка от деревьев и кустарников ярославль",
                "spil-derevev-i-kustarnikov+vykorchevyvanie-pnej",
                "расчистка древесной и кустарниковой растительности",
            ),
        ),
        "S10": (
            _ChildSpec(
                "DECORATIVE-POND",
                "Декоративный пруд на участке",
                "dekorativnyj-prud-na-uchastke",
                "декоративный пруд под ключ ярославль",
                "prudy-i-ozera",
                "создание декоративного водоёма на частном участке",
            ),
            _ChildSpec(
                "SWIMMING-POND",
                "Плавательный пруд",
                "plavatelnyj-prud-na-uchastke",
                "плавательный пруд на участке ярославль",
                "bassejny+prudy+filtracija",
                "создание купального пруда с фильтрацией",
            ),
            _ChildSpec(
                "WATERFALL-CASCADE",
                "Водопад и каскад на участке",
                "vodopad-i-kaskad-na-uchastke",
                "искусственный водопад на участке ярославль",
                "vodopady",
                "искусственный водопад или каскад как частный ландшафтный объект",
            ),
            _ChildSpec(
                "STREAM",
                "Декоративный ручей",
                "dekorativnyj-ruchej-na-uchastke",
                "декоративный ручей на участке ярославль",
                "ruchji",
                "создание искусственного декоративного ручья",
            ),
            _ChildSpec(
                "FOUNTAIN",
                "Фонтан на участке",
                "fontan-na-uchastke",
                "фонтан под ключ на участке ярославль",
                "fontany",
                "создание частного ландшафтного фонтана",
            ),
        ),
        "S11": (
            _ChildSpec(
                "TERRACE-VERANDA",
                "Туманообразование для террасы и веранды",
                "tumanoobrazovanie-dlya-terrasy-i-verandy",
                "система туманообразования для террасы ярославль",
                "chastnye-territorii+otkrytye-ploshhadki",
                "монтаж туманообразования в частной открытой зоне отдыха",
            ),
            _ChildSpec(
                "CAFE-OUTDOOR",
                "Туманообразование для кафе и открытых площадок",
                "tumanoobrazovanie-dlya-kafe-i-letnih-ploshchadok",
                "система туманообразования для кафе ярославль",
                "kafe-restorany+otkrytye-ploshhadki",
                "монтаж туманообразования на летней коммерческой площадке",
            ),
            _ChildSpec(
                "GREENHOUSE",
                "Туманообразование для теплиц и оранжерей",
                "tumanoobrazovanie-dlya-teplic-i-oranzherej",
                "система туманообразования для теплицы ярославль",
                "oranzherei-i-teplicy",
                "монтаж туманообразования для микроклимата растений",
            ),
        ),
        "S12": (
            _ChildSpec(
                "DRIVING",
                "Забивка и монтаж железобетонных свай",
                "zabivka-zhelezobetonnyh-svaj",
                "забивка железобетонных свай ярославль",
                "zabivnye-zhb-svai+kvadratnoe-sechenie",
                "забивка и монтаж железобетонных свай",
            ),
            _ChildSpec(
                "PRIVATE-HOUSE",
                "Фундамент на ЖБ сваях для частного дома",
                "fundament-na-zhb-svayah-dlya-chastnogo-doma",
                "фундамент на железобетонных сваях для частного дома ярославль",
                "generic-fundament-na-zhelezobetonnykh-svajakh",
                "фундамент на железобетонных сваях для частного дома",
            ),
            _ChildSpec(
                "BATHHOUSE",
                "Фундамент на ЖБ сваях для бани",
                "fundament-na-zhb-svayah-dlya-bani",
                "фундамент на железобетонных сваях для бани ярославль",
                "generic-fundament-na-zhelezobetonnykh-svajakh",
                "фундамент на железобетонных сваях для бани",
            ),
        ),
        "S13": (
            _ChildSpec(
                "CARPORT",
                "Навес для автомобиля",
                "naves-dlya-avtomobilya",
                "навес для автомобиля ярославль с установкой",
                "navesy-dlja-avtomobilja",
                "изготовление и монтаж металлического навеса для автомобиля",
            ),
            _ChildSpec(
                "TERRACE",
                "Навес для террасы и веранды",
                "naves-dlya-terrasy-i-verandy",
                "навес для террасы ярославль с установкой",
                "verandy-terrasy+dachnye-navesy",
                "изготовление и монтаж навеса для террасы или веранды",
            ),
            _ChildSpec(
                "BARBECUE",
                "Навес для зоны барбекю",
                "naves-dlya-zony-barbekyu",
                "навес для зоны барбекю ярославль",
                "navesy-dlja-barbekju",
                "изготовление и монтаж навеса над зоной барбекю",
            ),
            _ChildSpec(
                "POLYCARBONATE-HOME",
                "Навес из поликарбоната к дому",
                "naves-iz-polikarbonata-k-domu",
                "навес из поликарбоната к дому ярославль",
                "pristrojki-iz-polikarbonata",
                "изготовление лёгкого навеса из поликарбоната к дому",
            ),
        ),
        "S14": (
            _ChildSpec(
                "FIREPLACE",
                "Строительство камина",
                "stroitelstvo-kamina",
                "строительство камина ярославль",
                "kaminy",
                "строительство кладочного камина",
            ),
            _ChildSpec(
                "HEATING-STOVE",
                "Кладка отопительной печи",
                "kladka-otopitelnoj-pechi",
                "кладка отопительной печи ярославль",
                "otopitelnye-pechi",
                "кладка отопительной печи",
            ),
            _ChildSpec(
                "BARBECUE",
                "Барбекю-комплекс под ключ",
                "barbekyu-kompleks-pod-klyuch",
                "барбекю комплекс под ключ ярославль",
                "barbekju-kompleksy+grili",
                "строительство стационарного барбекю-комплекса",
            ),
            _ChildSpec(
                "BRICK-GRILL",
                "Кирпичный мангал",
                "kirpichnyj-mangal",
                "кладка кирпичного мангала ярославль",
                "mangaly+kirpichnaja-kladka",
                "кладка стационарного кирпичного мангала",
            ),
            _ChildSpec(
                "CAULDRON-SMOKEHOUSE",
                "Печь с казаном и коптильней",
                "pech-s-kazanom-i-koptilnej",
                "печь с казаном и коптильней ярославль",
                "pech-pod-kazan+koptilnja",
                "индивидуальная комплектация печного комплекса, не магазин оборудования",
            ),
        ),
        "S15": (
            _ChildSpec(
                "PRIVATE-HOUSE",
                "Снос частного дома",
                "snos-chastnogo-doma",
                "снос частного дома ярославль цена",
                "snos-domov",
                "снос частного жилого или дачного дома",
            ),
            _ChildSpec(
                "COUNTRY-HOUSE",
                "Демонтаж дачного дома и строений",
                "demontazh-dachnogo-doma",
                "демонтаж дачного дома с вывозом ярославль",
                "zdanija-i-sooruzhenija+dachnye-doma",
                "демонтаж небольшого дачного дома и строений",
            ),
            _ChildSpec(
                "DANGEROUS-BUILDING",
                "Демонтаж аварийных зданий",
                "demontazh-avarijnyh-zdanij",
                "снос аварийных зданий ярославль",
                "avarijnye-obekty",
                "демонтаж аварийного здания в допустимом масштабе",
            ),
            _ChildSpec(
                "MANUAL",
                "Ручная разборка зданий",
                "ruchnaya-razborka-zdanij",
                "ручная разборка зданий ярославль",
                "ruchnoj-razbor",
                "ручная разборка здания при ограниченном доступе",
            ),
            _ChildSpec(
                "MECHANIZED",
                "Механизированный снос зданий",
                "mehanizirovannyj-snos-zdanij",
                "механизированный снос зданий ярославль",
                "mehanizirovannyj-razbor+spec-tehnika",
                "только доступная компании техника и допустимый масштаб",
            ),
            _ChildSpec(
                "DEBRIS",
                "Вывоз строительного мусора после сноса",
                "vyvoz-stroitelnogo-musora-posle-snosa",
                "вывоз строительного мусора после сноса ярославль",
                "sortirovka+pogruzka+vyvoz",
                "только как часть или результат демонтажа, не общий вывоз любого мусора",
            ),
        ),
    }
)


def _business_evidence(wp_id: int, fragment: str) -> str:
    return f"business_source:wp-rest/pages/{wp_id}#content[{fragment}]"


def _hub(service_id: str) -> LegacyDestination:
    spec = _OWNER_SPECS[service_id]
    return LegacyDestination(
        destination_id=f"{service_id}-HUB",
        service_id=service_id,
        page_role="hub",
        title=spec.title,
        slug=spec.slug,
        representative_query=spec.query,
        parent_destination_id="",
        owner_wp_id=spec.wp_id,
        owner_current_url=spec.current_url,
        current_wp_id=spec.wp_id,
        current_url=spec.current_url,
        target_url=spec.current_url,
        url_action="reuse",
        current_post_type="page",
        target_template="servicepost.php",
        business_evidence=_business_evidence(spec.wp_id, spec.evidence_fragment),
        included_intent=spec.included_intent,
        excluded_primary_intents=spec.excluded_intents,
    )


LEGACY_HUB_OWNERS: Mapping[str, LegacyDestination] = MappingProxyType(
    {service_id: _hub(service_id) for service_id in LEGACY_SERVICE_ORDER}
)


def _child(service_id: str, spec: _ChildSpec) -> LegacyDestination:
    owner = LEGACY_HUB_OWNERS[service_id]
    return LegacyDestination(
        destination_id=f"{service_id}-CHILD-{spec.key}",
        service_id=service_id,
        page_role="child_service",
        title=spec.title,
        slug=spec.slug,
        representative_query=spec.query,
        parent_destination_id=f"{service_id}-HUB",
        owner_wp_id=owner.owner_wp_id,
        owner_current_url=owner.owner_current_url,
        current_wp_id=None,
        current_url="",
        target_url=f"{SITE_ROOT}/{spec.slug}/",
        url_action="create",
        current_post_type="",
        target_template="newservicepost.php",
        business_evidence=_business_evidence(owner.owner_wp_id, spec.evidence_fragment),
        included_intent=spec.included_intent,
        excluded_primary_intents=_OWNER_SPECS[service_id].excluded_intents,
    )


LEGACY_CHILDREN: Mapping[str, tuple[LegacyDestination, ...]] = MappingProxyType(
    {
        service_id: tuple(_child(service_id, spec) for spec in _CHILD_SPECS[service_id])
        for service_id in LEGACY_SERVICE_ORDER
    }
)
EXPECTED_CHILD_COUNTS: Mapping[str, int] = MappingProxyType(
    {service_id: len(LEGACY_CHILDREN[service_id]) for service_id in LEGACY_SERVICE_ORDER}
)


def all_legacy_children() -> tuple[LegacyDestination, ...]:
    return tuple(
        child
        for service_id in LEGACY_SERVICE_ORDER
        for child in LEGACY_CHILDREN[service_id]
    )


def all_legacy_destinations() -> tuple[LegacyDestination, ...]:
    return tuple(
        page
        for service_id in LEGACY_SERVICE_ORDER
        for page in (LEGACY_HUB_OWNERS[service_id], *LEGACY_CHILDREN[service_id])
    )


def _normalized(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def validate_legacy_architecture(
    hubs: Mapping[str, LegacyDestination] = LEGACY_HUB_OWNERS,
    children: Mapping[str, Sequence[LegacyDestination]] = LEGACY_CHILDREN,
) -> list[str]:
    """Reject owner drift, invented pages, collisions and protected owners."""

    errors: list[str] = []
    expected_services = set(LEGACY_SERVICE_ORDER)
    if set(hubs) != expected_services:
        errors.append("hubs must define exactly S9-S15")
    if set(children) != expected_services:
        errors.append("children must define exactly S9-S15")
    pages: list[LegacyDestination] = []
    for service_id in LEGACY_SERVICE_ORDER:
        owner = hubs.get(service_id)
        spec = _OWNER_SPECS[service_id]
        if owner is None:
            continue
        if not (
            owner.destination_id == f"{service_id}-HUB"
            and owner.service_id == service_id
            and owner.page_role == "hub"
            and owner.current_wp_id == spec.wp_id
            and owner.owner_wp_id == spec.wp_id
            and owner.current_url == spec.current_url
            and owner.owner_current_url == spec.current_url
            and owner.target_url == spec.current_url
            and owner.url_action == "reuse"
            and owner.current_post_type == "page"
            and owner.target_template == "servicepost.php"
            and not owner.parent_destination_id
        ):
            errors.append(f"exact live owner differs: {service_id}")
        pages.append(owner)
        service_children = tuple(children.get(service_id, ()))
        expected_child_specs = _CHILD_SPECS[service_id]
        if not 3 <= len(service_children) <= 6:
            errors.append(
                f"{service_id} must have 3-6 commercial children, found {len(service_children)}"
            )
        if {item.slug for item in service_children} != {
            item.slug for item in expected_child_specs
        }:
            errors.append(f"proven child coverage differs: {service_id}")
        expected_children = {
            item.slug: item for item in LEGACY_CHILDREN[service_id]
        }
        for child in service_children:
            if child != expected_children.get(child.slug):
                errors.append(
                    f"proven child definition differs: {child.destination_id}"
                )
            if not (
                child.service_id == service_id
                and child.page_role == "child_service"
                and child.parent_destination_id == f"{service_id}-HUB"
            ):
                errors.append(f"invalid child ownership: {child.destination_id}")
            if not (
                child.current_wp_id is None
                and not child.current_url
                and child.url_action == "create"
                and not child.current_post_type
                and child.target_template == "newservicepost.php"
            ):
                errors.append(f"invalid child URL action: {child.destination_id}")
            if (
                child.owner_wp_id != spec.wp_id
                or child.owner_current_url != spec.current_url
            ):
                errors.append(f"child live owner differs: {child.destination_id}")
            if child.target_url != f"{SITE_ROOT}/{child.slug}/":
                errors.append(f"invalid child target URL: {child.destination_id}")
            pages.append(child)

    destination_ids: set[str] = set()
    slugs: set[str] = set()
    target_urls: set[str] = set()
    queries: set[str] = set()
    for page in pages:
        if page.page_role == "hub":
            identity_is_valid = page.destination_id == f"{page.service_id}-HUB"
        else:
            identity_is_valid = page.destination_id.startswith(
                f"{page.service_id}-CHILD-"
            )
        if page.service_id not in expected_services or not identity_is_valid:
            errors.append(f"invalid destination identity: {page.destination_id}")
        if page.destination_id in destination_ids:
            errors.append(f"duplicate destination id: {page.destination_id}")
        destination_ids.add(page.destination_id)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", page.slug):
            errors.append(f"invalid slug: {page.destination_id}")
        if page.slug in slugs:
            errors.append(f"duplicate slug: {page.slug}")
        slugs.add(page.slug)
        if page.target_url in target_urls:
            errors.append(f"duplicate target URL: {page.target_url}")
        target_urls.add(page.target_url)
        normalized_query = _normalized(page.representative_query)
        if not normalized_query or normalized_query in queries:
            errors.append(f"blank or duplicate query: {page.destination_id}")
        queries.add(normalized_query)
        if not all(
            (
                page.title.strip(),
                page.business_evidence.strip(),
                page.included_intent.strip(),
                page.excluded_primary_intents,
            )
        ):
            errors.append(f"incomplete evidence or boundary: {page.destination_id}")
        if not page.business_evidence.startswith(
            f"business_source:wp-rest/pages/{page.owner_wp_id}#content["
        ):
            errors.append(f"business evidence owner differs: {page.destination_id}")
        searchable = _normalized(
            f"{page.title} {page.slug.replace('-', ' ')} "
            f"{page.representative_query} {page.included_intent}"
        )
        for protected in PROTECTED_PRIMARY_INTENTS:
            if _normalized(protected) in searchable:
                errors.append(f"claims protected owner: {page.destination_id}:{protected}")
        if page.service_id == "S9" and not {
            "обрезка деревьев",
            "обрезка кустарников",
        }.issubset(set(page.excluded_primary_intents)):
            errors.append(f"S9 pruning boundary is incomplete: {page.destination_id}")
        if page.service_id == "S12" and "винтовые сваи" not in page.excluded_primary_intents:
            errors.append(f"S12 screw-pile boundary is incomplete: {page.destination_id}")
    return sorted(set(errors))


def build_legacy_suggest_queue() -> list[dict[str, str]]:
    """Build two free Suggest probes per hub and proven child (72 total)."""

    errors = validate_legacy_architecture()
    if errors:
        raise ValueError("; ".join(errors))
    rows: list[dict[str, str]] = []
    query_number = SUGGEST_FIRST_QUERY_NUMBER
    for page in all_legacy_destinations():
        for seed, kind in (
            (page.title.casefold(), "root"),
            (page.representative_query, "transactional"),
        ):
            rows.append(
                {
                    "query_id": f"YS{query_number:06d}",
                    "seed": seed,
                    "service_id": page.service_id,
                    "destination_id": page.destination_id,
                    "page_role": page.page_role,
                    "region_id": str(SUGGEST_REGION_ID),
                    "reason": f"legacy_suggest_{kind}[{page.destination_id}]",
                }
            )
            query_number += 1
    _validate_legacy_suggest_queue(rows)
    return rows


def _validate_legacy_suggest_queue(rows: Sequence[Mapping[str, str]]) -> None:
    if not rows or len(rows) > MAX_REQUESTS:
        raise ValueError(f"legacy suggest queue must contain 1-{MAX_REQUESTS} rows")
    expected_destinations = {page.destination_id for page in all_legacy_destinations()}
    destination_counts = {destination_id: 0 for destination_id in expected_destinations}
    seen_ids: set[str] = set()
    seen_seeds: set[str] = set()
    for row in rows:
        if tuple(row) != SUGGEST_QUEUE_COLUMNS:
            raise ValueError("legacy suggest queue columns differ")
        query_id = row["query_id"]
        if not re.fullmatch(r"YS\d{6}", query_id) or query_id in seen_ids:
            raise ValueError(f"invalid or duplicate suggest query id: {query_id!r}")
        seen_ids.add(query_id)
        if not all(row[field].strip() for field in SUGGEST_QUEUE_COLUMNS):
            raise ValueError(f"blank legacy suggest queue field: {query_id}")
        if row["region_id"] != str(SUGGEST_REGION_ID):
            raise ValueError(f"legacy suggest region differs: {query_id}")
        destination_id = row["destination_id"]
        if destination_id not in expected_destinations:
            raise ValueError(f"unknown legacy suggest destination: {destination_id}")
        destination_counts[destination_id] += 1
        normalized_seed = _normalized(row["seed"])
        if normalized_seed in seen_seeds:
            raise ValueError(f"duplicate legacy suggest seed: {row['seed']!r}")
        seen_seeds.add(normalized_seed)
    if set(destination_counts.values()) != {2}:
        raise ValueError("legacy suggest queue must contain two probes per destination")


CSV_COLUMNS = (
    "destination_id",
    "service_id",
    "page_role",
    "title",
    "slug",
    "query",
    "parent_hub",
    "owner_wp_id",
    "owner_current_url",
    "current_url",
    "target_url",
    "url_action",
    "current_wp_id",
    "current_post_type",
    "target_template",
    "business_evidence",
    "semantic_evidence",
    "included_intent",
    "excluded_primary_intents",
    "boundary",
    "publication_status",
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _REPOSITORY_ROOT / "seo-data" / "2026-08-exp76-services"
DEFAULT_CSV_PATH = _DATA_ROOT / "processed" / "legacy_service_architecture.csv"
DEFAULT_MARKDOWN_PATH = _DATA_ROOT / "reviews" / "legacy_service_structure.md"
DEFAULT_SUGGEST_QUEUE_PATH = _DATA_ROOT / "raw" / "legacy-suggest-v2" / "queue.csv"
_QUEUE_EVIDENCE_PATH = "seo-data/2026-08-exp76-services/raw/legacy-suggest-v2/queue.csv"


def _semantic_evidence_by_destination() -> dict[str, str]:
    refs: dict[str, list[str]] = {}
    for row in build_legacy_suggest_queue():
        refs.setdefault(row["destination_id"], []).append(row["query_id"])
    return {
        destination_id: (
            f"suggest_queue:{_QUEUE_EVIDENCE_PATH}#{'|'.join(query_ids)};"
            "status=queued_not_collected"
        )
        for destination_id, query_ids in refs.items()
    }


def build_legacy_service_rows() -> list[dict[str, str]]:
    errors = validate_legacy_architecture()
    if errors:
        raise ValueError("; ".join(errors))
    evidence_refs = _semantic_evidence_by_destination()
    return [
        {
            "destination_id": page.destination_id,
            "service_id": page.service_id,
            "page_role": page.page_role,
            "title": page.title,
            "slug": page.slug,
            "query": page.representative_query,
            "parent_hub": page.parent_destination_id,
            "owner_wp_id": str(page.owner_wp_id),
            "owner_current_url": page.owner_current_url,
            "current_url": page.current_url,
            "target_url": page.target_url,
            "url_action": page.url_action,
            "current_wp_id": "" if page.current_wp_id is None else str(page.current_wp_id),
            "current_post_type": page.current_post_type,
            "target_template": page.target_template,
            "business_evidence": page.business_evidence,
            "semantic_evidence": evidence_refs[page.destination_id],
            "included_intent": page.included_intent,
            "excluded_primary_intents": "|".join(page.excluded_primary_intents),
            "boundary": page.boundary,
            "publication_status": "semantic_collection_queued",
        }
        for page in all_legacy_destinations()
    ]


def render_legacy_service_structure() -> str:
    build_legacy_service_rows()
    lines = [
        "# Legacy-услуги, переводимые в полноценные SEO-хабы",
        "",
        "Источник capability: `reviews/legacy_service_scope_audit.md`. Все семь live URL и WP ID сохраняются.",
        "Yandex Suggest пока только поставлен в очередь; Wordstat и SERP этим файлом не заявляются.",
        "",
        "Всего legacy-хабов: **7**.",
        "Всего дочерних услуг: **29**.",
        "Всего семантических проб в очереди: **72**.",
        "",
    ]
    for service_id in LEGACY_SERVICE_ORDER:
        hub = LEGACY_HUB_OWNERS[service_id]
        children = LEGACY_CHILDREN[service_id]
        lines.extend(
            [
                f"## {service_id} — {hub.title}",
                "",
                f"- Владелец: WP {hub.current_wp_id}, [{hub.current_url}]({hub.current_url})",
                "- Действие: `reuse`; URL и WP ID не меняются",
                f"- Шаблон хаба: `{hub.target_template}` с service-v2 наполнением",
                f"- Business evidence: `{hub.business_evidence}`",
                f"- Граница: {hub.boundary}",
                f"- Дочерних услуг: **{len(children)}**",
                "",
                "Дочерние услуги:",
                "",
            ]
        )
        for child in children:
            lines.extend(
                [
                    f"- **{child.title}** — `{child.destination_id}`, [{child.target_url}]({child.target_url})",
                    f"  - Запрос-представитель: {child.representative_query}",
                    f"  - Business evidence: `{child.business_evidence}`",
                    f"  - Граница: {child.boundary}",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _csv_bytes(
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def validate_checked_in_legacy_artifacts(
    csv_path: Path = DEFAULT_CSV_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
    suggest_queue_path: Path = DEFAULT_SUGGEST_QUEUE_PATH,
) -> list[str]:
    """Report missing or stale generated artifacts without rewriting them."""

    expected = (
        (
            csv_path,
            _csv_bytes(CSV_COLUMNS, build_legacy_service_rows()),
            "legacy architecture CSV",
        ),
        (
            markdown_path,
            render_legacy_service_structure().encode("utf-8"),
            "legacy architecture Markdown",
        ),
        (
            suggest_queue_path,
            _csv_bytes(SUGGEST_QUEUE_COLUMNS, build_legacy_suggest_queue()),
            "legacy Suggest queue",
        ),
    )
    errors: list[str] = []
    for path, expected_bytes, label in expected:
        try:
            actual_bytes = path.read_bytes()
        except OSError:
            errors.append(f"{label} is missing: {path}")
            continue
        if actual_bytes != expected_bytes:
            errors.append(f"{label} is stale: {path}")
    return errors


def write_legacy_service_architecture(
    csv_path: Path = DEFAULT_CSV_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
    suggest_queue_path: Path = DEFAULT_SUGGEST_QUEUE_PATH,
) -> tuple[int, int]:
    """Write byte-stable UTF-8 architecture, review and Suggest queue files."""

    rows = build_legacy_service_rows()
    queue_rows = build_legacy_suggest_queue()
    markdown = render_legacy_service_structure()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    suggest_queue_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    with suggest_queue_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=SUGGEST_QUEUE_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(queue_rows)
    return len(rows), len(queue_rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the offline S9-S15 legacy service architecture."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--suggest-queue", type=Path, default=DEFAULT_SUGGEST_QUEUE_PATH)
    args = parser.parse_args(argv)
    destination_count, queue_count = write_legacy_service_architecture(
        args.csv,
        args.markdown,
        args.suggest_queue,
    )
    print(
        f"Exported {destination_count} S9-S15 destinations and "
        f"{queue_count} Yandex Suggest probes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
