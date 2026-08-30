from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROBOTS = ROOT / "ftp_dump_minimal" / "robots.txt"


class RobotsPolicyTests(unittest.TestCase):
    def lines(self) -> list[str]:
        return [
            line.split("#", 1)[0].strip()
            for line in ROBOTS.read_text(encoding="utf-8-sig").splitlines()
            if line.split("#", 1)[0].strip()
        ]

    def test_wordpress_frontend_assets_remain_crawlable(self) -> None:
        lines = self.lines()

        self.assertNotIn("Disallow: /wp-", lines)
        self.assertIn("Disallow: /wp-admin/", lines)
        self.assertIn("Allow: /wp-admin/admin-ajax.php", lines)
        self.assertIn("Allow: /wp-content/themes/land76wp/", lines)
        self.assertIn("Allow: /wp-content/uploads/", lines)

    def test_legacy_parsers_keep_the_rules_in_the_user_agent_group(self) -> None:
        raw_lines = ROBOTS.read_text(encoding="utf-8-sig").splitlines()

        self.assertEqual("User-agent: *", raw_lines[0])
        self.assertNotEqual("", raw_lines[1].strip())

    def test_only_the_real_xml_sitemap_is_advertised(self) -> None:
        sitemap_lines = [line for line in self.lines() if line.startswith("Sitemap:")]

        self.assertEqual(["Sitemap: https://exp76.ru/sitemap.xml"], sitemap_lines)


if __name__ == "__main__":
    unittest.main()
