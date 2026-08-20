"""Deterministic intent and frozen-owner classification for semantic queries."""

from __future__ import annotations

from dataclasses import dataclass

from .normalize import normalize_query
from .scope import ScopeConfig


Term = tuple[str, ...]


@dataclass(frozen=True)
class QueryClassification:
    """One reproducible first-pass decision without changing source evidence."""

    intent: str
    service_id: str
    relevance: str
    exclusion_reason: str
    frozen_collision: bool
    geo: str
    entities: tuple[str, ...]
    owner_url: str = ""


_TRANSACTIONAL_TERMS: tuple[Term, ...] = (
    ("цена",), ("цены",), ("стоимость",), ("стоимости",), ("заказать",),
    ("под", "ключ"), ("монтаж",), ("устройство",), ("строительство",),
    ("услуга",), ("услуги",),
)
_INFORMATIONAL_TERMS: tuple[Term, ...] = (
    ("как",), ("своими", "руками"), ("схема",), ("схемы",), ("норма",),
    ("нормы",), ("ошибка",), ("ошибки",), ("инструкция",), ("инструкции",),
)
_COMMERCIAL_RESEARCH_TERMS: tuple[Term, ...] = (
    ("сравнение",), ("вариант",), ("варианты",), ("материал",), ("материалы",),
    ("расчет",), ("калькулятор",), ("срок",), ("сроки",), ("сколько",),
)
_PRODUCT_TERMS: tuple[Term, ...] = (
    ("купить",), ("продажа",), ("производитель",), ("магазин",),
)
_BRAND_TERMS: tuple[Term, ...] = (
    ("exp76",), ("exp", "76"), ("эксперт", "76"), ("эксперты", "76"),
    ("эксперты", "рыбинск"),
)

_EXCLUSION_TERMS: tuple[tuple[str, tuple[Term, ...]], ...] = (
    (
        "jobs",
        (
            ("вакансия",), ("вакансии",), ("работа",), ("зарплата",),
            ("зарплаты",), ("резюме",),
        ),
    ),
    (
        "training",
        (
            ("курс",), ("курсы",), ("обучение",), ("диплом",), ("дипломы",),
        ),
    ),
)

# Priority is intentional: specific engineering owners win before the broader
# drainage/dewatering terms when a query names more than one frozen direction.
_FROZEN_OWNERS: tuple[tuple[str, str, tuple[Term, ...]], ...] = (
    (
        "storm_sewer",
        "https://exp76.ru/category/livnevaya-kanalizatsiya/",
        (
            ("ливневка",), ("ливневки",), ("ливневую",), ("ливневая", "канализация"),
            ("ливневой", "канализации"), ("ливневые", "канализации"),
            ("ливневый", "дренаж"),
            ("дождеприемник",), ("дождеприемники",), ("ливнеприемник",),
            ("линейный", "водоотвод"), ("линейного", "водоотвода"),
            ("лотки", "водоотведения"), ("лотков", "водоотведения"),
        ),
    ),
    (
        "irrigation",
        "https://exp76.ru/category/avtopoliv-na-uchastke/",
        (
            ("автополив",), ("автополива",), ("автополивом",),
            ("автоматический", "полив"), ("автоматического", "полива"),
            ("капельный", "полив"), ("капельного", "полива"),
            ("ирригация",), ("ирригации",),
        ),
    ),
    (
        "blind_area",
        "https://exp76.ru/category/otmostka-vokrug-doma/",
        (("отмостка",), ("отмостки",), ("отмостку",), ("отмосткой",)),
    ),
    (
        "paving",
        "https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
        (
            ("тротуарная", "плитка"), ("тротуарной", "плитки"),
            ("тротуарную", "плитку"), ("брусчатка",), ("брусчатки",),
            ("брусчатку",), ("мощение",), ("мощения",),
            ("уличная", "плитка"), ("уличной", "плитки"),
            ("уличную", "плитку"), ("дворовая", "плитка"),
            ("дворовой", "плитки"), ("дворовую", "плитку"),
        ),
    ),
    (
        "drainage",
        "https://exp76.ru/category/drenazh-uchastka/",
        (
            ("дренаж",), ("дренажа",), ("дренажу",), ("дренажом",),
            ("дренажный",), ("дренажная",), ("дренажной",), ("дренажные",),
            ("дренажную",), ("дренажным",), ("дренажных",),
            ("дренированию",), ("грунтовые", "воды"), ("грунтовых", "вод"),
        ),
    ),
    (
        "dewatering",
        "https://exp76.ru/category/osushenie-uchastka/",
        (
            ("осушение",), ("осушения",), ("осушению",),
            ("заболоченный",), ("заболоченного",), ("заболоченном",),
        ),
    ),
)

_SERVICE_TERMS: tuple[tuple[str, tuple[Term, ...]], ...] = (
    (
        "S8",
        (
            ("въезд", "на", "участок"), ("въезд", "через", "канаву"),
            ("въезд", "в", "канаву"),
            ("заезд", "на", "участок"), ("заезд", "через", "канаву"),
            ("труба", "в", "канаву"), ("трубу", "в", "канаву"),
            ("мостик", "через", "канаву"), ("плиту", "через", "канаву"),
        ),
    ),
    (
        "S6",
        (
            ("подпорная", "стенка"), ("подпорной", "стенки"),
            ("подпорную", "стенку"), ("подпорная", "стена"),
            ("подпорной", "стены"),
        ),
    ),
    (
        "S7",
        (
            ("освещение", "участка"), ("ландшафтное", "освещение"),
            ("уличное", "освещение"), ("подсветка", "участка"),
            ("подсветка", "дорожек"),
        ),
    ),
    (
        "S2",
        (
            ("газон",), ("газона",), ("газону",), ("газоном",),
        ),
    ),
    (
        "S3",
        (
            ("посадка", "деревьев"), ("посадка", "кустарников"),
            ("посадка", "хвойных"), ("посадка", "крупномеров"),
            ("дендролог",),
        ),
    ),
    (
        "S4",
        (
            ("уход", "за", "садом"), ("обслуживание", "сада"),
            ("садовник",), ("садовника",), ("садовником",),
            ("садовые", "работы"), ("работы", "садовых"), ("работ", "садовых"),
            ("обрезка", "деревьев"),
            ("обрезка", "кустарников"), ("корчевание", "деревьев"),
            ("корчевка", "пня"),
        ),
    ),
    (
        "S5",
        (
            ("планировка", "участка"), ("планировка", "территории"),
            ("планировка", "грунта"), ("вертикальная", "планировка"),
            ("выравнивание", "участка"), ("выровнять", "участок"),
            ("поднять", "участок", "грунтом"),
        ),
    ),
    (
        "S1",
        (
            ("ландшафтный", "дизайн"), ("ландшафтное", "проектирование"),
            ("ландшафтному", "дизайну"), ("ландшафтного", "дизайна"),
            ("ландшафтная", "компания"), ("ландшафтный", "дизайнер"),
            ("дизайн", "проект", "участка"), ("проект", "благоустройства"),
            ("озеленение", "участка"), ("благоустройство", "участка"),
            ("благоустройство", "территории"), ("ландшафтные", "работы"),
            ("благоустройство",), ("благоустройства",), ("благоустройству",),
            ("благоустройстве",), ("благоучтройство",),
            ("проектные", "работы"), ("проекты", "придомовых", "территорий"),
            ("обустройства", "частного", "участка"),
            ("эксперты", "рыбинск"),
        ),
    ),
)


def classify_query(query: str, service_hint: str, scope: ScopeConfig) -> QueryClassification:
    """Classify one query with ordered, whole-token and whole-phrase matching."""
    service_ids = {service.service_id for service in scope.services}
    if service_hint and service_hint not in service_ids:
        raise ValueError(f"unknown service hint: {service_hint}")

    normalized = normalize_query(query)
    tokens = tuple(normalized.split())
    service_id = service_hint or infer_service_id(query)
    geo = _detect_geo(tokens, scope)

    for reason, terms in _EXCLUSION_TERMS:
        if _contains_any(tokens, terms):
            return QueryClassification(
                intent="irrelevant",
                service_id=service_id,
                relevance="excluded",
                exclusion_reason=reason,
                frozen_collision=False,
                geo=geo,
                entities=(reason,),
            )

    frozen = _match_frozen(tokens, scope)
    intent = _detect_intent(tokens, bool(service_id) or frozen is not None)
    entities = _entities(tokens, service_id, frozen[0] if frozen else "")
    if frozen:
        frozen_name, owner_url = frozen
        return QueryClassification(
            intent=intent,
            service_id=service_id,
            relevance="manual_review" if service_id else "frozen_collision",
            exclusion_reason="",
            frozen_collision=True,
            geo=geo,
            entities=entities or (frozen_name,),
            owner_url=owner_url,
        )
    if not service_id and _contains_any(tokens, _BRAND_TERMS):
        return QueryClassification(
            intent="brand_navigation",
            service_id="S1",
            relevance="relevant",
            exclusion_reason="",
            frozen_collision=False,
            geo=geo,
            entities=("service:S1", "brand:exp76"),
        )
    if not service_id:
        return QueryClassification(
            intent="irrelevant",
            service_id="",
            relevance="excluded",
            exclusion_reason="out_of_scope",
            frozen_collision=False,
            geo=geo,
            entities=entities,
        )
    return QueryClassification(
        intent=intent,
        service_id=service_id,
        relevance="relevant",
        exclusion_reason="",
        frozen_collision=False,
        geo=geo,
        entities=entities,
    )


def infer_service_id(query: str) -> str:
    """Return the first service whose explicit phrase matches the query."""
    tokens = tuple(normalize_query(query).split())
    for service_id, terms in _SERVICE_TERMS:
        if _contains_any(tokens, terms):
            return service_id
    return ""


def exclusion_evidence(query: str, reason: str) -> tuple[str, ...]:
    """Return canonical exclusion words present as complete tokens."""
    tokens = tuple(normalize_query(query).split())
    canonical_terms = {
        "jobs": (
            ("вакансия", (("вакансия",), ("вакансии",))),
            ("работа", (("работа",),)),
            ("зарплата", (("зарплата",), ("зарплаты",))),
            ("резюме", (("резюме",),)),
        ),
        "training": (
            ("курс", (("курс",), ("курсы",))),
            ("обучение", (("обучение",),)),
            ("диплом", (("диплом",), ("дипломы",))),
        ),
    }
    return tuple(
        word
        for word, terms in canonical_terms.get(reason, ())
        if _contains_any(tokens, terms)
    )


def _detect_intent(tokens: tuple[str, ...], has_service: bool) -> str:
    if _contains_any(tokens, _INFORMATIONAL_TERMS):
        return "informational"
    if _contains_any(tokens, _TRANSACTIONAL_TERMS):
        return "transactional"
    if _contains_any(tokens, _PRODUCT_TERMS):
        return "product_only"
    if _contains_any(tokens, _BRAND_TERMS):
        return "brand_navigation"
    if _contains_any(tokens, _COMMERCIAL_RESEARCH_TERMS) or has_service:
        return "commercial_research"
    return "irrelevant"


def _match_frozen(tokens: tuple[str, ...], scope: ScopeConfig) -> tuple[str, str] | None:
    candidates: list[tuple[int, int, str, str]] = []
    for priority, (name, owner_url, terms) in enumerate(_FROZEN_OWNERS):
        if owner_url not in scope.frozen_urls:
            continue
        indexes = [index for term in terms if (index := _phrase_index(tokens, term)) is not None]
        if name == "paving" and (contextual_index := _contextual_paving_index(tokens)) is not None:
            indexes.append(contextual_index)
        if indexes:
            candidates.append((min(indexes), priority, name, owner_url))
    if not candidates:
        return None
    _, _, name, owner_url = min(candidates)
    return name, owner_url


def _contextual_paving_index(tokens: tuple[str, ...]) -> int | None:
    tile_tokens = frozenset({"плитка", "плитки", "плитку", "плиткой"})
    outdoor_tokens = frozenset(
        {
            "дорожка", "дорожке", "дорожки", "дорожку", "двор", "дворе", "дворовой",
            "улица", "улице", "уличная", "уличной", "уличную", "участок", "участке",
            "участка", "дача", "даче",
        }
    )
    if not outdoor_tokens.intersection(tokens):
        return None
    return next((index for index, token in enumerate(tokens) if token in tile_tokens), None)


def _detect_geo(tokens: tuple[str, ...], scope: ScopeConfig) -> str:
    for region in sorted(scope.regions, key=lambda item: item.priority):
        region_tokens = tuple(normalize_query(region.name).split())
        if _contains_phrase(tokens, region_tokens):
            return region.name
    aliases: tuple[tuple[Term, str], ...] = (
        (("ярославская",), "Ярославская область"),
        (("ярославской",), "Ярославская область"),
        (("переславль",), "Переславль-Залесский"),
    )
    for phrase, region_name in aliases:
        if _contains_phrase(tokens, phrase):
            return region_name
    return ""


def _entities(tokens: tuple[str, ...], service_id: str, frozen_name: str) -> tuple[str, ...]:
    values: list[str] = []
    if service_id:
        values.append(f"service:{service_id}")
    if frozen_name:
        values.append(f"frozen:{frozen_name}")
    if "участок" in tokens or "участка" in tokens:
        values.append("object:site")
    return tuple(values)


def _contains_any(tokens: tuple[str, ...], terms: tuple[Term, ...]) -> bool:
    return any(_contains_phrase(tokens, term) for term in terms)


def _contains_phrase(tokens: tuple[str, ...], phrase: Term) -> bool:
    return _phrase_index(tokens, phrase) is not None


def _phrase_index(tokens: tuple[str, ...], phrase: Term) -> int | None:
    width = len(phrase)
    if width == 0 or width > len(tokens):
        return None
    return next(
        (index for index in range(len(tokens) - width + 1) if tokens[index:index + width] == phrase),
        None,
    )
