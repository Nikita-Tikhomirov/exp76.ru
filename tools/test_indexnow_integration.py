import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
MODULE = THEME / "inc" / "indexnow.php"
FUNCTIONS = THEME / "functions.php"


class IndexNowIntegrationTest(unittest.TestCase):
    def test_public_key_file_matches_module_key(self):
        module = MODULE.read_text(encoding="utf-8")
        match = re.search(r"LAND76_INDEXNOW_KEY',\s*'([a-f0-9]{32})'", module)
        self.assertIsNotNone(match)

        key_file = ROOT / f"{match.group(1)}.txt"
        self.assertTrue(key_file.exists())
        self.assertEqual(match.group(1), key_file.read_text(encoding="ascii").strip())

    def test_module_is_loaded_and_hooks_public_updates(self):
        functions = FUNCTIONS.read_text(encoding="utf-8")
        module = MODULE.read_text(encoding="utf-8")

        self.assertIn("/inc/indexnow.php", functions)
        self.assertIn("transition_post_status", module)
        self.assertIn("edited_category", module)
        self.assertIn("https://yandex.com/indexnow", module)
        self.assertIn("'blocking' => false", module)


if __name__ == "__main__":
    unittest.main()
