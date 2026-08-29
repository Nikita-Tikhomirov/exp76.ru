"""Build the superseding S1-S15 child-service architecture.

The first eight hubs come from the reviewed production architecture. The
remaining seven reuse the exact live WordPress owners audited in August 2026.
WP 6870 is deliberately promoted from the former S5 stump child to the S9 hub,
so the combined export has one owner and one search intent for that URL.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

from .final_service_architecture import (
    CSV_COLUMNS,
    HUB_METADATA as REVIEWED_HUB_METADATA,
    build_final_service_rows,
)
from .legacy_service_architecture import (
    LEGACY_CHILDREN,
    LEGACY_HUB_OWNERS,
    LEGACY_SERVICE_ORDER,
    build_legacy_service_rows,
)


COMPLETE_SERVICE_ORDER = tuple(f"S{number}" for number in range(1, 16))
OBSOLETE_DESTINATION_IDS = frozenset({"S5-CHILD-STUMPS"})
EXPECTED_REUSED_CHILD_IDS = frozenset({"S7-CHILD-HOLIDAY"})

_REVIEWED_COUNTS = {
    "S1": 5,
    "S2": 4,
    "S3": 5,
    "S4": 5,
    "S5": 5,
    "S6": 3,
    "S7": 5,
    "S8": 4,
}
_LEGACY_COUNTS = {
    service_id: len(LEGACY_CHILDREN[service_id])
    for service_id in LEGACY_SERVICE_ORDER
}
COMPLETE_CHILD_COUNTS: Mapping[str, int] = MappingProxyType(
    {**_REVIEWED_COUNTS, **_LEGACY_COUNTS}
)

COMPLETE_HUB_METADATA: Mapping[str, tuple[str, str, str]] = MappingProxyType(
    {
        **{
            service_id: (title, url, "")
            for service_id, (title, url) in REVIEWED_HUB_METADATA.items()
        },
        **{
            service_id: (
                LEGACY_HUB_OWNERS[service_id].title,
                LEGACY_HUB_OWNERS[service_id].current_url,
                str(LEGACY_HUB_OWNERS[service_id].current_wp_id),
            )
            for service_id in LEGACY_SERVICE_ORDER
        },
    }
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DATA_ROOT = _REPOSITORY_ROOT / "seo-data" / "2026-08-exp76-services"
DEFAULT_CSV_PATH = _DATA_ROOT / "processed" / "complete_service_children.csv"
DEFAULT_MARKDOWN_PATH = _DATA_ROOT / "reviews" / "complete_service_structure.md"
_LEGACY_SUGGEST_PATH = (
    "seo-data/2026-08-exp76-services/processed/legacy_suggestion_candidates_v2.csv"
)


def _legacy_child_rows() -> list[dict[str, str]]:
    """Map audited S9-S15 children into the production child CSV contract."""

    rows: list[dict[str, str]] = []
    for source in build_legacy_service_rows():
        if source["page_role"] != "child_service":
            continue
        row = {column: "" for column in CSV_COLUMNS}
        for column in row:
            if column in source:
                row[column] = source[column]
        service_id = source["service_id"]
        row.update(
            {
                "parent_hub": f"{service_id}-HUB",
                "parent_hub_url": LEGACY_HUB_OWNERS[service_id].current_url,
                "target_template": "newservicepost.php",
                "semantic_evidence": (
                    f"yandex_suggest:{_LEGACY_SUGGEST_PATH}"
                    f"#destination_id={source['destination_id']};verified=2026-08-29"
                ),
                "publication_status": "ready",
            }
        )
        rows.append(row)
    return rows


def validate_complete_service_rows(
    rows: Sequence[Mapping[str, str]],
) -> list[str]:
    """Fail closed when ownership, counts or publish routing drift."""

    errors: list[str] = []
    ids = [row.get("destination_id", "") for row in rows]
    urls = [row.get("target_url", "") for row in rows]
    if len(rows) != sum(COMPLETE_CHILD_COUNTS.values()):
        errors.append("complete child count differs")
    if len(ids) != len(set(ids)) or "" in ids:
        errors.append("destination ids must be non-blank and unique")
    if len(urls) != len(set(urls)) or "" in urls:
        errors.append("target urls must be non-blank and unique")
    if OBSOLETE_DESTINATION_IDS.intersection(ids):
        errors.append("obsolete S5 stump child remains")

    counts = Counter(row.get("service_id", "") for row in rows)
    if dict(counts) != dict(COMPLETE_CHILD_COUNTS):
        errors.append("per-hub child counts differ")

    reused = {
        row.get("destination_id", "")
        for row in rows
        if row.get("url_action") == "reuse"
    }
    if reused != EXPECTED_REUSED_CHILD_IDS:
        errors.append("reused child ownership differs")

    for row in rows:
        service_id = row.get("service_id", "")
        if service_id not in COMPLETE_HUB_METADATA:
            errors.append(f"unknown service id: {service_id!r}")
            continue
        _, hub_url, _ = COMPLETE_HUB_METADATA[service_id]
        if row.get("parent_hub") != f"{service_id}-HUB":
            errors.append(f"parent hub differs: {row.get('destination_id', '')}")
        if row.get("parent_hub_url") != hub_url:
            errors.append(f"parent hub url differs: {row.get('destination_id', '')}")
        if row.get("publication_status") != "ready":
            errors.append(
                f"child is not architecture-ready: {row.get('destination_id', '')}"
            )
        if row.get("url_action") == "create" and row.get("target_template") not in {
            "",
            "newservicepost.php",
        }:
            errors.append(f"new child template differs: {row.get('destination_id', '')}")

    holiday = next(
        (row for row in rows if row.get("destination_id") == "S7-CHILD-HOLIDAY"),
        None,
    )
    if not holiday or holiday.get("current_wp_id") != "10381":
        errors.append("seasonal S7 child owner differs")
    return errors


def build_complete_service_rows() -> list[dict[str, str]]:
    """Return the authoritative 65-child architecture in service order."""

    reviewed_rows = [
        dict(row)
        for row in build_final_service_rows()
        if row["destination_id"] not in OBSOLETE_DESTINATION_IDS
    ]
    for row in reviewed_rows:
        if row["url_action"] == "create" and not row["target_template"]:
            row["target_template"] = "newservicepost.php"
    combined = reviewed_rows + _legacy_child_rows()
    service_position = {
        service_id: position
        for position, service_id in enumerate(COMPLETE_SERVICE_ORDER)
    }
    combined.sort(key=lambda row: service_position[row["service_id"]])
    errors = validate_complete_service_rows(combined)
    if errors:
        raise ValueError("; ".join(errors))
    return combined


def render_complete_service_structure() -> str:
    """Render the same architecture for human review."""

    rows = build_complete_service_rows()
    lines = [
        "# Полная структура услуг EXP76",
        "",
        "Этот документ заменяет прежнее деление на готовые и отложенные направления.",
        "Все 15 опубликованных услуг являются хабами; WP 6870 больше не считается дочерней страницей S5.",
        "",
        "Всего хабов: **15**.",
        f"Всего дочерних услуг: **{len(rows)}**.",
        "",
    ]
    for service_id in COMPLETE_SERVICE_ORDER:
        title, hub_url, owner_wp_id = COMPLETE_HUB_METADATA[service_id]
        service_rows = [row for row in rows if row["service_id"] == service_id]
        lines.extend([f"## {service_id} — {title}", ""])
        owner_note = f", WP {owner_wp_id}" if owner_wp_id else ""
        lines.extend(
            [
                f"- Хаб: [{hub_url}]({hub_url}){owner_note}",
                f"- Дочерних услуг: **{len(service_rows)}**",
                "",
            ]
        )
        for row in service_rows:
            action = (
                f"reuse WP {row['current_wp_id']}"
                if row["url_action"] == "reuse"
                else "create"
            )
            lines.append(
                f"- **{row['title']}** — {row['destination_id']}; "
                f"[{row['target_url']}]({row['target_url']}); {action}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_complete_service_architecture(
    csv_path: Path = DEFAULT_CSV_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
) -> int:
    """Write deterministic UTF-8 CSV and Markdown artifacts."""

    rows = build_complete_service_rows()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_complete_service_structure())
    return len(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the complete EXP76 architecture.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN_PATH)
    args = parser.parse_args(argv)
    count = write_complete_service_architecture(args.csv, args.markdown)
    print(f"Exported {count} complete child services.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
