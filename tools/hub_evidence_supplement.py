"""Build verified image and case evidence for all S1-S15 hub sources."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Mapping, Sequence

from tools.site_content.cases import (
    CaseEvidence,
    FactSource,
    ImageAudit,
    PageAudit,
    ServiceSupport,
    audit_image_url,
    resolve_public_page,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HUBS_DIR = ROOT / "seo-content" / "service-hubs" / "hubs"
DEFAULT_OUTPUT = (
    ROOT / "seo-content" / "service-hubs" / "hub-evidence-supplement.json"
)
AUDIT_SOURCE = "seo-content/service-pages/evidence.json"
ALL_SERVICE_IDS = tuple(f"S{number}" for number in range(1, 16))

CASE_SPECS = {
    8613: {
        "service_ids": ("S2", "S5", "S9"),
        "url": "https://exp76.ru/fotogalereja/poselok-koprino/",
        "title": "Посёлок Коприно",
        "location": "посёлок Коприно",
        "work_types": (
            "корчевание пней",
            "планировка участка",
            "завоз плодородного грунта",
            "посев газона",
        ),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/IMG_0808.webp",
        "source_anchor": "services[destination_id=S9-CHILD-STUMPS]",
    },
    8608: {
        "service_ids": ("S10",),
        "url": "https://exp76.ru/fotogalereja/marievka/",
        "title": "Мариевка",
        "location": "Мариевка",
        "work_types": ("каскад водопадов", "пруд"),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/ceCDnbc-gM4.webp",
        "source_anchor": "services[destination_id=S10-CHILD-DECORATIVE-POND]",
    },
    8620: {
        "service_ids": ("S1", "S7"),
        "url": "https://exp76.ru/fotogalereja/rybinsk-shankhajj/",
        "title": "Рыбинск, Шанхай",
        "location": "Рыбинск, Шанхай",
        "work_types": ("3D-визуализация", "архитектурное освещение"),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/IMG_1814.webp",
        "source_anchor": "services[destination_id=S1-CHILD-3D]",
    },
    8636: {
        "service_ids": ("S2", "S5"),
        "url": "https://exp76.ru/fotogalereja/sudoverf/",
        "title": "Судоверфь",
        "location": "Судоверфь",
        "work_types": ("культивирование земли", "планировка территории", "посев газона"),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/IMG_0843.webp",
        "source_anchor": "services[destination_id=S5-CHILD-CULTIVATION]",
    },
    9415: {
        "service_ids": ("S5",),
        "url": "https://exp76.ru/fotogalereja/c-glebovo-rybinskijj-r-on/",
        "title": "с. Глебово, Рыбинский район",
        "location": "с. Глебово, Рыбинский район",
        "work_types": ("выравнивание земельного участка",),
        "image_url": "https://exp76.ru/wp-content/uploads/2019/02/IMG_20180919_165532_HDR.webp",
        "source_anchor": "services[destination_id=S5-CHILD-LEVEL]",
    },
    9567: {
        "service_ids": ("S5",),
        "url": "https://exp76.ru/fotogalereja/d-timoshkino/",
        "title": "д. Тимошкино",
        "location": "д. Тимошкино",
        "work_types": ("выравнивание земельного участка",),
        "image_url": "https://exp76.ru/wp-content/uploads/2019/02/IMG_20181103_121527_HDR.webp",
        "source_anchor": "services[destination_id=S5-CHILD-LEVEL]",
    },
    10107: {
        "service_ids": ("S6",),
        "url": "https://exp76.ru/poshekhone/",
        "title": "Пошехонье",
        "location": "Пошехонье",
        "work_types": ("устройство подпорной стенки",),
        "image_url": "https://exp76.ru/wp-content/uploads/2020/10/DSC01487.webp",
        "source_anchor": "services[destination_id=S6-CHILD-CONCRETE]",
    },
    8638: {
        "service_ids": ("S6",),
        "url": "https://exp76.ru/fotogalereja/timoshkino/",
        "title": "Тимошкино",
        "location": "Тимошкино",
        "work_types": ("подпорная стенка из плитняка методом сухой кладки",),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/IMG_1983.webp",
        "source_anchor": "services[destination_id=S6-CHILD-STONE]",
    },
    9684: {
        "service_ids": ("S7",),
        "url": "https://exp76.ru/fotogalereja/rybinsk-marievka/",
        "title": "Рыбинск, Мариевка",
        "location": "Рыбинск, Мариевка",
        "work_types": ("монтаж уличного освещения",),
        "image_url": "https://exp76.ru/wp-content/uploads/2019/02/EvxPksHMjgc.webp",
        "source_anchor": "services[destination_id=S7-CHILD-INSTALL]",
    },
    8604: {
        "service_ids": ("S7",),
        "url": "https://exp76.ru/fotogalereja/kamenniki/",
        "title": "Каменники",
        "location": "Каменники",
        "work_types": ("архитектурное освещение",),
        "image_url": "https://exp76.ru/wp-content/uploads/2018/02/DbDKG2WLtEk.webp",
        "source_anchor": "services[destination_id=S7-CHILD-ARCHITECTURAL]",
    },
}

ImageAuditor = Callable[[str, str], ImageAudit]
PageResolver = Callable[[str, str], PageAudit]


def _image_rows(value: object) -> list[Mapping[str, object]]:
    rows: list[Mapping[str, object]] = []
    if isinstance(value, Mapping):
        if isinstance(value.get("url"), str) and isinstance(value.get("alt"), str):
            rows.append(value)
        for item in value.values():
            rows.extend(_image_rows(item))
    elif isinstance(value, list):
        for item in value:
            rows.extend(_image_rows(item))
    return rows


def _load_hub_images(hubs_dir: Path) -> dict[str, dict[str, set[str]]]:
    by_service: dict[str, dict[str, set[str]]] = {}
    for service_id in ALL_SERVICE_IDS:
        path = hubs_dir / f"{service_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("service_id") != service_id:
            raise ValueError(f"{path.name} service_id differs")
        noncase: set[str] = set()
        case_images: set[str] = set()
        for row in _image_rows(payload):
            url = str(row["url"])
            if not url.startswith("https://exp76.ru/wp-content/uploads/"):
                raise ValueError(f"external hub image is forbidden: {url}")
            if isinstance(row.get("case_id"), int):
                case_images.add(url)
            else:
                noncase.add(url)
        if not noncase:
            raise ValueError(f"{service_id} has no service/context image")
        by_service[service_id] = {"noncase": noncase, "case": case_images}
    return by_service


def build_supplement(
    hubs_dir: Path,
    checked_date: str,
    *,
    image_auditor: ImageAuditor = audit_image_url,
    page_resolver: PageResolver = resolve_public_page,
) -> dict[str, object]:
    """Audit every selected S1-S15 image and the approved exact case owners."""

    images = _load_hub_images(hubs_dir)
    all_urls = sorted(
        {
            url
            for groups in images.values()
            for urls in groups.values()
            for url in urls
        }
        | {str(spec["image_url"]) for spec in CASE_SPECS.values()}
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        audits = dict(
            zip(
                all_urls,
                executor.map(
                    lambda url: image_auditor(url, checked_date),
                    all_urls,
                ),
            )
        )
    invalid = [url for url, audit in audits.items() if not audit.is_valid]
    if invalid:
        raise ValueError("unverified hub images: " + ", ".join(invalid))

    service_images: list[dict[str, object]] = []
    for service_id in ALL_SERVICE_IDS:
        for url in sorted(images[service_id]["noncase"]):
            service_images.append(
                {
                    "service_id": service_id,
                    "url": url,
                    "audit": asdict(audits[url]),
                    "source_ref": (
                        f"seo-content/service-hubs/hubs/{service_id}.json#selected-image"
                    ),
                }
            )

    cases: list[dict[str, object]] = []
    for page_id, spec in CASE_SPECS.items():
        page_audit = page_resolver(str(spec["url"]), checked_date)
        if not page_audit.is_valid or page_audit.page_id != page_id:
            raise ValueError(f"case page audit differs: {page_id}")
        image_url = str(spec["image_url"])
        image_audit = audits[image_url]
        service_ids = tuple(str(item) for item in spec["service_ids"])
        source_ref = f"{AUDIT_SOURCE}#{spec['source_anchor']}"
        work_types = tuple(str(item) for item in spec["work_types"])
        case = CaseEvidence(
            page_id=page_id,
            url=str(spec["url"]),
            title=str(spec["title"]),
            location=str(spec["location"]),
            work_types=work_types,
            service_ids=service_ids,
            image_urls=(image_url,),
            source_files=(
                AUDIT_SOURCE,
                *(f"seo-content/service-hubs/hubs/{service_id}.json" for service_id in service_ids),
            ),
            seo_ready=True,
            source_refs=(source_ref,),
            location_sources=(source_ref,),
            work_type_sources=tuple(
                FactSource(value=value, source_ref=source_ref)
                for value in work_types
            ),
            service_support=tuple(
                ServiceSupport(
                    service_id=service_id,
                    basis="explicit_work",
                    source_ref=source_ref,
                )
                for service_id in service_ids
            ),
            image_sources=(FactSource(value=image_url, source_ref=source_ref),),
            page_audit=page_audit,
            image_audits=(image_audit,),
            blocking_gaps=(),
        )
        cases.append(asdict(case))

    return {
        "schema_version": 1,
        "checked_date": checked_date,
        "sources": [
            {
                "path": AUDIT_SOURCE,
                "role": "legacy capability, exact case and media provenance",
            },
            {
                "path": "seo-content/service-hubs/hubs/S1.json..S15.json",
                "role": "selected hub media",
            },
            {
                "url": "https://exp76.ru/wp-json/wp/v2/pages",
                "role": "public case owner and publish status",
            },
        ],
        "service_images": service_images,
        "cases": sorted(cases, key=lambda item: int(item["page_id"])),
    }


def write_supplement(
    output_path: Path,
    hubs_dir: Path,
    checked_date: str,
) -> tuple[int, int]:
    document = build_supplement(hubs_dir, checked_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(document["service_images"]), len(document["cases"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit S1-S15 hub evidence.")
    parser.add_argument("--hubs-dir", type=Path, default=DEFAULT_HUBS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checked-date", required=True)
    args = parser.parse_args(argv)
    image_count, case_count = write_supplement(
        args.output,
        args.hubs_dir,
        args.checked_date,
    )
    print(f"Wrote {image_count} service images and {case_count} exact cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
