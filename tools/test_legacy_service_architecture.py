"""Contracts for the seven legacy service hubs promoted to S9-S15."""

from __future__ import annotations

import csv
import importlib
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path


EXPECTED_OWNERS = {
    "S9": (6870, "https://exp76.ru/services/vykorchevyvanie-pnejj-spil-derevev/"),
    "S10": (
        6900,
        "https://exp76.ru/services/sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev/",
    ),
    "S11": (6922, "https://exp76.ru/services/sistemy-tumanoobrazovaniya/"),
    "S12": (9138, "https://exp76.ru/services/fundament-na-zhelezobetonnykh-svajakh/"),
    "S13": (9312, "https://exp76.ru/services/navesy-iz-metalla/"),
    "S14": (9775, "https://exp76.ru/services/kaminy-pechi-barbekju/"),
    "S15": (9838, "https://exp76.ru/services/snos-i-demontazh-zdanijj-domov/"),
}

EXPECTED_CHILD_COUNTS = {
    "S9": 3,
    "S10": 5,
    "S11": 3,
    "S12": 3,
    "S13": 4,
    "S14": 5,
    "S15": 6,
}

EXPECTED_CHILD_SLUGS = {
    "S9": {
        "spil-i-udalenie-derevev",
        "korchevanie-pnej",
        "raschistka-uchastka-ot-derevev-i-kustarnikov",
    },
    "S10": {
        "dekorativnyj-prud-na-uchastke",
        "plavatelnyj-prud-na-uchastke",
        "vodopad-i-kaskad-na-uchastke",
        "dekorativnyj-ruchej-na-uchastke",
        "fontan-na-uchastke",
    },
    "S11": {
        "tumanoobrazovanie-dlya-terrasy-i-verandy",
        "tumanoobrazovanie-dlya-kafe-i-letnih-ploshchadok",
        "tumanoobrazovanie-dlya-teplic-i-oranzherej",
    },
    "S12": {
        "zabivka-zhelezobetonnyh-svaj",
        "fundament-na-zhb-svayah-dlya-chastnogo-doma",
        "fundament-na-zhb-svayah-dlya-bani",
    },
    "S13": {
        "naves-dlya-avtomobilya",
        "naves-dlya-terrasy-i-verandy",
        "naves-dlya-zony-barbekyu",
        "naves-iz-polikarbonata-k-domu",
    },
    "S14": {
        "stroitelstvo-kamina",
        "kladka-otopitelnoj-pechi",
        "barbekyu-kompleks-pod-klyuch",
        "kirpichnyj-mangal",
        "pech-s-kazanom-i-koptilnej",
    },
    "S15": {
        "snos-chastnogo-doma",
        "demontazh-dachnogo-doma",
        "demontazh-avarijnyh-zdanij",
        "ruchnaya-razborka-zdanij",
        "mehanizirovannyj-snos-zdanij",
        "vyvoz-stroitelnogo-musora-posle-snosa",
    },
}


def _architecture():
    try:
        return importlib.import_module("tools.seo_semantics.legacy_service_architecture")
    except ModuleNotFoundError as exc:
        raise AssertionError("legacy service architecture module is missing") from exc


class LegacyServiceArchitectureTests(unittest.TestCase):
    def test_exact_live_owners_are_reused_as_full_hubs(self) -> None:
        architecture = _architecture()

        self.assertEqual(tuple(EXPECTED_OWNERS), architecture.LEGACY_SERVICE_ORDER)
        self.assertEqual(set(EXPECTED_OWNERS), set(architecture.LEGACY_HUB_OWNERS))
        for service_id, (wp_id, current_url) in EXPECTED_OWNERS.items():
            hub = architecture.LEGACY_HUB_OWNERS[service_id]
            self.assertEqual(f"{service_id}-HUB", hub.destination_id)
            self.assertEqual("hub", hub.page_role)
            self.assertEqual(wp_id, hub.current_wp_id)
            self.assertEqual(current_url, hub.current_url)
            self.assertEqual(current_url, hub.target_url)
            self.assertEqual("reuse", hub.url_action)
            self.assertEqual("page", hub.current_post_type)
            self.assertEqual("servicepost.php", hub.target_template)
            self.assertEqual("", hub.parent_destination_id)
            self.assertIn(f"wp-rest/pages/{wp_id}#content", hub.business_evidence)

    def test_each_hub_has_three_to_six_traceable_children(self) -> None:
        architecture = _architecture()

        self.assertEqual(
            EXPECTED_CHILD_COUNTS,
            {
                service_id: len(children)
                for service_id, children in architecture.LEGACY_CHILDREN.items()
            },
        )
        children = architecture.all_legacy_children()
        self.assertEqual(
            EXPECTED_CHILD_SLUGS,
            {
                service_id: {child.slug for child in service_children}
                for service_id, service_children in architecture.LEGACY_CHILDREN.items()
            },
        )
        self.assertEqual(29, len(children))
        self.assertEqual(29, len({child.destination_id for child in children}))
        self.assertEqual(29, len({child.slug for child in children}))
        self.assertEqual(29, len({child.target_url for child in children}))
        for child in children:
            owner_wp_id, owner_url = EXPECTED_OWNERS[child.service_id]
            self.assertEqual("child_service", child.page_role)
            self.assertEqual(f"{child.service_id}-HUB", child.parent_destination_id)
            self.assertIsNone(child.current_wp_id)
            self.assertEqual("", child.current_url)
            self.assertEqual("create", child.url_action)
            self.assertEqual("newservicepost.php", child.target_template)
            self.assertEqual(owner_wp_id, child.owner_wp_id)
            self.assertEqual(owner_url, child.owner_current_url)
            self.assertIn(f"wp-rest/pages/{owner_wp_id}#content", child.business_evidence)
            self.assertNotIn("case-wp-", child.business_evidence)
            self.assertNotIn("context-case-wp-", child.business_evidence)

    def test_boundaries_keep_pruning_screw_piles_and_protected_categories_out(self) -> None:
        architecture = _architecture()

        self.assertEqual([], architecture.validate_legacy_architecture())
        s9_pages = (
            architecture.LEGACY_HUB_OWNERS["S9"],
            *architecture.LEGACY_CHILDREN["S9"],
        )
        for page in s9_pages:
            exclusions = "|".join(page.excluded_primary_intents)
            self.assertIn("обрезка деревьев", exclusions)
            self.assertIn("обрезка кустарников", exclusions)
        s12_pages = (
            architecture.LEGACY_HUB_OWNERS["S12"],
            *architecture.LEGACY_CHILDREN["S12"],
        )
        for page in s12_pages:
            self.assertIn("винтовые сваи", page.excluded_primary_intents)

        searchable = " ".join(
            f"{page.title} {page.slug} {page.representative_query}"
            for page in architecture.all_legacy_destinations()
        ).casefold()
        for forbidden in (
            "автополив",
            "дренаж участка",
            "ливневая канализация",
            "осушение участка",
            "отмостка",
            "тротуарная плитка",
        ):
            self.assertNotIn(forbidden, searchable)

    def test_validator_fails_closed_on_owner_or_protected_intent_tampering(self) -> None:
        architecture = _architecture()

        hubs = dict(architecture.LEGACY_HUB_OWNERS)
        hubs["S9"] = replace(hubs["S9"], current_wp_id=9999)
        self.assertTrue(
            any(
                "exact live owner differs" in error
                for error in architecture.validate_legacy_architecture(hubs=hubs)
            )
        )

        children = dict(architecture.LEGACY_CHILDREN)
        children["S10"] = (
            replace(
                children["S10"][0],
                representative_query="дренаж участка ярославль",
            ),
            *children["S10"][1:],
        )
        self.assertTrue(
            any(
                "claims protected owner" in error
                for error in architecture.validate_legacy_architecture(children=children)
            )
        )

    def test_validator_rejects_an_unproven_capability_hidden_behind_a_known_slug(self) -> None:
        architecture = _architecture()

        children = dict(architecture.LEGACY_CHILDREN)
        children["S10"] = (
            replace(
                children["S10"][0],
                title="Очистка и ремонт существующих прудов",
                representative_query="очистка пруда ярославль",
                business_evidence=(
                    "business_source:wp-rest/pages/6900#content[ochistka-chuzhih-prudov]"
                ),
            ),
            *children["S10"][1:],
        )

        self.assertTrue(
            any(
                "proven child definition differs" in error
                for error in architecture.validate_legacy_architecture(children=children)
            )
        )

    def test_validator_checks_protected_intents_in_exported_included_scope(self) -> None:
        architecture = _architecture()

        children = dict(architecture.LEGACY_CHILDREN)
        children["S13"] = (
            replace(
                children["S13"][0],
                included_intent="навес и дренаж участка",
            ),
            *children["S13"][1:],
        )

        self.assertTrue(
            any(
                "claims protected owner" in error
                for error in architecture.validate_legacy_architecture(children=children)
            )
        )

    def test_suggest_queue_has_two_probes_per_hub_and_child(self) -> None:
        architecture = _architecture()

        rows = architecture.build_legacy_suggest_queue()
        destinations = architecture.all_legacy_destinations()
        self.assertEqual(72, len(rows))
        self.assertEqual("YS001001", rows[0]["query_id"])
        self.assertEqual("YS001072", rows[-1]["query_id"])
        self.assertEqual(
            architecture.SUGGEST_QUEUE_COLUMNS,
            tuple(rows[0]),
        )
        self.assertEqual({"10841"}, {row["region_id"] for row in rows})
        self.assertEqual(
            {destination.destination_id for destination in destinations},
            {row["destination_id"] for row in rows},
        )
        self.assertEqual(
            {destination.destination_id: 2 for destination in destinations},
            Counter(row["destination_id"] for row in rows),
        )
        self.assertEqual(len(rows), len({row["query_id"] for row in rows}))
        self.assertEqual(len(rows), len({row["seed"].casefold() for row in rows}))

    def test_exports_are_utf8_byte_deterministic_and_queue_compatible(self) -> None:
        architecture = _architecture()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "processed" / "legacy.csv"
            markdown_path = root / "reviews" / "legacy.md"
            queue_path = root / "raw" / "legacy-suggest" / "queue.csv"

            first_counts = architecture.write_legacy_service_architecture(
                csv_path,
                markdown_path,
                queue_path,
            )
            first_payloads = (
                csv_path.read_bytes(),
                markdown_path.read_bytes(),
                queue_path.read_bytes(),
            )
            second_counts = architecture.write_legacy_service_architecture(
                csv_path,
                markdown_path,
                queue_path,
            )
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            with queue_path.open("r", encoding="utf-8", newline="") as handle:
                queue_rows = list(csv.DictReader(handle))

            self.assertEqual((36, 72), first_counts)
            self.assertEqual(first_counts, second_counts)
            self.assertEqual(
                first_payloads,
                (
                    csv_path.read_bytes(),
                    markdown_path.read_bytes(),
                    queue_path.read_bytes(),
                ),
            )
            self.assertFalse(first_payloads[0].startswith(b"\xef\xbb\xbf"))
            self.assertEqual(36, len(rows))
            self.assertEqual(72, len(queue_rows))
            self.assertEqual(list(architecture.CSV_COLUMNS), list(rows[0]))
            self.assertEqual(list(architecture.SUGGEST_QUEUE_COLUMNS), list(queue_rows[0]))
            self.assertTrue(
                all(row["semantic_evidence"].startswith("suggest_queue:") for row in rows)
            )
            markdown = first_payloads[1].decode("utf-8")
            self.assertIn("Всего legacy-хабов: **7**", markdown)
            self.assertIn("Всего дочерних услуг: **29**", markdown)
            for service_id, (wp_id, _) in EXPECTED_OWNERS.items():
                self.assertIn(f"## {service_id} —", markdown)
                self.assertIn(f"WP {wp_id}", markdown)

    def test_checked_in_artifacts_cannot_drift_from_the_generator(self) -> None:
        architecture = _architecture()
        validator = getattr(architecture, "validate_checked_in_legacy_artifacts", None)
        self.assertIsNotNone(validator, "checked-in artifact validator is missing")

        self.assertEqual([], validator())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "legacy.csv"
            markdown_path = root / "legacy.md"
            queue_path = root / "queue.csv"
            architecture.write_legacy_service_architecture(
                csv_path,
                markdown_path,
                queue_path,
            )
            csv_path.write_bytes(csv_path.read_bytes() + b"stale\n")

            self.assertTrue(
                any(
                    "legacy architecture CSV is stale" in error
                    for error in validator(
                        csv_path,
                        markdown_path,
                        queue_path,
                    )
                )
            )


if __name__ == "__main__":
    unittest.main()
