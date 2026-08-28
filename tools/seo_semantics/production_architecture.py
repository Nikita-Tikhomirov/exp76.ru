"""Build the reviewed Task 2 overlays from immutable local evidence.

The module never calls a search API.  It classifies the already stored top-10
results, records the human-reviewed destination ruling for every cluster and
then proves that the pair overlay agrees with those destination owners.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit

from .architecture import (
    CLUSTER_DECISION_COLUMNS,
    ClusterPageDecision,
    load_pair_reviews,
    validate_pair_architecture_alignment,
    validate_pair_review_coverage,
)
from .scope import load_scope


REVIEWER = "codex-2026-08-28"
COMMERCIAL_INTENTS = {"transactional", "commercial_research"}
HUB_PRIMARY_CLUSTERS = {
    "S1": "SERP-704B34378555",
    "S2": "SERP-D06FD14A8839",
    "S3": "SERP-F24614ECFE67",
    "S4": "SERP-6CE4B6AF888B",
    "S5": "SERP-6DB26688AA57",
    "S6": "SERP-69104D6AA308",
    "S7": "SERP-6979557B24CA",
    "S8": "SERP-DA28A58E74C6",
}
AUTOPOLIV_PROTECTED_CLUSTER = "SERP-92449D7EF3C6"
AUTOPOLIV_DESTINATION = "FROZEN-F839FE6BFD56"
AUTOPOLIV_URL = "https://exp76.ru/category/avtopoliv-na-uchastke/"
S7_EXCLUDED_CLUSTERS = {
    "HOLD-630573F85F65": (
        "missing_representative_serp:HOLD-630573F85F65|query_form:product_lighting_fixtures",
        "The head query explicitly targets lighting fixtures and has no successful representative SERP; product demand is excluded.",
    ),
    "SERP-5A0AE0E41D86": (
        "Q000107",
        "Stored SERP is product_catalog:10 with no service landing; product demand is excluded.",
    ),
    "SERP-4FFE505A1BD1": (
        "Q000110|Q000112",
        "Stored SERPs are guide/product led with no service landing; the mixed cluster is excluded from the ready hub.",
    ),
    "SERP-942863B727BD": (
        "Q000111",
        "Stored SERP is product/guide led with no service landing; lighting-product demand is excluded.",
    ),
    "SERP-10BA4FC77863": (
        "Q000113",
        "Stored SERP is dominated by municipal complaints, rules and repairs rather than private-site installation.",
    ),
}
S7_HUB_EVIDENCE = {
    "SERP-6979557B24CA": "Q000109",
    "SERP-2716C16CFFC8": "Q000114",
}
CHILD_GROUPS = {
    "S2-CHILD-RULONNY-GAZON": {
        "primary": "SERP-D405C455A674",
        "clusters": {
            "SERP-D405C455A674",
            "SERP-151040020C7C",
            "SERP-7C47C44022BF",
            "SERP-634958A3C2DB",
            "SERP-0767F40D1ED4",
            "SERP-4D82034EB5C5",
            "HOLD-38F85CB02478",
            "HOLD-89A4E8CC1C19",
        },
        "slug": "rulonnyj-gazon-pod-kljuch",
        "service_id": "S2",
        "business_offer_confirmed": "yes",
        "business_evidence": (
            "business_source:ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "gazon-posevnojj-i-gazon-rulonnyjj.json#services.items[Рулонный газон]"
        ),
    },
    "S2-CHILD-POSEVNOY-GAZON": {
        "primary": "SERP-6070ECC246E8",
        "clusters": {"SERP-6070ECC246E8", "SERP-1E2A5B0176EC", "SERP-C1723250580F"},
        "slug": "posevnoj-gazon-pod-kljuch",
        "service_id": "S2",
        "business_offer_confirmed": "yes",
        "business_evidence": (
            "business_source:ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "gazon-posevnojj-i-gazon-rulonnyjj.json#services.items[Посевной газон]"
        ),
    },
    "S3-CHILD-KRUPNOMERY": {
        "primary": "SERP-09010110F02E",
        "clusters": {"SERP-09010110F02E"},
        "slug": "posadka-krupnomerov",
        "service_id": "S3",
        "business_offer_confirmed": "no",
        "business_evidence": "",
    },
    "S4-CHILD-OBREZKA": {
        "primary": "SERP-B592CED7E831",
        "clusters": {
            "SERP-B592CED7E831",
            "SERP-0D0F2C22B0AB",
            "SERP-ED6D674F80F1",
            "SERP-8F99DD3FB843",
            "HOLD-0D178048D6E9",
        },
        "slug": "obrezka-derevev-i-kustarnikov",
        "service_id": "S4",
        "business_offer_confirmed": "yes",
        "business_evidence": (
            "business_source:ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "ukhod-za-sadom.json#seo.description+services.items[Обрезка]"
        ),
    },
    "S5-CHILD-VYRAVNIVANIE": {
        "primary": "SERP-13FD00FC92C7",
        "clusters": {
            "SERP-13FD00FC92C7",
            "SERP-3AF29E33EBAC",
            "SERP-F560E613866F",
            "HOLD-4E5B4B602503",
        },
        "slug": "vyravnivanie-uchastka",
        "service_id": "S5",
        "business_offer_confirmed": "yes",
        "business_evidence": (
            "business_source:ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/"
            "planirovka-territorii.json#intro+services.items[Выравнивание]"
        ),
    },
}
ARTICLE_GROUPS = {
    "S1-ARTICLE-DIY-DESIGN": {
        "primary": "HOLD-9CF4ABC55090",
        "clusters": {"HOLD-9CF4ABC55090", "HOLD-FD41CABAE854"},
    },
    "S3-ARTICLE-PLANTING-SCHEMES": {
        "primary": "HOLD-A31AAE5725CD",
        "clusters": {"HOLD-1D9AC2530460", "HOLD-A31AAE5725CD", "HOLD-AF75D8A25C90"},
    },
    "S4-ARTICLE-PRUNING-GUIDE": {
        "primary": "HOLD-136ED0AAB28A",
        "clusters": {"HOLD-136ED0AAB28A", "HOLD-32452491B993"},
    },
    "S6-ARTICLE-DIY-RETAINING-WALL": {
        "primary": "HOLD-70212404217F",
        "clusters": {"HOLD-544177B45D38", "HOLD-70212404217F"},
    },
    "S7-ARTICLE-DIY-LIGHTING": {
        "primary": "HOLD-EC53FCBA2C1F",
        "clusters": {"HOLD-5A855707AEC1", "HOLD-CA29C3BD9F29", "HOLD-EC53FCBA2C1F"},
    },
    "S8-ARTICLE-DIY-ENTRANCE": {
        "primary": "HOLD-BE8C4D20F9A4",
        "clusters": {
            "HOLD-2F1C98E80F71",
            "HOLD-5B52CBB329C4",
            "HOLD-BE8C4D20F9A4",
            "HOLD-EB70299AA189",
        },
    },
}
SPECIAL_URLS = {
    "SPECIAL-BRAND-HOMEPAGE": "https://exp76.ru/",
    "SPECIAL-CALCULATOR": "https://exp76.ru/kalkuljator-uslug/",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _transliterate(value: str) -> str:
    table = str.maketrans(
        {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
            "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
        }
    )
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold().translate(table)).strip("-")
    return slug[:72] or "semantic-guide"


def _successful_head_refs(
    clusters: Sequence[Mapping[str, str]], serp_rows: Sequence[Mapping[str, str]]
) -> dict[str, str]:
    query_ids: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in serp_rows:
        key = (row["service_id"], row["intent"], row["query"])
        if row["query_id"] not in query_ids[key]:
            query_ids[key].append(row["query_id"])
    refs: dict[str, str] = {}
    for cluster in clusters:
        key = (cluster["service_id"], cluster["intent"], cluster["head_query"])
        values = query_ids.get(key, [])
        refs[cluster["cluster_id"]] = "|".join(values) or (
            f"missing_representative_serp:{cluster['cluster_id']}"
        )
    return refs


def _s1_is_broad_need(query: str) -> bool:
    value = query.casefold()
    implementation_price = "реализац" in value and (
        "обустрой" in value or "благоустр" in value
    )
    if any(token in value for token in ("проект", "дизайн", "проектир")) and not implementation_price:
        return False
    return any(
        token in value
        for token in (
            "благоустр",
            "благоучтрой",
            "обустрой",
            "цен",
            "стоимост",
            "прейскурант",
            "компан",
            "сайт",
        )
    )


def _is_broad_s1_owner(cluster: Mapping[str, str]) -> bool:
    if cluster["service_id"] != "S1" or cluster["intent"] not in COMMERCIAL_INTENTS:
        return False
    return _s1_is_broad_need(cluster["head_query"])


def _child_owner(cluster_id: str) -> tuple[str, Mapping[str, object]] | None:
    for destination_id, group in CHILD_GROUPS.items():
        if cluster_id in group["clusters"]:
            return destination_id, group
    return None


def _article_owner(cluster_id: str) -> tuple[str, Mapping[str, object]] | None:
    for destination_id, group in ARTICLE_GROUPS.items():
        if cluster_id in group["clusters"]:
            return destination_id, group
    return None


def build_cluster_decisions(
    scope_path: Path,
    clusters: Sequence[Mapping[str, str]],
    serp_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Assign every cluster exactly once while keeping unsupported pages blocked."""
    scope = load_scope(scope_path)
    service_urls = {item.service_id: item.current_url for item in scope.services}
    refs = _successful_head_refs(clusters, serp_rows)
    broad_s1 = [row for row in clusters if _is_broad_s1_owner(row)]
    broad_primary = next(
        (row["cluster_id"] for row in broad_s1 if row["cluster_id"] == "SERP-7A77EA65DFCA"),
        broad_s1[0]["cluster_id"],
    )
    rows: list[dict[str, str]] = []
    for cluster in clusters:
        cluster_id = cluster["cluster_id"]
        service_id = cluster["service_id"]
        intent = cluster["intent"]
        current_url = service_urls.get(service_id, cluster.get("target_url", ""))
        evidence_refs = refs[cluster_id]
        values = {
            "cluster_id": cluster_id,
            "service_id": service_id,
            "destination_id": "",
            "page_role": "none",
            "parent_destination_id": "",
            "current_url": "",
            "proposed_url": "",
            "proposed_slug": "",
            "url_action": "exclude",
            "publication_status": "backlog",
            "business_offer_confirmed": "no",
            "evidence_refs": evidence_refs,
            "review_status": "reviewed",
            "reviewer": REVIEWER,
            "rationale": "",
        }
        if intent == "frozen_collision":
            values.update(
                destination_id=cluster_id,
                page_role="frozen",
                current_url=cluster["target_url"],
                proposed_slug=urlsplit(cluster["target_url"]).path.strip("/"),
                url_action="frozen",
                publication_status="ready",
                business_offer_confirmed="yes",
                evidence_refs=f"protected_owner:{cluster['target_url']}",
                rationale="Protected category 87-92 owner retained exactly; no new destination is allowed.",
            )
        elif intent in {"product_only", "external_noise"}:
            values.update(
                evidence_refs=evidence_refs if intent == "product_only" else "reviewed_external_noise_policy",
                rationale=(
                    "Product-only demand has no installation-service destination and remains excluded."
                    if intent == "product_only"
                    else "Reviewed external-noise cluster remains excluded from the page tree."
                ),
            )
        elif cluster_id in SPECIAL_URLS:
            target = SPECIAL_URLS[cluster_id]
            values.update(
                destination_id=cluster_id,
                page_role="special",
                current_url=target,
                proposed_slug=urlsplit(target).path.strip("/") or "homepage",
                url_action="special",
                publication_status="ready",
                evidence_refs="existing_special_owner",
                rationale="Existing special owner is retained and is outside the service-hub release inventory.",
            )
        elif cluster_id == "SPECIAL-EXTERNAL-EXCLUSION":
            values.update(
                evidence_refs="reviewed_external_noise_policy",
                rationale="Reviewed external-noise cluster remains excluded from the page tree.",
            )
        elif cluster_id == AUTOPOLIV_PROTECTED_CLUSTER:
            values.update(
                destination_id=AUTOPOLIV_DESTINATION,
                page_role="frozen",
                url_action="merge",
                publication_status="ready",
                evidence_refs=f"Q000046|protected_owner:{AUTOPOLIV_URL}",
                rationale=(
                    "Stored Q000046 is auto-irrigation dominated, so this lexical lawn projection "
                    "merges into the protected auto-irrigation owner instead of the S2 lawn hub."
                ),
            )
        elif cluster_id in S7_EXCLUDED_CLUSTERS:
            stored_refs, evidence_rationale = S7_EXCLUDED_CLUSTERS[cluster_id]
            values.update(
                evidence_refs=stored_refs,
                rationale=evidence_rationale,
            )
        elif intent == "informational":
            article_group = _article_owner(cluster_id)
            destination_id = (
                article_group[0]
                if article_group is not None
                else f"{service_id}-ARTICLE-{cluster_id.split('-', 1)[-1]}"
            )
            primary = article_group is None or cluster_id == article_group[1]["primary"]
            primary_cluster = (
                cluster
                if primary
                else next(item for item in clusters if item["cluster_id"] == article_group[1]["primary"])
            )
            slug = _transliterate(primary_cluster["head_query"])
            values.update(
                destination_id=destination_id,
                page_role="article",
                parent_destination_id=f"{service_id}-HUB",
                proposed_url=f"https://exp76.ru/{slug}/" if primary else "",
                proposed_slug=slug,
                url_action="article" if primary else "merge",
                publication_status="backlog",
                evidence_refs=f"missing_representative_serp:{cluster_id}",
                rationale=(
                    "Informational intent stays separate from commercial pages, but no successful stored "
                    "representative-query SERP exists; article is backlog pending evidence and media mapping."
                ),
            )
        elif _is_broad_s1_owner(cluster):
            values.update(
                destination_id="SPECIAL-SERVICES-CATALOG",
                page_role="special",
                current_url="https://exp76.ru/services/",
                proposed_slug="services",
                url_action="special" if cluster_id == broad_primary else "merge",
                publication_status="ready",
                business_offer_confirmed="yes",
                rationale=(
                    "Broad landscaping/complex-improvement demand retains the legacy /services/ owner; "
                    "it must not broaden the S1 landscape-design hub."
                ),
            )
        elif (child := _child_owner(cluster_id)) is not None:
            destination_id, group = child
            slug = str(group["slug"])
            primary = cluster_id == group["primary"]
            business_offer = str(group["business_offer_confirmed"])
            business_evidence = str(group["business_evidence"])
            publication = "blocked_facts"
            values.update(
                destination_id=destination_id,
                page_role="child_service",
                parent_destination_id=f"{service_id}-HUB",
                proposed_url=f"https://exp76.ru/{slug}/" if primary else "",
                proposed_slug=slug,
                url_action="child" if primary else "merge",
                publication_status=publication,
                business_offer_confirmed=business_offer,
                evidence_refs="|".join(
                    part for part in (evidence_refs, business_evidence) if part
                ),
                rationale=(
                    "Stored representative SERP supports a distinct service-page candidate. The exact "
                    + (
                        "offer is traceable to the current hub payload, while Task 3 case/photo mapping "
                        "remains incomplete; publication is blocked on proof mapping."
                        if business_offer == "yes"
                        else "business offer is not confirmed by current source material, and Task 3 "
                        "case/photo mapping is incomplete; publication is blocked on those facts."
                    )
                ),
            )
        elif intent in COMMERCIAL_INTENTS:
            hub_id = f"{service_id}-HUB"
            primary = cluster_id == HUB_PRIMARY_CLUSTERS[service_id]
            if cluster_id in S7_HUB_EVIDENCE:
                evidence_refs = S7_HUB_EVIDENCE[cluster_id]
            values.update(
                destination_id=hub_id,
                page_role="hub",
                current_url=current_url if primary else "",
                proposed_slug=urlsplit(service_urls[service_id]).path.strip("/").split("/")[-1],
                url_action="hub" if primary else "merge",
                publication_status="ready",
                business_offer_confirmed="yes",
                rationale=(
                    "Commercial intent remains with the immutable existing service hub; narrower "
                    "destination is not approved without separate offer and content evidence."
                ),
            )
        else:
            values.update(
                evidence_refs=evidence_refs or f"policy:{cluster_id}",
                rationale="Non-release semantic cluster remains explicitly excluded.",
            )
        rows.append({field: str(values[field]) for field in CLUSTER_DECISION_COLUMNS})
    return rows


def _result_format(row: Mapping[str, str]) -> str:
    """Classify a stored result into the page formats used by manual review notes."""
    host = (urlsplit(row["canonical_url"]).hostname or "").casefold()
    path = urlsplit(row["canonical_url"]).path.casefold()
    title = row["title"].casefold()
    if any(token in host for token in ("avito.", "profi.", "uslugi.yandex", "youdo.")):
        return "marketplace_directory"
    if any(token in host for token in ("2gis.", "zoon.", "yell.", "orgpage.")):
        return "local_directory"
    if any(token in host for token in ("ozon.", "market.yandex", "leroy", "vseinstrumenti")):
        return "product_catalog"
    if any(token in path for token in ("/blog", "/article", "/stati", "/wiki")) or any(
        token in title for token in ("как сделать", "своими руками", "инструкция", "схема", "советы")
    ):
        return "article_guide"
    if any(token in title for token in ("купить", "продажа", "товар")):
        return "product_catalog"
    if any(
        token in title
        for token in ("услуги", "под ключ", "монтаж", "устройство", "заказать", "работы")
    ):
        return "service_landing"
    return "topic_landing"


def _format_summary(rows: Sequence[Mapping[str, str]]) -> str:
    counts = Counter(_result_format(row) for row in rows)
    return ",".join(f"{name}:{count}" for name, count in sorted(counts.items()))


def canonical_need_label(service_id: str, query: str) -> str:
    """Describe the user need from query wording without consulting page owners."""
    value = query.casefold()
    if service_id == "S1":
        return (
            "комплексное благоустройство участка"
            if _s1_is_broad_need(query)
            else "ландшафтное проектирование и дизайн"
        )
    if service_id == "S2":
        if "полив" in value:
            return "автоматический полив газона"
        if "рулон" in value or "раскат" in value:
            return "рулонный газон"
        if "посевн" in value or "посев " in value:
            return "посевной газон"
        return "устройство газона"
    if service_id == "S3":
        if "крупномер" in value:
            return "посадка крупномеров"
        if "хвойн" in value:
            return "посадка хвойных"
        return "посадка деревьев и кустарников"
    if service_id == "S4":
        return "обрезка деревьев и кустарников" if "обрез" in value else "уход за садом"
    if service_id == "S5":
        if any(
            token in value
            for token in ("выравн", "выровн", "подсып", "подъем", "поднять", "поднятие")
        ):
            return "выравнивание и изменение отметок участка"
        return "планировка территории"
    if service_id == "S7":
        if "ландшафтное освещение" in value and not any(
            token in value for token in ("ярослав", "рыбин", "углич", "тутаев", "переслав", "монтаж")
        ):
            return "товары для ландшафтного освещения"
        if "подсветка" in value or value == "освещение участка":
            return "информационный выбор и схема освещения"
        if "рыбинский район" in value:
            return "муниципальное уличное освещение и ремонт"
        return "монтаж освещения частного участка"
    return {
        "S6": "устройство подпорной стенки",
        "S8": "устройство въезда через канаву",
    }.get(service_id, "проверяемая потребность")


def manual_review_rationale(row: Mapping[str, str], decision: str, observed: str) -> str:
    """Format an evidence annotation for a pre-existing manual pair decision."""
    left_query = row["left_query"]
    right_query = row["right_query"]
    left_need = canonical_need_label(row["left_service_id"], left_query)
    right_need = canonical_need_label(row["right_service_id"], right_query)
    if decision == "same_destination":
        return (
            f'same need after independent review: "{left_query}" ({left_need}) and '
            f'"{right_query}" ({right_need}) converge on one canonical answer; {observed}; '
            "stored top-10 result types and query wording support one service page."
        )
    return (
        f'different need after independent review: "{left_query}" targets {left_need}, while '
        f'"{right_query}" targets {right_need}; {observed}; stored top-10 result types and '
        "query wording require separate canonical answers."
    )


def validate_manual_review_evidence(
    ambiguous_rows: Sequence[Mapping[str, str]],
    serp_rows: Sequence[Mapping[str, str]],
    reviews: Mapping[str, object],
) -> list[str]:
    """Prove each static manual ruling cites its exact stored top-10 observations."""
    serp_by_query: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in serp_rows:
        serp_by_query[row["query_id"]].append(row)
    errors: list[str] = []
    for row in ambiguous_rows:
        if row["decision"] != "manual_review":
            continue
        pair_id = row["pair_id"]
        review = reviews.get(pair_id)
        if review is None:
            continue
        left_rows = serp_by_query[row["left_query_id"]]
        right_rows = serp_by_query[row["right_query_id"]]
        if len(left_rows) != 10 or len(right_rows) != 10:
            errors.append(f"{pair_id} lacks two complete stored top-10 result sets")
            continue
        observed = (
            f"overlap={row['overlap']}/10; "
            f"formats=left[{_format_summary(left_rows)}];right[{_format_summary(right_rows)}]"
        )
        rationale = review.rationale
        expected_prefix = (
            "same need after independent review:"
            if review.decision == "same_destination"
            else "different need after independent review:"
        )
        if not rationale.startswith(expected_prefix):
            errors.append(f"{pair_id} rationale has no independent need ruling")
        if row["left_query"] not in rationale or row["right_query"] not in rationale:
            errors.append(f"{pair_id} rationale does not name both reviewed queries")
        left_need = canonical_need_label(row["left_service_id"], row["left_query"])
        right_need = canonical_need_label(row["right_service_id"], row["right_query"])
        expected_decision = (
            "same_destination" if left_need == right_need else "separate_destinations"
        )
        if review.decision != expected_decision:
            errors.append(
                f"{pair_id} decision contradicts canonical needs: {left_need!r} vs {right_need!r}"
            )
        lowered = rationale.casefold()
        if (
            "owner" in lowered
            or "destination" in lowered
            or "support this ruling" in lowered
            or re.search(r"\b(?:S[1-8]-(?:HUB|CHILD|ARTICLE)|SPECIAL-)\S*", rationale)
        ):
            errors.append(f"{pair_id} rationale contains destination-led or generic wording")
        for field in ("rationale", "evidence_note"):
            if observed not in getattr(review, field):
                errors.append(f"{pair_id} {field} does not match stored SERP formats")
    return errors


def generate(data_root: Path) -> tuple[int, int]:
    """Validate the manual pair ledger, then regenerate page decisions from it."""
    processed = data_root / "processed"
    reviews_dir = data_root / "reviews"
    clusters = _read_csv(processed / "clusters.csv")
    serp_rows = _read_csv(processed / "serp_results.csv")
    ambiguous = _read_csv(processed / "serp_ambiguous_pairs.csv")
    candidates = _read_csv(processed / "candidate_cluster_map.csv")
    reviews = load_pair_reviews(reviews_dir / "serp_pair_reviews.csv")
    errors = validate_pair_review_coverage(ambiguous, reviews)
    errors.extend(validate_manual_review_evidence(ambiguous, serp_rows, reviews))
    if errors:
        raise ValueError("; ".join(sorted(set(errors))))

    decisions = build_cluster_decisions(data_root / "scope.json", clusters, serp_rows)

    decision_objects = {
        row["cluster_id"]: ClusterPageDecision(**{field: row[field] for field in CLUSTER_DECISION_COLUMNS})
        for row in decisions
    }
    errors = validate_pair_architecture_alignment(
        ambiguous, candidates, reviews, decision_objects
    )
    if len(ambiguous) != 1044 or len(reviews) != 263 or len(decisions) != 164:
        errors.append(
            f"cardinality drift: evidence={len(ambiguous)}, reviews={len(reviews)}, decisions={len(decisions)}"
        )
    if errors:
        raise ValueError("; ".join(sorted(set(errors))))
    _write_csv(reviews_dir / "cluster_page_decisions.csv", CLUSTER_DECISION_COLUMNS, decisions)
    return len(reviews), len(decisions)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args(argv)
    reviews, decisions = generate(args.data_root.resolve())
    print(f"manual reviews validated: pair_reviews={reviews}, cluster_decisions={decisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
