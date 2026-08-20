"""Command-line entry points for the read-only semantic-core pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .manifest import register_source
from .scope import load_scope


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.seo_semantics.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    validate_scope = commands.add_parser("validate-scope")
    validate_scope.add_argument("--scope", required=True, type=Path)

    register = commands.add_parser("register-source")
    register.add_argument("--file", required=True, type=Path)
    register.add_argument("--source", required=True)
    register.add_argument("--collected-at", required=True)
    register.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "validate-scope":
            scope = load_scope(args.scope)
            print(f"scope valid: {len(scope.services)} services, {len(scope.frozen_urls)} frozen URLs")
        elif args.command == "register-source":
            entry = register_source(args.file, args.source, args.collected_at, args.manifest)
            print(json.dumps(entry.__dict__, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
