"""Export the reviewed production child architecture to stable artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Mapping, Sequence

from .expanded_architecture import ExpandedPage
from .reviewed_service_architecture import (
    REVIEWED_CHILDREN,
    REUSE_DEPLOYMENT_REQUIREMENTS,
    SERVICE_ORDER,
    SPARSE_HUB_JUSTIFICATIONS,
    URL_DECISIONS,
    UrlDecision,
    validate_reviewed_child_architecture,
)


CSV_COLUMNS = (
    "destination_id",
    "service_id",
    "title",
    "slug",
    "query",
    "parent_hub",
    "parent_hub_url",
    "current_url",
    "target_url",
    "url_action",
    "current_wp_id",
    "current_post_type",
    "target_template",
    "excluded_primary_intents",
    "business_evidence",
    "semantic_evidence",
    "boundary",
    "publication_status",
)

HUB_METADATA: Mapping[str, tuple[str, str]] = {
    "S1": (
        "Ландшафтное проектирование",
        "https://exp76.ru/services/landshaftnoe-proektirovanie/",
    ),
    "S2": (
        "Газон посевной и рулонный",
        "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
    ),
    "S3": (
        "Посадка деревьев и кустарников",
        "https://exp76.ru/services/posadka-derevev-i-kustarnikov/",
    ),
    "S4": (
        "Уход за садом",
        "https://exp76.ru/services/ukhod-za-sadom/",
    ),
    "S5": (
        "Планировка территории",
        "https://exp76.ru/services/planirovka-territorii/",
    ),
    "S6": (
        "Подпорные стенки",
        "https://exp76.ru/services/podpornye-stenki/",
    ),
    "S7": (
        "Уличное и ландшафтное освещение",
        "https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/",
    ),
    "S8": (
        "Въезд через канаву",
        "https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/",
    ),
}

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = (
    _REPOSITORY_ROOT
    / "seo-data"
    / "2026-08-exp76-services"
    / "processed"
    / "final_service_children.csv"
)
DEFAULT_MARKDOWN_PATH = (
    _REPOSITORY_ROOT
    / "seo-data"
    / "2026-08-exp76-services"
    / "reviews"
    / "final_service_structure.md"
)


def build_final_service_rows(
    children: Mapping[str, Sequence[ExpandedPage]] = REVIEWED_CHILDREN,
    *,
    url_decisions: Mapping[str, UrlDecision] = URL_DECISIONS,
) -> list[dict[str, str]]:
    """Build one publication-ready row for every reviewed child."""

    errors = validate_reviewed_child_architecture(
        children,
        url_decisions=url_decisions,
    )
    if errors:
        raise ValueError("; ".join(errors))

    rows: list[dict[str, str]] = []
    for service_id in SERVICE_ORDER:
        _, parent_hub_url = HUB_METADATA[service_id]
        for page in children[service_id]:
            decision = url_decisions[page.destination_id]
            reuse_requirement = REUSE_DEPLOYMENT_REQUIREMENTS.get(
                page.destination_id,
                {},
            )
            rows.append(
                {
                    "destination_id": page.destination_id,
                    "service_id": service_id,
                    "title": page.title,
                    "slug": page.slug,
                    "query": page.representative_query,
                    "parent_hub": f"{service_id}-HUB",
                    "parent_hub_url": parent_hub_url,
                    "current_url": decision.current_url,
                    "target_url": decision.target_url,
                    "url_action": decision.url_action,
                    "current_wp_id": (
                        "" if decision.current_wp_id is None else str(decision.current_wp_id)
                    ),
                    "current_post_type": reuse_requirement.get("current_post_type", ""),
                    "target_template": reuse_requirement.get("target_template", ""),
                    "excluded_primary_intents": reuse_requirement.get(
                        "excluded_primary_intents",
                        "",
                    ),
                    "business_evidence": page.business_evidence,
                    "semantic_evidence": page.semantic_evidence,
                    "boundary": page.boundary,
                    "publication_status": "ready",
                }
            )
    return rows


def render_final_service_structure(
    children: Mapping[str, Sequence[ExpandedPage]] = REVIEWED_CHILDREN,
    *,
    url_decisions: Mapping[str, UrlDecision] = URL_DECISIONS,
) -> str:
    """Render a concise human review of the same validated architecture."""

    rows = build_final_service_rows(children, url_decisions=url_decisions)
    rows_by_service = {
        service_id: [row for row in rows if row["service_id"] == service_id]
        for service_id in SERVICE_ORDER
    }
    lines = [
        "# Финальная структура дочерних услуг",
        "",
        "Источник: `REVIEWED_CHILDREN`. В документ входят только страницы со статусом публикации `ready`.",
        "",
        f"Всего дочерних услуг: **{len(rows)}**.",
        "",
    ]
    for service_id in SERVICE_ORDER:
        hub_title, hub_url = HUB_METADATA[service_id]
        service_rows = rows_by_service[service_id]
        lines.extend(
            [
                f"## {service_id} — {hub_title}",
                "",
                f"- Родительский хаб: [{service_id}-HUB]({hub_url})",
                f"- Дочерних услуг: **{len(service_rows)}**",
            ]
        )
        justification = SPARSE_HUB_JUSTIFICATIONS.get(service_id)
        if justification:
            lines.extend(["", f"> Почему хаб разрежен: {justification}"])
        lines.extend(["", "Дочерние страницы:", ""])
        for row in service_rows:
            url_note = (
                f"переиспользовать WP {row['current_wp_id']}, "
                f"шаблон `{row['target_template']}`"
                if row["url_action"] == "reuse"
                else "создать"
            )
            lines.append(
                f"- **{row['title']}** — `{row['destination_id']}`, "
                f"`/{row['slug']}/`; {url_note}: {row['target_url']}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_final_service_architecture(
    csv_path: Path = DEFAULT_CSV_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
) -> int:
    """Write deterministic UTF-8 CSV and Markdown artifacts."""

    rows = build_final_service_rows()
    markdown = render_final_service_structure()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    return len(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the reviewed EXP76 child-service architecture."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN_PATH)
    args = parser.parse_args(argv)
    count = write_final_service_architecture(args.csv, args.markdown)
    print(f"Exported {count} final child services.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
