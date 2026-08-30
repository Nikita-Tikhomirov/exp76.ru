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
FUNCTIONS = (
    ROOT
    / "ftp_dump_minimal"
    / "wp-content"
    / "themes"
    / "land76wp"
    / "functions.php"
)
SERVICEPOST_CSS = (
    ROOT
    / "ftp_dump_minimal"
    / "wp-content"
    / "themes"
    / "land76wp"
    / "css"
    / "servicepost.css"
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
    def test_managed_child_uses_the_hub_presentation_scope(self) -> None:
        """Catches managed children falling back to the unscoped legacy canvas."""
        source = read_template()
        functions = FUNCTIONS.read_text(encoding="utf-8")
        enqueue_helper = php_function_body(functions, "land76wp_enqueue_managed_child_styles")
        runtime_enqueue = php_function_body(functions, "style_theme")

        self.assertIn("add_action( 'wp_enqueue_scripts', 'style_theme' );", functions)
        self.assertIn("/css/servicepost.css", enqueue_helper)
        self.assertIn("/css/service-v2.css", enqueue_helper)
        self.assertIn("land76wp_claims_managed_service_hub_post", runtime_enqueue)
        self.assertIn("land76wp_managed_page_contract", runtime_enqueue)
        self.assertIn("['role'] === 'child'", runtime_enqueue)
        self.assertIn("land76wp_enqueue_managed_child_styles();", runtime_enqueue)
        self.assertNotIn('<link rel="stylesheet"', source[source.index("$ns87_breadcrumb_title") :])
        self.assertIn('class="managed-service-child"', source)
        self.assertNotIn('class="service-v2 managed-service-child"', source)
        self.assertIn('class="service-v2__section managed-service-child__section', source)
        self.assertIn(
            'class="service-v2 service-v2__section managed-service-child__section service-v2__cta wrapper"',
            source,
        )

    def test_managed_child_sections_alternate_full_width_plain_and_texture(self) -> None:
        """Catches one tiled background being painted behind the whole child page."""
        css = SERVICEPOST_CSS.read_text(encoding="utf-8")

        plain = re.search(
            r"\.managed-service-child\s*>\s*\.managed-service-child__section:nth-of-type\(even\)\s*\{(?P<body>[^}]+)\}",
            css,
        )
        textured = re.search(
            r"\.managed-service-child\s*>\s*\.managed-service-child__section:nth-of-type\(odd\)\s*\{(?P<body>[^}]+)\}",
            css,
        )
        self.assertIsNotNone(plain)
        self.assertIsNotNone(textured)
        assert plain is not None and textured is not None
        self.assertRegex(plain.group("body"), r"background:\s*#fff\s*;")
        self.assertIn("sb5.png", textured.group("body"))
        self.assertIn("background-size: cover", textured.group("body"))

    def test_managed_child_related_heading_and_cards_are_not_stuck_or_faded(self) -> None:
        """Catches a low-contrast heading touching the first row of related cards."""
        css = SERVICEPOST_CSS.read_text(encoding="utf-8")

        heading = re.search(
            r"\.managed-service-child\s+\.service-related-services\s*>\s*h2\s*\{(?P<body>[^}]+)\}",
            css,
        )
        cards = re.search(
            r"\.managed-service-child\s+\.service-related-services\s+\.service\s*\{(?P<body>[^}]+)\}",
            css,
        )
        self.assertIsNotNone(heading)
        self.assertIsNotNone(cards)
        assert heading is not None and cards is not None
        self.assertIn("color: #333", heading.group("body"))
        self.assertRegex(heading.group("body"), r"margin-bottom:\s*(?:2(?:\.\d+)?rem|3[2-9]px|[4-9]\dpx)")
        self.assertIn("overflow: hidden", cards.group("body"))

    def test_managed_child_content_price_and_cta_have_readable_surfaces(self) -> None:
        """Catches the narrow content card and low-contrast copy on one fixed image."""
        css = SERVICEPOST_CSS.read_text(encoding="utf-8")
        managed = css[css.index("/* Managed child-service pages") :]

        full_width = re.search(
            r"\.managed-service-child\s+\.problem-block,\s*"
            r"\.managed-service-child\s+\.solution-block,\s*"
            r"\.managed-service-child\s+\.seo-text\s*\{(?P<body>[^}]+)\}",
            managed,
        )
        price = re.search(
            r"\.managed-service-child\s+\.managed-service-child__price-surface\s*\{(?P<body>[^}]+)\}",
            managed,
        )
        cta = re.search(
            r"\.managed-service-child\s*>\s*\.managed-service-child__section\.service-v2__cta\s*\{(?P<body>[^}]+)\}",
            managed,
        )
        self.assertIsNotNone(full_width)
        self.assertIsNotNone(price)
        self.assertIsNotNone(cta)
        assert full_width is not None and price is not None and cta is not None
        self.assertIn("width: 100%", full_width.group("body"))
        self.assertIn("max-width: none", full_width.group("body"))
        self.assertIn("background: rgba(255, 255, 255, .96)", price.group("body"))
        self.assertIn('class="managed-service-child__price-surface"', read_template())
        self.assertIn("casebg.png", cta.group("body"))
        self.assertIn("background-attachment: scroll !important", cta.group("body"))

    def test_managed_child_cta_reuses_the_hub_form_layout(self) -> None:
        """Catches the managed child CTA reverting to the inline legacy form."""
        source = read_template()
        cta = section(source, "<!-- 10. CTA -->", "<?php else : ?>")

        self.assertIn('class="service-v2__cta-inner"', cta)
        self.assertIn('class="formWrapper service-v2__form-wrapper"', cta)
        self.assertIn('class="form service-v2__form"', cta)
        self.assertIn('class="service-v2__consent"', cta)
        self.assertNotIn('style="display: flex;', cta)

    def test_managed_hero_reserves_room_between_actions_and_breadcrumbs(self) -> None:
        """Catches the compact legacy hero making new CTA controls overlap."""
        source = read_template()

        self.assertRegex(source, r"\.hero\s*\{[^}]*min-height:\s*620px;")
        self.assertRegex(source, r"\.hero__buttons\s*\{[^}]*margin-top:\s*24px;")

    def test_managed_hero_omits_scroll_cue_that_overlaps_long_breadcrumbs(self) -> None:
        """Keeps the legacy scroll cue from covering managed child breadcrumbs."""
        hero = section(read_template(), "<!-- 1.", "<!-- 2.")

        self.assertNotIn('class="animation-wrap"', hero)
        self.assertNotIn("Листайте", hero)

    def test_inline_advantage_background_uses_absolute_theme_asset_url(self) -> None:
        """Catches inline CSS resolving ``../img`` against the page URL."""
        source = read_template()

        self.assertIn(
            "get_template_directory_uri() . '/img/adv.png'",
            source,
        )
        self.assertNotIn("background: url(../img/adv.png)", source)

    def test_managed_page_uses_one_normalized_seen_image_registry(self) -> None:
        """Catches repeated files and WordPress resized variants on one page."""
        source = read_template()
        identity = php_function_body(source, "land76_newservice_image_identity")
        reserve = php_function_body(source, "land76_newservice_reserve_image")

        self.assertIn("wp_parse_url", identity)
        self.assertIn("-\\d+x\\d+", identity)
        self.assertIn("-scaled", identity)
        self.assertIn("land76_newservice_image_identity", reserve)
        self.assertIn("$ns87_rendered_image_identities", source)

        bootstrap = section(source, "$ns87_post_context", "$ns87_hero_title")
        for render_flag, image_url in (
            ("$ns87_render_hero_image", "$ns87_hero_image_url"),
            ("$ns87_render_main_image", "$ns87_main_image_url"),
            ("$ns87_render_context_image", "$ns87_context_image_url"),
        ):
            self.assertIn(
                f"{render_flag} = {render_flag} && land76_newservice_reserve_image($ns87_rendered_image_identities, {image_url})",
                bootstrap,
            )

        for start, end in (
            ("service-related-services", "service-related-articles"),
            ("service-related-articles", "<!-- 6."),
        ):
            self.assertIn(
                ", $ns87_rendered_image_identities)",
                section(source, start, end),
            )

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
        self.assertIn("$ns87_rendered_problem_image_urls", problem)
        self.assertIn("problem-item__number", problem)
        self.assertIn("str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)", problem)
        self.assertNotIn("land76_newservice_reserve_image", problem)
        self.assertIn("in_array($ns87_problem_img, $ns87_rendered_problem_image_urls, true)", problem)
        self.assertRegex(
            problem,
            r"(?s)if \(\$land76_managed_service_hub_post\).*problem-item__number",
        )
        self.assertRegex(
            problem,
            r"elseif \(\$ns87_problem_img !== ''\)\s*:\s*\?>\s*<img",
        )
        self.assertRegex(
            source,
            r"\.problem-item img\s*,\s*\.problem-item__number\s*\{[^}]*margin-right:\s*0;[^}]*margin-bottom:\s*15px;",
        )

        seo_content = section(source, "<!-- 4.", "<!-- 5.")
        context_figure = section(
            seo_content,
            '<figure class="service-context-image">',
            "</figure>",
        )
        self.assertIn("$ns87_context_image_url", context_figure)
        self.assertIn("$ns87_context_image_alt", context_figure)
        self.assertIn("$ns87_render_context_image", seo_content)

    def test_managed_cases_never_use_context_fallback_but_legacy_keeps_its_route(self) -> None:
        """Catches generated managed media masquerading as proof or a legacy regression."""
        source = read_template()
        cases = section(
            source,
            "<!-- 5.",
            "service-related-services",
        )

        selector = php_function_body(
            source,
            "land76_newservice_unique_project_image",
        )
        self.assertIn("get_field('slider', $post_id)", selector)
        self.assertIn("get_attached_media('image', $post_id)", selector)
        self.assertIn("land76_newservice_reserve_image($seen, $url)", selector)
        self.assertIn(
            "land76_newservice_unique_project_image($post_id, $ns87_rendered_image_identities, 'medium')",
            cases,
        )

        self.assertIn(
            "land76_get_card_image_url($post_id, 'medium', !$land76_managed_service_hub_post)",
            cases,
        )
        self.assertIn("get_the_post_thumbnail_url", cases)
        self.assertNotIn("_land76_context_image", cases)
        self.assertIn("if ($land76_managed_service_hub_post)", cases)
        fallback = section(
            cases,
            "} else {",
            "$project_title",
        )
        self.assertEqual(1, fallback.count("land76_newservice_context_image"))
        managed_branch = section(
            cases,
            "if ($land76_managed_service_hub_post)",
            "} else {",
        )
        self.assertNotIn("land76_newservice_context_image", managed_branch)
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
        self.assertIn("foreach (array('services', 'articles') as $section_name)", selector)
        self.assertIn("$item['page_key']", selector)
        self.assertLess(
            selector.index("foreach (array('services', 'articles') as $section_name)"),
            selector.index("foreach (array('card', 'main') as $role)"),
        )
        self.assertIn("'_land76_' . $role . '_image_url'", selector)
        self.assertIn("'_land76_' . $role . '_image_alt'", selector)
        self.assertIn("land76wp_service_hub_for_post", selector)
        self.assertIn("land76_service_v2_load", selector)
        self.assertIn("$service_v2['hero']['image']['url']", selector)
        self.assertIn("$service_v2['hero']['image']['alt']", selector)
        self.assertIn("foreach (array('scope', 'services', 'articles') as $hub_section_name)", selector)
        self.assertIn("$hub_item['image']['url']", selector)
        self.assertIn("$hub_item['image']['alt']", selector)
        self.assertLess(
            selector.index("foreach (array('scope', 'services', 'articles') as $hub_section_name)"),
            selector.index("foreach (array('services', 'articles') as $section_name)"),
        )
        self.assertIn("$candidates", selector)
        self.assertIn("foreach ($candidates as $candidate)", selector)
        self.assertIn(
            "land76_newservice_reserve_image($seen, $candidate['url'])",
            selector,
        )

        related = section(source, "service-related-services", "service-related-articles")
        self.assertIn(
            "land76_newservice_related_card_image($ns87_related_service_id, $ns87_rendered_image_identities)",
            related,
        )
        self.assertRegex(related, r"if \(\$ns87_related_service_card\['url'\] !== ''")

        related_articles = section(source, "service-related-articles", "<!-- 6.")
        self.assertIn(
            "land76_newservice_related_card_image($ns87_related_article->ID, $ns87_rendered_image_identities)",
            related_articles,
        )

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
