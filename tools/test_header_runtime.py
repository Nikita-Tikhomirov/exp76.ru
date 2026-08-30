import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
HEADER_FILES = tuple(sorted(THEME.glob("header*.php")))


class SharedHeaderRuntimeTests(unittest.TestCase):
    def test_every_header_exposes_wordpress_body_classes(self) -> None:
        """Lets logged-in frontend controls account for the WordPress admin bar."""
        self.assertGreaterEqual(len(HEADER_FILES), 6)
        for template in HEADER_FILES:
            source = template.read_text(encoding="utf-8")
            self.assertRegex(
                source,
                r"<body\s+<\?php\s+body_class\(\);\s*\?>>",
                template.name,
            )

    def test_mobile_menu_clears_the_admin_bar_hit_area(self) -> None:
        """Prevents the admin profile link intercepting the visible burger button."""
        css = (THEME / "css" / "styles.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"body\.admin-bar\s+\.burger\s*\{[^}]*top:\s*49px\s*!important",
        )
        self.assertRegex(
            css,
            r"body\.admin-bar\s+\.menu\.active\s*\{[^}]*top:\s*32px",
        )
        self.assertRegex(
            css,
            r"body:has\(#wpadminbar\)\s+\.burger",
        )
        self.assertRegex(
            css,
            r"body:has\(#wpadminbar\)\s+\.menu\.active",
        )
        self.assertRegex(
            css,
            r"@media[^\{]*max-width:\s*782px[^\{]*\{[\s\S]*?"
            r"body\.admin-bar\s+\.burger\s*\{[^}]*top:\s*63px\s*!important",
        )
        self.assertRegex(
            css,
            r"@media[^\{]*max-width:\s*782px[^\{]*\{[\s\S]*?"
            r"body\.admin-bar\s+\.menu\.active\s*\{[^}]*top:\s*46px",
        )


if __name__ == "__main__":
    unittest.main()
