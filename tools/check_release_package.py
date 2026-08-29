"""Versioned release gate for deploy-package runtime membership."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.release_dependency_closure import (
    DependencyClosureError,
    assert_dependency_closure,
    load_deploy_list,
)


PUBLIC_RUNTIME_ENTRYPOINTS = (
    "wp-content/themes/land76wp/inc/service-v2.php",
    "wp-content/themes/land76wp/servicepost.php",
    "wp-content/themes/land76wp/page-service-hub-region.php",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fail closed when a production package omits runtime dependencies"
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--public-runtime-deploy-list", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        deployed = load_deploy_list(args.public_runtime_deploy_list)
        assert_dependency_closure(
            args.source_root,
            deployed,
            PUBLIC_RUNTIME_ENTRYPOINTS,
        )
    except (DependencyClosureError, OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "PASS release package dependency closure "
        f"public_runtime_files={len(deployed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
