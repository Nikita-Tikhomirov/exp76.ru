import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.manifest import register_source


class SemanticManifestTest(unittest.TestCase):
    def test_register_source_records_relative_path_sha_and_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "raw.csv"
            source_file.write_text("query\nгазон\n", encoding="utf-8")
            manifest = root / "manifest.json"

            entry = register_source(source_file, "wordstat", "2026-08-20T12:00:00+03:00", manifest)

            expected_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
            self.assertEqual(entry.sha256, expected_sha)
            self.assertEqual(entry.source, "wordstat")
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved["files"][0]["sha256"], expected_sha)

    def test_register_source_rejects_secret_like_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "yandex-password.csv"
            path.write_text("query\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "secret-like filename"):
                register_source(path, "wordstat", "2026-08-20T12:00:00+03:00", root / "manifest.json")


if __name__ == "__main__":
    unittest.main()
