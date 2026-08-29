import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
IMPORTER = THEME / "inc" / "import-service-hubs.php"
SERVICE_V2 = THEME / "inc" / "service-v2.php"
AUTHORITATIVE_MANIFEST = (
    ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
)

RELEASE_ID = "service-hubs-2026-08-28"
ACTIVE_RELEASE_OPTION = "land76_service_hubs_active_release_id"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def php_function_body(source: str, function_name: str) -> str:
    match = re.search(
        r"function\s+" + re.escape(function_name) + r"\s*\([^)]*\)\s*\{",
        source,
    )
    if match is None:
        raise AssertionError(f"function {function_name} not found")

    start = match.end() - 1
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : index]
    raise AssertionError(f"function {function_name} has no closing brace")


def braced_body(source: str, opening_brace: int) -> str:
    depth = 0
    for index in range(opening_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening_brace + 1 : index]
    raise AssertionError("block has no closing brace")


class ExactReleaseAdmissionTests(unittest.TestCase):
    def expected_page_keys(self) -> list[str]:
        manifest = json.loads(read(AUTHORITATIVE_MANIFEST))
        self.assertEqual(RELEASE_ID, manifest["release_id"])
        return sorted(
            str(item["page_key"])
            for item in manifest["managed_pages"]
            if item["page_role"] in {"child_service", "article"}
        )

    def embedded_page_keys(self) -> list[str]:
        source = read(IMPORTER)
        match = re.search(
            r"<<<'LAND76_SERVICE_HUB_EXPECTED_PAGE_KEYS_JSON'\s*(.*?)\s*"
            r"LAND76_SERVICE_HUB_EXPECTED_PAGE_KEYS_JSON;",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "importer must embed the frozen release inventory")
        return json.loads(match.group(1).strip())

    def test_importer_pins_the_authoritative_65_child_and_11_article_keys(self) -> None:
        expected = self.expected_page_keys()
        embedded = self.embedded_page_keys()

        self.assertEqual(76, len(expected))
        self.assertEqual(65, sum("-CHILD-" in key for key in expected))
        self.assertEqual(11, sum("-ARTICLE-" in key for key in expected))
        self.assertEqual(expected, embedded)
        self.assertEqual(len(embedded), len(set(embedded)))

    def test_payload_and_release_manifest_are_each_checked_against_frozen_keys(self) -> None:
        source = read(IMPORTER)
        validator = php_function_body(
            source, "land76wp_service_hubs_validate_expected_inventory"
        )
        payload_validator = php_function_body(
            source, "land76wp_service_hubs_validate_payload"
        )
        binding_validator = php_function_body(
            source, "land76wp_service_hubs_validate_manifest_binding"
        )

        for marker in (
            "land76wp_service_hubs_expected_page_keys",
            "expected_inventory_mismatch",
            "count($expected_page_keys) !== 76",
            "count($actual_page_keys) !== 76",
            "65",
            "11",
        ):
            self.assertIn(marker, validator)
        self.assertIn("land76wp_service_hubs_validate_expected_inventory", payload_validator)
        self.assertGreaterEqual(
            binding_validator.count(
                "land76wp_service_hubs_validate_expected_inventory"
            ),
            2,
            "payload and release manifest must fail independently when truncated",
        )


class DurableActivationGateTests(unittest.TestCase):
    def test_schema_v2_requires_its_exact_release_marker_but_v1_does_not(self) -> None:
        source = read(SERVICE_V2)
        loader = php_function_body(source, "land76_service_v2_load")
        gate = php_function_body(source, "land76_service_v2_release_is_active")
        schema_v1_start = loader.index("if ($schema_version === 1)")
        schema_v2_start = loader.index("elseif ($schema_version === 2)")
        schema_v1 = loader[schema_v1_start:schema_v2_start]
        schema_v2 = loader[schema_v2_start:]

        self.assertNotIn("land76_service_v2_release_is_active", schema_v1)
        self.assertIn("$payload['release_id']", schema_v2)
        self.assertIn("land76_service_v2_release_is_active", schema_v2)
        self.assertIn("get_option", gate)
        self.assertIn("hash_equals", gate)
        self.assertIn(ACTIVE_RELEASE_OPTION, source)

    def test_activation_helper_accepts_update_option_false_when_readback_matches(self) -> None:
        source = read(IMPORTER)
        activate = php_function_body(
            source, "land76wp_service_hubs_activate_verified_release"
        )
        snapshot = php_function_body(
            source, "land76wp_service_hubs_active_release_snapshot"
        )

        self.assertIn("land76wp_service_hubs_expected_release_id", activate)
        self.assertIn("activation_release_mismatch", activate)
        self.assertIn("update_option", activate)
        self.assertIn("false", activate, "the marker option must not autoload")
        self.assertIn("get_option", activate)
        self.assertIn("hash_equals", activate)
        self.assertIn("release_activation_failed", activate)
        self.assertNotRegex(
            activate,
            r"if\s*\(\s*!\s*update_option",
            "WordPress returns false when the same value is already stored",
        )
        self.assertIn("option_exists", snapshot)
        self.assertIn("option_value", snapshot)

    def test_publish_repairs_marker_only_after_full_verification_and_commit(self) -> None:
        source = read(IMPORTER)
        publish = php_function_body(source, "land76wp_service_hubs_publish_plan")
        no_op_start = publish.index(
            "if ($publish_ids === array() && $reuse_operations === array())"
        )
        transaction_start = publish.index("START TRANSACTION", no_op_start)
        no_op_branch = publish[no_op_start:transaction_start]

        self.assertIn("land76wp_service_hubs_activate_verified_release", no_op_branch)
        self.assertLess(
            publish.index("land76wp_service_hubs_verify_staged_item"), no_op_start
        )
        commit = publish.index("COMMIT", transaction_start)
        final_activation = publish.rindex(
            "land76wp_service_hubs_activate_verified_release"
        )
        self.assertLess(commit, final_activation)
        self.assertIn("$transaction_committed", publish[commit:final_activation])
        catch_start = publish.index("catch (Throwable $error)", commit)
        catch_body = braced_body(publish, publish.index("{", catch_start))
        self.assertNotIn(
            "land76wp_service_hubs_activate_verified_release",
            catch_body,
        )
        self.assertIn("land76wp_service_hubs_active_release_snapshot", publish)

    def test_exact_managed_reuse_owner_can_take_the_no_op_activation_path(self) -> None:
        publish = php_function_body(
            read(IMPORTER), "land76wp_service_hubs_publish_plan"
        )
        reuse_branch_start = publish.index("if ($operation['action'] === 'reuse_update')")
        reuse_branch_end = publish.index("continue;", reuse_branch_start)
        reuse_branch = publish[reuse_branch_start:reuse_branch_end]

        self.assertIn("managed_exact_match", reuse_branch)
        self.assertIn("land76wp_service_hubs_verify_staged_item", reuse_branch)
        self.assertIn("'publish'", reuse_branch)
        self.assertIn("$stats['unchanged']++", reuse_branch)
        self.assertLess(
            reuse_branch.index("land76wp_service_hubs_verify_staged_item"),
            reuse_branch.index("$reuse_operations[]"),
        )


if __name__ == "__main__":
    unittest.main()
