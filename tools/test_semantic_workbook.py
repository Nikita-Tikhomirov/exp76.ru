import csv
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from tools.seo_semantics.architecture import CONTENT_BRIEF_COLUMNS
from tools.seo_semantics.cli import main
from tools.seo_semantics.workbook import (
    build_workbook,
    validate_processed_data,
    validate_workbook,
)


SHEET_NAMES = (
    "scope_urls",
    "keywords_raw",
    "keywords_clean",
    "minus_words",
    "frozen_collisions",
    "serp_results",
    "clusters",
    "url_map",
    "content_briefs",
    "launch_monitoring",
    "qa_log",
)
ROOT = Path(__file__).resolve().parents[1]
REAL_PROCESSED = ROOT / "seo-data/2026-08-exp76-services/processed"
REAL_SCOPE = ROOT / "seo-data/2026-08-exp76-services/scope.json"

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_fixture(processed_dir: Path, *, invalid: bool = False) -> None:
    processed_dir.mkdir(parents=True)

    _write_csv(
        processed_dir / "scope_urls.csv",
        [
            "service_id",
            "service_name",
            "current_url",
            "current_status",
            "current_canonical",
            "current_template",
            "webmaster_impressions",
            "webmaster_clicks",
            "frozen",
            "notes",
        ],
        [
            {
                "service_id": "S1",
                "service_name": "Ландшафтное проектирование",
                "current_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "current_status": "200",
                "current_canonical": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "current_template": "service-category",
                "webmaster_impressions": "147",
                "webmaster_clicks": "13",
                "frozen": "false",
                "notes": "Существующий URL сохраняется",
            }
        ],
    )
    raw_rows = [
        {
            "keyword_id": "K0001",
            "query_raw": "ландшафтный дизайн ярославль",
            "query_normalized": "ландшафтный дизайн ярославль",
            "sources": "webmaster",
            "impressions": "16",
            "clicks": "2",
            "ctr": "12.5",
            "avg_position": "8.4",
            "collected_at": "2026-08-20T18:17:52+03:00",
        }
    ]
    if invalid:
        raw_rows.append(
            {
                "keyword_id": "K0002",
                "query_raw": "посадка кустарников ярославль",
                "query_normalized": "посадка кустарников ярославль",
                "sources": "webmaster",
                "impressions": "5",
                "clicks": "1",
                "ctr": "20",
                "avg_position": "12",
                "collected_at": "2026-08-20T18:17:52+03:00",
            }
        )
    raw_fields = [
        "keyword_id",
        "query_raw",
        "query_normalized",
        "sources",
        "impressions",
        "clicks",
        "ctr",
        "avg_position",
        "collected_at",
    ]
    _write_csv(processed_dir / "keywords_raw.csv", raw_fields, raw_rows)

    clean_rows = [
        {
            **raw_rows[0],
            "service_id": "S1",
            "intent": "commercial_research",
            "relevance": "relevant",
            "frozen_collision": "false",
            "owner_url": "",
            "review_status": "reviewed",
            "final_decision": "keep",
        }
    ]
    if invalid:
        clean_rows.append(
            {
                **raw_rows[1],
                "service_id": "S3",
                "intent": "commercial_research",
                "relevance": "relevant",
                "frozen_collision": "false",
                "owner_url": "",
                "review_status": "manual_review",
                "final_decision": "keep",
            }
        )
    clean_fields = raw_fields[:3] + [
        "service_id",
        "intent",
        "relevance",
        "frozen_collision",
        "owner_url",
    ] + raw_fields[3:] + ["review_status", "final_decision"]
    _write_csv(processed_dir / "keywords_clean.csv", clean_fields, clean_rows)

    _write_csv(
        processed_dir / "minus_words.csv",
        ["scope", "service_id", "word", "reason", "source_query_ids", "status"],
        [
            {
                "scope": "global",
                "service_id": "",
                "word": "обучение",
                "reason": "training",
                "source_query_ids": "K0999",
                "status": "accepted",
            }
        ],
    )

    frozen_rows = [
        {
            "keyword_id": "K0009",
            "query_raw": "ремонт ливневой канализации",
            "query_normalized": "ремонт ливневой канализации",
            "service_id": "",
            "intent": "commercial_research",
            "relevance": "frozen_collision",
            "frozen_collision": "true",
            "owner_url": "https://exp76.ru/category/livnevaya-kanalizatsiya/",
            "impressions": "4",
            "clicks": "1",
            "ctr": "25",
            "review_status": "reviewed",
            "final_decision": "frozen_owner",
        }
    ]
    _write_csv(
        processed_dir / "frozen_collisions.csv",
        [
            "keyword_id",
            "query_raw",
            "query_normalized",
            "service_id",
            "intent",
            "relevance",
            "frozen_collision",
            "owner_url",
            "impressions",
            "clicks",
            "ctr",
            "review_status",
            "final_decision",
        ],
        frozen_rows,
    )

    serp_fields = [
        "query_id",
        "query",
        "service_id",
        "intent",
        "region",
        "device",
        "checked_at",
        "rank",
        "url",
        "canonical_url",
        "title",
        "source_file",
        "method",
    ]
    serp_queries = [
        (
            "Q000001",
            "ландшафтный дизайн ярославль",
            "S1",
            "commercial_research",
            [
                "https://example.test/same-1/",
                "https://example.test/same-2/",
                *(f"https://example.test/cross-{rank}/" for rank in range(1, 6)),
                *(f"https://example.test/q0001-{rank}/" for rank in range(8, 11)),
            ],
        ),
        (
            "Q000002",
            "проектирование участка ярославль",
            "S1",
            "commercial_research",
            [
                "https://example.test/same-1/",
                "https://example.test/same-2/",
                *(f"https://example.test/q0002-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000003",
            "планировка территории ярославль",
            "S5",
            "transactional",
            [
                *(f"https://example.test/cross-{rank}/" for rank in range(1, 6)),
                *(f"https://example.test/q0003-{rank}/" for rank in range(6, 11)),
            ],
        ),
        (
            "Q000004",
            "расчет стоимости благоустройства онлайн",
            "S1",
            "commercial_research",
            [
                "https://example.test/special-1/",
                "https://example.test/special-2/",
                *(f"https://example.test/q000004-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000005",
            "калькулятор стоимости работ",
            "S4",
            "transactional",
            [
                "https://example.test/special-1/",
                "https://example.test/special-2/",
                *(f"https://example.test/q000005-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000006",
            "газон купить",
            "S2",
            "product_only",
            [
                "https://example.test/exclusion-split-1/",
                "https://example.test/exclusion-split-2/",
                *(f"https://example.test/q000006-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000007",
            "укладка газона",
            "S2",
            "transactional",
            [
                "https://example.test/exclusion-split-1/",
                "https://example.test/exclusion-split-2/",
                *(f"https://example.test/q000007-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000008",
            "техника для участка купить",
            "S5",
            "product_only",
            [
                "https://example.test/shared-exclusion-1/",
                "https://example.test/shared-exclusion-2/",
                *(f"https://example.test/q000008-{rank}/" for rank in range(3, 11)),
            ],
        ),
        (
            "Q000009",
            "магазин техники для участка",
            "S5",
            "commercial_research",
            [
                "https://example.test/shared-exclusion-1/",
                "https://example.test/shared-exclusion-2/",
                *(f"https://example.test/q000009-{rank}/" for rank in range(3, 11)),
            ],
        ),
    ]
    serp_queries.extend(
        (
            f"Q{index:06d}",
            f"fixture query {index:03d}",
            "S1",
            "commercial_research",
            [f"https://example.test/q{index:06d}-{rank}/" for rank in range(1, 11)],
        )
        for index in range(10, 142)
    )
    serp_rows = []
    for query_id, query, service_id, intent, urls in serp_queries:
        for rank, url in enumerate(urls, start=1):
            serp_rows.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "service_id": service_id,
                    "intent": intent,
                    "region": "Ярославль",
                    "device": "desktop",
                    "checked_at": "2026-08-21T12:00:00+03:00",
                    "rank": str(rank),
                    "url": url,
                    "canonical_url": url,
                    "title": f"Результат {rank}",
                    "source_file": "fixture.jsonl",
                    "method": "live_yandex_organic",
                }
            )
    _write_csv(processed_dir / "serp_results.csv", serp_fields, serp_rows)

    def cluster_row(
        cluster_id: str,
        service_id: str,
        name: str,
        head_query: str,
        candidate_count: int,
        intent: str,
        target_url: str,
        url_action: str,
        validation_status: str,
        *,
        query_ids: str = "",
    ) -> dict[str, str]:
        return {
            "cluster_id": cluster_id,
            "service_id": service_id,
            "cluster_name": name,
            "head_query": head_query,
            "query_ids": query_ids,
            "candidate_count": str(candidate_count),
            "intent": intent,
            "webmaster_impressions": "16" if cluster_id == "C0001" else "0",
            "webmaster_clicks": "2" if cluster_id == "C0001" else "0",
            "serp_cohesion": "0.8",
            "target_url": target_url,
            "url_action": url_action,
            "priority": "P1",
            "confidence": "high",
            "validation_status": validation_status,
            "review_status": "reviewed",
        }

    clusters = [
        cluster_row(
            "C0001",
            "S1",
            "ландшафтное проектирование — commercial",
            "ландшафтный дизайн ярославль",
            2,
            "commercial_research",
            "https://exp76.ru/services/landshaftnoe-proektirovanie/",
            "keep_enhance",
            "verified",
            query_ids="K0001" + ("|K0009" if invalid else ""),
        ),
        cluster_row(
            "C0002",
            "S5",
            "планировка территории — transactional",
            "планировка территории ярославль",
            1,
            "transactional",
            "https://exp76.ru/services/planirovka-territorii/",
            "keep_enhance",
            "verified",
        ),
        cluster_row(
            "SPECIAL-CALCULATOR",
            "S1|S4",
            "калькулятор благоустройства",
            "расчет стоимости благоустройства онлайн",
            2,
            "mixed_manual",
            "https://exp76.ru/kalkulyator/",
            "keep_special_owner",
            "special_owner_reviewed",
        ),
        cluster_row(
            "EXCLUDE-SPLIT",
            "S2",
            "газон купить — product",
            "газон купить",
            1,
            "product_only",
            "",
            "exclude",
            "policy_exclusion_reviewed",
        ),
        cluster_row(
            "C0003",
            "S2",
            "укладка газона — transactional",
            "укладка газона",
            1,
            "transactional",
            "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
            "keep_enhance",
            "verified",
        ),
        cluster_row(
            "EXCLUDE-SHARED",
            "S5",
            "техника для участка — excluded",
            "техника для участка купить",
            2,
            "mixed_manual",
            "",
            "exclude",
            "policy_exclusion_reviewed",
        ),
    ]
    if invalid:
        clusters.append(
            cluster_row(
                "C0099",
                "S3",
                "посадка кустарников — commercial",
                "посадка кустарников ярославль",
                1,
                "commercial_research",
                "",
                "keep_enhance",
                "accepted",
            )
        )
    cluster_fields = list(clusters[0])
    _write_csv(processed_dir / "clusters.csv", cluster_fields, clusters)

    def url_row(map_id: str, cluster: dict[str, str]) -> dict[str, str]:
        return {
            "map_id": map_id,
            "cluster_id": cluster["cluster_id"],
            "service_id": cluster["service_id"],
            "cluster_name": cluster["cluster_name"],
            "intent": cluster["intent"],
            "current_url": cluster["target_url"],
            "target_url": cluster["target_url"],
            "url_action": cluster["url_action"],
            "validation_status": cluster["validation_status"],
            "confidence": cluster["confidence"],
            "review_status": cluster["review_status"],
        }

    url_rows = [url_row(f"M{index:04d}", cluster) for index, cluster in enumerate(clusters, 1)]
    if invalid:
        url_rows[0]["target_url"] = "https://exp76.ru/services/new-landscape/"
        url_rows[0]["url_action"] = "new_child_candidate"
        url_rows.append(
            {
                **url_rows[0],
                "map_id": "M0098",
                "target_url": "https://exp76.ru/services/another-owner/",
            }
        )
    _write_csv(processed_dir / "url_map.csv", list(url_rows[0]), url_rows)

    def candidate_row(
        service_id: str,
        query: str,
        intent: str,
        cluster_id: str,
        query_id: str,
        target_url: str,
        url_action: str,
    ) -> dict[str, str]:
        return {
            "candidate_key": f"{service_id}|{query}|{intent}",
            "service_id": service_id,
            "query": query,
            "intent": intent,
            "cluster_id": cluster_id,
            "representative_query_ids": query_id,
            "current_url": target_url,
            "target_url": target_url,
            "url_action": url_action,
            "assignment_method": "direct_serp_representative",
            "validation_status": "serp_direct_reviewed",
            "review_status": "reviewed",
            "reviewer": "fixture",
            "rationale": "fixture candidate",
        }

    candidate_rows = [
        candidate_row(
            "S1",
            "ландшафтный дизайн ярославль",
            "commercial_research",
            "C0001",
            "Q000001",
            "https://exp76.ru/services/landshaftnoe-proektirovanie/",
            "keep_enhance",
        ),
        candidate_row(
            "S1",
            "проектирование участка ярославль",
            "commercial_research",
            "C0001",
            "Q000002",
            "https://exp76.ru/services/landshaftnoe-proektirovanie/",
            "keep_enhance",
        ),
        candidate_row(
            "S5",
            "планировка территории ярославль",
            "transactional",
            "C0002",
            "Q000003",
            "https://exp76.ru/services/planirovka-territorii/",
            "keep_enhance",
        ),
        candidate_row(
            "S1",
            "расчет стоимости благоустройства онлайн",
            "commercial_research",
            "SPECIAL-CALCULATOR",
            "Q000004",
            "https://exp76.ru/kalkulyator/",
            "keep_special_owner",
        ),
        candidate_row(
            "S4",
            "калькулятор стоимости работ",
            "transactional",
            "SPECIAL-CALCULATOR",
            "Q000005",
            "https://exp76.ru/kalkulyator/",
            "keep_special_owner",
        ),
        candidate_row("S2", "газон купить", "product_only", "EXCLUDE-SPLIT", "Q000006", "", "exclude"),
        candidate_row(
            "S2",
            "укладка газона",
            "transactional",
            "C0003",
            "Q000007",
            "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
            "keep_enhance",
        ),
        candidate_row(
            "S5",
            "техника для участка купить",
            "product_only",
            "EXCLUDE-SHARED",
            "Q000008",
            "",
            "exclude",
        ),
        candidate_row(
            "S5",
            "магазин техники для участка",
            "commercial_research",
            "EXCLUDE-SHARED",
            "Q000009",
            "",
            "exclude",
        ),
    ]
    _write_csv(
        processed_dir / "candidate_cluster_map.csv",
        [
            "candidate_key",
            "service_id",
            "query",
            "intent",
            "cluster_id",
            "representative_query_ids",
            "current_url",
            "target_url",
            "url_action",
            "assignment_method",
            "validation_status",
            "review_status",
            "reviewer",
            "rationale",
        ],
        candidate_rows,
    )
    ambiguous_fields = [
        "pair_id",
        "left_query_id",
        "right_query_id",
        "left_query",
        "right_query",
        "left_service_id",
        "right_service_id",
        "left_intent",
        "right_intent",
        "overlap",
        "shared_urls",
        "decision",
        "owner_action",
        "validation_status",
        "review_status",
        "reviewer",
        "rationale",
    ]
    _write_csv(
        processed_dir / "serp_ambiguous_pairs.csv",
        ambiguous_fields,
        [
            {
                "pair_id": "PAIR-SAME",
                "left_query_id": "Q000001",
                "right_query_id": "Q000002",
                "left_query": "ландшафтный дизайн ярославль",
                "right_query": "проектирование участка ярославль",
                "left_service_id": "S1",
                "right_service_id": "S1",
                "left_intent": "commercial_research",
                "right_intent": "commercial_research",
                "overlap": "2",
                "shared_urls": "https://example.test/same-1/|https://example.test/same-2/",
                "decision": "manual_review",
                "owner_action": "hold_current_url",
                "validation_status": "serp_pair_pending_review",
                "review_status": "pending",
                "reviewer": "",
                "rationale": "same-service threshold fixture",
            },
            {
                "pair_id": "PAIR-CROSS",
                "left_query_id": "Q000001",
                "right_query_id": "Q000003",
                "left_query": "ландшафтный дизайн ярославль",
                "right_query": "планировка территории ярославль",
                "left_service_id": "S1",
                "right_service_id": "S5",
                "left_intent": "commercial_research",
                "right_intent": "transactional",
                "overlap": "5",
                "shared_urls": "|".join(
                    f"https://example.test/cross-{rank}/" for rank in range(1, 6)
                ),
                "decision": "owner_boundary_split",
                "owner_action": "hold_distinct_service_owners",
                "validation_status": "cross_service_owner_boundary_reviewed",
                "review_status": "reviewed",
                "reviewer": "policy_scope_owner",
                "rationale": "cross-service boundary fixture",
            },
            {
                "pair_id": "PAIR-SPECIAL",
                "left_query_id": "Q000004",
                "right_query_id": "Q000005",
                "left_query": "расчет стоимости благоустройства онлайн",
                "right_query": "калькулятор стоимости работ",
                "left_service_id": "S1",
                "right_service_id": "S4",
                "left_intent": "commercial_research",
                "right_intent": "transactional",
                "overlap": "2",
                "shared_urls": "https://example.test/special-1/|https://example.test/special-2/",
                "decision": "shared_special_owner",
                "owner_action": "hold_shared_special_owner",
                "validation_status": "shared_special_owner_reviewed",
                "review_status": "reviewed",
                "reviewer": "policy_special_owner",
                "rationale": "shared calculator owner fixture",
            },
            {
                "pair_id": "PAIR-EXCLUSION-SPLIT",
                "left_query_id": "Q000006",
                "right_query_id": "Q000007",
                "left_query": "газон купить",
                "right_query": "укладка газона",
                "left_service_id": "S2",
                "right_service_id": "S2",
                "left_intent": "product_only",
                "right_intent": "transactional",
                "overlap": "2",
                "shared_urls": (
                    "https://example.test/exclusion-split-1/|"
                    "https://example.test/exclusion-split-2/"
                ),
                "decision": "policy_exclusion_split",
                "owner_action": "retain_exclusion_and_service_assignment",
                "validation_status": "policy_exclusion_split_reviewed",
                "review_status": "reviewed",
                "reviewer": "policy_exclusion",
                "rationale": "one excluded assignment fixture",
            },
            {
                "pair_id": "PAIR-SHARED-EXCLUSION",
                "left_query_id": "Q000008",
                "right_query_id": "Q000009",
                "left_query": "техника для участка купить",
                "right_query": "магазин техники для участка",
                "left_service_id": "S5",
                "right_service_id": "S5",
                "left_intent": "product_only",
                "right_intent": "commercial_research",
                "overlap": "2",
                "shared_urls": (
                    "https://example.test/shared-exclusion-1/|"
                    "https://example.test/shared-exclusion-2/"
                ),
                "decision": "shared_policy_exclusion",
                "owner_action": "retain_shared_exclusion",
                "validation_status": "shared_policy_exclusion_reviewed",
                "review_status": "reviewed",
                "reviewer": "policy_exclusion",
                "rationale": "shared exclusion owner fixture",
            },
        ],
    )

    _write_csv(
        processed_dir / "content_briefs.csv",
        [
            "service_id",
            "target_url",
            "page_type",
            "source_cluster_ids",
            "primary_query",
            "secondary_queries",
            "title_intent",
            "h1_intent",
            "required_sections",
            "price_factors",
            "case_ids",
            "photo_ids",
            "internal_links",
            "frozen_links",
            "missing_facts",
            "status",
        ],
        [
            {
                "service_id": "S1",
                "target_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "page_type": "existing_service",
                "source_cluster_ids": "C0001",
                "primary_query": "ландшафтный дизайн ярославль",
                "secondary_queries": "проектирование участка ярославль",
                "title_intent": "Ландшафтное проектирование в Ярославле — цена",
                "h1_intent": "Ландшафтное проектирование участка",
                "required_sections": "цены|этапы|кейсы|FAQ",
                "price_factors": "площадь|состав проекта",
                "case_ids": "case-42",
                "photo_ids": "photo-101|photo-102",
                "internal_links": "https://exp76.ru/services/ukhod-za-sadom/",
                "frozen_links": "https://exp76.ru/category/drenazh-uchastka/",
                "missing_facts": "срок выезда специалиста",
                "status": "draft",
            }
        ],
    )
    _write_csv(
        processed_dir / "launch_monitoring.csv",
        [
            "cluster_id",
            "target_url",
            "launch_date",
            "baseline_28d_impressions",
            "baseline_clicks",
            "baseline_ctr",
            "baseline_position",
            "day_7",
            "day_14",
            "day_30",
            "day_60",
            "day_90",
            "leads",
            "calls",
            "decision",
        ],
        [
            {
                "cluster_id": "C0001",
                "target_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                "launch_date": "2026-09-01",
                "baseline_28d_impressions": "147",
                "baseline_clicks": "13",
                "baseline_ctr": "8.84",
                "baseline_position": "12.3",
                "day_7": "не начато",
                "day_14": "не начато",
                "day_30": "не начато",
                "day_60": "не начато",
                "day_90": "не начато",
                "leads": "",
                "calls": "",
                "decision": "Без публикации на текущем этапе",
            }
        ],
    )
    _write_csv(
        processed_dir / "qa_log.csv",
        ["check_id", "cluster_id", "check", "status", "evidence", "issue", "resolution"],
        [
            {
                "check_id": "QA0001",
                "cluster_id": "C0001",
                "check": "frozen owner protected",
                "status": "passed",
                "evidence": "scope contract",
                "issue": "",
                "resolution": "",
            }
        ],
    )


def _sheet_xml_by_name(archive: zipfile.ZipFile) -> dict[str, ET.Element]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    sheets = {}
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        relation_id = sheet.attrib[f"{{{REL_NS}}}id"]
        target = targets[relation_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        sheets[sheet.attrib["name"]] = ET.fromstring(archive.read(target))
    return sheets


def _cell(sheet: ET.Element, reference: str) -> ET.Element:
    cell = sheet.find(f".//{{{MAIN_NS}}}c[@r='{reference}']")
    if cell is None:
        raise AssertionError(f"missing cell {reference}")
    return cell


def _remove_sheet_declaration(source: Path, target: Path, sheet_name: str) -> None:
    """Corrupt only the workbook catalog to exercise missing-sheet QA."""
    removed = False
    with zipfile.ZipFile(source) as input_archive, zipfile.ZipFile(target, "w") as output_archive:
        for item in input_archive.infolist():
            data = input_archive.read(item.filename)
            if item.filename == "xl/workbook.xml":
                workbook = ET.fromstring(data)
                sheets = workbook.find(f"{{{MAIN_NS}}}sheets")
                if sheets is None:
                    raise AssertionError("workbook has no sheets catalog")
                for sheet in list(sheets):
                    if sheet.attrib.get("name") == sheet_name:
                        sheets.remove(sheet)
                        removed = True
                        break
                data = ET.tostring(workbook, encoding="utf-8", xml_declaration=True)
            output_archive.writestr(item, data)
    if not removed:
        raise AssertionError(f"sheet not found in test workbook: {sheet_name}")


class SemanticWorkbookTest(unittest.TestCase):
    def test_artifact_runtime_retries_a_blank_transient_exit(self):
        import tools.seo_semantics.workbook as workbook_module

        transient = subprocess.CompletedProcess(
            args=["node"],
            returncode=3221225477,
            stdout="",
            stderr="",
        )
        success = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout="VALIDATION_JSON:[]\n",
            stderr="",
        )
        with (
            patch.object(workbook_module, "_require_runtime"),
            patch.object(workbook_module, "_create_module_junction"),
            patch.object(workbook_module.shutil, "copy2"),
            patch.object(workbook_module.subprocess, "run", side_effect=[transient, success]) as run,
        ):
            output = workbook_module._run_node("validate", "--input", "fixture.xlsx")

        self.assertEqual(output, "VALIDATION_JSON:[]\n")
        self.assertEqual(run.call_count, 2)

    def test_artifact_runtime_preserves_stdout_when_stderr_is_whitespace(self):
        import tools.seo_semantics.workbook as workbook_module

        failure = subprocess.CompletedProcess(
            args=["node"],
            returncode=9,
            stdout="real diagnostic\n",
            stderr=" \n",
        )
        with (
            patch.object(workbook_module, "_require_runtime"),
            patch.object(workbook_module, "_create_module_junction"),
            patch.object(workbook_module.shutil, "copy2"),
            patch.object(workbook_module.subprocess, "run", return_value=failure) as run,
        ):
            with self.assertRaisesRegex(RuntimeError, r"exit 9.*real diagnostic"):
                workbook_module._run_node("validate", "--input", "fixture.xlsx")

        self.assertEqual(run.call_count, 1)

    def test_processed_data_fixture_passes_generic_invariants(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)

            self.assertEqual(validate_processed_data(processed_dir), [])

    def test_processed_data_rejects_content_brief_cluster_from_another_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            brief_path = processed_dir / "content_briefs.csv"
            fields, rows = _read_csv(brief_path)
            rows[0]["source_cluster_ids"] = "C0002"
            _write_csv(brief_path, fields, rows)

            errors = validate_processed_data(processed_dir)

            self.assertIn("content_brief_source_service_mismatch:S1:C0002:S5", errors)
            self.assertIn("content_brief_source_target_mismatch:S1:C0002", errors)

    def test_processed_data_rejects_non_service_content_brief_source_cluster(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            brief_path = processed_dir / "content_briefs.csv"
            fields, rows = _read_csv(brief_path)
            rows[0]["source_cluster_ids"] = "EXCLUDE-SPLIT"
            _write_csv(brief_path, fields, rows)

            self.assertIn(
                "content_brief_source_action:S1:EXCLUDE-SPLIT:exclude",
                validate_processed_data(processed_dir),
            )

    def test_processed_data_rejects_untraceable_content_brief_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            brief_path = processed_dir / "content_briefs.csv"
            fields, rows = _read_csv(brief_path)
            rows[0]["primary_query"] = "придуманный запрос"
            rows[0]["secondary_queries"] = "планировка территории ярославль"
            _write_csv(brief_path, fields, rows)

            errors = validate_processed_data(processed_dir)

            self.assertIn(
                "content_brief_query_missing:S1:primary_query:придуманный запрос",
                errors,
            )
            self.assertIn(
                "content_brief_query_outside_sources:S1:secondary_queries:планировка территории ярославль",
                errors,
            )

    def test_processed_data_requires_content_brief_candidate_provenance_columns(self):
        for missing_field in ("assignment_method", "validation_status", "review_status"):
            with self.subTest(missing_field=missing_field), tempfile.TemporaryDirectory() as tmp:
                processed_dir = Path(tmp) / "processed"
                _write_fixture(processed_dir)
                candidate_path = processed_dir / "candidate_cluster_map.csv"
                fields, rows = _read_csv(candidate_path)
                fields.remove(missing_field)
                for row in rows:
                    row.pop(missing_field)
                _write_csv(candidate_path, fields, rows)

                self.assertIn(
                    f"missing_processed_columns:candidate_cluster_map.csv:{missing_field}",
                    validate_processed_data(processed_dir),
                )

    def test_processed_data_rejects_non_reviewed_direct_content_brief_candidate(self):
        mutations = (
            ("assignment_method", "representative_stratum_projection"),
            ("validation_status", "manual_projection_pending"),
            ("review_status", "pending"),
        )
        for field, value in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                processed_dir = Path(tmp) / "processed"
                _write_fixture(processed_dir)
                candidate_path = processed_dir / "candidate_cluster_map.csv"
                fields, rows = _read_csv(candidate_path)
                candidate = next(
                    row
                    for row in rows
                    if row["candidate_key"]
                    == "S1|ландшафтный дизайн ярославль|commercial_research"
                )
                candidate[field] = value
                _write_csv(candidate_path, fields, rows)

                self.assertIn(
                    "content_brief_query_outside_sources:"
                    "S1:primary_query:ландшафтный дизайн ярославль",
                    validate_processed_data(processed_dir),
                )

    def test_processed_data_reports_serp_owner_and_exact_once_breaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)

            serp_path = processed_dir / "serp_results.csv"
            serp_fields, serp_rows = _read_csv(serp_path)
            next(
                row
                for row in serp_rows
                if row["query_id"] == "Q000001" and row["rank"] == "10"
            )["rank"] = "9"
            _write_csv(serp_path, serp_fields, serp_rows)

            url_map_path = processed_dir / "url_map.csv"
            url_fields, url_rows = _read_csv(url_map_path)
            url_rows[0]["cluster_id"] = "C9999"
            url_rows[0]["url_action"] = "owner_conflict"
            _write_csv(url_map_path, url_fields, url_rows)

            candidate_path = processed_dir / "candidate_cluster_map.csv"
            candidate_fields, candidate_rows = _read_csv(candidate_path)
            candidate_rows.append(dict(candidate_rows[0]))
            _write_csv(candidate_path, candidate_fields, candidate_rows)

            errors = validate_processed_data(processed_dir)

            self.assertIn("serp_rank_contract:Q000001", errors)
            self.assertIn("cluster_id_missing_from_url_map:C0001", errors)
            self.assertIn("cluster_id_missing_from_clusters:C9999", errors)
            self.assertIn("forbidden_url_action:url_map.csv:C9999:owner_conflict", errors)
            self.assertIn("owner_conflict:url_map.csv:C9999", errors)
            self.assertIn(
                "duplicate_candidate_key:S1|ландшафтный дизайн ярославль|commercial_research",
                errors,
            )
            self.assertIn("candidate_count_mismatch:C0001:expected=2:actual=3", errors)

    def test_processed_data_rejects_serp_coverage_and_result_contract_breaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            serp_path = processed_dir / "serp_results.csv"
            fields, rows = _read_csv(serp_path)
            rows = [row for row in rows if row["query_id"] != "Q000141"]
            next(
                row
                for row in rows
                if row["query_id"] == "Q000004" and row["rank"] == "1"
            )["title"] = ""
            invalid_url = next(
                row
                for row in rows
                if row["query_id"] == "Q000005" and row["rank"] == "1"
            )
            invalid_url["url"] = "ftp://example.test/not-organic"
            invalid_url["canonical_url"] = "ftp://example.test/not-organic"
            tracking_url = next(
                row
                for row in rows
                if row["query_id"] == "Q000006" and row["rank"] == "1"
            )
            tracking_url["url"] = "https://yandex.ru/an/count/unsafe"
            tracking_url["canonical_url"] = "https://yandex.ru/an/count/unsafe/"
            canonical_mismatch = next(
                row
                for row in rows
                if row["query_id"] == "Q000007" and row["rank"] == "1"
            )
            canonical_mismatch["url"] = "http://WWW.Example.test/path//to/page/?utm=fixture"
            _write_csv(serp_path, fields, rows)

            errors = validate_processed_data(processed_dir)

            self.assertIn("serp_row_count:expected=1410:actual=1400", errors)
            self.assertIn(
                "serp_query_id_coverage:missing=Q000141:extra=none",
                errors,
            )
            self.assertIn("serp_missing_title:Q000004:1", errors)
            self.assertIn("serp_invalid_url:Q000005:1", errors)
            self.assertIn("serp_ad_tracking_url:Q000006:1", errors)
            self.assertIn("serp_canonical_mismatch:Q000007:1", errors)

    def test_processed_data_rejects_cluster_url_map_field_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            url_map_path = processed_dir / "url_map.csv"
            fields, rows = _read_csv(url_map_path)
            rows[0]["confidence"] = "medium"
            _write_csv(url_map_path, fields, rows)

            self.assertIn(
                "cluster_url_map_mismatch:C0001:confidence",
                validate_processed_data(processed_dir),
            )

    def test_processed_data_rejects_an_invalid_ambiguous_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            ambiguous_path = processed_dir / "serp_ambiguous_pairs.csv"
            fields, rows = _read_csv(ambiguous_path)
            rows[1]["owner_action"] = "hold_current_url"
            _write_csv(ambiguous_path, fields, rows)

            self.assertIn(
                "invalid_serp_ambiguous_pair:PAIR-CROSS:policy_fields",
                validate_processed_data(processed_dir),
            )

    def test_processed_data_rejects_policy_not_backed_by_candidate_assignments(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            ambiguous_path = processed_dir / "serp_ambiguous_pairs.csv"
            fields, rows = _read_csv(ambiguous_path)
            rows[1].update(
                {
                    "decision": "shared_special_owner",
                    "owner_action": "hold_shared_special_owner",
                    "validation_status": "shared_special_owner_reviewed",
                    "review_status": "reviewed",
                    "reviewer": "policy_special_owner",
                }
            )
            _write_csv(ambiguous_path, fields, rows)

            self.assertIn(
                "invalid_serp_ambiguous_pair:PAIR-CROSS:assignment_policy",
                validate_processed_data(processed_dir),
            )

    def test_processed_data_rejects_unsafe_pending_serp_cluster_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp) / "processed"
            _write_fixture(processed_dir)
            cluster_path = processed_dir / "clusters.csv"
            fields, rows = _read_csv(cluster_path)
            rows[0].update(
                {
                    "url_action": "article_candidate",
                    "validation_status": "serp_direct_reviewed|serp_pair_pending_review",
                    "review_status": "pending",
                }
            )
            _write_csv(cluster_path, fields, rows)

            self.assertIn(
                "invalid_pending_serp_cluster:C0001",
                validate_processed_data(processed_dir),
            )

    def test_real_processed_core_has_pinned_cardinality_and_actions(self):
        _, serp_rows = _read_csv(REAL_PROCESSED / "serp_results.csv")
        _, cluster_rows = _read_csv(REAL_PROCESSED / "clusters.csv")
        _, url_rows = _read_csv(REAL_PROCESSED / "url_map.csv")
        _, candidate_rows = _read_csv(REAL_PROCESSED / "candidate_cluster_map.csv")
        _, ambiguous_rows = _read_csv(REAL_PROCESSED / "serp_ambiguous_pairs.csv")
        brief_fields, brief_rows = _read_csv(REAL_PROCESSED / "content_briefs.csv")

        self.assertEqual(len({row["query_id"] for row in serp_rows}), 141)
        self.assertEqual(len(serp_rows), 1410)
        self.assertEqual(len(cluster_rows), 164)
        self.assertEqual(len(url_rows), 164)
        self.assertEqual(len(candidate_rows), 4236)
        self.assertEqual(len({row["candidate_key"] for row in candidate_rows}), 4236)
        self.assertEqual(len(brief_rows), 35)
        self.assertEqual(len({row["destination_id"] for row in brief_rows}), 35)
        self.assertEqual(brief_fields, list(CONTENT_BRIEF_COLUMNS))
        self.assertEqual(
            Counter(row["url_action"] for row in candidate_rows),
            Counter(
                {
                    "article_candidate": 225,
                    "exclude": 202,
                    "unresolved": 3781,
                    "keep_enhance": 5,
                    "keep_special_owner": 23,
                }
            ),
        )
        expected_cluster_actions = Counter(
            {
                "merge": 106,
                "article": 13,
                "exclude": 23,
                "hub": 8,
                "frozen": 6,
                "child": 5,
                "special": 3,
            }
        )
        self.assertEqual(
            Counter(row["url_action"] for row in cluster_rows),
            expected_cluster_actions,
        )
        self.assertEqual(
            Counter(row["url_action"] for row in url_rows),
            expected_cluster_actions,
        )
        self.assertEqual(len(ambiguous_rows), 1044)
        self.assertEqual(
            Counter(row["decision"] for row in ambiguous_rows),
            Counter(
                {
                    "manual_review": 263,
                    "owner_boundary_split": 747,
                    "shared_special_owner": 5,
                    "policy_exclusion_split": 24,
                    "shared_policy_exclusion": 5,
                }
            ),
        )
        self.assertEqual(
            Counter(row["review_status"] for row in cluster_rows),
            Counter({"reviewed": 164}),
        )
        pending_serp_clusters = [
            row
            for row in cluster_rows
            if "serp_pair_pending_review" in row["validation_status"].split("|")
        ]
        self.assertEqual(len(pending_serp_clusters), 0)
        self.assertEqual(validate_processed_data(REAL_PROCESSED), [])

    def test_validation_reports_missing_sheet_even_with_source_comparison(self):
        """Catches source comparison dereferencing a sheet already reported as missing."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            complete = root / "complete.xlsx"
            incomplete = root / "incomplete.xlsx"
            _write_fixture(processed_dir)
            build_workbook(processed_dir, complete)
            _remove_sheet_declaration(complete, incomplete, "qa_log")

            self.assertEqual(
                validate_workbook(incomplete, processed_dir),
                ["missing_sheet:qa_log"],
            )

    def test_export_and_qa_cli_pass_on_the_real_semantic_core(self):
        """Catches CLI drift and real-data owner/click/frozen validation gaps."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "semantic.xlsx"

            export_result = main(
                [
                    "export",
                    "--processed-dir",
                    str(REAL_PROCESSED),
                    "--output",
                    str(output),
                ]
            )
            qa_result = main(
                [
                    "qa",
                    "--scope",
                    str(REAL_SCOPE),
                    "--processed-dir",
                    str(REAL_PROCESSED),
                    "--workbook",
                    str(output),
                ]
            )

            self.assertEqual(export_result, 0)
            self.assertEqual(qa_result, 0)

    def test_qa_cli_rejects_a_workbook_built_from_stale_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "semantic.xlsx"
            _write_fixture(processed_dir)
            build_workbook(processed_dir, output)
            self.assertEqual(validate_workbook(output, processed_dir), [])
            qa_log = processed_dir / "qa_log.csv"
            qa_log.write_text(
                qa_log.read_text(encoding="utf-8") + "QA999,,new check,passed,new evidence,,\n",
                encoding="utf-8",
            )

            result = main(
                [
                    "qa",
                    "--scope",
                    str(REAL_SCOPE),
                    "--processed-dir",
                    str(processed_dir),
                    "--workbook",
                    str(output),
                ]
            )

            self.assertEqual(result, 4)

    def test_qa_cli_requires_the_non_workbook_ambiguous_pairs_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "semantic.xlsx"
            _write_fixture(processed_dir)
            build_workbook(processed_dir, output)
            (processed_dir / "serp_ambiguous_pairs.csv").unlink()

            result = main(
                [
                    "qa",
                    "--scope",
                    str(REAL_SCOPE),
                    "--processed-dir",
                    str(processed_dir),
                    "--workbook",
                    str(output),
                ]
            )

            self.assertEqual(result, 2)

    def test_qa_cli_rejects_invalid_processed_serp_even_when_workbook_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "semantic.xlsx"
            _write_fixture(processed_dir)
            serp_path = processed_dir / "serp_results.csv"
            fields, rows = _read_csv(serp_path)
            next(
                row
                for row in rows
                if row["query_id"] == "Q000001" and row["rank"] == "10"
            )["rank"] = "9"
            _write_csv(serp_path, fields, rows)
            build_workbook(processed_dir, output)

            result = main(
                [
                    "qa",
                    "--scope",
                    str(REAL_SCOPE),
                    "--processed-dir",
                    str(processed_dir),
                    "--workbook",
                    str(output),
                ]
            )

            self.assertEqual(result, 4)

    def test_builds_exact_styled_sheet_contract_with_typed_values(self):
        """Catches omitted sheets, broken navigation, string metrics and lost visual controls."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "semantic.xlsx"
            _write_fixture(processed_dir)

            build_workbook(processed_dir, output)

            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                sheets = _sheet_xml_by_name(archive)
                self.assertEqual(tuple(sheets), SHEET_NAMES)
                table_xml = [
                    ET.fromstring(archive.read(name))
                    for name in archive.namelist()
                    if name.startswith("xl/tables/table") and name.endswith(".xml")
                ]
                self.assertEqual(len(table_xml), len(SHEET_NAMES))
                self.assertTrue(
                    all(table.find(f"{{{MAIN_NS}}}autoFilter") is not None for table in table_xml)
                )
                for sheet in sheets.values():
                    # artifact-tool 2.8.6 currently drops its documented freezeRows
                    # state on XLSX export; the runtime limitation is reported separately.
                    self.assertIsNotNone(sheet.find(f"{{{MAIN_NS}}}sheetViews"))
                    widths = [
                        float(column.attrib["width"])
                        for column in sheet.findall(f".//{{{MAIN_NS}}}col")
                        if "width" in column.attrib
                    ]
                    self.assertTrue(widths)
                    self.assertLessEqual(max(widths), 60.0)

                styles = archive.read("xl/styles.xml").decode("utf-8")
                self.assertIn("FF14532D", styles)
                self.assertIn("FFFFC7CE", styles)
                self.assertIn("FFFFEB9C", styles)
                self.assertIn("FFC6EFCE", styles)
                self.assertIn("conditionalFormatting", archive.read("xl/worksheets/sheet3.xml").decode("utf-8"))
                self.assertIn("conditionalFormatting", archive.read("xl/worksheets/sheet5.xml").decode("utf-8"))
                self.assertIn("conditionalFormatting", archive.read("xl/worksheets/sheet7.xml").decode("utf-8"))

                raw_sheet = sheets["keywords_raw"]
                ctr_cell = _cell(raw_sheet, "G2")
                self.assertNotIn(ctr_cell.attrib.get("t"), {"inlineStr", "s", "str"})
                self.assertAlmostEqual(float(ctr_cell.find(f"{{{MAIN_NS}}}v").text), 0.125)
                collected_cell = _cell(raw_sheet, "I2")
                self.assertNotIn(collected_cell.attrib.get("t"), {"inlineStr", "s", "str"})
                collected_value = float(collected_cell.find(f"{{{MAIN_NS}}}v").text)
                collected_at = datetime(1899, 12, 30) + timedelta(days=collected_value)
                self.assertEqual(collected_at, datetime(2026, 8, 20, 18, 17, 52))

                url_sheet = sheets["url_map"]
                url_cell = _cell(url_sheet, "G2")
                self.assertNotEqual(url_cell.attrib.get("t"), "e")
                self.assertEqual(
                    url_cell.find(f"{{{MAIN_NS}}}v").text,
                    "https://exp76.ru/services/landshaftnoe-proektirovanie/",
                )

                launch_sheet = sheets["launch_monitoring"]
                launch_date_cell = _cell(launch_sheet, "C2")
                self.assertNotIn(launch_date_cell.attrib.get("t"), {"inlineStr", "s", "str"})
                launch_date_value = float(launch_date_cell.find(f"{{{MAIN_NS}}}v").text)
                launch_date = datetime(1899, 12, 30) + timedelta(days=launch_date_value)
                self.assertEqual(launch_date, datetime(2026, 9, 1))
                self.assertEqual(
                    _cell(launch_sheet, "H2").find(f"{{{MAIN_NS}}}v").text,
                    "не начато",
                )

                self.assertFalse(any(name.startswith("xl/externalLinks/") for name in archive.namelist()))
                package_text = "\n".join(
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.endswith((".xml", ".rels"))
                ).lower()
                self.assertNotIn("api_key", package_text)
                self.assertNotIn("authorization: bearer", package_text)

            self.assertEqual(validate_workbook(output), [])

    def test_renders_every_contractual_sheet_for_visual_review(self):
        """Catches a renderer that silently omits a sheet or writes an empty preview."""
        from tools.seo_semantics.workbook import render_workbook

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "semantic.xlsx"
            preview_dir = root / "previews"
            _write_fixture(processed_dir)
            build_workbook(processed_dir, output)

            previews = render_workbook(output, preview_dir)

            self.assertEqual(
                [path.name for path in previews],
                [f"{index:02d}-{name}.png" for index, name in enumerate(SHEET_NAMES, start=1)],
            )
            self.assertTrue(all(path.is_file() and path.stat().st_size > 100 for path in previews))

    def test_validation_reports_owner_click_and_frozen_breaks(self):
        """Catches ambiguous ownership, orphan clicks and reassigned protected queries."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "invalid.xlsx"
            _write_fixture(processed_dir, invalid=True)
            build_workbook(processed_dir, output)

            self.assertEqual(
                validate_workbook(output),
                [
                    "blank_target_url:C0099",
                    "clicked_query_without_cluster:K0002",
                    "duplicate_cluster_owner:C0001",
                    "frozen_collision_assigned_new_url:K0009",
                ],
            )

    def test_build_rejects_missing_csv_before_partial_export(self):
        """Catches silent delivery of a workbook with a missing contractual sheet."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            processed_dir = root / "processed"
            output = root / "partial.xlsx"
            _write_fixture(processed_dir)
            (processed_dir / "qa_log.csv").unlink()

            with self.assertRaisesRegex(ValueError, "missing CSV files: qa_log.csv"):
                build_workbook(processed_dir, output)
            self.assertFalse(output.exists())

    def test_workbook_runtime_configuration_is_not_bound_to_one_user_profile(self):
        import tools.seo_semantics.workbook as workbook_module

        source = Path(workbook_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn(r"C:\Users\user", source)


if __name__ == "__main__":
    unittest.main()
