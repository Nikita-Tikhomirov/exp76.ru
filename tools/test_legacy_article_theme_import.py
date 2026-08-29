from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
SOURCE_PAYLOAD = ROOT / "seo-content" / "legacy-articles" / "import" / "legacy-services-blog-import.json"
THEME_PAYLOAD = THEME / "import" / "legacy-services-blog-import.json"
WRAPPER = THEME / "inc" / "import-legacy-services-blog.php"
BASE_IMPORTER = THEME / "inc" / "import-drenazh-blog.php"
FUNCTIONS = THEME / "functions.php"


def read(path: Path) -> str:
    value = path.read_text(encoding="utf-8")
    if "\ufffd" in value:
        raise AssertionError(f"replacement character in {path}")
    return value


class LegacyArticleThemeImportTests(unittest.TestCase):
    def test_theme_payload_is_exact_local_copy(self) -> None:
        self.assertTrue(SOURCE_PAYLOAD.is_file())
        self.assertTrue(THEME_PAYLOAD.is_file())
        self.assertEqual(THEME_PAYLOAD.read_bytes(), SOURCE_PAYLOAD.read_bytes())
        payload = json.loads(read(THEME_PAYLOAD))
        self.assertEqual(payload["type"], "legacy_services_blog_posts")
        self.assertEqual(payload["category_ids"], [72])
        self.assertEqual(len(payload["posts"]), 11)
        self.assertTrue(all(post["categories"] == [72] for post in payload["posts"]))

    def test_wrapper_delegates_to_existing_importer_with_own_payload_path(self) -> None:
        source = read(WRAPPER)
        self.assertIn("import/legacy-services-blog-import.json", source)
        self.assertIn("function land76wp_legacy_services_blog_import_default_json_path()", source)
        self.assertIn("function land76wp_run_legacy_services_blog_import($json_path = '')", source)
        self.assertIn("function_exists('land76wp_run_drenazh_blog_import')", source)
        self.assertIn("return land76wp_run_drenazh_blog_import($json_path);", source)
        self.assertIn("Base SEO blog importer is unavailable.", source)

    def test_wrapper_has_no_automatic_execution_or_hooks(self) -> None:
        source = read(WRAPPER)
        self.assertEqual(source.count("land76wp_run_legacy_services_blog_import("), 1)
        self.assertEqual(source.count("land76wp_run_drenazh_blog_import("), 1)
        for forbidden in (
            "add_action(",
            "add_filter(",
            "register_activation_hook(",
            "admin_init",
            "wp_loaded",
            "after_setup_theme",
            "$_GET",
            "$_POST",
        ):
            self.assertNotIn(forbidden, source)

    def test_functions_loads_wrapper_after_base_importer_without_running_it(self) -> None:
        source = read(FUNCTIONS)
        self.assertEqual(source.count("import-legacy-services-blog.php"), 1)
        self.assertIn("$land76_legacy_services_blog_import_file", source)
        self.assertRegex(
            source,
            re.compile(
                r"\$land76_legacy_services_blog_import_file\s*=.*?"
                r"if\s*\(file_exists\(\$land76_legacy_services_blog_import_file\)\)\s*\{\s*"
                r"require_once\s+\$land76_legacy_services_blog_import_file;\s*\}",
                re.DOTALL,
            ),
        )
        self.assertLess(source.index("import-drenazh-blog.php"), source.index("import-legacy-services-blog.php"))
        self.assertNotIn("land76wp_run_legacy_services_blog_import(", source)

    def test_wrapper_does_not_reimplement_base_importer(self) -> None:
        source = read(WRAPPER)
        base = read(BASE_IMPORTER)
        self.assertIn("function land76wp_run_drenazh_blog_import", base)
        self.assertNotIn("function land76wp_run_drenazh_blog_import", source)
        self.assertNotIn("wp_insert_post", source)
        self.assertNotIn("wp_update_post", source)

    @unittest.skipUnless(shutil.which("php"), "php is unavailable")
    def test_wrapper_php_syntax(self) -> None:
        result = subprocess.run(
            ["php", "-l", str(WRAPPER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
