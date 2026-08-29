"""Runtime ownership contracts for all upgraded legacy service hubs."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"

EXPECTED_LEGACY_OWNERS = {
    "S9": (6870, "vykorchevyvanie-pnejj-spil-derevev"),
    "S10": (6900, "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev"),
    "S11": (6922, "sistemy-tumanoobrazovaniya"),
    "S12": (9138, "fundament-na-zhelezobetonnykh-svajakh"),
    "S13": (9312, "navesy-iz-metalla"),
    "S14": (9775, "kaminy-pechi-barbekju"),
    "S15": (9838, "snos-i-demontazh-zdanijj-domov"),
}


class LegacyHubRuntimeTests(unittest.TestCase):
    def test_service_v2_router_has_exact_s9_s15_owners(self) -> None:
        source = (THEME / "inc" / "service-v2.php").read_text(encoding="utf-8")
        found = {
            service_id: (int(page_id), slug)
            for page_id, slug, service_id in re.findall(
                r"(\d+)\s*=>\s*array\('slug'\s*=>\s*'([^']+)',\s*"
                r"'service_id'\s*=>\s*'(S(?:[1-9]|1[0-5]))'\)",
                source,
            )
        }

        self.assertEqual(
            EXPECTED_LEGACY_OWNERS,
            {key: found[key] for key in EXPECTED_LEGACY_OWNERS},
        )
        self.assertEqual(15, len(found))

    def test_hub_registry_preserves_every_legacy_wp_owner_and_canonical(self) -> None:
        source = (THEME / "inc" / "service-hub-registry.php").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r"<<<'LAND76_SERVICE_HUB_REGISTRY_JSON'\s*(.*?)\s*"
            r"LAND76_SERVICE_HUB_REGISTRY_JSON;",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        registry = json.loads(match.group(1))

        self.assertEqual({f"S{index}" for index in range(1, 16)}, set(registry))
        for service_id, (page_id, slug) in EXPECTED_LEGACY_OWNERS.items():
            item = registry[service_id]
            self.assertEqual(page_id, item["hub_post_id"])
            self.assertEqual(slug, item["hub_slug"])
            self.assertEqual(slug, item["grouping_slug"])
            self.assertEqual(
                f"https://exp76.ru/services/{slug}/",
                item["canonical"],
            )
            self.assertEqual("redirect_to_hub", item["archive_policy"])

    def test_managed_child_router_accepts_s1_s15_but_not_s16(self) -> None:
        source = (THEME / "servicepost.php").read_text(encoding="utf-8")
        registry = (THEME / "inc" / "service-hub-registry.php").read_text(
            encoding="utf-8"
        )

        self.assertIn("land76wp_claims_managed_service_hub_post", source)
        self.assertIn("land76wp_managed_page_contract", source)
        self.assertIn("$land76_managed_contract['role'] !== 'child'", source)
        self.assertIn("S(?:[1-9]|1[0-5])-CHILD-", registry)
        self.assertNotIn("S[1-8]-CHILD-", registry)


if __name__ == "__main__":
    unittest.main()
