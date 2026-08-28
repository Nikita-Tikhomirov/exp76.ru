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


class ChildServiceTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = TEMPLATE.read_text(encoding="utf-8")

    def test_price_table_uses_service_neutral_labels(self) -> None:
        self.assertIn(">Стоимость<", self.source)
        self.assertIn(">Примечание<", self.source)
        self.assertNotIn("Цена\n            за метр", self.source)

    def test_exact_cases_section_is_hidden_when_no_case_is_selected(self) -> None:
        assignment = self.source.index(
            "$ns87_selected_projects = land76_newservice_selected_real_projects"
        )
        guard = self.source.index(
            "if (!empty($ns87_selected_projects))",
            assignment,
        )
        section = self.source.index(
            '<section class="services wrapper casesCustom">',
            guard,
        )
        self.assertLess(assignment, guard)
        self.assertLess(guard, section)

    def test_managed_children_render_parent_and_related_service_links(self) -> None:
        self.assertIn("land76wp_service_hub_for_post", self.source)
        self.assertIn("$ns87_parent_hub_url", self.source)
        self.assertIn("blogseo_related_services", self.source)
        self.assertIn("Другие услуги направления", self.source)
        self.assertRegex(
            self.source,
            re.compile(r"hero__breadcramps.*ns87_parent_hub_url", re.DOTALL),
        )

    def test_cta_avoids_an_unconditional_one_day_promise(self) -> None:
        self.assertNotIn("Получите расчет по услуге за 1 день", self.source)
        self.assertIn("Получите расчёт по вашему участку", self.source)


if __name__ == "__main__":
    unittest.main()
