import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.manifest import register_source, validate_manifest


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

    def test_register_source_rejects_a_manifest_alias_of_the_source_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "source-manifest.json"
            original_contents = "query\nгазон\n"
            source_file.write_text(original_contents, encoding="utf-8")
            alias_path = root / "raw" / ".." / "source-manifest.json"

            with self.assertRaisesRegex(ValueError, "source file and manifest path must differ"):
                register_source(source_file, "wordstat", "2026-08-20T12:00:00+03:00", alias_path)

            self.assertEqual(source_file.read_text(encoding="utf-8"), original_contents)

    def test_validate_manifest_rejects_invalid_required_entry_fields(self):
        valid_entry = {
            "path": "serp/result.jsonl",
            "source": "serp",
            "collected_at": "2026-08-20T12:00:00+03:00",
            "sha256": "a" * 64,
            "byte_count": 123,
        }
        invalid_entries = []
        for field in valid_entry:
            entry = valid_entry.copy()
            del entry[field]
            invalid_entries.append((f"missing_{field}", entry))
        invalid_entries.extend(
            (
                ("empty_path", {**valid_entry, "path": " "}),
                ("non_string_source", {**valid_entry, "source": 1}),
                ("naive_collected_at", {**valid_entry, "collected_at": "2026-08-20T12:00:00"}),
                ("short_sha256", {**valid_entry, "sha256": "a" * 63}),
                ("non_hex_sha256", {**valid_entry, "sha256": "g" * 64}),
                ("boolean_byte_count", {**valid_entry, "byte_count": True}),
                ("negative_byte_count", {**valid_entry, "byte_count": -1}),
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "source-manifest.json"
            for label, entry in invalid_entries:
                with self.subTest(label=label):
                    manifest.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "manifest entry"):
                        validate_manifest(manifest)

    def test_validate_manifest_rejects_duplicate_paths(self):
        entry = {
            "path": "serp/result.jsonl",
            "source": "serp",
            "collected_at": "2026-08-20T12:00:00+03:00",
            "sha256": "a" * 64,
            "byte_count": 123,
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "source-manifest.json"
            manifest.write_text(json.dumps({"files": [entry, entry]}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate manifest entry path"):
                validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
