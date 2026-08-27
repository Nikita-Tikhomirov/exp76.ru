import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.service_v2 import ContractError, count_words, render_service, validate_service


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp"
DATA_DIR = THEME / "content" / "service-v2"

EXPECTED_SERVICES = {
    "S1": (673, "landshaftnoe-proektirovanie"),
    "S2": (6868, "gazon-posevnojj-i-gazon-rulonnyjj"),
    "S3": (6871, "posadka-derevev-i-kustarnikov"),
    "S4": (9357, "ukhod-za-sadom"),
    "S5": (667, "planirovka-territorii"),
    "S6": (676, "podpornye-stenki"),
    "S7": (6918, "ulichnoe-osveshhenie-uchastka"),
    "S8": (9282, "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch"),
}

EXPECTED_CASES = {
    "S1": [10345, 10136, 9445],
    "S2": [10096, 9554],
    "S3": [10096],
    "S4": [],
    "S5": [],
    "S6": [],
    "S7": [],
    "S8": [],
}


class ServiceV2Test(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "tools.service_v2", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def load_services(self) -> list[dict[str, object]]:
        self.assertTrue(DATA_DIR.is_dir(), "production service-v2 data directory is missing")
        files = sorted(DATA_DIR.glob("*.json"))
        self.assertEqual(len(files), 8, "exactly eight approved service payloads must ship")
        return [json.loads(path.read_text(encoding="utf-8")) for path in files]

    def test_real_payloads_pass_the_production_contract(self) -> None:
        """Catches incomplete copy, placeholders, unsafe owners and missing SEO fields."""
        result = self.run_cli("validate", str(DATA_DIR))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["services"], 8)
        self.assertEqual(summary["errors"], 0)
        self.assertGreaterEqual(summary["words"], 7000)

    def test_payloads_keep_the_eight_existing_url_owners(self) -> None:
        """Catches accidental URL, ID or canonical changes that would lose page history."""
        services = self.load_services()
        actual = {
            str(service["service_id"]): (int(service["page_id"]), str(service["slug"]))
            for service in services
        }

        self.assertEqual(actual, EXPECTED_SERVICES)
        for service in services:
            slug = str(service["slug"])
            self.assertEqual(service["canonical"], f"https://exp76.ru/services/{slug}/")
            self.assertEqual(service["parent_id"], 921)
            self.assertEqual(service["wp_template"], "servicepost.php")

    def test_only_verified_cases_are_presented_as_completed_work(self) -> None:
        """Catches invented portfolio proof on services that have no confirmed case."""
        services = self.load_services()
        actual = {
            str(service["service_id"]): [int(case["page_id"]) for case in service["proof"]["cases"]]
            for service in services
        }

        self.assertEqual(actual, EXPECTED_CASES)

    def test_seo_titles_descriptions_and_h1_are_unique(self) -> None:
        """Catches duplicate snippets or generic H1 values across the eight owners."""
        services = self.load_services()
        titles = [str(service["seo"]["title"]) for service in services]
        descriptions = [str(service["seo"]["description"]) for service in services]
        h1_values = [str(service["hero"]["title"]) for service in services]

        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(len(descriptions), len(set(descriptions)))
        self.assertEqual(len(h1_values), len(set(h1_values)))
        for title in titles:
            self.assertGreaterEqual(len(title), 45)
            self.assertLessEqual(len(title), 85)
        for description in descriptions:
            self.assertGreaterEqual(len(description), 110)
            self.assertLessEqual(len(description), 180)
        for service in services:
            self.assertGreaterEqual(count_words(service), 900, str(service["service_id"]))

    def test_contract_rejects_hotlinked_production_images(self) -> None:
        """Catches third-party image dependencies and accidental stock-photo hotlinking."""
        service = copy.deepcopy(self.load_services()[0])
        service["hero"]["image"]["url"] = "https://example.com/unverified-image.webp"

        with self.assertRaises(ContractError):
            validate_service(service)

    def test_build_outputs_complete_accessible_html_for_every_service(self) -> None:
        """Catches empty production sections, broken form fallback and image accessibility regressions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli("build", str(DATA_DIR), temp_dir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            rendered = sorted(Path(temp_dir).glob("*.html"))
            self.assertEqual(len(rendered), 8)
            for path in rendered:
                html = path.read_text(encoding="utf-8")
                self.assertEqual(html.count("<h1"), 1, path.name)
                self.assertGreaterEqual(html.count("<h2"), 7, path.name)
                self.assertGreaterEqual(html.count('class="service-v2__faq-item"'), 5, path.name)
                self.assertIn('<form class="form service-v2__form" method="post"', html)
                self.assertIn('action="/server.php"', html)
                self.assertIn('name="form_version" value="service-v2"', html)
                self.assertIn('name="source"', html)
                self.assertIn('name="consent" value="1"', html)
                self.assertNotIn('alt=""', html)
                self.assertNotIn('href="#"', html)
                self.assertNotIn("privacy.html", html)
                self.assertNotIn("consent.html", html)
                self.assertNotIn("Lorem", html)
                self.assertNotIn("TODO", html)
                self.assertNotIn("TBD", html)
                self.assertNotIn("{{", html)
                for target in set(re.findall(r'href="(#service-v2-[^"]+)"', html)):
                    self.assertIn(f'id="{target[1:]}"', html, f"broken anchor {target} in {path.name}")

    def test_committed_fragments_match_validated_payloads(self) -> None:
        """Catches stale production HTML after a content or renderer change."""
        rendered_dir = DATA_DIR / "rendered"
        self.assertEqual(len(list(rendered_dir.glob("*.html"))), 8)

        for json_path in sorted(DATA_DIR.glob("*.json")):
            service = json.loads(json_path.read_text(encoding="utf-8"))
            validate_service(service)
            actual = (rendered_dir / f"{service['slug']}.html").read_text(encoding="utf-8")
            self.assertEqual(actual, render_service(service), json_path.name)

    def test_theme_routes_only_approved_pages_through_service_v2(self) -> None:
        """Catches a broad template switch that would alter unrelated legacy pages."""
        helper = THEME / "inc" / "service-v2.php"
        template = THEME / "inc" / "service-v2-template.php"
        servicepost = THEME / "servicepost.php"

        self.assertTrue(helper.is_file())
        self.assertTrue(template.is_file())
        helper_source = helper.read_text(encoding="utf-8")
        template_source = template.read_text(encoding="utf-8")
        router_source = servicepost.read_text(encoding="utf-8")
        self.assertIn("land76_service_v2_current", router_source)
        self.assertIn("service-v2-template.php", router_source)
        self.assertIn("page_id", helper_source)
        self.assertIn("slug", helper_source)
        self.assertNotIn("wp_delete_post", helper_source + template_source)
        self.assertNotIn("wp_update_post", helper_source + template_source)

    def test_form_legal_links_have_complete_theme_routes(self) -> None:
        """Catches production forms linking to the two legacy 404 responses."""
        helper = THEME / "inc" / "legal-pages.php"
        template = THEME / "inc" / "legal-page-template.php"

        self.assertTrue(helper.is_file())
        self.assertTrue(template.is_file())
        helper_source = helper.read_text(encoding="utf-8")
        template_source = template.read_text(encoding="utf-8")
        self.assertIn("'privacy'", helper_source)
        self.assertIn("'consent'", helper_source)
        self.assertIn("Политика конфиденциальности", template_source)
        self.assertIn("Согласие на обработку персональных данных", template_source)
        self.assertIn("info@exp76.ru", template_source)
        self.assertGreaterEqual(count_words(template_source), 500)
        for placeholder in ("Lorem", "TODO", "TBD", "{{", "здесь будет"):
            self.assertNotIn(placeholder, template_source)

    def test_legacy_legal_links_redirect_to_canonical_documents(self) -> None:
        """Catches old relative privacy.html links resolving to nested 404 pages."""
        helper_source = (THEME / "inc" / "legal-pages.php").read_text(encoding="utf-8")

        self.assertIn("privacy.html", helper_source)
        self.assertIn("consent.html", helper_source)
        self.assertIn("wp_safe_redirect", helper_source)
        self.assertIn("301", helper_source)

    def test_lead_handler_validates_requests_and_mail_delivery(self) -> None:
        """Catches false success responses and unrecorded consent/source data."""
        handler_source = (ROOT / "ftp_dump_minimal" / "server.php").read_text(encoding="utf-8")

        self.assertIn("REQUEST_METHOD", handler_source)
        self.assertIn("http_response_code(405)", handler_source)
        self.assertIn("http_response_code(422)", handler_source)
        self.assertIn("http_response_code(500)", handler_source)
        self.assertIn("$_POST['consent'] ??", handler_source)
        self.assertIn("land76_clean_post_value('source'", handler_source)
        self.assertIn("$mail_sent = @mail(", handler_source)
        self.assertIn("if (!$mail_sent)", handler_source)


if __name__ == "__main__":
    unittest.main()
