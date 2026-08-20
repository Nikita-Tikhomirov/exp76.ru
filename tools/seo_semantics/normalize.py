"""Query text normalization for deterministic duplicate detection."""

from __future__ import annotations

import re
import unicodedata


_AREA_NOTATION = re.compile(r"\b(?:м2|кв\.?\s*м)\b", flags=re.IGNORECASE)


def normalize_query(value: str) -> str:
    """Return a comparable query while preserving words, numbers, and modifiers."""
    normalized = unicodedata.normalize("NFKC", value).lower().replace("ё", "е")
    normalized = _AREA_NOTATION.sub(" м2 ", normalized)
    normalized = "".join(
        " " if unicodedata.category(character).startswith("P") else character
        for character in normalized
    )
    return " ".join(normalized.split())
