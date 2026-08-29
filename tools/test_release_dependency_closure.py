"""Regression contracts for deploy-package runtime dependency closure."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "ftp_dump_minimal"

ENTRYPOINTS = (
    "wp-content/themes/land76wp/inc/service-v2.php",
    "wp-content/themes/land76wp/servicepost.php",
    "wp-content/themes/land76wp/page-service-hub-region.php",
)
BASE_DEPLOYMENT = {
    *ENTRYPOINTS,
    "wp-content/themes/land76wp/inc/newservicepost.php",
}
EXPECTED_RUNTIME_DEPENDENCIES = {
    "wp-content/themes/land76wp/css/service-v2.css",
    "wp-content/themes/land76wp/inc/service-v2-template.php",
}


def _write_source(root: Path, relative: str, source: str) -> None:
    path = root.joinpath(*PurePosixPath(relative).parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _closure_module(test_case: unittest.TestCase):
    try:
        from tools import release_dependency_closure
    except (ImportError, ModuleNotFoundError):
        test_case.fail(
            "tools.release_dependency_closure must guard production package membership"
        )
    return release_dependency_closure


class ReleaseDependencyClosureTests(unittest.TestCase):
    def test_php_dir_literal_dependency_is_resolved_from_the_referring_file(self) -> None:
        """Catches a same-directory PHP include escaping or bypassing package closure."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        dependency = "wp-content/themes/example/inc/dependency.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php require_once __DIR__ . '/dependency.php';\n",
            )
            _write_source(source_root, dependency, "<?php\n")

            try:
                missing = closure.find_missing_dependencies(
                    source_root,
                    {runtime},
                    {runtime},
                )
            except ValueError as error:
                self.fail(f"__DIR__ dependency must remain relative: {error}")

        self.assertEqual(
            {(dependency, runtime)},
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_static_concatenation_is_resolved_without_reading_commented_code(self) -> None:
        """Catches split literal dependencies being missed or retired comments blocking a build."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        dependency = "wp-content/themes/example/css/runtime.css"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php\n"
                "// get_template_directory() . '/css/retired.css';\n"
                "$css = get_template_directory() . '/css/' . 'runtime.css';\n",
            )
            _write_source(source_root, dependency, "/* runtime */\n")

            try:
                missing = closure.find_missing_dependencies(
                    source_root,
                    {runtime},
                    {runtime},
                )
            except ValueError as error:
                self.fail(f"comments must not create runtime dependencies: {error}")

        self.assertEqual(
            {(dependency, runtime)},
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_parent_dir_and_directory_separator_expression_is_resolved(self) -> None:
        """Catches a static dirname(__DIR__) dependency bypassing package closure."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        dependency = "wp-content/themes/example/bootstrap.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php require dirname(__DIR__) . DIRECTORY_SEPARATOR . 'bootstrap.php';\n",
            )
            _write_source(source_root, dependency, "<?php\n")

            missing = closure.find_missing_dependencies(
                source_root,
                {runtime},
                {runtime},
            )

        self.assertEqual(
            {(dependency, runtime)},
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_dynamic_runtime_path_expression_is_rejected(self) -> None:
        """Catches an unsupported dependency expression silently passing the release gate."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php require get_template_directory() . '/inc/' . $name . '.php';\n",
            )

            with self.assertRaisesRegex(ValueError, "unsupported runtime path expression"):
                closure.find_missing_dependencies(
                    source_root,
                    {runtime},
                    {runtime},
                )

    def test_grouped_theme_base_dependency_is_resolved(self) -> None:
        """Catches parentheses around a static theme root bypassing closure."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        dependency = "wp-content/themes/example/inc/dependency.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php require (get_template_directory()) . '/inc/dependency.php';\n",
            )
            _write_source(source_root, dependency, "<?php\n")

            missing = closure.find_missing_dependencies(
                source_root,
                {runtime},
                {runtime},
            )

        self.assertEqual(
            {(dependency, runtime)},
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_static_theme_root_alias_dependency_is_resolved(self) -> None:
        """Catches a locally aliased static theme root bypassing closure."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        dependency = "wp-content/themes/example/inc/dependency.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php\n"
                "$root = get_template_directory();\n"
                "require $root . '/inc/dependency.php';\n",
            )
            _write_source(source_root, dependency, "<?php\n")

            missing = closure.find_missing_dependencies(
                source_root,
                {runtime},
                {runtime},
            )

        self.assertEqual(
            {(dependency, runtime)},
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_case_fold_dependency_collision_is_rejected(self) -> None:
        """Catches distinct Linux paths collapsing into one supposedly complete dependency."""
        closure = _closure_module(self)
        runtime = "wp-content/themes/example/inc/runtime.php"
        first = "wp-content/themes/example/inc/A.php"
        second = "wp-content/themes/example/inc/a.php"
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            _write_source(
                source_root,
                runtime,
                "<?php\n"
                "require get_template_directory() . '/inc/A.php';\n"
                "require get_template_directory() . '/inc/a.php';\n",
            )
            _write_source(source_root, first, "<?php\n")
            _write_source(source_root, second, "<?php\n")

            with self.assertRaisesRegex(ValueError, "case-fold runtime dependency collision"):
                closure.find_missing_dependencies(
                    source_root,
                    {runtime},
                    {runtime},
                )

    def test_incomplete_service_v2_deployment_reports_every_missing_runtime_file(self) -> None:
        """Catches a release listing entrypoints but omitting their PHP or CSS runtime files."""
        closure = _closure_module(self)

        missing = closure.find_missing_dependencies(
            SOURCE_ROOT,
            BASE_DEPLOYMENT,
            ENTRYPOINTS,
        )

        self.assertEqual(
            EXPECTED_RUNTIME_DEPENDENCIES,
            {item.dependency for item in missing},
        )
        self.assertEqual(
            {
                (
                    "wp-content/themes/land76wp/css/service-v2.css",
                    "wp-content/themes/land76wp/inc/service-v2.php",
                ),
                (
                    "wp-content/themes/land76wp/inc/service-v2-template.php",
                    "wp-content/themes/land76wp/servicepost.php",
                ),
            },
            {(item.dependency, item.required_by) for item in missing},
        )

    def test_complete_service_v2_deployment_has_closed_runtime_dependencies(self) -> None:
        """Catches the guard rejecting a deployment after both required files are present."""
        closure = _closure_module(self)

        closure.assert_dependency_closure(
            SOURCE_ROOT,
            BASE_DEPLOYMENT | EXPECTED_RUNTIME_DEPENDENCIES,
            ENTRYPOINTS,
        )

    def test_release_gate_cli_fails_closed_for_an_incomplete_deploy_list(self) -> None:
        """Catches a package builder ignoring the dependency-closure failure exit code."""
        with tempfile.TemporaryDirectory() as temporary:
            deploy_list = Path(temporary) / "phase-A2-public-runtime-DEPLOY-FILES.txt"
            deploy_list.write_text(
                "\n".join(sorted(BASE_DEPLOYMENT)) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.check_release_package",
                    "--source-root",
                    str(SOURCE_ROOT),
                    "--public-runtime-deploy-list",
                    str(deploy_list),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        for dependency in EXPECTED_RUNTIME_DEPENDENCIES:
            self.assertIn(dependency, result.stderr)

    def test_release_gate_cli_accepts_the_complete_public_runtime_inventory(self) -> None:
        """Catches the versioned release gate not wiring the successful closure path."""
        with tempfile.TemporaryDirectory() as temporary:
            deploy_list = Path(temporary) / "phase-A2-public-runtime-DEPLOY-FILES.txt"
            deploy_list.write_text(
                "\n".join(
                    sorted(BASE_DEPLOYMENT | EXPECTED_RUNTIME_DEPENDENCIES)
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.check_release_package",
                    "--source-root",
                    str(SOURCE_ROOT),
                    "--public-runtime-deploy-list",
                    str(deploy_list),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("PASS release package dependency closure", result.stdout)

    def test_release_gate_script_accepts_direct_execution(self) -> None:
        """Catches the checked-in gate importing only when invoked as a module."""
        with tempfile.TemporaryDirectory() as temporary:
            deploy_list = Path(temporary) / "phase-A2-public-runtime-DEPLOY-FILES.txt"
            deploy_list.write_text(
                "\n".join(
                    sorted(BASE_DEPLOYMENT | EXPECTED_RUNTIME_DEPENDENCIES)
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "check_release_package.py"),
                    "--source-root",
                    str(SOURCE_ROOT),
                    "--public-runtime-deploy-list",
                    str(deploy_list),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("PASS release package dependency closure", result.stdout)


if __name__ == "__main__":
    unittest.main()
