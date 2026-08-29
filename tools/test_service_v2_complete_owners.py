"""Exact runtime owners for all 15 service-v2 hubs."""

from __future__ import annotations

import unittest

from tools.service_v2 import EXACT_SERVICE_OWNERS, PAGE_ARCHITECTURE_PATH


EXPECTED_LEGACY_OWNERS = {
    "S9": (6870, "vykorchevyvanie-pnejj-spil-derevev"),
    "S10": (6900, "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev"),
    "S11": (6922, "sistemy-tumanoobrazovaniya"),
    "S12": (9138, "fundament-na-zhelezobetonnykh-svajakh"),
    "S13": (9312, "navesy-iz-metalla"),
    "S14": (9775, "kaminy-pechi-barbekju"),
    "S15": (9838, "snos-i-demontazh-zdanijj-domov"),
}


class CompleteHubOwnerTests(unittest.TestCase):
    def test_all_fifteen_exact_owners_are_registered(self) -> None:
        self.assertEqual(tuple(f"S{number}" for number in range(1, 16)), tuple(EXACT_SERVICE_OWNERS))
        self.assertEqual(
            EXPECTED_LEGACY_OWNERS,
            {key: EXACT_SERVICE_OWNERS[key] for key in EXPECTED_LEGACY_OWNERS},
        )

    def test_validator_uses_complete_destination_ledger(self) -> None:
        self.assertEqual("complete_page_architecture.csv", PAGE_ARCHITECTURE_PATH.name)


if __name__ == "__main__":
    unittest.main()
