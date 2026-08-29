"""Fail closed when a deployment omits static theme runtime dependencies."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


RUNTIME_SUFFIXES = frozenset({".php", ".css", ".js", ".mjs"})
THEME_DIRECTORY_FUNCTIONS = frozenset(
    {
        "get_template_directory",
        "get_template_directory_uri",
        "get_stylesheet_directory",
        "get_stylesheet_directory_uri",
    }
)


@dataclass(frozen=True, order=True)
class MissingDependency:
    """One package member required by a deployed runtime source file."""

    dependency: str
    required_by: str


class DependencyClosureError(RuntimeError):
    """Raised when a deployment inventory is not runtime-complete."""

    def __init__(self, missing: Sequence[MissingDependency]) -> None:
        self.missing = tuple(missing)
        details = "\n".join(
            f"- {item.dependency} (required by {item.required_by})"
            for item in self.missing
        )
        super().__init__(f"deployment dependency closure is incomplete:\n{details}")


@dataclass(frozen=True)
class _PhpToken:
    kind: str
    value: str
    offset: int


def _normalize_relative(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path:
        raise ValueError(f"invalid deployment path: {path!r}")
    if path.startswith("/") or PurePosixPath(path).is_absolute():
        raise ValueError(f"deployment path must be relative: {path!r}")
    normalized = posixpath.normpath(path)
    if normalized in {"", "."} or normalized == ".." or normalized.startswith("../"):
        raise ValueError(f"deployment path escapes source root: {path!r}")
    return normalized


def _theme_root(relative: str) -> str:
    parts = PurePosixPath(relative).parts
    for index in range(len(parts) - 2):
        if parts[index : index + 2] == ("wp-content", "themes"):
            return "/".join(parts[: index + 3])
    raise ValueError(f"runtime entry is outside a WordPress theme: {relative}")


def _decode_php_string(source: str, start: int) -> tuple[_PhpToken, int]:
    quote = source[start]
    cursor = start + 1
    value: list[str] = []
    dynamic = False
    while cursor < len(source):
        character = source[cursor]
        if character == quote:
            return (
                _PhpToken("dynamic_string" if dynamic else "string", "".join(value), start),
                cursor + 1,
            )
        if character == "\\" and cursor + 1 < len(source):
            escaped = source[cursor + 1]
            if quote == "'" and escaped not in {"'", "\\"}:
                value.extend(("\\", escaped))
            else:
                value.append(escaped)
            cursor += 2
            continue
        if quote == '"' and character in {"$", "{"}:
            dynamic = True
        value.append(character)
        cursor += 1
    raise ValueError(f"unterminated PHP string at byte {start}")


def _php_tokens(source: str) -> tuple[_PhpToken, ...]:
    """Tokenize the PHP subset used by static local path expressions."""
    tokens: list[_PhpToken] = []
    cursor = 0
    in_php = False
    while cursor < len(source):
        if not in_php:
            opening = source.find("<?", cursor)
            if opening < 0:
                break
            cursor = opening + (5 if source[opening : opening + 5].lower() == "<?php" else 2)
            in_php = True
            continue
        if source.startswith("?>", cursor):
            cursor += 2
            in_php = False
            continue
        character = source[cursor]
        if character.isspace():
            cursor += 1
            continue
        if source.startswith("//", cursor) or character == "#":
            newline = source.find("\n", cursor + 1)
            closing = source.find("?>", cursor + 1)
            boundaries = [value for value in (newline, closing) if value >= 0]
            cursor = min(boundaries) if boundaries else len(source)
            continue
        if source.startswith("/*", cursor):
            closing = source.find("*/", cursor + 2)
            if closing < 0:
                raise ValueError(f"unterminated PHP comment at byte {cursor}")
            cursor = closing + 2
            continue
        if character in {"'", '"'}:
            token, cursor = _decode_php_string(source, cursor)
            tokens.append(token)
            continue
        if character == "$":
            end = cursor + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            tokens.append(_PhpToken("variable", source[cursor:end], cursor))
            cursor = end
            continue
        if character.isalpha() or character == "_" or ord(character) >= 128:
            end = cursor + 1
            while end < len(source):
                candidate = source[end]
                if not (candidate.isalnum() or candidate == "_" or ord(candidate) >= 128):
                    break
                end += 1
            tokens.append(_PhpToken("identifier", source[cursor:end], cursor))
            cursor = end
            continue
        tokens.append(_PhpToken("symbol", character, cursor))
        cursor += 1
    return tuple(tokens)


def _path_base(
    tokens: Sequence[_PhpToken],
    index: int,
    relative: str,
    aliases: dict[str, str],
) -> tuple[str, int] | None:
    token = tokens[index]
    lowered = token.value.lower()
    if token.value == "(" and index + 1 < len(tokens):
        grouped = _path_base(tokens, index + 1, relative, aliases)
        if grouped is not None:
            root, cursor = grouped
            if cursor < len(tokens) and tokens[cursor].value == ")":
                return root, cursor + 1
        return None
    if token.kind == "variable" and token.value in aliases:
        return aliases[token.value], index + 1
    if (
        token.kind == "identifier"
        and lowered in THEME_DIRECTORY_FUNCTIONS
        and index + 2 < len(tokens)
        and tokens[index + 1].value == "("
        and tokens[index + 2].value == ")"
    ):
        return _theme_root(relative), index + 3
    if token.kind == "identifier" and lowered == "__dir__":
        return posixpath.dirname(relative), index + 1
    if (
        token.kind == "identifier"
        and lowered == "dirname"
        and index + 3 < len(tokens)
        and tokens[index + 1].value == "("
        and tokens[index + 2].kind == "identifier"
        and tokens[index + 2].value.lower() == "__dir__"
        and tokens[index + 3].value == ")"
    ):
        return posixpath.dirname(posixpath.dirname(relative)), index + 4
    return None


def _static_path_expression(
    tokens: Sequence[_PhpToken],
    index: int,
    relative: str,
    aliases: dict[str, str],
) -> tuple[str | None, int]:
    base = _path_base(tokens, index, relative, aliases)
    if base is None:
        return None, index + 1
    root, cursor = base
    if cursor >= len(tokens) or tokens[cursor].value != ".":
        return root, cursor

    pieces: list[str] = []
    while cursor < len(tokens) and tokens[cursor].value == ".":
        cursor += 1
        if cursor >= len(tokens):
            raise ValueError(f"unsupported runtime path expression in {relative}")
        piece = tokens[cursor]
        if piece.kind == "string":
            pieces.append(piece.value)
        elif piece.kind == "identifier" and piece.value.lower() == "directory_separator":
            pieces.append("/")
        else:
            raise ValueError(
                f"unsupported runtime path expression in {relative} at byte {piece.offset}"
            )
        cursor += 1

    dependency = posixpath.join(root, "".join(pieces).lstrip("/"))
    return _normalize_relative(dependency), cursor


def _runtime_dependencies(relative: str, source: str) -> list[str]:
    tokens = _php_tokens(source)
    dependencies: list[str] = []
    exact: set[str] = set()
    folded: dict[str, str] = {}
    aliases: dict[str, str] = {}

    def record(dependency: str) -> None:
        if PurePosixPath(dependency).suffix.lower() not in RUNTIME_SUFFIXES:
            return
        case_key = dependency.casefold()
        previous = folded.get(case_key)
        if previous is not None and previous != dependency:
            raise ValueError(
                "case-fold runtime dependency collision: "
                f"{previous!r} and {dependency!r}"
            )
        folded[case_key] = dependency
        if dependency not in exact:
            exact.add(dependency)
            dependencies.append(dependency)

    index = 0
    while index < len(tokens):
        token = tokens[index]
        is_assignment = (
            token.kind == "variable"
            and index + 2 < len(tokens)
            and tokens[index + 1].value == "="
            and tokens[index + 2].value not in {"=", ">"}
        )
        expression_index = index + 2 if is_assignment else index
        dependency, next_index = _static_path_expression(
            tokens,
            expression_index,
            relative,
            aliases,
        )
        if is_assignment:
            if dependency is None:
                aliases.pop(token.value, None)
            else:
                aliases[token.value] = dependency
        index = max(index + 1, next_index)
        if dependency is None:
            continue
        record(dependency)
    return dependencies


def find_missing_dependencies(
    source_root: Path,
    deployed_paths: Iterable[str],
    entrypoints: Iterable[str],
) -> tuple[MissingDependency, ...]:
    """Return missing PHP/CSS/JS files reachable from selected theme entrypoints."""
    root = source_root.resolve()
    deployed: set[str] = set()
    deployed_case_names: dict[str, str] = {}
    for path in deployed_paths:
        normalized = _normalize_relative(path)
        case_key = normalized.casefold()
        previous = deployed_case_names.get(case_key)
        if previous is not None and previous != normalized:
            raise ValueError(
                "case-fold deployment path collision: "
                f"{previous!r} and {normalized!r}"
            )
        deployed_case_names[case_key] = normalized
        deployed.add(normalized)
    requested = tuple(_normalize_relative(path) for path in entrypoints)
    if not requested:
        raise ValueError("at least one runtime entrypoint is required")

    missing: dict[str, MissingDependency] = {}
    queue = list(requested)
    visited: set[str] = set()
    dependency_case_names: dict[str, str] = {}
    for entrypoint in requested:
        if entrypoint not in deployed:
            missing.setdefault(
                entrypoint,
                MissingDependency(entrypoint, "<runtime entrypoint>"),
            )

    while queue:
        relative = queue.pop(0)
        if relative in visited:
            continue
        visited.add(relative)

        source_path = (root / Path(*PurePosixPath(relative).parts)).resolve()
        try:
            source_path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"runtime source escapes source root: {relative}") from error
        if not source_path.is_file():
            raise ValueError(f"runtime source file is missing: {relative}")
        source = source_path.read_text(encoding="utf-8")

        for dependency in _runtime_dependencies(relative, source):
            case_key = dependency.casefold()
            previous = dependency_case_names.get(case_key)
            if previous is not None and previous != dependency:
                raise ValueError(
                    "case-fold runtime dependency collision: "
                    f"{previous!r} and {dependency!r}"
                )
            dependency_case_names[case_key] = dependency
            dependency_path = (root / Path(*PurePosixPath(dependency).parts)).resolve()
            try:
                dependency_path.relative_to(root)
            except ValueError as error:
                raise ValueError(
                    f"runtime dependency escapes source root: {dependency}"
                ) from error
            if not dependency_path.is_file():
                raise ValueError(
                    f"runtime dependency source file is missing: {dependency}"
                )
            if dependency not in deployed:
                missing.setdefault(
                    dependency,
                    MissingDependency(dependency, relative),
                )
            if dependency_path.suffix.lower() == ".php":
                queue.append(dependency)

    return tuple(sorted(missing.values()))


def assert_dependency_closure(
    source_root: Path,
    deployed_paths: Iterable[str],
    entrypoints: Iterable[str],
) -> None:
    """Raise with every missing member when the deployment is not closed."""
    missing = find_missing_dependencies(source_root, deployed_paths, entrypoints)
    if missing:
        raise DependencyClosureError(missing)


def load_deploy_list(path: Path) -> tuple[str, ...]:
    values = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    )
    normalized = tuple(_normalize_relative(value) for value in values)
    folded = [value.casefold() for value in normalized]
    if len(folded) != len(set(folded)):
        raise ValueError(f"deploy list contains duplicate or case-fold paths: {path}")
    return normalized
