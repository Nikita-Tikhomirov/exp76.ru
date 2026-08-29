import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
HANDLER = ROOT / "ftp_dump_minimal" / "server.php"
FORM_CLIENT = THEME / "js" / "form-submit.js"
MAIN_JS = THEME / "js" / "main.js"
FUNCTIONS = THEME / "functions.php"
REGISTRY = THEME / "inc" / "service-hub-registry.php"
NEW_SERVICE = THEME / "inc" / "newservicepost.php"
SEO_BLOG = THEME / "inc" / "seoblogpost.php"
SERVICE_PAGE = THEME / "servicepost.php"
SINGLE = THEME / "single.php"
HOME_PAGE = THEME / "index.php"
LEGACY_CTA_TEMPLATES = (
    THEME / "casenew.php",
    *(THEME / f"category-{category_id}.php" for category_id in range(87, 93)),
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


class ContactEndpointContractTests(unittest.TestCase):
    def test_endpoint_returns_json_and_rejects_every_untrusted_boundary(self) -> None:
        """Catches accepting GET, CSRF, no consent, malformed phone or a filled honeypot."""
        source = read(HANDLER)

        self.assertIn("require_once __DIR__ . '/wp-load.php'", source)
        self.assertIn("application/json", source)
        self.assertIn("REQUEST_METHOD", source)
        self.assertIn("http_response_code(405)", source)
        self.assertIn("wp_verify_nonce", source)
        self.assertIn("land76_contact_form", source)
        self.assertIn("land76_nonce", source)
        self.assertIn("consent", source)
        self.assertIn("website", source)
        self.assertRegex(source, r"strlen\([^)]*phone[^)]*\)\s*<\s*10")
        self.assertRegex(source, r"strlen\([^)]*phone[^)]*\)\s*>\s*15")
        self.assertIn("wp_send_json_error", source)
        self.assertIn("wp_send_json_success", source)

    def test_endpoint_reports_mail_failure_instead_of_false_success(self) -> None:
        """Catches treating a rejected wp_mail call as an accepted lead."""
        source = read(HANDLER)

        self.assertIn("$mail_sent = wp_mail(", source)
        self.assertIn("if (!$mail_sent)", source)
        failure = source.index("if (!$mail_sent)")
        self.assertIn("wp_send_json_error", source[failure:])
        self.assertIn("500", source[failure:])

    def test_endpoint_rate_limits_a_salted_remote_addr_hash_only(self) -> None:
        """Catches trusting spoofable proxy headers or storing a raw client IP in throttle state."""
        source = read(HANDLER)
        client_hash = php_function_body(source, "land76_contact_client_hash")
        throttle = php_function_body(source, "land76_contact_enforce_throttle")

        self.assertIn("REMOTE_ADDR", client_hash)
        self.assertNotIn("HTTP_X_FORWARDED_FOR", source)
        self.assertNotIn("HTTP_CLIENT_IP", source)
        self.assertIn("FILTER_VALIDATE_IP", client_hash)
        self.assertIn("hash_hmac", client_hash)
        self.assertIn("wp_salt('nonce')", client_hash)
        self.assertNotIn("get_transient", client_hash)
        self.assertNotIn("set_transient", client_hash)

        self.assertIn("land76_contact_client_hash()", throttle)
        self.assertIn("get_transient", throttle)
        self.assertIn("set_transient", throttle)
        self.assertIn("rate_limited", throttle)
        self.assertIn("land76_contact_acquire_throttle_lock($rate_key", throttle)
        self.assertRegex(throttle, r"land76_contact_error\([^;]+,\s*429\s*\)")

    def test_endpoint_blocks_replay_before_mail_and_releases_reservation_on_failure(self) -> None:
        """Catches identical valid submissions racing through or a failed mail locking out retry."""
        source = read(HANDLER)
        throttle = php_function_body(source, "land76_contact_enforce_throttle")
        replay_lock = php_function_body(source, "land76_contact_acquire_replay_lock")
        throttle_lock = php_function_body(source, "land76_contact_acquire_throttle_lock")

        self.assertIn("submission_fingerprint", throttle)
        self.assertIn("replay_key", throttle)
        self.assertIn("duplicate_submission", throttle)
        self.assertIn("return $replay_key", throttle)
        self.assertIn("land76_contact_acquire_throttle_lock", replay_lock)
        self.assertIn("add_option", throttle_lock)
        self.assertIn("get_option", throttle_lock)
        self.assertIn("delete_option", throttle_lock)
        self.assertIn("register_shutdown_function", throttle_lock)
        self.assertIn("land76_contact_acquire_replay_lock($replay_key)", throttle)
        atomic_lock = throttle.index("land76_contact_acquire_replay_lock($replay_key)")
        replay_lookup = throttle.index("get_transient($replay_key)")
        self.assertLess(atomic_lock, replay_lookup)

        throttle_call = source.index("$replay_key = land76_contact_enforce_throttle(")
        mail_call = source.index("$mail_sent = wp_mail(")
        mail_failure = source.index("if (!$mail_sent)", mail_call)
        reservation_release = source.index("delete_transient($replay_key)", mail_failure)
        self.assertLess(throttle_call, mail_call)
        self.assertLess(mail_failure, reservation_release)


class FormClientContractTests(unittest.TestCase):
    def test_response_classifier_rejects_http_200_error_and_invalid_json(self) -> None:
        """Catches showing success for a 200 response whose JSON says failure or is malformed."""
        if not FORM_CLIENT.is_file():
            self.fail("missing testable form response client")
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not installed")

        program = """
const client = require(process.argv[1]);
const cases = [
  client.classifyResponse(200, '{"success":false,"data":{"code":"mail_failed"}}').ok,
  client.classifyResponse(200, 'OK').ok,
  client.classifyResponse(500, '{"success":true}').ok,
  client.classifyResponse(200, '{"success":true,"data":{"code":"accepted"}}').ok
];
process.stdout.write(JSON.stringify(cases));
"""
        completed = subprocess.run(
            [node, "-e", program, str(FORM_CLIENT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual([False, False, False, True], json.loads(completed.stdout))

    def test_form_client_creates_accessible_status_without_ajax_wrapper(self) -> None:
        """Catches a valid lead CTA resetting silently when legacy message markup is absent."""
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not installed")

        program = r"""
const client = require(process.argv[1]);
const classes = {};
const attrs = {};
const status = {
  hidden: true,
  textContent: '',
  className: '',
  classList: { toggle: (name, enabled) => { classes[name] = enabled; } },
  setAttribute: (name, value) => { attrs[name] = value; }
};
const form = {
  style: {},
  parentElement: { querySelector: () => null },
  ownerDocument: { createElement: () => status },
  insertAdjacentElement: (position, node) => { form.inserted = { position, node }; }
};
client.setResultState(form, true, 'Заявка отправлена.');
process.stdout.write(JSON.stringify({
  inserted: form.inserted.position,
  hidden: status.hidden,
  text: status.textContent,
  role: attrs.role,
  live: attrs['aria-live'],
  success: classes['land76-form-status--success'],
  error: classes['land76-form-status--error']
}));
"""
        completed = subprocess.run(
            [node, "-e", program, str(FORM_CLIENT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            {
                "inserted": "afterend",
                "hidden": False,
                "text": "Заявка отправлена.",
                "role": "status",
                "live": "polite",
                "success": True,
                "error": False,
            },
            json.loads(completed.stdout),
        )

    def test_theme_loads_nonce_client_and_disables_status_only_legacy_submitter(self) -> None:
        """Catches main.js attaching its old HTTP-status-only success handler."""
        functions = read(FUNCTIONS)
        main = read(MAIN_JS)

        self.assertIn("land76-form-submit", functions)
        self.assertIn("form-submit.js", functions)
        self.assertIn("wp_create_nonce('land76_contact_form')", functions)
        self.assertIn("land76FormConfig", functions)
        self.assertIn("window.land76FormClient||document.querySelectorAll", main)

    def test_rendered_forms_have_reusable_nonce_consent_and_honeypot_fields(self) -> None:
        """Catches a template posting without the server-side security fields."""
        functions = read(FUNCTIONS)
        security_fields = php_function_body(functions, "land76_render_form_security_fields")

        self.assertIn("wp_nonce_field", security_fields)
        self.assertIn("land76_nonce", security_fields)
        self.assertIn('name="website"', security_fields)
        self.assertIn('autocomplete="off"', security_fields)
        self.assertIn("land76_render_form_security_fields", read(NEW_SERVICE))
        self.assertIn("land76_render_form_security_fields", read(SERVICE_PAGE))
        self.assertIn(
            "form.querySelector('[name=\"consent\"], .formConsent__input')",
            read(FORM_CLIENT),
        )

    def test_every_legacy_cta_is_a_validated_contact_form(self) -> None:
        """Catches visible CTA forms falling back to a no-op GET submission."""
        for path in LEGACY_CTA_TEMPLATES:
            with self.subTest(template=path.name):
                source = read(path)
                cta_match = re.search(
                    r'<form\s+class="cta-form\s+form"[^>]*method="post"[^>]*action="/server\.php"[^>]*>'
                    r'(?P<body>.*?)</form>',
                    source,
                    re.DOTALL,
                )
                self.assertIsNotNone(cta_match, f"invalid CTA form in {path.name}")
                body = cta_match.group("body")
                self.assertRegex(body, r'<input[^>]+name="name"')
                self.assertRegex(body, r'<input[^>]+name="phone"')
                self.assertIn("land76_render_form_security_fields", body)
                self.assertRegex(body, r'name="consent"[^>]+value="1"[^>]+required')

    def test_managed_service_cta_has_a_safe_non_javascript_fallback(self) -> None:
        """Catches personal lead fields leaking into a page URL when JavaScript is blocked."""
        source = read(NEW_SERVICE)
        cta_match = re.search(
            r'<form\s+class="cta-form\s+form"[^>]*method="post"[^>]*'
            r'action="<\?php echo esc_url\(home_url\(\'/server\.php\'\)\); \?>"[^>]*>'
            r'(?P<body>.*?)</form>',
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(cta_match, "managed CTA has no explicit POST endpoint")
        body = cta_match.group("body")
        self.assertIn("land76_render_form_security_fields", body)
        self.assertRegex(body, r'name="consent"[^>]+value="1"[^>]+required')
        self.assertIn("home_url('/privacy/')", body)
        self.assertIn("home_url('/consent/')", body)

    def test_homepage_form_has_post_security_and_linked_consent_documents(self) -> None:
        """Catches the primary homepage form hiding the documents it asks users to accept."""
        source = read(HOME_PAGE)
        self.assertIn(
            '<form class="form" method="post" action="<?php echo esc_url(home_url(\'/server.php\')); ?>">',
            source,
        )
        self.assertIn("land76_render_form_security_fields('home-request-v3')", source)
        self.assertRegex(source, r'name="consent"[^>]+value="1"[^>]+required')
        self.assertIn("home_url('/privacy/')", source)
        self.assertIn("home_url('/consent/')", source)


class ManagedRuntimeContractTests(unittest.TestCase):
    def test_managed_contract_validates_owner_role_topic_canonical_and_runtime_shape(self) -> None:
        """Catches a partially owned post entering managed rendering or schema."""
        source = read(REGISTRY)
        body = php_function_body(source, "land76wp_managed_page_contract")

        for marker in (
            "_land76_import_owner",
            "_land76_page_key",
            "_land76_service_id",
            "_land76_topic_key",
            "_land76_canonical",
            "get_permalink",
            "CHILD",
            "ARTICLE",
            "post_type",
            "post_status",
            "servicepost.php",
            "has_category",
        ):
            self.assertIn(marker, body)

    def test_managed_pages_emit_one_shared_schema_graph(self) -> None:
        """Catches duplicate generic and registry JSON-LD scripts for a managed page."""
        registry = read(REGISTRY)
        functions = read(FUNCTIONS)
        output = php_function_body(functions, "land76_output_structured_data")

        self.assertNotIn("land76wp_service_hub_output_registry_schema", registry)
        self.assertIn("land76wp_service_hub_schema_context", output)
        self.assertIn("land76_schema_managed_main_node", output)
        self.assertIn("land76_schema_managed_breadcrumb_node", output)
        self.assertIn("land76_schema_managed_faq_node", output)
        self.assertEqual(1, output.count('type=\"application/ld+json\"'))
        self.assertEqual(1, output.count("'@graph'"))

        managed_faq = php_function_body(functions, "land76_schema_managed_faq_node")
        self.assertIn("land76_service_v2_current", managed_faq)
        self.assertIn("ns87_faq_items", managed_faq)
        self.assertIn("blogseo_faq_items", managed_faq)
        self.assertIn("land76_schema_faq_entities", managed_faq)

    def test_hub_schema_context_uses_validated_service_v2_h1_description_and_hero(self) -> None:
        """Catches a released hub graph falling back to stale post meta or thumbnail data."""
        context = php_function_body(
            read(REGISTRY),
            "land76wp_service_hub_schema_context",
        )

        self.assertIn("$role === 'hub'", context)
        self.assertIn("land76_service_v2_current", context)
        self.assertIn("$service_v2['hero']['title']", context)
        self.assertNotIn("$title = (string) $service_v2['seo']['title']", context)
        self.assertIn("$service_v2['seo']['description']", context)
        self.assertIn("$service_v2['hero']['image']['url']", context)
        self.assertIn("$service_v2['hero']['image']['alt']", context)
        self.assertNotIn("|| empty($service_v2['hero']['image']['url'])", context)
        self.assertIn("has_post_thumbnail($post_id)", context)

        release_data = context.index("land76_service_v2_current")
        legacy_description = context.index("get_post_meta($post_id, '_aioseo_description'", release_data)
        legacy_image = context.index("get_post_meta($post_id, '_land76_main_image_url'", release_data)
        self.assertLess(release_data, legacy_description)
        self.assertLess(release_data, legacy_image)

    def test_managed_routes_suppress_every_secondary_schema_emitter(self) -> None:
        """Catches a body template, rendered hub or AIOSEO adding a second JSON-LD graph."""
        emitters = {
            path.relative_to(THEME).as_posix()
            for path in THEME.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".php", ".html"}
            and 'application/ld+json' in read(path)
        }
        self.assertEqual(
            {
                "calc.php",
                "casenew.php",
                "functions.php",
                "inc/seoblogpost.php",
                "portfolio.php",
                "services.php",
            },
            emitters,
        )

        blog = read(SEO_BLOG)
        managed_flag = blog.index("$blogseo_is_managed_runtime")
        managed_schema_guard = blog.index("if (!$blogseo_is_managed_runtime)", managed_flag)
        inline_schema = blog.index('<script type="application/ld+json">', managed_schema_guard)
        self.assertLess(managed_flag, managed_schema_guard)
        self.assertLess(managed_schema_guard, inline_schema)

        registry = read(REGISTRY)
        disable = php_function_body(
            registry,
            "land76wp_service_hub_disable_aioseo_schema",
        )
        output_filter = php_function_body(
            registry,
            "land76wp_service_hub_filter_aioseo_schema_output",
        )
        self.assertIn("land76wp_service_hub_schema_context", disable)
        self.assertIn("get_queried_object_id", disable)
        self.assertIn("land76wp_service_hub_schema_context", output_filter)
        self.assertIn("return array()", output_filter)
        self.assertIn("add_filter('aioseo_schema_disable'", registry)
        self.assertIn("add_filter('aioseo_schema_output'", registry)

    def test_claimed_managed_child_fails_closed_in_page_and_single_routes(self) -> None:
        """Catches missing owner or corrupt managed metadata falling through to legacy."""
        claims = php_function_body(
            read(REGISTRY),
            "land76wp_claims_managed_service_hub_post",
        )
        self.assertIn("land76wp_has_managed_service_hub_owner", claims)
        self.assertIn("_land76_page_key", claims)
        self.assertIn("CHILD|ARTICLE|GEO", claims)

        for path in (SERVICE_PAGE, SINGLE):
            source = read(path)
            self.assertIn("land76wp_claims_managed_service_hub_post", source)
            self.assertIn("land76wp_managed_page_contract", source)
            self.assertIn("status_header(404)", source)
            owner_check = source.index("land76wp_claims_managed_service_hub_post")
            contract_check = source.index("land76wp_managed_page_contract", owner_check)
            not_found = source.index("status_header(404)", contract_check)
            legacy_render = source.index("newservicepost.php", not_found)
            self.assertLess(owner_check, contract_check)
            self.assertLess(contract_check, not_found)
            self.assertLess(not_found, legacy_render)

    def test_empty_managed_case_selection_never_inherits_category_cases(self) -> None:
        """Catches an explicitly empty managed case field expanding to every category case."""
        body = php_function_body(
            read(NEW_SERVICE),
            "land76_newservice_selected_real_projects",
        )
        self.assertIn("land76wp_has_managed_service_hub_owner", body)
        self.assertIn("return is_array($selected_projects)", body)
        managed_guard = body.index("land76wp_has_managed_service_hub_owner")
        managed_return = body.index("return is_array($selected_projects)", managed_guard)
        category_lookup = body.index("get_the_category", managed_return)
        self.assertLess(managed_guard, managed_return)
        self.assertLess(managed_return, category_lookup)


if __name__ == "__main__":
    unittest.main()
