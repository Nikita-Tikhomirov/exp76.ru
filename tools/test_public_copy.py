import json
import re
import unittest
from pathlib import Path

from tools.service_v2 import render_service


ROOT = Path(__file__).resolve().parents[1]
HUB_SOURCE_DIR = ROOT / "seo-content" / "service-hubs" / "hubs"

FORBIDDEN_PUBLIC_LANGUAGE = re.compile(
    r"(?:\bхаб\w*\b|URL-владел\w*|утвержд[её]нн\w*\s+архитектур\w*|"
    r"действующ\w*\s+страниц\w*|стар\w*\s+страниц\w*|в\s+этом\s+контенте|"
    r"\bинтент\w*\b|\bкластер\w*\b|\bCMS\b|\bWP\s*\d*\b|"
    r"подтвержд[её]нн\w*\s+кейс\w*|опубликованн\w+\s+текст\w*|"
    r"не\s+подтвержда\w*|неподтвержд[её]нн\w*\s+модел\w*|"
    r"перед\s+публикаци\w*|нет\s+подтвержд[её]нн\w*)",
    re.IGNORECASE,
)


def _public_source_strings(value: object, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        if path.endswith((".url", ".canonical", ".source_ref")):
            return []
        if path in {"$.service_id", "$.page_key", "$.release_id"}:
            return []
        return [(path, value)]
    if isinstance(value, dict):
        rows: list[tuple[str, str]] = []
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if child_path.startswith("$.fact_evidence"):
                continue
            rows.extend(_public_source_strings(child, child_path))
        return rows
    if isinstance(value, list):
        rows = []
        for index, child in enumerate(value):
            rows.extend(_public_source_strings(child, f"{path}[{index}]"))
        return rows
    return []


class ManagedPublicCopyTests(unittest.TestCase):
    def test_hub_sources_and_rendered_html_do_not_expose_editorial_language(self) -> None:
        paths = sorted(HUB_SOURCE_DIR.glob("S*.json"))
        self.assertEqual(15, len(paths))

        for path in paths:
            service = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(service_id=service["service_id"], surface="source"):
                for field_path, text in _public_source_strings(service):
                    self.assertIsNone(
                        FORBIDDEN_PUBLIC_LANGUAGE.search(text),
                        f"{field_path}: {text}",
                    )

            rendered = render_service(service)
            visible_text = re.sub(r"<[^>]+>", " ", rendered)
            visible_text = re.sub(r"\s+", " ", visible_text)
            with self.subTest(service_id=service["service_id"], surface="html"):
                self.assertIsNone(
                    FORBIDDEN_PUBLIC_LANGUAGE.search(visible_text),
                    visible_text,
                )


if __name__ == "__main__":
    unittest.main()
