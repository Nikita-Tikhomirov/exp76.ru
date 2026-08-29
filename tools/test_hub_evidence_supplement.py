"""Verified legacy hub cases and service images are loadable fail-closed."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.site_content.contracts import load_case_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "seo-content" / "service-hubs" / "case-catalog.json"
HUBS = ROOT / "seo-content" / "service-hubs" / "hubs"
PRESENTATION_MANIFEST = (
    ROOT / "seo-content" / "service-pages" / "presentation-images-manifest.json"
)


def _images(value: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    if isinstance(value, dict):
        if isinstance(value.get("url"), str) and isinstance(value.get("alt"), str):
            result.append(value)
        for item in value.values():
            result.extend(_images(item))
    elif isinstance(value, list):
        for item in value:
            result.extend(_images(item))
    return result


class HubEvidenceSupplementTests(unittest.TestCase):
    def test_exact_legacy_cases_are_available(self) -> None:
        catalog = load_case_catalog(CATALOG)
        self.assertEqual({"S2", "S5", "S9"}, set(catalog[8613].service_ids))
        self.assertEqual({"S10"}, set(catalog[8608].service_ids))
        self.assertTrue(catalog[8613].seo_ready)
        self.assertTrue(catalog[8608].seo_ready)

    def test_newly_audited_cases_close_the_exact_child_evidence_gaps(self) -> None:
        catalog = load_case_catalog(CATALOG)
        expected = {
            8620: {"S1", "S7"},
            8636: {"S2", "S5"},
            9415: {"S5"},
            9567: {"S5"},
            10107: {"S6"},
            8638: {"S6"},
            9684: {"S7"},
            8604: {"S7"},
        }
        for page_id, service_ids in expected.items():
            with self.subTest(page_id=page_id):
                self.assertTrue(service_ids.issubset(catalog[page_id].service_ids))
                self.assertTrue(catalog[page_id].seo_ready)
                self.assertFalse(catalog[page_id].blocking_gaps)
                self.assertTrue(catalog[page_id].image_urls)

    def test_every_noncase_s1_s15_hub_image_is_verified_for_its_service(self) -> None:
        catalog = load_case_catalog(CATALOG)
        presentation = json.loads(PRESENTATION_MANIFEST.read_text(encoding="utf-8"))
        generated_by_service: dict[str, set[str]] = {}
        for asset in presentation["assets"]:
            output = asset.get("output", {})
            url = str(output.get("url", ""))
            if output.get("status") != "ready" or not url:
                continue
            for target in asset.get("targets", []):
                page_key = str(target.get("page_key", ""))
                if page_key.endswith("-HUB"):
                    service_id = page_key.removesuffix("-HUB")
                    generated_by_service.setdefault(service_id, set()).add(url)

        for number in range(1, 16):
            service_id = f"S{number}"
            payload = json.loads(
                (HUBS / f"{service_id}.json").read_text(encoding="utf-8")
            )
            noncase_urls = {
                str(image["url"])
                for image in _images(payload)
                if not isinstance(image.get("case_id"), int)
            }
            self.assertTrue(noncase_urls, service_id)
            verified_urls = set(
                catalog.verified_image_urls_by_service.get(service_id, frozenset())
            ) | generated_by_service.get(service_id, set())
            self.assertTrue(
                noncase_urls.issubset(verified_urls),
                service_id,
            )

    def test_every_hub_case_image_is_owned_and_supports_its_service(self) -> None:
        catalog = load_case_catalog(CATALOG)
        for number in range(1, 16):
            service_id = f"S{number}"
            payload = json.loads(
                (HUBS / f"{service_id}.json").read_text(encoding="utf-8")
            )
            for image in _images(payload):
                case_id = image.get("case_id")
                if not isinstance(case_id, int):
                    continue
                with self.subTest(service_id=service_id, case_id=case_id):
                    self.assertIn(service_id, catalog[case_id].service_ids)
                    self.assertIn(image["url"], catalog[case_id].image_urls)


if __name__ == "__main__":
    unittest.main()
