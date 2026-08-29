import hashlib
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
INC = THEME / "inc"
IMPORTER = INC / "import-service-hubs.php"
REGISTRY = INC / "service-hub-registry.php"
IMPORT_PAYLOAD = THEME / "import" / "service-hubs-import.json"
IMPORT_RELEASE_MANIFEST = THEME / "import" / "service-hubs-release-manifest.json"
ACF_RELATIONS = THEME / "import" / "acf-service-hub-relations.json"
ACF_BLOG_SOURCE = ROOT / "seo-content" / "blog" / "acf-seo-blog-post-fields.json"
ACF_BLOG_THEME = THEME / "import" / "acf-seo-blog-post-fields.json"
RELEASE_MANIFEST = ROOT / "seo-content" / "service-hubs" / "release-manifest.json"
FUNCTIONS = THEME / "functions.php"
NEW_SERVICE = INC / "newservicepost.php"
SEO_BLOG = INC / "seoblogpost.php"
SEO_INDEXING = INC / "seo-category-indexing.php"
REGION_TEMPLATE = THEME / "page-service-hub-region.php"
SERVICEPOST = THEME / "servicepost.php"
SERVICEPOST_CSS = THEME / "css" / "servicepost.css"
DRENAZH_BLOG_IMPORTER = INC / "import-drenazh-blog.php"
ACF_STORAGE_BEHAVIOR = ROOT / "tools" / "test_service_hubs_acf_storage.php"

RELEASE_ID = "service-hubs-2026-08-28"
IMPORT_OWNER = "land76-service-hubs"
FORBIDDEN_KEYS = {"cleanup", "delete_stale_posts", "delete_stale_terms"}

EXPECTED_REGISTRY = {
    "S1": (673, "landshaftnoe-proektirovanie"),
    "S2": (6868, "gazon-posevnojj-i-gazon-rulonnyjj"),
    "S3": (6871, "posadka-derevev-i-kustarnikov"),
    "S4": (9357, "ukhod-za-sadom"),
    "S5": (667, "planirovka-territorii"),
    "S6": (676, "podpornye-stenki"),
    "S7": (6918, "ulichnoe-osveshhenie-uchastka"),
    "S8": (9282, "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch"),
    "S9": (6870, "vykorchevyvanie-pnejj-spil-derevev"),
    "S10": (6900, "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev"),
    "S11": (6922, "sistemy-tumanoobrazovaniya"),
    "S12": (9138, "fundament-na-zhelezobetonnykh-svajakh"),
    "S13": (9312, "navesy-iz-metalla"),
    "S14": (9775, "kaminy-pechi-barbekju"),
    "S15": (9838, "snos-i-demontazh-zdanijj-domov"),
}

LEGACY_IMPORT_HASHES = {
    "import-autopoliv.php": "f3c42978d8f111b6ad75effe515ce86d8f1ad09b4450cec928e92ff77b607132",
    "import-autopoliv-blog.php": "be938192842798f5027a0d1c655135515c227ba23ecffd4c5c3904b961dfc32c",
    "import-livnevka.php": "7736c2107754cef1512cc679284fa03a3b1274aa134a70972a314e668ec31d3d",
    "import-livnevka-blog.php": "9438244f58662b23d55e7a0b6e12be4c50c6fb7c7eb01129ae36268e28759c56",
    "import-osushenie.php": "0099cabc45f0bfc376a9f5533045b11fd2693c0d8c2aa21ee62a05d53f9879bd",
    "import-osushenie-blog.php": "9d5663f452b3df00b4242b1a358ddce9139d126bf19c214e22a2b687c9f5c091",
    "import-otmostka.php": "0f25f40e6c6f9cbdff5a4a72183d86843a8107dfd3085b24ef454fcb1e05c6a3",
    "import-otmostka-blog.php": "eeab52cf6e8fbe2c8296033f08f81f8f857c6c93729c4138d0817280420354e7",
    "import-plitka.php": "d6a3d8c762c2ae8d1b20fa4971f171257f48037e308d1159cde48f0f093cee40",
    "import-plitka-blog.php": "6d6c3dcda02f15986a9e1a4435a39988b882f3e3e2b295dcbc9c3043326385f4",
    "import-drenazh.php": "bd13a0e750bf5310ad617b46b88904959860e6c5645af30a26f6ef8cfccdea86",
    "import-drenazh-blog.php": "3a05d971062528c788245e596687f5ce1e810695ec0aa94be287e64d888ef838",
    "import-case-seo.php": "b8341aa87a8b26e95d9cdc67da7090eb3e6bfb9151446e6f530bd8fd9fd607c0",
    "import-service-previews.php": "cf00ad108fb6edf6c9bbc925594dfe6ef805c0d05232f45d945eccb4330af562",
}

LEGACY_CATEGORY_HASHES = {
    "casenew.php": "61dffab97d2bedd930101690eabc1b3b2ed27bfda7de68d0f3a6a1e864d8b310",
    "category-87.php": "c38b039f959671395c58d1ba24886cee37ad6671f7d85ed2be18b7a9646a0a9f",
    "category-88.php": "ff1f49bc47a133418e4a7f0a32a9b35ff6a3f85d47c0342deb5fc3e99838c6a0",
    "category-89.php": "cf546ea31c7efd34dd7854c878990c0f169447447641d5bc6d7a2a73736d4dfa",
    "category-90.php": "4c84282b3181986d06ab5fe798dd35b64f63141860f320ee3a1965c95d85043a",
    "category-91.php": "62db1f8b874b41a84ab252767a313abd1f15df1c5adaabbf754a6565ebe85ee7",
    "category-92.php": "f69236dc0a86786916c3ec109bf7279b5c318bbc69ce22fb759ff2d15ff756ab",
}


def read(path):
    value = path.read_text(encoding="utf-8")
    if "\ufffd" in value:
        raise AssertionError(f"replacement character in {path}")
    return value


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


def find_acf_field(value, name):
    if isinstance(value, dict):
        if value.get("name") == name:
            return value
        for child in value.values():
            found = find_acf_field(child, name)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_acf_field(child, name)
            if found is not None:
                return found
    return None


def php_function_body(source, function_name):
    match = re.search(r"function\s+" + re.escape(function_name) + r"\s*\([^)]*\)\s*\{", source)
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


class ServiceHubRegistryTests(unittest.TestCase):
    def registry(self):
        source = read(REGISTRY)
        match = re.search(
            r"<<<'LAND76_SERVICE_HUB_REGISTRY_JSON'\s*(.*?)\s*LAND76_SERVICE_HUB_REGISTRY_JSON;",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "registry must keep its single JSON source in a PHP 7.4 nowdoc")
        return json.loads(match.group(1).strip())

    def test_registry_has_exact_fifteen_frozen_hubs(self):
        registry = self.registry()
        self.assertEqual(set(registry), set(EXPECTED_REGISTRY))
        for service_id, (post_id, slug) in EXPECTED_REGISTRY.items():
            item = registry[service_id]
            self.assertEqual(item["service_id"], service_id)
            self.assertEqual(item["topic_key"], service_id)
            self.assertEqual(item["hub_post_id"], post_id)
            self.assertEqual(item["hub_slug"], slug)
            self.assertEqual(item["grouping_slug"], slug)
            self.assertEqual(item["canonical"], f"https://exp76.ru/services/{slug}/")
            self.assertEqual(item["archive_policy"], "redirect_to_hub")

    def test_registry_exposes_lookup_helpers_without_duplicate_template_maps(self):
        source = read(REGISTRY)
        for name in (
            "land76wp_service_hub_registry",
            "land76wp_service_hub_by_service_id",
            "land76wp_service_hub_by_grouping_slug",
            "land76wp_service_hub_for_post",
            "land76wp_is_managed_service_hub_post",
        ):
            self.assertIn(f"function {name}", source)

    def test_registry_drives_service_and_breadcrumb_schema_for_hubs_and_children(self):
        registry = read(REGISTRY)
        functions = read(FUNCTIONS)
        self.assertNotIn("land76wp_service_hub_output_registry_schema", registry)
        self.assertIn("function land76wp_service_hub_schema_context", registry)
        self.assertIn("function land76wp_managed_page_contract", registry)
        self.assertIn("land76_schema_managed_main_node", functions)
        self.assertIn("land76_schema_managed_breadcrumb_node", functions)
        self.assertIn("land76wp_service_hub_schema_context", functions)
        self.assertIn("'@type' => 'Service'", functions)
        self.assertIn("'@type' => 'BreadcrumbList'", functions)
        self.assertEqual(1, functions.count("add_action('wp_head', 'land76_output_structured_data'"))

    def test_managed_records_use_exact_registry_seo_and_canonical_meta(self):
        source = read(REGISTRY)
        for marker in (
            "land76wp_service_hub_filter_managed_title",
            "land76wp_service_hub_filter_managed_description",
            "land76wp_service_hub_filter_managed_canonical",
            "_aioseo_title",
            "_aioseo_description",
            "_land76_canonical",
            "aioseo_title",
            "aioseo_description",
            "aioseo_canonical_url",
            "wpseo_title",
            "wpseo_metadesc",
            "wpseo_canonical",
            "pre_get_document_title",
            "get_canonical_url",
        ):
            self.assertIn(marker, source)


class ImportPayloadAndAcfTests(unittest.TestCase):
    def test_import_payload_is_ready_and_bound_to_exact_release_inventory(self):
        payload = json.loads(read(IMPORT_PAYLOAD))
        self.assertTrue(IMPORT_RELEASE_MANIFEST.is_file(), "release inventory must ship with payload")
        release_manifest = json.loads(read(IMPORT_RELEASE_MANIFEST))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["release_id"], RELEASE_ID)
        self.assertEqual(payload["release_status"], "ready")
        self.assertEqual(76, len(payload["items"]))
        self.assertEqual(
            {"child_service": 65, "article": 11},
            {
                role: sum(item["role"] == role for item in payload["items"])
                for role in ("child_service", "article")
            },
        )
        self.assertEqual(payload["manifest_sha256"], sha256(IMPORT_RELEASE_MANIFEST))
        self.assertEqual(release_manifest["schema_version"], 1)
        self.assertEqual(release_manifest["release_id"], RELEASE_ID)
        self.assertEqual(release_manifest["release_status"], "ready")
        self.assertEqual(76, len(release_manifest["items"]))
        self.assertEqual(release_manifest["source_manifest_sha256"], sha256(RELEASE_MANIFEST))
        expected_inventory = sorted(
            (
                {"page_key": item["page_key"], "checksum": item["checksum"]}
                for item in payload["items"]
            ),
            key=lambda item: (item["page_key"], item["checksum"]),
        )
        self.assertEqual(expected_inventory, release_manifest["items"])
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(recursive_keys(payload)))
        self.assertTrue(FORBIDDEN_KEYS.isdisjoint(recursive_keys(release_manifest)))

    def test_relationship_acf_schema_selects_existing_page_ids(self):
        groups = json.loads(read(ACF_RELATIONS))
        selected_works = find_acf_field(groups, "selected_works_posts")
        selected_projects = find_acf_field(groups, "selected_real_projects")
        for field in (selected_works, selected_projects):
            self.assertIsNotNone(field)
            self.assertEqual(field["type"], "relationship")
            self.assertEqual(field["post_type"], ["page"])
            self.assertEqual(field["post_status"], ["publish"])
            self.assertEqual(field["return_format"], "id")
        self.assertIn("category", json.dumps(groups, ensure_ascii=False))
        self.assertIn("category:74", json.dumps(groups, ensure_ascii=False))

    def test_blog_acf_copies_are_identical_and_allow_post_or_page(self):
        self.assertEqual(ACF_BLOG_SOURCE.read_bytes(), ACF_BLOG_THEME.read_bytes())
        groups = json.loads(read(ACF_BLOG_SOURCE))
        field = find_acf_field(groups, "blogseo_related_services")
        self.assertIsNotNone(field)
        self.assertEqual(set(field["post_type"]), {"post", "page"})
        self.assertFalse(field.get("taxonomy"))


class ImporterSafetyTests(unittest.TestCase):
    def source(self):
        return read(IMPORTER)

    def test_generic_acf_storage_behavior_fixture(self):
        php = os.environ.get("LAND76_PHP_BINARY") or shutil.which("php")
        if php is None:
            self.skipTest("PHP runtime is not installed")
        completed = subprocess.run(
            [php, str(ACF_STORAGE_BEHAVIOR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_stage_and_publish_pass_complete_post_map_to_every_verifier_call(self):
        source = self.source()
        build_body = php_function_body(source, "land76wp_service_hubs_build_plan")
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")
        publish_body = php_function_body(source, "land76wp_service_hubs_publish_plan")
        self.assertIn("land76wp_service_hubs_build_relation_post_ids", build_body)
        self.assertIn(
            "land76wp_service_hubs_build_validated_hub_relation_post_ids",
            build_body,
        )
        self.assertIn(
            "land76wp_service_hubs_validate_relation_operation_namespace",
            build_body,
        )
        self.assertIsNotNone(
            re.search(
                r"land76wp_service_hubs_verify_staged_item\(.*?,\s*\$relation_post_ids\s*,\s*\$required_status\s*\)",
                build_body,
                re.DOTALL,
            )
        )
        for body, expected_calls in ((stage_body, 2), (publish_body, 3)):
            calls = re.findall(
                r"land76wp_service_hubs_verify_staged_item\((.*?)\)",
                body,
                re.DOTALL,
            )
            self.assertEqual(expected_calls, len(calls))
            for call in calls:
                self.assertRegex(
                    call,
                    r",\s*\$post_ids(?:\s*,\s*'(?:draft|publish)')?\s*$",
                )

    def test_generic_acf_write_and_verify_are_bound_to_exact_schema_keys(self):
        source = self.source()
        apply_body = php_function_body(source, "land76wp_service_hubs_apply_acf")
        verify_body = php_function_body(source, "land76wp_service_hubs_verify_staged_item")
        self.assertIn("land76wp_service_hubs_resolve_acf_field", apply_body)
        self.assertIn("update_field($field['key']", apply_body)
        self.assertIn("land76wp_service_hubs_restore_raw_acf_storage", apply_body)
        self.assertIn("get_field($field['key'], $post_id, false)", verify_body)
        self.assertIn("'_' . $field_name", verify_body)
        image_validator = php_function_body(
            source,
            "land76wp_service_hubs_validate_image_attachment_id",
        )
        self.assertIn("wp_attachment_is_image($attachment_id)", image_validator)
        theme_validator = php_function_body(
            source,
            "land76wp_service_hubs_is_allowed_theme_context_image_url",
        )
        self.assertIn("is_file($image_path)", theme_validator)

    def test_managed_problem_images_merge_raw_keys_without_changing_legacy_reads(self):
        source = read(NEW_SERVICE)
        formatted_call = "get_field('ns87_problem_items', $ns87_post_context)"
        managed_guard = "if ($land76_managed_service_hub_post"
        raw_call = "get_field('field_ns87_problem_items', $ns87_post_context, false)"
        merge_call = "land76wp_service_hubs_merge_problem_item_images("
        self.assertEqual(1, source.count(raw_call))
        formatted_index = source.index(formatted_call)
        managed_index = source.index(managed_guard, formatted_index)
        raw_index = source.index(raw_call, managed_index)
        merge_index = source.index(merge_call, raw_index)
        managed_close = source.index("\n}", merge_index)
        self.assertLess(formatted_index, managed_index)
        self.assertLess(managed_index, raw_index)
        self.assertLess(raw_index, merge_index)
        self.assertLess(merge_index, managed_close)
        self.assertNotIn(raw_call, source[:managed_index])

    def test_importer_defaults_to_preview_and_contains_no_delete_api(self):
        source = self.source()
        self.assertIn("$mode = 'preview'", source)
        for forbidden in (
            "wp_delete_post",
            "wp_delete_term",
            "wp_trash_post",
            "delete_term_meta",
            "delete_post_meta",
            "$wpdb->delete",
        ):
            self.assertNotIn(forbidden, source)

    def test_forbidden_keys_are_rejected_recursively(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_reject_forbidden_keys")
        for key in FORBIDDEN_KEYS:
            self.assertIn(f"'{key}'", body)
        self.assertIn("land76wp_service_hubs_reject_forbidden_keys($value", body)

    def test_build_plan_is_pure_and_validation_precedes_mutation(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_build_plan")
        for mutation in (
            "wp_insert_post",
            "wp_update_post",
            "wp_insert_term",
            "wp_set_post_categories",
            "update_post_meta",
            "update_term_meta",
            "update_field",
            "$wpdb->query",
        ):
            self.assertNotIn(mutation, body)
        runner = php_function_body(source, "land76wp_run_service_hubs_import")
        self.assertLess(runner.index("land76wp_service_hubs_build_plan"), runner.index("land76wp_service_hubs_execute_plan"))
        self.assertIn("$mode === 'preview'", runner)

    def test_draft_and_empty_payloads_are_nonapplicable_or_rejected(self):
        source = self.source()
        self.assertIn("release_status", source)
        self.assertIn("draft", source)
        self.assertIn("ready", source)
        self.assertIn("empty_payload", source)
        self.assertIn("draft_release_apply_forbidden", source)
        self.assertIn("applicable", source)

    def test_plan_and_result_expose_required_stats(self):
        source = self.source()
        for key in (
            "planned",
            "created",
            "updated",
            "unchanged",
            "unresolved_cases",
            "errors",
            "rollback_snapshot",
        ):
            self.assertIn(f"'{key}'", source)

    def test_transaction_rolls_back_on_any_throwable_path(self):
        source = self.source()
        self.assertIn("START TRANSACTION", source)
        self.assertIn("COMMIT", source)
        self.assertIn("ROLLBACK", source)
        self.assertIn("catch (Throwable $error)", source)
        self.assertIn("rollback_snapshot", source)
        self.assertIn("transaction_start_failed", source)
        self.assertIn("transaction_commit_failed", source)
        self.assertIn("transaction_rollback_failed", source)

    def test_exact_ownership_checksum_and_no_slug_adoption(self):
        source = self.source()
        for key in (
            "_land76_release_id",
            "_land76_manifest_sha256",
            "_land76_page_key",
            "_land76_service_id",
            "_land76_topic_key",
            "_land76_canonical",
            "_land76_import_owner",
            "_land76_import_checksum",
        ):
            self.assertIn(key, source)
        self.assertIn(IMPORT_OWNER, source)
        self.assertIn("hash_equals", source)
        self.assertIn("slug_conflict", source)
        self.assertIn("published_record_cannot_be_restaged", source)
        self.assertIn("checksum", source)
        self.assertIn("land76wp_service_hubs_find_page_key_posts", source)
        self.assertIn("page_key_conflict", source)

    def test_reuse_contract_allowlist_is_exact_and_frozen(self):
        source = self.source()
        match = re.search(
            r"<<<'LAND76_SERVICE_HUB_REUSE_CONTRACTS_JSON'\s*(.*?)\s*"
            r"LAND76_SERVICE_HUB_REUSE_CONTRACTS_JSON;",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "reuse owners need one frozen JSON allowlist")
        contracts = json.loads(match.group(1).strip())
        required_contracts = {
            "S7-CHILD-HOLIDAY": {
                "page_key": "S7-CHILD-HOLIDAY",
                "service_id": "S7",
                "post_id": 10381,
                "post_type": "page",
                "post_status": "publish",
                "slug": "novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti",
                "parent_id": 0,
                "current_url": "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
                "target_url": "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
                "legacy_template": "servicepost.php",
                "target_template": "servicepost.php",
            },
        }
        self.assertEqual(required_contracts, contracts)
        self.assertNotIn("S5-CHILD-STUMPS", contracts)
        reuse_registry = php_function_body(
            source, "land76wp_service_hubs_reuse_contracts"
        )
        self.assertNotIn("count($decoded) !== 2", reuse_registry)
        for marker in (
            "foreach ($decoded",
            "array_keys",
            "page_key",
            "post_id",
            "current_url",
            "target_url",
            "legacy_template",
            "target_template",
        ):
            self.assertIn(marker, reuse_registry)

    def test_reuse_planner_accepts_only_exact_legacy_or_managed_owner(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_plan_reuse_item")
        for marker in (
            "get_post",
            "get_permalink",
            "get_page_template_slug",
            "land76wp_service_hubs_find_page_key_posts",
            "land76wp_service_hubs_find_global_slug_posts",
            "reuse_contract_mismatch",
            "reuse_missing_post",
            "reuse_id_mismatch",
            "reuse_type_mismatch",
            "reuse_status_mismatch",
            "reuse_slug_mismatch",
            "reuse_parent_mismatch",
            "reuse_url_mismatch",
            "reuse_template_mismatch",
            "reuse_owner_mismatch",
            "reuse_partial_owner",
            "reuse_update",
        ):
            self.assertIn(marker, body)
        self.assertIn("land76wp_service_hubs_import_owner", body)
        self.assertIn("_land76_import_owner", body)
        self.assertIn("_land76_page_key", body)
        self.assertIn("_land76_service_id", body)
        self.assertIn("_land76_topic_key", body)
        self.assertIn("_land76_canonical", body)
        self.assertIn("_land76_release_id", body)
        self.assertIn("_land76_manifest_sha256", body)
        self.assertIn("_land76_import_checksum", body)
        plan_body = php_function_body(source, "land76wp_service_hubs_plan_item")
        self.assertIn("land76wp_service_hubs_reuse_contract_for_item", plan_body)
        self.assertIn("land76wp_service_hubs_plan_reuse_item", plan_body)

    def test_stage_verifies_but_never_mutates_published_reuse_owners(self):
        source = self.source()
        revalidate = php_function_body(
            source, "land76wp_service_hubs_revalidate_stage_targets"
        )
        self.assertIn("reuse_update", revalidate)
        self.assertIn("land76wp_service_hubs_verify_reuse_target", revalidate)
        stage = php_function_body(source, "land76wp_service_hubs_execute_stage")
        self.assertGreaterEqual(stage.count("reuse_update"), 3)
        self.assertIn("land76wp_service_hubs_verify_reuse_target", stage)
        self.assertLess(
            stage.index("land76wp_service_hubs_revalidate_stage_targets"),
            stage.index("START TRANSACTION"),
        )

    def test_reuse_publish_revalidates_snapshots_and_rolls_back(self):
        source = self.source()
        publish = php_function_body(source, "land76wp_service_hubs_publish_plan")
        self.assertGreaterEqual(
            publish.count("land76wp_service_hubs_verify_reuse_target"), 3
        )
        self.assertLess(
            publish.index("land76wp_service_hubs_verify_reuse_target"),
            publish.index("START TRANSACTION"),
        )
        inside_verify = publish.index(
            "land76wp_service_hubs_verify_reuse_target",
            publish.index("START TRANSACTION"),
        )
        snapshot = publish.index("land76wp_service_hubs_snapshot_post", inside_verify)
        apply_update = publish.index(
            "land76wp_service_hubs_apply_reuse_item", snapshot
        )
        self.assertLess(inside_verify, snapshot)
        self.assertLess(snapshot, apply_update)
        self.assertIn("ROLLBACK", publish)
        self.assertIn("publish_rollback", publish)

    def test_reuse_update_preserves_id_type_slug_parent_status_and_permalink(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_apply_reuse_item")
        for marker in (
            "wp_update_post",
            "_wp_page_template",
            "target_template",
            "land76wp_service_hubs_apply_post_metadata",
            "wp_set_post_categories",
        ):
            self.assertIn(marker, body)
        for forbidden in ("post_type", "post_status", "post_name", "post_parent"):
            self.assertNotIn(forbidden, body)
        snapshot = php_function_body(source, "land76wp_service_hubs_snapshot_post")
        for marker in (
            "post_type",
            "post_status",
            "post_name",
            "post_parent",
            "permalink",
            "template",
            "post_content_sha256",
        ):
            self.assertIn(marker, snapshot)

    def test_reuse_page_keys_resolve_only_through_the_frozen_managed_owner(self):
        body = php_function_body(
            self.source(), "land76wp_service_hubs_resolve_page_key"
        )
        for marker in (
            "land76wp_service_hubs_reuse_contracts",
            "get_post",
            "get_permalink",
            "get_page_template_slug",
            "_land76_import_owner",
            "_land76_page_key",
            "_land76_service_id",
            "_land76_topic_key",
            "target_template",
            "target_url",
        ):
            self.assertIn(marker, body)

    def test_servicepost_routes_only_managed_child_pages_to_new_template(self):
        source = read(SERVICEPOST)
        for marker in (
            "land76_service_v2_current",
            "get_queried_object_id",
            "land76wp_claims_managed_service_hub_post",
            "land76wp_managed_page_contract",
            "['role'] !== 'child'",
            "status_header(404)",
            "nocache_headers()",
            "get_header('seo')",
            "/inc/newservicepost.php",
            "get_footer()",
            "return;",
            "get_header('service')",
        ):
            self.assertIn(marker, source)
        owner_check = source.index("land76wp_claims_managed_service_hub_post")
        contract_check = source.index("land76wp_managed_page_contract", owner_check)
        not_found = source.index("status_header(404)", contract_check)
        managed_render = source.index("/inc/newservicepost.php", not_found)
        service_v2 = source.index("land76_service_v2_current", managed_render)
        legacy_render = source.index("get_header('service')", service_v2)
        self.assertLess(
            owner_check,
            contract_check,
        )
        self.assertLess(
            contract_check,
            not_found,
        )
        self.assertLess(not_found, managed_render)
        self.assertLess(managed_render, service_v2)
        self.assertLess(service_v2, legacy_render)

    def test_importer_accepts_exact_service_range_s1_s15(self):
        source = self.source()
        for marker in (
            "S(?:[1-9]|1[0-5])-(?:CHILD|ARTICLE|GEO)-",
            "S(?:[1-9]|1[0-5])-CHILD-",
            "S(?:[1-9]|1[0-5])-HUB",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("S[1-8]", source)

    def test_item_contract_binds_page_key_role_and_requires_seo(self):
        body = php_function_body(self.source(), "land76wp_service_hubs_validate_item")
        for marker in (
            "expected_role_token",
            "page_key_ownership_mismatch",
            "missing_seo",
            "invalid_seo",
        ):
            self.assertIn(marker, body)
        self.assertIn("$service_id . '-' . $expected_role_token . '-'", body)

    def test_relations_are_typed_unambiguous_and_preflighted(self):
        source = self.source()
        validate_body = php_function_body(source, "land76wp_service_hubs_validate_item")
        for marker in (
            "ambiguous_managed_acf_field",
            "ambiguous_related_services",
        ):
            self.assertIn(marker, validate_body)
        service_reference_body = php_function_body(
            source, "land76wp_service_hubs_validate_related_service_references"
        )
        relation_list_body = php_function_body(source, "land76wp_service_hubs_validate_relation_list")
        self.assertIn("invalid_related_service_reference", service_reference_body)
        self.assertIn("duplicate_relation", service_reference_body)
        self.assertIn("duplicate_relation", relation_list_body)
        build_body = php_function_body(source, "land76wp_service_hubs_build_plan")
        self.assertIn("land76wp_service_hubs_preflight_external_relations", build_body)
        preflight_body = php_function_body(source, "land76wp_service_hubs_preflight_external_relations")
        self.assertIn("land76wp_service_hubs_resolve_related_slugs", preflight_body)
        self.assertIn("land76wp_service_hubs_resolve_page_key", preflight_body)

    def test_articles_require_a_primary_relation_owned_by_the_same_service(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_preflight_external_relations")
        self.assertIn("missing_primary_commercial_relation", body)
        self.assertIn("$has_primary_commercial", body)
        self.assertIn("land76wp_service_hubs_service_id_for_post", body)

    def test_stage_uses_drafts_and_managed_categories_preserve_unrelated_terms(self):
        source = self.source()
        self.assertIn("'post_status' => 'draft'", source)
        self.assertIn("land76wp_service_hubs_merge_categories", source)
        body = php_function_body(source, "land76wp_service_hubs_merge_categories")
        self.assertIn("72", body)
        self.assertIn("74", body)
        self.assertIn("array_diff", body)
        self.assertIn("array_unique", body)
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")
        self.assertIn("$operation['action'] === 'create' ? array()", stage_body)

    def test_publish_keeps_normal_records_status_only_and_isolates_reuse_updates(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_publish_plan")
        self.assertIn("land76wp_service_hubs_verify_staged_item", body)
        self.assertIn("land76wp_service_hubs_apply_reuse_item", body)
        self.assertIn("wp_update_post", body)
        self.assertIn("'post_status' => 'publish'", body)
        for mutation in (
            "wp_insert_post",
            "wp_insert_term",
            "wp_set_post_categories",
            "update_post_meta",
            "update_term_meta",
            "update_field",
        ):
            self.assertNotIn(mutation, body)
        self.assertIn(
            "if ($publish_ids === array() && $reuse_operations === array())", body
        )
        self.assertGreaterEqual(body.count("land76wp_service_hubs_verify_staged_item"), 2)

    def test_stage_revalidates_targets_and_verifies_outputs_before_commit(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_execute_stage")
        self.assertIn("land76wp_service_hubs_revalidate_stage_targets", body)
        self.assertIn("land76wp_service_hubs_verify_staged_item", body)
        self.assertIn("'draft'", body)
        self.assertLess(body.index("land76wp_service_hubs_revalidate_stage_targets"), body.index("land76wp_service_hubs_install_missing_acf_schema"))
        self.assertLess(body.index("land76wp_service_hubs_verify_staged_item"), body.index("COMMIT"))

    def test_stage_holds_a_fail_closed_release_lock_through_commit_or_rollback(self):
        source = self.source()
        lock_name_body = php_function_body(
            source, "land76wp_service_hubs_release_lock_name"
        )
        acquire_body = php_function_body(
            source, "land76wp_service_hubs_acquire_release_lock"
        )
        release_body = php_function_body(
            source, "land76wp_service_hubs_release_release_lock"
        )
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")

        self.assertIn("land76wp_service_hubs_import_owner", lock_name_body)
        self.assertIn("$release_id", lock_name_body)
        self.assertIn("hash(", lock_name_body)
        self.assertIn("'sha256'", lock_name_body)
        self.assertIn("GET_LOCK", acquire_body)
        self.assertIn(", 0)", acquire_body)
        self.assertIn("!== '1'", acquire_body)
        self.assertIn("RELEASE_LOCK", release_body)
        self.assertIn("land76wp_service_hubs_acquire_release_lock", stage_body)
        self.assertIn("stage_lock_unavailable", stage_body)
        self.assertIn("finally", stage_body)
        self.assertIn("land76wp_service_hubs_release_release_lock", stage_body)
        self.assertLess(
            stage_body.index("land76wp_service_hubs_acquire_release_lock"),
            stage_body.index("land76wp_service_hubs_revalidate_stage_targets"),
        )
        self.assertLess(
            stage_body.index("COMMIT"),
            stage_body.rindex("land76wp_service_hubs_release_release_lock"),
        )
        self.assertLess(
            stage_body.index("ROLLBACK"),
            stage_body.rindex("land76wp_service_hubs_release_release_lock"),
        )

    def test_stage_lock_rejects_connection_drift_before_mutation_and_commit(self):
        source = self.source()
        lock_name_body = php_function_body(
            source, "land76wp_service_hubs_release_lock_name"
        )
        acquire_body = php_function_body(
            source, "land76wp_service_hubs_acquire_release_lock"
        )
        owns_body = php_function_body(
            source, "land76wp_service_hubs_owns_release_lock"
        )
        release_body = php_function_body(
            source, "land76wp_service_hubs_release_release_lock"
        )
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")

        for identity_marker in ("$wpdb->dbname", "$wpdb->prefix", "home_url"):
            self.assertIn(identity_marker, lock_name_body)
        self.assertIn("CONNECTION_ID()", acquire_body)
        self.assertIn("'connection_id'", acquire_body)
        self.assertIn("CONNECTION_ID()", owns_body)
        self.assertIn("IS_USED_LOCK", owns_body)
        self.assertIn("$lock['connection_id']", owns_body)
        self.assertIn("land76wp_service_hubs_owns_release_lock", release_body)
        self.assertLess(
            release_body.index("land76wp_service_hubs_owns_release_lock"),
            release_body.index("RELEASE_LOCK"),
        )

        ownership_checks = [
            index
            for index in range(len(stage_body))
            if stage_body.startswith("land76wp_service_hubs_owns_release_lock", index)
        ]
        self.assertGreaterEqual(len(ownership_checks), 2)
        self.assertLess(
            ownership_checks[0],
            stage_body.index("land76wp_service_hubs_install_missing_acf_schema"),
        )
        self.assertLess(
            stage_body.rindex("land76wp_service_hubs_verify_staged_item"),
            ownership_checks[-1],
        )
        self.assertLess(ownership_checks[-1], stage_body.index("COMMIT"))
        self.assertIn("stage_lock_lost", stage_body)

    def test_stage_disables_wpdb_reconnect_for_the_entire_mutation_window(self):
        source = self.source()
        pin_body = php_function_body(
            source, "land76wp_service_hubs_pin_wpdb_connection"
        )
        restore_body = php_function_body(
            source, "land76wp_service_hubs_restore_wpdb_connection"
        )
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")

        for marker in ("ReflectionObject", "reconnect_retries", "setValue", "0"):
            self.assertIn(marker, pin_body)
        self.assertIn("reconnect_retries", restore_body)
        self.assertIn("setValue", restore_body)
        self.assertIn("land76wp_service_hubs_pin_wpdb_connection", stage_body)
        self.assertIn("stage_connection_pin_unavailable", stage_body)
        self.assertIn("land76wp_service_hubs_restore_wpdb_connection", stage_body)
        self.assertLess(
            stage_body.index("land76wp_service_hubs_pin_wpdb_connection"),
            stage_body.index("land76wp_service_hubs_revalidate_stage_targets"),
        )
        self.assertLess(
            stage_body.index("land76wp_service_hubs_release_release_lock"),
            stage_body.index("land76wp_service_hubs_restore_wpdb_connection"),
        )

    def test_connection_pin_rejects_an_unknown_wpdb_reconnect_implementation(self):
        body = php_function_body(
            self.source(), "land76wp_service_hubs_pin_wpdb_connection"
        )
        self.assertIn("getMethod('query')", body)
        self.assertIn("getMethod('_do_query')", body)
        self.assertIn("getMethod('check_connection')", body)
        self.assertIn("getDeclaringClass()->getName()", body)
        self.assertGreaterEqual(body.count("!== 'wpdb'"), 4)

    def test_publish_uses_the_same_pinned_lock_around_every_status_mutation(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_publish_plan")

        for marker in (
            "land76wp_service_hubs_acquire_release_lock",
            "land76wp_service_hubs_pin_wpdb_connection",
            "publish_lock_unavailable",
            "publish_connection_pin_unavailable",
            "land76wp_service_hubs_release_release_lock",
            "land76wp_service_hubs_restore_wpdb_connection",
            "land76wp_service_hubs_owns_release_lock",
            "publish_lock_lost",
            "START TRANSACTION",
            "COMMIT",
            "ROLLBACK",
            "finally",
        ):
            self.assertIn(marker, body)

        mutation_index = body.index("wp_update_post")
        self.assertLess(
            body.index("land76wp_service_hubs_owns_release_lock"), mutation_index
        )
        self.assertGreater(
            body.index("land76wp_service_hubs_owns_release_lock", mutation_index),
            mutation_index,
        )
        self.assertLess(
            body.index("land76wp_service_hubs_acquire_release_lock"),
            body.index("land76wp_service_hubs_verify_staged_item"),
        )
        self.assertLess(
            body.index("COMMIT"),
            body.rindex("land76wp_service_hubs_release_release_lock"),
        )
        self.assertLess(
            body.index("ROLLBACK"),
            body.rindex("land76wp_service_hubs_release_release_lock"),
        )

    def test_staged_verifier_rechecks_content_acf_media_categories_and_relations(self):
        body = php_function_body(self.source(), "land76wp_service_hubs_verify_staged_item")
        for marker in (
            "post_content",
            "post_title",
            "get_field",
            "_land76_related_article_ids",
            "blogseo_related_services",
            "_aioseo_title",
            "_aioseo_description",
            "_wp_page_template",
            "get_post_thumbnail_id",
            "wp_get_post_categories",
            "other_grouping_ids",
        ):
            self.assertIn(marker, body)

    def test_draft_verification_never_uses_the_plain_draft_permalink(self):
        source = self.source()
        permalink_body = php_function_body(
            source, "land76wp_service_hubs_verify_published_permalink"
        )
        self.assertIn("$post->post_status !== 'publish'", permalink_body)
        self.assertLess(
            permalink_body.index("$post->post_status !== 'publish'"),
            permalink_body.index("get_permalink"),
        )
        verifier_body = php_function_body(source, "land76wp_service_hubs_verify_staged_item")
        self.assertIn("land76wp_service_hubs_verify_published_permalink", verifier_body)
        self.assertNotIn("get_permalink", verifier_body)

    def test_release_manifest_exactly_binds_payload_page_keys_and_checksums(self):
        source = self.source()
        binding_body = php_function_body(
            source, "land76wp_service_hubs_validate_manifest_binding"
        )
        for marker in (
            "manifest_hash_mismatch",
            "manifest_release_mismatch",
            "manifest_inventory_mismatch",
            "page_key",
            "checksum",
            "source_manifest_sha256",
        ):
            self.assertIn(marker, binding_body)
        runner_body = php_function_body(source, "land76wp_run_service_hubs_import")
        self.assertIn("land76wp_service_hubs_default_release_manifest_path", runner_body)
        self.assertIn("land76wp_service_hubs_validate_manifest_binding", runner_body)
        self.assertLess(
            runner_body.index("land76wp_service_hubs_validate_manifest_binding"),
            runner_body.index("land76wp_service_hubs_build_plan"),
        )

    def test_geo_resolution_is_exact_and_requires_local_evidence(self):
        source = self.source()
        body = php_function_body(source, "land76wp_service_hubs_plan_geo_item")
        for marker in (
            "post_parent",
            "post_name",
            "publish",
            "global_slug_collision",
            "duplicate_geo_child",
            "local_evidence",
            "case_ids",
            "page-service-hub-region.php",
        ):
            self.assertIn(marker, body)
        self.assertIn("if ($local_evidence === array())", body)
        self.assertIn("(int) $city_parent->post_parent !== 0", body)
        validate_body = php_function_body(source, "land76wp_service_hubs_validate_local_evidence")
        self.assertIn("invalid_local_evidence", validate_body)
        self.assertIn("land76wp_service_hubs_is_list", validate_body)

    def test_acf_is_verified_before_apply_and_omitted_values_are_preserved(self):
        source = self.source()
        self.assertIn("land76wp_service_hubs_verify_acf_schema", source)
        self.assertIn("acf_unavailable", source)
        self.assertIn("acf_schema_incompatible", source)
        self.assertIn("array_key_exists", source)
        self.assertIn("selected_works_posts", source)
        self.assertIn("selected_real_projects", source)
        verify_body = php_function_body(source, "land76wp_service_hubs_verify_acf_schema")
        self.assertIn("acf_get_field($field_key)", verify_body)
        self.assertIn("acf_get_field_group", verify_body)
        self.assertIn("acf_group_incompatible", verify_body)
        self.assertIn("group_land76_service_hub_category_relations", source)
        self.assertIn("group_land76_service_hub_post_relations", source)
        self.assertIn("group_blogseo_post", source)
        validate_body = php_function_body(source, "land76wp_service_hubs_validate_item")
        self.assertIn("forbidden_acf_field", validate_body)
        build_body = php_function_body(source, "land76wp_service_hubs_build_plan")
        self.assertIn("land76wp_service_hubs_preflight_item_acf", build_body)
        preflight_body = php_function_body(source, "land76wp_service_hubs_preflight_item_acf")
        self.assertIn("acf_get_field", preflight_body)
        self.assertIn("unknown_acf_field", preflight_body)

    def test_only_the_exact_known_legacy_blog_relation_schema_is_migratable(self):
        source = self.source()
        legacy_body = php_function_body(
            source, "land76wp_service_hubs_is_exact_legacy_blog_relation"
        )
        for marker in (
            "field_blogseo_related_services",
            "group_blogseo_post",
            "category:74",
            "'post_type' => array('post')",
            "'post_status' => array('publish')",
            "'filters' => array('search', 'taxonomy')",
            "'return_format' => 'id'",
        ):
            self.assertIn(marker, legacy_body)
        self.assertIn("land76wp_service_hubs_acf_group_definition_matches", legacy_body)
        self.assertNotIn("land76wp_service_hubs_acf_group_matches", legacy_body)
        verify_body = php_function_body(source, "land76wp_service_hubs_verify_acf_schema")
        self.assertIn("land76wp_service_hubs_inspect_blog_relation", verify_body)
        self.assertIn("land76wp_service_hubs_blog_relation_group", verify_body)
        self.assertIn("acf_get_raw_field_group", verify_body)
        self.assertIn("$result['migrations'][]", verify_body)
        inspect_body = php_function_body(
            source, "land76wp_service_hubs_inspect_blog_relation"
        )
        self.assertIn("land76wp_service_hubs_is_exact_legacy_blog_relation", inspect_body)
        self.assertIn("land76wp_service_hubs_blog_relation_candidate_fields", inspect_body)
        self.assertIn("acf_schema_incompatible", inspect_body)
        candidates_body = php_function_body(
            source, "land76wp_service_hubs_blog_relation_candidate_fields"
        )
        for marker in (
            "post_type = %s",
            "post_status = %s",
            "post_name = %s",
            "ORDER BY ID ASC",
            "FOR UPDATE",
            "acf_get_raw_field",
            "clean_post_cache",
        ):
            self.assertIn(marker, candidates_body)
        group_body = php_function_body(
            source, "land76wp_service_hubs_blog_relation_group"
        )
        for marker in (
            "post_type = %s",
            "post_status = %s",
            "post_name = %s",
            "ORDER BY ID ASC",
            "FOR UPDATE",
            "clean_post_cache",
            "acf_get_raw_field_group",
        ):
            self.assertIn(marker, group_body)

    def test_legacy_acf_migration_is_targeted_and_runs_inside_stage_transaction(self):
        source = self.source()
        migrate_body = php_function_body(
            source, "land76wp_service_hubs_migrate_legacy_blog_relation"
        )
        self.assertIn("field_blogseo_related_services", migrate_body)
        self.assertIn("acf_update_field", migrate_body)
        self.assertIn("land76wp_service_hubs_inspect_blog_relation", migrate_body)
        self.assertIn("$candidate_ids", migrate_body)
        self.assertIn("$candidate_parents", migrate_body)
        self.assertIn("$verified_ids", migrate_body)
        self.assertIn("$verified_parents", migrate_body)
        self.assertIn("$target_field['ID']", migrate_body)
        self.assertIn("$target_field['parent']", migrate_body)
        self.assertNotIn("acf_update_field_group", migrate_body)
        for destructive_marker in (
            "acf_delete_field",
            "wp_delete_post",
            "wp_trash_post",
            "DELETE FROM",
        ):
            self.assertNotIn(destructive_marker, migrate_body)
        install_body = php_function_body(source, "land76wp_service_hubs_install_missing_acf_schema")
        self.assertIn("$migrations", install_body)
        self.assertIn("land76wp_service_hubs_migrate_legacy_blog_relation", install_body)
        stage_body = php_function_body(source, "land76wp_service_hubs_execute_stage")
        self.assertLess(stage_body.index("START TRANSACTION"), stage_body.index("land76wp_service_hubs_install_missing_acf_schema"))
        self.assertLess(stage_body.index("land76wp_service_hubs_install_missing_acf_schema"), stage_body.index("COMMIT"))

    def test_case_ids_must_resolve_to_published_case_pages(self):
        registry = read(REGISTRY)
        predicate = php_function_body(
            registry, "land76wp_is_supported_case_template"
        )
        self.assertIn(
            "return in_array((string) $template, array('casenew.php', 'portfoliopost.php'), true);",
            predicate,
        )
        self.assertEqual(1, registry.count("'casenew.php'"))
        self.assertEqual(1, registry.count("'portfoliopost.php'"))

        importer = php_function_body(
            self.source(), "land76wp_service_hubs_validate_case_ids"
        )
        self.assertIn("post_type !== 'page'", importer)
        self.assertIn("post_status !== 'publish'", importer)
        self.assertIn(
            "land76wp_is_supported_case_template(get_page_template_slug($case_id))",
            importer,
        )

        schema = php_function_body(read(FUNCTIONS), "land76_schema_is_case_template")
        self.assertIn(
            "land76wp_is_supported_case_template(get_page_template_slug(get_queried_object_id()))",
            schema,
        )

        region = read(REGION_TEMPLATE)
        self.assertIn(
            "land76wp_is_supported_case_template(get_page_template_slug($land76_region_case->ID))",
            region,
        )
        for consumer in (importer, schema, region):
            self.assertNotIn("casenew.php", consumer)
            self.assertNotIn("portfoliopost.php", consumer)

        seo_case = php_function_body(read(FUNCTIONS), "land76_is_case_seo_template")
        self.assertIn("is_page_template('casenew.php')", seo_case)
        self.assertNotIn("portfoliopost.php", seo_case)

    def test_main_image_must_resolve_to_an_image_attachment(self):
        body = php_function_body(self.source(), "land76wp_service_hubs_validate_item")
        self.assertIn("attachment_url_to_postid", body)
        self.assertIn("get_post_mime_type", body)
        self.assertIn("image/", body)

    def test_presentation_images_validate_store_and_verify_each_media_role(self):
        source = self.source()
        validator = php_function_body(
            source, "land76wp_service_hubs_validate_presentation_images"
        )
        for marker in (
            "hero",
            "context",
            "card",
            "https://exp76.ru/wp-content/themes/land76wp/generated/context/",
            "context-photo-",
            ".webp",
            "get_template_directory",
            "is_file",
        ):
            self.assertIn(marker, validator)
        self.assertNotIn("attachment_url_to_postid", validator)
        item_validator = php_function_body(source, "land76wp_service_hubs_validate_item")
        self.assertIn("land76wp_service_hubs_validate_presentation_images", item_validator)

        apply_body = php_function_body(
            source, "land76wp_service_hubs_apply_post_metadata"
        )
        verify_body = php_function_body(
            source, "land76wp_service_hubs_verify_staged_item"
        )
        meta_keys_body = php_function_body(
            source, "land76wp_service_hubs_presentation_meta_keys"
        )
        for role in ("hero", "context", "card"):
            for field in ("url", "alt"):
                meta_key = f"_land76_{role}_image_{field}"
                self.assertIn(meta_key, meta_keys_body)
        self.assertIn("land76wp_service_hubs_presentation_meta_keys", apply_body)
        self.assertIn("land76wp_service_hubs_presentation_meta_keys", verify_body)
        self.assertIn("_land76_main_image_url", apply_body)
        self.assertIn("set_post_thumbnail", apply_body)

    def test_new_runner_never_calls_legacy_importers(self):
        source = self.source()
        for token in (
            "land76wp_run_drenazh_import",
            "land76wp_run_otmostka_import",
            "land76wp_run_plitka_import",
            "land76wp_run_osushenie_import",
            "land76wp_run_livnevka_import",
            "land76wp_run_autopoliv_import",
        ):
            self.assertNotIn(token, source)

    def test_admin_tools_runner_is_post_nonce_and_confirmation_guarded(self):
        source = self.source()
        self.assertIn("add_management_page", source)
        self.assertIn("manage_options", source)
        self.assertIn("check_admin_referer", source)
        self.assertIn("REQUEST_METHOD", source)
        self.assertIn("POST", source)
        self.assertIn("confirmation_release_id", source)
        self.assertIn("hash_equals", source)
        self.assertIn("land76wp_run_service_hubs_import($json_path, 'preview')", source)
        render_body = php_function_body(source, "land76wp_service_hubs_render_tools_page")
        self.assertIn("land76wp_service_hubs_execute_plan($preview, $requested_mode)", render_body)
        self.assertEqual(render_body.count("land76wp_run_service_hubs_import"), 1)
        self.assertNotIn("$_GET", source)

    def test_grouping_verifier_rechecks_every_owned_meta_field(self):
        body = php_function_body(self.source(), "land76wp_service_hubs_verify_grouping_terms")
        for key in (
            "_land76_release_id",
            "_land76_manifest_sha256",
            "_land76_page_key",
            "_land76_service_id",
            "_land76_topic_key",
            "_land76_canonical",
            "_land76_archive_policy",
            "_land76_import_owner",
            "_land76_import_checksum",
            "_land76_hub_url",
        ):
            self.assertIn(key, body)

    def test_php_uses_php_74_compatible_syntax(self):
        source = self.source() + read(REGISTRY) + read(REGION_TEMPLATE)
        for unsupported in ("str_contains(", "str_starts_with(", "match (", "fn(", "readonly "):
            self.assertNotIn(unsupported, source)


class ThemeRoutingTests(unittest.TestCase):
    def test_functions_only_adds_registry_and_isolated_runner_requires(self):
        source = read(FUNCTIONS)
        expected_old = (
            "service-v2.php",
            "legal-pages.php",
            "import-drenazh.php",
            "import-drenazh-blog.php",
            "import-otmostka.php",
            "import-otmostka-blog.php",
            "import-plitka.php",
            "import-plitka-blog.php",
            "import-osushenie.php",
            "import-osushenie-blog.php",
            "import-livnevka.php",
            "import-livnevka-blog.php",
            "import-autopoliv.php",
            "import-autopoliv-blog.php",
            "import-case-seo.php",
            "import-service-previews.php",
            "seo-category-indexing.php",
            "indexnow.php",
        )
        for filename in expected_old:
            self.assertIn(filename, source)
        self.assertIn("service-hub-registry.php", source)
        self.assertIn("import-service-hubs.php", source)
        self.assertLess(source.index("service-hub-registry.php"), source.index("import-service-hubs.php"))

    def test_service_and_article_templates_use_explicit_topic_and_registry(self):
        service = read(NEW_SERVICE)
        article = read(SEO_BLOG)
        for source in (service, article):
            self.assertIn("_land76_topic_key", source)
            self.assertIn("land76wp_service_hub_registry", source)
            self.assertIn("_land76_import_owner", source)
        self.assertIn("_land76_main_image_url", service)
        self.assertIn("_land76_main_image_alt", service)
        self.assertIn("_land76_related_article_ids", service)
        self.assertIn("blogseo_related_services", article)

    def test_rendered_relations_fail_closed_on_status_and_managed_role(self):
        service = read(NEW_SERVICE)
        article = read(SEO_BLOG)
        for source in (service, article):
            self.assertIn("post_status !== 'publish'", source)
            self.assertIn("_land76_page_key", source)
        self.assertIn("-ARTICLE-", service)
        self.assertIn("-CHILD-", article)
        self.assertIn("hub_post_id", article)

    def test_related_cards_render_target_card_image_alt_with_proof_fallback(self):
        service = read(NEW_SERVICE)
        helper = php_function_body(service, "land76_newservice_related_card_image")
        self.assertIn("foreach (array('card', 'main') as $role)", helper)
        self.assertIn("land76_service_v2_load", helper)
        self.assertIn("['hero']['image']['url']", helper)
        self.assertIn("['hero']['image']['alt']", helper)
        self.assertIn(
            "land76_newservice_related_card_image($ns87_related_service_id)",
            service,
        )
        for marker in (
            "_land76_card_image_url",
            "_land76_card_image_alt",
            "_land76_main_image_url",
            "_land76_main_image_alt",
        ):
            self.assertGreaterEqual(service.count(marker), 1, marker)
        for marker in (
            'loading="lazy"',
            'decoding="async"',
            'class="service__img"',
        ):
            self.assertGreaterEqual(service.count(marker), 2, marker)
        css = read(SERVICEPOST_CSS)
        self.assertIn(".service-related-card-image", css)
        self.assertIn("object-fit: cover", css)

    def test_managed_templates_do_not_use_drainage_fallback(self):
        service = read(NEW_SERVICE)
        article = read(SEO_BLOG)
        self.assertIn("$land76_managed_service_hub_post", service)
        self.assertIn("$land76_managed_service_hub_post", article)
        self.assertRegex(service, r"if\s*\(\s*!\s*\$land76_managed_service_hub_post[^)]*\).*drenazh")
        self.assertRegex(article, r"if\s*\(\s*!\s*\$land76_managed_service_hub_post[^)]*\).*drenazh")
        self.assertIn("_land76_import_owner", service)
        self.assertIn("_land76_import_owner", article)
        context_body = php_function_body(service, "land76_newservice_context_image")
        self.assertIn("!isset($rules[$topic_key])", context_body)

    def test_grouping_archives_redirect_without_changing_legacy_indexable_ids(self):
        source = read(SEO_INDEXING)
        self.assertIn("return array(87, 88, 89, 90, 91, 92);", source)
        self.assertIn("land76wp_service_hub_by_grouping_slug", source)
        self.assertIn("wp_safe_redirect", source)
        self.assertIn("redirect_canonical", source)
        self.assertIn("wp_sitemaps_taxonomies_query_args", source)
        self.assertIn("aioseo_sitemap_terms", source)
        self.assertNotIn("aioseo_sitemap_exclude_terms", source)
        self.assertNotIn("87, 88, 89, 90, 91, 92,", source)

    def test_grouping_routing_requires_the_complete_owned_term_contract(self):
        source = read(SEO_INDEXING)
        ownership_body = php_function_body(
            source, "land76_is_owned_service_hub_grouping_term"
        )
        for marker in (
            "_land76_release_id",
            "_land76_manifest_sha256",
            "_land76_page_key",
            "_land76_service_id",
            "_land76_topic_key",
            "_land76_canonical",
            "_land76_hub_url",
            "_land76_archive_policy",
            "_land76_import_owner",
            "_land76_import_checksum",
            "land76wp_service_hubs_expected_release_id",
            "land76wp_service_hubs_term_checksum",
        ):
            self.assertIn(marker, ownership_body)
        archive_body = php_function_body(source, "land76_service_hub_grouping_for_current_archive")
        sitemap_body = php_function_body(source, "land76_service_hub_grouping_term_ids")
        self.assertIn("land76_is_owned_service_hub_grouping_term", archive_body)
        self.assertIn("land76_is_owned_service_hub_grouping_term", sitemap_body)

    def test_region_template_fails_closed_and_uses_shared_components(self):
        source = read(REGION_TEMPLATE)
        for marker in (
            "Template Name: Service Hub Region",
            "_land76_service_id",
            "_land76_region",
            "_land76_local_evidence",
            "post_parent",
            "land76wp_service_hub_by_service_id",
            "service-v2-template.php",
            "status_header(404)",
            "_land76_import_owner",
            "_land76_page_key",
            "_land76_topic_key",
            "_land76_main_image_url",
            "_land76_main_image_alt",
            "selected_real_projects",
            "land76wp_is_supported_case_template",
        ):
            self.assertIn(marker, source)

    def test_isolated_relation_resolver_checks_post_and_page_exact_canonical(self):
        source = read(IMPORTER)
        body = php_function_body(source, "land76wp_service_hubs_resolve_related_slugs")
        lookup_body = php_function_body(source, "land76wp_service_hubs_find_global_slug_posts")
        self.assertIn("'post'", lookup_body)
        self.assertIn("'page'", lookup_body)
        self.assertIn("get_permalink", body)
        self.assertIn("_land76_canonical", body)
        self.assertIn("related_role_mismatch", body)
        self.assertIn("hub_post_id", body)
        self.assertIn("has_category(74", body)


class BackwardCompatibilityTests(unittest.TestCase):
    def test_legacy_importers_are_byte_identical(self):
        for name, expected in LEGACY_IMPORT_HASHES.items():
            self.assertEqual(sha256(INC / name), expected, name)

    def test_hardened_legacy_cta_templates_are_byte_identical(self):
        for name, expected in LEGACY_CATEGORY_HASHES.items():
            self.assertEqual(sha256(THEME / name), expected, name)

    def test_changed_text_and_json_are_utf8_without_replacement_characters(self):
        for path in (
            IMPORTER,
            REGISTRY,
            IMPORT_PAYLOAD,
            IMPORT_RELEASE_MANIFEST,
            ACF_RELATIONS,
            FUNCTIONS,
            NEW_SERVICE,
            SEO_BLOG,
            SEO_INDEXING,
            REGION_TEMPLATE,
            ACF_BLOG_SOURCE,
            ACF_BLOG_THEME,
            DRENAZH_BLOG_IMPORTER,
        ):
            read(path)

    def test_php_lint_when_runtime_is_available(self):
        php = shutil.which("php")
        if php is None:
            self.skipTest("PHP runtime is not installed")
        for path in (IMPORTER, REGISTRY, REGION_TEMPLATE, FUNCTIONS, NEW_SERVICE, SEO_BLOG, SEO_INDEXING, DRENAZH_BLOG_IMPORTER):
            completed = subprocess.run([php, "-l", str(path)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
