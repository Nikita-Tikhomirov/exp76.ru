import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT
    / "ftp_dump_minimal"
    / "wp-content"
    / "themes"
    / "land76wp"
    / "inc"
    / "newservicepost.php"
)


def read_template() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def php_function_body(source: str, function_name: str) -> str:
    match = re.search(
        rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{",
        source,
    )
    if match is None:
        raise AssertionError(f"missing PHP function {function_name}")

    depth = 1
    cursor = match.end()
    while cursor < len(source) and depth:
        if source[cursor] == "{":
            depth += 1
        elif source[cursor] == "}":
            depth -= 1
        cursor += 1
    if depth:
        raise AssertionError(f"unbalanced PHP function {function_name}")
    return source[match.end() : cursor - 1]


def section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    return source[start_index : source.index(end, start_index)]


class ManagedPresentationRuntimeTests(unittest.TestCase):
    def test_managed_hero_prefers_role_meta_and_falls_back_to_real_main_pair(self) -> None:
        """Catches imported hero metadata being stored but ignored by the hero."""
        source = read_template()
        selector = php_function_body(
            source,
            "land76_newservice_managed_presentation_image",
        )

        self.assertIn("land76-service-hubs", selector)
        self.assertIn("array('main', 'hero', 'context')", selector)
        self.assertIn("'_land76_' . $role . '_image_url'", selector)
        self.assertIn("'_land76_' . $role . '_image_alt'", selector)
        self.assertIn("$role !== 'main'", selector)
        self.assertIn("'_land76_main_image_url'", selector)
        self.assertIn("'_land76_main_image_alt'", selector)
        self.assertIn("$url === '' || $alt === ''", selector)

        bootstrap = section(source, "$ns87_post_context", "$ns87_hero_title")
        self.assertIn(
            "land76_newservice_managed_presentation_image($ns87_post_context, 'hero')",
            bootstrap,
        )
        hero = section(source, "<!-- 1.", "<!-- 2.")
        self.assertIn("$ns87_hero_image_url", hero)
        self.assertNotIn("$ns87_main_image_url", hero)

    def test_context_meta_renders_once_with_its_alt_and_main_fallback_is_not_duplicated(self) -> None:
        """Catches context media being reduced to repeated main-image thumbnails."""
        source = read_template()
        bootstrap = section(source, "$ns87_post_context", "$ns87_hero_title")
        self.assertIn(
            "land76_newservice_managed_presentation_image($ns87_post_context, 'context')",
            bootstrap,
        )

        problem = section(source, "<!-- 2.", "<!-- 3.")
        self.assertIn("$ns87_problem_reserved_image_urls", problem)
        self.assertIn("$ns87_rendered_problem_image_urls", problem)
        self.assertIn("in_array($ns87_problem_img, $ns87_problem_reserved_image_urls, true)", problem)
        self.assertIn("in_array($ns87_problem_img, $ns87_rendered_problem_image_urls, true)", problem)
        self.assertRegex(problem, r"if \(\$ns87_problem_img !== ''\)\s*:\s*\?>\s*<img")

        seo_content = section(source, "<!-- 4.", "<!-- 5.")
        context_figure = section(
            seo_content,
            '<figure class="service-context-image">',
            "</figure>",
        )
        self.assertIn("$ns87_context_image_url", context_figure)
        self.assertIn("$ns87_context_image_alt", context_figure)
        self.assertIn("$ns87_context_image_url !== $ns87_main_image_url", seo_content)

    def test_managed_cases_never_use_context_fallback_but_legacy_keeps_its_route(self) -> None:
        """Catches generated managed media masquerading as proof or a legacy regression."""
        cases = section(
            read_template(),
            "<!-- 5.",
            "service-related-services",
        )

        self.assertIn(
            "land76_get_card_image_url($post_id, 'medium', !$land76_managed_service_hub_post)",
            cases,
        )
        self.assertIn("get_the_post_thumbnail_url", cases)
        self.assertNotIn("_land76_context_image", cases)
        self.assertIn(
            "if (!$project_image && !$land76_managed_service_hub_post)",
            cases,
        )
        fallback = section(
            cases,
            "if (!$project_image && !$land76_managed_service_hub_post)",
            "$project_title",
        )
        self.assertEqual(1, fallback.count("land76_newservice_context_image"))
        self.assertRegex(cases, r"if \(\$project_image\)\s*:\s*\?>")

    def test_real_main_image_keeps_its_own_url_and_alt(self) -> None:
        """Catches replacing the evidence-backed main image with generated media."""
        seo_content = section(
            read_template(),
            "<!-- 4.",
            "<!-- 5.",
        )
        main_figure = section(
            seo_content,
            '<figure class="service-main-image">',
            "</figure>",
        )

        self.assertIn("$ns87_main_image_url", main_figure)
        self.assertIn("$ns87_main_image_alt", main_figure)
        self.assertNotIn("$ns87_hero_image", main_figure)
        self.assertNotIn("$ns87_context_image", main_figure)

    def test_related_hub_card_uses_service_v2_hero_when_post_meta_is_absent(self) -> None:
        """Catches every child-to-hub relation degrading to a text-only card."""
        source = read_template()
        selector = php_function_body(
            source,
            "land76_newservice_related_card_image",
        )

        self.assertIn("array('card', 'main')", selector)
        self.assertIn("'_land76_' . $role . '_image_url'", selector)
        self.assertIn("'_land76_' . $role . '_image_alt'", selector)
        self.assertIn("land76wp_service_hub_for_post", selector)
        self.assertIn("land76_service_v2_load", selector)
        self.assertIn("$service_v2['hero']['image']['url']", selector)
        self.assertIn("$service_v2['hero']['image']['alt']", selector)

        related = section(source, "service-related-services", "service-related-articles")
        self.assertIn(
            "land76_newservice_related_card_image($ns87_related_service_id)",
            related,
        )
        self.assertRegex(related, r"if \(\$ns87_related_service_card\['url'\] !== ''")

    def test_managed_pricing_renders_factors_while_legacy_keeps_its_table(self) -> None:
        """Catches managed factor explanations being shown as fake price rows."""
        pricing = section(read_template(), "<!-- 6.", "<!-- 8.")
        managed = section(
            pricing,
            "<?php if ($land76_managed_service_hub_post) : ?>",
            "<?php else : ?>",
        )
        legacy = section(pricing, "<?php else : ?>", "<?php endif; ?>")

        self.assertIn('class="service-price-factors"', managed)
        self.assertIn("$ns87_price_row['service']", managed)
        self.assertIn("$ns87_price_row['term']", managed)
        self.assertNotIn("$ns87_price_row['price']", managed)
        self.assertNotIn("<table", managed)
        self.assertNotIn("по расчету", managed.casefold())
        self.assertIn("<table", legacy)
        self.assertIn("$ns87_price_row['price']", legacy)


if __name__ == "__main__":
    unittest.main()
